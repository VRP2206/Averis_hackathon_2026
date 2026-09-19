"""HTTP API for the dashboard. Run: `sdoc serve` (or `uvicorn sdoc.api:app`).

Endpoints
  GET  /health
  GET  /emails                 inbox summary (id, from, subject, attachments)
  GET  /emails/{id}            one email
  POST /process                run the pipeline over the whole inbox
  POST /process/{id}           run one email, return its result
  GET  /results                every result (full detail)
  GET  /results/{id}           one result
  GET  /submission             scorer-shaped JSON
  GET  /metrics                score vs ground truth (if the file exists)
  PATCH /results/{id}/review   reviewer override: {"status": ..., "defect_fields": [...]}
"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .evaluate import Evaluator
from .models import EmailResult, Status
from .pipeline import Pipeline, build_pipeline
from .store import JsonFileStore, ResultStore

app = FastAPI(title="SDOC", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_pipeline: Optional[Pipeline] = None
_store: ResultStore = JsonFileStore(settings.output_dir / "results.json")


def pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline(settings)
    return _pipeline


@app.get("/health")
def health():
    return {"ok": True, "llm_provider": settings.llm_provider, "results": len(_store.all())}


@app.get("/emails")
def emails():
    return [{"email_id": e.email_id, "from": e.sender, "subject": e.subject,
             "attachments": e.attachments, "result": (_store.get(e.email_id) or EmailResult(
                 email_id=e.email_id, category="GENERAL")).model_dump(mode="json", include={"category", "status", "review_reason", "defect_fields"})}
            for e in pipeline().inbox.emails()]


@app.get("/emails/{email_id}")
def email(email_id: str):
    try:
        return pipeline().inbox.get(email_id).model_dump(by_alias=True)
    except FileNotFoundError:
        raise HTTPException(404, "no such email")


@app.post("/process")
def process_all(workers: int = 8):
    results = pipeline().run(workers=workers)
    _store.put_many(results.values())
    return {"processed": len(results)}


@app.post("/process/{email_id}")
def process_one(email_id: str):
    try:
        email = pipeline().inbox.get(email_id)
    except FileNotFoundError:
        raise HTTPException(404, "no such email")
    result = pipeline().process(email)
    _store.put(result)
    return result


@app.get("/results")
def results():
    return sorted(_store.all(), key=lambda r: r.email_id)


@app.get("/results/{email_id}")
def result(email_id: str):
    r = _store.get(email_id)
    if r is None:
        raise HTTPException(404, "not processed yet")
    return r


@app.get("/submission")
def submission():
    return _store.submission()


@app.get("/metrics")
def metrics():
    if not settings.ground_truth.exists():
        raise HTTPException(404, "ground truth not available")
    return Evaluator(settings.ground_truth).score(_store.submission())


class ReviewPatch(BaseModel):
    status: Status
    defect_fields: list[str] = []
    reviewer: str = "reviewer"


@app.patch("/results/{email_id}/review")
def review(email_id: str, patch: ReviewPatch):
    r = _store.get(email_id)
    if r is None:
        raise HTTPException(404, "not processed yet")
    r.status, r.defect_fields = patch.status, patch.defect_fields
    r.has_defect = patch.status == Status.MISMATCH and bool(patch.defect_fields)
    r.review_reason = None if patch.status != Status.NEEDS_REVIEW else r.review_reason
    r.decided_by = "human"
    r.notes.append(f"overridden by {patch.reviewer}")
    _store.put(r)
    return r
