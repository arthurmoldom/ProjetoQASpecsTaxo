CREATE TABLE MLMP_dataSwamp.bronze_sheets_RegistroDePlanosESPECsAtivos (
    campaign_id STRING,
    campaign_name STRING,
    impressions INT64,
    clicks INT64,
    load_date DATE
);


REATE TABLE MLMP_dataSwamp.monitoramento_sheet_RegistroDePlanosESPECsAtivos (
    dt_leitura TIMESTAMP,
    spreadsheet_id STRING,
    spreadsheet_nome STRING,

    gid STRING,
    aba_nome STRING,

    ultima_modificacao TIMESTAMP,

    qtd_colunas INT64,
    hash_colunas STRING,

    qtd_linhas INT64,
    hash_conteudo STRING,

    status STRING,
    detalhes STRING
)
PARTITION BY DATE(dt_leitura);