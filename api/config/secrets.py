from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):

    # Worker configuration
    LOG_LEVEL: str
    MODEL_NAME: str

    # ElasticSerch variables used by elsticsearch service
    ELASTIC_CLUSTER: List[str]
    ELASTIC_PRT: str
    ELASTIC_USR: str
    ELASTIC_PSW: str
    ELASTIC_PAGE_SIZE: int

    # MinIO variables used by MinIO service
    MINIO_URL: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')


settings = Settings()
