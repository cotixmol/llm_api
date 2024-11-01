from pydantic import BaseModel
from typing import Optional, Union


class Metric(BaseModel):
    name: str
    value: float
    total: Optional[int] = None
    min: Union[int, float]
    max: Union[int, float]

    def model_dump(self, *args, **kwargs) -> dict:
        if not self.total:
            return {self.name: {}}
        return {
            self.name:{
                "name": self.name,
                "value": self.value,
                "total": self.total,
                "min": self.min,
                "max": self.max
            }
        }
