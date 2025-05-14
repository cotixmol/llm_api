from fastapi import APIRouter, Depends, HTTPException
from V2.api.dtos.summary_dto import SummaryResponse, SummaryRequest
from V2.core.interfaces.repositories.summary_repository_interface import (
    SummaryRepositoryInterface,
)
from V2.core.factories.summary_repository_factory import (
    build_summary_repository,
)
from V2.core.use_cases.summary_use_case import SummaryUseCase

summary_router_V2 = APIRouter()


@summary_router_V2.post(
    "/summary",
    response_model=SummaryResponse,
)
async def summary_endpoint(
    request: SummaryRequest,
    summary_repository: SummaryRepositoryInterface = Depends(build_summary_repository),
) -> SummaryResponse:
    try:
        use_case = SummaryUseCase(summary_repository)
        return await use_case.execute(request)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
