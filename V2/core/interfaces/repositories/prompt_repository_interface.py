import typing
from abc import ABC, abstractmethod
from V2.api.dtos.prompt_dto import PromptRequest


class PromptRepositoryInterface(ABC):
    @abstractmethod
    async def execute_prompt(
        self, request: PromptRequest
    ) -> typing.Dict[str, typing.Any]:
        """
        Executes a prompt request and returns the response from the LLM.
        """
        pass
