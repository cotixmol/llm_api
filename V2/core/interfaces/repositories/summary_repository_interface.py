from abc import ABC, abstractmethod
from V2.api.dtos.summary_dto import SummaryRequest
from V2.api.dtos.classification_dto import BaseDocument
from typing import List


class SummaryRepositoryInterface(ABC):
    @abstractmethod
    def fetch_documents(self, request: SummaryRequest) -> List[dict]:
        pass
