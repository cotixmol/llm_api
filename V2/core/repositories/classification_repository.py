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
from V2.api.dtos.classification_dto import BaseDocument


class ClassificationRepository(ClassificationRepositoryInterface):
    def __init__(
        self,
        document_search_service_repository: DocumentSearchServiceRepositoryInterface,
        llm_service_repository: LLMServiceRepositoryInterface,
    ):
        self.document_search_service_repository = document_search_service_repository
        self.llm_service_repository = llm_service_repository

    async def fetch_documents(
        self, request: ClassificationRequest
    ) -> List[BaseDocument]:
        """
        Retrieves documents via the document search repository. The conversion to BaseDocument is handled by the search service.
        """
        return await self.document_search_service_repository.get_documents(request)

    async def classify_documents(
        self, request: ClassificationRequest, docs: List[BaseDocument]
    ) -> List[dict]:
        """
        Delegates classification to the LLM service repository.
        Expects docs to be already converted to the agnostic BaseDocument type.
        """
        classification_results = await self.llm_service_repository.classify_document(
            request, docs
        )
        return classification_results
