from pydantic import BaseModel


class Index(BaseModel):
    index: str
    n_docs: str
    size_bytes: str
