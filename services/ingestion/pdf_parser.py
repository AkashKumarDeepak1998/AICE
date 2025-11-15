"""Utility helpers for pulling structured text out of PDFs."""

from __future__ import annotations

from pathlib import Path
from typing import List

try:
    import pdfplumber  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pdfplumber = None


def extract_text(pdf_path: Path) -> List[str]:
    """Return a list of page-level strings for downstream parsing."""

    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    if pdfplumber:
        with pdfplumber.open(pdf_path) as pdf:
            return [page.extract_text() or "" for page in pdf.pages]

    # lightweight fallback: treat the PDF as plain text for CI
    return [pdf_path.read_text(encoding="utf-8", errors="ignore")]
