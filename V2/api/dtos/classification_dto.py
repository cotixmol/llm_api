from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from V2.core.objects.elastic_search_object import ElasticSearchDocument
from V2.api.dtos.common_dto import Filters


class ClassificationRequest(BaseModel):
    index_pattern: str
    since_date: str
    to_date: str
    filters: Optional[Filters] = None
    prompt: dict
    update_field: str
    task_key: str
    # Discuss the origin of these in V1, as a possible request field
    match_field: str
    #####
    valid_labels: List[str]
    max_ndocs: Optional[int] = 10000
    batch_size: Optional[int] = 50
    query: Optional[str] = None


class ClassificationResponse(BaseModel):
    total_docs: int
    updated_docs: int


class ClassificationOutput(BaseModel):
    classification: Optional[str]
    metadata: Dict[str, Any]
