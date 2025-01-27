import typing
from fastapi import APIRouter, HTTPException, Depends
from api.dtos.responses_dtos import LLMClassificationResponse
from api.dtos.requests_dtos import LLMClassificationPreviewPayload
from api.config.logger import logger
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
from core.repositories.llm_repository import LLMRepository
from factories.repositories.elasticsearch_repository_factory import get_elasticsearch_repository
from factories.repositories.query_repository_factory import get_query_repository
from factories.repositories.llm_repository_factory import get_llm_repository
from services.elasticsearch_service import ElasticsearchException
from core.cases.get_classification_response import GetClassificationResponseCase
from api.dtos.responses_dtos import LLMPromptResponse
from api.dtos.requests_dtos import LLMPromptPreviewPayload
from core.cases.get_prompt_response import GetPromptResponseCase


llm_router = APIRouter()

@llm_router.post(
        '/classification',
        response_model=LLMClassificationResponse,
        response_model_exclude_none=True
    )
async def get_classification_ipcva(
    parameters: LLMClassificationPreviewPayload,
    es_repository: ElasticsearchRepository = Depends(
        get_elasticsearch_repository),
    query_repository: Query = Depends(
        get_query_repository
    ),
    llm_repository: LLMRepository = Depends(
        get_llm_repository
    )
) -> LLMClassificationResponse:
    try:
        llm_case = GetClassificationResponseCase(
            es_repository=es_repository,
            query_repository=query_repository,
            llm_repository=llm_repository,
            index_pattern=parameters.index_pattern,
            since_date=parameters.since_date,
            to_date=parameters.to_date,
            extra_args=parameters.filters,
            update_field= parameters.update_field,
            task_key= parameters.task_key,
            prompt=parameters.prompt
        )
        response = await llm_case()
        return response
    except ElasticsearchException as error:
        logger.error(f"ElasticError: {error}")
        raise HTTPException(status_code=404, detail=f"{error}")
    except Exception as error:
        logger.error(f"{type(error)}: {error}")
        raise HTTPException(status_code=500, detail="It seems that there is not enough data to build topics")


@llm_router.post(
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
        llm_case = GetPromptResponseCase(
            llm_repository=llm_repository,
            prompt=parameters.prompt
        )
        response = await llm_case()
        return response
    except Exception as error:
        logger.error(f"{type(error)}: {error}")
        raise HTTPException(status_code=500, detail="It seems that IA is not available right now. Please try again later.")
