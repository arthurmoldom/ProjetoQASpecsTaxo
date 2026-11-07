from googleapiclient.discovery import build


def obter_metadata_planilha(
    spreadsheet_id,
    creds
):

    drive = build(
        "drive",
        "v3",
        credentials=creds
    )

    arquivo = drive.files().get(
        fileId=spreadsheet_id,
        fields="id,name,modifiedTime"
    ).execute()

    return {
        "spreadsheet_id": arquivo["id"],
        "nome": arquivo["name"],
        "modified_time": arquivo["modifiedTime"]
    }