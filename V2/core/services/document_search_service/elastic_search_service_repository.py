from typing import List, Dict, Optional
from V2.core.interfaces.services.document_search_service_repository_interface import (
    DocumentSearchServiceRepositoryInterface,
)
from V2.core.services.document_search_service.query_builder import QueryBuilder
from V2.api.dtos.classification_dto import ClassificationRequest


class ElasticSearchServiceRepositoryV2(DocumentSearchServiceRepositoryInterface):
    def __init__(self, page_size: int = 1000):
        self.page_size = page_size
        # self.es_client = ... # Initialize your ES client

    async def get_documents(self, request: ClassificationRequest) -> List[Dict]:
        """
        Directly build an ES-specific query from ClassificationRequest and retrieve documents.
        """
        query_builder = QueryBuilder()

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
        query_builder.set_size(size=min(self.page_size, request.max_ndocs or 1000))

        query_body = query_builder.build()

        # Now make the actual Elasticsearch request (stubbed out):
        # response = await self.es_client.search(index=request.index_pattern, body=query_body)
        # hits = response["hits"]["hits"]

        # Simulate returns
        hits = []  # replace with real data
        return hits

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
