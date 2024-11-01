from pydantic import BaseModel
import typing


class HistogramPoint(BaseModel):
  key: str
  value: int


class Histogram(BaseModel):
  points: typing.List[HistogramPoint]


  def model_dump(self, *args, **kwargs) -> typing.Dict:
    if not self.points:
      return {}
    return {
      "keys": [point.key for point in self.points],
      "values": [point.value for point in self.points]
    }