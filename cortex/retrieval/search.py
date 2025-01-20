from typing import List, Literal
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_core.documents import Document
from cortex.config import settings


class SearchRequest(BaseModel):
    name: str
    tags: List[str] = []
    query: str
    top_k: int = 10
    search_type: str = "default"
    content_only: bool = False
    opts: dict = {}


def search_by_collection(
    collection_name: str, 
    tags: List[str],
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
        base_url=settings.ollama_base_url,
        model="nomic-embed-text:latest",
    )
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=settings.embeddings_dir,
    )
    retriever = vector_store.as_retriever(
        search_type=search_type, 
        search_kwargs={
            "k": top_k, 
            "filter": {"source": {"$in": tags}} if tags else None, 
            **kwargs
        }
    )
    return retriever.invoke(query)