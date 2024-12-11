from pydantic import BaseModel
import typing


class LinealHeatmap(BaseModel):
    title: str = "Lineal HeatMap"
    yAxis: typing.List = []
    xAxis: typing.List = []
    data: typing.List = []
