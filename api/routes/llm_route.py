import typing
from fastapi import APIRouter, HTTPException, Depends
from api.dtos.requests_dtos import TopicPreviewPayload
from api.dtos.responses_dtos import BaseResponse
from api.config.logger import logger
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
from core.repositories.llm_repository import LLMRepository
from factories.repositories.elasticsearch_repository_factory import get_elasticsearch_repository
from factories.repositories.query_repository_factory import get_query_repository
from factories.repositories.lllm_repository_factory import get_llm_repository

from core.cases.get_topics_charts import GetTopicChartsCase
from services.elasticsearch_service import ElasticsearchException
from core.repositories.bertopic_repository import BertopicRepositoryException


@topic_router.post(
        '/llm',
        #response_model=BaseResponse[None, typing.Dict],
        #response_model_exclude_none=True
    )
async def get_classification_ipcva(
    #parameters: TopicPreviewPayload,
    es_repository: ElasticsearchRepository = Depends(
        get_elasticsearch_repository),
    query_repository: Query = Depends(
        get_query_repository
    ),
    llm_repository: LLMRepository = Depends(
        get_llm_repository
    )
) -> BaseResponse:
    try:
        response = llm_repository.get_classification_ipcva()
        return response
    except ElasticsearchException as error:
        logger.error(f"ElasticError: {error}")
        raise HTTPException(status_code=404, detail=f"{error}")
    except Exception as error:
        logger.error(f"{type(error)}: {error}")
        raise HTTPException(status_code=500, detail="It seems that there is not enough data to build topics")
