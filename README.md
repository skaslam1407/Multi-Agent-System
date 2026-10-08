# Intelligent Multi-Agent System

A manager-led multi-agent system that researches a task, writes Python code, and reviews/revises it until approved. Uses an OpenAI-compatible LLM endpoint (Ollama by default).

## How it works

```
User task -> Manager (agent/manager.py)
               |-- research -> workers/research_agent.py
               |-- coding   -> workers/coding_agent.py
               |-- review   -> workers/reviewer_agent.py (returns approved / needs_revision JSON)
               |-- finish
```

- `main.py` – CLI entry point, prompts for a task, runs the manager, prints RESEARCH / CODE / REVIEW.
- `agent/manager.py` – `choose_worker()` + `run_manager()` orchestration loop.
- `agent/state.py` – shared state dict (`task`, `research`, `code`, `review`, `history`, `revision_count`).
- `workers/` – `research_agent.py`, `coding_agent.py`, `reviewer_agent.py`.
- `llm.py` – `call_llm()` wrapper with retries/backoff (uses `openai` client against `BASE_URL`).
- `config.py` / `.env` – model, endpoint, retries, timeout, max revisions.
- `validation.py` – rejects empty / >5000 char tasks.
- `permissions.py` – per-agent tool allowlist + demo.
- `logger.py` – standard logging (`agent` logger).
- `animation.py` – terminal spinner (`with thinking("...")`) shown while the LLM is thinking. Set `NO_ANIMATION=1` to disable.

## Prerequisites

- Python 3.10+ (tested on 3.14.7)
- Ollama running locally **or** any OpenAI-compatible server
- A pulled model, e.g. `qwen2.5:1.5b`

## Setup

```bash
cd multi-agent

# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
# requirements: openai>=1.0.0, python-dotenv>=1.0.0, fastmcp>=0.1.0

# 3. Start Ollama (in a separate terminal)
ollama serve
ollama pull qwen2.5:1.5b

# 4. Configure environment
cp .env .env.local  # optional backup
```

Edit `.env`:

```env
MODEL=qwen2.5:1.5b
BASE_URL=http://localhost:11434/v1
API_KEY=ollama
MAX_REVISIONS=8
MAX_RETRIES=3
TIMEOUT=60
```

| Variable | Default in `config.py` | Description |
|---|---|---|
| `MODEL` | `qwen3:1.7b` | Model name served by Ollama |
| `BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible endpoint |
| `API_KEY` | `ollama` | Dummy key required by client (Ollama ignores it) |
| `MAX_REVISIONS` | `8` | Max code-write attempts before manager finishes |
| `MAX_RETRIES` | `3` | LLM request retries on failure |
| `TIMEOUT` | `60` | LLM request timeout (seconds) |

## Run

```bash
source .venv/bin/activate
python main.py
```

Each agent is called automatically by the manager LLM, call-by-call:
if an agent is not required for the task it is skipped and the flow
moves to the next one. No permission is asked from the user.

```bash
python main.py --task "write a palindrome function"
python main.py --no-research   # hard-disable research
python main.py --no-review     # hard-disable review
python main.py --verbose       # show INFO logs on console
python main.py --help
```

Console output stays clean: INFO logs go to `agent.log`, only
warnings/errors print to the console (plus the spinner animation).
Set `LOG_LEVEL=INFO` or pass `--verbose` to see full logs,
`NO_ANIMATION=1` to disable the spinner.

Then enter a task when prompted:

```
==================================================
 INTELLIGENT MULTI-AGENT SYSTEM
==================================================

Enter your task: write a python function to check palindrome

Manager selected: research
Manager selected: coding
Manager selected: review
Manager selected: finish

==================================================
 RESEARCH
==================================================
...

==================================================
 CODE
==================================================
...

==================================================
 REVIEW
==================================================
Status: approved
Feedback: The solution is correct.

Permission Demonstration
------------------------------
...
```

## Troubleshooting

- `LLM error: LLM request failed after 3 attempts.` – Ollama is not running, wrong `BASE_URL`, or model not pulled. Check with `curl http://localhost:11434/api/tags` and `ollama list`.
- `Validation error: Task cannot be empty.` – you pressed Enter with no input.
- `ValueError: Unknown worker: ...` – the manager LLM returned an unexpected word. Re-run; parsing accepts any response containing `research/coding/review/finish`.
- `ValueError: Reviewer returned invalid JSON` – reviewer output was not parseable JSON even after stripping ``` fences. Re-run or try a larger model.
- `(no final review - max revisions reached...)` – code never got `approved` within `MAX_REVISIONS`. Increase `MAX_REVISIONS` or clarify the task.
- Timeout issues – increase `TIMEOUT` in `.env` for slow machines/small models.

## Project structure

```
multi-agent/
├── main.py
├── config.py
├── llm.py
├── animation.py
├── logger.py
├── validation.py
├── permissions.py
├── requirements.txt
├── .env
├── agent/
│   ├── manager.py
│   └── state.py
└── workers/
    ├── research_agent.py
    ├── coding_agent.py
    └── reviewer_agent.py
```

While any agent waits for the LLM you will see e.g. `⠋ Research agent thinking...`.
Set `NO_ANIMATION=1 python main.py` to disable it (useful for logs/tests).
