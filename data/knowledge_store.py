"""SQLite-backed knowledge store with naive embedding support."""

from __future__ import annotations

import json
import math
import sqlite3
import uuid
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from services.ingestion.schemas import Question


class KnowledgeStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id TEXT UNIQUE,
                    body TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    embedding TEXT NOT NULL
                )
                """
            )
            columns = {row[1] for row in conn.execute("PRAGMA table_info(questions)")}
            if "question_id" not in columns:
                conn.execute("ALTER TABLE questions ADD COLUMN question_id TEXT")
            conn.commit()

    def upsert_questions(self, questions: Iterable[Question]) -> int:
        rows = []
        for question in questions:
            if not question.question_id:
                question.question_id = self._generate_id()
            embedding = self._embed(question.body)
            rows.append((question.question_id, question.body, json.dumps(question.to_dict()), json.dumps(embedding)))

        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT INTO questions(question_id, body, payload, embedding)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(question_id) DO UPDATE SET
                    body=excluded.body,
                    payload=excluded.payload,
                    embedding=excluded.embedding
                """,
                rows,
            )
            conn.commit()
        return len(rows)

    def search(self, query: str, limit: int = 5) -> List[Question]:
        query_vec = self._embed(query)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT question_id, payload, embedding FROM questions").fetchall()

        scored = []
        for question_id, payload_json, embedding_json in rows:
            embedding = json.loads(embedding_json)
            score = self._cosine_similarity(query_vec, embedding)
            scored.append((score, self._row_to_question(question_id, payload_json)))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [question for _, question in scored[:limit]]

    def get(self, question_id: str) -> Optional[Question]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT question_id, payload FROM questions WHERE question_id = ?",
                (question_id,),
            ).fetchone()
        if not row:
            return None
        return self._row_to_question(row[0], row[1])

    def _embed(self, text: str) -> List[float]:
        # Tiny deterministic embedding using character hashing for offline use
        vector = [0.0] * 16
        for idx, ch in enumerate(text):
            bucket = idx % len(vector)
            vector[bucket] += (ord(ch) % 31) / 100.0
        return vector

    def _cosine_similarity(self, left: Sequence[float], right: Sequence[float]) -> float:
        dot = sum(l * r for l, r in zip(left, right))
        left_norm = math.sqrt(sum(l * l for l in left))
        right_norm = math.sqrt(sum(r * r for r in right))
        if not left_norm or not right_norm:
            return 0.0
        return dot / (left_norm * right_norm)

    def _generate_id(self) -> str:
        return uuid.uuid4().hex

    def _row_to_question(self, question_id: str, payload_json: str) -> Question:
        payload = json.loads(payload_json)
        question = Question.from_dict(payload)
        question.question_id = question_id or question.question_id
        return question
