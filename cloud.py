from config import MyFile, IS_CLOUD, BUCKET_NAME
from google.cloud import storage


def upload_file_to_cloud_storage(file: MyFile) -> None:
    upload_generic_to_cloud_storage(file.name, file.path)


def upload_generic_to_cloud_storage(name: str, content) -> None:
    """Helper that works both locally and in cloud, can be used for testing."""

    if not IS_CLOUD:
        print(f"[LOCAL MODE] Would upload {name}")
        return

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(name)
    blob.upload_from_filename(content)
    print(f"Uploaded {name} to {BUCKET_NAME}")