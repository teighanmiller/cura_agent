from abc import ABC, abstractmethod
from transformers import Pipeline
import json
import subprocess
from utility import retry


class Agent(ABC):
    def __init__(self, pipe: Pipeline) -> None:
        self.pipe = pipe

    @abstractmethod
    def make_message(self, query: str) -> list[dict]:
        pass

    def query(self, message) -> str:
        result = self.pipe(message)
        return result[0]["generated_text"][-1]["content"]

    @retry(max_attempts=3, delay=1)
    def get_response(self, message) -> str:
        message = self.make_message(message)
        try:
            resp = self.query(message)
            print(f"Response: {resp}")
            json_resp = json.loads(resp)
            return self.handle_response(json_resp)
        except Exception as e:
            raise e

    def create_tool_call(self, tool, tool_dict) -> list[str]:
        if tool == "web":
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
            return cmd
        else:
            raise ValueError

    def handle_tool_call(self, tool: str, tool_dict: dict):
        cmd = self.create_tool_call(tool, tool_dict)

        cli_result = subprocess.run(cmd, capture_output=True, text=True)

        return cli_result.stdout

    def handle_response(self, response: dict):
        response_type = response.get("type", {})

        if response_type == {}:
            raise ValueError
        elif response_type == "response":
            text_response = response.get("response", {})
            return text_response if text_response != {} else "Error generating response"
        elif response == "tool_call":
            tool_response = response.get("tool", {})
            arg_response = response.get("args", {})

            if tool_response != {} and arg_response != {}:
                tool_results = self.handle_tool_call(
                    tool=tool_response, tool_dict=arg_response
                )

                return self.query(tool_results)
            else:
                raise ValueError
        else:
            raise ValueError

    def handle(self, message) -> str:
        response = self.get_response(message)
        return response
