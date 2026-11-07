###VIA PIP/REQUIREMENTS
from datetime import datetime, timezone
import pandas                   as pd
import os
import json
### Do Projeto
from config                     import (SPREADSHEET_ID,ARQ_CONTROLE,CSV_FOLDER,GCS_PREFIX,GCS_BUCKET, TB_MONITORAMENTO,TB_BRONZE,PROJECT_ID,TB_CADASTRO)
from auth.auth                  import get_credentials
from sheets.leitura             import ( abrir_planilha,ler_aba,ler_aba_excel,ler_aba_raw,ler_excel_raw)
from storage.controle_csv       import (append_registros)
from utils.sanitizacao          import (higienizar_dataframe,normalizar_colunas,sanitizar_nome_arquivo)
from storage.gcs                import (upload_csv_para_gcs)
from sheets.filetype            import (obter_info_arquivo)
from sheets.excel               import (baixar_excel)
from sheets.header_locator      import (localizar_header,aplicar_header)
from bq.carga                   import (carregar_dataframe)
from export.export_csv          import (exportar_csv)


def localizar_gid(planilha, gid):

    for worksheet in planilha.worksheets():

        if str(worksheet.id) == str(gid):
            return worksheet

    return None



def main():

    creds = get_credentials()
    print(type(creds))

    if hasattr(creds, "service_account_email"):
        print("SA:", creds.service_account_email)
    else:
        print("Sem atributo service_account_email")

    print("Abrindo planilha mestre...")

    planilha_mestre = abrir_planilha(
        SPREADSHEET_ID,
        creds
    )

    registros_controle  = []
    registros_bronze    = []
    cadastros_bq        = []
    for aba_cadastro in planilha_mestre.worksheets():

        nome_aba_cadastro = aba_cadastro.title

        print(            f"Aba:{nome_aba_cadastro}, gid:{aba_cadastro.id}"        )

        # ignora aba de formulário
        if nome_aba_cadastro.lower() == "form":
            continue

        try:

            df_cadastro = ler_aba(                aba_cadastro            )
            #print(df_cadastro.dtypes)
            #print(df_cadastro)
            #break

        except Exception as e:

            print(                f"Erro lendo cadastro {nome_aba_cadastro}: {e}"            )

            continue

        if df_cadastro.empty:

            print(                f"{nome_aba_cadastro} sem registros."            )

            continue
        df_cadastro_bq = df_cadastro.copy()
        df_cadastro_bq["dt_carga"] = (    datetime.now(timezone.utc))
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
                            [
                                "true",
                                "1",
                                "sim",
                                "yes",
                                "verdadeiro"
                            ]
                        )
                    ]   
#        print(df_cadastro)
        
        
        for _, row in df_cadastro.iterrows():
            
            

            spreadsheet_id          = str(row.get("ID da planilha", "")).strip()
            gid                     = str(row.get("Gid", "") ).strip()
            aba_esperada            = str(row.get("Aba", "")).strip()
            campanha                = str(row.get("Campanha", "")).strip()
            tipo                    = str(row.get("Tipo", "")).strip()
            status = "OK"
            detalhe = ""
            aba_encontrada = ""
            arquivo_csv = None

            
            if spreadsheet_id == "":

                status = "ERRO"
                detalhe = "ID da planilha vazio"

            else:

                try:
                    info_arquivo = obter_info_arquivo(spreadsheet_id,creds)
                    mime_type = (info_arquivo["mimeType"])
                    if (mime_type == "application/vnd.google-apps.spreadsheet"):
                        planilha_destino = abrir_planilha(spreadsheet_id,creds)
                        worksheet = localizar_gid(planilha_destino,gid)
                        if worksheet is None:
                            status = "ERRO"
                            detalhe = ("GID não encontrado")
                        else:
                            aba_encontrada = (worksheet.title)
                            df_raw = ler_aba_raw(worksheet)
                            linha_header = localizar_header(df_raw,tipo)
                            df_conteudo = aplicar_header(df_raw,linha_header,tipo)

                    elif (mime_type =="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
                        status = "INFO"
                        detalhe = ("Arquivo Excel processado")
                        caminho_excel = (f"tmp/xlsx/{spreadsheet_id}.xlsx")
                        os.makedirs("tmp/xlsx",exist_ok=True)
                        try:
                            baixar_excel(spreadsheet_id,caminho_excel,creds)             
                        except Exception as e:
                            status = "ERRO"
                            detalhe = (f"Falha download Excel: "f"{str(e)}")
                            registros_controle.append(
                                {"dt_leitura"       :datetime.now(timezone.utc),
                                "aba_cadastro"      :nome_aba_cadastro,
                                "campanha"          :campanha,
                                "tipo"              :tipo,
                                "spreadsheet_id"    :spreadsheet_id,
                                "gid"               :gid,
                                "aba_esperada"      :aba_esperada,
                                "aba_encontrada"    :"",
                                "status"            :status,
                                "detalhes"          :detalhe,
                                "arquivo_csv"       :"",
                                "mime_type"         :mime_type
                                }
                            )

                            continue

                        aba_encontrada = (aba_esperada)
                        abas_excel = listar_abas_excel(caminho_excel)
                        if aba_esperada not in abas_excel:
                            status = "ERRO"
                            detalhe = (f"Aba não encontrada no Excel: "f"{aba_esperada}")
                            continue
                        
                        df_raw = ler_excel_raw(caminho_excel,aba_esperada)
                        linha_header = localizar_header(df_raw,tipo)
                        df_conteudo = aplicar_header(df_raw,linha_header)

                    else:
                        status = "ERRO"
                        detalhe = (f"Formato de arquivo não suportado: "f"{mime_type}")
                        continue
                    
                    nome_aba_real = aba_encontrada
                    

                    df_conteudo = higienizar_dataframe(df_conteudo)
                    df_conteudo = normalizar_colunas(df_conteudo)
                    idx = linha_header+1 ##pandas conta de 0
                    for _, linha in df_conteudo.iterrows():
                        
                        registros_bronze.append(
                                {
                                    "dt_carga" : datetime.now(timezone.utc),
                                    "campanha" : campanha,
                                    "tipo" : tipo,
                                    "spreadsheet_id": spreadsheet_id,
                                    "gid" : gid,
                                    "aba" : nome_aba_real,
                                    "payload_json" : json.dumps(    linha.to_dict(),    ensure_ascii=False),
                                    "source_row": idx + 1,
                                    "header_row":linha_header
                                }
                            )
                        idx += 1

#                    print(f"{nome_aba_real}: "f"{len(df_conteudo)} linhas")

                    nome_aba = f"{campanha}_{tipo}_{gid}"
                    nome_aba = sanitizar_nome_arquivo(nome_aba )

                    nome_sheet = str(nome_aba_real)
                    nome_sheet = sanitizar_nome_arquivo(nome_sheet)
                                
#                    print(f"ANTES EXPORT {nome_aba}")
#                    print("CSV_FOLDER =", CSV_FOLDER)
#                    print("worksheet.title =", repr(nome_sheet))
#                    print("nome_aba =", repr(nome_aba))
                    arquivo_csv = exportar_csv(
                    df=df_conteudo,
                    pasta=CSV_FOLDER,
                    gid=nome_aba,
                    nome_aba=nome_sheet
                    )
                    print(f"DEPOIS EXPORT {nome_aba}")
                    if (
                        aba_encontrada
                        !=
                        aba_esperada
                    ):

                        status = "ALERTA"
                        detalhe = (
                            "Aba renomeada"
                        )

                    data_ref = datetime.now(timezone.utc).strftime("%Y%m%d" )

#                    print(f'{data_ref} Enviar para GCS')
                    blob_name = (
                        f"{GCS_PREFIX}/raw/"
                        f"dt={data_ref}/"
                        f"{nome_aba}/"
                        f"{nome_sheet}.csv"
                    )
#                    print("nome_aba =", repr(nome_aba))
#                    print("worksheet.title =", repr(nome_aba_real))
#                    print("nome_sheet =", repr(nome_sheet))
#                    print(f"{GCS_PREFIX}")
                    gcs_uri = upload_csv_para_gcs(
                        credentials=creds,
                        bucket_name=GCS_BUCKET,
                        arquivo_local=arquivo_csv,
                        blob_name=blob_name
                    )

                    print(
                        f"Enviado para {gcs_uri}"
                    )

                except Exception as e:
                    print("\nERRO REAL:")
                    print(type(e))
                    print(str(e))

                    raise
            registros_controle.append(
                {"dt_leitura"    :datetime.now(timezone.utc),
                 "aba_cadastro"  :nome_aba_cadastro,
                 "campanha"      :campanha,
                 "tipo"          :tipo,
                 "spreadsheet_id":spreadsheet_id,
                 "gid"           :str(gid),
                 "aba_esperada"  :aba_esperada,
                 "aba_encontrada":aba_encontrada,
                 "status"        :status,
                 "detalhes"      :detalhe, 
                 "arquivo_csv"   :arquivo_csv,
                 "mime_type"     :mime_type
                }
            )

    append_registros(registros_controle, ARQ_CONTROLE)
    
    try:
        data_ref = datetime.now(timezone.utc).strftime("%Y%m%d")
        
        
        
        blob_monitoramento = (f"{GCS_PREFIX}/monitoramento/"
                            f"dt={data_ref}/"
                            f"{os.path.basename(ARQ_CONTROLE)}"
                            )
        
        
#        print("Enviando monitoramento para storage")


        gcs_monitoramento = upload_csv_para_gcs(
                                credentials=creds,
                                bucket_name=GCS_BUCKET,
                                arquivo_local=ARQ_CONTROLE,
                                blob_name=blob_monitoramento)
#        print(f"Monitoramento enviado: "f"{gcs_monitoramento}")
#        print(f"{len(registros_controle)} registros processados")
        df_monitoramento = pd.read_csv(ARQ_CONTROLE,    sep=";")
        df_monitoramento["dt_leitura"] = pd.to_datetime(    df_monitoramento["dt_leitura"],    utc=True,    errors="coerce")
        df_monitoramento["gid"] = (    df_monitoramento["gid"]    .fillna("")    .astype(str))


        df_bronze = pd.DataFrame(registros_bronze)
        df_bronze["gid"] = (    df_bronze["gid"]    .fillna("")    .astype(str))

#        print(f"Bronze: {df_bronze.shape}")
#        print(df_bronze.head(1))
#        print(type(df_bronze.iloc[0]["payload_json"]))
        df_cadastro_final = pd.concat(cadastros_bq,ignore_index=True)
#        print(f"Cadastro: {df_cadastro_final.shape}")
        print("------tipos----------")
        print(df_bronze.dtypes)
        print(df_monitoramento.dtypes)
        print(df_cadastro_final.dtypes)
        print("------tipos----------")
        print(f"Salvando no BigQuery")
        carregar_dataframe(
            df=df_cadastro_final,
            tabela=TB_CADASTRO,
            creds=creds,
            project_id=PROJECT_ID
        )
        carregar_dataframe(
                df=df_monitoramento,
                tabela=TB_MONITORAMENTO,    
                creds=creds,
                project_id=PROJECT_ID
        )

        carregar_dataframe(
            df=df_bronze,
            tabela=TB_BRONZE,
            creds=creds,
            project_id=PROJECT_ID
            )

       
        if os.path.exists(ARQ_CONTROLE):
            os.remove(ARQ_CONTROLE)

    except Exception as e:
        print(      f"Falha upload monitoramento: "
                    f"{str(e)}"    )

if __name__ == "__main__":
    main()
