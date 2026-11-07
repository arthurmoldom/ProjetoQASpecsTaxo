from google.cloud import storage
from google.auth.transport.requests import Request


def upload_csv_para_gcs(
    credentials,
    bucket_name,
    arquivo_local,
    blob_name
):

    credentials.refresh(Request())

    client = storage.Client(
        project="project-f193f4f9-98c9-4623-ab5",
        credentials=credentials
    )

    bucket = client.bucket(
        bucket_name
    )

    blob = bucket.blob(
        blob_name
    )

    #print("INICIANDO UPLOAD")
#    blob.upload_from_string(
#    "teste python")
    blob.upload_from_filename(
            arquivo_local
    )

    #print("UPLOAD FINALIZADO")

    return (
        f"gs://{bucket_name}/{blob_name}"
    )