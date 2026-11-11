import time

import numpy as np
import pandas as pd
import gspread

from sheets.leitura import ler_aba_raw


def aparar_raw(df_raw):
    """
    Remove linhas/colunas vazias do final (o Google Sheets devolve o grid
    inteiro, o Excel pode trazer 'used range' sujo). Evita SHA diferente
    só porque alguém formatou células vazias.
    Mantém a numeração original das linhas (só corta o fim).
    """

    df = df_raw.fillna("").astype(str)

    if df.empty:
        return df

    nao_vazio = (df.apply(lambda c: c.str.strip()) != "").to_numpy()

    linhas = np.where(nao_vazio.any(axis=1))[0]
    colunas = np.where(nao_vazio.any(axis=0))[0]

    if len(linhas) == 0:
        return df.iloc[0:0, 0:0]

    return df.iloc[: linhas.max() + 1, : colunas.max() + 1].reset_index(drop=True)


def detectar_header(df_raw, tipo):
    """
    Devolve o índice (base 0) da linha de cabeçalho se a aba segue o
    layout mínimo de SPEC ou PLANO. Devolve None se NÃO segue.

    (localizar_header() devolve 0 quando não acha -> não serve para
    decidir se a aba deve ser lida.)
    """

    tipo = str(tipo).strip().upper()

    if tipo == "SPEC":

        for idx in range(len(df_raw)):

            valores = [
                str(x).strip().upper()
                for x in df_raw.iloc[idx].tolist()
            ]

            if "VEÍCULO" in valores or "VEICULO" in valores:
                return idx

    elif tipo == "PLANO":

        for idx in range(len(df_raw)):

            linha = " ".join(
                str(x).upper()
                for x in df_raw.iloc[idx].tolist()
            )

            if "DETALHAMENTO GERAL" in linha:

                header = idx + 2

                # precisa existir a linha de cabeçalho (idx+2)
                if header < len(df_raw):
                    return header

                return None

    return None


def _ler_gsheet_com_retry(worksheet, tentativas=4):
    # Sheets API: 60 leituras/min/usuário. Ler todas as abas gasta cota.
    for i in range(tentativas):
        try:
            return ler_aba_raw(worksheet)
        except gspread.exceptions.APIError as e:
            if "429" in str(e) and i < tentativas - 1:
                time.sleep(20 * (i + 1))
                continue
            raise


def iterar_abas_gsheet(planilha):
    """Gera (nome_aba, gid, df_raw) para TODAS as abas do Google Sheets."""

    for ws in planilha.worksheets():

        try:
            df_raw = _ler_gsheet_com_retry(ws)
            yield ws.title, str(ws.id), df_raw, None
        except Exception as e:
            yield ws.title, str(ws.id), None, e


def iterar_abas_excel(caminho_excel):
    """Gera (nome_aba, gid, df_raw) para TODAS as abas do .xlsx."""

    xls = pd.ExcelFile(caminho_excel)

    for nome in xls.sheet_names:

        try:
            df_raw = pd.read_excel(
                xls,
                sheet_name=nome,
                header=None,
                dtype=str
            )
            yield nome, "", df_raw, None
        except Exception as e:
            yield nome, "", None, e
