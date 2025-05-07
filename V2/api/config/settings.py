import yaml
import os
from V2.core.services.storage_service.minio_service import MinIOClient
from V2.api.config.secrets import secrets

VERSION = open("VERSION").read().strip()

minio_client = MinIOClient(
    minio_endpoint=secrets.MINIO_URL,
    minio_access_key=secrets.MINIO_ACCESS_KEY,
    minio_secret_key=secrets.MINIO_SECRET_KEY,
)


def load_settings():
    with open(secrets.CONFIG_PATH, "r") as file:
        full_config = yaml.safe_load(file)

    config_type = os.getenv("CONFIG_TYPE", "gpu_full_1")

    return full_config[config_type]


node_config = load_settings()
