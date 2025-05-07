from V2.core.services.document_search_service.elastic_search_service import (
    ElasticsearchService,
)
from V2.api.config.secrets import secrets


# TODO: We can add verify_certs, max_retries and timeout to the secrets file
def build_es_service() -> ElasticsearchService:
    return ElasticsearchService(
        elasticsearch_prt=secrets.ELASTIC_PRT,
        elasticsearch_usr=secrets.ELASTIC_USR,
        elasticsearch_psw=secrets.ELASTIC_PSW,
        elasticsearch_cluster=secrets.ELASTIC_CLUSTER,
        verify_certs=False,
        max_retries=5,
        timeout=10,
    )
