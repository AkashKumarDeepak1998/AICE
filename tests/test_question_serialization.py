from services.ingestion.schemas import Choice, Question, QuestionMetadata


def test_question_serialization_roundtrip(tmp_path):
    metadata = QuestionMetadata(source_path=tmp_path / "doc.pdf", tags=["pdf"], section="page-1", difficulty="easy")
    question = Question(
        body="Sample question?",
        choices=[Choice(label="A", body="Yes", is_correct=True), Choice(label="B", body="No")],
        solution="A",
        explanation="Because it's correct",
        metadata=metadata,
        question_id="abc123",
    )

    serialized = question.to_dict()
    reconstructed = Question.from_dict(serialized)

    assert reconstructed.body == question.body
    assert reconstructed.question_id == "abc123"
    assert reconstructed.metadata is not None
    assert str(reconstructed.metadata.source_path).endswith("doc.pdf")
    assert reconstructed.metadata.tags == ["pdf"]
