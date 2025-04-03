from fastapi import Depends
from V2.core.repositories.elasticsearch_repository import ElasticsearchRepositoryV2
from V2.core.repositories.llm_repository import LLMRepositoryV2
from V2.core.services.classification_repository import ClassificationRepository


def get_classification_repo():
    es_repo = ElasticsearchRepositoryV2(page_size=1000)
    llm_repo = LLMRepositoryV2()
    return ClassificationRepository(es_repo, llm_repo)
