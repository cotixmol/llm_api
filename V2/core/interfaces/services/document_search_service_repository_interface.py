from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from V2.api.dtos.classification_dto import ClassificationRequest
from V2.api.dtos.classification_dto import BaseDocument


class DocumentSearchServiceRepositoryInterface(ABC):
    @abstractmethod
    def create_query(self, request: ClassificationRequest) -> dict:
        pass

    @abstractmethod
    async def get_documents(
        self, request: ClassificationRequest, docs: List[BaseDocument]
    ) -> List[Dict]:
        pass

    @abstractmethod
    async def update_documents(
        self, request: ClassificationRequest, docs: List[BaseDocument], classification
    ) -> None:
        pass
