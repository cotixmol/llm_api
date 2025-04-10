from typing import List, Dict, Optional
from V2.core.interfaces.services.document_search_service_repository_interface import (
    DocumentSearchServiceRepositoryInterface,
)
from V2.core.services.document_search_service.es_query_builder import ESQueryBuilder
from V2.api.dtos.classification_dto import ClassificationRequest
from V2.core.services.document_search_service.elastic_search_service import (
    ElasticsearchService,
)


class ElasticSearchServiceRepositoryV2(DocumentSearchServiceRepositoryInterface):
    def __init__(self, es_service: ElasticsearchService):
        self._elastic_search_service = es_service
        self._page_size = 1000

    async def _prepare_query_builder(
        self, request: ClassificationRequest
    ) -> ESQueryBuilder:
        """Translate a ClassificationRequest into a fully configured ESQueryBuilder."""

        DEFAULT_SIZE = 1000
        qb = (
            ESQueryBuilder()
            .set_date_range(request.since_date, request.to_date)
            .set_fields(request.filters.fields)
            .set_match_by_field(request.match_field)
            .set_not_match_by_field(request.update_field)
            .set_filters(request.filters.model_dump())
            .set_sort("@timestamp", {"order": "desc"})
            .set_sort("created_at", {"order": "desc"})
            .set_size(min(self._page_size, request.max_ndocs or DEFAULT_SIZE))
        )

        if request.query:
            qb.set_query_string(request.query)

        return qb

    async def _execute_search(
        self, request: ClassificationRequest, qb: ESQueryBuilder
    ) -> List[Dict]:
        """Run the query builder in a loop, using search_after pagination."""

        total_hits: List[Dict] = []
        last_sort: Optional[List] = None

        while True:
            # Compute how many documents remain to be fetched
            remaining = (
                request.max_ndocs - len(total_hits)
                if request.max_ndocs
                else self._page_size
            )
            if remaining <= 0:
                break

            # Set new page size and search_after value as needed
            qb.set_size(min(self._page_size, remaining))
            qb.set_search_after(last_sort) if last_sort else qb.clear_search_after()

            # Execute the search
            resp = await self._elastic_search_service.run_search_query(
                index_pattern=request.index_pattern, body=qb.build()
            )
            hits = resp["hits"]["hits"]
            if not hits:
                break

            # Store the last sort value for pagination
            last_sort = hits[-1]["sort"]

            # Accumulate hits
            total_hits.extend(
                {"_index": h["_index"], "_id": h["_id"], **h["_source"]} for h in hits
            )

            # If we got fewer hits than page_size, we've exhausted the index
            if len(hits) < self._page_size:
                break

        return total_hits

    async def get_documents(self, request: ClassificationRequest) -> List[Dict]:
        """Public entry point: build query, paginate, and return flat hits."""

        qb = await self._prepare_query_builder(request)
        return await self._execute_search(request, qb)

    async def update_documents(
        self,
        es_index_list: List[str],
        data_to_update: List[Dict],
        doc_id_list: List[str],
    ) -> None:
        """
        Bulk updates documents in Elasticsearch.
        """
        pass
