"""SQLite-backed knowledge store with naive embedding support."""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Iterable, List, Sequence

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
                    body TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    embedding TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def upsert_questions(self, questions: Iterable[Question]) -> int:
        rows = []
        for question in questions:
            embedding = self._embed(question.body)
            rows.append((question.body, json.dumps(question.to_dict()), json.dumps(embedding)))

        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("INSERT INTO questions(body, payload, embedding) VALUES (?, ?, ?)", rows)
            conn.commit()
        return len(rows)

    def search(self, query: str, limit: int = 5) -> List[Question]:
        query_vec = self._embed(query)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT payload, embedding FROM questions").fetchall()

        scored = []
        for payload_json, embedding_json in rows:
            embedding = json.loads(embedding_json)
            score = self._cosine_similarity(query_vec, embedding)
            scored.append((score, Question(**json.loads(payload_json))))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [question for _, question in scored[:limit]]

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
