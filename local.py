from services.minio_service import MinIOClient
from minio import Minio


client = Minio(
    endpoint="minio.reputacion.digital:9000",
    access_key="ds_user",
    secret_key="ds_secure_password"
)

lista_de_cosas = client.list_objects(bucket_name="ds-models")
for ob in list(lista_de_cosas):
    print(ob.__dict__)
