import typing
from fastapi import APIRouter, HTTPException, Depends
from api.dtos.requests_dtos import TopicPreviewPayload
from api.dtos.responses_dtos import BaseResponse
from V2.api.config.logger import logger
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
from core.repositories.llm_repository import LLMRepository
from factories.repositories.elasticsearch_repository_factory import get_elasticsearch_repository
from factories.repositories.query_repository_factory import get_query_repository
from factories.repositories.llm_repository_factory import get_llm_repository

from core.cases.get_topics_charts import GetTopicChartsCase
from services.elasticsearch_service import ElasticsearchException
from core.repositories.bertopic_repository import BertopicRepositoryException

topic_router = APIRouter()

@topic_router.post(
        '/',
        response_model=BaseResponse[None, typing.Dict],
        response_model_exclude_none=True
    )
async def get_topic_report(
    parameters: TopicPreviewPayload,
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
        case = GetTopicChartsCase(
            es_repository=es_repository,
            query_repository=query_repository,
            llm_repository=llm_repository,
            index_pattern=parameters.index_pattern,
            since_date=parameters.since_date,
            to_date=parameters.to_date,
            extra_args=parameters.filters,
            max_ndocs=parameters.max_ndocs
        )
        topics, n_docs = await case()
        return BaseResponse(data=None, chart=topics, n_docs=n_docs)
    except ElasticsearchException as error:
        logger.error(f"ElasticError: {error}")
        raise HTTPException(status_code=404, detail=f"{error}")
    except BertopicRepositoryException as error:
        logger.error(f"BertError {error}")
        raise HTTPException(status_code=400, detail=f"{error}")
    except Exception as error:
        logger.error(f"{type(error)}: {error}")
        raise HTTPException(status_code=500, detail="It seems that there is not enough data to build topics")

