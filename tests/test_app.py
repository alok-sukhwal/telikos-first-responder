"""The Streamlit app itself, driven through Streamlit's own AppTest harness."""

from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from first_responder import knowledge_base

APP = str(Path(__file__).parent.parent / "app.py")
FIXTURE_KB = Path(__file__).parent / "fixtures" / "kb"


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """Drive the real app over the fixture corpus rather than ``docs/kb/``.

    ``app.py`` resolves its own ``KB_DIR``, so the loader it imports is redirected instead.
    Asserting against production knowledge-base content would make a document rename — the
    expected workflow — fail the suite with no code defect.
    """
    load_real = knowledge_base.load_knowledge_base

    def load_fixture_kb(directory: Path) -> knowledge_base.KnowledgeBase:
        return load_real(FIXTURE_KB)

    monkeypatch.setattr(knowledge_base, "load_knowledge_base", load_fixture_kb)
    st.cache_resource.clear()
    return AppTest.from_file(APP, default_timeout=60).run()


def test_app_boots(app: AppTest) -> None:
    assert not app.exception
    assert app.title[0].value == "Telikos First Responder"


def test_a_question_is_answered_from_the_knowledge_base(app: AppTest) -> None:
    app.chat_input[0].set_value("how do I reset an invoice").run()

    reply = app.chat_message[-1].markdown[0].value
    assert not app.exception
    assert "**billing.md**" in reply
    assert "To reset an invoice, open it in Telikos and choose Reset." in reply


def test_the_app_under_test_is_not_reading_the_production_corpus(app: AppTest) -> None:
    """Proves the redirect above took effect, rather than the suite passing by coincidence."""
    app.chat_input[0].set_value("how do I reset an invoice").run()

    assert "billing-and-invoicing.md" not in app.chat_message[-1].markdown[0].value
