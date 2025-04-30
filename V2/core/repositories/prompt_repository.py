from typing import List
from V2.api.dtos.prompt_dto import PromptRequest
from V2.core.interfaces.repositories.prompt_repository_interface import (
    PromptRepositoryInterface,
)
from V2.core.interfaces.services.llm_service_repository_interface import (
    LLMServiceRepositoryInterface,
)


class PromptRepository(PromptRepositoryInterface):
    def __init__(self, llm_service_repository: LLMServiceRepositoryInterface):
        """
        Initializes the PromptRepository with the LLM service repository.
        """
        self.llm_service_repository = llm_service_repository

    async def execute_prompt(
        self, request: PromptRequest
    ) -> List[str]:
        """
        Executes a prompt request by delegating to the LLM service repository.
        """

        messages_list = [{"role": message.role, "content": message.content} for message in request.messages_list]
        response = await self.llm_service_repository.execute_prompt(
            messages_list=messages_list,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            )
        return response