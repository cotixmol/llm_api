from pydantic import BaseModel

class TopicInfo(BaseModel):
    topic: str
    title: str
    summary: str

    def model_dump(self, *args, **kwargs) -> dict:
        if not self.title:
            return {self.topic: {}}
        return {
            self.topic: {
                    "title": self.title,
                    "summary": self.summary
            }
        }
    