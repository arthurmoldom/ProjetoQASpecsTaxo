# Sheets → Bronze (QA Taxo)

Lê planilhas de **Spec** e **Plano** (Google Sheets e Excel/.xlsx no Drive), detecta mudanças por aba via **SHA256** e carrega só o que mudou na camada bronze do BigQuery. As camadas silver são geradas por procs SQL (fora deste repositório).

## Fluxo

1. `main.py` lê a planilha mestre (cadastro): `Campanha`, `Tipo` (Spec/Plano), `ID da planilha`, `Ativa`.
2. Para cada **arquivo** ativo (deduplicado por `spreadsheet_id + tipo`), identifica o `mimeType` (Google Sheets ou .xlsx) e percorre **todas as abas**.
3. Cada aba passa por `sheets/abas.py::detectar_header`. Se não seguir o layout mínimo, fica `IGNORADA`.
   - **SPEC:** linha com a coluna "Veículo".
   - **PLANO:** linha com "DETALHAMENTO GERAL"; o header fica 2 linhas abaixo.
4. O conteúdo é higienizado e o `sha256` é calculado. Ele é comparado com o último SHA de `(spreadsheet_id, aba)` em `bronze_qa_taxo_sha`.
   - **Igual:** `SEM_ALTERACAO`, não sobe nada.
   - **Diferente ou inexistente:** o conteúdo vai para a bronze, o CSV vai para o GCS e o status é `ATUALIZADA`.
5. A carga no BigQuery segue esta ordem: **bronze → tabela de SHA → cadastro → monitoramento**.

## Tabelas (dataset `MLMP_dataSwamp`)

| Tabela | Função |
|---|---|
| `bronze_qa_taxo` | Uma linha por linha de dados, com `payload_json`, `sha256` e `dt_carga` (carimbo único da execução). |
| `bronze_qa_taxo_sha` | Último SHA por `(spreadsheet_id, aba)`. Criada automaticamente (`CREATE TABLE IF NOT EXISTS`). |
| `monitoramento_sheet_...` | Uma linha por aba por execução. Status: `ATUALIZADA`, `SEM_ALTERACAO`, `IGNORADA`, `INFO`, `ERRO`. |
| `cadastro_sheet_...` | Cópia do cadastro a cada execução. |

DDL e `ALTER TABLE` estão em `sql/create_tbl.sql`. O rótulo de versão da silver está em `sql/silver_versao_aba.sql`.

## Pontos de atenção para alterações futuras

Requer credenciais ADC com permissão para impersonar a SA definida em `auth/auth.py` QUANDO EXECUTADO NO COMPUTADOR!

- **Ordem da carga no BigQuery.** A tabela de SHA só pode ser gravada **depois** que a bronze carregou. Se inverter, uma aba fica marcada como "enviada" sem estar na bronze e nunca mais sobe. Não coloque `try/except` engolindo erro nessa etapa.
- **O que entra no SHA.** É o DataFrame final (após `aplicar_header`, `higienizar_dataframe` e `normalizar_colunas`, sem linhas vazias). Qualquer mudança nessas funções, ou nos nomes de coluna, **muda o SHA de todas as abas** e gera reingestão total. Faça isso de forma consciente.
- **Chave da aba = nome.** Aba renomeada é tratada como aba nova. No Excel não existe `gid`.
- **Detecção de layout.** Alterar `detectar_header` muda quais abas são lidas. `localizar_header` (legado) devolve 0 quando não encontra, e não serve para decidir se uma aba deve ser lida.
- **Cadastro por arquivo, não por aba.** Como todas as abas são varridas, linhas repetidas do mesmo arquivo são puladas (`INFO`). `Aba` e `Gid` do cadastro hoje são só informativos.
- **Excel:** células vazias viram `""` (não `NaN`, que gera JSON inválido no `payload_json`). Só `.xlsx` é suportado, `.xls` não. O download exige o escopo `drive.readonly` em `auth/auth.py`.
- **Cota do Google Sheets:** ler todas as abas consome leituras (60 por minuto). Há retry em 429, mas arquivos com muitas abas aumentam o tempo de execução.
- **Novas colunas na bronze.** O `carregar_dataframe` usa `WRITE_APPEND`, então qualquer coluna nova exige `ALTER TABLE ... ADD COLUMN` antes, ou `schema_update_options` na carga.
- **Silver.** A bronze acumula **versões** de cada aba. As procs precisam decidir entre última versão (`ultima_versao`) ou histórico. A chave da versão é `(spreadsheet_id, aba, dt_carga)`, não o SHA, porque um SHA pode voltar (A→B→A). O fuso do rótulo é `America/Sao_Paulo`. Se a proc montar SQL com `FORMAT()`, escape os `%` como `%%`.
- **Carga inicial.** Linhas antigas da bronze (`sha256 IS NULL`) serão reingeridas na primeira execução. Apague-as antes para não duplicar a silver->verifique na tabela sql as procedures e views  
- **Credenciais.** Não versione `creds/service-account.json`. O `auth.py` usa ADC com impersonação de service account.
- **GCS.** O nome do CSV inclui `sha[:8]`, então várias versões no mesmo dia não se sobrescrevem: `QA_Taxo/raw/dt=YYYYMMDD/<campanha_tipo_id>/<aba>_<sha8>.csv`.

## Executar

```bash
pip install -r requirements.txt
python main.py        # ou: docker build -t sheets . && docker run sheets
```

