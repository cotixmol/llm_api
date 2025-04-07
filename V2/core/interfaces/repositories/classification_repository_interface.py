import typing
from abc import ABC, abstractmethod
from V2.api.dtos.classification_dto import ClassificationRequest


class ClassificationRepositoryInterface(ABC):
    @abstractmethod
    async def fetch_documents(
        self, request: ClassificationRequest
    ) -> typing.List[dict]:
        pass

    @abstractmethod
    async def classify_documents(
        self, request: ClassificationRequest, docs: typing.List[dict]
    ) -> typing.List[dict]:
        pass
