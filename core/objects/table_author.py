from pydantic import BaseModel
import typing

class RowAuthor(BaseModel):
    name: str
    value: float
    category: str
    followers: typing.Optional[int]
    reach: float
    engagement: typing.Optional[float]


class Table(BaseModel):
    category: str
    table: typing.List[RowAuthor]

    def model_dump(self, *args, **kwargs) -> dict:
        if not self.table:
            return {self.category: {}}
        
        return {
            self.category: [
                {
                    "author": row.name,
                    "documents": row.value,
                    "category": row.category,
                    "followers": row.followers,
                    "reach": row.reach,
                    "engagement": row.engagement
                } for row in self.table
            ]
        }
