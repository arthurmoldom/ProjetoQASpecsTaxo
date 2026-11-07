import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def baixar_excel(file_id,nome_arquivo,creds):
    drive = build("drive","v3",credentials=creds)
    request = drive.files().get_media(fileId=file_id,supportsAllDrives=True)
    with open(nome_arquivo, "wb") as fh:
        downloader = MediaIoBaseDownload(fh,request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return nome_arquivo 