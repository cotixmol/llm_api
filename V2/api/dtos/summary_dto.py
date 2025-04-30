from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from V2.api.dtos.common_dto import Filters


class SummaryResponse(BaseModel):
    response: Dict[str, Any]


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
