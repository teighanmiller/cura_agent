from abc import ABC, abstractmethod
from transformers import Pipeline


class Agent(ABC):
    def __init__(self, pipe: Pipeline) -> None:
        self.pipe = pipe

    @abstractmethod
    def make_message(self, query: str) -> list[dict]:
        pass

    def query(self, message) -> str:
        result = self.pipe(message)
        return result[0]["generated_text"][-1]["content"]

    def handle(self, message) -> str:
        message = self.make_message(message)
        return self.query(message)
