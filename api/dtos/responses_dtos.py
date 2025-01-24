from pydantic import BaseModel
import typing


Data = typing.TypeVar("Data")
Chart = typing.TypeVar("Chart")

class BaseResponse(BaseModel, typing.Generic[Data, Chart]):
    data: Data
    chart: Chart
    n_docs: typing.Optional[int]

class LLMClassificationResponse(BaseModel): #######!!!!!!!!!!
    total_docs: int
    updated_docs: int
    
class LLMPromptResponse(BaseModel): ############!!!!!!!!!
    response: str
    