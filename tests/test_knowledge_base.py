"""Loading the knowledge base: passage splitting, filtering and failure handling."""

from pathlib import Path

import pytest

from first_responder.knowledge_base import load_knowledge_base, split_passages

FIXTURE_KB = Path(__file__).parent / "fixtures" / "kb"


def test_loads_passages_from_every_markdown_file() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert [(p.source, p.position) for p in kb.passages] == [
        ("billing.md", 0),
        ("billing.md", 1),
        ("headings.md", 0),
        ("headings.md", 1),
        ("headings.md", 2),
        ("setup.md", 0),
        ("setup.md", 1),
    ]
    assert kb.warnings == ()


def test_passages_are_trimmed_and_never_empty() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert all(p.text == p.text.strip() for p in kb.passages)
    assert all(p.text for p in kb.passages)


def test_passage_text_is_byte_identical_to_the_source() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    first = next(p for p in kb.passages if p.source == "billing.md" and p.position == 0)
    assert first.text == (
        "To reset an invoice, open it in Telikos and choose Reset. The invoice\n"
        "returns to draft so the charges can be edited again."
    )


def test_no_passage_line_is_invented_or_altered() -> None:
    """The loader removes blank lines between blocks and rewrites nothing else."""
    kb = load_knowledge_base(FIXTURE_KB)
    sources = {
        path.name: path.read_text(encoding="utf-8").splitlines() for path in FIXTURE_KB.glob("*.md")
    }

    for p in kb.passages:
        for line in p.text.splitlines():
            assert line in sources[p.source], f"{p.source}: {line!r} is not a line of the source"


def test_consecutive_blank_lines_do_not_produce_empty_passages() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    setup = [p for p in kb.passages if p.source == "setup.md"]
    assert len(setup) == 2
    assert setup[1].text == "The client lists recent invoices on its home screen."


def test_other_extensions_and_subfolders_are_ignored() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert {p.source for p in kb.passages} == {"billing.md", "headings.md", "setup.md"}


def test_missing_directory_yields_no_passages_and_no_exception() -> None:
    kb = load_knowledge_base(FIXTURE_KB / "does-not-exist")

    assert kb.passages == ()
    assert len(kb.warnings) == 1


def test_directory_without_markdown_warns_and_still_loads(tmp_path: Path) -> None:
    (tmp_path / "readme.txt").write_text("nothing to index", encoding="utf-8")

    kb = load_knowledge_base(tmp_path)

    assert kb.passages == ()
    assert len(kb.warnings) == 1


def test_undecodable_file_is_skipped_by_name_and_others_still_load(tmp_path: Path) -> None:
    (tmp_path / "good.md").write_text("A readable passage about invoices.", encoding="utf-8")
    (tmp_path / "broken.md").write_bytes(b"\xff\xfe not valid utf-8 \xff")

    kb = load_knowledge_base(tmp_path)

    assert [p.source for p in kb.passages] == ["good.md"]
    assert len(kb.warnings) == 1
    assert "broken.md" in kb.warnings[0]


def test_document_like_files_that_are_not_md_are_named_in_a_warning(tmp_path: Path) -> None:
    (tmp_path / "loaded.md").write_text("A passage about invoices.", encoding="utf-8")
    (tmp_path / "dropped-in.mdx").write_text("# Ignored\n\nBody.", encoding="utf-8")

    kb = load_knowledge_base(tmp_path)

    assert [p.source for p in kb.passages] == ["loaded.md"]
    assert len(kb.warnings) == 1
    assert "dropped-in.mdx" in kb.warnings[0]


# --- passage splitting: a heading is joined to the body it labels ---


def test_heading_is_joined_to_the_body_that_follows_it() -> None:
    assert split_passages("## Head\n\nBody here.") == ["## Head\nBody here."]


def test_several_blank_lines_after_a_heading_still_join() -> None:
    assert split_passages("## Head\n\n\nBody here.") == ["## Head\nBody here."]


def test_consecutive_heading_blocks_join_to_the_same_body() -> None:
    assert split_passages("## A\n\n### B\n\nBody.") == ["## A\n### B\nBody."]


def test_a_block_of_several_heading_lines_joins_as_one() -> None:
    assert split_passages("## A\n### B\n\nBody.") == ["## A\n### B\nBody."]


def test_heading_with_no_body_at_end_of_file_survives_alone() -> None:
    assert split_passages("Body.\n\n## Trailing") == ["Body.", "## Trailing"]


def test_a_passage_that_already_has_a_body_is_not_joined_onward() -> None:
    """Re-running over an already-joined document must not merge further."""
    assert split_passages("## A\nbody\n\nmore") == ["## A\nbody", "more"]


def test_documents_without_headings_split_on_blank_lines_as_before() -> None:
    assert split_passages("p1\n\np2") == ["p1", "p2"]


@pytest.mark.parametrize("text", ["#hashtag topic", "####### seven hashes"])
def test_hash_shapes_that_are_not_headings_are_body_text(text: str) -> None:
    assert split_passages(f"{text}\n\nnext") == [text, "next"]


@pytest.mark.parametrize("document", ["", "   \n\n  "])
def test_empty_documents_yield_no_passages(document: str) -> None:
    assert split_passages(document) == []
