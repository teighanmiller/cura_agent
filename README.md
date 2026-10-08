# Cura Agent

> **Status: Active Development** — `agents` has been merged into `main`; the core query → classify → dispatch → tool-call → respond loop runs end to end for calendar and general chat queries.

Cura is a multi-agent AI assistant that routes natural language queries to specialized sub-agents — currently general chat (with web search) and Google Calendar management. The system is built around a classification layer that reads an incoming query, determines which domain agent should handle it, dispatches the request, executes any necessary tool calls, and returns a synthesized response.

The long-term goal is a personal assistant that can operate across multiple domains (calendar, email, tasks, search) from a single natural language interface, eventually running on fine-tuned local models rather than a hosted API.

---

## Architecture

```
User Query
    │
    ▼
ClassificationAgent       ← determines which domain the query belongs to
    │
    ▼
Domain Agent              ← BaseAgent (chat/web), CalenderAgent (EmailAgent, TaskAgent — planned)
    │
    ▼
Cura CLI (Rust)           ← handles gcal / web / time calls to external services
    │
    ▼
Response Handler          ← parses structured output, re-queries with tool results, returns final reply
```

Each agent (`src/agents/`) declares a Pydantic `response_model` (`src/models.py`) and queries its pipeline with `response_format` set to that model, so every LLM turn returns validated, structured JSON instead of free-text that needs manual parsing. The active pipeline is `OpenAIPipeline` (`src/pipelines.py`), which calls `client.chat.completions.parse` against the OpenAI API — a local, offline `HFPipeline` exists as a stub but currently raises `NotImplementedError` for structured output, so there is no working local-inference path yet despite `transformers`/`torch` being listed as dependencies.

API calls to external services are handled by **[cura](https://github.com/teighanmiller/cura/tree/main)**, a companion Rust CLI, invoked via `subprocess` from `Agent.handle_tool_call`. It currently exposes three subcommands: `gcal` (list/create/look up/delete events), `web` (DuckDuckGo search), and `time` (local date/time — used to ground the calendar agent's relative-date reasoning, e.g. "next Friday"). Keeping the API layer in a separate binary decouples the Python agent stack from network I/O and lets the CLI be used independently of the agent system.

A minimal Gradio chat UI (`src/chat.py`) is wired up to `backend.process_message`, which also writes a timed, per-turn JSONL trace to `logs/queries.log`.

---

## Current Development Phase

The project is in **Phase 1: Core Agent Loop**. The classification, chat, and calendar agents exist and complete an end-to-end query cycle with structured outputs. The focus right now is reliability of that loop (auth/timeout handling, prompt correctness) before expanding to additional domain agents.

### What works
- Query classification routing to the correct domain agent (`ClassificationResponse`, structured output)
- Google Calendar: list events, look up an event by name, create timed/all-day/recurring events, and delete an event by name — all via the `cura gcal` subcommand
- Date-aware calendar reasoning — the agent fetches the current datetime via `cura time` so it can resolve relative dates ("next Friday") instead of guessing
- General chat agent with web search fallback (`cura web`, DuckDuckGo)
- A 20s subprocess timeout around CLI tool calls, with a friendly re-auth prompt if the Google Calendar OAuth flow needs to be redone
- Basic Gradio chat UI (`src/chat.py`) wired to the backend
- Per-request timing instrumentation and JSONL query/conversation logging (`logs/queries.log`)

### What is still open
- **Conversation memory**: `Agent.memories` / `add_memory` exist but nothing currently populates them — no cross-turn memory is wired into `process_message` yet
- **Local/offline inference**: `HFPipeline` is a stub that raises `NotImplementedError`; the project currently depends on the OpenAI API rather than running fully locally
- Additional domain agents (email, tasks)
- Improved prompt templates / fewer malformed clarifying-question loops

---

## Known Issues

### 1. ~~Slow local inference~~ — resolved by switching to a hosted API

Earlier versions ran classification and response synthesis on a local `transformers` pipeline (e.g. Qwen2.5-3B-Instruct on CPU), with end-to-end latency around 78 seconds per calendar query. The project has since switched its active pipeline to `OpenAIPipeline`, which offloads inference to the OpenAI API. This resolves the latency problem but is a deliberate tradeoff against the original "no external API" goal — see [Design Considerations](#design-considerations--future-directions) below. Local inference (`HFPipeline`) is left as an unimplemented stub rather than removed, so the project can return to it once fine-tuned domain models are ready.

### 2. ~~Malformed response synthesis~~ — resolved by structured outputs

The model used to occasionally echo prompt fragments, truncate replies, or ignore tool output because responses were raw text manually parsed as JSON. Every agent now declares a Pydantic `response_model` (`src/models.py`) and calls `client.chat.completions.parse` with `response_format` set to it, so the API itself validates the shape of every response — `handle_response` works on typed model instances, not ad hoc dicts.

### 3. No conversation memory

`Agent.memories` / `add_memory` are defined but unused — `backend.process_message` creates no persistent session state between calls, so each query is handled independently with no history of prior turns.

### 4. No automated test coverage

There is no test suite yet (`pytest` is configured but has nothing to collect) — correctness is currently verified by manual exercising of the agent loop.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Inference | OpenAI API (`openai`), structured outputs via Pydantic (`pydantic`) |
| Local inference (stubbed, not yet working) | Hugging Face `transformers`, PyTorch |
| Chat UI | Gradio |
| API CLI | Rust ([cura](https://github.com/teighanmiller/cura/tree/main)) |
| API integrations | Google Calendar API, DuckDuckGo web search (via `cura`) |
| Linting / formatting | Ruff (pre-commit enforced) |
| Testing | pytest (no tests written yet) |
| Package management | uv |

---

## Getting Started

**Prerequisites:**
- Python 3.12+, [`uv`](https://github.com/astral-sh/uv)
- The [`cura`](https://github.com/teighanmiller/cura/tree/main) Rust CLI built and available on your `PATH` — agent tool calls shell out to it directly (`gcal`, `web`, `time` subcommands)
- An OpenAI API key (current inference backend)
- Google OAuth credentials for Calendar access

```bash
git clone <repo-url>
cd cura_agent

uv sync                      # install dependencies
echo "GPT_API_KEY=sk-..." > .env

uv run src/chat.py           # launches the Gradio chat UI
```

Google Calendar integration requires OAuth 2.0 credentials (`client_secret.json`) — see the [Google Calendar Python Quickstart](https://developers.google.com/calendar/api/quickstart/python). The first `cura gcal` call will prompt an OAuth flow and cache the resulting token; if a tool call ever times out, re-run `cura gcal event-list` in a terminal to re-authenticate.

---

## Design Considerations & Future Directions

### Skill files vs. separate agents

The current design uses a dedicated agent class per domain (calendar, email, etc.), each running its own inference pass. An alternative worth exploring is a **skill-file architecture** — a single model that selects and executes modular skill definitions at runtime rather than routing to entirely separate agents. This could reduce total inference passes per query and lower memory overhead from running multiple model instances. The tradeoff is that a generalist model handling all skills may be less reliable than a domain-specific one; the right answer likely depends on how far the fine-tuning work progresses.

### Fine-tuning

A core long-term goal of this project is **fine-tuning small LLMs for specific question types** (calendar queries, task management, etc.) rather than relying on large general-purpose models to handle everything well. The expectation is that a fine-tuned 1–3B parameter model can match or exceed the quality of a larger general model on a narrow domain, at a fraction of the inference cost. The agent-per-domain architecture is intentionally structured to make this incremental: each domain agent can be swapped for a fine-tuned model independently as training data is collected. In the meantime, the project uses the OpenAI API (via structured outputs) as the working inference backend — `HFPipeline` is kept as the intended seam for dropping local/fine-tuned models back in once they're ready, rather than reintroducing the latency and reliability issues the local `transformers` path originally had.

---

## Roadmap

- [x] Structured output for response synthesis (Pydantic `response_model` + `client.chat.completions.parse`)
- [x] Calendar event deletion (`delete-event`)
- [x] Date/time-aware calendar prompts (`cura time` grounding)
- [x] Minimal Gradio chat UI
- [ ] Wire up conversation memory across turns (scaffolding exists, unused)
- [ ] Restore a working local/offline inference path (`HFPipeline` currently stubbed)
- [ ] Replace LLM-based classifier with embedding/rules router
- [ ] Automated test coverage
- [ ] Email domain agent
- [ ] Task management domain agent
- [ ] Evaluate skill-file architecture as an alternative to per-domain agents
- [ ] Collect domain-specific training data for fine-tuning experiments

---

## License

MIT
