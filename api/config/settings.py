from dotenv import load_dotenv
from services.minio_service import MinIOClient
from api.config.secrets import settings as s
VERSION = open("VERSION").read().strip()

load_dotenv('../.env')


minio_client = MinIOClient(
    minio_endpoint= s.MINIO_URL, 
    minio_access_key= s.MINIO_ACCESS_KEY,
    minio_secret_key=s.MINIO_SECRET_KEY
)
