def avaliar_status(
    aba_atual,
    ultimo,
    colunas_esperadas,
    hash_colunas_atual,
    hash_conteudo_atual
):

    if ultimo is None:

        return (
            "ALERTA",
            "Aba criada"
        )

    if (
        ultimo["aba_nome"]
        !=
        aba_atual["nome"]
    ):

        return (
            "ALERTA",
            f'Aba renomeada de {ultimo["aba_nome"]} para {aba_atual["nome"]}'
        )

    obrigatorias = colunas_esperadas.get(
        aba_atual["nome"],
        []
    )

    colunas_atuais = aba_atual["colunas"]

    for col in obrigatorias:

        if col not in colunas_atuais:

            return (
                "ERRO",
                f"Coluna obrigatória ausente: {col}"
            )

    if (
        ultimo["hash_colunas"]
        !=
        hash_colunas_atual
    ):

        return (
            "INFORMACAO",
            "Estrutura de colunas alterada"
        )

    if (
        ultimo["hash_conteudo"]
        !=
        hash_conteudo_atual
    ):

        return (
            "INFORMACAO",
            "Conteúdo alterado"
        )

    return (
        "OK",
        ""
    )