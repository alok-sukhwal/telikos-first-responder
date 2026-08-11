"""Telikos First Responder — Streamlit chat over a local knowledge base.

Entry point: renders the chat UI, loads the documents in ``docs/kb/`` once, and answers each
question with the passages that best match it. Answer composition through the ``Answerer`` seam
is a later slice — see docs/brief.md.
"""

from pathlib import Path

import streamlit as st

from first_responder.knowledge_base import KnowledgeBase, load_knowledge_base
from first_responder.replies import compose_reply

KB_DIR = Path(__file__).parent / "docs" / "kb"


@st.cache_resource
def get_knowledge_base() -> KnowledgeBase:
    """Load the knowledge base once per app process; editing docs/kb/ needs a restart."""
    return load_knowledge_base(KB_DIR)


st.set_page_config(page_title="Telikos First Responder", page_icon="💬")
st.title("Telikos First Responder")
st.caption("Ask a functional question — answers come from the local knowledge base.")

knowledge_base = get_knowledge_base()
for warning in knowledge_base.warnings:
    st.warning(warning)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    reply = compose_reply(prompt, knowledge_base)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
