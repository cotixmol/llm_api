from __future__ import annotations

from typing import List, Dict, Optional, Union, Type

from V2.core.interfaces.services.document_search_service_repository_interface import (
    DocumentSearchServiceRepositoryInterface,
)
from V2.core.services.document_search_service.es_query_builder import ESQueryBuilder
from V2.api.dtos.classification_dto import ClassificationRequest
from V2.api.dtos.summary_dto import SummaryRequest
from V2.core.services.document_search_service.elastic_search_service import (
    ElasticsearchService,
)
from V2.utils.logger import logger
from V2.api.dtos.common_dto import BaseDocument


# ─────────────────────────────────────────────────────────────
#  Query‑builder helpers
# ─────────────────────────────────────────────────────────────


class ClassificationQueryBuilder:
    """Translate a *ClassificationRequest* into an ESQueryBuilder."""

    def __init__(self, request: ClassificationRequest, page_size: int):
        self.request = request
        self.page_size = page_size

    def build(self) -> ESQueryBuilder:
        qb = ESQueryBuilder()
        qb = (
            qb.set_date_range(self.request.since_date, self.request.to_date)
            .set_fields(self.request.filters.fields)
            .set_match_by_field(self.request.match_field)
            .set_not_match_by_field(self.request.update_field)
            .set_filters(self.request.filters.model_dump())
            .set_sort("@timestamp", {"order": "desc"})
            .set_sort("created_at", {"order": "desc"})
            .set_size(min(self.page_size, self.request.max_ndocs or 1000))
        )
        if self.request.query:
            qb.set_query_string(self.request.query)
        return qb


class SummaryQueryBuilder:
    """Translate a *SummaryRequest* into an ESQueryBuilder."""

    def __init__(self, request: SummaryRequest, page_size: int):
        self.request = request
        self.page_size = page_size

    def _collect_fields(self) -> List[str]:
        fields = list(self.request.filters.fields)
        for value in ("content", "interactions"):
            if value not in fields:
                fields.append(value)
        return fields

    def build(self) -> ESQueryBuilder:
        if self.request.filters is None:
            raise ValueError("filters must be provided")

        fields = self._collect_fields()

        qb = ESQueryBuilder()
        qb = (
            qb.set_date_range(self.request.since_date, self.request.to_date)
            .set_fields(fields)
            .set_match_by_field(self.request.summary_field or "content")
            .set_filters(self.request.filters.model_dump())
            .set_sort("interactions", {"order": "desc", "unmapped_type": "long"})
            .set_sort("@timestamp", {"order": "desc"})
            .set_sort("created_at", {"order": "desc"})
            .set_size(min(self.page_size, self.request.max_ndocs or 1000))
        )

        base_qs = '(NOT category.keyword: "Streaming") AND (NOT content_type.keyword: "Repost")'
        qb.set_query_string(
            f"{base_qs} AND ({self.request.query})" if self.request.query else base_qs
        )

        if self.request.summary_field:
            qb.set_custom_agg(
                "top_categories_hits",
                {
                    "terms": {
                        "field": f"{self.request.summary_field}.keyword",
                        "size": 100,
                    },
                    "aggs": {
                        "top_docs": {
                            "top_hits": {
                                "sort": [
                                    {
                                        "interactions": {
                                            "order": "desc",
                                            "unmapped_type": "long",
                                        }
                                    }
                                ],
                                "_source": {"includes": fields},
                            }
                        }
                    },
                },
            )

        return qb


# ─────────────────────────────────────────────────────────────
#  Search‑runner helpers
# ─────────────────────────────────────────────────────────────


class _BaseSearchRunner:
    """Shared pagination utility methods."""

    def __init__(self, es_service: ElasticsearchService, page_size: int):
        self.es_service = es_service
        self.page_size = page_size

    async def _paginate(
        self,
        request: Union[ClassificationRequest, SummaryRequest],
        qb: ESQueryBuilder,
    ) -> List[Dict]:
        total_hits: List[Dict] = []
        last_sort: Optional[List] = None
        page_number = 1

        while True:
            remaining = (
                request.max_ndocs - len(total_hits)
                if request.max_ndocs
                else self.page_size
            )
            if remaining <= 0:
                break

            qb.set_size(min(self.page_size, remaining))
            qb.set_search_after(last_sort) if last_sort else qb.clear_search_after()

            resp = await self.es_service.run_search_query(
                index_pattern=request.index_pattern,
                body=qb.build(),
            )
            hits = resp.hits

            logger.info(
                "%d documents fetched on page %d from index %s",
                len(hits),
                page_number,
                request.index_pattern,
            )

            if not hits:
                break

            total_hits.extend(
                {"_index": h["_index"], "_id": h["_id"], **h["_source"]} for h in hits
            )
            last_sort = hits[-1]["sort"]

            if len(hits) < self.page_size:
                break

            page_number += 1

        return total_hits


class ClassificationSearchRunner(_BaseSearchRunner):
    async def run(
        self, request: ClassificationRequest, qb: ESQueryBuilder
    ) -> List[Dict]:
        return await self._paginate(request, qb)


class SummarySearchRunner(_BaseSearchRunner):
    async def run(self, request: SummaryRequest, qb: ESQueryBuilder) -> List[Dict]:
        # If a summary_field is provided → aggregation path
        if request.summary_field:
            resp = await self.es_service.run_search_query(
                index_pattern=request.index_pattern,
                body=qb.build(),
            )
            buckets = resp.aggregations.get("top_categories_hits", {}).get(
                "buckets", []
            )
            docs: List[Dict] = [
                {"_index": h["_index"], "_id": h["_id"], **h["_source"]}
                for bucket in buckets
                for h in bucket["top_docs"]["hits"]["hits"]
            ]
            logger.info(
                "Fetched %d top-category documents from index %s",
                len(docs),
                request.index_pattern,
            )
            return docs

        # Otherwise → classic pagination
        return await self._paginate(request, qb)


# ─────────────────────────────────────────────────────────────
#  Public repository (unchanged interface)
# ─────────────────────────────────────────────────────────────


class ElasticSearchServiceRepositoryV2(DocumentSearchServiceRepositoryInterface):
    """Same public API, but internally delegates to the new helpers."""

    def __init__(self, es_service: ElasticsearchService):
        self._elastic_search_service = es_service
        self._page_size = 10000  # Default page size for pagination

    # ───────────── GET DOCUMENTS ─────────────
    async def get_documents(
        self, request: Union[ClassificationRequest, SummaryRequest]
    ) -> List[BaseDocument]:
        if isinstance(request, ClassificationRequest):
            builder_cls = ClassificationQueryBuilder
            runner_cls = ClassificationSearchRunner
        elif isinstance(request, SummaryRequest):
            builder_cls = SummaryQueryBuilder
            runner_cls = SummarySearchRunner
        else:
            raise TypeError(f"Unsupported request type: {type(request)}")

        qb = builder_cls(request, self._page_size).build()
        runner = runner_cls(self._elastic_search_service, self._page_size)
        raw_results = await runner.run(request, qb)
        return [BaseDocument.from_elasticsearch(doc) for doc in raw_results]

    # ───────────── UPDATE DOCUMENTS (unchanged) ─────────────
    async def update_documents(
        self,
        request: ClassificationRequest,
        documents: List[BaseDocument],
        classification_list: List[Dict],
    ) -> None:
        actions = []
        for document, classification in zip(documents, classification_list):
            if classification.get(request.update_field) is None:
                continue
            actions.append(
                {
                    "_op_type": "update",
                    "_index": document.index,
                    "_id": document.id,
                    "doc": classification,
                }
            )

        if not actions:
            logger.info("No documents to update in Elasticsearch.")
            return

        await self._elastic_search_service.bulk_update(actions, chunk_size=500)
        logger.info("Bulk-updated %d documents.", len(actions))
