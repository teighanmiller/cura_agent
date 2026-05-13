from agents.agent import Agent

BASE_PROMPT = """
You are a helpful assistant that answers your bosses questions to the best of your ability.
Your answer should be specific and completely answer the question.
If you have been given a request that is not within your capabilities tell your boss this.
If a question or request requires domain specific knowledge or data that frequently changes perform a web search.
Your response should be polite and complete.

You must always respond with a single JSON object in one of these two formats:

If you can answer directly:
{"type": "response", "content": "<your answer here>"}

If you need to perform a web search:
{"type": "tool_call", "tool": "web", "args": {"query": "<search query>", "engine": "duck-duck-go", "max_value": <N>}}

Your boss has asked you the following:
"""


class BaseAgent(Agent):
    def __init__(self, pipe) -> None:
        super().__init__(pipe)

    def make_message(self, query: str) -> list[dict]:
        return [
            {
                "role": "user",
                "content": BASE_PROMPT + "\n" + query + "\n" + self._memory_block(),
            }
        ]
