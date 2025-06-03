from pydantic import BaseModel

from typing import List, Dict, Optional, Any, TypeVar, Generic

Data = TypeVar("Data")
Chart = TypeVar("Chart")


class BaseResponse(BaseModel, Generic[Data, Chart]):
    data: Data
    chart: Chart
    n_docs: Optional[int]


class LLMClassificationResponse(BaseModel):
    total_docs: int
    updated_docs: int


class LLMPromptResponse(BaseModel):
    response: str


class LLMSummaryResponse(BaseModel):
    response: Dict[str, Any]


class LLMTestResponse(BaseModel):
    response: List[dict]


class VectorizedSearchResponse(BaseModel):
    response: List[str]


class FunctionCallingResponse(BaseModel):
    result: Dict[str, Any]
