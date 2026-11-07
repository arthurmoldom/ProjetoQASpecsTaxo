import pandas as pd
import re
import unicodedata


def limpar_texto(valor):

    if pd.isna(valor):
        return valor

    valor = str(valor)

    # remove quebras de linha
    valor = valor.replace("\r\n", " ")
    valor = valor.replace("\n", " ")
    valor = valor.replace("\r", " ")

    # remove tabs
    valor = valor.replace("\t", " ")

    # remove espaços múltiplos
    valor = re.sub(r"\s+", " ", valor)

    # trim
    valor = valor.strip()

    return valor


def higienizar_dataframe(df):

    return df.map(limpar_texto)

def normalizar_colunas(df):

    novas_colunas = []

    for col in df.columns:

        col = limpar_texto(col)

        col = col.lower()

        col = re.sub(
            r'[^a-zA-Z0-9_]',
            '_',
            col
        )

        col = re.sub(
            r'_+',
            '_',
            col
        )

        col = col.strip("_")

        novas_colunas.append(col)

    df.columns = novas_colunas

    return df

def sanitizar_nome_arquivo(texto):
   
    texto = str(texto)

    texto = unicodedata.normalize("NFKD",texto )

    texto = texto.strip()
    texto =  re.sub(r'[<>:"/\\|?*\n\r\t]', '_', texto)
    texto = re.sub(r'_+','_',texto    )
    
    resposta = ( str(texto)
                    .replace("/", "_")
                    .replace("\\", "_")
                    .replace(":", "_")
                    .replace("*", "_")
                    .replace("?", "_")
                    .replace("|", "_")
                    .replace("<", "_")
                    .replace(">", "_")
                    .replace('"', "_")
                    .replace(" ", "_")
                )
    return resposta