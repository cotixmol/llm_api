from typing import Dict, List, Any, Optional


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
        self._date_range["since"] = since_iso_time
        self._date_range["to"] = to_iso_time
        return self

    def set_fields(self, fields: List[str]) -> "QueryBuilder":
        self._fields.extend(fields)
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
        Builds an Elasticsearch DSL query from the stored parameters.
        """
        bool_query = {"must": [], "must_not": [], "filter": []}

        # Date range
        if "since" in self._date_range and "to" in self._date_range:
            bool_query["filter"].append(
                {
                    "range": {
                        "@timestamp": {
                            "gte": self._date_range["since"],
                            "lte": self._date_range["to"],
                        }
                    }
                }
            )

        # Match by field
        if self._match_by_field:
            # Example approach: just ensure the field exists; adapt to your needs
            bool_query["must"].append({"exists": {"field": self._match_by_field}})

        # Not match by field
        if self._not_match_by_field:
            bool_query["must_not"].append(
                {"exists": {"field": self._not_match_by_field}}
            )

        # Additional filters
        for key, value in self._filters.items():
            bool_query["filter"].append({"term": {key: value}})

        # Query string
        if self._query_string:
            bool_query["must"].append(
                {"query_string": {"query": self._query_string, "fields": self._fields}}
            )

        # Final DSL
        return {
            "_source": self._fields,
            "query": {"bool": bool_query},
            "sort": self._sort,
        }
