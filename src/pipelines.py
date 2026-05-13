from typing import Protocol, Any, cast
from openai import OpenAI
from transformers import pipeline
from openai.types.chat import ChatCompletionMessageParam


class PipelineProtocal(Protocol):
    def __call__(self, messages: list) -> str: ...


class OpenAIPipeline:
    def __init__(self, model="gpt-4.1-nano") -> None:
        self.client = OpenAI()
        self.model = model

    def __call__(self, messages: list[ChatCompletionMessageParam]) -> str:
        response = self.client.chat.completions.create(
            model=self.model, messages=messages
        )
        return response.choices[0].message.content or ""


class HFPipeline:
    def __init__(self, model) -> None:
        self.pipe = pipeline("text-generation", model=model)

    def __call__(self, messages: list) -> str:
        result = cast(Any, self.pipe(messages))
        return result[0]["generated_text"][-1]["content"]
