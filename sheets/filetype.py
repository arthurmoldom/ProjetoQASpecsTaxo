from googleapiclient.discovery import build


def obter_info_arquivo(file_id,creds):
#    print(f"(i)Consultando arquivo: {file_id}")
    drive = build(        "drive",        "v3",        credentials=creds    )
#    print(f"(m)Conectado para download de Excel do {file_id}")
    arquivo = drive.files().get(fileId=file_id,fields="id,name,mimeType",supportsAllDrives=True).execute()
    print(f"(f)Consultando arquivo: {arquivo}")
    return drive.files().get(fileId=file_id,fields="id,name,mimeType",supportsAllDrives=True).execute()