from abc import ABC, abstractmethod
from typing import List, Dict


class LLMServiceInterface(ABC):
    @abstractmethod
    async def apply_prompt_classification(
        self, docs: List[Dict], prompt_args: dict
    ) -> List[Dict]:
        """
        Call the LLM to process the documents based on the prompt arguments.
        Should return the list of documents with classification updates.
        """
        pass
