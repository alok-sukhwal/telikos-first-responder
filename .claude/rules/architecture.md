---
description: Where architecture decisions live and when a new ADR is required.
alwaysApply: true
---

# Architecture decisions

Architecture and other costly-to-reverse decisions are recorded as ADRs in `docs/adr/`.
Read them before changing anything structural — they capture the *why*, not just the *what*.

**A new ADR (`docs/adr/NNNN-<slug>.md`) is REQUIRED before you:**
- make a breaking change to a decision already recorded in an ADR (e.g. swapping the retrieval
  approach, the UI framework, or the LLM seam);
- introduce a decision that is costly or painful to reverse (a database, an external service,
  a new architectural layer, a public interface contract).

If you're about to do one of these, STOP, propose the ADR, and wait for approval.
