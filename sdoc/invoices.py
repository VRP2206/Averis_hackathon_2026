"""Receipts / invoices view: pull invoice numbers, order refs and amounts out
of billing emails so a reviewer can find a charge without opening each one.
Regex-based, deterministic; the source line is kept as evidence."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .models import Category, Email
from .textnorm import strip_noise

_INVOICE = re.compile(r"\b(?:invoice|inv\.?|billing|bill)\s*(?:no\.?|#|number|-)?\s*[:#-]?\s*(\d{6,12})\b", re.I)
_BARE_NUM = re.compile(r"\b(\d{10})\b")                       # SAP-style billing document numbers
_OC = re.compile(r"\b(5[A-Z]{3}-\d{5})\b")                     # order confirmation refs, e.g. 5RSG-00133
_AMOUNT = re.compile(r"\b(USD|MYR|RM|SGD|EUR|AED|INR|\$)\s?([\d,]+(?:\.\d{1,2})?)", re.I)
_TOPIC = [
    (re.compile(r"cancel", re.I), "cancellation"),
    (re.compile(r"missing gr|goods receipt", re.I), "missing goods receipt"),
    (re.compile(r"d\s*&\s*d|demurrage|detention", re.I), "demurrage / detention"),
    (re.compile(r"local charges|thc|telex", re.I), "local charges"),
    (re.compile(r"freight", re.I), "freight"),
]


@dataclass
class InvoiceRecord:
    email_id: str
    sender: str
    subject: str
    topic: str
    invoice_numbers: list[str] = field(default_factory=list)
    order_refs: list[str] = field(default_factory=list)
    amounts: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class InvoiceExtractor:
    def extract(self, email: Email) -> InvoiceRecord:
        text = f"{email.subject}\n{strip_noise(email.body)}"
        rec = InvoiceRecord(email_id=email.email_id, sender=email.sender, subject=email.subject,
                            topic=next((t for p, t in _TOPIC if p.search(text)), "query"))
        rec.invoice_numbers = self._uniq(_INVOICE.findall(text) or _BARE_NUM.findall(text))
        rec.order_refs = self._uniq(_OC.findall(text))
        rec.amounts = self._uniq(f"{c.upper()} {n}" for c, n in _AMOUNT.findall(text))
        rec.evidence = [ln.strip() for ln in text.splitlines()
                        if ln.strip() and (_INVOICE.search(ln) or _AMOUNT.search(ln))][:4]
        return rec

    def extract_all(self, emails: list[Email], categories: dict[str, str]) -> list[InvoiceRecord]:
        return [self.extract(e) for e in emails
                if categories.get(e.email_id) == Category.INVOICE_QUERY.value]

    @staticmethod
    def _uniq(items) -> list[str]:
        seen: list[str] = []
        for i in items:
            if i not in seen:
                seen.append(i)
        return seen
