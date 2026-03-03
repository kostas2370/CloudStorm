import io
import zipfile
import logging

from django.conf import settings
from azure.storage.blob import BlobServiceClient

logger = logging.Logger("CloudStorm Logger")


def download_group_zip(group):
    blob_service_client = BlobServiceClient.from_connection_string(
        settings.AZURE_CONNECTION_STRING
    )
    container = settings.AZURE_CONTAINER

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in group.files.all():
            blob_path = file.file.name
            try:
                blob_client = blob_service_client.get_blob_client(
                    container=container, blob=blob_path
                )
                file_data = blob_client.download_blob().readall()
                filename = file.name or blob_path.split("/")[-1]
                zf.writestr(filename, file_data)
            except Exception as e:
                logger.error(f"Error downloading blob {blob_path}: {e}")

    zip_buffer.seek(0)
    return zip_buffer
