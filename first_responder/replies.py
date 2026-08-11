"""Compose the chat reply for a question, from the passages the keyword scan found."""

from __future__ import annotations

from collections.abc import Sequence

from first_responder.knowledge_base import KnowledgeBase
from first_responder.retrieval import Match, normalise, search

ASK_A_REAL_QUESTION = "That doesn't look like a question — try asking about Telikos in a few words."
NO_MATCH = "Nothing in the knowledge base matched that — try rephrasing."

_SEPARATOR = "\n\n---\n\n"


def format_matches(matches: Sequence[Match]) -> str:
    """Render each match as its source filename followed by the passage text in full."""
    return _SEPARATOR.join(
        f"**{match.passage.source}**\n\n{match.passage.text}" for match in matches
    )


def compose_reply(question: str, knowledge_base: KnowledgeBase) -> str:
    """Answer *question* from *knowledge_base*, or explain why there is nothing to show.

    A question with no words left after normalisation never reaches retrieval.
    """
    if not normalise(question):
        return ASK_A_REAL_QUESTION

    matches = search(question, knowledge_base.passages)
    return format_matches(matches) if matches else NO_MATCH
