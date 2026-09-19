"""Language detection and translation for non-English emails, via the
configured LLM. Deterministic fallback: detect obvious non-Latin scripts and
report that translation needs an LLM provider."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .llm import LLMClient, try_llm

_SCRIPTS = [
    (re.compile(r"[一-鿿]"), "zh"), (re.compile(r"[぀-ヿ]"), "ja"),
    (re.compile(r"[가-힯]"), "ko"), (re.compile(r"[؀-ۿ]"), "ar"),
    (re.compile(r"[฀-๿]"), "th"), (re.compile(r"[Ѐ-ӿ]"), "ru"),
]
_MALAY = re.compile(r"\b(sila|terima kasih|tuan|puan|mohon|sertakan|tarikh)\b", re.I)


@dataclass
class Translation:
    source_language: str
    target_language: str
    text: str
    translated: bool
    note: str = ""


class Translator:
    SYSTEM = ("You translate business emails about shipping documents. Keep reference numbers, "
              "company names, ports and dates exactly as written. Reply with JSON only: "
              '{"source_language": "<ISO 639-1>", "translation": "<text in the target language>"}')

    def __init__(self, llm: LLMClient):
        self.llm = llm

    @staticmethod
    def guess_language(text: str) -> str:
        for pat, code in _SCRIPTS:
            if pat.search(text):
                return code
        if _MALAY.search(text):
            return "ms"
        return "en"

    def translate(self, text: str, target: str = "en") -> Translation:
        guess = self.guess_language(text)
        if guess == target:
            return Translation(guess, target, text, False, "already in the target language (heuristic)")
        reply = try_llm(self.llm, self.SYSTEM,
                        f"Target language: {target}\n\n{text[:6000]}", max_tokens=2000)
        if not reply or "translation" not in reply:
            return Translation(guess, target, text, False,
                               "translation needs an LLM provider (set SDOC_LLM_PROVIDER)")
        return Translation(str(reply.get("source_language", guess)), target, str(reply["translation"]), True)
