"""Load the local knowledge base: Markdown documents split into passages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_BLANK_LINE = re.compile(r"\n\s*\n")
_HEADING_LINE = re.compile(r"^ {0,3}#{1,6}(\s|$)")
_IGNORED_SUFFIXES = frozenset({".mdx", ".markdown", ".rst"})


@dataclass(frozen=True)
class Passage:
    """One block of text from a knowledge-base document, kept exactly as written."""

    source: str
    position: int
    text: str


@dataclass(frozen=True)
class KnowledgeBase:
    """Passages loaded from disk, plus any warnings raised while loading."""

    passages: tuple[Passage, ...] = ()
    warnings: tuple[str, ...] = ()


def _is_heading_only(block: str) -> bool:
    """True if every line of *block* is a Markdown ATX heading (``#`` … ``######``).

    Deliberately strict: ``#hashtag`` and ``#######`` are body text, not headings, so a block
    containing them is never treated as a label with no content of its own.
    """
    return all(_HEADING_LINE.match(line) for line in block.splitlines())


def split_passages(document: str) -> list[str]:
    """Split a document into passages: blank-line blocks, with headings joined to their body.

    A block whose every line is a heading is a label, not an answer — on its own it matches a
    question's topic words while containing nothing that answers them. Such a block is joined,
    with a single newline, to the next block that has a body; consecutive heading blocks join to
    that same body. So a document written in idiomatic Markdown, with a blank line after each
    heading, yields the same passages as one where heading and body are already adjacent.

    A heading with nothing after it stays a passage of its own, since there is nothing to join it
    to. Otherwise no passage is heading-only.
    """
    passages: list[str] = []
    pending: list[str] = []
    for block in _BLANK_LINE.split(document):
        block = block.strip()
        if not block:
            continue
        if _is_heading_only(block):
            pending.append(block)
            continue
        passages.append("\n".join([*pending, block]))
        pending.clear()

    if pending:
        passages.append("\n".join(pending))
    return passages


def load_knowledge_base(directory: Path) -> KnowledgeBase:
    """Load every ``*.md`` file directly inside *directory*, in filename order.

    Sub-folders and other extensions are ignored. A file that cannot be read or decoded is
    skipped with a warning naming it; the remaining documents still load. Files that look like
    documents but are not ``.md`` are also named in a warning, so a dropped-in file that will
    never be searched says so rather than disappearing.
    """
    if not directory.is_dir():
        return KnowledgeBase(warnings=(f"Knowledge base directory not found: {directory}",))

    documents = sorted(path for path in directory.glob("*.md") if path.is_file())
    if not documents:
        return KnowledgeBase(warnings=(f"No .md documents found in {directory}",))

    passages: list[Passage] = []
    warnings: list[str] = []
    ignored = sorted(
        path.name
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in _IGNORED_SUFFIXES
    )
    if ignored:
        warnings.append(
            f"Not loaded — only .md documents are searched: {', '.join(ignored)}. "
            "Rename to .md to include it."
        )

    for path in documents:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            warnings.append(f"Skipped {path.name} — could not be read: {exc}")
            continue
        passages.extend(
            Passage(source=path.name, position=position, text=block)
            for position, block in enumerate(split_passages(text))
        )

    return KnowledgeBase(tuple(passages), tuple(warnings))
