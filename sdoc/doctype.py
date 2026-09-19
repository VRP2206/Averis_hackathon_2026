"""Decide what kind of document an attachment actually is.

Content wins over the filename: a file named `_BL` whose first lines say
COMMERCIAL INVOICE is a Commercial Invoice.
"""
from __future__ import annotations

import re

from .models import Document, DocType

_TITLE_RULES: list[tuple[re.Pattern, DocType]] = [
    (re.compile(r"commercial invoice", re.I), DocType.COMMERCIAL_INVOICE),
    (re.compile(r"packing list", re.I), DocType.PACKING_LIST),
    (re.compile(r"certificate of origin", re.I), DocType.CERTIFICATE_OF_ORIGIN),
    # "BILL OF LADING INSTRUCTION" is an SI, so the instruction rule comes first.
    (re.compile(r"shipping instruction|lading instruction|bl instruction|\bs\.?i\.?\b(?!\w)", re.I), DocType.SI),
    (re.compile(r"bill of lading|\bb/?l\b.*(draft|no\.?)", re.I), DocType.BL),
]


class DocTypeDetector:
    def detect(self, doc: Document) -> DocType:
        if not doc.readable:
            return self._from_name(doc.path)
        head = "\n".join(doc.lines[:6])
        for pattern, kind in _TITLE_RULES:
            if pattern.search(head):
                return kind
        # Look further down the page, then fall back to the filename.
        for pattern, kind in _TITLE_RULES:
            if pattern.search(doc.text[:2000]):
                return kind
        return self._from_name(doc.path)

    @staticmethod
    def _from_name(path: str) -> DocType:
        stem = path.rsplit("/", 1)[-1].upper()
        if "_SI." in stem:
            return DocType.SI
        if "_BL." in stem:
            return DocType.BL
        return DocType.UNKNOWN
