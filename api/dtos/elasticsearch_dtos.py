from pydantic import BaseModel
from typing import Optional, List, Dict


class IndexStatus(BaseModel):
    health: str
    status: Optional[str] = None
    index: str
    uuid: Optional[str] = None
    pri: Optional[str] = None
    rep: Optional[str] = None
    docs_count: str
    docs_deleted:Optional[str] = None
    store_size: Optional[str] = None
    pri_store_size: str
    dataset_size: Optional[str] = None


class SearchResponse(BaseModel):
    hits: Optional[List] = []
    aggregations: Optional[Dict] = {}
    total_hits: Optional[int] = 0
