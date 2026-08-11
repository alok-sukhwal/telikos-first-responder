"""Scoring and ranking: distinct-word scoring, tie-breaks and the top-3 cut."""

from pathlib import Path

from first_responder.knowledge_base import Passage, load_knowledge_base
from first_responder.retrieval import (
    document_frequencies,
    normalise,
    search,
    term_weight,
    unmatched_terms,
)

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
    assert matches[0].score > matches[1].score


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
    assert matches[0].score > matches[1].score


def test_repeated_word_in_a_passage_scores_once() -> None:
    once = passage("a.md", 0, "invoice")
    many = passage("b.md", 0, "invoice invoice invoice invoice invoice")

    matches = search("invoice", [once, many])

    assert len({m.score for m in matches}) == 1


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


# --- rarity weighting: a corpus-wide word must not tie with a discriminating one ---


def test_a_rare_word_outranks_a_corpus_wide_one() -> None:
    """Under flat scoring both of these score 1 and document order decides."""
    passages = [
        passage("a.md", 0, "invoice mentioned here"),
        passage("b.md", 0, "invoice and the rare word telescope"),
        passage("c.md", 0, "invoice again"),
        passage("d.md", 0, "invoice yet again"),
    ]

    matches = search("telescope", passages)
    common = search("invoice", passages)

    assert [m.passage.source for m in matches] == ["b.md"]
    assert matches[0].score > common[0].score


def test_matching_one_rare_word_beats_matching_one_common_word() -> None:
    passages = [
        passage("common.md", 0, "invoice one"),
        passage("common.md", 1, "invoice two"),
        passage("common.md", 2, "invoice three"),
        passage("rare.md", 0, "telescope"),
    ]

    matches = search("invoice telescope", passages)

    assert matches[0].passage.source == "rare.md"


def test_a_word_in_every_passage_still_scores_above_zero() -> None:
    """Weighting must not silence a word just because it is everywhere."""
    passages = [passage("a.md", 0, "invoice"), passage("b.md", 0, "invoice")]

    matches = search("invoice", passages)

    assert len(matches) == 2
    assert all(m.score > 0 for m in matches)


def test_term_weight_falls_as_a_word_gets_more_common() -> None:
    assert term_weight(1, 100) > term_weight(50, 100) > term_weight(100, 100) > 0


def test_document_frequencies_counts_passages_not_occurrences() -> None:
    passages = [passage("a.md", 0, "invoice invoice invoice"), passage("b.md", 0, "invoice")]

    assert document_frequencies(passages)["invoice"] == 2


# --- naming the words the corpus has never seen ---


def test_unmatched_terms_names_words_absent_from_the_corpus() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert unmatched_terms("how do I archive an invoice", kb.passages) == ["archive"]


def test_unmatched_terms_keeps_question_order_and_drops_duplicates() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert unmatched_terms("zebra archive zebra", kb.passages) == ["zebra", "archive"]


def test_unmatched_terms_is_empty_when_every_word_matched() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert unmatched_terms("reset invoice", kb.passages) == []


def test_question_matching_nothing_returns_no_results() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert search("zzzz quantum", kb.passages) == []


def test_question_of_only_stop_words_returns_no_results() -> None:
    kb = load_knowledge_base(FIXTURE_KB)

    assert search("the and of", kb.passages) == []
