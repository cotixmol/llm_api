import typing
from fastapi import APIRouter, HTTPException, Depends
from api.dtos.responses_dtos import LLMClassificationResponse, LLMSummaryResponse, LLMPromptResponse, LLMTestResponse, FunctionCallingResponse
from api.dtos.requests_dtos import LLMClassificationPreviewPayload, LLMPromptPreviewPayload, LLMSummaryPreviewPayload, LLMTestPreviewPayload, FunctionCallingPayload
from V2.api.config.logger import logger
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
from core.repositories.llm_repository import LLMRepository
from factories.repositories.elasticsearch_repository_factory import get_elasticsearch_repository
from factories.repositories.query_repository_factory import get_query_repository
from factories.repositories.llm_repository_factory import get_llm_repository
from factories.services.llm_client_factory import get_llm_service
from services.elasticsearch_service import ElasticsearchException
from core.cases.get_classification_response import GetClassificationResponseCase
from core.cases.get_prompt_response import GetPromptResponseCase
from core.cases.get_summary_response import GetSummaryResponseCase
from core.cases.get_function_calling_response import GetFunctionCallingCase
from api.utils.dict_from_vllm_response import convert_request_outputs_to_dict

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
            prompt=parameters.prompt,
            valid_labels=parameters.valid_labels,
            max_ndocs=parameters.max_ndocs,
            batch_size=parameters.batch_size,
            query=parameters.query
        )
        response = await llm_case()
        return response
    except ElasticsearchException as error:
        logger.error(f"ElasticError: {error}")
        raise HTTPException(status_code=404, detail=f"{error}")
    except Exception as error:
        logger.error(f"{type(error)}: {error}")
        raise HTTPException(status_code=500, detail=str(error))


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
            prompt=parameters.prompt,
        )
        response = await llm_case()
        return response
    except Exception as error:
        logger.error(f"{type(error)}: {error}")
        raise HTTPException(status_code=500, detail="It seems that IA is not available right now. Please try again later.")


@llm_router.post(
        '/summary',
        response_model=LLMSummaryResponse,
        response_model_exclude_none=True
    )
async def get_llm_summary(
    parameters: LLMSummaryPreviewPayload,
    es_repository: ElasticsearchRepository = Depends(
        get_elasticsearch_repository),
    query_repository: Query = Depends(
        get_query_repository
    ),
    llm_repository: LLMRepository = Depends(
        get_llm_repository
    )
) -> LLMSummaryResponse:
    try:
        llm_case = GetSummaryResponseCase(
            es_repository=es_repository,
            query_repository=query_repository,
            llm_repository=llm_repository,
            index_pattern=parameters.index_pattern,
            since_date=parameters.since_date,
            to_date=parameters.to_date,
            extra_args=parameters.filters,
            max_ndocs=parameters.max_ndocs,
            prompt=parameters.prompt,
            query=parameters.query,
            summary_field=parameters.summary_field,
            batch_size=parameters.batch_size
        )
        response = await llm_case()
        return response
    except ElasticsearchException as error:
        logger.error(f"ElasticError: {error}")
        raise HTTPException(status_code=404, detail=f"{error}")
    except Exception as error:
        logger.error(f"{type(error)}: {error}")
        raise HTTPException(status_code=500, detail="It seems that IA is not available right now. Please try again later.")
    
@llm_router.post(
        '/test',
        response_model=LLMTestResponse,
        response_model_exclude_none=True
    )
async def get_llm_default_response(
    parameters: LLMTestPreviewPayload,
    llm_service: LLMRepository = Depends(
        get_llm_service
    )
) -> LLMTestResponse:
    try:
        model_response = await llm_service.test_model(prompt=parameters.prompt)
        dict_responses= convert_request_outputs_to_dict(model_response)   
        response = LLMTestResponse(response=dict_responses)

        return response
    except Exception as error:
        logger.error(f"{type(error)}: {error}")
        raise HTTPException(status_code=500, detail="Something went wrong.")


@llm_router.post(
    "/functioncalling",
    response_model=FunctionCallingResponse,
    response_model_exclude_none=True
)
async def function_calling(
    parameters: FunctionCallingPayload,
    llm_repository: LLMRepository = Depends(get_llm_repository),
    query_repository: Query = Depends(get_query_repository),
    es_repository: ElasticsearchRepository = Depends(get_elasticsearch_repository)
) -> FunctionCallingResponse:
    try:
        function_calling_case = GetFunctionCallingCase(
            llm_repository=llm_repository,
            user_input=parameters.user_input,
            es_repository=es_repository,
            query_repository=query_repository
            )

        response = await function_calling_case()
        return response
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))