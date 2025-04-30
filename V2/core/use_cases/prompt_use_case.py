from V2.api.dtos.prompt_dto import PromptRequest, PromptResponse, PromptMessageItem
from V2.core.interfaces.repositories.prompt_repository_interface import (
    PromptRepositoryInterface,
)


class PromptUseCase:
    """
    Use case for handling prompt requests.
    This class is responsible for orchestrating the prompt execution process.
    """

    def __init__(self, prompt_repository: PromptRepositoryInterface):
        self.prompt_repository = prompt_repository

    async def execute(self, request: PromptRequest) -> PromptResponse:
        """
        Executes the prompt request by delegating to the repository.
        """
        try:
            prompt_result = await self.prompt_repository.execute_prompt(request)
        except Exception as e:
            raise ValueError(f"Failed to execute prompt: {str(e)}")
        print(f"[DEBUG] Prompt result: {prompt_result}")

        #append response to previous messages
        messages_list = request.messages_list
        messages_list.append(
            PromptMessageItem(
                role="assistant",
                content=prompt_result[0],
            )
        )

        return PromptResponse(
            messages_list=messages_list,
        )