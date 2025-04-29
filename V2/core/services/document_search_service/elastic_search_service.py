from typing import List, Dict, Any, Iterable
import logging

from elasticsearch import AsyncElasticsearch, NotFoundError, BadRequestError
from elasticsearch.helpers import async_streaming_bulk
from V2.core.objects.elastic_search_object import ElasticSearchResponse


class ElasticsearchException(RuntimeError):
    """Raised when any ES‑specific operation fails."""


class ElasticsearchService:
    """
    Async wrapper around the official Elasticsearch client.
    """

    def __init__(
        self,
        elasticsearch_prt: int,
        elasticsearch_usr: str,
        elasticsearch_psw: str,
        elasticsearch_cluster: List[str],
        verify_certs: bool = False,
        max_retries: int = 5,
        timeout: int = 10,
        retry_on_timeout: bool = True,
    ) -> None:

        self._elasticsearch_prt = elasticsearch_prt
        self._elasticsearch_usr = elasticsearch_usr
        self._elasticsearch_psw = elasticsearch_psw
        self._elasticsearch_cluster = elasticsearch_cluster
        self._verify_certs = verify_certs
        self._max_retries = max_retries
        self._timeout = timeout
        self._retry_on_timeout = retry_on_timeout

        self._client = AsyncElasticsearch(
            hosts=[
                f"https://{node}:{ self._elasticsearch_prt}"
                for node in self._elasticsearch_cluster
            ],
            http_auth=(self._elasticsearch_usr, self._elasticsearch_psw),
            verify_certs=self._verify_certs,
            retry_on_timeout=self._retry_on_timeout,
            max_retries=self._max_retries,
        )

    # -------------------- SEARCH -------------------- #
    async def run_search_query(
        self, *, index_pattern: str, body: Dict[str, Any]
    ) -> ElasticSearchResponse:
        try:
            response = await self._client.options(request_timeout=self._timeout).search(
                index=index_pattern, body=body
            )

        except (NotFoundError, BadRequestError) as error:
            logging.error("Elasticsearch query failed: %s", error)
            raise ElasticsearchException(str(error)) from error

        if response["_shards"].get("failures"):
            logging.error("Shard failures: %s", response["_shards"]["failures"])
            raise ElasticsearchException("Shard failures during search")

        total_hits = response["hits"]["total"]["value"]
        hits = [hit for hit in response["hits"]["hits"]]
        aggregations: Dict[str, Any] = {}

        if body.get("aggs"):
            if "aggregations" not in response.keys():
                raise ElasticsearchException(
                    f"ElasticService error: Bad query. Check that the index pattern is correct"
                )
            aggregations = response["aggregations"]
        return ElasticSearchResponse(
            hits=hits, aggregations=aggregations, total_hits=total_hits
        )

    # -------------------- BULK UPDATE -------------------- #
    async def bulk_update(
        self, actions: Iterable[Dict[str, Any]], chunk_size: int = 500
    ) -> None:
        async for ok, res in async_streaming_bulk(
            self._client, actions, chunk_size=chunk_size
        ):
            if not ok:
                logging.error("Bulk update failed: %s", res)
                raise ElasticsearchException(str(res))

    # -------------------- SHUTDOWN -------------------- #
    async def close(self) -> None:
        await self._client.close()
