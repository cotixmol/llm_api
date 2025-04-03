from typing import List, Dict
from V2.api.dtos.classification_dto import ClassificationRequest
from V2.core.interfaces.repositories.classification_repository_interface import (
    ClassificationRepositoryInterface,
)
from V2.core.interfaces.services.document_search_service_repository_interface import (
    DocumentSearchServiceInterface,
)
from V2.core.interfaces.services.llm_service_repository_interface import (
    LLMServiceRepositoryInterface,
)


class ClassificationRepository(ClassificationRepositoryInterface):
    def __init__(
        self,
        document_search_service_repository: DocumentSearchServiceInterface,
        llm_service_repository: LLMServiceRepositoryInterface,
    ):
        self.document_search_service_repository = document_search_service_repository
        self.llm_service_repository = llm_service_repository

    async def fetch_documents(self, payload: ClassificationRequest) -> List[Dict]:
        query_body = {
            "range": {
                "timestamp": {
                    "gte": payload.since_date,
                    "lte": payload.to_date,
                }
            },
            # Additional filter logic can go here.
        }
        docs = await self.document_search_service_repository.get_documents(
            payload.index_pattern, query_body, payload.max_ndocs
        )
        return docs

    async def classify_documents(
        self, payload: ClassificationRequest, docs: List[Dict]
    ) -> List[Dict]:
        results = await self.llm_service_repository.apply_prompt_classification(
            docs, payload.prompt
        )
        await self.document_search_service_repository.update_documents(
            results, payload.index_pattern, payload.update_field
        )
        return results
