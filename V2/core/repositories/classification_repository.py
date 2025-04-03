from typing import List, Dict
from V2.api.dtos.classification_dto import LLMClassificationRequest
from V2.core.interfaces.classification_repository_interface import (
    ClassificationRepositoryInterface,
)
from V2.core.interfaces.document_search_interface import DocumentSearchServiceInterface
from V2.core.interfaces.llm_service_interface import LLMServiceInterface


class ClassificationRepository(ClassificationRepositoryInterface):
    def __init__(
        self,
        search_service: DocumentSearchServiceInterface,
        llm_service: LLMServiceInterface,
    ):
        self.search_service = search_service
        self.llm_service = llm_service

    async def fetch_documents(self, payload: LLMClassificationRequest) -> List[Dict]:
        query_body = {
            "range": {
                "timestamp": {
                    "gte": payload.since_date,
                    "lte": payload.to_date,
                }
            },
            # Additional filter logic can go here.
        }
        docs = await self.search_service.get_documents(
            payload.index_pattern, query_body, payload.max_ndocs
        )
        return docs

    async def classify_documents(
        self, payload: LLMClassificationRequest, docs: List[Dict]
    ) -> List[Dict]:
        results = await self.llm_service.apply_prompt_classification(
            docs, payload.prompt
        )
        await self.search_service.update_documents(
            results, payload.index_pattern, payload.update_field
        )
        return results
