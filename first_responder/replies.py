"""Compose the chat reply for a question, from the passages the keyword scan found."""

from __future__ import annotations

from collections.abc import Sequence

from first_responder.knowledge_base import KnowledgeBase
from first_responder.retrieval import Match, normalise, search, unmatched_terms

ASK_A_REAL_QUESTION = "That doesn't look like a question — try asking about Telikos in a few words."
NO_MATCH = "Nothing in the knowledge base matched that — try rephrasing."

_SEPARATOR = "\n\n---\n\n"


def format_terms(terms: Sequence[str]) -> str:
    """Render words as a bolded, comma-separated list, with ``and`` before the last."""
    bolded = [f"**{term}**" for term in terms]
    if len(bolded) == 1:
        return bolded[0]
    return f"{', '.join(bolded[:-1])} and {bolded[-1]}"


def format_matches(matches: Sequence[Match]) -> str:
    """Render each match as its source filename followed by the passage text in full."""
    return _SEPARATOR.join(
        f"**{match.passage.source}**\n\n{match.passage.text}" for match in matches
    )


def compose_reply(question: str, knowledge_base: KnowledgeBase) -> str:
    """Answer *question* from *knowledge_base*, or explain why there is nothing to show.

    A question with no words left after normalisation never reaches retrieval. When some of the
    question's words appear nowhere in the corpus, the reply says so before showing what did
    match — otherwise a partial answer reads as a confident whole one.
    """
    if not normalise(question):
        return ASK_A_REAL_QUESTION

    matches = search(question, knowledge_base.passages)
    if not matches:
        return NO_MATCH

    missing = unmatched_terms(question, knowledge_base.passages)
    if not missing:
        return format_matches(matches)

    caveat = f"Nothing in the knowledge base mentions {format_terms(missing)}. Here's what matched:"
    return f"{caveat}\n\n{format_matches(matches)}"
