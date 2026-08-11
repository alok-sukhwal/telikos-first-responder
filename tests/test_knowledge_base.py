"""Loading the knowledge base: passage splitting, filtering and failure handling."""

from pathlib import Path

from first_responder.knowledge_base import load_knowledge_base

FIXTURE_KB = Path(__file__).parent / "fixtures" / "kb"


def test_loads_passages_from_every_markdown_file() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert [(p.source, p.position) for p in kb.passages] == [
        ("billing.md", 0),
        ("billing.md", 1),
        ("setup.md", 0),
        ("setup.md", 1),
    ]
    assert kb.warnings == ()


def test_passages_are_trimmed_and_never_empty() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert all(p.text == p.text.strip() for p in kb.passages)
    assert all(p.text for p in kb.passages)


def test_passage_text_is_byte_identical_to_the_source_paragraph() -> None:
    kb = load_knowledge_base(FIXTURE_KB)
    source = (FIXTURE_KB / "billing.md").read_text(encoding="utf-8")

    first = next(p for p in kb.passages if p.source == "billing.md" and p.position == 0)
    assert first.text == source.split("\n\n")[0].strip()
    assert first.text == (
        "To reset an invoice, open it in Telikos and choose Reset. The invoice\n"
        "returns to draft so the charges can be edited again."
    )


def test_consecutive_blank_lines_do_not_produce_empty_passages() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    setup = [p for p in kb.passages if p.source == "setup.md"]
    assert len(setup) == 2
    assert setup[1].text == "The client lists recent invoices on its home screen."


def test_other_extensions_and_subfolders_are_ignored() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert {p.source for p in kb.passages} == {"billing.md", "setup.md"}


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
