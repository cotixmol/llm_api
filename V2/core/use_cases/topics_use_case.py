from V2.api.dtos.topics_dto import TopicsResponse, TopicsRequest
from V2.core.interfaces.repositories.topics_repository_interface import (
    TopicsRepositoryInterface,
)


class TopicsUseCase:
    """
    Use case for handling topics requests.
    This class is responsible for orchestrating the topics process,
    """

    def __init__(self, topics_repository: TopicsRepositoryInterface):
        self.topics_repository = topics_repository

    async def execute(self, request: TopicsRequest) -> TopicsResponse:

        documents = await self.topics_repository.fetch_documents_for_topics(request)

        topics = await self.topics_repository.get_topics_for_topics(documents)

        enriched_topics = await self.topics_repository.enrich_topics(topics)

        topics_response = self.topics_repository.build_topics_response(enriched_topics)

        return TopicsResponse()
