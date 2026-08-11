"""The Streamlit app itself, driven through Streamlit's own AppTest harness."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "app.py")


@pytest.fixture
def app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=60).run()


def test_app_boots(app: AppTest) -> None:
    assert not app.exception
    assert app.title[0].value == "Telikos First Responder"


def test_a_question_is_answered_from_the_knowledge_base(app: AppTest) -> None:
    app.chat_input[0].set_value("what is the default invoice trigger").run()

    assert not app.exception
    assert "billing-and-invoicing.md" in app.chat_message[-1].markdown[0].value
