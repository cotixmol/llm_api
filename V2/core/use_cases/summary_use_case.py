from V2.api.dtos.classification_dto import (
    ClassificationRequest,
    ClassificationResponse,
)
from V2.core.interfaces.repositories.summary_repository_interface import (
    SummaryRepositoryInterface,
)


class SummaryUseCase:
    def __init__(self, summary_repository: SummaryRepositoryInterface):
        self.summary_repository = summary_repository

    async def execute(self, request: ClassificationRequest) -> ClassificationResponse:
        docs = await self.summary_repository.fetch_documents_for_summary(request)
