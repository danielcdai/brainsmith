import warnings

from pydantic import BaseModel
from pathlib import Path
from typing import Literal, List
from langchain_core.documents import Document



"""File loader for the BrainSmith vector database."""
warnings.warn(
    "BrainSmithLoader is deprecated and will be removed in a future release. "
    "Please use Chunker instead.",
    DeprecationWarning,
    stacklevel=2
)
class BrainSmithLoader(BaseModel):
    file_path: Path

    def __init__(self, **data):
        super().__init__(**data)
        self.file_path = Path(self.file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"The file {self.file_path} does not exist.")


    def _get_splitter(
            self, 
            chunk_size: int,
            chunk_overlap: int,
            split_type: Literal["char", "semantic"] = "char"
        ):
        match split_type:
            case "char":
                from langchain_text_splitters import RecursiveCharacterTextSplitter
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
            # For semantic splitting, we use the Ollama embeddings to split the text into meaningful chunks
            # Chunk size and overlap are not used in this case
            case "semantic":
                from langchain_experimental.text_splitter import SemanticChunker
                from langchain_ollama import OllamaEmbeddings
                from cortex.config import settings
                text_splitter = SemanticChunker(
                    embeddings = OllamaEmbeddings(
                        base_url=settings.ollama_base_url,
                        model="nomic-embed-text:latest",
                    )
                )
            case _:
                raise ValueError(f"Invalid split type: {split_type}")
        return text_splitter


    # TODO: Need to test if involve loader would make the chunking better
    def _text_load(
            self, 
            chunk_size: int, 
            chunk_overlap: int, 
            split_type: Literal["char", "semantic"] = "char"
        ) -> List[Document]:
        with open(self.file_path, "r") as f:
            uploaded_file =  f.read()
        text_splitter = self._get_splitter(chunk_size, chunk_overlap, split_type)
        return text_splitter.create_documents([uploaded_file])


    def _pdf_load(
            self,
            chunk_size: int,
            chunk_overlap: int,
            split_type: Literal["char", "semantic"] = "char"
    ) -> List[Document]:
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(self.file_path)
        text_splitter = self._get_splitter(chunk_size, chunk_overlap, split_type)
        return loader.load_and_split(text_splitter=text_splitter)
    

    def load(
            self,
            load_type: Literal["txt", "pdf"] = "txt", 
            chunk_size: int = 1000, 
            chunk_overlap: int = 200,
            splitter: Literal["char", "semantic"] = "char"
        ) -> List[Document]:
        # TODO: Add support for other load types like PDF, CSV, Markdown, Code, Semantic, etc.
        match load_type:
            case "txt":
                return self._text_load(chunk_size=chunk_size, chunk_overlap=chunk_overlap, split_type=splitter)
            case "pdf":
                return self._pdf_load(chunk_size=chunk_size, chunk_overlap=chunk_overlap, split_type=splitter)
            case _:
                raise ValueError(f"Invalid load type: {load_type}")
