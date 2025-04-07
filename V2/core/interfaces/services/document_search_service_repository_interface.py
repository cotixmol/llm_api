from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from V2.api.dtos.classification_dto import ClassificationRequest


class DocumentSearchServiceRepositoryInterface(ABC):
    @abstractmethod
    def create_query(self, request: ClassificationRequest) -> dict:
        pass

    @abstractmethod
    async def get_documents(
        self, index_pattern: str, query_body: dict, max_docs: Optional[int] = None
    ) -> List[Dict]:
        pass

    @abstractmethod
    async def update_documents(
        self, docs: List[Dict], index_pattern: str, field: str
    ) -> None:
        pass
