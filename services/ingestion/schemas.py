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


@dataclass
class QuestionMetadata:
    """Metadata extracted from PDF/image context."""

    source_path: Path
    tags: List[str] = field(default_factory=list)
    difficulty: Optional[str] = None
    section: Optional[str] = None
    ingestion_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Question:
    """Normalized structure saved in the knowledge store."""

    body: str
    choices: List[Choice]
    solution: str
    explanation: Optional[str] = None
    metadata: Optional[QuestionMetadata] = None

    def to_dict(self) -> Dict:
        return {
            "body": self.body,
            "choices": [choice.__dict__ for choice in self.choices],
            "solution": self.solution,
            "explanation": self.explanation,
            "metadata": {
                "source_path": str(self.metadata.source_path) if self.metadata else None,
                "tags": self.metadata.tags if self.metadata else [],
                "difficulty": self.metadata.difficulty if self.metadata else None,
                "section": self.metadata.section if self.metadata else None,
                "ingestion_timestamp": self.metadata.ingestion_timestamp.isoformat()
                if self.metadata
                else None,
            },
        }
