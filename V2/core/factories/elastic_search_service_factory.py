from V2.core.services.document_search_service.elastic_search_service import (
    ElasticsearchService,
)


def build_es_service() -> ElasticsearchService:
    return ElasticsearchService(
        elasticsearch_prt=settings.ES_PORT,
        elasticsearch_usr=settings.ES_USER,
        elasticsearch_psw=settings.ES_PASS,
        elasticsearch_cluster=settings.ES_CLUSTER_NODES,
    )
