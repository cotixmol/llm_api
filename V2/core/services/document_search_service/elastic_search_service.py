from __future__ import annotations
from typing import List, Dict, Any, Iterable
import logging

from elasticsearch import AsyncElasticsearch, NotFoundError, BadRequestError
from elasticsearch.helpers import async_streaming_bulk


class ElasticsearchException(RuntimeError):
    pass


class ElasticsearchService:
    """
    Tiny wrapper around AsyncElasticsearch.
    • run_search_query  – used by _execute_search
    • bulk_update       – used by update_documents (if/when you wire it)
    • close             – optional graceful shutdown
    """

    def __init__(
        self,
        *,
        hosts: List[str],
        port: int,
        user: str | None = None,
        password: str | None = None,
        verify_certs: bool = False,
        max_retries: int = 5,
        timeout: int = 10,
    ) -> None:
        self._client = AsyncElasticsearch(
            hosts=[f"https://{h}:{port}" for h in hosts],
            http_auth=(user, password) if user else None,
            verify_certs=verify_certs,
            retry_on_timeout=True,
            max_retries=max_retries,
        )
        self._timeout = timeout

    # ---------- SEARCH ----------
    async def run_search_query(
        self, *, index_pattern: str, body: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            return await self._client.options(request_timeout=self._timeout).search(
                index=index_pattern, body=body
            )
        except (NotFoundError, BadRequestError) as exc:
            logging.error("Elasticsearch query failed: %s", exc)
            raise ElasticsearchException(str(exc)) from exc

    # ---------- BULK UPDATE ----------
    async def bulk_update(
        self, actions: Iterable[Dict[str, Any]], *, chunk_size: int = 500
    ) -> None:
        async for ok, res in async_streaming_bulk(
            self._client, actions, chunk_size=chunk_size
        ):
            if not ok:
                logging.error("Bulk update failed: %s", res)
                raise ElasticsearchException(str(res))

    async def close(self) -> None:
        await self._client.close()
