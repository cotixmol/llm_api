from typing import List, Dict
from V2.api.dtos.classification_dto import ClassificationRequest
from V2.core.interfaces.repositories.classification_repository_interface import (
    ClassificationRepositoryInterface,
)
from V2.core.interfaces.services.document_search_service_repository_interface import (
    DocumentSearchServiceRepositoryInterface,
)
from V2.core.interfaces.services.llm_service_repository_interface import (
    LLMServiceRepositoryInterface,
)


class ClassificationRepository(ClassificationRepositoryInterface):
    def __init__(
        self,
        document_search_service_repository: DocumentSearchServiceRepositoryInterface,
        llm_service_repository: LLMServiceRepositoryInterface,
    ):
        self.document_search_service_repository = document_search_service_repository
        self.llm_service_repository = llm_service_repository

    async def fetch_documents(self, payload: ClassificationRequest) -> List[Dict]:
        pass

    async def classify_documents(
        self, payload: ClassificationRequest, docs: List[Dict]
    ) -> List[Dict]:
        pass
