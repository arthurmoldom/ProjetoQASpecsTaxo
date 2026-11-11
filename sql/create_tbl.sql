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


--depara_silver_plano	"
CREATE TABLE `project-f193f4f9-98c9-4623-ab5.MLMP_dataSwamp.depara_silver_plano`
(
  coluna_logica STRING,
  coluna_normalizada STRING,
  categoria STRING,
  mes_normalizado STRING,
  tipo_dado STRING,
  manter STRING,
  observacao STRING,
  coluna_origem STRING,
  prioridade INT64
);
--"bronze_qa_taxo	"
CREATE TABLE `project-f193f4f9-98c9-4623-ab5.MLMP_dataSwamp.bronze_qa_taxo`
(
  dt_carga TIMESTAMP,
  campanha STRING,
  tipo STRING,
  spreadsheet_id STRING,
  gid STRING,
  aba STRING,
  payload_json STRING,
  source_row INT64,
  header_row INT64,
  sha256 STRING
)
PARTITION BY DATE(dt_carga);
--"depara_silver_spec	"
CREATE TABLE `project-f193f4f9-98c9-4623-ab5.MLMP_dataSwamp.depara_silver_spec`
(
  coluna_origem STRING,
  coluna_logica STRING,
  coluna_normalizada STRING,
  categoria STRING,
  mes_normalizado STRING,
  tipo_dado STRING,
  manter STRING,
  observacao STRING,
  prioridade INT64
);
--"
CREATE TABLE `project-f193f4f9-98c9-4623-ab5.MLMP_dataSwamp.bronze_sheet_spec`
(
  dt_carga TIMESTAMP,
  campanha STRING,
  tipo STRING,
  spreadsheet_id STRING,
  gid STRING,
  aba STRING,
  payload_json STRING
);