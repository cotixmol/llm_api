from pydantic import BaseModel
import typing


class Point(BaseModel):
    lon: float
    lat: float 

class HeatMap(BaseModel):
    coordinates: typing.List[Point]

    def model_dump(self):
        if not self.coordinates:
            return {}
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [point.lon, point.lat]
                    }
                }
                for point in self.coordinates
            ]
        }
