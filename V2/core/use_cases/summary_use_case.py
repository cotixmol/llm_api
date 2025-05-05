from V2.api.dtos.summary_dto import (
    SummaryRequest,
    SummaryResponse,
)
from V2.core.interfaces.repositories.summary_repository_interface import (
    SummaryRepositoryInterface,
)


class SummaryUseCase:
    def __init__(self, summary_repository: SummaryRepositoryInterface):
        self.summary_repository = summary_repository

    async def execute(self, request: SummaryRequest) -> SummaryResponse:
        docs = await self.summary_repository.fetch_documents_for_summary(request)
        summary = await self.summary_repository.create_summary(docs)
        return SummaryResponse(response=summary)
