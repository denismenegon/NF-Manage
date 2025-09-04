import pandas as pd
import time
import math
import asyncio
from playwright.async_api import async_playwright, Playwright
from main_ler_planilha import ler_planilha
from main_autenticacao import senha_valida, acesso_prestador, autenticar_NF, logout

async def emitir_NF(pagina, cnpj):
    seletor_nfse = 'img[src="imgs/icon_nfse3.gif"]'
    await pagina.locator(seletor_nfse).click(timeout=40000)

async def emitir_NF_Aba_01(pagina, cnpj):
    seletor_campo_valor = 'input[type="text"][size="20"][style*="width: 240px;"]'
    seletor_botao_pesquisar = 'button:text("Pesquisar")'
    seletor_botao_proximo = 'button:text("Próximo Passo")'

    time.sleep (2)
    await pagina.fill(seletor_campo_valor, str(cnpj))
    time.sleep (2)
    await pagina.locator(seletor_botao_pesquisar).nth(0).click()
    time.sleep (2)
    await pagina.locator(seletor_botao_proximo).nth(0).click()


async def emitir_NF_Aba_02(pagina, atividade, aliquota, descricao, valor, dia):
    await pagina.get_by_role("textbox", name="Código do Serviço/Atividade:").click()
    time.sleep (2)
    await pagina.get_by_text(str(atividade)).click()
    time.sleep (2)

    campo = pagina.locator('input[type="text"][size="20"][style*="width: 75px"]')
    campo.wait_for(state="visible", timeout=100000)
    await campo.click()
    
    time.sleep (2)
    
    await campo.fill(str(aliquota))
    time.sleep (2)

    seletor_textarea = 'textarea[style="width: 460px; height: 150px;"]'
    await pagina.locator(seletor_textarea).fill(descricao)
    time.sleep (2)

    campo_valor = pagina.get_by_label("Valor do serviço prestado:")
    await campo_valor.click()
    time.sleep (2)

    await campo_valor.fill(valor)
    time.sleep (2)
    await pagina.get_by_role("button", name="Próximo Passo >>").click()


async def processar_NF(pagina):
    # Clica no botão que tem o texto visível "Emitir Nfse"
    await pagina.get_by_text("Emitir Nfse").click()
    print("Clicado no botão 'Emitir Nfse'.")
    time.sleep (3)
    
    # Clica no botão que contém exatamente o texto "OK"
    await pagina.get_by_role("button", name="OK").click()
    time.sleep (3)

    # Clica no botão que contém exatamente o texto "OK"
    await pagina.get_by_role("button", name="Cancelar").click()


async def automatizar_site(dados, progresso, background_tipo):
    async with async_playwright() as p:
        navegador = await p.chromium.launch(headless=background_tipo)  # use headless para servidor
        pagina = await navegador.new_page()

        total_passos = len(dados)

        blnStart = False

        print ('Total de linhas: ', total_passos)

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

                print("CNPJ: ", authCNPJ)

                if authSite.find("capivari") != -1: continue

            if not pd.isna(cnpj) and str(cnpj).strip() != '' and await senha_valida(senha):
                time.sleep(2)
                await autenticar_NF(pagina, authSite, authCNPJ, authSenha)
                time.sleep(2)
                await emitir_NF(pagina, authCNPJ)
                blnStart = True
            else:
                if not blnStart and not pd.isna(cnpj) and str(cnpj).strip() != '':
                    time.sleep(2)
                    await autenticar_NF(pagina, authSite, authCNPJ, authSenha)
                    time.sleep(2)
                    await emitir_NF(pagina, authCNPJ)
                    time.sleep(2)

                if not pd.isna(cnpj) and str(cnpj).strip() != '':
                    time.sleep(2)
                    await emitir_NF_Aba_01(pagina, cnpj)
                    time.sleep(2)
                    await emitir_NF_Aba_02(pagina, atividade, aliquota, descricao, valor, dia)
                    time.sleep(2)
                    await processar_NF(pagina)
                    time.sleep(5)
                    await logout(pagina)
                    blnStart = False

        navegador.close()

async def emitir_arquivo(caminho_arquivo, progresso, background_tipo):
    dados = ler_planilha(caminho_arquivo)
    await automatizar_site(dados, progresso, background_tipo)
