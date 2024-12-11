from pydantic import BaseModel
import typing

class Word(BaseModel):
    name: str
    frequency: float


class Wordcloud(BaseModel):
    category: str
    data: typing.List[Word]

    def model_dump(self, *args, **kwargs) -> dict:
        if not self.data:
            return {self.category: []}
        
        return {
            self.category: [
                {
                    "text": row.name,
                    "frequency": row.frequency
                } for row in self.data
            ]
        }
