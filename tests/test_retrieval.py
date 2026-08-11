"""Scoring and ranking: distinct-word scoring, tie-breaks and the top-3 cut."""

from pathlib import Path

from first_responder.knowledge_base import Passage, load_knowledge_base
from first_responder.retrieval import normalise, search

FIXTURE_KB = Path(__file__).parent / "fixtures" / "kb"


def passage(source: str, position: int, text: str) -> Passage:
    return Passage(source=source, position=position, text=text)


def test_normalise_lowercases_strips_punctuation_and_drops_stop_words() -> None:
    assert normalise("How do I reset an invoice?") == ["reset", "invoice"]


def test_markdown_syntax_is_not_a_token_of_its_own() -> None:
    assert normalise("## Default invoice trigger") == ["default", "invoice", "trigger"]


def test_top_passage_is_the_invoice_reset_paragraph() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    matches = search("how do I reset an invoice", kb.passages)

    assert matches[0].passage.source == "billing.md"
    assert matches[0].passage.position == 0
    assert matches[0].score == 2


def test_a_question_matching_only_a_heading_still_returns_the_answer() -> None:
    """ "window" appears only in headings.md's heading; the answer is in the body below it."""
    kb = load_knowledge_base(FIXTURE_KB)

    matches = search("how long is the refund window", kb.passages)

    assert matches[0].passage.source == "headings.md"
    assert (
        "A refund can be requested within fourteen days of the charge." in matches[0].passage.text
    )


def test_two_distinct_matches_outrank_one() -> None:
    passages = [
        passage("a.md", 0, "This mentions invoice only."),
        passage("b.md", 0, "This mentions reset and invoice together."),
    ]

    matches = search("reset invoice", passages)

    assert [m.passage.source for m in matches] == ["b.md", "a.md"]
    assert [m.score for m in matches] == [2, 1]


def test_repeated_word_in_a_passage_scores_once() -> None:
    once = passage("a.md", 0, "invoice")
    many = passage("b.md", 0, "invoice invoice invoice invoice invoice")

    matches = search("invoice", [once, many])

    assert {m.score for m in matches} == {1}


def test_repeated_word_in_the_question_does_not_change_ranking() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    once = search("invoice", kb.passages)
    twice = search("invoice invoice", kb.passages)

    assert [(m.passage.source, m.passage.position, m.score) for m in once] == [
        (m.passage.source, m.passage.position, m.score) for m in twice
    ]


def test_returns_at_most_three_ordered_by_score_then_filename_then_position() -> None:
    passages = [
        passage("b.md", 1, "invoice reset"),
        passage("a.md", 0, "invoice"),
        passage("a.md", 1, "invoice reset"),
        passage("c.md", 0, "invoice"),
        passage("b.md", 0, "invoice"),
    ]

    matches = search("reset invoice", passages)

    assert [(m.passage.source, m.passage.position) for m in matches] == [
        ("a.md", 1),
        ("b.md", 1),
        ("a.md", 0),
    ]


def test_ties_break_on_alphabetically_earlier_filename() -> None:
    passages = [passage("z.md", 0, "invoice"), passage("a.md", 0, "invoice")]

    matches = search("invoice", passages)

    assert [m.passage.source for m in matches] == ["a.md", "z.md"]


def test_no_stemming_or_substring_matching() -> None:
    passages = [passage("a.md", 0, "The client lists recent invoices.")]

    assert search("invoice", passages) == []


def test_question_matching_nothing_returns_no_results() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert search("zzzz quantum", kb.passages) == []


def test_question_of_only_stop_words_returns_no_results() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert search("the and of", kb.passages) == []
