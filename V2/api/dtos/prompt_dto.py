from typing import Dict, Any, Optional
from pydantic import BaseModel



class PromptRequest(BaseModel):
    input_prompt: str

class PromptResponse(BaseModel):
    response: str

class PromptOutput(BaseModel):
    prompt: Optional[str]
    metadata: Dict[str, Any]

