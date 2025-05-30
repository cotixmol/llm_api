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
    async def process_topics_pipeline(
        self, documents: List[BaseDocument]
    ):
        """
        Ejecuta el pipeline completo: modelado, enriquecimiento y mapeo a DTO.
        """
        pass

