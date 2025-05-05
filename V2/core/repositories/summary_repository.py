from typing import List, Dict
from V2.api.dtos.classification_dto import ClassificationRequest
from V2.core.interfaces.repositories.summary_repository_interface import (
    SummaryRepositoryInterface,
)
from V2.api.dtos.summary_dto import SummaryRequest

from V2.core.interfaces.services.document_search_service_repository_interface import (
    DocumentSearchServiceRepositoryInterface,
)
from V2.core.interfaces.services.llm_service_repository_interface import (
    LLMServiceRepositoryInterface,
)
from V2.api.dtos.common_dto import BaseDocument


class SummaryRepository(SummaryRepositoryInterface):
    def __init__(
        self,
        document_search_service_repository: DocumentSearchServiceRepositoryInterface,
        llm_service_repository: LLMServiceRepositoryInterface,
    ):
        self.document_search_service_repository = document_search_service_repository
        self.llm_service_repository = llm_service_repository

    async def fetch_documents_for_summary(
        self, request: SummaryRequest
    ) -> List[BaseDocument]:
        return await self.document_search_service_repository.get_documents(request)

    async def create_summary(
        self,
        documents: List[BaseDocument],
        request: SummaryRequest,
    ) -> Dict[str, str]:
        return await self.llm_service_repository.generate_summary(documents, request)
