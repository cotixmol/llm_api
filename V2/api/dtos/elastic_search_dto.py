from pydantic import BaseModel
from typing import Optional, List, Dict


class SearchResponse(BaseModel):
    hits: Optional[List] = []
    aggregations: Optional[Dict] = {}
    total_hits: Optional[int] = 0
