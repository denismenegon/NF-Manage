import pandas as pd

def ler_planilha(caminho):
    df = pd.read_excel(caminho)
    return df