from pydantic import BaseModel
import typing

class Timeline(BaseModel):
    messure: str
    x: typing.List
    y: typing.List
    
    def model_dump(self, *args, **kwargs) -> dict[str, any]:
        if not any(self.y):
            return {self.messure: {}}
        return {
            self.messure: {
                "x": self.x,
                "y": self.y
            }
        }
