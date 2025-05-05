from abc import ABC, abstractmethod
from V2.api.dtos.summary_dto import SummaryRequest
from V2.api.dtos.common_dto import BaseDocument
from typing import List, Dict


class SummaryRepositoryInterface(ABC):
    @abstractmethod
    def fetch_documents_for_summary(
        self, request: SummaryRequest
    ) -> List[BaseDocument]:
        pass

    @abstractmethod
    async def create_summary(
        self,
        documents: List[BaseDocument],
        request: SummaryRequest,
    ) -> Dict[str, str]:
        pass
