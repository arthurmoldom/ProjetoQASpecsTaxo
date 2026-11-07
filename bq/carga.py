from google.cloud import bigquery

def dataframe_para_bq(
    client,
    df,
    tabela
):

    job = client.load_table_from_dataframe(
        df,
        tabela
    )

    job.result()
    
def inserir_controle(
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




from google.cloud import bigquery


def carregar_dataframe(    df,    tabela,    creds,    project_id):
    client = bigquery.Client(        project=project_id,        credentials=creds    )
    job_config = bigquery.LoadJobConfig( write_disposition=bigquery.WriteDisposition.WRITE_APPEND    )
    job = client.load_table_from_dataframe(        df,        tabela,        job_config=job_config)
    job.result()
    print(        f"Carga concluída: {tabela}")