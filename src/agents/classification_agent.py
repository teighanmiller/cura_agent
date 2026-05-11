from agents.agent import Agent


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
        return super().handle(message)
