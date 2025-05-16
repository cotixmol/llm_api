from fastapi import APIRouter, Depends, HTTPException
from V2.api.dtos.topics_dto import (
    TopicsRequest,
    TopicsResponse,
)
from V2.core.interfaces.repositories.topics_repository_interface import (
    TopicsRepositoryInterface,
)
from V2.core.factories.topics_repository_factory import (
    build_topics_repository,
)
from V2.core.use_cases.topics_use_case import TopicsUseCase

topics_router_V2 = APIRouter()


@topics_router_V2.post("/topics", response_model=TopicsResponse)
async def topics_endpoint(
    request: TopicsRequest,
    topics_repository: TopicsRepositoryInterface = Depends(build_topics_repository),
) -> TopicsResponse:
    try:
        use_case = TopicsUseCase(topics_repository)
        return await use_case.execute(request)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
