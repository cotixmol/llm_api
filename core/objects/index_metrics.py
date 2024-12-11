from pydantic import BaseModel


class IndexMetrics(BaseModel):
    mentions: int
    reach: int
    interactions: int
    users: int
