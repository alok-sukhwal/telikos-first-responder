# ADR 0001 — Initial stack

- **Status:** Accepted
- **Date:** 2026-08-10

## Context

Telikos First Responder is a 1.5-day MVP: a single-page chat UI that answers users' functional
questions from a small set of local documents. Priorities are shipping something that runs
end-to-end quickly, keeping infrastructure at zero, and not painting ourselves into a corner on
the parts most likely to change (the knowledge source and the LLM). See docs/brief.md.

## Decision

1. **Language: Python (≥ 3.11).** Chosen by the team; fits the retrieval + LLM problem.
2. **UI: Streamlit.** A working chat UI in a few lines with almost no frontend code — the
   fastest path to an end-to-end app in the timebox. Chosen over FastAPI + a hand-rolled
   HTML/JS frontend, which would spend build time on plumbing we don't need yet.
3. **Package manager: uv.** Fast, modern, single-tool dependency and environment management.
4. **Retrieval: in-memory keyword scan, no storage.** The document set is small and the build
   is short, so we scan documents in memory per query. Chosen over in-memory embeddings and
   over a real vector DB, both of which add setup disproportionate to the MVP.
5. **Answer generation: an `Answerer` seam with a local stub default.** Answer composition sits
   behind a single interface. The MVP default is a local stub that needs no API key, so the app
   runs for everyone today; a real LLM (Claude, a local model, …) is a one-file swap later.
6. **Project layout: flat package.** Application code in `first_responder/`, entry point
   `app.py` at the root. No `src/` indirection or build step for a project this size.

## Consequences

- The app runs end-to-end on day one with zero external services and no secrets.
- Keyword retrieval will miss meaning-based matches (synonyms, paraphrases); if answer quality
  demands it, moving to embeddings is a **new ADR** (it changes decision 4).
- Swapping in a real LLM is cheap and localised, but the stub's answers are intentionally basic
  until then.
- Streamlit trades fine-grained UI control for speed; a richer or embeddable UI later would be a
  **new ADR** (it changes decision 2).
