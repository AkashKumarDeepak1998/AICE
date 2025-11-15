"""Feedback loop utilities for updating prompts and weights."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import json


@dataclass
class UserPerformance:
    user_id: str
    question_id: str
    is_correct: bool
    difficulty: str


class FeedbackLoop:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, performances: Iterable[UserPerformance]) -> None:
        payload = [performance.__dict__ for performance in performances]
        history = []
        if self.log_path.exists():
            history = json.loads(self.log_path.read_text())
        history.extend(payload)
        self.log_path.write_text(json.dumps(history, indent=2))

    def aggregate(self) -> dict:
        if not self.log_path.exists():
            return {"total": 0, "accuracy": 0}
        history = json.loads(self.log_path.read_text())
        total = len(history)
        accuracy = sum(1 for entry in history if entry["is_correct"]) / max(total, 1)
        return {"total": total, "accuracy": accuracy}
