from storage.controle_csv import (
    carregar_historico
)
from google.cloud import bigquery


def inserir_monitoramento(
    client,
    tabela,
    registros
):

    errors = client.insert_rows_json(
        tabela,
        registros
    )

    if errors:
        raise Exception(errors)


def obter_ultimo_registro(
    gid,
    arquivo_controle
):

    df = carregar_historico(
        arquivo_controle
    )

    if df.empty:
        return None

    df = df[
        df["gid"] == str(gid)
    ]

    if df.empty:
        return None

    df = df.sort_values(
        "dt_leitura",
        ascending=False
    )

    return (
        df.iloc[0]
        .to_dict()
    )

def salvar_execucao(
    registros,
    arquivo
):

    import pandas as pd
    import os

    os.makedirs(
        os.path.dirname(arquivo),
        exist_ok=True
    )

    pd.DataFrame(
        registros
    ).to_csv(
        arquivo,
        sep=";",
        encoding="utf-8-sig",
        index=False
    )