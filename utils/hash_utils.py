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

def sha256_texto(texto):

    return hashlib.sha256(
        texto.encode("utf-8")
    ).hexdigest()


def sha256_dataframe(df):
    """
    SHA256 do conteúdo que vai para a bronze (cabeçalho + linhas já higienizadas).
    Mudou qualquer célula, nome de coluna ou ordem de linhas -> muda o sha.
    """

    return sha256_texto(
        df.to_csv(
            index=False,
            lineterminator="\n"
        )
    )
