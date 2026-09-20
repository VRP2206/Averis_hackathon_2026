"""Attachment readers: turn bytes into a `Document` (text + label/value pairs).

A reader never raises for bad input: an empty, corrupt or image-only file
comes back with `readable=False` and an `error`, and the gate turns that
into NEEDS_REVIEW / unreadable.
"""
from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from pathlib import PurePosixPath

from .models import Document

log = logging.getLogger(__name__)


class DocumentReader(ABC):
    extensions: tuple[str, ...] = ()

    def read(self, path: str, data: bytes) -> Document:
        kind = PurePosixPath(path).suffix.lstrip(".").lower()
        if not data:
            return Document(path=path, kind=kind, readable=False, error="empty file (0 bytes)")
        try:
            text, pairs = self._parse(data)
        except Exception as exc:  # corrupt / truncated file
            log.debug("reader failed on %s: %s", path, exc)
            return Document(path=path, kind=kind, readable=False, error=f"cannot parse: {type(exc).__name__}")
        if not text.strip() and not pairs:
            return Document(path=path, kind=kind, readable=False,
                            error="no text layer (scanned image?)")
        return Document(path=path, kind=kind, text=text, pairs=pairs)

    @abstractmethod
    def _parse(self, data: bytes) -> tuple[str, list[tuple[str, str]]]: ...


class TxtReader(DocumentReader):
    extensions = ("txt",)

    def _parse(self, data):
        return data.decode("utf-8", errors="replace"), []


class PdfReader(DocumentReader):
    extensions = ("pdf",)

    def _parse(self, data):
        try:
            return self._parse_pdf(data)
        except Exception:
            # Git on Windows can rewrite line endings inside .pdf files (LF -> CRLF).
            # That shifts every byte offset and breaks the PDF cross-reference table.
            # Undoing the conversion restores the original file exactly, so retry once.
            fixed = data.replace(b"\r\n", b"\n")
            if fixed == data:
                raise
            return self._parse_pdf(fixed)

    def _parse_pdf(self, data):
        import pdfplumber
        parts, pairs = [], []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
                pairs.extend(self._bold_label_pairs(page))
        return "\n".join(parts), pairs

    @staticmethod
    def _bold_label_pairs(page) -> list[tuple[str, str]]:
        """Form layouts print the label in bold and the value in regular
        weight on the same line. Splitting by font avoids the glyph
        interleaving `extract_text` produces when a long label overlaps
        the value column."""
        words = page.extract_words(extra_attrs=["fontname"])
        rows: dict[int, list] = {}
        for w in words:
            rows.setdefault(round(w["top"] / 3), []).append(w)   # 3pt line tolerance
        pairs = []
        for _, ws in sorted(rows.items()):
            ws.sort(key=lambda w: w["x0"])
            label = " ".join(w["text"] for w in ws if "bold" in w["fontname"].lower())
            value = " ".join(w["text"] for w in ws if "bold" not in w["fontname"].lower())
            if label and value:
                pairs.append((label.rstrip(": "), value))
        return pairs


class DocxReader(DocumentReader):
    extensions = ("docx",)

    def _parse(self, data):
        from docx import Document as Docx
        d = Docx(io.BytesIO(data))
        lines = [p.text for p in d.paragraphs if p.text.strip()]
        pairs: list[tuple[str, str]] = []
        for table in d.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells]
                if len(cells) >= 2 and cells[0]:
                    pairs.append((cells[0], cells[1]))
                    lines.append(f"{cells[0]}: {cells[1]}")
        return "\n".join(lines), pairs


class XlsxReader(DocumentReader):
    extensions = ("xlsx", "xlsm")

    def _parse(self, data):
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        lines, pairs = [], []
        for ws in wb.worksheets:
            lines.append(f"[sheet] {ws.title}")
            for row in ws.iter_rows(values_only=True):
                cells = ["" if v is None else str(v).strip() for v in row]
                if not any(cells):
                    continue
                if len(cells) >= 2 and cells[0] and cells[1]:
                    pairs.append((cells[0], cells[1]))
                lines.append(": ".join(c for c in cells if c))
        return "\n".join(lines), pairs


class ReaderRegistry:
    """Picks a reader by file extension. Unknown types are unreadable."""

    def __init__(self, readers: list[DocumentReader] | None = None):
        self._by_ext: dict[str, DocumentReader] = {}
        for r in readers or [TxtReader(), PdfReader(), DocxReader(), XlsxReader()]:
            self.register(r)

    def register(self, reader: DocumentReader) -> None:
        for ext in reader.extensions:
            self._by_ext[ext] = reader

    def read(self, path: str, data: bytes) -> Document:
        kind = PurePosixPath(path).suffix.lstrip(".").lower()
        reader = self._by_ext.get(kind)
        if reader is None:
            return Document(path=path, kind=kind, readable=False, error=f"unsupported type .{kind}")
        return reader.read(path, data)
