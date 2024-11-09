from dotenv import load_dotenv
from services.minio_service import MinIOClient
from api.config.secrets import (
    MINIO_URL,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY
)

VERSION = open("VERSION").read().strip()

load_dotenv('../.env')


minio_client = MinIOClient(
    minio_endpoint= MINIO_URL, 
    minio_access_key= MINIO_ACCESS_KEY,
    minio_secret_key=MINIO_SECRET_KEY
)
