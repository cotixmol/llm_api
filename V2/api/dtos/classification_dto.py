import typing
from pydantic import BaseModel


class Filters(BaseModel):
    fields: typing.Optional[typing.List[str]] = [
        "_id",
        "created_at",
        "category",
        "content_type",
        "author",
        "content",
        "source",
    ]
    category: typing.Optional[typing.List[str]] = []
    lang: typing.Optional[typing.List[str]] = None
    words: typing.Optional[typing.List[str]] = None
    not_words: typing.Optional[typing.List[str]] = None
    sentiment: typing.Optional[typing.List[str]] = None
    emotion: typing.Optional[typing.List[str]] = None


class ClassificationRequest(BaseModel):
    index_pattern: str
    since_date: str
    to_date: str
    filters: typing.Optional[Filters] = None
    prompt: dict
    update_field: str
    task_key: str
    # Discuss the origin of these in V1, as a possible request field
    match_field: str
    #####
    valid_labels: typing.List[str]
    max_ndocs: typing.Optional[int] = 10000
    batch_size: typing.Optional[int] = 50
    query: typing.Optional[str] = None


class ClassificationResponse(BaseModel):
    total_docs: int
    updated_docs: int
