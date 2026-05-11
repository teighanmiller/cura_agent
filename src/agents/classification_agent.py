from datetime import datetime
from pathlib import Path

from agents.agent import Agent

LOG_FILE = Path(__file__).parent.parent.parent / "logs" / "queries.log"
LOG_FILE.parent.mkdir(exist_ok=True)


class ClassificationAgent(Agent):
    CLASSIFICATION_PROMPT = """
    Your task is to direct this query to the correct sub-agent.
    The sub-agents are as follows:
    - chat_agent: This agent is in charge of handling any general queries the user has that don't involve the other agents.
    - calendar_agent: This agent is in charge of handling the users calendar.

    Your response should be a JSON object in the format: {"type": "classification", "class": "<classification>"} where <classification> is one of "calendar_agent" or "chat_agent".

    User Query:
    """

    def __init__(self, pipe) -> None:
        super().__init__(pipe)

    def make_message(self, query: str) -> list[dict]:
        return [{"role": "user", "content": self.CLASSIFICATION_PROMPT + "\n" + query}]

    def handle(self, message: str) -> str:
        result = super().handle(message)
        with LOG_FILE.open("a") as f:
            f.write(
                f"{datetime.now().isoformat()} query={message!r} classification={result!r}\n"
            )
        return result
