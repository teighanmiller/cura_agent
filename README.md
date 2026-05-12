# Cura Agent

> **Status: Active Development** — This project is under active construction. The primary development branch is [`agents`](../../tree/agents). The `main` branch reflects the project scaffold only.

Cura is a locally-run, multi-agent AI assistant designed to route natural language queries to specialized sub-agents — starting with calendar management via Google Calendar. The system is built around a classification layer that reads an incoming query, determines which domain agent should handle it, dispatches the request, executes any necessary tool calls, and returns a synthesized response.

The long-term goal is a personal assistant that can operate across multiple domains (calendar, email, tasks, search) from a single natural language interface, running entirely on local hardware without dependency on external AI APIs.

---

## Architecture

```
User Query
    │
    ▼
ClassificationAgent       ← determines which domain the query belongs to
    │
    ▼
Domain Agent              ← e.g. CalendarAgent, (EmailAgent, TaskAgent — planned)
    │
    ▼
Cura CLI (Rust)           ← handles API calls to external services
    │
    ▼
Response Handler          ← synthesizes tool output into a natural language reply
```

Each agent layer runs inference independently using locally-hosted models via the Hugging Face `transformers` stack. No external LLM API is used.

API calls to external services are handled by **[cura](https://github.com/teighanmiller/cura/tree/main)**, a companion Rust CLI. Keeping the API layer in a separate binary decouples the Python inference stack from network I/O and allows the CLI to be used independently of the agent system.

---

## Current Development Phase

The project is in **Phase 1: Core Agent Loop**. The classification and calendar agents exist and can complete an end-to-end query cycle. The focus right now is getting a reliable, correct loop before expanding to additional domain agents.

### What works
- Query classification routing to the correct domain agent
- Google Calendar read access via OAuth
- End-to-end response for calendar queries (e.g. *"What is on my calendar today?"*)

### What is being actively built (see [`agents` branch](../../tree/agents))
- Improved prompt templates for the classification and response-synthesis steps
- Persistent session / conversation memory
- Additional domain agents (email, tasks)
- Gradio-based chat UI

---

## Known Issues

### 1. Slow inference times

End-to-end latency is currently unacceptably high for interactive use. A representative timing breakdown from a single calendar query:

| Step | Time (ms) |
|---|---|
| `ClassificationAgent.query` | 2,892 |
| `CalendarAgent.query` | 11,198 |
| `tool_call.gcal` (API) | 72 |
| `CalendarAgent.handle_response` | 24,980 |
| **Total** | **~78,000** |

The Google Calendar API call itself takes ~72 ms — nearly all latency comes from local model inference. Running two full inference passes (classification + response synthesis) on CPU produces multi-second delays at each step, and the response-synthesis step alone currently accounts for ~25 seconds.

**Fix in progress:** Migrating the inference backend from the default `transformers` pipeline to a quantized GGUF model served via `llama-cpp-python`, which reduces per-token latency by 4–8× on Apple Silicon and modern CPUs without requiring a GPU. Classification will also be replaced with a lightweight fine-tuned model or a rules/embedding-based router to eliminate a full LLM call for a task that doesn't need one.

### 2. Response synthesis errors

The `handle_response` step occasionally produces malformed output — the model echoes prompt fragments, produces incomplete sentences, or ignores the tool call result entirely when the calendar returns an empty or unusual payload.

**Fix in progress:** Adding structured output constraints (JSON mode / grammar-based sampling) to the response synthesis step so the model is forced to produce a well-formed reply. Prompt templates are also being tightened to reduce the context the model can ignore.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Local inference | Hugging Face `transformers`, PyTorch |
| API CLI | Rust ([cura](https://github.com/teighanmiller/cura/tree/main)) |
| API integrations | Google Calendar API |
| Linting / formatting | Ruff |
| Testing | pytest |
| Package management | uv |

---

## Getting Started

> Full setup instructions will be added once the `agents` branch stabilizes. The steps below set up the project scaffold.

**Prerequisites:** Python 3.12+, [`uv`](https://github.com/astral-sh/uv)

```bash
git clone <repo-url>
cd cura_agent
git checkout agents          # active development branch

uv sync                      # install dependencies
cp .env.example .env         # add your Google OAuth credentials
uv run main.py
```

Google Calendar integration requires OAuth 2.0 credentials. See the [Google Calendar Python Quickstart](https://developers.google.com/calendar/api/quickstart/python) for credential setup.

---

## Design Considerations & Future Directions

### Skill files vs. separate agents

The current design uses a dedicated agent class per domain (calendar, email, etc.), each running its own inference pass. An alternative worth exploring is a **skill-file architecture** — a single model that selects and executes modular skill definitions at runtime rather than routing to entirely separate agents. This could reduce total inference passes per query and lower memory overhead from running multiple model instances. The tradeoff is that a generalist model handling all skills may be less reliable than a domain-specific one; the right answer likely depends on how far the fine-tuning work progresses.

### Fine-tuning

A core long-term goal of this project is **fine-tuning small LLMs for specific question types** (calendar queries, task management, etc.) rather than relying on large general-purpose models to handle everything well. The expectation is that a fine-tuned 1–3B parameter model can match or exceed the quality of a larger general model on a narrow domain, at a fraction of the inference cost — directly addressing the latency problems described above. The agent-per-domain architecture is intentionally structured to make this incremental: each domain agent can be swapped for a fine-tuned model independently as training data is collected.

---

## Roadmap

- [ ] Replace CPU inference with quantized GGUF backend (llama-cpp-python)
- [ ] Replace LLM-based classifier with embedding/rules router
- [ ] Structured output for response synthesis
- [ ] Conversation memory across turns
- [ ] Email domain agent
- [ ] Task management domain agent
- [ ] Gradio chat UI
- [ ] Evaluate skill-file architecture as an alternative to per-domain agents
- [ ] Collect domain-specific training data for fine-tuning experiments

---

## License

MIT
