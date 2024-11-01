from pydantic import BaseModel
from enum import Enum
import typing


class ColorPalet(Enum):
    positive = "#7FCD91"
    neutral = "grey"    #D1D4C9"
    negative = "#EE4540"
    anger = "#EE4540"
    enojo = "#EE4540"
    Enojo = "#EE4540"
    sadness = "#7DBCC8"
    tristeza = "#7DBCC8"
    Tristeza = "#7DBCC8"
    others = "grey"     #D1D4C9",
    joy = "#FCFA70"
    alegia = "#FCFA70"
    alegria = "#FCFA70"
    Alegría = "#FCFA70"
    surprise = "#fd751c"
    sorpresa = "#fd751c"
    Sorpresa = "#fd751c"
    disgust = "#7FCD91"
    asco = "#7FCD91"
    Rechazo = "#7FCD91"
    felicidad = "#fff300"
    happiness = "#fff300"
    ira = "#ff0000"
    verguenza = "#5100ff"
    shame = "#5100ff"
    Miedo = "#d44dea"
    miedo = "#d44dea"
    fear = "#d44dea"
    Instagram = "#9E37B8"
    Twitter = "#1DA1F2"
    X = "#1DA1F2"
    Facebook = "#1877f2"
    TikTok = "#000000"
    Google = "#4285f4"
    Reddit = "#FF5700"
    YouTube = "#FF0000"
    Streaming = "#6441a5"

class PieSlice(BaseModel):
    name: str
    value: float
    color: str


class PieChart(BaseModel):
    category: str
    slices: typing.List[PieSlice]

    def model_dump(self, *args, **kwargs) -> dict:
        if not self.slices:
            return {self.category: {}}
        return {
            self.category: [
                {
                    "name": slice.name,
                    "value": slice.value,
                    "itemStyle": {
                        "color": slice.color
                    }
                }
                for slice in self.slices
            ]
        }
