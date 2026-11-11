from google.auth import default
from google.auth import impersonated_credentials


TARGET_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/drive.readonly",  # necessário p/ files.get_media (baixar .xlsx)
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/devstorage.full_control"
]

TARGET_PRINCIPAL = (
    "integracao-api-dv360@project-f193f4f9-98c9-4623-ab5.iam.gserviceaccount.com"
)


def get_credentials():

    source_credentials, _ = default()

    target_credentials = impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=TARGET_PRINCIPAL,
        target_scopes=TARGET_SCOPES,
        lifetime=3600
    )

    return target_credentials