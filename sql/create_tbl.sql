-- 1) Bronze: nova coluna com o SHA256 da versão da aba que originou a linha
ALTER TABLE MLMP_dataSwamp.bronze_qa_taxo
  ADD COLUMN IF NOT EXISTS sha256 STRING;

-- Linhas antigas (sha256 IS NULL) serão reingeridas na 1ª execução nova, pois a tabela de SHA começa vazia.
-- Opção recomendada antes da 1ª execução (evita duplicidade na silver):
-- DELETE FROM MLMP_dataSwamp.bronze_qa_taxo WHERE sha256 IS NULL;

-- 2) Tabela acessória (também é criada automaticamente pelo código com CREATE TABLE IF NOT EXISTS)
CREATE TABLE IF NOT EXISTS MLMP_dataSwamp.bronze_qa_taxo_sha (
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
CLUSTER BY spreadsheet_id, aba;
