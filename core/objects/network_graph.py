from pydantic import BaseModel
import typing

class NetworkNode(BaseModel):
    name: str
    value: int
    category: int
    soft_size: float = 0.0

    def model_dump(self, *args, **kwargs) -> typing.Dict:
        if not self.name:
          return 
        return {
            "name": self.name,
            "value": self.value,
            "category": self.category,
            "symbolSize": self.soft_size
        }


class NetworkLink(BaseModel):
    source: str
    target: str
    value: int

class NetworkCategory(BaseModel):
    name: str

class NetworkGraph(BaseModel):
    title: str = "Network Graph"
    nodes: typing.List[NetworkNode]
    links: typing.List[NetworkLink]
    categories: typing.List[NetworkCategory]

    def model_dump(self, *args, **kwargs) -> typing.Dict:
        if not self.nodes:
          return {}
        return {
          self.title: {
              "nodes": [node.model_dump() for node in self.nodes],
              "links": self.links,
              "categories": self.categories
          }
        }
