from pathlib import Path

from data.knowledge_store import KnowledgeStore
from services.ingestion.schemas import Choice, Question, QuestionMetadata


def _sample_question(tmp_path: Path) -> Question:
    metadata = QuestionMetadata(source_path=tmp_path / "source.txt", tags=["pdf"], section="page-1")
    return Question(
        body="What is 2 + 2?",
        choices=[Choice(label="A", body="4", is_correct=True), Choice(label="B", body="5")],
        solution="A",
        metadata=metadata,
    )


def test_upsert_and_get_roundtrip(tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite")
    question = _sample_question(tmp_path)

    stored = store.upsert_questions([question])
    assert stored == 1
    assert question.question_id is not None

    fetched = store.get(question.question_id)
    assert fetched is not None
    assert fetched.body == question.body
    assert fetched.question_id == question.question_id
    assert fetched.metadata and fetched.metadata.section == "page-1"


def test_search_returns_question_objects(tmp_path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite")
    question = _sample_question(tmp_path)
    store.upsert_questions([question])

    results = store.search("2 + 2", limit=1)
    assert len(results) == 1
    assert results[0].choices[0].body == "4"
    assert results[0].metadata is not None
