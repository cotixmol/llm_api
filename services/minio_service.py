from minio import Minio
from minio.error import S3Error
import logging
import os


class MinIOException(Exception):
    pass


class MinIOClient:

    def __init__(self, minio_endpoint: str, minio_access_key: str,
                 minio_secret_key: str) -> None:
        self.client = Minio(endpoint=minio_endpoint,
                            access_key=minio_access_key,
                            secret_key=minio_secret_key,
                            secure=False)

    def get_file(self, bucket: str, file: str) -> any:
        object = self.client.get_object(bucket_name=bucket, object_name=file)
        return object

    def update_model(self, model_name: str, bucket: str) -> bool:
        logging.info(f"Updating model {model_name}")
        model_path = os.path.join(f"{os.getcwd()}/models/",
                                  f"{model_name}.pickle")
        if os.path.isfile(model_path):
            logging.info("Model already exist")
            return True
        try:
            model_file = self.get_file(bucket=bucket,
                                       file=f"{model_name}.pickle")
            with open(model_path, 'wb') as f:
                f.write(model_file.read())
            logging.info("Model updated")
            return True
        except S3Error as error:
            logging.error(f"{error}")
            raise MinIOException(error)
