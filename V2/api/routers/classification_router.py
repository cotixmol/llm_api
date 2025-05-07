from fastapi import APIRouter, Depends, HTTPException
from V2.api.dtos.classification_dto import (
    ClassificationRequest,
    ClassificationResponse,
)
from V2.core.use_cases.classification_use_case import ClassificationUseCase
from V2.core.factories.classification_repository_factory import (
    build_classification_repository,
)
from V2.core.interfaces.repositories.classification_repository_interface import (
    ClassificationRepositoryInterface,
)

classification_router_V2 = APIRouter()


@classification_router_V2.post("/classification", response_model=ClassificationResponse)
async def classification_endpoint(
    request: ClassificationRequest,
    classification_repository: ClassificationRepositoryInterface = Depends(
        build_classification_repository
    ),
) -> ClassificationResponse:
    try:
        use_case = ClassificationUseCase(classification_repository)
        return await use_case.execute(request)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
