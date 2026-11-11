###VIA PIP/REQUIREMENTS
from datetime import datetime, timezone
import pandas                   as pd
import os
import json
### Do Projeto
from config                     import (SPREADSHEET_ID,ARQ_CONTROLE,CSV_FOLDER,GCS_PREFIX,GCS_BUCKET,
                                        TB_MONITORAMENTO,TB_BRONZE,PROJECT_ID,TB_CADASTRO,TB_SHA,TIPOS_VALIDOS)
from auth.auth                  import get_credentials
from sheets.leitura             import (abrir_planilha,ler_aba)
from storage.controle_csv       import (append_registros)
from utils.sanitizacao          import (higienizar_dataframe,normalizar_colunas,sanitizar_nome_arquivo)
from utils.hash_utils           import (sha256_dataframe)
from storage.gcs                import (upload_csv_para_gcs)
from sheets.filetype            import (obter_info_arquivo)
from sheets.excel               import (baixar_excel)
from sheets.header_locator      import (aplicar_header)
from sheets.abas                import (aparar_raw,detectar_header,iterar_abas_gsheet,iterar_abas_excel)
from bq.carga                   import (carregar_dataframe)
from bq.sha_controle            import (garantir_tabela_sha,carregar_ultimos_shas)
from export.export_csv          import (exportar_csv)

MIME_GSHEET = "application/vnd.google-apps.spreadsheet"
MIME_XLSX   = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Carimbo ÚNICO da execução. É ele que vira "dt_carga" na bronze e "dt_ingestao" na tabela de SHA,
# e é a base do rótulo "YYYY-MM-DD HH:mm P - Aba" da silver (todas as abas da mesma execução
# precisam ter o mesmo timestamp, senão o desempate A/B/C não funciona).
DT_EXECUCAO = datetime.now(timezone.utc)


def novo_controle(**kw):
    base = {"dt_leitura"    : DT_EXECUCAO,
            "aba_cadastro"  : "",
            "campanha"      : "",
            "tipo"          : "",
            "spreadsheet_id": "",
            "gid"           : "",
            "aba_esperada"  : "",
            "aba_encontrada": "",
            "status"        : "OK",
            "detalhes"      : "",
            "arquivo_csv"   : "",
            "mime_type"     : ""}
    base.update(kw)
    return base


def main():

    creds = get_credentials()

    print("Abrindo planilha mestre...")
    planilha_mestre = abrir_planilha(SPREADSHEET_ID, creds)

    print("Carregando últimos SHA256 já enviados à bronze...")
    garantir_tabela_sha(creds, PROJECT_ID, TB_SHA)
    shas_anteriores = carregar_ultimos_shas(creds, PROJECT_ID, TB_SHA)
    print(f"  {len(shas_anteriores)} abas com SHA conhecido")

    registros_controle  = []
    registros_bronze    = []
    registros_sha       = []
    cadastros_bq        = []
    arquivos_vistos     = set()   # (spreadsheet_id, tipo) -> cada ARQUIVO é lido uma vez só

    for aba_cadastro in planilha_mestre.worksheets():

        nome_aba_cadastro = aba_cadastro.title
        print(f"Aba:{nome_aba_cadastro}, gid:{aba_cadastro.id}")

        # ignora aba de formulário
        if nome_aba_cadastro.lower() == "form":
            continue

        try:
            df_cadastro = ler_aba(aba_cadastro)
        except Exception as e:
            print(f"Erro lendo cadastro {nome_aba_cadastro}: {e}")
            continue

        if df_cadastro.empty:
            print(f"{nome_aba_cadastro} sem registros.")
            continue

        df_cadastro_bq = df_cadastro.copy()
        df_cadastro_bq["dt_carga"] = DT_EXECUCAO
        df_cadastro_bq = df_cadastro_bq.rename(columns={
                            "ID"            : "id",
                            "Timestamp"     : "timestamp_cadastro",
                            "Campanha"      : "campanha",
                            "Tipo"          : "tipo",
                            "URL"           : "url",
                            "ID da planilha": "spreadsheet_id",
                            "Aba"           : "aba",
                            "Gid"           : "gid",
                            "Link da Aba"   : "link_aba",
                            "Responsável"   : "responsavel",
                            "Ativa"         : "ativa" })
        cadastros_bq.append(df_cadastro_bq)

        df_cadastro = df_cadastro[
                        df_cadastro["Ativa"].astype(str).str.lower().isin(
                            ["true", "1", "sim", "yes", "verdadeiro"]
                        )
                    ]

        for _, row in df_cadastro.iterrows():

            spreadsheet_id  = str(row.get("ID da planilha", "")).strip()
            aba_esperada    = str(row.get("Aba", "")).strip()
            campanha        = str(row.get("Campanha", "")).strip()
            tipo            = str(row.get("Tipo", "")).strip()
            ctx = dict(aba_cadastro=nome_aba_cadastro, campanha=campanha, tipo=tipo,
                       spreadsheet_id=spreadsheet_id, aba_esperada=aba_esperada)

            if spreadsheet_id == "":
                registros_controle.append(novo_controle(**ctx, status="ERRO", detalhes="ID da planilha vazio"))
                continue

            if tipo.upper() not in TIPOS_VALIDOS:
                registros_controle.append(novo_controle(**ctx, status="ERRO",
                                          detalhes=f"Tipo inválido '{tipo}' (esperado: {TIPOS_VALIDOS})"))
                continue

            # várias linhas do cadastro podem apontar para o mesmo arquivo (uma por aba).
            # Como agora varremos TODAS as abas, o arquivo só precisa ser lido uma vez.
            chave_arquivo = (spreadsheet_id, tipo.upper())
            if chave_arquivo in arquivos_vistos:
                registros_controle.append(novo_controle(**ctx, status="INFO",
                                          detalhes="Arquivo já processado nesta execução (outra linha do cadastro)"))
                continue
            arquivos_vistos.add(chave_arquivo)

            # ---------- 1) Descobre o tipo do arquivo e obtém um iterador de abas ----------
            try:
                info_arquivo = obter_info_arquivo(spreadsheet_id, creds)
                mime_type = info_arquivo["mimeType"]
                ctx["mime_type"] = mime_type

                if mime_type == MIME_GSHEET:
                    abas = iterar_abas_gsheet(abrir_planilha(spreadsheet_id, creds))

                elif mime_type == MIME_XLSX:
                    os.makedirs("tmp/xlsx", exist_ok=True)
                    caminho_excel = f"tmp/xlsx/{spreadsheet_id}.xlsx"
                    baixar_excel(spreadsheet_id, caminho_excel, creds)
                    abas = iterar_abas_excel(caminho_excel)

                else:
                    registros_controle.append(novo_controle(**ctx, status="ERRO",
                                              detalhes=f"Formato de arquivo não suportado: {mime_type}"))
                    continue

            except Exception as e:
                # erro ao abrir/baixar o arquivo: registra e segue para o próximo (NÃO derruba a execução)
                registros_controle.append(novo_controle(**ctx, status="ERRO",
                                          detalhes=f"Falha ao abrir/baixar arquivo: {e}"))
                continue

            # ---------- 2) Passa por TODAS as abas ----------
            for nome_aba, gid, df_raw, erro_leitura in abas:

                ctx_aba = dict(ctx, gid=gid, aba_encontrada=nome_aba)

                if erro_leitura is not None:
                    registros_controle.append(novo_controle(**ctx_aba, status="ERRO",
                                              detalhes=f"Falha lendo aba: {erro_leitura}"))
                    continue

                try:
                    df_raw = aparar_raw(df_raw)
                    linha_header = detectar_header(df_raw, tipo)

                    # aba que não segue o layout mínimo -> ignorada
                    if linha_header is None:
                        registros_controle.append(novo_controle(**ctx_aba, status="IGNORADA",
                                                  detalhes=f"Layout {tipo.upper()} não reconhecido"))
                        continue

                    df_conteudo = aplicar_header(df_raw, linha_header, tipo)
                    df_conteudo = higienizar_dataframe(df_conteudo)
                    df_conteudo = normalizar_colunas(df_conteudo)

                    # remove linhas totalmente vazias (mantém o índice p/ calcular source_row)
                    df_conteudo = df_conteudo[(df_conteudo.fillna("") != "").any(axis=1)]

                    if df_conteudo.empty:
                        registros_controle.append(novo_controle(**ctx_aba, status="IGNORADA",
                                                  detalhes="Layout ok, mas sem linhas de dados"))
                        continue

                    # ---------- 3) SHA256 x último SHA conhecido ----------
                    sha = sha256_dataframe(df_conteudo)
                    sha_anterior = shas_anteriores.get((spreadsheet_id, nome_aba))

                    if sha == sha_anterior:
                        registros_controle.append(novo_controle(**ctx_aba, status="SEM_ALTERACAO",
                                                  detalhes=f"sha256={sha}"))
                        continue

                    detalhe = "ABA NOVA" if sha_anterior is None else "ABA ALTERADA"

                    # ---------- 4) Mudou -> bronze + CSV + GCS ----------
                    for i, (_, linha) in enumerate(df_conteudo.iterrows()):
                        registros_bronze.append({
                            "dt_carga"      : DT_EXECUCAO,
                            "campanha"      : campanha,
                            "tipo"          : tipo,
                            "spreadsheet_id": spreadsheet_id,
                            "gid"           : gid,
                            "aba"           : nome_aba,
                            "payload_json"  : json.dumps(linha.to_dict(), ensure_ascii=False),
                            # índice do df_conteudo = posição da linha após o header (0,1,2...)
                            "source_row"    : int(df_conteudo.index[i]) + int(linha_header) + 2,
                            "header_row"    : int(linha_header),
                            "sha256"        : sha,
                        })

                    registros_sha.append({
                        "dt_ingestao"   : DT_EXECUCAO,
                        "campanha"      : campanha,
                        "tipo"          : tipo,
                        "spreadsheet_id": spreadsheet_id,
                        "gid"           : gid,
                        "aba"           : nome_aba,
                        "sha256"        : sha,
                        "qtd_linhas"    : int(len(df_conteudo)),
                        "header_row"    : int(linha_header),
                        "mime_type"     : mime_type,
                    })

                    nome_arq = sanitizar_nome_arquivo(f"{campanha}_{tipo}_{spreadsheet_id}")
                    nome_sheet = sanitizar_nome_arquivo(nome_aba)
                    arquivo_csv = exportar_csv(df=df_conteudo, pasta=CSV_FOLDER,
                                               gid=nome_arq, nome_aba=nome_sheet)

                    blob_name = (f"{GCS_PREFIX}/raw/"
                                 f"dt={DT_EXECUCAO.strftime('%Y%m%d')}/"
                                 f"{nome_arq}/"
                                 f"{nome_sheet}_{sha[:8]}.csv")   # sha no nome: 2 execuções no dia não se sobrescrevem
                    gcs_uri = upload_csv_para_gcs(credentials=creds, bucket_name=GCS_BUCKET,
                                                  arquivo_local=arquivo_csv, blob_name=blob_name)
                    print(f"[{detalhe}] {nome_aba} -> {gcs_uri}")

                    registros_controle.append(novo_controle(**ctx_aba, status="ATUALIZADA",
                                              detalhes=f"{detalhe}; sha256={sha}; linhas={len(df_conteudo)}",
                                              arquivo_csv=arquivo_csv))

                except Exception as e:
                    # erro numa aba não derruba as demais
                    print(f"ERRO na aba '{nome_aba}' ({spreadsheet_id}): {type(e).__name__}: {e}")
                    registros_controle.append(novo_controle(**ctx_aba, status="ERRO",
                                              detalhes=f"{type(e).__name__}: {e}"))

    append_registros(registros_controle, ARQ_CONTROLE)

    # ---------- 5) Cargas no BigQuery ----------
    # Sem try/except engolindo erro: se a bronze falhar o job deve falhar (e a tabela de SHA NÃO é gravada,
    # senão a aba ficaria marcada como "já enviada" sem estar na bronze).
    try:
        data_ref = DT_EXECUCAO.strftime("%Y%m%d")
        upload_csv_para_gcs(credentials=creds, bucket_name=GCS_BUCKET, arquivo_local=ARQ_CONTROLE,
                            blob_name=f"{GCS_PREFIX}/monitoramento/dt={data_ref}/{os.path.basename(ARQ_CONTROLE)}")
    except Exception as e:
        print(f"Falha upload monitoramento p/ GCS: {e}")

    # 5.1 bronze primeiro...
    if registros_bronze:
        df_bronze = pd.DataFrame(registros_bronze)
        df_bronze["gid"] = df_bronze["gid"].fillna("").astype(str)
        print(f"Bronze: {df_bronze.shape}")
        carregar_dataframe(df=df_bronze, tabela=TB_BRONZE, creds=creds, project_id=PROJECT_ID)

        # 5.2 ...depois os SHAs (só quem realmente subiu)
        carregar_dataframe(df=pd.DataFrame(registros_sha), tabela=TB_SHA, creds=creds, project_id=PROJECT_ID)
    else:
        print("Nenhuma aba nova/alterada. Bronze não atualizada.")

    # 5.3 cadastro e monitoramento
    if cadastros_bq:
        carregar_dataframe(df=pd.concat(cadastros_bq, ignore_index=True), tabela=TB_CADASTRO,
                           creds=creds, project_id=PROJECT_ID)

    df_monitoramento = pd.read_csv(ARQ_CONTROLE, sep=";", dtype=str)
    df_monitoramento["dt_leitura"] = pd.to_datetime(df_monitoramento["dt_leitura"], utc=True, errors="coerce")
    df_monitoramento["gid"] = df_monitoramento["gid"].fillna("").astype(str)
    carregar_dataframe(df=df_monitoramento, tabela=TB_MONITORAMENTO, creds=creds, project_id=PROJECT_ID)

    if os.path.exists(ARQ_CONTROLE):
        os.remove(ARQ_CONTROLE)


if __name__ == "__main__":
    main()
