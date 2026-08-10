"""Telikos First Responder — Streamlit chat skeleton.

Hello-world entry point: renders a chat UI that boots and echoes a placeholder.
Retrieval and answer composition are not wired up yet — see docs/brief.md.
"""

import streamlit as st

st.set_page_config(page_title="Telikos First Responder", page_icon="💬")
st.title("Telikos First Responder")
st.caption("Skeleton — answering isn't wired up yet.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    reply = "🚧 First Responder is booting. Retrieval and answers aren't wired up yet."
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
