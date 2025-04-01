import typing
from fastapi import APIRouter, HTTPException, Depends
from api.dtos.requests_dtos import VectorizedSearchPreviewPayload  # Asegúrate de definir este DTO
from api.dtos.responses_dtos import VectorizedSearchResponse
from api.config.logger import logger
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
from factories.repositories.elasticsearch_repository_factory import get_elasticsearch_repository
from factories.repositories.query_repository_factory import get_query_repository
from services.elasticsearch_service import ElasticsearchException
from core.cases.get_vectorized_search_response import GetVectorizedSearchResponseCase

vectorized_search_router = APIRouter()

@vectorized_search_router.post(
    '/',
    response_model=VectorizedSearchResponse,
    response_model_exclude_none=True
)
async def vectorized_search(
    parameters: VectorizedSearchPreviewPayload,
    es_repository: ElasticsearchRepository = Depends(get_elasticsearch_repository),
    query_repository: Query = Depends(get_query_repository)
) -> VectorizedSearchResponse:
    try:
        vectorized_search_case = GetVectorizedSearchResponseCase(
            es_repository=es_repository,
            query_repository=query_repository,
            index_pattern=parameters.index_pattern,
            since_date=parameters.since_date,
            to_date=parameters.to_date,
            extra_args=parameters.extra_args,
            max_ndocs=parameters.max_ndocs,
            input_question=parameters.input_question
        )

        vectorized_response = await vectorized_search_case()

        return vectorized_response
    except ElasticsearchException as error:
        logger.error(f"ElasticError: {error}")
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        logger.error(f"{type(error)}: {error}")
        raise HTTPException(status_code=500, detail="An error occurred during vectorized search")

