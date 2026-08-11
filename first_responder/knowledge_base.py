"""Load the local knowledge base: Markdown documents split into passages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_BLANK_LINE = re.compile(r"\n\s*\n")


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


def split_passages(document: str) -> list[str]:
    """Split a document on blank lines, trimming each block and dropping empty ones."""
    return [block.strip() for block in _BLANK_LINE.split(document) if block.strip()]


def load_knowledge_base(directory: Path) -> KnowledgeBase:
    """Load every ``*.md`` file directly inside *directory*, in filename order.

    Sub-folders and other extensions are ignored. A file that cannot be read or decoded is
    skipped with a warning naming it; the remaining documents still load.
    """
    if not directory.is_dir():
        return KnowledgeBase(warnings=(f"Knowledge base directory not found: {directory}",))

    documents = sorted(path for path in directory.glob("*.md") if path.is_file())
    if not documents:
        return KnowledgeBase(warnings=(f"No .md documents found in {directory}",))

    passages: list[Passage] = []
    warnings: list[str] = []
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
