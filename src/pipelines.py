import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Protocol
from openai import OpenAI
from transformers import pipeline
from openai.types.chat import ChatCompletionMessageParam


class PipelineProtocal(Protocol):
    def __call__(
        self, response_format: type[BaseModel], messages: list
    ) -> BaseModel: ...


class OpenAIPipeline:
    def __init__(self, model="gpt-4.1-nano") -> None:
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("GPT_API_KEY"))
        self.model = model

    def __call__(
        self,
        response_format: type[BaseModel],
        messages: list[ChatCompletionMessageParam],
    ) -> BaseModel:
        response = self.client.chat.completions.parse(
            model=self.model, messages=messages, response_format=response_format
        )
        return response.choices[0].message.parsed  # type: ignore[return-value]


class HFPipeline:
    def __init__(self, model) -> None:
        self.pipe = pipeline("text-generation", model=model)

    def __call__(self, response_format: type[BaseModel], messages: list) -> BaseModel:
        raise NotImplementedError(
            "HFPipeline does not support structured output (response_format) yet"
        )
