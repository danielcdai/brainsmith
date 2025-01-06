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



with st.sidebar:
    chat_provider = st.selectbox("Chat Provider", ["OpenAI", "Ollama"], key="chat_provider")
    if chat_provider == "OpenAI":
        openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
        "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    elif chat_provider == "Ollama":
        ollama_base_url = st.text_input("Ollama Base URL", key="ollama_base_url", value="http://localhost:11434")
        if ollama_base_url:
            url = f"{ollama_base_url}/v1/models"
            response = requests.get(url)
            if response.status_code == 200:
                models = response.json()
                model_names = [model["id"] for model in models["data"]]
                ollama_model = st.selectbox("Ollama Model", model_names, key="ollama_model")
            else:
                st.error(f"Failed to fetch models from Ollama: {response.text}")
                ollama_model = None
    else:
        st.error("Invalid chat provider selected.")
        st.stop()

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
embedded_names.insert(0, None)
with st.expander("Context Agent"):
    st.selectbox("Deja Vu", embedded_names, key="embedding_name")

if st.session_state["chat_provider"] == "OpenAI" and "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    if st.session_state["chat_provider"] == "OpenAI" and not openai_api_key:
        st.warning("Please add your OpenAI API key to continue.")
        st.stop()
    with st.chat_message("user"):
        st.markdown(prompt)

    graph = None
    if st.session_state["embedding_name"] is None:
        from cortex.tools.default_agent import get_default_agent_graph
        if st.session_state["chat_provider"] == "OpenAI":
            graph = get_default_agent_graph(api_key=openai_api_key, model=st.session_state["openai_model"])
        elif st.session_state["chat_provider"] == "Ollama":
            graph = get_default_agent_graph(base_url=ollama_base_url, model=ollama_model)
    else:
        from cortex.tools.context_agent import get_context_agent_graph
        if st.session_state["chat_provider"] == "OpenAI":
            graph = get_context_agent_graph(st.session_state["embedding_name"], api_key=openai_api_key, model=st.session_state["openai_model"])
        elif st.session_state["chat_provider"] == "Ollama":
            graph = get_context_agent_graph(st.session_state["embedding_name"], base_url=ollama_base_url, model=ollama_model)

    from typing import Literal
    def stream_graph_updates(user_input: str, mode: Literal["values", "messages"] = "values"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        if mode == "messages":
            ai_answer = ""
        for chunk in graph.stream(
            {"messages": st.session_state.messages}, stream_mode=mode
        ):
            match mode:
                case "values":
                    if len(chunk["messages"]) % 2 == 0:
                        # Debug only
                        # print(chunk["messages"][-1].content, end='\n', flush=True)
                        ai_answer = chunk["messages"][-1].content
                case "messages":
                    from langchain_core.messages import AIMessageChunk
                    if len(chunk) % 2 == 0 and isinstance(chunk, tuple) and len(chunk) > 0 and type(chunk[0]) == AIMessageChunk:
                        content = chunk[0].content
                        ai_answer += content
                        # Debug only
                        # print(content, end='', flush=True)
                        yield content
        return ai_answer

    with st.chat_message("assistant"):
        # FIXME: Ollama chat is not streaming properly here
        stream = stream_graph_updates(prompt, mode="messages")
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
    print(st.session_state.messages)


if len(st.session_state.messages):
    if st.button("🗑️ Clear"):
        st.session_state.messages = []
        st.rerun()