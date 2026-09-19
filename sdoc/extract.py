"""Stage 2: pull the 7 comparison fields out of an SI or BL document.

`HeuristicExtractor` matches label synonyms ("POD", "Discharge Port",
"Port of Discharge (POD)") against label/value lines. It is exact, free
and covers the common layouts. `LLMExtractor` reads the whole document
and is used by `CascadeExtractor` only for fields the heuristic missed.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Optional

from .llm import LLMClient, try_llm
from .models import COMPARE_FIELDS, Document, DocType, ExtractedField, Extraction
from .textnorm import norm_label, squash

# Synonyms per field. Matching is on `norm_label()` output, so "Port of
# Loading (POL)" and "PORT OF LOADING" both become "portofloading".
LABEL_SYNONYMS: dict[str, list[str]] = {
    "shipper": ["Shipper", "Shipper/Exporter", "Shipper (Principal or Seller)", "Exporter",
                "Shipper Name", "Shipper / Exporter"],
    "consignee": ["Consignee", "Consignee (Non-Negotiable)", "To the Order of", "Consigned to",
                  "Consignee Name"],
    "notify_party": ["Notify Party", "Notify", "Notify Party/Intermediate Consignee", "Notify Address",
                     "Also Notify"],
    "port_of_loading": ["Port of Loading", "Port of Loading (POL)", "Load Port", "POL", "Loading Port",
                        "Port of Departure"],
    "port_of_discharge": ["Port of Discharge", "Port of Discharge (POD)", "Discharge Port", "POD",
                          "Discharging Port", "Port of Unloading"],
    "container_count": ["No. of Containers", "Total Containers", "No. of Containers or Packages",
                        "Container Count", "Number of Containers", "Containers", "Total No. of Containers",
                        "Container Qty", "Qty of Containers"],
    "gross_weight_kg": ["Gross Weight (KG)", "Gross Wt (kgs)", "Gross Weight", "GROSS WEIGHT",
                        "Total Gross Weight", "G.W.", "GW", "Gross Wt", "Total Gross Wt"],
}
_NORMED: dict[str, str] = {}
for _field, _labels in LABEL_SYNONYMS.items():
    for _l in _labels:
        _NORMED[norm_label(_l)] = _field
        _NORMED["total" + norm_label(_l)] = _field      # "TOTAL Gross Wt (kgs)"

BLANK_RE = re.compile(r"^\s*(\?+|_+\s*(mt|kg|kgs)?|tba|tbc|tbd|n/?a|-+|none|nil)?\s*$", re.I)


def is_blank(value: Optional[str]) -> bool:
    return value is None or bool(BLANK_RE.match(value))


class Extractor(ABC):
    @abstractmethod
    def extract(self, doc: Document) -> Extraction: ...


class HeuristicExtractor(Extractor):
    """Label-synonym matching over (label, value) candidates."""

    def extract(self, doc: Document) -> Extraction:
        found: dict[str, ExtractedField] = {}
        for label, value, source in self._candidates(doc):
            field = self._field_for(label)
            if field is None or field in found:
                continue
            value = self._clean_value(field, value)
            found[field] = ExtractedField(field=field, value=value, source=source,
                                          confidence=0.95 if not is_blank(value) else 0.9,
                                          blank=is_blank(value))
        for f in COMPARE_FIELDS:
            found.setdefault(f, ExtractedField(field=f, value=None, source=None, confidence=0.0))
        return Extraction(doc_path=doc.path, doc_type=doc.doc_type, fields=found, method="heuristic")

    # -- candidates ----------------------------------------------------------
    def _candidates(self, doc: Document):
        # Structured pairs first (DOCX / XLSX tables) - most reliable.
        for label, value in doc.pairs:
            yield label, value, f"{label}: {value}"[:200]
        for line in doc.lines:
            if ":" in line:
                label, value = line.split(":", 1)
                if len(label) <= 60:
                    yield label, value, line
            # PDF layout: "<Label>   <value>" separated by spaces only.
            yield from self._split_space_separated(line)

    def _split_space_separated(self, line: str):
        words = line.split()
        # Try label prefixes of 1..5 words.
        for n in range(min(5, len(words) - 1), 0, -1):
            label = " ".join(words[:n])
            if self._field_for(label) is not None:
                yield label, " ".join(words[n:]), line
                return

    @staticmethod
    def _field_for(label: str) -> Optional[str]:
        key = norm_label(label)
        if key in _NORMED:
            return _NORMED[key]
        # Tolerate a few stray characters after a known label, e.g. a CJK
        # gloss that a PDF font rendered as junk: "grossweightnn".
        for syn, field in _NORMED.items():
            if len(syn) >= 6 and key.startswith(syn) and len(key) - len(syn) <= 4:
                return field
        return None

    @staticmethod
    def _clean_value(field: str, value: str) -> str:
        value = value.strip()
        if field in ("shipper", "consignee", "notify_party"):
            # "NAME | addr; addr" (xlsx) or "NAME\naddr" (docx): keep the name.
            value = value.split("|")[0].splitlines()[0] if value else value
        return squash(value)


class LLMExtractor(Extractor):
    SYSTEM = (
        "You extract fields from shipping documents (Shipping Instruction or Bill of Lading). "
        "Labels vary: 'POD', 'Discharge Port' and 'Port of Discharge' are the same field; "
        "'To the Order of' is the consignee; 'Notify' is the notify party. Copy values exactly as "
        "written. For parties give the company name only (first line). If a value is a placeholder "
        "such as ???, ____, TBA or blank, return it as written and set blank=true. If a field is not "
        "present, value=null. Reply with JSON only:\n"
        '{"doc_type": "SI|BL|COMMERCIAL_INVOICE|PACKING_LIST|CERTIFICATE_OF_ORIGIN|UNKNOWN", '
        '"fields": {"<field>": {"value": str|null, "source_line": str|null, "confidence": 0-1, "blank": bool}}}\n'
        f"Fields: {', '.join(COMPARE_FIELDS)}.")

    def __init__(self, llm: LLMClient, strong: bool = False):
        self.llm, self.strong = llm, strong

    def extract(self, doc: Document) -> Extraction:
        reply = try_llm(self.llm, self.SYSTEM, f"Document ({doc.kind}):\n\n{doc.text[:6000]}",
                        strong=self.strong, max_tokens=900)
        fields: dict[str, ExtractedField] = {}
        raw = (reply or {}).get("fields", {}) if isinstance(reply, dict) else {}
        for f in COMPARE_FIELDS:
            item = raw.get(f) or {}
            value = item.get("value")
            value = squash(str(value)) if value is not None else None
            fields[f] = ExtractedField(
                field=f, value=value, source=item.get("source_line"),
                confidence=float(item.get("confidence", 0.0)) if value is not None else 0.0,
                blank=bool(item.get("blank")) or is_blank(value) if value is not None else False)
        doc_type = doc.doc_type
        if reply and reply.get("doc_type") in DocType.__members__:
            doc_type = DocType(reply["doc_type"])
        return Extraction(doc_path=doc.path, doc_type=doc_type, fields=fields, method="llm")


class CascadeExtractor(Extractor):
    """Heuristic first; ask the LLM only for fields still missing."""

    def __init__(self, heuristic: HeuristicExtractor, llm: Optional[LLMExtractor],
                 min_confidence: float = 0.6):
        self.heuristic, self.llm, self.min_confidence = heuristic, llm, min_confidence

    def extract(self, doc: Document) -> Extraction:
        result = self.heuristic.extract(doc)
        missing = [f for f, ef in result.fields.items() if ef.confidence < self.min_confidence]
        if not missing or self.llm is None or not self.llm.llm.available:
            return result
        llm_result = self.llm.extract(doc)
        for f in missing:
            cand = llm_result.fields[f]
            if cand.value is not None and cand.confidence >= self.min_confidence:
                result.fields[f] = cand
        result.method = "heuristic+llm"
        return result
