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
        # Build the query DSL
        query_builder = QueryBuilder()

        query_builder.set_date_range(request.since_date, request.to_date)
        query_builder.set_fields(request.fields)

        if request.exclude_field:
            query_builder.set_not_match_by_field(request.exclude_field)

        if request.filters:
            query_builder.set_filters(request.filters)

        if request.query_string:
            query_builder.set_query_string(request.query_string)

        # Sort if needed
        query_builder.set_sort("@timestamp", {"order": "desc"})
        query_builder.set_sort("created_at", {"order": "desc"})

        # Build the final body
        query_body = query_builder.build()
        query_body["size"] = min(self.page_size, request.max_ndocs or 1000)

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
        # Example stub: loop or use bulk operations
        # for index, body, doc_id in zip(es_index_list, data_to_update, doc_id_list):
        #     await self.es_client.update(index=index, id=doc_id, body={"doc": body})
        pass
