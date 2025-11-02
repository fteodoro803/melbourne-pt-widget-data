from config import MyFile, IS_CLOUD, BUCKET_NAME
from google.cloud import storage


def upload_file_to_cloud_storage(file: MyFile) -> None:
    """Helper that works both locally and in cloud, can be used for testing."""

    if not IS_CLOUD:
        print(f"[LOCAL MODE] Would upload {file}")
        return

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob: storage.Blob = bucket.blob(file.name)
    blob.upload_from_filename(file.path)
    print(f"Uploaded {file} to {BUCKET_NAME}")

def upload_string_to_cloud_storage(output_file: str, string: str) -> None:
    if not IS_CLOUD:
        print(f"[LOCAL MODE] Would upload {output_file}")
        return

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob: storage.Blob = bucket.blob(output_file)
    blob.upload_from_string(string, content_type="text/html")
    print(f"Uploaded {output_file} to {BUCKET_NAME}")