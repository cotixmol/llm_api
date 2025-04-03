from V2.api.dtos.classification_dto import (
    ClassificationRequest,
    ClassificationResponse,
)
from V2.core.interfaces.repositories.classification_repository_interface import (
    ClassificationRepositoryInterface,
)


class ClassificationUseCase:
    def __init__(self, classification_repository: ClassificationRepositoryInterface):
        self.classification_repository = classification_repository

    async def execute(self, request: ClassificationRequest) -> ClassificationResponse:
        documents = await self.classification_repository.fetch_documents(request)
        classification_results = (
            await self.classification_repository.classify_documents(request, documents)
        )
        return ClassificationResponse(
            total_docs=len(classification_results),
            updated_docs=sum(1 for doc in classification_results if doc.get("updated")),
        )
