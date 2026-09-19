"""Stage 3: normalise each field and compare SI against BL.

Plain, deterministic code: ports compare by UN/LOCODE when present,
container strings become a count, weights become whole kilograms, and
party names are compared case- and punctuation-insensitively.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Optional

from .models import COMPARE_FIELDS, Extraction, FieldComparison


class Normaliser(ABC):
    @abstractmethod
    def normalise(self, value: str) -> Optional[str]: ...

    def equal(self, a: Optional[str], b: Optional[str]) -> bool:
        return a is not None and a == b


class PartyNormaliser(Normaliser):
    _LEGAL = re.compile(r"\b(co|ltd|limited|inc|llc|pte|sdn|bhd|gmbh|ag|sa|plc|fze|fzco|corp|corporation)\b\.?")

    def normalise(self, value):
        v = value.upper().split("|")[0]
        v = re.sub(r"[^\w& ]+", " ", v)
        v = re.sub(r"\s+", " ", v).strip()
        return v or None

    def equal(self, a, b):
        if a is None or b is None:
            return False
        if a == b:
            return True
        # Tolerate differences only in legal-form suffixes / punctuation.
        strip = lambda s: re.sub(r"\s+", " ", self._LEGAL.sub("", s.lower())).strip()
        return strip(a) == strip(b)


class PortNormaliser(Normaliser):
    """Normalised form is "NAME|LOCODE". Two ports match only if the names
    agree and, when both carry a UN/LOCODE, the codes agree too: a BL that
    says "BUSAN (VNSGN)" against an SI "HOCHIMINH CITY (VNSGN)" is a defect."""

    _LOCODE = re.compile(r"\(([A-Z]{5})\)")

    def normalise(self, value):
        upper = value.upper()
        m = self._LOCODE.search(upper)
        code = m.group(1) if m else ""
        name = re.sub(r"\(\s*[A-Z]{5}\s*\)", " ", upper)          # drop the code
        name = re.sub(r"[^A-Z ]+", " ", name)                       # drop punctuation, "(WESTPORT)" stays as words
        name = re.sub(r"\s+", " ", name).strip()
        if not name and not code:
            return None
        return f"{name}|{code}"

    def equal(self, a, b):
        if a is None or b is None:
            return False
        an, ac = a.split("|"); bn, bc = b.split("|")
        if ac and bc and ac != bc:
            return False
        return an == bn


class CountNormaliser(Normaliser):
    _NUM = re.compile(r"\d+")

    def normalise(self, value):
        m = self._NUM.search(value.replace(",", ""))
        return m.group(0).lstrip("0") or "0" if m else None


class WeightKgNormaliser(Normaliser):
    _NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(kgs?|kilograms?|mts?|tons?|t\b)?", re.I)

    def normalise(self, value):
        m = self._NUM.search(value)
        if not m:
            return None
        n = float(m.group(1).replace(",", ""))
        unit = (m.group(2) or "kg").lower()
        if unit.startswith(("mt", "ton", "t")):
            n *= 1000
        return str(int(round(n)))


NORMALISERS: dict[str, Normaliser] = {
    "shipper": PartyNormaliser(),
    "consignee": PartyNormaliser(),
    "notify_party": PartyNormaliser(),
    "port_of_loading": PortNormaliser(),
    "port_of_discharge": PortNormaliser(),
    "container_count": CountNormaliser(),
    "gross_weight_kg": WeightKgNormaliser(),
}


class Comparator:
    def __init__(self, normalisers: dict[str, Normaliser] | None = None):
        self.normalisers = normalisers or NORMALISERS

    def compare(self, si: Extraction, bl: Extraction) -> list[FieldComparison]:
        out: list[FieldComparison] = []
        for f in COMPARE_FIELDS:
            n = self.normalisers[f]
            s, b = si.fields[f], bl.fields[f]
            sn = n.normalise(s.value) if s.usable else None
            bn = n.normalise(b.value) if b.usable else None
            out.append(FieldComparison(field=f, si_value=s.value, bl_value=b.value,
                                       si_normalised=sn, bl_normalised=bn, match=n.equal(sn, bn)))
        return out
