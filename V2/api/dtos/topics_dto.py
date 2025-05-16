from typing import Optional, TypeVar, Generic
from pydantic import BaseModel
from V2.api.dtos.common_dto import Filters

Data = TypeVar("Data")
Chart = TypeVar("Chart")


class TopicsResponse(BaseModel, Generic[Data, Chart]):
    data: Data
    chart: Chart
    n_docs: Optional[int]


class TopicsRequest(BaseModel):
    index_pattern: str
    since_date: str
    to_date: str
    filters: Optional[Filters] = None
    max_ndocs: Optional[int] = 10000
