import json
from datetime import datetime
from pathlib import Path


from agents.base_agent import BaseAgent
from agents.classification_agent import ClassificationAgent
from agents.calendar_agent import CalenderAgent
from timing import start_trace, timed
from pipelines import OpenAIPipeline

# pipe = pipeline("text-generation", model="Qwen/Qwen2.5-3B-Instruct")
pipe = OpenAIPipeline()

AGENTS = {
    "classification": ClassificationAgent(pipe),
    "chat_agent": BaseAgent(pipe),
    "calendar_agent": CalenderAgent(pipe),
}

LOG_FILE = Path(__file__).parent.parent / "logs" / "queries.log"
LOG_FILE.parent.mkdir(exist_ok=True)


def process_message(message: str) -> str:
    trace = start_trace()

    with timed("classification"):
        query_class = AGENTS["classification"].handle(message)

    agent = AGENTS[query_class]

    with timed(f"{query_class}.handle"):
        result = agent.handle(message)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": message,
        "classification": query_class,
        **trace.to_dict(),
    }
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    return result
