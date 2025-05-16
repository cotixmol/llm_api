from abc import ABC, abstractmethod
from V2.api.dtos.topics_dto import TopicsRequest
from V2.api.dtos.common_dto import BaseDocument
from typing import List


class TopicsRepositoryInterface(ABC):
    @abstractmethod
    async def fetch_documents_for_topics(
        self, request: TopicsRequest
    ) -> List[BaseDocument]:
        pass

    @abstractmethod
    async def method2(self) -> None:
        pass

    @abstractmethod
    async def method3(self) -> None:
        pass
