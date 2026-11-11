from google.cloud import bigquery

DDL = """
CREATE TABLE IF NOT EXISTS `{tabela}` (
    dt_ingestao     TIMESTAMP,
    campanha        STRING,
    tipo            STRING,
    spreadsheet_id  STRING,
    gid             STRING,
    aba             STRING,
    sha256          STRING,
    qtd_linhas      INT64,
    header_row      INT64,
    mime_type       STRING
)
PARTITION BY DATE(dt_ingestao)
CLUSTER BY spreadsheet_id, aba
"""


def garantir_tabela_sha(creds, project_id, tabela):

    client = bigquery.Client(project=project_id, credentials=creds)
    client.query(DDL.format(tabela=tabela)).result()


def carregar_ultimos_shas(creds, project_id, tabela):
    """
    {(spreadsheet_id, aba): sha256 da última versão enviada à bronze}
    """

    client = bigquery.Client(project=project_id, credentials=creds)

    sql = f"""
        SELECT
            spreadsheet_id,
            aba,
            ARRAY_AGG(sha256 ORDER BY dt_ingestao DESC LIMIT 1)[OFFSET(0)] AS sha256
        FROM `{tabela}`
        GROUP BY spreadsheet_id, aba
    """

    return {
        (r.spreadsheet_id, r.aba): r.sha256
        for r in client.query(sql).result()
    }
