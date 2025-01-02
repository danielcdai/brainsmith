import pytest
import random
from app.retrieval.search import search_by_collection
from app.retrieval.embedding import (
    start_embedding_task,
    initialize_embedding_task
)


@pytest.fixture
def setup_embedding_task():
    task_id = "test_task"
    name = "test_embedding"
    texts = [
        "Alice and Bob are siblings.",
        "Bob and Charlie are best friends.",
        "Charlie and Dave work together.",
        "Dave and Eve are neighbors.",
        "Eve and Alice went to the same school.",
        "Alice and Charlie are cousins.",
        "Bob and Dave play in the same football team.",
        "Charlie and Eve are in the same book club.",
        "Dave and Alice volunteer at the same charity.",
        "Eve and Bob are gym buddies."
    ]
    initialize_embedding_task(task_id)
    yield task_id, name, texts


def test_start_embedding_task_and_search(setup_embedding_task):
    task_id, name, texts = setup_embedding_task
    start_embedding_task(name, task_id, texts)
    questions = [
        "Who are siblings?",
        "Who are best friends?",
        "Who works together?",
        "Who are neighbors?",
        "Who went to the same school?"
    ]
    random_question = random.choice(questions)
    results = search_by_collection(collection_name=name, query=random_question, top_k=3, search_type="similarity")
    mmr_results = search_by_collection(collection_name=name, query=random_question, top_k=3, search_type="mmr", fetch_k=10)
    assert len(results) == 3
    assert len(mmr_results) == 3
    assert results != mmr_results


@pytest.fixture(scope="module", autouse=True)
def cleanup_embedding_dir():
    yield
    from app.config import settings
    import shutil
    import os
    if os.path.exists(settings.embeddings_dir):
        shutil.rmtree(settings.embeddings_dir)