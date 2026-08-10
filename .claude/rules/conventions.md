---
description: Always-on coding conventions for Telikos First Responder.
alwaysApply: true
---

# Coding conventions

- **Language:** Python ≥ 3.11. Type-hint every function signature.
- **Formatting & linting:** Ruff is the single tool. Run `uv run ruff format .` and
  `uv run ruff check .` before considering work done; fix what it flags.
- **Layout:** flat package — application code lives in `first_responder/`, the Streamlit
  entry point is `app.py` at the repo root. No `src/` indirection for a build this size.
- **Style:** prefer small, plain functions over classes until state or polymorphism actually
  justifies a class (the pluggable `Answerer` is a deliberate exception).
- **Docstrings:** module- and public-function-level docstrings, short and purposeful. Skip
  the obvious.
- **Dependencies:** add with `uv add`; keep them few. A new runtime dependency for the MVP is
  a decision — call it out.
- **Secrets:** never commit API keys. LLM credentials load from the environment only.
