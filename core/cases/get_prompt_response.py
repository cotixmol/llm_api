from api.dtos.responses_dtos import LLMPromptResponse
from core.repositories.llm_repository import LLMRepository

class GetPromptResponseCase:
    def __init__(
            self,
            llm_repository: LLMRepository,
            prompts: list, 
            batch_size: int,
            fill_batches: bool
    ):
        self.llm_repository = llm_repository
        self.prompts = prompts
        self.batch_size = batch_size
        self.fill_batches = fill_batches

    async def __call__(self) -> LLMPromptResponse:      
        ### MAKE CLASSIFICATION ###
        prediction = await self.llm_repository.apply_prompts(prompts=self.prompts, 
                                                             batch_size=self.batch_size, 
                                                             fill_batches=self.fill_batches)

        return LLMPromptResponse(response=prediction)
    


