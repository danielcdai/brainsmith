from pydantic import BaseModel
from pathlib import Path
from typing import Literal, List
from langchain_core.documents import Document


"""File loader for the BrainSmith vector database."""
class BrainSmithLoader(BaseModel):
    file_path: Path

    def __init__(self, **data):
        super().__init__(**data)
        self.file_path = Path(self.file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"The file {self.file_path} does not exist.")


    def _text_load(self, chunk_size: int, chunk_overlap: int):
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        with open(self.file_path, "r") as f:
            uploaded_file =  f.read()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return text_splitter.create_documents([uploaded_file])
    

    def load(
            self,
            load_type: Literal["text"] = "text", 
            chunk_size: int = 1000, 
            chunk_overlap: int = 200
        ) -> List[Document]:
        match load_type:
            case "text":
                return self._text_load(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            case _:
                raise ValueError(f"Invalid load type: {load_type}")
