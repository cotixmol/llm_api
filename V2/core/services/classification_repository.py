from typing import List, Dict
from V2.api.dtos.classification_dto import LLMClassificationRequest
from V2.core.interfaces.classification_repository_interface import (
    ClassificationRepositoryInterface,
)
from V2.core.repositories.elasticsearch_repository import ElasticsearchRepositoryV2
from V2.core.repositories.llm_repository import LLMRepositoryV2


class ClassificationRepository(ClassificationRepositoryInterface):
    def __init__(
        self,
        es_repository: ElasticsearchRepositoryV2,
        llm_repository: LLMRepositoryV2,
    ):
        self.es_repository = es_repository
        self.llm_repository = llm_repository

    async def fetch_documents(self, payload: LLMClassificationRequest) -> List[Dict]:
        # Example of building an ES query from the request
        query_body = {
            "range": {
                "timestamp": {
                    "gte": payload.since_date,
                    "lte": payload.to_date,
                }
            },
            # Add filter logic to replicate older code
        }
        # Then call the local ES stub
        docs = await self.es_repository.get_documents(
            payload.index_pattern, query_body, payload.max_ndocs
        )
        return docs

    async def classify_documents(
        self, payload: LLMClassificationRequest, docs: List[Dict]
    ) -> List[Dict]:
        # Example classification using the local LLM stub
        results = await self.llm_repository.apply_prompt_classification(
            docs, payload.prompt
        )
        # Possibly also update docs in ES
        await self.es_repository.update_documents(
            results, payload.index_pattern, payload.update_field
        )
        return results
