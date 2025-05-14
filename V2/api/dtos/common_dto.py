# V2/api/dtos/common.py  (new tiny file – just a model, not a new repo function)
from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class Filters(BaseModel):
    fields: Optional[List[str]] = [
        "_id",
        "created_at",
        "category",
        "content_type",
        "author",
        "content",
        "source",
    ]
    category: Optional[List[str]] = []
    lang: Optional[List[str]] = None
    words: Optional[List[str]] = None
    not_words: Optional[List[str]] = None
    sentiment: Optional[List[str]] = None
    emotion: Optional[List[str]] = None


class BaseDocument(BaseModel):
    id: str
    index: str
    content: str
    metadata: Dict[str, Any] = {}

    @classmethod
    def from_elasticsearch(cls, es_doc: Dict) -> "BaseDocument":
        """
        Converts an Elasticsearch document (represented as a dict)
        into a BaseDocument instance.
        The 'index' field is now stored as a top-level property.
        """
        doc_id = es_doc.get("_id")
        index = es_doc.get("_index")
        content = es_doc.get("content", "")
        metadata = {
            "created_at": es_doc.get("created_at"),
            "category": es_doc.get("category"),
            "summary_field_category": es_doc.get("summary_field_category"),
            "author": es_doc.get("author"),
            "followers": es_doc.get("followers"),
            "following": es_doc.get("following"),
            "location": es_doc.get("location"),
            "coordinates": es_doc.get("coordinates"),
            "content_type": es_doc.get("content_type"),
            "reach": es_doc.get("reach"),
            "estimated_reach": es_doc.get("estimated_reach"),
            "engagement": es_doc.get("engagement"),
            "reactions": es_doc.get("reactions"),
            "interactions": es_doc.get("interactions"),
            "shares": es_doc.get("shares"),
            "replies": es_doc.get("replies"),
            "source": es_doc.get("source"),
            "lang": es_doc.get("lang"),
            "author_thumbnail": es_doc.get("author_thumbnail"),
            "sentiment_name": es_doc.get("sentiment_name"),
            "embedding": es_doc.get("embedding"),
            "primary_category": es_doc.get("primary_category"),
        }
        return cls(id=doc_id, index=index, content=content, metadata=metadata)
