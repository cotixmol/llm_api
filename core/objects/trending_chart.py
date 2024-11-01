from pydantic import BaseModel
import typing


class Trend(BaseModel):
    label: str
    value: int
    evolution: float
    previus: int


class TrendChart(BaseModel):
    title: str
    trends: typing.List[Trend]

    def model_dump(self, *args, **kwargs) -> dict:
        if not self.trends:
            return {self.title: {}}
        return {
            self.title: [
                {
                    "label": trend.label,
                    "value": trend.value,
                    "evolution": trend.evolution,
                    "previus": trend.previus
                }
                for trend in self.trends
            ]
        }
