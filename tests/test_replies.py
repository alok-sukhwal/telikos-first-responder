"""Reply composition: which branch a question takes and how passages are rendered."""

from pathlib import Path

import pytest

from first_responder import replies
from first_responder.knowledge_base import KnowledgeBase, load_knowledge_base
from first_responder.replies import ASK_A_REAL_QUESTION, NO_MATCH, compose_reply

FIXTURE_KB = Path(__file__).parent / "fixtures" / "kb"


@pytest.fixture
def knowledge_base() -> KnowledgeBase:
    return load_knowledge_base(FIXTURE_KB)


def test_reply_labels_each_passage_with_its_source_filename(
    knowledge_base: KnowledgeBase,
) -> None:
    reply = compose_reply("how do I reset an invoice", knowledge_base)

    assert "**billing.md**" in reply
    assert "To reset an invoice, open it in Telikos and choose Reset." in reply


def test_reply_never_truncates_a_passage(knowledge_base: KnowledgeBase) -> None:
    reply = compose_reply("reset invoice", knowledge_base)

    expected = next(p for p in knowledge_base.passages if p.position == 0)
    assert expected.text in reply


def test_unmatched_question_gets_the_no_match_message(knowledge_base: KnowledgeBase) -> None:
    assert compose_reply("zzzz quantum", knowledge_base) == NO_MATCH


@pytest.mark.parametrize("question", ["", "   ", "the and of", "?!"])
def test_empty_question_takes_the_ask_a_real_question_branch(
    question: str, knowledge_base: KnowledgeBase
) -> None:
    assert compose_reply(question, knowledge_base) == ASK_A_REAL_QUESTION


@pytest.mark.parametrize("question", ["", "   ", "the and of"])
def test_retrieval_is_never_invoked_for_an_empty_question(
    question: str, knowledge_base: KnowledgeBase, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("search() should not run for a question with no words")

    monkeypatch.setattr(replies, "search", fail)

    assert compose_reply(question, knowledge_base) == ASK_A_REAL_QUESTION


def test_empty_knowledge_base_falls_through_to_the_no_match_message() -> None:
    assert compose_reply("reset invoice", KnowledgeBase()) == NO_MATCH
