from V2.api.dtos.classification_dto import (
    ClassificationRequest,
    ClassificationResponse,
)
from V2.core.interfaces.repositories.classification_repository_interface import (
    ClassificationRepositoryInterface,
)
from V2.api.dtos.topics_dto import TopicsResponse
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

    async def execute(self, request: ClassificationRequest) -> ClassificationResponse:

        documents = await self.topics_repository.fetch_documents_for_topics(request)

        # We need to add all the other steps here for the topics use case

        return TopicsResponse()
