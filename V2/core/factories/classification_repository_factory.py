from fastapi import Depends
from V2.core.services.document_search_service.elastic_search_service_repository import (
    ElasticSearchServiceRepositoryV2,
)
from V2.core.services.llm_service.llm_service_repository import LLMServiceRepositoryV2
from V2.core.repositories.classification_repository import ClassificationRepository
from V2.core.factories.elastic_search_service_factory import build_es_service
from V2.core.services.document_search_service.elastic_search_service import (
    ElasticsearchService,
)


def build_classification_repository():
    es_service: ElasticsearchService = Depends(build_es_service)
    document_search_service_repository = ElasticSearchServiceRepositoryV2(
        es_service=es_service
    )
    llm_service_repository = LLMServiceRepositoryV2()
    return ClassificationRepository(
        document_search_service_repository, llm_service_repository
    )
