from api.dtos.responses_dtos import LLMPromptResponse
from core.repositories.llm_repository import LLMRepository

class GetPromptResponseCase:
    def __init__(
            self,
            llm_repository: LLMRepository,
            prompt: str, 
    ):
        self.llm_repository = llm_repository
        self.prompt = prompt

    async def __call__(self) -> LLMPromptResponse:      
        ### MAKE CLASSIFICATION ###
        prediction = await self.llm_repository.apply_prompt(prompt=self.prompt)

        return LLMPromptResponse(response=prediction)

