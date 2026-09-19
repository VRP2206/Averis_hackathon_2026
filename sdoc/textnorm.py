"""Small text utilities shared by classification and extraction."""
from __future__ import annotations

import re

_SIG_MARKERS = re.compile(
    r"^\s*(best regards|regards|thanks|thank you|kind regards|--\s*$|sent from my)", re.I)
_QUOTE_MARKERS = re.compile(
    r"^\s*(from:|-----original message-----|on .+ wrote:|>)", re.I)
_BANNER = re.compile(r"^\s*(caution|warning|external)[:\s].*(external|outside).*$", re.I | re.M)


def strip_noise(body: str) -> str:
    """Drop signature blocks, quoted threads and external-sender banners so
    classification keys off what the sender actually wrote."""
    body = _BANNER.sub("", body or "")
    kept: list[str] = []
    for line in body.splitlines():
        if _QUOTE_MARKERS.match(line) or _SIG_MARKERS.match(line):
            break
        kept.append(line)
    return "\n".join(kept).strip()


def norm_label(label: str) -> str:
    """Normalise a field label for synonym matching: lowercase, drop CJK
    glosses, brackets and punctuation."""
    label = re.sub(r"[　-鿿＀-￯]+", " ", label)   # CJK
    label = re.sub(r"\(.*?\)", " ", label)                          # (POL), (KGS)
    label = re.sub(r"[^a-z0-9]+", "", label.lower())
    return label


def squash(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()
