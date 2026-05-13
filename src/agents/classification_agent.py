from agents.agent import Agent


class ClassificationAgent(Agent):
    CLASSIFICATION_PROMPT = """
    Your task is to direct this query to the correct sub-agent.
    The sub-agents are as follows:
    - chat_agent: Handles general questions and requests, including web searches for current information.
    - calendar_agent: Handles all Google Calendar operations — listing events, looking up events, and creating events.

    Route to calendar_agent for anything involving scheduling, meetings, events, or the user's calendar.
    Route to chat_agent for everything else.

    Your response should be a JSON object in the format: {"type": "classification", "class": "<classification>"} where <classification> is one of "calendar_agent" or "chat_agent".

    User Query:
    """

    def __init__(self, pipe) -> None:
        super().__init__(pipe)

    def make_message(self, query: str) -> list[dict]:
        return [
            {
                "role": "user",
                "content": self.CLASSIFICATION_PROMPT
                + "\n"
                + query
                + "\n"
                + self._memory_block(),
            }
        ]

    def handle(self, message: str) -> str:
        return super().handle(message)
