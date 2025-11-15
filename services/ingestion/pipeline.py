"""High-level ingestion orchestration for OCR + PDF parsing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from . import ocr, pdf_parser
from .schemas import Choice, Question, QuestionMetadata


class IngestionPipeline:
    """Simple orchestrator that normalizes assets into Question objects."""

    def __init__(self, tmp_dir: Path):
        self.tmp_dir = tmp_dir
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def ingest_pdf(self, pdf_path: Path) -> List[Question]:
        pages = pdf_parser.extract_text(pdf_path)
        questions: List[Question] = []
        for idx, page in enumerate(pages, 1):
            prompt = self._heuristic_chunk(page)
            if not prompt:
                continue
            metadata = QuestionMetadata(source_path=pdf_path, tags=["pdf"], section=f"page-{idx}")
            questions.extend(self._chunk_to_questions(prompt, metadata))
        return questions

    def ingest_images(self, image_paths: Iterable[Path]) -> List[Question]:
        questions: List[Question] = []
        for image_path in image_paths:
            result = ocr.run_ocr(image_path)
            metadata = QuestionMetadata(
                source_path=image_path,
                tags=["image"],
                section="ocr",
            )
            metadata.tags.append("ocr")
            metadata.tags.append(f"confidence-metadata:{result['metadata'][:32]}")
            questions.extend(self._chunk_to_questions(result["text"], metadata))
        return questions

    def _chunk_to_questions(self, blob: str, metadata: QuestionMetadata) -> List[Question]:
        """Very small heuristic parser that expects JSON lines blobs."""

        questions: List[Question] = []
        for line in blob.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                # fallback: treat the entire line as the body with dummy choices
                questions.append(
                    Question(
                        body=line,
                        choices=[Choice(label="A", body=line)],
                        solution="A",
                        metadata=metadata,
                        explanation=None,
                    )
                )
                continue

            choices = [
                Choice(label=choice.get("label", ""), body=choice.get("body", ""), is_correct=choice.get("is_correct", False))
                for choice in payload.get("choices", [])
            ]
            if not choices:
                choices = [Choice(label="A", body="Unable to parse choices", is_correct=True)]
            solution = next((choice.label for choice in choices if choice.is_correct), choices[0].label)
            questions.append(
                Question(
                    body=payload.get("body", ""),
                    choices=choices,
                    solution=solution,
                    explanation=payload.get("explanation"),
                    metadata=metadata,
                )
            )
        return questions

    def _heuristic_chunk(self, page_text: str) -> str:
        """Split page text into JSON-lines friendly format."""

        parts = [part.strip() for part in page_text.split("\n\n") if part.strip()]
        return "\n".join(parts)
