from typing import Dict, List, Any, Optional, Callable
import iso8601
from V2.api.config.logger import logger


class ESQueryBuilder:
    def __init__(self):
        self._fields: List[str] = []
        self._filters: Dict[str, Any] = {}
        self._sort: List[Dict[str, Dict[str, str]]] = []
        self._match_by_field: Optional[str] = None
        self._not_match_by_field: Optional[str] = None
        self._query_string: Optional[str] = None
        self._date_range: Dict[str, str] = {}
        self._size: int | None = None
        self._search_after: Optional[List] = None
        self._aggs: Dict[str, Any] = {}

        self._filter_registry: Dict[str, Callable[[Any], Dict[str, Any]]] = {
            "category": self._build_category_filter,
            "sentiment": self._build_sentiment_filter,
            "emotion": self._build_emotion_filter,
            "lang": self._build_lang_filter,
            "words": self._build_words_filter,
            "not_words": self._build_not_words_filter,
        }

    def set_date_range(self, since_iso_time: str, to_iso_time: str) -> "ESQueryBuilder":
        """
        Sets the date range for the query.
        V2 avoids range duplication that ocurred in V1 by mutating the internal class state before building the query.
        """
        since_iso_time_parsed = iso8601.parse_date(since_iso_time).isoformat()
        to_iso_time_parsed = iso8601.parse_date(to_iso_time).isoformat()
        self._date_range["since"] = since_iso_time_parsed
        self._date_range["to"] = to_iso_time_parsed
        return self

    def set_fields(self, fields: List[str]) -> "ESQueryBuilder":
        """
        Replaces the current _source fields. Ensures that the 'content'
        field is included, to mirror the V1 logic.
        """

        fields_copy = list(fields)
        if "content" not in fields_copy:
            fields_copy.append("content")

        self._fields = fields_copy
        return self

    def set_match_by_field(self, field: str = "content") -> "ESQueryBuilder":
        self._match_by_field = field
        return self

    def set_not_match_by_field(self, field: str) -> "ESQueryBuilder":
        self._not_match_by_field = field
        return self

    def set_filters(self, filters: Dict) -> "ESQueryBuilder":
        self._filters.update(filters)
        return self

    def set_sort(self, field: str, order: Dict[str, str]) -> "ESQueryBuilder":
        self._sort.append({field: order})
        return self

    def set_query_string(self, query_string: str) -> "ESQueryBuilder":
        self._query_string = query_string
        return self

    def set_size(self, size: int) -> "ESQueryBuilder":
        self._size = size
        return self

    def set_search_after(self, sort_id: List[Any]) -> "ESQueryBuilder":
        self._search_after = sort_id
        return self

    def clear_search_after(self) -> "ESQueryBuilder":
        self._search_after = None
        return self

    def set_custom_agg(self, name: str, body: Dict[str, Any]) -> "ESQueryBuilder":
        """Register a named aggregation block (used only by Summary)."""
        self._aggs[name] = body
        return self

    # -------------------------------------------------------------------------
    #                          BUILD METHOD
    # -------------------------------------------------------------------------

    def build(self) -> Dict[str, Any]:
        """
        Builds an Elasticsearch DSL query replicating the shape of the original Query (V1).
        """
        # This mirrors the structure in the old Query class:
        query_template = {
            "track_total_hits": "true",
            "sort": [],
            "aggs": {},
            "size": 0,
            "runtime_mappings": {},
            "_source": [],
            "query": {"bool": {"must": [], "filter": [], "should": [], "must_not": []}},
        }

        # 1) Set the fields
        query_template["_source"] = list(
            set(self._fields)
        )  # Remove duplicates, just in case

        # 2) Date range (use "created_at" to match V1’s default date field)
        if "since" in self._date_range and "to" in self._date_range:
            query_template["query"]["bool"]["must"].append(
                {
                    "range": {
                        "created_at": {
                            "format": "strict_date_optional_time",
                            "gte": self._date_range["since"],
                            "lte": self._date_range["to"],
                        }
                    }
                }
            )

        # 3) Match by field (as a filter)
        if self._match_by_field:
            query_template["query"]["bool"]["filter"].append(
                {
                    "bool": {
                        "should": [{"exists": {"field": self._match_by_field}}],
                        "minimum_should_match": 1,
                    }
                }
            )

        # 4) Not match by field (must_not)
        if self._not_match_by_field:
            query_template["query"]["bool"]["must_not"].append(
                {"exists": {"field": self._not_match_by_field}}
            )

        # 5) Filters using registry or fallback
        for key, value in self._filters.items():
            if key in self._filter_registry:
                snippet = self._filter_registry[key](
                    value
                )  # Execute the correct build function in the registry
                query_template["query"]["bool"]["filter"].append(snippet)
            else:
                logger.warning(
                    f"Unrecognized filter key '{key}', using simple term query."
                )
                query_template["query"]["bool"]["filter"].append({"term": {key: value}})

        # 6) Query string
        if self._query_string:
            query_template["query"]["bool"]["filter"].append(
                {"query_string": {"query": self._query_string}}
            )

        # 7) Sorting
        if self._sort:
            query_template["sort"].extend(self._sort)

        # 8) Size
        if self._size is not None:
            query_template["size"] = self._size

        # 9) Search after (for pagination)
        if self._search_after:  # NEW
            query_template["search_after"] = self._search_after

        # 10) Aggregations
        if self._aggs:
            query_template["aggs"] = self._aggs

        # Return final DSL
        return query_template

    # -------------------------------------------------------------------------
    #                         PRIVATE SET_FILTER BUILDERS
    # -------------------------------------------------------------------------

    def _build_category_filter(self, categories: List[str]) -> Dict[str, Any]:
        return {
            "bool": {
                "minimum_should_match": 1,
                "should": [{"match_phrase": {"category": cat}} for cat in categories],
            }
        }

    def _build_sentiment_filter(self, sentiments: List[str]) -> Dict[str, Any]:
        return {
            "bool": {
                "minimum_should_match": 1,
                "should": [{"match_phrase": {"sentiment_name": s}} for s in sentiments],
            }
        }

    def _build_emotion_filter(self, emotions: List[str]) -> Dict[str, Any]:
        return {
            "bool": {
                "minimum_should_match": 1,
                "should": [{"match_phrase": {"emotion": e}} for e in emotions],
            }
        }

    def _build_lang_filter(self, langs: List[str]) -> Dict[str, Any]:
        return {
            "bool": {
                "minimum_should_match": 1,
                "should": [{"match_phrase": {"lang": lng}} for lng in langs],
            }
        }

    def _build_words_filter(self, words: List[str]) -> Dict[str, Any]:
        should_clauses = []
        for w in words:
            if "*" in w:
                should_clauses.append(
                    {
                        "bool": {
                            "should": [
                                {"query_string": {"fields": ["content"], "query": w}}
                            ],
                            "minimum_should_match": 1,
                        }
                    }
                )
            else:
                should_clauses.append(
                    {
                        "bool": {
                            "should": [{"match_phrase": {"content": w}}],
                            "minimum_should_match": 1,
                        }
                    }
                )
        return {"bool": {"minimum_should_match": 1, "should": should_clauses}}

    def _build_not_words_filter(self, not_words: List[str]) -> Dict[str, Any]:
        must_not_clause = []
        for w in not_words:
            if "*" in w:
                must_not_clause.append(
                    {
                        "bool": {
                            "should": [
                                {"query_string": {"fields": ["content"], "query": w}}
                            ],
                            "minimum_should_match": 1,
                        }
                    }
                )
            else:
                must_not_clause.append(
                    {
                        "bool": {
                            "should": [{"match_phrase": {"content": w}}],
                            "minimum_should_match": 1,
                        }
                    }
                )
        return {
            "bool": {
                "must_not": {
                    "bool": {"should": must_not_clause, "minimum_should_match": 1}
                }
            }
        }
