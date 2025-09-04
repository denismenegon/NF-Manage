from flask import Flask, render_template, request, jsonify
import os
import sys
import asyncio
import threading
import webbrowser

from main_emitir import emitir_arquivo
from main_consulta import consultar_arquivos
from main_autenticacao import senha_valida, acesso_prestador, autenticar_NF

import tkinter as tk
from tkinter import filedialog

def escolher_pasta():
    root = tk.Tk()
    root.withdraw()  # Oculta a janela principal
    root.attributes('-topmost', True)  # Força ficar em cima de todas as janelas
    pasta = filedialog.askdirectory(title="Selecione a pasta de destino")
    root.destroy()  # Fecha a janela oculta
    return pasta


def resource_path(relative_path):
    """Pega caminho absoluto para recurso, funciona no .exe e no script normal"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_path, "ms-playwright")
    else:
        base_path = os.path.abspath(".")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_path, "ms-playwright")
    return os.path.join(base_path, relative_path)

# Flask setup
template_folder = resource_path("templates")
static_folder = resource_path("static")
app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

progresso = {"valor": 0}

# Função utilitária para rodar coroutines em thread
def run_async_task(coro):
    threading.Thread(target=lambda: asyncio.run(coro), daemon=True).start()

# Rotas
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/selecionar_pasta", methods=["GET"])
def selecionar_pasta():
    pasta = escolher_pasta()
    return jsonify({"caminho": pasta})

@app.route("/progresso")
def get_progresso():
    return jsonify(progresso)

@app.route("/processar", methods=["POST"])
def processar():
    os.makedirs("uploads", exist_ok=True)
    arquivo = request.files["arquivo"]
    caminho = os.path.join("uploads", arquivo.filename)
    arquivo.save(caminho)

    background = request.form.get("tipo_background")
    background_tipo = bool(background)

    progresso["valor"] = 0
    run_async_task(emitir_arquivo(caminho, progresso, background_tipo))

    return render_template("index.html")

@app.route("/consultar", methods=["POST"])
def consultar():
    os.makedirs("uploads", exist_ok=True)
    arquivo_consulta = request.files["arquivo_consulta"]
    caminho = os.path.join("uploads", arquivo_consulta.filename)
    arquivo_consulta.save(caminho)

    diretorio = request.form.get("diretorio")
    data_inicial = request.form.get("data_inicial")
    data_final = request.form.get("data_final")
    mes_referencia = request.form.get("mes_referencia")
    tipo_pdf = request.form.get("tipo_pdf")
    tipo_xml = request.form.get("tipo_xml")
    background = request.form.get("tipo_background")
    background_tipo = bool(background)

    progresso["valor"] = 0
    run_async_task(consultar_arquivos(caminho, diretorio, data_inicial, data_final,
                                      mes_referencia, tipo_pdf, tipo_xml, progresso, background_tipo))

    return render_template("index.html")

# Rota para encerrar o .exe automaticamente
@app.route("/shutdown", methods=["POST", "GET"])
def shutdown():
    print("Fechando o servidor Flask e o .exe...")
    os._exit(0)
    return "Shutting down..."

# Função para abrir navegador automaticamente
def abrir_navegador():
    webbrowser.open("http://127.0.0.1:5000")

# Main
if __name__ == "__main__":
    progresso["valor"] = 0
    threading.Timer(1, abrir_navegador).start()

    if getattr(sys, 'frozen', False):
        app.run(debug=False, use_reloader=False)
    else:
        app.run(debug=True, use_reloader=False)


# from flask import Flask, render_template, request, jsonify
# import os
# import sys
# import asyncio
# import webbrowser
# import threading
# from main_emitir import emitir_arquivo  # importando sua função
# from main_consulta import consultar_arquivos  # importando sua função
# from main_autenticacao import senha_valida, acesso_prestador, autenticar_NF

# def resource_path(relative_path):
#     """Pega caminho absoluto para recurso, funciona no .exe e no script normal"""
#     if getattr(sys, 'frozen', False):
#         base_path = sys._MEIPASS
#         os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_path, "ms-playwright")
#     else:
#         base_path = os.path.abspath(".")
#         os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_path, "ms-playwright")
#     return os.path.join(base_path, relative_path)

# # usa assim:
# template_folder = resource_path("templates")
# static_folder = resource_path("static")

# app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

# progresso = {"valor": 0}  # variável global simples

# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/progresso")
# def get_progresso():
#     return jsonify(progresso)  # retorna valor atual


# @app.route("/processar", methods=["POST"])
# def processar():
#     os.makedirs("uploads", exist_ok=True)
#     arquivo = request.files["arquivo"]
#     caminho = os.path.join("uploads", arquivo.filename)
#     arquivo.save(caminho)

#     background = request.form.get("tipo_background")
#     background_tipo = True if background is not None else False

#     progresso["valor"] = 0  # zera progresso antes de começar

#     # Chama o processo Playwright com o arquivo salvo
#     asyncio.run(emitir_arquivo(caminho, progresso, background_tipo))

#     # return f"Arquivo {arquivo.filename} processado com sucesso!"

#     return render_template("index.html")

# @app.route("/consultar", methods=["POST"])
# def consultar():
#     # Pegando valores do formulário
#     os.makedirs("uploads", exist_ok=True)
#     arquivo_consulta = request.files["arquivo_consulta"]
#     caminho = os.path.join("uploads", arquivo_consulta.filename)
#     arquivo_consulta.save(caminho)

#     print("arquivo_consulta: ", arquivo_consulta.filename)

#     diretorio = request.form.get("diretorio")
#     data_inicial = request.form.get("data_inicial")
#     data_final = request.form.get("data_final")
#     mes_referencia = request.form.get("mes_referencia")
#     tipo_pdf = request.form.get("tipo_pdf")  # Vai ser "PDF" se marcado ou None se não marcado
#     tipo_xml = request.form.get("tipo_xml")  # Vai ser "XML" se marcado ou None se não marcado
#     background = request.form.get("tipo_background")
#     background_tipo = True if background is not None else False

#     # Exemplo: apenas para teste, imprimindo no console
#     print("Diretório:", diretorio)
#     print("Data inicial:", data_inicial)
#     print("Data final:", data_final)
#     print("Mês Referência:", mes_referencia)
#     print("PDF marcado:", tipo_pdf is not None)
#     print("XML marcado:", tipo_xml is not None)
#     print("Background:", background_tipo is not None)

#     # Aqui você pode implementar a lógica para:
#     # - Ler arquivos do diretório
#     # - Filtrar pelo período
#     # - Filtrar pelo tipo de arquivo (PDF/XML)

#     progresso["valor"] = 0  # zera progresso antes de começar

#     # Chama o processo Playwright com o arquivo salvo
#     asyncio.run(consultar_arquivos(caminho, diretorio, data_inicial, data_final, mes_referencia, tipo_pdf, tipo_xml, progresso, background_tipo))

#     # 
#     # Inicia a automação em uma nova thread
#     # thread_consulta = threading.Thread(
#     #     target=iniciar_consulta_thread, 
#     #     args=(caminho, diretorio, data_inicial, data_final, tipo_pdf, tipo_xml, progresso, background_tipo)
#     # )
#     # thread_consulta.start()
#     # 

#     # return f"Consulta feita para o caminha {caminho} e diretório {diretorio} de {data_inicial} até {data_final} PDF {tipo_pdf} XML {tipo_xml}"

#     return render_template("index.html")

# # 
# # Adicione esta função para rodar a automação em uma thread separada
# def iniciar_consulta_thread(caminho, diretorio, data_inicial, data_final, tipo_pdf, tipo_xml, progresso, background_tipo):
#     asyncio.run(consultar_arquivos(caminho, diretorio, data_inicial, data_final, tipo_pdf, tipo_xml, progresso, background_tipo))
# # 


# if __name__ == "__main__":
#     # AQUI: Zere o progresso antes de iniciar
#     progresso["valor"] = 0 

#     # Abre o navegador em uma thread separada para não travar o Flask
#     def abrir_navegador():
#         webbrowser.open("http://127.0.0.1:5000")

#     threading.Timer(1, abrir_navegador).start()
#     app.run(debug=True, use_reloader=True)


# # # if __name__ == "__main__":
# # #     app.run(debug=True)