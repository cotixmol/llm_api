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

    async def _build_elastic_search_query(self, request: ClassificationRequest) -> Dict:
        """
        Builds and returns the final Elasticsearch query body
        derived from the ClassificationRequest.
        """
        DEFAULT_SIZE = 1000

        query_builder = ESQueryBuilder()

        query_builder.set_date_range(
            since_iso_time=request.since_date, to_iso_time=request.to_date
        )
        query_builder.set_fields(fields=request.filters.fields)
        query_builder.set_match_by_field(field=request.match_field)
        query_builder.set_not_match_by_field(field=request.update_field)
        query_builder.set_filters(filters=request.filters.model_dump())
        if request.query:
            query_builder.set_query_string(query_string=request.query)
        query_builder.set_sort(field="@timestamp", order={"order": "desc"})
        query_builder.set_sort(field="created_at", order={"order": "desc"})
        query_builder.set_size(
            size=min(self._page_size, request.max_ndocs or DEFAULT_SIZE)
        )

        return query_builder.build()

    async def _execute_search(
        self, request: ClassificationRequest, body: Dict
    ) -> List[Dict]:
        total_hits: List[Dict] = []
        last_sort: Optional[List] = None

        while True:
            remaining = (
                request.max_ndocs - len(total_hits)
                if request.max_ndocs is not None
                else self._page_size
            )
            if remaining <= 0:
                break

            body["size"] = min(self._page_size, remaining)
            if last_sort:
                body["search_after"] = last_sort
            else:
                body.pop("search_after", None)

            es_resp = await self._elastic_search_service.run_search_query(
                index_pattern=req.index_pattern,
                body=body,
            )
            hits = es_resp["hits"]["hits"]
            if not hits:
                break

            last_sort = hits[-1]["sort"]

            for hit in hits:
                flat = {"_index": hit["_index"], "_id": hit["_id"], **hit["_source"]}
                total_hits.append(flat)

            if len(hits) < self._page_size:
                break

        return total_hits

    async def get_documents(self, request: ClassificationRequest) -> List[Dict]:
        body = await self._build_elastic_search_query(request)
        return await self._execute_search(request, body)

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
