from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMServiceRepositoryInterface(ABC):
    @abstractmethod
    async def classify_document(
        self, docs: List[Dict], prompt_args: dict
    ) -> List[Dict]:
        """
        Call the LLM to process the documents based on the prompt arguments.
        Should return the list of documents with classification updates.
        """
        pass

    @abstractmethod
    async def execute_prompt(
        self, prompt_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes a generic prompt request and returns the response.
        """
        pass
