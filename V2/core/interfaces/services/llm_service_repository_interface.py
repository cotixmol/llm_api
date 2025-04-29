from abc import ABC, abstractmethod
from typing import List, Dict
from V2.api.dtos.classification_dto import ClassificationRequest
from V2.api.dtos.classification_dto import BaseDocument


class LLMServiceRepositoryInterface(ABC):
    @abstractmethod
    async def classify_documents(
        self, request: ClassificationRequest, docs: List[BaseDocument]
    ) -> List[Dict]:
        """
        Call the LLM to process the documents based on the prompt arguments.
        Should return the list of documents with classification updates.
        """
        pass
