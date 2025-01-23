import typing
from fastapi import APIRouter, HTTPException, Depends
from api.dtos.responses_dtos import LLMPromptResponse
from api.dtos.requests_dtos import LLMPromptPreviewPayload
from api.config.logger import logger
from core.repositories.llm_repository import LLMRepository
from factories.repositories.lllm_repository_factory import get_llm_repository
from core.cases.get_prompt_response2 import GetPromptResponseCase2


llm_router2 = APIRouter()

@llm_router2.post(
        '/prompt',
        response_model=LLMPromptResponse,
        response_model_exclude_none=True
    )
async def get_llm_prompt(
    parameters: LLMPromptPreviewPayload,
    llm_repository: LLMRepository = Depends(
        get_llm_repository
    )
) -> LLMPromptResponse:
    try:
        llm_case = GetPromptResponseCase2(
            llm_repository=llm_repository,
            prompt=parameters.prompt
        )
        response = await llm_case()
        return response
    except Exception as error:
        logger.error(f"{type(error)}: {error}")
        raise HTTPException(status_code=500, detail="It seems that IA is not available right now. Please try again later.")
