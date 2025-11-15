"""FastAPI developer console for batch uploads and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile

from data.knowledge_store import KnowledgeStore
from services.ingestion.pipeline import IngestionPipeline

app = FastAPI(title="AICE Developer Portal")
tmp_dir = Path(".tmp/ingestion")
ingestion = IngestionPipeline(tmp_dir=tmp_dir)
store = KnowledgeStore(db_path=Path("data/knowledge.sqlite"))


@app.get("/")
def root() -> dict:
    """Provide a quick index so hitting the base URL is informative."""
    return {
        "service": "AICE Developer Portal",
        "status": "ok",
        "routes": {
            "upload_pdf": "/upload/pdf",
            "upload_images": "/upload/images",
            "validate": "/validate",
            "tag": "/tag",
        },
    }


@app.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    content = await file.read()
    tmp_path = tmp_dir / file.filename
    tmp_path.write_bytes(content)
    questions = ingestion.ingest_pdf(tmp_path)
    stored = store.upsert_questions(questions)
    return {"stored": stored, "questions": [question.to_dict() for question in questions]}


@app.post("/upload/images")
async def upload_images(files: List[UploadFile] = File(...)):
    paths = []
    for file in files:
        data = await file.read()
        tmp_path = tmp_dir / file.filename
        tmp_path.write_bytes(data)
        paths.append(tmp_path)
    questions = ingestion.ingest_images(paths)
    stored = store.upsert_questions(questions)
    return {"stored": stored, "questions": [question.to_dict() for question in questions]}


@app.post("/validate")
async def validate(question_payload: str):
    data = json.loads(question_payload)
    return {"valid": True, "preview": data}


@app.post("/tag")
async def tag_question(question_id: str, tags: List[str]):
    # Placeholder endpoint for human-in-the-loop tagging
    return {"question_id": question_id, "tags": tags, "status": "queued"}
