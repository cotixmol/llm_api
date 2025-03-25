import typing
from pydantic import BaseModel


class Filters(BaseModel):
    fields: typing.Optional[typing.List[str]] = ["_id", "created_at", "category", "content_type", "author", "content", "source"]
    category: typing.Optional[typing.List[str]] = []
    lang: typing.Optional[typing.List[str]] = None
    words: typing.Optional[typing.List[str]] = None
    not_words: typing.Optional[typing.List[str]] = None
    sentiment: typing.Optional[typing.List[str]] = None
    emotion: typing.Optional[typing.List[str]] = None


class DataPreviewPayload(BaseModel):
    index_pattern: str
    since_date: str
    to_date: str
    page_size: typing.Optional[int] = 100
    page_number: typing.Optional[int] = 1
    extra_args: typing.Optional[Filters] = None


class AnalyticsPreviewPayload(BaseModel):
    index_pattern: str
    charts: typing.List[str]
    since_date: str
    to_date: str
    filters: typing.Optional[Filters] = None


class PdfPreviewPayload(BaseModel):
    charts: typing.List[dict]
    index_pattern: str
    since_date: str
    to_date: str


class TopicPreviewPayload(BaseModel):
    index_pattern: str
    since_date: str
    to_date: str
    filters: typing.Optional[Filters] = None
    max_ndocs: typing.Optional[int] = 10000

class LLMClassificationPreviewPayload(BaseModel):
    index_pattern: str
    since_date: str
    to_date: str
    filters: typing.Optional[Filters] = None
    prompt: dict
    update_field: str
    task_key: str
    valid_labels: typing.List[str]
    max_ndocs: typing.Optional[int] = 10000
    batch_size: typing.Optional[int] = 50
    query: typing.Optional[str] = None

class LLMPromptPreviewPayload(BaseModel):
    prompt: list
    batch_size: int
    fill_batches: bool

class LLMTestPreviewPayload(BaseModel):
    prompt: typing.Any

class LLMSummaryPreviewPayload(BaseModel):
    index_pattern: str
    since_date: str
    to_date: str
    filters: typing.Optional[Filters] = None
    prompt: dict
    max_ndocs: typing.Optional[int] = 10000
    query: typing.Optional[str] = None
    summary_field: typing.Optional[str] = None  # Hacemos summary_field opcional
    batch_size: typing.Optional[int] = 2
