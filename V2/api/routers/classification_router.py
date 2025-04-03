from fastapi import APIRouter, Depends, HTTPException
from V2.api.dtos.classification_dto import (
    LLMClassificationRequest,
    LLMClassificationResponse,
)
from V2.core.use_cases.classification_use_case import ClassificationUseCase
from V2.core.factories.classification_repository_factory import get_classification_repo
from V2.core.interfaces.classification_repository_interface import (
    ClassificationRepositoryInterface,
)

router = APIRouter()


@router.post("/classification", response_model=LLMClassificationResponse)
async def classification_endpoint(
    request: LLMClassificationRequest,
    classification_repo: ClassificationRepositoryInterface = Depends(
        get_classification_repo
    ),
) -> LLMClassificationResponse:
    try:
        use_case = ClassificationUseCase(classification_repo)
        return await use_case.execute(request)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
