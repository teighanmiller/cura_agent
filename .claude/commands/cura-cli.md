# cura CLI Reference

You are being given full context about the `cura` Rust CLI so you can answer questions about it, invoke it correctly, or help extend it.

**Source:** https://github.com/teighanmiller/cura  
**Binary name:** `cura`  
**Language:** Rust (edition 2024), async via Tokio  
**Purpose:** A personal productivity CLI and the tool layer for the `cura_agent` AI agent project. Each subcommand is a discrete, testable operation the agent calls by name with well-defined arguments — analogous to an MCP server exposing capabilities to a model.

---

## Architecture

Top-level subcommands (defined in `main.rs`):

| Subcommand | Module | Description |
|---|---|---|
| `gcal` | `google_cal.rs` | Google Calendar operations |
| `web` | `web.rs` | DuckDuckGo web search |


---

## Subcommand reference

### `cura gcal` — Google Calendar

Three sub-subcommands defined in `GcalCommands` enum (`google_cal.rs`):

#### `event-list`
List events. Defaults to today if no range given.

```bash
cura gcal event-list
cura gcal event-list --start-time "2026-04-24 09:00:00 +0000" --end-time "2026-04-24 17:00:00 +0000"
```

- `start_time` / `end_time`: optional. Format: `"YYYY-MM-DD HH:MM:SS ±HHMM"`
- Without args, `get_period(&[])` returns a today-scoped window.

#### `event-details`
Look up a specific event by name keyword. Optionally scoped to a time range.

```bash
cura gcal event-details --name "Team standup"
cura gcal event-details --name "standup" --start-time "2026-04-24 09:00:00 +0000" --end-time "2026-04-24 17:00:00 +0000"
```

- `name`: required string; passed as `q` parameter to the Calendar API.
- `start_time` / `end_time`: optional. Same format as `event-list`.

#### `new-event`
Create a calendar event. Supports all-day (date only) or timed events, with optional recurrence.

```bash
# All-day event
cura gcal new-event --name "Conference" --description "Annual conf" --date 2026-05-01

# Timed event
cura gcal new-event --name "Standup" --description "Daily sync" --date 2026-04-24 --start-time "09:00:00" --end-time "09:30:00"

# Recurring timed event
cura gcal new-event --name "Weekly review" --description "Weekly" --date 2026-04-24 --start-time "10:00:00" --end-time "10:30:00" --freq weekly
```

- `name`: required
- `description`: optional
- `date`: `YYYY-MM-DD` (required for all-day; also used as base date for timed events)
- `start-time` / `end-time` (event creation): `HH:MM:SS` — if both provided, creates a timed event; otherwise all-day
- `freq`: optional recurrence — values: `daily`, `weekly`, `monthly`, `yearly` — maps to `RRULE:FREQ=...`
- All events are inserted into the `"primary"` calendar.

**Date/time format summary:**

| Flag | Context | Format |
|---|---|---|
| `--date` | new-event | `YYYY-MM-DD` |
| `--start-time` / `--end-time` | new-event (timed) | `HH:MM:SS` |
| `--start-time` / `--end-time` | event-list / event-details | `YYYY-MM-DD HH:MM:SS ±HHMM` |

---

### `cura web` — Web search

```bash
cura web "your search query"
cura web "your search query" --max-value 5
cura web "your search query" --engine duck-duck-go
```

- Positional arg: search query string (required)
- `--max-value`: limit number of results returned
- `--engine`: search provider; currently only `duck-duck-go` is supported

---

## Auth flow

Defined in `auth.rs`. On first run, `cura` opens a browser OAuth consent screen. The resulting token is stored in `token_cache.json` at the project root. Subsequent runs reuse the cached token without re-prompting.

Requires `client_secret.json` (Google OAuth 2.0 Desktop credentials) in the project root. Get this from the Google Cloud Console with the Calendar API enabled.

---

## Build and install

```bash
cargo build --release
# Binary: target/release/cura
cp target/release/cura /usr/local/bin/   # optional: add to PATH
```
---

## Role in cura_agent

`cura` is the **tool layer** for the `cura_agent` project (`https://github.com/teighanmiller/cura_agent`). The agent invokes `cura` subcommands as discrete, structured operations rather than calling Google APIs directly. This keeps the agent interface stable and each operation independently testable.
