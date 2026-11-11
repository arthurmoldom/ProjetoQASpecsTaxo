-- ============================================================================
-- Rótulo de versão da aba:  "YYYY-MM-DD HH:mm P - <Nome da Aba>"
--   ex.: "2026-11-11 12:36 A - Digital v06"
--        "2026-11-11 12:36 B - Digital v05"
--
-- Use este bloco (CTE `rotulo`) DENTRO das duas procs (silver_plano e silver_spec),
-- trocando só a tabela/colunas finais. Chave da versão = (spreadsheet_id, aba, dt_carga):
-- dt_carga é o carimbo único da execução, então identifica a versão mesmo que um mesmo
-- sha256 volte (A -> B -> A).
-- ============================================================================
WITH versoes AS (
  SELECT DISTINCT
    spreadsheet_id,
    aba,
    dt_carga,
    sha256
  FROM `project-f193f4f9-98c9-4623-ab5.MLMP_dataSwamp.bronze_qa_taxo`
  WHERE sha256 IS NOT NULL
),
carimbo AS (
  SELECT
    *,
    -- HH em 0-23, mm = minutos. Fuso: ajuste se não for Brasil.
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', dt_carga, 'America/Sao_Paulo') AS ts_txt
  FROM versoes
),
rotulo AS (
  SELECT
    spreadsheet_id,
    aba,
    dt_carga,
    sha256,
    CONCAT(
      ts_txt, ' ',
      -- maior nome da aba = A, depois B, C, D...  (por arquivo e por carimbo)
      CHR(64 + ROW_NUMBER() OVER (
                 PARTITION BY spreadsheet_id, ts_txt
                 ORDER BY aba DESC)),
      ' - ', aba
    ) AS versao_aba
  FROM carimbo
)
SELECT
  b.*,
  r.versao_aba
FROM `project-f193f4f9-98c9-4623-ab5.MLMP_dataSwamp.bronze_qa_taxo` AS b
JOIN rotulo AS r
  ON  b.spreadsheet_id = r.spreadsheet_id
  AND b.aba            = r.aba
  AND b.dt_carga       = r.dt_carga;
