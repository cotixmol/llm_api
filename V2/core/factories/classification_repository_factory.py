from fastapi import Depends
from V2.core.services.elasticsearch_repository import ElasticsearchRepositoryV2
from V2.core.services.llm_repository import LLMRepositoryV2
from V2.core.repositories.classification_repository import ClassificationRepository


def build_classification_repository():
    es_repo = ElasticsearchRepositoryV2(page_size=1000)
    llm_repo = LLMRepositoryV2()
    return ClassificationRepository(es_repo, llm_repo)
