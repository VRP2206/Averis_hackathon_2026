"""Inbox access: local bundle folder or the organisers' HTTP server."""
from __future__ import annotations

import json
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path

from .models import Email


class InboxRepository(ABC):
    @abstractmethod
    def emails(self) -> list[Email]: ...

    @abstractmethod
    def get(self, email_id: str) -> Email: ...

    @abstractmethod
    def read_bytes(self, attachment_path: str) -> bytes: ...

    def __iter__(self):
        return iter(self.emails())


class LocalInbox(InboxRepository):
    def __init__(self, root: Path | str):
        self.root = Path(root)
        if not (self.root / "inbox").is_dir():
            raise FileNotFoundError(f"No inbox/ folder under {self.root}")

    def emails(self) -> list[Email]:
        return [Email.model_validate(json.loads(p.read_text(encoding="utf-8")))
                for p in sorted((self.root / "inbox").glob("email_*.json"))]

    def get(self, email_id: str) -> Email:
        p = self.root / "inbox" / f"{email_id}.json"
        return Email.model_validate(json.loads(p.read_text(encoding="utf-8")))

    def read_bytes(self, attachment_path: str) -> bytes:
        return (self.root / attachment_path).read_bytes()


class HttpInbox(InboxRepository):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str) -> bytes:
        with urllib.request.urlopen(self.base_url + path, timeout=30) as r:
            return r.read()

    def emails(self) -> list[Email]:
        return [Email.model_validate(e) for e in json.loads(self._get("/emails"))]

    def get(self, email_id: str) -> Email:
        return Email.model_validate(json.loads(self._get(f"/emails/{email_id}")))

    def read_bytes(self, attachment_path: str) -> bytes:
        return self._get("/" + attachment_path.lstrip("/"))

    def submit(self, submission: dict) -> dict:
        req = urllib.request.Request(
            self.base_url + "/submit", data=json.dumps(submission).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())


def open_inbox(source: str | Path) -> InboxRepository:
    s = str(source)
    if s.startswith(("http://", "https://")):
        return HttpInbox(s)
    return LocalInbox(s)
