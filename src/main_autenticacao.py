import time
import math
import asyncio
import os
import requests
from playwright.sync_api import sync_playwright

async def logout(pagina):
    await pagina.get_by_text("Sair do sistema").click()


async def senha_valida(senha):
    if senha is None:
        return False
    if isinstance(senha, float) and math.isnan(senha):
        return False
    if str(senha).strip() == '':
        return False
    return True

async def acesso_prestador(pagina, seletor):
    tentativas = 0
    max_tentativas = 3
    while await pagina.locator(seletor).is_visible() and tentativas < max_tentativas:
        await pagina.locator(seletor).click()

        tentativas += 1
    return not await pagina.locator(seletor).is_visible()

async def autenticar_NF(pagina, site, cnpj, senha):
    await pagina.goto(site)

    time.sleep (2)

    botao_ok_locator = pagina.get_by_role("button", name="OK")

    if await tentar_verificar(pagina, botao_ok_locator):
        await botao_ok_locator.click()

    time.sleep(2)

    seletor_imagem = 'img.imagem1[alt="Acesso Exclusivo Prestador"]'
    await acesso_prestador(pagina, seletor_imagem)

    time.sleep (5)
    
    # Use seletores robustos para encontrar os elementos
    campo_cnpj = pagina.get_by_label("CNPJ:")
    campo_senha = pagina.get_by_label("Senha:")
    botao_entrar = pagina.get_by_role("button", name="Entrar")

    # Preencher o campo de CNPJ
    # O método .fill() já espera que o campo esteja visível e habilitado antes de preencher
    await campo_cnpj.fill(str(cnpj))
    time.sleep (2)

    # Preencher o campo de senha
    await campo_senha.fill(str(senha))
    time.sleep (2)

    # Clicar no botão "Entrar"
    # O método .click() também espera que o elemento esteja visível, habilitado e pronto
    await botao_entrar.click()
    time.sleep (2)

async def tentar_verificar(pagina, alvo, tentativas=10, intervalo=2):
    """
    Pode receber um seletor CSS, um texto ou um locator direto.
    """
    # Se for locator, usa direto
    if not isinstance(alvo, str):
        locator = alvo
    else:
        # Se o string começar com '#' ou '.' ou outro seletor CSS, usa locator
        if alvo.startswith("#") or alvo.startswith("."):
            locator = pagina.locator(alvo)
        else:
            # caso seja um texto, usa get_by_text
            locator = pagina.get_by_text(alvo)

    print("Locator: ", locator)
    
    for i in range(tentativas):
        try:
            if await locator.is_visible():
                print(f"Elemento encontrado: {alvo}")
                return True
        except Exception:
            pass
        print(f"Tentativa {i+1}/{tentativas} falhou para {alvo}")
        await asyncio.sleep(intervalo)

    print(f"Não foi possível encontrar: {alvo}")

    return False