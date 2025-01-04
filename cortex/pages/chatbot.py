# This module implements a simple chatbot interface using Streamlit and OpenAI's API.

# The UI includes:
# - A sidebar for entering the OpenAI API key.
# - A main area for displaying the chat interface and messages.

# Features:
# - Displays a title and caption for the chatbot.
# - Stores the OpenAI model and chat messages in the session state.
# - Allows users to input messages and receive responses from the OpenAI model.
# - Provides a button to clear the chat history.

# Note:
# This UI is intended to act as a playground and content management system for the admins of BrainSmith.
# It is not meant to be exposed on the public internet and should not be used as a client-facing interface.

from openai import OpenAI
import streamlit as st




with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"

st.title("💬Chatbot")
st.caption("🚀 A chatbot powered by OpenAI")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    if not openai_api_key:
        st.warning("Please add your OpenAI API key to continue.")
        st.stop()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = OpenAI(api_key=openai_api_key)
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})

if len(st.session_state.messages):
    if st.button("🗑️ Clear"):
        st.session_state.messages = []
        st.rerun()