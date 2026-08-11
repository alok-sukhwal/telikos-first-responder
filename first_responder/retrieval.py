"""Rank knowledge-base passages against a question with an in-memory keyword scan."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from first_responder.knowledge_base import Passage

STOP_WORDS = frozenset(
    """
    a an and are as at be but by can do does for from how i in is it of on or that the to
    what when where which who why with you
    """.split()
)

DEFAULT_LIMIT = 3

_PUNCTUATION = re.compile(r"[^\w\s]")


@dataclass(frozen=True)
class Match:
    """A passage and the number of distinct question words it contains."""

    passage: Passage
    score: int


def normalise(text: str) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace and drop stop words.

    Applied identically to questions and to passage text, so Markdown syntax such as ``##``
    disappears rather than becoming a token of its own.
    """
    words = _PUNCTUATION.sub(" ", text.lower()).split()
    return [word for word in words if word not in STOP_WORDS]


def search(question: str, passages: Sequence[Passage], limit: int = DEFAULT_LIMIT) -> list[Match]:
    """Return up to *limit* passages scoring at least 1, best first.

    A passage scores one point per *distinct* question word whose exact token appears in it —
    no stemming, no synonyms, no substring matching. Ties break by filename A→Z, then by
    position within the file.
    """
    query = set(normalise(question))
    if not query:
        return []

    matches = [
        Match(passage, score)
        for passage in passages
        if (score := len(query & set(normalise(passage.text)))) > 0
    ]
    matches.sort(key=lambda match: (-match.score, match.passage.source, match.passage.position))
    return matches[:limit]
