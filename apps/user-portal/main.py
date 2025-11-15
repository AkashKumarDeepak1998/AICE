"""FastAPI app exposing mock tests, analytics, and remediation."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

from data.knowledge_store import KnowledgeStore
from services.ingestion.schemas import Question
from services.llm.pipeline import AdaptiveLLMPipeline, UserAnswer

app = FastAPI(title="AICE User Portal")
store = KnowledgeStore(db_path=Path("data/knowledge.sqlite"))
llm = AdaptiveLLMPipeline()


@app.get("/mock-tests")
def mock_tests() -> Dict:
    questions = store.search("government exam", limit=30)
    blueprint = {"easy": 10, "medium": 15, "hard": 5}
    mock_test = llm.build_mock_test(questions, blueprint)
    return {"count": len(mock_test), "questions": [question.to_dict() for question in mock_test]}


def _fetch_question(question_id: str) -> Question | None:
    return store.get(question_id)


class UserAnswerPayload(BaseModel):
    question_id: str
    answer: str
    is_correct: bool


@app.post("/analytics")
def analytics(user_answers: List[UserAnswerPayload]):
    sections: Dict[str, int] = {"easy": 0, "medium": 0, "hard": 0}
    correct = 0
    for answer in user_answers:
        question = _fetch_question(answer.question_id)
        if question:
            difficulty = llm.classify_difficulty(question)
            sections[difficulty] += 1
        if answer.is_correct:
            correct += 1
    return {"accuracy": correct / max(len(user_answers), 1), "distribution": sections}


@app.post("/remediation")
def remediation(user_answers: List[UserAnswerPayload]):
    question_lookup = {
        answer.question_id: _fetch_question(answer.question_id)
        for answer in user_answers
        if _fetch_question(answer.question_id)
    }
    payload = [UserAnswer(**answer.dict()) for answer in user_answers]
    remediations = llm.remediation_questions(payload, question_lookup)
    return {"count": len(remediations), "questions": [question.to_dict() for question in remediations]}
