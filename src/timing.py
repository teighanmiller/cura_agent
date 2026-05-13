import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StepTiming:
    name: str
    duration_ms: float
    error: Optional[str] = None


@dataclass
class ConversationTurn:
    messages: list[dict]
    response: str


@dataclass
class RequestTrace:
    steps: list[StepTiming] = field(default_factory=list)
    conversation: list[ConversationTurn] = field(default_factory=list)

    def record(self, name: str, duration_ms: float, error: Optional[str] = None):
        self.steps.append(StepTiming(name, duration_ms, error))

    def record_turn(self, messages: list[dict], response: str):
        self.conversation.append(ConversationTurn(messages=messages, response=response))

    def total_ms(self) -> float:
        return sum(s.duration_ms for s in self.steps)

    def to_log_str(self) -> str:
        parts = [f"{s.name}={s.duration_ms:.1f}" for s in self.steps]
        parts.append(f"total={self.total_ms():.1f}")
        return " ".join(parts)

    def conversation_log(self) -> str:
        if not self.conversation:
            return ""
        lines = ["--- conversation ---"]
        for i, turn in enumerate(self.conversation, 1):
            lines.append(f"  [turn {i}]")
            for msg in turn.messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                lines.append(f"    {role}: {content!r}")
            lines.append(f"    assistant: {turn.response!r}")
        return "\n".join(lines)

    def summary(self) -> str:
        lines = ["--- timing ---"]
        for s in self.steps:
            status = f" [ERROR: {s.error}]" if s.error else ""
            lines.append(f"  {s.name:<30} {s.duration_ms:>8.1f} ms{status}")
        lines.append(f"  {'TOTAL':<30} {self.total_ms():>8.1f} ms")
        conv = self.conversation_log()
        if conv:
            lines.append(conv)
        return "\n".join(lines)


# Thread-local-style global trace for the current request.
_current_trace: Optional[RequestTrace] = None


def start_trace() -> RequestTrace:
    global _current_trace
    _current_trace = RequestTrace()
    return _current_trace


def current_trace() -> Optional[RequestTrace]:
    return _current_trace


@contextmanager
def timed(step_name: str):
    trace = current_trace()
    t0 = time.perf_counter()
    error = None
    try:
        yield
    except Exception as e:
        error = type(e).__name__
        raise
    finally:
        elapsed = (time.perf_counter() - t0) * 1000
        if trace is not None:
            trace.record(step_name, elapsed, error)
