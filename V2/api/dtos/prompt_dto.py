from typing import List, Literal
from pydantic import BaseModel, Field

class PromptMessageItem(BaseModel):
    role:    Literal["system","assistant","user"]
    content: str

class PromptRequest(BaseModel):
    messages_list: List[PromptMessageItem]
    temperature: float = Field(0.1, ge=0.0, le=1.0)  # default 0.1, optional now
    top_p:       float = Field(0.9, ge=0.0, le=1.0)  # default 1.0
    max_tokens:  int   = Field(500, gt=0)

class PromptResponse(BaseModel):
    messages_list: List[PromptMessageItem]