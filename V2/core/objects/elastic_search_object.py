from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import typing
from datetime import datetime


class ElasticSearchResponse(BaseModel):
    hits: Optional[List] = []
    aggregations: Optional[Dict] = {}
    total_hits: Optional[int] = 0


class ElasticSearchDocument(BaseModel):
    id: str = Field(alias="_id")
    index: str = Field(alias="_index")
    created_at: datetime
    category: typing.Optional[str] = None
    author: typing.Optional[str] = None
    followers: typing.Optional[int] = None
    following: typing.Optional[int] = None
    location: typing.Optional[str] = None
    coordinates: typing.Optional[str] = None
    content_type: typing.Optional[str] = None
    content: typing.Optional[str] = None
    reach: typing.Optional[int] = None
    estimated_reach: typing.Optional[int] = None
    engagement: typing.Optional[int] = None
    reactions: typing.Optional[int] = None
    interactions: typing.Optional[int] = None
    shares: typing.Optional[int] = None
    replies: typing.Optional[int] = None
    source: typing.Optional[str] = None
    lang: typing.Optional[str] = None
    category: typing.Optional[str] = None
    author_thumbnail: typing.Optional[str] = None
    sentiment_name: typing.Optional[str] = None
    embedding: typing.Optional[typing.List[float]] = None
    primary_category: typing.Optional[str] = None
