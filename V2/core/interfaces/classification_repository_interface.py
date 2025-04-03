import typing
from abc import ABC, abstractmethod
from V2.api.dtos.classification_dto import LLMClassificationRequest


class ClassificationRepositoryInterface(ABC):
    @abstractmethod
    async def fetch_documents(
        self, payload: LLMClassificationRequest
    ) -> typing.List[dict]:
        pass

    @abstractmethod
    async def classify_documents(
        self, payload: LLMClassificationRequest, docs: typing.List[dict]
    ) -> typing.List[dict]:
        pass
