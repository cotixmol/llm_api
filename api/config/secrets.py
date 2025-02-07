import os
from dotenv import load_dotenv

load_dotenv('.env')

LOG_LEVEL = os.environ.get("LOG_LEVEL")

ELASTIC_PRT = os.environ.get("ELASTIC_PRT")
ELASTIC_USR = os.environ.get("ELASTIC_USR")
ELASTIC_PSW = os.environ.get("ELASTIC_PSW")
ELASTIC_CLUSTER = os.environ.get("ELASTIC_CLUSTER")
ELASTIC_PAGE_SIZE = os.environ.get("ELASTIC_PAGE_SIZE")
ELASTIC_TIMEOUT = os.environ.get("ELASTIC_TIMEOUT")

MINIO_URL=os.environ.get("MINIO_URL")
MINIO_ACCESS_KEY=os.environ.get("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY=os.environ.get("MINIO_SECRET_KEY")
MINIO_BUCKET=os.environ.get("MINIO_BUCKET")
MODEL_NAME=os.environ.get("MODEL_NAME")
