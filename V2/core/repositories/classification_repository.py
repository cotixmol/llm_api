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

    async def fetch_documents(self, request: ClassificationRequest) -> List[Dict]:
        """
        Calls the document search repository's get_documents method,
        which internally handles building the Elasticsearch query.
        """
        documents = await self.document_search_service_repository.get_documents(request)
        return documents

    async def classify_documents(
        self, request: ClassificationRequest, docs: List[Dict]
    ) -> List[Dict]:
        """
        Calls the LLM service repository's classify_document method
        for each document.
        """
        classification_results = []
        for doc in docs:
            classification_result = await self.llm_service_repository.classify_document(
                request, doc, prompt_args=request.prompt_args
            )
            classification_results.append(classification_result)
        return classification_results
