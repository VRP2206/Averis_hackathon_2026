"""Where results live. The API uses `InMemoryStore`; the backend can swap
in DynamoDB / Firestore by implementing `ResultStore`."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Optional

from .models import EmailResult


class ResultStore(ABC):
    @abstractmethod
    def put(self, result: EmailResult) -> None: ...

    @abstractmethod
    def get(self, email_id: str) -> Optional[EmailResult]: ...

    @abstractmethod
    def all(self) -> list[EmailResult]: ...

    def put_many(self, results: Iterable[EmailResult]) -> None:
        for r in results:
            self.put(r)

    def submission(self) -> dict:
        return {r.email_id: r.to_submission() for r in sorted(self.all(), key=lambda r: r.email_id)}


class InMemoryStore(ResultStore):
    def __init__(self):
        self._data: dict[str, EmailResult] = {}

    def put(self, result):
        self._data[result.email_id] = result

    def get(self, email_id):
        return self._data.get(email_id)

    def all(self):
        return list(self._data.values())


class JsonFileStore(InMemoryStore):
    """In-memory with a JSON file behind it (survives restarts, no DB)."""

    def __init__(self, path: Path | str):
        super().__init__()
        self.path = Path(path)
        if self.path.exists():
            for item in json.loads(self.path.read_text(encoding="utf-8")):
                r = EmailResult.model_validate(item)
                self._data[r.email_id] = r

    def put(self, result):
        super().put(result)
        self._flush()

    def put_many(self, results):
        for r in results:
            self._data[r.email_id] = r
        self._flush()

    def _flush(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([r.model_dump(mode="json") for r in self._data.values()], indent=1),
                             encoding="utf-8")
