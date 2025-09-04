import pandas as pd
import math
import requests
import os
import asyncio
import time
import re
from datetime import datetime
from playwright.async_api import async_playwright, Playwright

from main_ler_planilha import ler_planilha
# Assumindo que essas funções também são assíncronas
# Caso contrário, elas precisam ser convertidas ou chamadas com asyncio
from main_ler_planilha import ler_planilha
from main_autenticacao import senha_valida, autenticar_NF, logout, tentar_verificar

async def consultar_NF(pagina, cnpj):
    """
    Navega para a seção de consulta de NF.
    """
    seletor_nfse = 'img[src="imgs/icon_nfse5.gif"]'
    # Adicionamos await
    await pagina.locator(seletor_nfse).click(timeout=40000)

async def consultar_Periodo(pagina, perIni, perFim):
    """
    Preenche os campos de data e verifica a mensagem de erro.
    """
    # Seletor CSS para encontrar o input de radio com type="radio" e value="periodo"
    seletor_css = 'input[type="radio"][value="periodo"]'
    
    # Clicar no elemento (precisa de await)
    await pagina.locator(seletor_css).click()

    # Formata as datas
    print ("Minha Data Início: ", perIni)
    if str(perIni).strip() != '':
        objeto_data = datetime.strptime(perIni, '%Y-%m-%d')
        data_inicial = objeto_data.strftime('%d/%m/%Y')

        # Preenche os campos (precisa de await)
        await pagina.get_by_role("textbox", name="De:").fill(data_inicial)
        
    if str(perFim).strip() != '':
        objeto_data = datetime.strptime(perFim, '%Y-%m-%d')
        data_final = objeto_data.strftime('%d/%m/%Y')

        # Preenche os campos (precisa de await)
        await pagina.get_by_role("textbox", name="Até:").fill(data_final)
    
    time.sleep (2)

    await consultar(pagina)

    mensagem_de_erro = pagina.get_by_text("A consulta não retornou dados.")

    time.sleep (3)

    # Aguarda a visibilidade da mensagem de erro e clica no botão OK
    # if await mensagem_de_erro.is_visible(): 
    #     await pagina.get_by_role("button", name="OK").click()
    #     return False
    # else:
    #     return True


    if await tentar_verificar(pagina, mensagem_de_erro):
        await pagina.get_by_role("button", name="OK").click()
        return False
    else:
         return True
    
    
async def consultar(pagina):
    """
    Clica no botão 'Consultar' da página.
    """
    seletor_botao_consultar = 'button:text("Consultar")'
    # Clicamos no primeiro botão 'Consultar' (precisa de await)
    await pagina.locator(seletor_botao_consultar).nth(0).click()

async def automatizar_consulta(dados, diretorio_arquivo, data_inicial, data_final, mes_referencia, tipo_pdf, tipo_xml, progresso, background_tipo):
    """
    Função principal que itera sobre os dados e realiza a automação.
    """
    # Usamos async_playwright para um contexto assíncrono
    async with async_playwright() as p:
        # Lança o navegador de forma assíncrona
        # navegador = await p.chromium.launch(headless=False)

        # 
        # AQUI: Adicione os argumentos de linha de comando
        # launch_options = {
        #     "headless": background_tipo,
        #     "args": ["--headless=new"]
        # }
        
        # Inicie o navegador com as opções
        # navegador = await p.chromium.launch(**launch_options)
        # 

        navegador = await p.chromium.launch(headless=background_tipo)

        context = await navegador.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/119.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo"
        )

        pagina = await context.new_page()
        
        total_passos = len(dados)

        for i, (index, linha) in enumerate(dados.iterrows()):
            progresso["valor"] = int((i + 1) / total_passos * 100)
            await asyncio.sleep(1)  # simula trabalho

            atividade = linha['Atividade']
            site = linha['Site']
            cnpj = linha['CNPJ']
            senha = linha['Senha']
            aliquota = linha['Alíquota']
            descricao = linha['Descrição']
            valor = linha['Valor']
            dia = linha['Dia']
            
            if await senha_valida(senha):
                authSite = site
                authCNPJ = cnpj
                authSenha = senha

            if not pd.isna(cnpj) and str(cnpj).strip() != '' and await senha_valida(senha):
                if authSite.find("capivari") != -1:
                    await processamento_Capivari(pagina, authSite, authCNPJ, authSenha, diretorio_arquivo, data_inicial, data_final, tipo_pdf, tipo_xml)
                else:
                    await processamento_Outros(site, pagina, authCNPJ, authSenha, diretorio_arquivo, mes_referencia)
                    
                
        await navegador.close()


async def processamento_Capivari (pagina, authSite, authCNPJ, authSenha, diretorio_arquivo, data_inicial, data_final, tipo_pdf, tipo_xml):
    time.sleep(5)
    # Chamadas assíncronas para funções de autenticação e consulta
    await autenticar_NF(pagina, authSite, authCNPJ, authSenha)
    time.sleep(5)
    # await para as funções
    await consultar_NF(pagina, authCNPJ)
    time.sleep(5)
    # O 'if' agora usa 'await' para chamar a função async
    if await consultar_Periodo(pagina, data_inicial, data_final):
        time.sleep(5)
        # Chamadas de download assíncronas
        await download_PDF(pagina, tipo_pdf, diretorio_arquivo, authCNPJ)
        time.sleep(5)
        await download_XML(pagina, tipo_xml, diretorio_arquivo, authCNPJ)
        time.sleep(5)
    # await para a função de logout
    await logout(pagina)


async def processamento_Outros(site, pagina, cnpj, senha, diretorio_arquivo, mes_referencia):
    await pagina.goto(site)
    time.sleep(2)

    # Preenche identificação e senha
    await pagina.fill("#ctl00_ContentPlaceHolder1_txtidentificacao", str(int(cnpj)))
    time.sleep(2)

    await pagina.fill("#ctl00_ContentPlaceHolder1_txtsenha", str(senha))

    time.sleep(5)

    # 1. Localiza o iframe do reCAPTCHA e o botão de seleção
    captcha_frame = pagina.frame_locator("iframe[title='reCAPTCHA']")
    captcha_box = captcha_frame.locator("#recaptcha-anchor")

    # 2. Clica no botão para exibir o pop-up com as imagens
    await captcha_box.click()

    # Aguarda o texto do captcha aparecer
    texto_instrucao = pagina.get_by_text("Selecione todas as imagens com", exact=False)

    print("Aguardando o pop-up do captcha estabilizar...")
    if await tentar_verificar(pagina, texto_instrucao):
        print("Pop-up do captcha estabilizado. Resolva o desafio...")

        try:
            # --- Opção 1: esperar sumir o botão "VERIFICAR"
            botao_verificar = pagina.get_by_role("button", name="VERIFICAR", exact=True)
            await botao_verificar.wait_for(state="hidden", timeout=480000)

            # --- Opção 2: garantir que o recaptcha foi validado (checkbox marcada)
            await pagina.wait_for_selector(".recaptcha-checkbox-checked", timeout=280000)

            print("Captcha resolvido! Continuando a automação...")

        except Exception as e:
            print(f"Não foi possível detectar a resolução do captcha: {e}")
    else:
        print("O pop-up do captcha não apareceu!")


    # Depois que o usuário resolver, clica em Confirmar
    # await pagina.click("#ctl00_ContentPlaceHolder1_BtnEntrar")

    # Crie o localizador para o botão "Entendi"
    # O get_by_text é a melhor opção, pois o texto é estável
    botao_confirmar = pagina.get_by_text("Confirmar")

    # Use sua função tentar_verificar para checar se o botão existe e está visívels
    # A função irá aguardar de forma robusta a visibilidade do elemento
    if await tentar_verificar(pagina, botao_confirmar):
        print("Botão 'Confirmar' encontrado. Clicando...")
        # Clica no botão. O Playwright já espera que ele esteja pronto para a ação.
        await botao_confirmar.click()
        print("Botão 'Confirmar' clicado com sucesso!")
    else:
        # Se o botão não for encontrado, o script continua sem clicar
        print("Botão 'Confirmar' não foi encontrado. Prosseguindo...")

    # Espera alguns segundos para ver o resultado
    await pagina.wait_for_timeout(10000)

    time.sleep(2)

    # Crie o localizador para o botão "Entendi"
    # O get_by_text é a melhor opção, pois o texto é estável
    botao_entendi = pagina.get_by_text("Entendi")

    # Use sua função tentar_verificar para checar se o botão existe e está visível
    # A função irá aguardar de forma robusta a visibilidade do elemento
    if await tentar_verificar(pagina, botao_entendi):
        print("Botão 'Entendi' encontrado. Clicando...")
        # Clica no botão. O Playwright já espera que ele esteja pronto para a ação.
        await botao_entendi.click()
        print("Botão 'Entendi' clicado com sucesso!")
    else:
        # Se o botão não for encontrado, o script continua sem clicar
        print("Botão 'Entendi' não foi encontrado. Prosseguindo...")

    time.sleep(2)

    # Crie o localizador para o link "Painel do Prestador"
    # O get_by_text é a melhor opção para links, pois o texto é estável
    link_painel = pagina.get_by_text("Painel do Prestador")

    # Use a sua função tentar_verificar para aguardar o link estar visível
    # A função irá verificar o link de forma robusta e resiliente
    if await tentar_verificar(pagina, link_painel):
        print("Link 'Painel do Prestador' encontrado. Clicando...")
        
        # O método .click() do Playwright já espera que o link esteja pronto para a ação
        await link_painel.click()
        
        print("Link clicado com sucesso!")
    else:
        # Se o link não for encontrado, o script continua sem quebrar
        print("Link 'Painel do Prestador' não foi encontrado. Prosseguindo...")

    time.sleep(2)

    # Crie o localizador para o link usando o texto
    link_consulta = pagina.get_by_text("Consulta de Lançamentos")

    # Use sua função para esperar o elemento
    if await tentar_verificar(pagina, link_consulta):
        print("Link 'Consulta de Lançamentos' encontrado. Clicando...")
        
        # O método .click() do Playwright já espera que o link esteja pronto para a ação
        await link_consulta.click()
        
        print("Link clicado com sucesso!")
    else:
        # Se o link não for encontrado, o script continua sem falhar
        print("Link 'Consulta de Lançamentos' não foi encontrado. Prosseguindo...")
        
    time.sleep(2)

    if (mes_referencia != "Selecione..."):
        time.sleep(2)
        await pagina.fill("#ctl00_ContentPlaceHolder1_txtmesano", str(mes_referencia) + "/" + str(datetime.now().year))
        time.sleep(2)
        await pagina.press("#ctl00_ContentPlaceHolder1_txtmesano", "Tab")
        time.sleep(2)
        
    # Seleciona todos os botões de impressão
    impressoras = pagina.locator("table#ctl00_ContentPlaceHolder1_GrdDados img[title='Clique aqui para Imprimir']")
    total = await impressoras.count()

    print(f"Total de itens para imprimir: {total}")

    for i in range(total):
        print(f"Processando item {i+1} de {total}...")
        
        # Espera pelo popup que será aberto
        async with pagina.expect_popup() as popup_info:
            # Clica no botão da linha atual
            await impressoras.nth(i).click()

        # Obtém a referência para a nova aba que exibe o PDF
        pagina_pdf = await popup_info.value

        # Espera a página do PDF carregar completamente para garantir que a URL esteja disponível
        await pagina_pdf.wait_for_load_state('domcontentloaded')

        # Obtém a URL do PDF
        pdf_url = pagina_pdf.url
        print(f"URL do PDF encontrada: {pdf_url}")

        # Fecha a aba do visualizador de PDF imediatamente
        await pagina_pdf.close()
        print("Aba do PDF fechada.")
        
        # --- Faz o download do arquivo a partir da URL obtida ---
        try:
            # Faz a requisição HTTP para a URL do PDF
            resposta = requests.get(pdf_url)
            
            # Verifica se a requisição foi bem-sucedida (código 200)
            if resposta.status_code == 200:
                # Cria um nome de arquivo simples, como "documento_1.pdf"
                nome_arquivo = f"documento_{i+1}_{str(cnpj).replace('.', '').replace('-', '').replace('/', '')}.pdf"
                
                caminho_salvo = os.path.join(diretorio_arquivo, nome_arquivo)

                # Salva o conteúdo da resposta em um arquivo local em modo binário
                with open(caminho_salvo, 'wb') as f:
                    f.write(resposta.content)
                    
                print(f"PDF baixado e salvo com sucesso como '{caminho_salvo}'.")
                print(f"Diretório: {diretorio_arquivo}")
            else:
                print(f"Erro ao baixar o PDF. Código de status: {resposta.status_code}")
        except Exception as e:
            print(f"Ocorreu um erro durante o download: {e}")

    print("Processo de download concluído.")


    print("\n--- Iniciando download de XMLs ---")
    xml_locators = pagina.locator("table#ctl00_ContentPlaceHolder1_GrdDados img[title='Clique aqui para Baixar o XML']")
    total_xmls = await xml_locators.count()

    print(f"Total de XMLs para baixar: {total_xmls}")

    for i in range(total_xmls):
        print(f"Processando XML {i+1} de {total_xmls}...")
        
        # Playwright detecta o evento de download
        async with pagina.expect_download() as download_info, pagina.expect_popup() as popup_info_xml:
            await xml_locators.nth(i).click()

        download = await download_info.value
        pagina_xml = await popup_info_xml.value

        # Usa o nome de arquivo sugerido pelo servidor
        nome_arquivo_xml = download.suggested_filename
        caminho_salvo_xml = os.path.join(diretorio_arquivo, nome_arquivo_xml)
        
        # Salva o arquivo no diretório especificado
        await download.save_as(caminho_salvo_xml)
        
        # Fecha a aba que foi aberta para o download
        await pagina_xml.close()

        print(f"XML baixado e salvo com sucesso como '{caminho_salvo_xml}'.")
        print("Aba do XML fechada.")

    # --- FIM DA SEÇÃO PARA XMLs ---

    print("\nProcesso de download concluído.")


async def download_PDF(pagina, tipo_pdf, diretorio_arquivo, authCNPJ):
    if tipo_pdf:
        print("PDF")

        # Descobre o número total de páginas
        # total_paginas_texto = await pagina.locator("span:has-text('de')").inner_text()
        total_paginas_texto = await pagina.locator("span.ytb-text", has_text=re.compile(r"^de\s+\d+")).inner_text()
        total_paginas = int(total_paginas_texto.replace("de", "").strip())
        print("Total de páginas:", total_paginas)

        pagina_atual_input = pagina.locator("input.x-tbar-page-number")

        # Loop de paginação
        for pagina_atual in range(1, total_paginas + 1):
            # Garante que está na página certa
            valor_atual = await pagina_atual_input.input_value()
            if int(valor_atual) != pagina_atual:
                time.sleep(2)

                await pagina_atual_input.fill(str(pagina_atual))
                await pagina.keyboard.press("Enter")
                await pagina.wait_for_timeout(2000)  # espera carregar tabela

            # Localiza todas as linhas da tabela
            linhas = pagina.locator('div.x-grid3-body .x-grid3-row')
            qtd = await linhas.count()
            print(f"Página {pagina_atual} -> {qtd} linhas")

            # Itera sobre cada linha
            for i in range(qtd):
                # celula_alvo = linhas.nth(i).locator('.x-grid3-col.x-grid3-cell.x-grid3-td-7.viewNota')

                celula_alvo = linhas.nth(i).locator('.x-grid3-col.x-grid3-cell.x-grid3-td-7.viewNota')

                # Verifica se o elemento existe/está visível
                if not await tentar_verificar(pagina, celula_alvo, tentativas=5, intervalo=1):
                    celula_alvo = linhas.nth(i).locator('.x-grid3-col.x-grid3-cell.x-grid3-td-7.viewNotaCanc')



                async with pagina.expect_popup() as popup_info_detalhes:
                    await celula_alvo.dblclick(force=True)

                pagina_detalhes = await popup_info_detalhes.value

                async with pagina_detalhes.expect_popup() as popup_info_pdf:
                    await pagina_detalhes.get_by_role("link", name="Exportar PDF").click()

                pagina_do_pdf = await popup_info_pdf.value
                url_do_pdf = pagina_do_pdf.url
                print(f"Baixando PDF da URL: {url_do_pdf}")

                response = requests.get(url_do_pdf)
                if response.status_code == 200:
                    nome_arquivo = f"documento_{pagina_atual}_{i+1}_{authCNPJ.replace('.', '').replace('-', '').replace('/', '')}.pdf"
                    caminho_salvo = os.path.join(diretorio_arquivo, nome_arquivo)
                    with open(caminho_salvo, 'wb') as f:
                        f.write(response.content)
                    print(f"PDF da linha {i+1} da página {pagina_atual} salvo em {caminho_salvo}")
                else:
                    print(f"Falha ao baixar PDF da linha {i+1} da página {pagina_atual}")

                await pagina_do_pdf.close()
                await pagina_detalhes.close()
                await pagina.wait_for_timeout(1000)

async def download_XML(pagina, tipo_xml, diretorio_arquivo, authCNPJ):
    """
    Lógica de download de arquivos XML, com diretório parametrizado.
    """
    if tipo_xml:
        print("Iniciando download de XML...")

        # Captura o download mesmo que abra uma nova aba
        async with pagina.expect_download() as download_info:
            await pagina.locator('img[src="imgs/download.png"]').nth(0).click()
        
        download = await download_info.value

        # Salva no diretório desejado
        nome_arquivo = f"XML_{authCNPJ.replace('.', '').replace('-', '').replace('/', '')}_{download.suggested_filename}"
        caminho_final = os.path.join(diretorio_arquivo, nome_arquivo)
        await download.save_as(caminho_final)

        print(f"Download do XML concluído: {caminho_final}")


async def consultar_arquivos(caminho_arquivo, diretorio_arquivo, data_inicial, data_final, mes_referencia, tipo_pdf, tipo_xml, progresso, background_tipo):
    """
    Função principal que inicia o processo de automação.
    """
    dados = ler_planilha(caminho_arquivo)
    # A chamada da função assíncrona deve usar await
    await automatizar_consulta(dados, diretorio_arquivo, data_inicial, data_final, mes_referencia, tipo_pdf, tipo_xml, progresso, background_tipo)


