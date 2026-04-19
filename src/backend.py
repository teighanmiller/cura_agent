from transformers import pipeline

from agents.base_agent import BaseAgent
from agents.classification_agent import ClassificationAgent
from agents.calendar_agent import CalenderAgent

pipe = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B-Instruct")

AGENTS = {
    "classification": ClassificationAgent(pipe),
    "chat_agent": BaseAgent(pipe),
    "calendar_agent": CalenderAgent(pipe),
}


def process_message(message: str) -> str:
    query_class = AGENTS["classification"].handle(message)
    agent = AGENTS[query_class]
    return agent.handle(message)
