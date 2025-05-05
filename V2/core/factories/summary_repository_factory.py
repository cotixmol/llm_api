from fastapi import Depends
from V2.core.services.document_search_service.elastic_search_service_repository import (
    ElasticSearchServiceRepositoryV2,
)
from V2.core.services.llm_service.vllm_service_repository import VLLMServiceRepositoryV2
from V2.core.repositories.classification_repository import SummaryRepository
from V2.core.factories.elastic_search_service_factory import build_es_service
from V2.core.factories.llm.llm_service_factory import (
    build_vllm_service,
)


def build_summary_repository():
    es_service = Depends(build_es_service)
    document_search_service_repository = ElasticSearchServiceRepositoryV2(
        es_service=es_service
    )

    llm_service = Depends(build_vllm_service)
    llm_service_repository = VLLMServiceRepositoryV2(llm_service=llm_service)

    return SummaryRepository(document_search_service_repository, llm_service_repository)
