from agents.agent import Agent
from models import EmailAgentResponse

EMAIL_PROMPT = """
You are a helpful assistant that manages my email.
Based on the given information, take the appropriate email action.
The action should be exactly as specified in the message.
If you need clarification before proceeding, ask your boss.

Rules:
- If a relative date or range is given (e.g. "last week", "yesterday", "this month"), resolve it to an
  explicit start_time/end_time using today's date, given below.
- Before sending an email, confirm you have a recipient, a subject, and a body — if any are missing, ask.
- Do not send an email unless explicitly asked to send or reply — if unsure whether a draft should be sent,
  ask for confirmation first.

You can take one of the following actions:
- Send an email
- Look up a specific email by subject or sender
- List/search emails, optionally within a date range
- Delete an email by subject or sender

You must always respond with a single JSON object in one of these formats:

To send an email:
{"type": "tool_call", "command": "new-email", "to": "<recipient address>", "subject": "<subject line>", "body": "<email body>"}

To list recent emails:
{"type": "tool_call", "command": "email-list"}

To list/search emails matching a query within a date range:
{"type": "tool_call", "command": "email-list", "query": "<search terms, e.g. sender or keyword>", "start_time": "<YYYY-MM-DD HH:MM:SS +0000>", "end_time": "<YYYY-MM-DD HH:MM:SS +0000>"}

To look up an email by subject or sender:
{"type": "tool_call", "command": "email-details", "query": "<subject or sender>"}

To delete an email by subject or sender:
{"type": "tool_call", "command": "delete-email", "query": "<subject or sender>"}

To ask a clarifying question:
{"type": "response", "content": "<your clarifying question here>"}

I have asked you the following:
"""

TIME_ADDITION = """
The current datetime is:
"""

DATETIME_CMD = [
    "time",
    {"command": "date-time"},
]


class EmailAgent(Agent):
    response_model = EmailAgentResponse

    def __init__(self, pipe) -> None:
        super().__init__(pipe)

    def make_message(self, query: str) -> list[dict]:
        datetime_str = self.handle_tool_call(DATETIME_CMD[0], DATETIME_CMD[1])
        return [
            {
                "role": "user",
                "content": EMAIL_PROMPT
                + "\n"
                + query
                + "\n"
                + TIME_ADDITION
                + " "
                + datetime_str
                + "\n"
                + self._memory_block(),
            }
        ]
