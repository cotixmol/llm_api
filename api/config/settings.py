import yaml
import os
from services.minio_service import MinIOClient
from api.config.secrets import settings as s

VERSION = open("VERSION").read().strip()

minio_client = MinIOClient(
    minio_endpoint= s.MINIO_URL, 
    minio_access_key= s.MINIO_ACCESS_KEY,
    minio_secret_key=s.MINIO_SECRET_KEY
)

def load_config():
    with open(s.CONFIG_PATH, 'r') as file:
        full_config = yaml.safe_load(file)

    config_type = os.getenv("CONFIG_TYPE", "gpu_full_1")
    
    return full_config[config_type]

node_config = load_config()
