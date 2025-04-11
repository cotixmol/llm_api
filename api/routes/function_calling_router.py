from fastapi import APIRouter, HTTPException, Depends
from api.dtos.requests_dtos import FunctionCallingPayload  # Define this DTO
from api.dtos.responses_dtos import FunctionCallingResponse  # Define this DTO
from services.llm_vllm_service import LLMService
from core.cases.function_calling_case import FunctionCallingCase
from factories.services.llm_service_factory import get_llm_service

function_calling_router = APIRouter()

@function_calling_router.post(
    "/function_calling",
    response_model=FunctionCallingResponse,
    response_model_exclude_none=True
)
async def function_calling(
    parameters: FunctionCallingPayload,
    llm_service: LLMService = Depends(get_llm_service)
) -> FunctionCallingResponse:
    try:
        function_calling_case = FunctionCallingCase(
            llm_service=llm_service,
            tools=parameters.tools,
            tool_functions=parameters.tool_functions
        )

        response = await function_calling_case.execute(parameters.messages)
        return response
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))