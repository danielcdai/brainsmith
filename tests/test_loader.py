import pytest
from pathlib import Path
from cortex.retrieval.loader import BrainSmithLoader
from langchain_core.documents import Document


def test_brainsmithloader_file_not_found():
    """Test that the loader raises a FileNotFoundError when the file does not exist."""
    with pytest.raises(FileNotFoundError):
        BrainSmithLoader(file_path="non_existent_file.txt")


def test_brainsmithloader_load_text():
    """Test that the loader can load text from a file."""
    test_file = Path("tests/corpus/paul_graham_essay.txt")
    loader = BrainSmithLoader(file_path=test_file)
    documents = loader.load(load_type="text", chunk_size=1000, chunk_overlap=50)

    assert isinstance(documents, list)
    assert all(isinstance(doc, Document) for doc in documents)
    assert len(documents) > 100


def test_brainsmithloader_invalid_load_type():
    test_file = Path("tests/corpus/paul_graham_essay.txt")
    loader = BrainSmithLoader(file_path=test_file)
    with pytest.raises(ValueError):
        loader.load(load_type="invalid_type")