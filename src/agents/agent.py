from abc import ABC, abstractmethod
from pipelines import PipelineProtocal
import subprocess
from typing import ClassVar
from pydantic import BaseModel
from models import CalendarAgentResponse, ClassificationResponse
from utility import retry
from timing import timed, current_trace


class Agent(ABC):
    response_model: ClassVar[type[BaseModel]]

    def __init__(self, pipe: PipelineProtocal) -> None:
        self.pipe = pipe
        self.memories: list[str] = []

    @abstractmethod
    def make_message(self, query: str) -> list[dict]:
        pass

    def add_memory(self, fact: str) -> None:
        self.memories.append(fact)

    def _memory_block(self) -> str:
        if not self.memories:
            return ""
        facts = "/n".join(f"- {mem}" for mem in self.memories)
        return f"Conversation history: \n{facts}\n"

    def query(self, response_format: type[BaseModel], messages: list) -> BaseModel:
        response = self.pipe(response_format=response_format, messages=messages)
        trace = current_trace()
        if trace is not None:
            trace.record_turn(
                messages=messages, response=response.model_json_schema.__str__()
            )
        return response

    @retry(max_attempts=3, delay=1)
    def get_response(self, message) -> str:
        print("Getting response....")
        agent_name = type(self).__name__
        with timed(f"{agent_name}.make_message"):
            messages = self.make_message(message)
        try:
            with timed(f"{agent_name}.query"):
                parsed = self.query(self.response_model, messages)
            print("Query made...")
            with timed(f"{agent_name}.handle_response"):
                return self.handle_response(parsed)
            print("Handling response....")
        except Exception as e:
            raise e

    def create_tool_call(self, tool, tool_dict) -> list[str]:
        if tool == "time":
            return ["cura", "time", tool_dict["command"]]
        elif tool == "web":
            cmd = ["cura", "web", tool_dict["query"]]
            if "engine" in tool_dict:
                cmd += ["--engine", tool_dict["engine"]]
            if "max_value" in tool_dict:
                cmd += ["--max-value", str(tool_dict["max_value"])]
            return cmd
        elif tool == "gcal":
            cmd = ["cura", "gcal", tool_dict["command"]]
            if "name" in tool_dict:
                cmd += ["--name", tool_dict["name"]]
            if "description" in tool_dict:
                cmd += ["--description", tool_dict["description"]]
            if "date" in tool_dict:
                cmd += ["--date", tool_dict["date"]]
            if "start_time" in tool_dict:
                cmd += ["--start-time", tool_dict["start_time"]]
            if "end_time" in tool_dict:
                cmd += ["--end-time", tool_dict["end_time"]]
            if "freq" in tool_dict:
                cmd += ["--freq", tool_dict["freq"]]
            return cmd
        else:
            raise ValueError

    def handle_tool_call(self, tool: str, tool_dict: dict):
        cmd = self.create_tool_call(tool, tool_dict)

        with timed(f"tool_call.{tool}"):
            try:
                cli_result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=20
                )
            except subprocess.TimeoutExpired:
                return (
                    "This action has failed. The use must login and authenticate Google Calender."
                    "Please inform the user to run `cura gcal event-list` in their terminal "
                    "to complete Google authentication, then try again."
                )

            if cli_result.returncode:
                error_detail = cli_result.stderr.strip() or "unknown error"
                return f"Error occured during the operation: {error_detail}"

        return cli_result.stdout

    def _empty_result_message(self, tool: str, tool_dict: dict) -> str:
        if tool == "gcal":
            command = tool_dict.get("command", "")
            if command == "event-list":
                return "There are no events on the calendar."
            elif command == "new-event":
                return "Event successfully created."
            else:
                return "Calendar operation completed successfully."
        elif tool == "web":
            return "No results found for that query."
        return "The operation completed with no output."

    def handle_response(self, response: BaseModel) -> str:
        if isinstance(response, ClassificationResponse):
            return response.class_name

        response_type = getattr(response, "type", None)
        if response_type == "response":
            return getattr(response, "content", "")

        tool = "gcal" if isinstance(response, CalendarAgentResponse) else "web"
        args = response.model_dump(exclude_none=True, exclude={"type", "content"})

        tool_results = self.handle_tool_call(tool=tool, tool_dict=args)
        if not tool_results.strip():
            tool_results = self._empty_result_message(tool, args)
        follow_up = self.query(
            self.response_model, [{"role": "user", "content": tool_results}]
        )
        return self.handle_response(follow_up)

    def handle(self, message) -> str:
        response = self.get_response(message)
        return response
