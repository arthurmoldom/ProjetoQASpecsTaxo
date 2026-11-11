CREATE OR REPLACE PROCEDURE `project-f193f4f9-98c9-4623-ab5.MLMP_dataSwamp.pr_recriar_silver_spec`()
BEGIN

  DECLARE v_select STRING;

  DECLARE v_sql STRING;

  ----------------------------------------------------------------------
  -- Geração dinâmica das colunas
  ----------------------------------------------------------------------

  SET v_select = (

    WITH base AS (

      SELECT

          coluna_normalizada,

          ARRAY_AGG(
              coluna_origem
              ORDER BY prioridade
          ) AS origens

      FROM
          MLMP_dataSwamp.depara_silver_spec

      WHERE
          manter = 'S'
          AND coluna_origem IS NOT NULL

      GROUP BY
          coluna_normalizada

    )

    SELECT
        STRING_AGG(
            FORMAT(
                """
                COALESCE(
                    %s
                ) AS %s
                """,

                (
                    SELECT STRING_AGG(
                        FORMAT(
                            "JSON_VALUE(payload_json,'$.%s')",
                            origem
                        ),
                        ', '
                    )
                    FROM
                        UNNEST(origens) origem
                ),

                LOWER(coluna_normalizada)
            ),

            ',\n'
        )

    FROM
        base

  );

  ----------------------------------------------------------------------
  -- Montagem SQL Silver
  ----------------------------------------------------------------------

  SET v_sql = FORMAT(

  """
  CREATE OR REPLACE TABLE
  MLMP_dataSwamp.silver_spec
  AS

  WITH Ultima_Carga AS (

      SELECT
          TIMESTAMP_SUB(
              MAX(dt_carga),
              INTERVAL 15 MINUTE
          ) AS dt_limite

      FROM
          MLMP_dataSwamp.bronze_qa_taxo

  ),versoes AS (
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
    FORMAT_TIMESTAMP('%%Y-%%m-%%d %%H:%%M', dt_carga, 'America/Sao_Paulo') AS ts_txt
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

      b.dt_carga,

      b.campanha,

      b.spreadsheet_id,

      b.gid,

      b.aba,

      b.source_row,

      b.header_row,
      r.versao_aba,
      %s

  FROM
      MLMP_dataSwamp.bronze_qa_taxo b
JOIN rotulo AS r
  ON  b.spreadsheet_id = r.spreadsheet_id
  AND b.aba            = r.aba
  AND b.dt_carga       = r.dt_carga
  CROSS JOIN
      Ultima_Carga u

  WHERE
      b.tipo = 'SPEC'

      AND b.dt_carga >= u.dt_limite

  """,

  v_select

  );

  ----------------------------------------------------------------------
  -- DEBUG
  ----------------------------------------------------------------------

  SELECT v_sql;

  ----------------------------------------------------------------------
  -- EXECUÇÃO
  ----------------------------------------------------------------------

  EXECUTE IMMEDIATE v_sql;

END;