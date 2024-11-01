import os
from dotenv import load_dotenv

load_dotenv('.env')

ELASTIC_PRT = os.environ.get("ELASTIC_PRT")
ELASTIC_USR = os.environ.get("ELASTIC_USR")
ELASTIC_PSW = os.environ.get("ELASTIC_PSW")
ELASTIC_IP = os.environ.get("ELASTIC_IP")
