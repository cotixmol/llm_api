from V2.utils.logger import logger
from api.dtos.responses_dtos import VectorizedSearchResponse
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
from services.elasticsearch_service import ElasticsearchException
from core.repositories.embedding_repository import EmbeddingRepository
import iso8601


class GetVectorizedSearchResponseCase:
    def __init__(
        self,
        es_repository: ElasticsearchRepository,
        query_repository: Query,
        embedding_repository: EmbeddingRepository,
        index_pattern: str,
        since_date: str,
        to_date: str,
        # extra_args: dict,
        max_ndocs: int,
        input_question: str = None,
        query: str = None,
    ):

        since_iso_time = iso8601.parse_date(since_date).isoformat()
        to_iso_time = iso8601.parse_date(to_date).isoformat()
        self.query_repository = query_repository
        self.es_repository = es_repository
        self.embedding_repository = embedding_repository
        self.index_pattern = index_pattern
        self.since_iso_time = since_iso_time
        self.to_iso_time = to_iso_time
        # self.extra_args = extra_args
        self.max_ndocs = max_ndocs
        self.query = query
        self.input_question = input_question

    async def __call__(self) -> VectorizedSearchResponse:
        ### CREATE EMBEDDING QUESTION ###
        if not self.input_question:
            raise ValueError("Input question is required for vectorized search")

        question_embedding = await self.embedding_repository.get_embedding(
            self.input_question
        )
        question_embedding = question_embedding.cpu().tolist()

        ### CREATE QUERY ###
        knn_query = Query()
        knn_query.set_date_range(self.since_iso_time, self.to_iso_time)
        if self.query:
            knn_query.set_query_string(query_string=self.query)
        knn_query.set_knn_query(
            query_vector=question_embedding, k=1000, num_candidates=10000
        )
        try:
            ### SEARCH DOCUMENTS ###
            response = await self.es_repository.get_vectorized_search_data(
                index_pattern=self.index_pattern,
                query=knn_query,
                max_ndocs=self.max_ndocs,
            )

            # PROCESS RESPONSE
            processed_response = []
            for hit in response.hits:
                source = hit["_source"]
                processed_response.append(source.get("content"))

        except ElasticsearchException as ese:
            logger.error(f"Error en Elasticsearch: {ese}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado durante la búsqueda vectorizada: {e}")
            raise
        finally:
            ### CLOSE CLIENT ###
            await self.es_repository.close_client()
            logger.info(f"Client closed")

        return VectorizedSearchResponse(response=processed_response)
