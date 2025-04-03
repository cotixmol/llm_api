from V2.api.dtos.classification_dto import (
    LLMClassificationRequest,
    LLMClassificationResponse,
)
from V2.core.interfaces.classification_repository_interface import (
    ClassificationRepositoryInterface,
)


class ClassificationUseCase:
    def __init__(self, repository: ClassificationRepositoryInterface):
        self.repository = repository

    async def execute(
        self, request: LLMClassificationRequest
    ) -> LLMClassificationResponse:
        documents = await self.repository.fetch_documents(request)
        classification_results = await self.repository.classify_documents(
            request, documents
        )
        return LLMClassificationResponse(
            total_docs=len(classification_results),
            updated_docs=sum(1 for doc in classification_results if doc.get("updated")),
        )
