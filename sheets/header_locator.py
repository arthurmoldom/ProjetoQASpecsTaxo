import pandas as pd


MESES = [    "JANEIRO",    "FEVEREIRO",    "MARÇO",   "MARCO",   "ABRIL",    "MAIO",
    "JUNHO",    "JULHO",    "AGOSTO",    "SETEMBRO",    "OUTUBRO",    "NOVEMBRO",    "DEZEMBRO"]


def numero_para_coluna(numero):
    resultado = ""
    while numero >= 0:
        resultado = (            chr(numero % 26 + 65)            + resultado        )
        numero = (            numero // 26        ) - 1
    return resultado


def localizar_header(    df_raw,    tipo):
    tipo = str(tipo).upper()
    if tipo == "SPEC":
        for idx, row in df_raw.iterrows():
            valores = [
                str(x).strip().upper()
                for x in row.tolist()
            ]
            if "VEÍCULO" in valores:
                return idx
            if "VEICULO" in valores:
                return idx
    elif tipo == "PLANO":
        for idx, row in df_raw.iterrows():
            linha = " ".join(
                [
                    str(x).upper()
                    for x in row.tolist()
                ]
            )
            if "DETALHAMENTO GERAL" in linha:
                return idx + 2
    return 0


def aplicar_header(    df_raw,    linha_header,    tipo):
    header = (
        df_raw
        .iloc[linha_header]
        .fillna("")
        .astype(str)
    )

    #
    # PLANO possui header em duas linhas
    #
    if str(tipo).upper() == "PLANO":

        header_superior = (
            df_raw
            .iloc[linha_header - 1]
            .fillna("")
            .astype(str)
        )

        contexto = ""

        novo_header = []

        for i in range(len(header)):
            superior = (str(header_superior.iloc[i]).strip())
            inferior = (str(header.iloc[i]).strip())

            # Célula mesclada
            if superior:
                contexto = superior
            # Meses
            if contexto.upper() in MESES:
                if inferior:
                    nome = (
                        f"{contexto}_{inferior}"
                    )
                else:
                    nome = contexto
            else:
                nome = inferior
            novo_header.append(nome)
        header = pd.Series( novo_header )

    dados = df_raw.iloc[linha_header + 1:].copy()
    print(f"\nHEADER IDENTIFICADO: {linha_header}")

    novas_colunas = []
    for i, col in enumerate(header):
        letra = numero_para_coluna(i)
        col = str(col).strip()
        if not col:
            col = "UNNAMED"
        col = (
            col
            .replace("\n", " ")
            .replace("\r", " ")
            .strip()
        )
        novas_colunas.append(
            f"{letra}__{col}"
        )
    dados.columns = novas_colunas
    print("COLUNAS IDENTIFICADAS:")
    for col in dados.columns:
        print(f"  -> {col}")
    dados.reset_index(drop=True,inplace=True)
    return dados