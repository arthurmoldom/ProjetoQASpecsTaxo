import hashlib


def gerar_hash_texto(texto):

    return hashlib.md5(
        texto.encode("utf-8")
    ).hexdigest()


def hash_colunas(colunas):

    return gerar_hash_texto(
        "|".join(colunas)
    )


def hash_dataframe(df):

    conteudo = df.to_csv(
        index=False
    )

    return gerar_hash_texto(
        conteudo
    )