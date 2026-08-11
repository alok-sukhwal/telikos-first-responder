"""Rank knowledge-base passages against a question with an in-memory keyword scan."""

from __future__ import annotations

import math
import re
from collections import Counter
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
    """A passage and its score: the combined rarity of the question words it contains."""

    passage: Passage
    score: float


def normalise(text: str) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace and drop stop words.

    Applied identically to questions and to passage text, so Markdown syntax such as ``##``
    disappears rather than becoming a token of its own.
    """
    words = _PUNCTUATION.sub(" ", text.lower()).split()
    return [word for word in words if word not in STOP_WORDS]


def document_frequencies(passages: Sequence[Passage]) -> Counter[str]:
    """Count how many passages each word appears in. Recomputed per query — nothing is stored."""
    frequencies: Counter[str] = Counter()
    for passage in passages:
        frequencies.update(set(normalise(passage.text)))
    return frequencies


def term_weight(frequency: int, total: int) -> float:
    """How much a word is worth: rarer words weigh more.

    ``log(1 + total / frequency)`` — always positive, so a word appearing in *every* passage
    still counts for something rather than dropping to zero and hiding its passages entirely.
    """
    return math.log(1 + total / frequency)


def unmatched_terms(question: str, passages: Sequence[Passage]) -> list[str]:
    """Question words that appear in no passage at all, in the order they were asked.

    A word the corpus has never heard of is usually the one that mattered. Naming it lets the
    reply say what it does not know instead of quietly answering a narrower question.
    """
    frequencies = document_frequencies(passages)
    return [word for word in dict.fromkeys(normalise(question)) if word not in frequencies]


def search(question: str, passages: Sequence[Passage], limit: int = DEFAULT_LIMIT) -> list[Match]:
    """Return up to *limit* passages containing at least one question word, best first.

    A passage scores the summed *weight* of the distinct question words whose exact token
    appears in it — no stemming, no synonyms, no substring matching. Weighting by rarity keeps
    a word like ``invoice``, which is in most of the corpus, from tying every passage that
    mentions it against one that matches a genuinely discriminating word. Ties break by
    filename A→Z, then by position within the file.
    """
    query = set(normalise(question))
    if not query or not passages:
        return []

    total = len(passages)
    frequencies = document_frequencies(passages)

    matches = []
    for passage in passages:
        hits = query & set(normalise(passage.text))
        if hits:
            score = sum(term_weight(frequencies[word], total) for word in hits)
            matches.append(Match(passage, score))

    matches.sort(key=lambda match: (-match.score, match.passage.source, match.passage.position))
    return matches[:limit]
