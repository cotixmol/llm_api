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
from V2.core.interfaces.services.topics_modelling_service_repository_interface import (
    TopicsModellingServiceRepositoryInterface,
)
from V2.api.dtos.topics_dto import TopicsRequest, TopicsResponse


class TopicsRepository(TopicsRepositoryInterface):
    def __init__(
        self,
        document_search_service_repository: DocumentSearchServiceRepositoryInterface,
        llm_service_repository: LLMServiceRepositoryInterface,
        topics_modelling_repository: TopicsModellingServiceRepositoryInterface,
    ):
        self.document_search_service_repository = document_search_service_repository
        self.llm_service_repository = llm_service_repository
        self.topics_modelling_repository = topics_modelling_repository

    async def fetch_documents_for_topics(
        self, request: TopicsRequest
    ) -> List[BaseDocument]:
        """
        Retrieves documents via the document search repository. The conversion to BaseDocument is handled by the search service.
        """
        return await self.document_search_service_repository.get_documents(request)

    async def get_topics_for_topics(
        self, docs: List[BaseDocument], max_topics: int = 8
    ) -> list[dict]:
        """
        Delegates to the modelling adapter and returns raw topics.
        """
        return await self.topics_modelling_repository.get_topics(docs, max_topics)

    async def enrich_topics(self, topics: list[dict]) -> list[dict]:
        """
        Delegates to the LLM adapter to add names + summaries.
        """
        return await self.llm_service_repository.enrich_topics(topics)

    def build_topics_response(self, topics: list[dict]) -> TopicsResponse:
        """
        Pure mapping to your DTO – synchronous.
        """
        return TopicsResponse(topics=topics)
