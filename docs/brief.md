# Telikos First Responder — product brief

## What this is

Telikos First Responder is the first line of support for Telikos users: a chat agent that
answers users' functional questions. A user asks a question in a chat UI; the agent finds the
relevant material in a local knowledge base of documents and composes a plain-language answer
from it. It exists to deflect routine "how do I… / what is…" questions so people get an
instant, grounded answer instead of waiting on a human.

## MVP (in scope)

- A single-page **chat UI** — type a question, get an answer.
- A **knowledge base** built from a small set of **local documents** dropped into the project.
- **Simplest retrieval:** an in-memory keyword scan finds the passages most relevant to the
  question — no vector database, no embeddings.
- An **LLM composes the answer** from the retrieved passages, behind a pluggable `Answerer`
  seam. For now the default is a **local stub** that needs no API key; a real model can be
  swapped in later without touching the rest of the app.

## Out of scope (deliberately, for the MVP)

- User accounts, authentication, multi-tenant / multi-user separation.
- Conversation memory across sessions — each question stands on its own.
- Live ingestion from external systems (Confluence, ticketing, email, etc.).
- Streaming responses, feedback controls (👍/👎), and analytics.
- Source citations in answers — a nice-to-have, not required for the MVP.

## North star

Answer a real user question, from real local docs, in the chat UI, well enough that a person
would have been happy to receive it. Everything above is in service of that; anything that
doesn't move it is out.
