from typing import Dict, List, Any, Optional
import iso8601


class QueryBuilder:
    def __init__(self):
        self._fields: List[str] = []
        self._filters: Dict[str, Any] = {}
        self._sort: List[Dict[str, Dict[str, str]]] = []
        self._match_by_field: Optional[str] = None
        self._not_match_by_field: Optional[str] = None
        self._query_string: Optional[str] = None
        self._date_range: Dict[str, str] = {}

    def set_date_range(self, since_iso_time: str, to_iso_time: str) -> "QueryBuilder":
        """
        Sets the date range for the query.
        V2 avoids range duplication that ocurred in V1 by mutating the internal class state before building the query.
        """
        since_iso_time_parsed = iso8601.parse_date(since_iso_time).isoformat()
        to_iso_time_parsed = iso8601.parse_date(to_iso_time).isoformat()
        self._date_range["since"] = since_iso_time_parsed
        self._date_range["to"] = to_iso_time_parsed
        return self

    def set_fields(self, fields: List[str]) -> "QueryBuilder":
        """
        Replaces the current _source fields. Ensures that the 'content'
        field is included, to mirror the V1 logic.
        """

        fields_copy = list(fields)
        if "content" not in fields_copy:
            fields_copy.append("content")

        self._fields = fields_copy
        return self

    def set_match_by_field(self, field: str) -> "QueryBuilder":
        self._match_by_field = field
        return self

    def set_not_match_by_field(self, field: str) -> "QueryBuilder":
        self._not_match_by_field = field
        return self

    def set_filters(self, filters: Dict[str, Any]) -> "QueryBuilder":
        self._filters.update(filters)
        return self

    def set_sort(self, field: str, order: Dict[str, str]) -> "QueryBuilder":
        """
        Example: set_sort("@timestamp", {"order": "desc"})
        """
        self._sort.append({field: order})
        return self

    def set_query_string(self, query_string: str) -> "QueryBuilder":
        self._query_string = query_string
        return self

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

        # 5) Filters (simple direct approach to replicate V1 usage)
        #    In V1, there's more intricate logic; for now, we add a basic "term" for each filter key.
        for key, value in self._filters.items():
            query_template["query"]["bool"]["filter"].append({"term": {key: value}})

        # 6) Query string
        if self._query_string:
            query_template["query"]["bool"]["filter"].append(
                {"query_string": {"query": self._query_string}}
            )

        # 7) Sorting
        query_template["sort"].extend(self._sort)

        # Return final DSL
        return query_template
