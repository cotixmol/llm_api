from pydantic import BaseModel
import typing

class RowSource(BaseModel):
    source: str
    documents: float
    total_reach: float
    unique_authors: int
    avg_engagement: typing.Optional[float]


class Table(BaseModel):
    category: str
    table: typing.List[RowSource]

    def model_dump(self, *args, **kwargs) -> dict:
        if not self.table:
            return {self.category: []}
        
        return {
            self.category: [
                {
                    "source": row.source,
                    "documents": row.documents,
                    "total_reach": row.total_reach,
                    "unique_authors": row.unique_authors,
                    "avg_engagement": row.avg_engagement * 100 if row.avg_engagement else 0
                } for row in self.table
            ]
        }
