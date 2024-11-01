from pydantic import BaseModel
import typing

class Row(BaseModel):
    source: str
    author: str
    content: str
    interactions: int
    category: str

class Table(BaseModel):
    category: str
    table: typing.List[Row]

    def model_dump(self, *args, **kwargs) -> dict:
        if not self.table:
            return {self.category: []}
        
        return {
            self.category: [
                {
                    "source": row.source,
                    "author": row.author,
                    "content": row.content,
                    "interactions": row.interactions,
                    "category": row.category
                } for row in self.table
            ]
        }
