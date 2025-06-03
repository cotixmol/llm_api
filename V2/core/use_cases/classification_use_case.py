from V2.api.dtos.classification_dto import (
    ClassificationRequest,
    ClassificationResponse,
)
from V2.core.interfaces.repositories.classification_repository_interface import (
    ClassificationRepositoryInterface,
)
from V2.api.dtos.common_dto import BaseDocument


class ClassificationUseCase:
    """
    Use case for handling classification requests.
    This class is responsible for orchestrating the classification process,
    including fetching documents (when necessary) and classifying them.
    """

    def __init__(self, classification_repository: ClassificationRepositoryInterface):
        self.classification_repository = classification_repository

    async def execute(self, request: ClassificationRequest) -> ClassificationResponse:

        #         documents = (
        #     BaseDocument(request.documents)
        #     if request.documents
        #     else await self.classification_repository.fetch_documents_for_classification(request)
        # )
        if request.documents:
            documents = [
                d if isinstance(d, BaseDocument) else BaseDocument(**d)
                for d in request.documents
            ]
        else:
            documents = (
                await self.classification_repository.fetch_documents_for_classification(
                    request
                )
            )

        classification_list = await self.classification_repository.classify_documents(
            request, documents
        )
        await self.classification_repository.push_classified_documents(
            request, documents, classification_list
        )

        return ClassificationResponse(
            total_docs=len(classification_list),
            updated_docs=sum(
                1
                for d in classification_list
                if d.get(request.update_field) is not None
            ),
        )
