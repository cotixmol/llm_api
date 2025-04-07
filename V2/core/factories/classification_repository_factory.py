from fastapi import Depends
from V2.core.services.document_search_service.elastic_search_service_repository import (
    ElasticSearchServiceRepositoryV2,
)
from V2.core.services.llm_service.llm_service_repository import LLMServiceRepositoryV2
from V2.core.repositories.classification_repository import ClassificationRepository


def build_classification_repository():
    document_search_service_repository = ElasticSearchServiceRepositoryV2(
        page_size=1000
    )
    llm_service_repository = LLMServiceRepositoryV2()
    return ClassificationRepository(
        document_search_service_repository, llm_service_repository
    )
