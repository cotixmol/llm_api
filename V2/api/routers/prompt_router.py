from fastapi import APIRouter, Depends, HTTPException
from V2.api.dtos.prompt_dto import (
    PromptRequest,
    PromptResponse,
)
from V2.core.use_cases.prompt_use_case import PromptUseCase
from V2.core.factories.prompt_repository_factory import (
    build_prompt_repository,
)
from V2.core.interfaces.repositories.prompt_repository_interface import (
    PromptRepositoryInterface,
)

prompt_router_V2 = APIRouter()


@prompt_router_V2.post(
    "/prompt", response_model=PromptResponse
)
async def prompt_endpoint(
    request: PromptRequest,
    prompt_repository: PromptRepositoryInterface = Depends(
        build_prompt_repository
    ),
) -> PromptResponse:
    try:
        use_case = PromptUseCase(prompt_repository)
        return await use_case.execute(request)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
