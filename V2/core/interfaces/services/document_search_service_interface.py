from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class DocumentSearchServiceInterface(ABC):
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
