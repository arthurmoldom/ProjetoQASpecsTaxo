## SERVICE_ACCOUNT_FILE = "creds/service-account.json"

SPREADSHEET_ID = "1ncSntsyAe5g39rnX7rQq2VZ4YUlm9W0VZrWR0pUFGRc"
#https://docs.google.com/spreadsheets/d/1ncSntsyAe5g39rnX7rQq2VZ4YUlm9W0VZrWR0pUFGRc/edit?gid=0#gid=0
ABA = "data"

PROJECT_ID = "project-f193f4f9-98c9-4623-ab5"

DATASET = "MLMP_dataSwamp"

ARQ_EXECUCAO = (    "tmp/controle/execucao.csv")


TB_MONITORAMENTO = (f"{PROJECT_ID}.{DATASET}.monitoramento_sheet_RegistroDePlanosESPECsAtivos")
TB_BRONZE        =(    f"{PROJECT_ID}.{DATASET}.bronze_qa_taxo" )
TB_CADASTRO = (f"{PROJECT_ID}.{DATASET}.cadastro_sheet_RegistroDePlanosESPECsAtivos")
#TB_CONTROLE = "monitoramento_sheet_RegistroDePlanosESPECsAtivos"
#TABELA = "bronze_sheets_RegistroDePlanosESPECsAtivos" 
#TB_EXECUCAO = "monitoramento_sheet_ControleExec_RegistroDePlanosESPECsAtivos"


CSV_FOLDER = "tmp/csvs"

GCS_BUCKET = "rawdata_scrappers"

GCS_PREFIX = "QA_Taxo"

COLUNAS_ESPERADAS = {
    "Campanhas": [
        "campaign_id",
        "campaign_name",
        "impressions"
    ]
}


ARQ_CONTROLE = (
    "tmp/controle/"
    "monitoramento_sheet_RegistroDePlanosESPECsAtivos.csv"
)

ARQ_EXECUCAO = (
    "tmp/controle/"
    "monitoramento_sheet_ControleExec_RegistroDePlanosESPECsAtivos.csv"
)