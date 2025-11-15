# AICE Platform Skeleton

This repository wires together the key services requested for an adaptive government-exam preparation platform. The code is intentionally lightweight so it can run inside the execution environment without external services, yet the modules map 1:1 with the production architecture.

## Layout

```
services/
  ingestion/
    ocr.py           # OCR helpers (pytesseract when available)
    pdf_parser.py    # PDF text extraction
    pipeline.py      # Converts OCR/PDF output into normalized questions
  llm/
    pipeline.py      # Difficulty classification, remediation, mock tests
  feedback/
    loop.py          # Captures user performance for prompt tuning
apps/
  dev-portal/       # FastAPI dashboard for staff ingest & tagging
  user-portal/      # FastAPI user surface for mock tests + analytics
data/
  knowledge_store.py # SQLite + naive embeddings for retrieval
```

## Running the portals

1. Install dependencies:

```bash
pip install fastapi uvicorn pydantic pytesseract pdfplumber pillow
```

2. Launch the developer portal:

```bash
uvicorn apps.dev-portal.main:app --reload
```

3. Launch the user portal:

```bash
uvicorn apps.user-portal.main:app --reload --port 8001
```

Both applications share the SQLite-backed knowledge store under `data/knowledge.sqlite`, enabling rapid iteration on ingestion pipelines and the adaptive LLM logic.

## Feedback loop

`services/feedback/loop.py` demonstrates how to persist user performance signals. Those aggregates can be fed back into `services/llm/pipeline.py` (e.g., to adjust blueprint ratios or prompt templates) to continuously calibrate question difficulty.
