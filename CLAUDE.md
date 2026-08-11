# Telikos First Responder

A chat agent that answers users' functional questions from a local knowledge base.
Full product intent lives in **docs/brief.md** — read it first.

## How to run

```bash
uv sync                       # install dependencies
uv run streamlit run app.py   # start the chat UI (http://localhost:8501)
uv run pytest                 # run the tests
uv run pytest --cov           # run the tests with line coverage; fails under 90%
```

## Rules

1. **Stay in scope.** Respect the MVP and out-of-scope lists in `docs/brief.md`. Don't add features that aren't asked for.
2. **Simplest retrieval.** Answers come from an in-memory keyword scan over local documents — no vector DB, no embeddings, unless a new ADR changes it.
3. **LLM behind a seam.** All answer generation goes through the `Answerer` interface. The default is a local, no-API-key stub; never commit secrets or hard-code a provider.
4. **Typed, linted, tested.** Type-hint every function. Run `uv run ruff format .`, `uv run ruff check .` and `uv run pytest` before calling work done. Tests are pytest, in one flat `tests/` directory — no unit/integration split.
5. **Decisions are recorded.** Architecture choices live in `docs/adr/`; propose a new ADR before any breaking or costly-to-reverse change.

## Where the detail lives

- **docs/brief.md** — product brief: the idea, the MVP, what's out of scope (the north star).
- **docs/adr/** — architecture decision records; `0001-initial-stack.md` explains the stack and why.

@.claude/rules/conventions.md
@.claude/rules/architecture.md
