import typing
from abc import ABC, abstractmethod
from V2.api.dtos.classification_dto import ClassificationRequest
from V2.api.dtos.classification_dto import BaseDocument
from typing import List, Dict


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

    @abstractmethod
    async def push_documents(
        self,
        request: ClassificationRequest,
        documents: List[BaseDocument],
        classification_list: List[Dict],
    ) -> None:
        pass
