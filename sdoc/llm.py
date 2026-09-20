"""LLM access behind one small interface, with a disk cache.

`LLMClient.complete_json()` sends a system + user prompt and returns parsed
JSON. Implementations: Anthropic API, Amazon Bedrock, or `NullClient`
(always unavailable, so the pipeline stays on rules and heuristics).
"""
from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from .config import Settings

log = logging.getLogger(__name__)

_JSON_ONLY = "\n\nReply with a single JSON object and nothing else: no prose, no code fences."


class LLMUnavailable(RuntimeError):
    pass


class LLMClient(ABC):
    available: bool = True

    @abstractmethod
    def complete_json(self, system: str, user: str, *, strong: bool = False,
                      max_tokens: int = 1024) -> dict[str, Any]: ...

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text[text.find("{"):]
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end < 0:
            raise ValueError(f"no JSON object in LLM reply: {text[:120]!r}")
        return json.loads(text[start:end + 1])


class NullClient(LLMClient):
    available = False

    def complete_json(self, system, user, *, strong=False, max_tokens=1024):
        raise LLMUnavailable("no LLM provider configured (SDOC_LLM_PROVIDER=none)")


class AnthropicClient(LLMClient):
    def __init__(self, fast_model: str, strong_model: str):
        import anthropic
        self._client = anthropic.Anthropic()          # reads ANTHROPIC_API_KEY
        self.fast_model, self.strong_model = fast_model, strong_model

    def complete_json(self, system, user, *, strong=False, max_tokens=1024):
        if strong:
            # Claude 4.6+ (Sonnet 5 included) answers 400 to an assistant prefill, so ask for JSON in the prompt.
            msg = self._client.messages.create(
                model=self.strong_model, max_tokens=max_tokens, system=system + _JSON_ONLY,
                messages=[{"role": "user", "content": user}],
            )
            return self._parse_json(next(b.text for b in msg.content if b.type == "text"))
        msg = self._client.messages.create(
            model=self.fast_model,
            max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user},
                      {"role": "assistant", "content": "{"}],   # prefill: JSON only (Haiku 4.5 still allows it)
        )
        return self._parse_json("{" + msg.content[0].text)


class BedrockClient(LLMClient):
    def __init__(self, region: str, fast_model: str, strong_model: str):
        import boto3
        self._client = boto3.client("bedrock-runtime", region_name=region)
        self.fast_model, self.strong_model = fast_model, strong_model

    def complete_json(self, system, user, *, strong=False, max_tokens=1024):
        if strong:
            # Sonnet 5 rejects assistant prefill and non-default temperature (400), so neither is sent.
            resp = self._client.converse(
                modelId=self.strong_model,
                system=[{"text": system + _JSON_ONLY}],
                messages=[{"role": "user", "content": [{"text": user}]}],
                inferenceConfig={"maxTokens": max_tokens},
            )
            blocks = resp["output"]["message"]["content"]
            return self._parse_json(next(b["text"] for b in blocks if "text" in b))
        resp = self._client.converse(
            modelId=self.fast_model,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user}]},
                      {"role": "assistant", "content": [{"text": "{"}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0},
        )
        return self._parse_json("{" + resp["output"]["message"]["content"][0]["text"])


class GeminiClient(LLMClient):
    """Google Gemini via the REST API (no SDK dependency). Uses JSON mode."""

    ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, fast_model: str, strong_model: str):
        import os
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise LLMUnavailable("GEMINI_API_KEY not set")
        self.fast_model, self.strong_model = fast_model, strong_model

    def complete_json(self, system, user, *, strong=False, max_tokens=1024):
        import urllib.request
        body = json.dumps({
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": max_tokens,
                                 "responseMimeType": "application/json"},
        }).encode()
        req = urllib.request.Request(
            self.ENDPOINT.format(model=self.strong_model if strong else self.fast_model),
            data=body, headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return self._parse_json(text)


class CachedClient(LLMClient):
    """Caches replies on disk keyed by prompt hash, so reruns are free."""

    def __init__(self, inner: LLMClient, cache_dir: Path):
        self.inner, self.cache_dir = inner, cache_dir
        self.available = inner.available
        cache_dir.mkdir(parents=True, exist_ok=True)

    def complete_json(self, system, user, *, strong=False, max_tokens=1024):
        key = hashlib.sha256(f"{strong}|{system}|{user}".encode()).hexdigest()
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        result = self.inner.complete_json(system, user, strong=strong, max_tokens=max_tokens)
        path.write_text(json.dumps(result), encoding="utf-8")
        return result


def build_llm(cfg: Settings) -> LLMClient:
    # Provider SDKs read their keys from the process environment; make sure
    # values from .env are there too (pydantic-settings keeps them private).
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    inner: LLMClient
    try:
        if cfg.llm_provider == "anthropic":
            inner = AnthropicClient(cfg.llm_fast_model, cfg.llm_strong_model)
        elif cfg.llm_provider == "bedrock":
            inner = BedrockClient(cfg.bedrock_region, cfg.bedrock_fast_model, cfg.bedrock_strong_model)
        elif cfg.llm_provider == "gemini":
            inner = GeminiClient(cfg.gemini_fast_model, cfg.gemini_strong_model)
        else:
            return NullClient()
    except Exception as exc:
        log.warning("LLM provider %s unavailable (%s); running rules-only", cfg.llm_provider, exc)
        return NullClient()
    return CachedClient(inner, cfg.llm_cache_dir)


def try_llm(client: LLMClient, system: str, user: str, **kw) -> Optional[dict[str, Any]]:
    """Call the LLM, or return None if it is unavailable or fails."""
    if not client.available:
        return None
    try:
        return client.complete_json(system, user, **kw)
    except Exception as exc:
        log.warning("LLM call failed: %s", exc)
        return None
