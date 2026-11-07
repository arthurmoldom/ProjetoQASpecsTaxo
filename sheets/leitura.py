import gspread
import pandas as pd

def ler_aba_raw(worksheet):
    valores = worksheet.get_all_values()
    return pd.DataFrame(valores)

def ler_excel_raw(arquivo_excel,nome_aba):
    return pd.read_excel(arquivo_excel,sheet_name=nome_aba,header=None,dtype=str)

def ler_aba_excel(arquivo_excel,nome_aba):

    return pd.read_excel(arquivo_excel,sheet_name=nome_aba, dtype=str  )

def listar_abas_excel( arquivo_excel):
    excel = pd.ExcelFile(
    arquivo_excel
    )
    return excel.sheet_names

def abrir_planilha(spreadsheet_id,    creds):
    gc = gspread.authorize(creds)
    return gc.open_by_key(spreadsheet_id)


def listar_abas(planilha):
    resultado = []
    for aba in planilha.worksheets():
        resultado.append(
            {"gid": str(aba.id),  "nome": aba.title }     )
    return resultado


def ler_aba(worksheet):
    valores = worksheet.get_all_values()
    if not valores:
        return pd.DataFrame()
    cabecalho = valores[0]
    dados = valores[1:]
    colunas = []
    for i, coluna in enumerate(cabecalho):
        coluna = coluna.strip()
        if coluna == "":
            coluna = f"SEM_NOME_{i+1}"
        colunas.append(coluna)
    df = pd.DataFrame(  dados,     columns=colunas )
    return df


def obter_cabecalho(worksheet):
    cabecalho = worksheet.row_values(1)
    resultado = []
    for i, col in enumerate(cabecalho):
        col = col.strip()
        if col == "":
            col = f"SEM_NOME_{i+1}"
        resultado.append(col)
    return resultado

def localizar_gid(    planilha,    gid):
    for worksheet in planilha.worksheets():
        if str(worksheet.id) == str(gid):
            return worksheet
    return None