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

import requests
import json

import streamlit as st
from openai import OpenAI




with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"

st.title("💬Chatbot")
st.caption("🚀 A chatbot powered by OpenAI")
def get_embedded_names():
    """
    GET endpoint to retrieve the list of names that have been embedded.
    """

    url = "http://localhost:8000/embedding/names"
    response = requests.request("GET", url)
    response.raise_for_status()
    try:
        return response.json()
    except json.JSONDecodeError as e:
        st.error(f"Failed to decode JSON response: {e}")
        return []

embedded_names = get_embedded_names()
embedded_names.append(None)
st.selectbox("Deja Vu", embedded_names, key="embedding_name")

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
    messages_payload = st.session_state.messages.copy()

    def _contextual_user_input(original_user_input):
        import requests
        import json

        url = "http://localhost:8000/search"

        payload = json.dumps({
            "name": st.session_state["embedding_name"],
            "query": original_user_input,
            "top_k": 3,
            "search_type": "similarity",
            "content_only": True
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        try:
            response.raise_for_status()
            content_list = response.json()
            combined_context = ", ".join([f"context {i+1}: {item}" for i, item in enumerate(content_list)])
            rag_prompt = f"""Answer the following question based on the given context.
            ---
            Context: {combined_context}
            ---
            Question: {original_user_input}
            ---
            Answer: """
            return rag_prompt
        except Exception as err:
            st.error(f"Error occurred while returning the chunking response: {err}")
        return None

    if st.session_state["embedding_name"] is not None:
        with st.spinner("Checking embedded knowledge..."):
            original_user_input = messages_payload[0]["content"]
            processed_user_input = _contextual_user_input(original_user_input)
            if processed_user_input is not None:
                messages_payload[0] = {"role": "user", "content": processed_user_input}
            else:
                st.warning("Failed to get the search result from your question, continue the chat without context.")
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in messages_payload
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})

if len(st.session_state.messages):
    if st.button("🗑️ Clear"):
        st.session_state.messages = []
        st.rerun()