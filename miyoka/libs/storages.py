from pathlib import Path
from logging import Logger
import os
import zipfile
from google.cloud import storage
from google.cloud.exceptions import Conflict


def init_storage_client(project_id: str):
    return storage.Client(project=project_id)


class BaseStorageClient:
    def __init__(
        self,
        bucket_name: str,
        location: str,
        storage_client: storage.Client,
        logger: Logger,
        acl: str | None = None,
    ):
        self.bucket_name = bucket_name
        self.storage_client = storage_client
        self.location = location
        self.logger = logger

        if self.ensure_bucket(acl=acl):
            self.patch_cors_configuration()

    def ensure_bucket(self, acl: str | None = None) -> bool:
        try:
            self.storage_client.create_bucket(
                self.bucket_name,
                project=self.storage_client.project,
                location=self.location,
                # https://cloud.google.com/storage/docs/access-control/lists#predefined-acl
                predefined_acl=acl,
                predefined_default_object_acl=acl,
            )
            self.logger.info(f"Bucket {self.bucket_name} created.")
            return True
        except Conflict as ex:
            self.logger.info(f"Bucket {self.bucket_name} already exists. ex: {ex}")

        return False

    def upload_file(
        self,
        source_file_name,
        destination_blob_name,
        delete_original: bool,
    ):
        """Uploads a file to the bucket."""
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)

        self.logger.info(
            f"File {source_file_name} uploaded to {destination_blob_name}."
        )

        if delete_original:
            os.remove(source_file_name)

    def patch_cors_configuration(self):
        """Set a bucket's CORS policies configuration."""
        bucket = self.storage_client.get_bucket(self.bucket_name)
        bucket.cors = [
            {
                "origin": ["*"],
                "responseHeader": ["*"],
                "method": ["*"],
                "maxAgeSeconds": 3600,
            }
        ]
        bucket.patch()

        print(f"Set CORS policies for bucket {bucket.name} is {bucket.cors}")
        return bucket


class FrameStorage(BaseStorageClient):
    def __init__(self, workers: int, skip_upload: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workers = workers
        self.skip_upload = skip_upload

    def upload_as_zip(self, source_dir, dest_path):
        """Uploads a zip file to the bucket."""
        zip_path = "tmp.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, source_dir))

        self.upload_file(zip_path, dest_path, delete_original=True)

    def download_frames(self, replay_id, round_id) -> str:
        download_dir_path = f"download/{replay_id}/{round_id}/frames"

        if os.path.isdir(download_dir_path):
            return download_dir_path

        bucket = self.storage_client.bucket(self.bucket_name)

        blobs = self.storage_client.list_blobs(
            self.bucket_name, prefix=f"{replay_id}/{round_id}/frames"
        )

        print(f"blobs: {blobs}")

        paths = [blob.name for blob in blobs if blob.name.endswith(".zip")]
        print(f"paths: {paths}")

        for path in paths:
            source_blob_name = path
            destination_file_name = "tmp-frames.zip"
            blob = bucket.blob(source_blob_name)
            blob.download_to_filename(destination_file_name)

            print(
                "Downloaded storage object {} from bucket {} to local file {}.".format(
                    source_blob_name, self.bucket_name, destination_file_name
                )
            )

            print(f"Extracting zip {destination_file_name}...")
            with zipfile.ZipFile(destination_file_name, "r") as zip_ref:
                zip_ref.extractall(download_dir_path)

            os.remove(destination_file_name)

        return download_dir_path
