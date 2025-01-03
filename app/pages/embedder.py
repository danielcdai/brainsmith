import streamlit as st

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"


st.title("Embedder")
st.caption("📖 Enlighten me with your knowledge")


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "text-embedding-ada-002"


uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"])
if uploaded_file is None:
    st.info("Upload a file to get started.")

with st.expander("📚 Embedding options"):
    name = st.text_input("Name", "my-embedding")
    tag = st.text_input("Tag", "tutorial")
    chunk_size = st.number_input("Chunk size", min_value=1, value=100)
    chunk_overlap = st.number_input("Chunk overlap", min_value=0, value=0)
    dimension = st.number_input("Dimension", min_value=1, value=512)

start_btn = st.button("Start")


if start_btn:
    if not openai_api_key:
        st.warning("Please add your OpenAI API key to continue.")
        st.stop()
    st.info("Starting the embedding process...")