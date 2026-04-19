from agents.agent import Agent


class BaseAgent(Agent):
    def __init__(self, pipe) -> None:
        super().__init__(pipe)

    def make_message(self, query: str) -> list[dict]:
        return [{"role": "user", "content": query}]
