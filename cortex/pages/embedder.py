import requests
import streamlit as st


with st.sidebar:
    ollama_base_url = st.text_input("Ollama Base URL", key="ollama_base_url", value="http://localhost:11434")
    # Disable openai embedding for now
    # openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    # "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"


st.title("Embedder")
st.caption("📖 Enlighten me with your knowledge")


# if "openai_model" not in st.session_state:
#     st.session_state["openai_model"] = "text-embedding-ada-002"
if "ollama_model" not in st.session_state:
    st.session_state["ollama_model"] = "nomic-embed-text:latest"


uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"])
if uploaded_file is None:
    st.info("Upload a file to get started.")

with st.expander("📚 Embedding options"):
    name = st.text_input("Name", "my-embedding")
    tag = st.text_input("Tag", "tutorial")
    chunk_size = st.number_input("Chunk size", min_value=1, value=400, step=200)
    chunk_overlap = st.number_input("Chunk overlap", min_value=0, value=20, step=10)
    dimension = st.number_input("Dimension", min_value=1, value=512, step=256)

start_btn = st.button("Start")


def _do_chunking():
    url = "http://localhost:8000/chunk"

    payload = {
        'chunk_size': chunk_size,
        'chunk_overlap': chunk_overlap,
        'content_only': True
    }
    files=[uploaded_file]
    headers = {}

    files = {
        'file': uploaded_file
    }
    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    try:
        response.raise_for_status()
        return response.json()
    except Exception as err:
        st.error(f"Error occurred while returning the chunking response: {err}")
    return None
    

def _do_embedding_start(chunks):
    import json
    url = "http://localhost:8000/embedding/start"
    payload = json.dumps({
        "name": name,
        "texts": chunks   
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)

    try:
        response.raise_for_status()
        return response.json()
    except Exception as err:
        st.error(f"Error occurred while starting the embedding: {err}")
    return None


def _check_embedding_status(url):
    import time
    progress_bar = st.progress(0, text="Embedding in progress...")
    while True:
        response = requests.get(url)
        try:
            response.raise_for_status()
            status = response.json()
            progress_bar_value = status['progress'] % 100

            # Format ETA
            estimated_time = int(status['estimated_time_left'])
            if estimated_time >= 3600:
                hours = estimated_time // 3600
                minutes = (estimated_time % 3600) // 60
                seconds = estimated_time % 60
                eta_text = f"{int(hours)} h {int(minutes)} min {int(seconds)} s"
            elif estimated_time >= 60:
                minutes = estimated_time // 60
                seconds = estimated_time % 60
                eta_text = f"{int(minutes)} min {int(seconds)} s"
            else:
                eta_text = f"{int(estimated_time)} s"

            if estimated_time > 0.0:
                progress_text = f"Embedding in progress... ETA: {eta_text}..."
            else:
                progress_text = "Embedding in progress... No ETA available yet."
            if status['status'] == 'completed':
                st.success("Embedding is done.")
                progress_bar.progress(100, text="")
                break
            elif status['status'] == 'failed':
                progress_bar.progress(progress_bar_value, text="")
                st.error("Embedding failed.")
                break
            progress_bar.progress(progress_bar_value, text=progress_text)
            # Polling every 1 second
            time.sleep(1)
        except requests.exceptions.HTTPError as err:
            progress_bar.progress(progress_bar_value, text="Embedding failed.")
            st.error("Embedding failed.")
        except Exception as err:
            st.error(f"Error occurred while checking the embedding status: {err}")
        finally:
            st.session_state["button_clicked"] = True


# TODO: Disable the button once it is clicked
if start_btn:
    if not ollama_base_url:
        st.warning("Please specify your Ollama service base url to continue.")
        st.stop()

    with st.spinner("Starting the embedding process..."):
        start_btn = False
        chunks = _do_chunking()
        if not chunks:
            st.error("No chunks returned. Please check your file.")
            st.stop()
        embedding_start_response = _do_embedding_start(chunks)
        check_status_url = embedding_start_response['check_status_url']
        check_status_url = f'http://localhost:8000{check_status_url}'
        _check_embedding_status(check_status_url)
    # if not openai_api_key:
    #     st.warning("Please add your OpenAI API key to continue.")
    #     st.stop()