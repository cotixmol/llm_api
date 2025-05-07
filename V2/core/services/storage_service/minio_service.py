from minio import Minio
from minio.error import S3Error
import logging
import os


class MinIOException(Exception):
    pass


class MinIOClient:

    def __init__(
        self, minio_endpoint: str, minio_access_key: str, minio_secret_key: str
    ) -> None:
        self.client = Minio(
            endpoint=minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False,
        )

    def update_model_folder(self, bucket: str, model_name: str) -> None:
        logging.info(f"Updating model {model_name}")

        # folder that stores the models
        models_path = os.path.join(f"{os.getcwd()}/models")

        logging.info(f"Model path {models_path}")
        # model folder path
        folder_path = os.path.join(f"{models_path}/", f"{model_name}")
        logging.info(f"Folder path {folder_path}")
        if os.path.isdir(folder_path) or os.path.isfile(folder_path):
            logging.info("Model already exist")
            return True
        try:
            os.makedirs(folder_path, exist_ok=True)
            for item in self.client.list_objects(
                bucket, prefix=model_name, recursive=True
            ):
                # file destination path in model folder
                item_path = os.path.join(f"{models_path}/", f"{item.object_name}")
                self.client.fget_object(bucket, item.object_name, item_path)
            logging.info("Model updated")
            return True
        except S3Error as error:
            logging.error(f"{error}")
            raise MinIOException(error)
