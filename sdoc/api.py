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

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .evaluate import Evaluator
from .models import EmailResult, Status
from .pipeline import Pipeline, build_pipeline
from .store import ResultStore, make_store

app = FastAPI(title="SDOC", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_pipeline: Optional[Pipeline] = None
_store: ResultStore = make_store(settings.dynamodb_table, settings.output_dir / "results.json")


def pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        from .inbox import open_inbox
        from .mail import CompositeInbox, UploadInbox
        inbox = CompositeInbox(open_inbox(settings.data_dir))
        inbox.add_source("upload", UploadInbox(settings.output_dir / "mail_cache" / "upload"))
        _pipeline = build_pipeline(settings, inbox)
    return _pipeline


def _inbox():
    from .mail import CompositeInbox
    ib = pipeline().inbox
    assert isinstance(ib, CompositeInbox)
    return ib


@app.get("/health")
def health():
    return {"ok": True, "llm_provider": settings.llm_provider, "results": _store.count()}


@app.get("/emails")
def emails():
    ib = _inbox()
    done = {r.email_id: r for r in _store.all()}      # one scan, not one lookup per email
    return [{"email_id": e.email_id, "from": e.sender, "subject": e.subject, "source": ib.source_of(e.email_id),
             "attachments": e.attachments, "result": (done.get(e.email_id) or EmailResult(
                 email_id=e.email_id, category="GENERAL")).model_dump(mode="json", include={"category", "status", "review_reason", "defect_fields"})}
            for e in ib.emails()]


# -- real mail in: IMAP mailbox and uploaded .eml ---------------------------------
class MailboxConnect(BaseModel):
    host: str = "imap.gmail.com"
    user: str
    password: str            # Gmail: an App Password; held in memory only
    folder: str = "INBOX"
    limit: int = 50


@app.post("/mailbox/connect")
def mailbox_connect(req: MailboxConnect):
    """Connect an IMAP mailbox, pull the latest messages and process them."""
    from .mail import ImapInbox
    src = ImapInbox(req.host, req.user, req.password, settings.output_dir / "mail_cache" / "imap",
                    folder=req.folder, limit=req.limit)
    try:
        total = src.test()
        fresh = src.refresh()
    except Exception as exc:
        raise HTTPException(400, f"could not connect: {exc}")
    _inbox().add_source("mailbox", src)
    results = pipeline().run(fresh)
    _store.put_many(results.values())
    return {"connected": True, "host": req.host, "user": req.user, "folder": req.folder,
            "messages_in_folder": total, "fetched": len(fresh), "processed": len(results)}


@app.post("/mailbox/refresh")
def mailbox_refresh():
    src = _inbox().sources.get("mailbox")
    if src is None:
        raise HTTPException(404, "no mailbox connected")
    fresh = src.refresh()                         # type: ignore[attr-defined]
    results = pipeline().run(fresh)
    _store.put_many(results.values())
    return {"fetched": len(fresh), "processed": len(results)}


@app.delete("/mailbox")
def mailbox_disconnect():
    _inbox().remove_source("mailbox")
    return {"connected": False}


@app.get("/mailbox")
def mailbox_status():
    src = _inbox().sources.get("mailbox")
    if src is None:
        return {"connected": False}
    return {"connected": True, "host": src.host, "user": src.user, "folder": src.folder,   # type: ignore[attr-defined]
            "cached": len(src.emails())}


@app.post("/upload")
async def upload_eml(file: UploadFile = File(...)):
    """Upload one .eml (raw email with attachments); it is processed at once."""
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "empty file")
    up = _inbox().sources["upload"]
    e = up.add(raw, file.filename or "upload")      # type: ignore[attr-defined]
    r = pipeline().process(e)
    _store.put(r)
    return r


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


@app.get("/invoices")
def invoices():
    """Receipts view: invoice numbers, order refs and amounts from billing emails."""
    from .invoices import InvoiceExtractor
    cats = {r.email_id: r.category.value for r in _store.all()}
    return [r.to_dict() for r in InvoiceExtractor().extract_all(pipeline().inbox.emails(), cats)]


class TranslateRequest(BaseModel):
    target: str = "en"


_translator = None


@app.post("/translate/{email_id}")
def translate(email_id: str, req: TranslateRequest):
    """Detect the email's language and translate body + subject to `target`."""
    global _translator
    from .llm import build_llm
    from .translate import Translator
    if _translator is None:
        _translator = Translator(build_llm(settings))
    try:
        email = pipeline().inbox.get(email_id)
    except FileNotFoundError:
        raise HTTPException(404, "no such email")
    t = _translator.translate(f"{email.subject}\n\n{email.body}", req.target)
    return {"email_id": email_id, "source_language": t.source_language, "target_language": t.target_language,
            "translated": t.translated, "text": t.text, "note": t.note, "llm_provider": settings.llm_provider}


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
