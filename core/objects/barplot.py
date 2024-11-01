from pydantic import BaseModel
import typing

class BarPlotUnit(BaseModel):
    name: str
    value: float

class Barplot(BaseModel):
    category: str
    bars: typing.List[BarPlotUnit]

    def model_dump(self, *args, **kwargs) -> dict:
        if not self.bars:
            return {self.category: []}
        return {
            self.category: self.bars[::-1]
        }