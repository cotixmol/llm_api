from typing import List
from V2.core.interfaces.services.document_search_service_repository_interface import (
    DocumentSearchServiceRepositoryInterface,
)
from V2.core.interfaces.services.llm_service_repository_interface import (
    LLMServiceRepositoryInterface,
)
from V2.api.dtos.common_dto import BaseDocument
from V2.core.interfaces.repositories.topics_repository_interface import (
    TopicsRepositoryInterface,
)
from V2.api.dtos.topics_dto import TopicsRequest


class TopicsRepository(TopicsRepositoryInterface):
    def __init__(
        self,
        document_search_service_repository: DocumentSearchServiceRepositoryInterface,
        llm_service_repository: LLMServiceRepositoryInterface,
    ):
        self.document_search_service_repository = document_search_service_repository
        self.llm_service_repository = llm_service_repository

    async def fetch_documents_for_topics(
        self, request: TopicsRequest
    ) -> List[BaseDocument]:
        """
        Retrieves documents via the document search repository. The conversion to BaseDocument is handled by the search service.
        """
        return await self.document_search_service_repository.get_documents(request)

    async def method2(self) -> None:
        pass

    async def method3(self) -> None:
        pass
