from V2.core.services.document_search_service.elastic_search_service import (
    ElasticsearchService,
)
from api.config.secrets import settings


def build_es_service() -> ElasticsearchService:
    return ElasticsearchService(
        elasticsearch_prt=settings.ES_PORT,
        elasticsearch_usr=settings.ES_USER,
        elasticsearch_psw=settings.ES_PASS,
        elasticsearch_cluster=settings.ES_CLUSTER_NODES,
        verify_certs=settings.ES_VERIFY_CERTS,
        max_retries=settings.ES_MAX_RETRIES,
        timeout=settings.ES_TIMEOUT,
    )
