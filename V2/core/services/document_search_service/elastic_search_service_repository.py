from typing import List, Dict, Optional, Union
from V2.core.interfaces.services.document_search_service_repository_interface import (
    DocumentSearchServiceRepositoryInterface,
)
from V2.core.services.document_search_service.es_query_builder import ESQueryBuilder
from V2.api.dtos.classification_dto import ClassificationRequest
from V2.api.dtos.summary_dto import SummaryRequest
from V2.core.services.document_search_service.elastic_search_service import (
    ElasticsearchService,
)
from api.config import logger
from V2.api.dtos.common_dto import BaseDocument


class ElasticSearchServiceRepositoryV2(DocumentSearchServiceRepositoryInterface):
    def __init__(self, es_service: ElasticsearchService):
        self._elastic_search_service = es_service
        self._page_size = 1000

    async def get_documents(
        self, request: Union[ClassificationRequest, SummaryRequest]
    ) -> List[BaseDocument]:
        """Public entry point: build query, paginate, and return parsed BaseDocument objects."""
        qb = await self._prepare_query_builder(request)
        raw_results = await self._execute_search(request, qb)
        documents = [BaseDocument.from_elasticsearch(doc) for doc in raw_results]
        return documents

    async def update_documents(
        self,
        request: ClassificationRequest,
        documents: List[BaseDocument],
        classification_list: List[Dict],
    ) -> None:
        actions = []
        for doc, classification in zip(documents, classification_list):
            if classification.get(request.update_field) is None:
                continue
            actions.append(
                {
                    "_op_type": "update",
                    "_index": doc.index,
                    "_id": doc.id,
                    "doc": classification,
                }
            )

        if not actions:
            logger.info("No documents to update in Elasticsearch.")
            return

        await self._elastic_search_service.bulk_update(actions, chunk_size=500)
        logger.info("Bulk-updated %d documents.", len(actions))

    async def _prepare_query_builder(
        self, request: Union[ClassificationRequest, SummaryRequest]
    ) -> ESQueryBuilder:
        """Translate a Request into a fully configured ESQueryBuilder."""
        qb = ESQueryBuilder().set_date_range(request.since_date, request.to_date)
        # ────────────────────────  CLASSIFICATION  ─────────────────────── #
        if isinstance(request, ClassificationRequest):
            qb = (
                qb.set_fields(request.filters.fields)
                .set_match_by_field(request.match_field)
                .set_not_match_by_field(request.update_field)
                .set_filters(request.filters.model_dump())
                .set_sort("@timestamp", {"order": "desc"})
                .set_sort("created_at", {"order": "desc"})
                .set_size(min(self._page_size, request.max_ndocs or 1000))
            )

            if request.query:
                qb.set_query_string(request.query)

        # ───────────────────────────  SUMMARY  ──────────────────────────── #
        if isinstance(request, SummaryRequest):

            if request.filters is None:
                raise ValueError("filters must be provided")
            fields = list(request.filters.fields)
            for name in ("content", "interactions"):
                if name not in fields:
                    fields.append(name)

            qb = (
                qb.set_fields(fields)
                .set_match_by_field(request.summary_field or "content")
                .set_filters(request.filters.model_dump())
                .set_sort("interactions", {"order": "desc", "unmapped_type": "long"})
                .set_sort("@timestamp", {"order": "desc"})
                .set_sort("created_at", {"order": "desc"})
                .set_size(min(self._page_size, request.max_ndocs or 1000))
            )

            base_qs = '(NOT category.keyword: "Streaming") AND (NOT content_type.keyword: "Repost")'
            qb.set_query_string(
                f"{base_qs} AND ({request.query})" if request.query else base_qs
            )

            if request.summary_field:
                qb.set_custom_agg(
                    "top_categories_hits",
                    {
                        "terms": {
                            "field": f"{request.summary_field}.keyword",
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

    async def _execute_search(
        self,
        request: Union[ClassificationRequest, SummaryRequest],
        qb: ESQueryBuilder,
    ) -> List[Dict]:
        """
        • ClassificationRequest                → paginated plain hits
        • SummaryRequest *without* summary_field → paginated plain hits
        • SummaryRequest *with*  summary_field → one-shot aggs query
        """

        # ──────────────────────────────────────────────────────────────
        # 1) SummaryRequest *with* summary_field  → use aggregation path
        # ──────────────────────────────────────────────────────────────
        if isinstance(request, SummaryRequest) and request.summary_field:
            resp = await self._elastic_search_service.run_search_query(
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

        # ──────────────────────────────────────────────────────────────
        # 2) ClassificationRequest  *or*  SummaryRequest without aggs
        #    → classic search_after pagination
        # ──────────────────────────────────────────────────────────────
        total_hits: List[Dict] = []
        last_sort: Optional[List] = None
        page_number = 1

        while True:
            # how many do we still need?
            remaining = (
                request.max_ndocs - len(total_hits)
                if request.max_ndocs
                else self._page_size
            )
            if remaining <= 0:
                break

            # resize page + set/clear search_after
            qb.set_size(min(self._page_size, remaining))
            qb.set_search_after(last_sort) if last_sort else qb.clear_search_after()

            resp = await self._elastic_search_service.run_search_query(
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

            # accumulate results
            total_hits.extend(
                {"_index": h["_index"], "_id": h["_id"], **h["_source"]} for h in hits
            )
            last_sort = hits[-1]["sort"]

            # stop if final page shorter than page_size
            if len(hits) < self._page_size:
                break

            page_number += 1

        return total_hits
