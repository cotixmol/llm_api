from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class SummaryResponse(BaseModel):
    response: Dict[str, Any]


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


class SummaryRequest(BaseModel):
    index_pattern: str
    since_date: str
    to_date: str
    filters: Optional[Filters] = None
    max_ndocs: Optional[int] = 10000
    prompt: dict
    query: Optional[str] = None
    summary_field: str = None
    batch_size: Optional[int] = 50
