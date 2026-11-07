import os
import pandas as pd


def carregar_historico(nome_arquivo):

    if not os.path.exists(nome_arquivo):

        return pd.DataFrame()

    return pd.read_csv(
        nome_arquivo,
        sep=";",
        dtype=str
    )


def salvar_historico(df, nome_arquivo):

    os.makedirs(
        os.path.dirname(nome_arquivo),
        exist_ok=True
    )

    df.to_csv(
        nome_arquivo,
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )


def append_registros(
    registros,
    nome_arquivo
):

    df_novo = pd.DataFrame(registros)

    if os.path.exists(nome_arquivo):

        df_antigo = pd.read_csv(
            nome_arquivo,
            sep=";",
            dtype=str
        )

        df_final = pd.concat(
            [df_antigo, df_novo],
            ignore_index=True
        )

    else:

        df_final = df_novo

    salvar_historico(
        df_final,
        nome_arquivo
    )