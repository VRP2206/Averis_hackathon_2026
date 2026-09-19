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
from .models import Category, Document, DocType, Email, EmailResult, Status
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
        if cls.category == Category.BL_COMPARISON:
            self._compare_documents(email, result)
        if self.drafter:
            result.draft_reply = self.drafter.draft(result, email.subject)
        return result

    def _compare_documents(self, email: Email, result: EmailResult) -> None:
        docs = [self._read(path) for path in email.attachments]
        ctx = GateContext(email=email, documents=docs)

        reason = self.gate.before_extraction(ctx)
        if reason:
            result.status, result.review_reason = Status.NEEDS_REVIEW, reason
            result.notes += [d.error for d in docs if d.error]
            return
        if len(docs) < 2:
            result.notes.append("request for draft BL; nothing to compare")
            return

        ctx.si = self.extractor.extract(self._pick(docs, DocType.SI))
        ctx.bl = self.extractor.extract(self._pick(docs, DocType.BL))
        result.extractions = [ctx.si, ctx.bl]

        reason = self.gate.after_extraction(ctx)
        if reason:
            result.status, result.review_reason = Status.NEEDS_REVIEW, reason
            result.notes += [f"{ex.doc_type.value}: {f.field} {'blank' if f.blank else 'not found'}"
                             for ex in (ctx.si, ctx.bl) for f in ex.fields.values() if not f.usable]
            return

        result.comparisons = self.comparator.compare(ctx.si, ctx.bl)
        result.defect_fields = [c.field for c in result.comparisons if not c.match]
        result.has_defect = bool(result.defect_fields)
        result.status = Status.MISMATCH if result.has_defect else Status.OK

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
