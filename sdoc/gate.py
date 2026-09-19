"""The review gate: decide whether a comparison can be trusted at all.

Checks run in order and the first failure wins. Each returns a
`ReviewReason`, which the pipeline turns into NEEDS_REVIEW.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .models import Document, DocType, Email, Extraction, ReviewReason
from .textnorm import strip_noise


@dataclass
class GateContext:
    email: Email
    documents: list[Document]
    si: Optional[Extraction] = None
    bl: Optional[Extraction] = None


class GateCheck(ABC):
    label: str = "check"

    @abstractmethod
    def check(self, ctx: GateContext) -> Optional[ReviewReason]: ...


class AttachmentCheck(GateCheck):
    """Fewer than two documents. A bare 'please send the draft BL' request is
    not a comparison and passes as not-comparable; an email that says the
    documents are attached (or compares them) but lacks them is escalated."""

    label = "Both documents are attached"
    EXPECTS_DOCS = re.compile(
        r"(attached|attachment|please find|enclosed|compare the si|si and (the )?(draft )?bl|"
        r"still missing|been dropped|pfa\b)", re.I)

    def check(self, ctx):
        if len(ctx.documents) >= 2:
            return None
        if ctx.documents or self.EXPECTS_DOCS.search(strip_noise(ctx.email.body)):
            return ReviewReason.MISSING_ATTACHMENT
        return None


class ReadableCheck(GateCheck):
    label = "Every attachment can be read"

    def check(self, ctx):
        return ReviewReason.UNREADABLE if any(not d.readable for d in ctx.documents) else None


class DocTypeCheck(GateCheck):
    """Need exactly one SI and one BL among the readable documents."""
    label = "One Shipping Instruction and one Bill of Lading"

    def check(self, ctx):
        if len(ctx.documents) < 2:
            return None
        types = [d.doc_type for d in ctx.documents]
        if DocType.SI in types and DocType.BL in types:
            return None
        return ReviewReason.WRONG_DOC_TYPE


class ValueCheck(GateCheck):
    """A blank or unfound field on either side means we cannot decide."""
    label = "All 7 fields have a value on both documents"

    def check(self, ctx):
        if ctx.si is None or ctx.bl is None:
            return None
        for ex in (ctx.si, ctx.bl):
            if any(not f.usable for f in ex.fields.values()):
                return ReviewReason.MISSING_VALUE
        return None


class ReviewGate:
    def __init__(self, pre_checks: list[GateCheck] | None = None,
                 post_checks: list[GateCheck] | None = None):
        # Before extraction: do we even have two readable, right-typed documents?
        self.pre_checks = pre_checks or [AttachmentCheck(), ReadableCheck(), DocTypeCheck()]
        # After extraction: are the values complete?
        self.post_checks = post_checks or [ValueCheck()]

    def before_extraction(self, ctx: GateContext, log: Optional[list] = None) -> Optional[ReviewReason]:
        return self._run(self.pre_checks, ctx, log)

    def after_extraction(self, ctx: GateContext, log: Optional[list] = None) -> Optional[ReviewReason]:
        return self._run(self.post_checks, ctx, log)

    @staticmethod
    def _run(checks, ctx, log):
        """Run checks in order; the first failure wins. `log` collects
        (label, reason-or-None) for the audit trail."""
        for c in checks:
            reason = c.check(ctx)
            if log is not None:
                log.append((c.label, reason))
            if reason is not None:
                return reason
        return None
