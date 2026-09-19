"""Orchestrates the stages for one email and for the whole inbox."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, Optional

from .classify import CascadeClassifier, Classifier, LLMClassifier, RuleClassifier
from .compare import Comparator
from .config import Settings, settings as default_settings
from .doctype import DocTypeDetector
from .drafts import ReplyDrafter
from .extract import CascadeExtractor, Extractor, HeuristicExtractor, LLMExtractor
from .gate import GateContext, ReviewGate
from .inbox import InboxRepository, open_inbox
from .llm import build_llm
from .models import COMPARE_FIELDS, Category, Document, DocType, Email, EmailResult, Status, TraceStep
from .readers import ReaderRegistry

log = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, inbox: InboxRepository, classifier: Classifier, readers: ReaderRegistry,
                 doctypes: DocTypeDetector, extractor: Extractor, gate: ReviewGate,
                 comparator: Comparator, drafter: Optional[ReplyDrafter] = None):
        self.inbox, self.classifier, self.readers = inbox, classifier, readers
        self.doctypes, self.extractor, self.gate = doctypes, extractor, gate
        self.comparator, self.drafter = comparator, drafter

    # -- one email ------------------------------------------------------------
    def process(self, email: Email) -> EmailResult:
        cls = self.classifier.classify(email)
        result = EmailResult(email_id=email.email_id, category=cls.category,
                             decided_by=cls.decided_by, classification=cls)
        ranked = ", ".join(f"{k} {v:g}" for k, v in sorted(cls.scores.items(), key=lambda kv: -kv[1]))
        self._step(result, "classify", f"Classified as {cls.category.value}", "decision",
                   f"Decided by {cls.decided_by}, confidence {cls.confidence:.0%}." + (f" Points: {ranked}." if ranked else ""),
                   cls.evidence)
        if cls.category == Category.BL_COMPARISON:
            self._compare_documents(email, result)
        else:
            self._step(result, "decide", "No document check needed", "info",
                       "Only BL comparison emails have their attachments compared.")
        if self.drafter:
            result.draft_reply = self.drafter.draft(result, email.subject)
        return result

    @staticmethod
    def _step(result: EmailResult, stage: str, title: str, outcome: str = "info",
              detail: str = "", evidence: Optional[list[str]] = None) -> None:
        result.trace.append(TraceStep(stage=stage, title=title, outcome=outcome, detail=detail, evidence=evidence or []))

    def _gate_steps(self, result: EmailResult, log: list) -> None:
        for label, reason in log:
            self._step(result, "gate", label, "fail" if reason else "pass",
                       f"Failed: {reason.value}. We stop here and ask a person." if reason else "Passed.")

    def _compare_documents(self, email: Email, result: EmailResult) -> None:
        docs = [self._read(path) for path in email.attachments]
        ctx = GateContext(email=email, documents=docs)
        self._step(result, "read", f"Read {len(docs)} attachment(s)", "info",
                   "Each file is opened by its format and typed by its content, not its name.",
                   [f"{d.path.rsplit('/', 1)[-1]}: {d.kind.upper()}, "
                    + (f"detected as {d.doc_type.value}" if d.readable else f"unreadable ({d.error})")
                    for d in docs] or ["no attachments"])

        log: list = []
        reason = self.gate.before_extraction(ctx, log)
        self._gate_steps(result, log)
        if reason:
            result.status, result.review_reason = Status.NEEDS_REVIEW, reason
            result.notes += [d.error for d in docs if d.error]
            self._step(result, "decide", f"NEEDS_REVIEW: {reason.value}", "decision",
                       "We cannot compare these documents safely, so a person decides instead of the tool guessing.")
            return
        if len(docs) < 2:
            result.notes.append("request for draft BL; nothing to compare")
            self._step(result, "decide", "OK: nothing to compare yet", "decision",
                       "The email asks for the draft BL rather than sending documents, so there is nothing to check.")
            return

        ctx.si = self.extractor.extract(self._pick(docs, DocType.SI))
        ctx.bl = self.extractor.extract(self._pick(docs, DocType.BL))
        result.extractions = [ctx.si, ctx.bl]
        for ex in (ctx.si, ctx.bl):
            self._step(result, "extract", f"Read 7 fields from the {ex.doc_type.value} ({ex.method})", "info",
                       "Each value comes from the line quoted here. Labels differ between documents; we match them by meaning.",
                       [f"{f}: {ex.fields[f].value!r}  <-  {ex.fields[f].source or 'not found'}" for f in COMPARE_FIELDS])

        log = []
        reason = self.gate.after_extraction(ctx, log)
        self._gate_steps(result, log)
        if reason:
            result.status, result.review_reason = Status.NEEDS_REVIEW, reason
            result.notes += [f"{ex.doc_type.value}: {f.field} {'blank' if f.blank else 'not found'}"
                             for ex in (ctx.si, ctx.bl) for f in ex.fields.values() if not f.usable]
            self._step(result, "decide", f"NEEDS_REVIEW: {reason.value}", "decision",
                       "A blank or missing value is uncertainty, not a mismatch, so a person decides.", result.notes)
            return

        result.comparisons = self.comparator.compare(ctx.si, ctx.bl)
        result.defect_fields = [c.field for c in result.comparisons if not c.match]
        result.has_defect = bool(result.defect_fields)
        result.status = Status.MISMATCH if result.has_defect else Status.OK
        self._step(result, "compare", "Compared normalised values", "info",
                   "Ports compare on name and UN/LOCODE, containers as a count, weights in kg, companies ignoring "
                   "case and punctuation. This step is plain code, not AI.",
                   [f"{'MATCH   ' if c.match else 'MISMATCH'} {c.field}: SI {c.si_normalised!r} vs BL {c.bl_normalised!r}"
                    for c in result.comparisons])
        verdict = f": {', '.join(result.defect_fields)}" if result.defect_fields else ": all 7 fields match"
        self._step(result, "decide", result.status.value + verdict, "decision",
                   "The draft BL needs amending." if result.has_defect else "The draft BL agrees with the SI.")

    def _read(self, path: str) -> Document:
        try:
            data = self.inbox.read_bytes(path)
        except Exception as exc:
            doc = Document(path=path, kind=path.rsplit(".", 1)[-1], readable=False, error=f"missing file: {exc}")
        else:
            doc = self.readers.read(path, data)
        doc.doc_type = self.doctypes.detect(doc)
        return doc

    @staticmethod
    def _pick(docs: list[Document], kind: DocType) -> Document:
        return next(d for d in docs if d.doc_type == kind)

    # -- whole inbox ----------------------------------------------------------
    def run(self, emails: Optional[Iterable[Email]] = None, workers: int = 8) -> dict[str, EmailResult]:
        emails = list(emails) if emails is not None else self.inbox.emails()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(self._safe_process, emails))
        return {r.email_id: r for r in results}

    def _safe_process(self, email: Email) -> EmailResult:
        try:
            return self.process(email)
        except Exception as exc:  # never lose an email: escalate instead
            log.exception("pipeline failed on %s", email.email_id)
            return EmailResult(email_id=email.email_id, category=Category.GENERAL,
                               notes=[f"pipeline error: {exc}"])


def build_pipeline(cfg: Settings | None = None, inbox: InboxRepository | None = None) -> Pipeline:
    """Wire the default pipeline from settings. With no LLM configured it
    runs entirely on rules and heuristics."""
    cfg = cfg or default_settings
    inbox = inbox or open_inbox(cfg.data_dir)
    llm = build_llm(cfg)
    classifier = CascadeClassifier(RuleClassifier(), LLMClassifier(llm) if llm.available else None)
    extractor: Extractor = CascadeExtractor(
        HeuristicExtractor(),
        LLMExtractor(llm) if (llm.available and cfg.use_llm_for_extraction) else None,
        cfg.extraction_min_confidence)
    return Pipeline(inbox=inbox, classifier=classifier, readers=ReaderRegistry(),
                    doctypes=DocTypeDetector(), extractor=extractor, gate=ReviewGate(),
                    comparator=Comparator(), drafter=ReplyDrafter())
