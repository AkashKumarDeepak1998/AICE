"""Core domain models shared by ingestion and downstream services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Choice:
    """Represents a single multiple-choice option."""

    label: str
    body: str
    is_correct: bool = False

    def to_dict(self) -> Dict:
        return {"label": self.label, "body": self.body, "is_correct": self.is_correct}

    @classmethod
    def from_dict(cls, payload: Dict) -> "Choice":
        return cls(
            label=payload.get("label", ""),
            body=payload.get("body", ""),
            is_correct=payload.get("is_correct", False),
        )


@dataclass
class QuestionMetadata:
    """Metadata extracted from PDF/image context."""

    source_path: Optional[Path] = None
    tags: List[str] = field(default_factory=list)
    difficulty: Optional[str] = None
    section: Optional[str] = None
    ingestion_timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "source_path": str(self.source_path) if self.source_path else None,
            "tags": list(self.tags),
            "difficulty": self.difficulty,
            "section": self.section,
            "ingestion_timestamp": self.ingestion_timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: Optional[Dict]) -> Optional["QuestionMetadata"]:
        if not payload:
            return None
        source = payload.get("source_path")
        timestamp = payload.get("ingestion_timestamp")
        return cls(
            source_path=Path(source) if source else None,
            tags=payload.get("tags", []),
            difficulty=payload.get("difficulty"),
            section=payload.get("section"),
            ingestion_timestamp=datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow(),
        )


@dataclass
class Question:
    """Normalized structure saved in the knowledge store."""

    body: str
    choices: List[Choice]
    solution: str
    explanation: Optional[str] = None
    metadata: Optional[QuestionMetadata] = None
    question_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "body": self.body,
            "choices": [choice.to_dict() for choice in self.choices],
            "solution": self.solution,
            "explanation": self.explanation,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "question_id": self.question_id,
        }

    @classmethod
    def from_dict(cls, payload: Dict) -> "Question":
        metadata = QuestionMetadata.from_dict(payload.get("metadata"))
        choices = [Choice.from_dict(choice) for choice in payload.get("choices", [])]
        return cls(
            body=payload.get("body", ""),
            choices=choices,
            solution=payload.get("solution", ""),
            explanation=payload.get("explanation"),
            metadata=metadata,
            question_id=payload.get("question_id"),
        )
