"""OCR helpers built around pytesseract with graceful degradation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

try:
    import pytesseract  # type: ignore
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None
    Image = None


def run_ocr(image_path: Path, language: str = "eng") -> Dict[str, Optional[str]]:
    """Run OCR on the provided image.

    Returns a dictionary with raw text and debugging metadata so the dev
    portal can surface confidence values.
    """

    if not image_path.exists():
        raise FileNotFoundError(image_path)

    if pytesseract and Image:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=language)
        confidences = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
    else:  # pragma: no cover - placeholder for offline development
        text = image_path.read_text(encoding="utf-8", errors="ignore")
        confidences = {"level": [], "conf": []}

    return {
        "text": text.strip(),
        "metadata": json.dumps(confidences)[:2000],  # clamp for SQLite
    }
