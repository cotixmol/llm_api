from pydantic import BaseModel
import typing


class StackedSerie(BaseModel):
    name: str
    data: typing.List[typing.Union[int, float]]

class StackedLine(BaseModel):
    title: str
    x: typing.List
    series: typing.List


    def model_dump(self, *args, **kwargs) -> typing.Dict[str, typing.Any]:
        if not self.series:
            return {self.title: {}}
        return {
            self.title: {
                "x": self.x,
                "series": [
                    {
                        "name": item.name,
                        "data": item.data
                    } for item in self.series
                ]
            }
        }
