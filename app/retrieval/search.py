from typing import List, Literal
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.config import settings


class SearchRequest(BaseModel):
    name: str
    query: str
    top_k: int = 10
    search_type: str = "default"
    content_only: bool = False
    opts: dict = {}


def search_by_collection(
    collection_name: str, 
    query: str, 
    top_k: int = 5, 
    search_type: Literal["similarity", "mmr"] = "similarity",
    **kwargs
) -> List[Document]:
    """
    Perform a similarity search by collection name via the Chroma.
    2 search types are supported: "similarity" and "mmr".
    """
    from langchain_ollama import OllamaEmbeddings
    embeddings = OllamaEmbeddings(
        # TODO: Make both url and model configurable
        base_url="http://localhost:11434",
        model="nomic-embed-text:latest",
    )
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=settings.embeddings_dir,  # Where to save data locally, remove if not necessary
    )
    if search_type == "similarity":
        return vector_store.similarity_search(
            query=query,
            k=top_k,
            # TODO: Add metadata support here
            # filter={"source": "tweet"},
        )
    elif search_type == "mmr":
        if "fetch_k" not in kwargs:
            kwargs["fetch_k"] = top_k * 5
        retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": top_k, **kwargs})
        return retriever.invoke(query)
    else:
        raise ValueError("Invalid search type. Please choose 'similarity' or 'mmr'.")