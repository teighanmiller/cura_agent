from agents.agent import Agent
from models import CalendarAgentResponse

CALENDER_PROMPT = """
You are a helpful assistant that manages my calendar.
Based on the given information, take the appropriate calendar action.
The action should be exactly as specified in the message.
If you need clarification before proceeding, ask your boss.

Rules:
- If a day name is given (e.g. "Monday", "Friday"), use the next upcoming occurrence of that day from today's date.
- If a day is given but no time is provided, ask the user whether it should be an all-day event or what the start and end time should be.
- If only a time is given with no date or day, ask the user for the date — do not assume or infer one.
- Assume that unless specified or inferable the event is a single event not a recurring event.

You can take one of the following actions:
- Book a meeting (timed or all-day, optionally recurring)
- Look up a specific event by name
- List events on the calendar
- Delete an event by name
- Ask a clarifying question

You must always respond with a single JSON object in one of these formats:

To book a timed meeting:
{"type": "tool_call", "command": "new-event", "name": "<meeting title>", "description": "<brief summary>", "date": "<YYYY-MM-DD>", "start_time": "<YYYY-MM-DD HH:MM:SS ±HHMM>", "end_time": "<YYYY-MM-DD HH:MM:SS ±HHMM>"}

To book a recurring timed meeting (freq: daily | weekly | monthly | yearly):
{"type": "tool_call", "command": "new-event", "name": "<meeting title>", "description": "<brief summary>", "date": "<YYYY-MM-DD>", "start_time": "<YYYY-MM-DD HH:MM:SS ±HHMM>", "end_time": "<YYYY-MM-DD HH:MM:SS ±HHMM>", "freq": "<frequency>"}

To book an all-day event:
{"type": "tool_call", "command": "new-event", "name": "<meeting title>", "description": "<brief summary>", "date": "<YYYY-MM-DD>"}

To list today's events:
{"type": "tool_call", "command": "event-list"}

To list events in a time range:
{"type": "tool_call", "command": "event-list", "start_time": "<YYYY-MM-DD HH:MM:SS +0000>", "end_time": "<YYYY-MM-DD HH:MM:SS +0000>"}

To look up an event by name:
{"type": "tool_call", "command": "event-details", "name": "<event name>"}

To look up an event by name within a time range:
{"type": "tool_call", "command": "event-details", "name": "<event name>", "start_time": "<YYYY-MM-DD HH:MM:SS +0000>", "end_time": "<YYYY-MM-DD HH:MM:SS +0000>"}

To delete an event by name:
{"type": "tool_call", "command": "delete-event", "name": "<event name>"}

To delete an event by name within a time range (use when multiple events share a name):
{"type": "tool_call", "command": "delete-event", "name": "<event name>", "start_time": "<YYYY-MM-DD HH:MM:SS +0000>", "end_time": "<YYYY-MM-DD HH:MM:SS +0000>"}

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


class CalenderAgent(Agent):
    response_model = CalendarAgentResponse

    def __init__(self, pipe) -> None:
        super().__init__(pipe)

    def make_message(self, query: str) -> list[dict]:
        datetime_str = self.handle_tool_call(DATETIME_CMD[0], DATETIME_CMD[1])
        return [
            {
                "role": "user",
                "content": CALENDER_PROMPT
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
