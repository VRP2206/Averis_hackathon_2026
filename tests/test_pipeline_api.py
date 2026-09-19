"""End-to-end: pipeline on real emails, evaluator, and the HTTP API."""
import pytest
from fastapi.testclient import TestClient

from sdoc.config import settings
from sdoc.evaluate import Evaluator
from sdoc.models import ReviewReason, Status
from sdoc.pipeline import build_pipeline


@pytest.fixture(scope="module")
def pipe(inbox):
    return build_pipeline(settings, inbox)


@pytest.mark.parametrize("email_id,status,reason", [
    ("email_001", Status.OK, None),
    ("email_501", Status.NEEDS_REVIEW, ReviewReason.WRONG_DOC_TYPE),
    ("email_506", Status.NEEDS_REVIEW, ReviewReason.MISSING_ATTACHMENT),
    ("email_507", Status.NEEDS_REVIEW, ReviewReason.MISSING_ATTACHMENT),
    ("email_512", Status.NEEDS_REVIEW, ReviewReason.UNREADABLE),
    ("email_516", Status.NEEDS_REVIEW, ReviewReason.MISSING_VALUE),
    ("email_003", Status.OK, None),          # "please send the draft BL": nothing to compare
])
def test_edge_cases(pipe, inbox, email_id, status, reason):
    r = pipe.process(inbox.get(email_id))
    assert (r.status, r.review_reason) == (status, reason)


def test_mismatch_carries_evidence_and_draft(pipe, inbox):
    for mail in inbox.emails()[:120]:
        r = pipe.process(mail)
        if r.status == Status.MISMATCH:
            bad = [c for c in r.comparisons if not c.match]
            assert [c.field for c in bad] == r.defect_fields
            assert all(c.si_value and c.bl_value for c in bad)
            assert r.draft_reply and "amend" in r.draft_reply.lower()
            return
    pytest.fail("no MISMATCH found in first 120 emails")


@pytest.mark.skipif(not settings.ground_truth.exists(), reason="ground truth not present")
def test_full_run_scores_high(pipe):
    results = pipe.run()
    sub = {eid: r.to_submission() for eid, r in results.items()}
    score = Evaluator(settings.ground_truth).score(sub)
    assert score["stage1"]["macro_f1"] >= 0.97
    assert score["end_to_end"]["rate"] >= 0.95
    assert score["reliability"]["escalation_recall"] == 1.0


def test_api_smoke(inbox, tmp_path, monkeypatch):
    from sdoc import api
    from sdoc.store import JsonFileStore
    monkeypatch.setattr(api, "_store", JsonFileStore(tmp_path / "r.json"))
    monkeypatch.setattr(api, "_pipeline", build_pipeline(settings, inbox))
    c = TestClient(api.app)
    assert c.get("/health").json()["ok"] is True
    assert c.get("/results/email_001").status_code == 404
    r = c.post("/process/email_001").json()
    assert r["category"] == "BL_COMPARISON"
    assert c.get("/results/email_001").json()["email_id"] == "email_001"
    patched = c.patch("/results/email_001/review", json={"status": "MISMATCH", "defect_fields": ["shipper"]}).json()
    assert patched["decided_by"] == "human" and patched["has_defect"] is True
    assert c.get("/submission").json()["email_001"]["defect_fields"] == ["shipper"]


@pytest.mark.parametrize("email_id,last_title", [
    ("email_025", "MISMATCH: port_of_discharge, container_count"),
    ("email_501", "NEEDS_REVIEW: wrong_doc_type"),
    ("email_002", "No document check needed"),
])
def test_trace_explains_the_decision(pipe, inbox, email_id, last_title):
    """Every result carries an audit trail that starts with classification and ends with the verdict."""
    r = pipe.process(inbox.get(email_id))
    assert r.trace[0].stage == "classify" and r.trace[0].evidence
    assert r.trace[-1].title == last_title
