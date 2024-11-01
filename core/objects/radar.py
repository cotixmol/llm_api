from pydantic import BaseModel
import typing

class RadarUnit(BaseModel):
    name: str
    value: float

class Radar(BaseModel):
    category: str
    radars: typing.List[RadarUnit]

    def model_dump(self, *args, **kwargs) -> dict:
        if not self.radars:
            return {self.category: {}}
        
        values = {
            "name": self.category.replace("radar_", ""),
            "value": [radar.value for radar in self.radars]
        }
        max_value = max(self.radars, key=lambda x:x.value).value + 100
        return {
            self.category: {
                "tooltip": {
                    "trigger": 'axis'
                },
                "radar": [
                    {
                    "indicator": [{ "text": radar.name, "max": max_value } for radar in self.radars],
                    "radius": 100
                    }
                ],
                "series": [
                    {
                        "type": 'radar',
                        "areaStyle": {},
                        "tooltip": {
                            "trigger": 'item'
                        },
                        "data": [values]
                    }
                ]
            }
        }