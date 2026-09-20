"""Where results live. Locally the API uses `JsonFileStore`; on AWS set
SDOC_DYNAMODB_TABLE and it uses `DynamoDBStore` (see `make_store`)."""
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

    def count(self) -> int:
        return len(self.all())

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


class DynamoDBStore(ResultStore):
    """One item per email. Lambda instances are ephemeral and run side by side,
    so results must live outside the process: this is what makes `POST /process`
    on one instance visible to `GET /emails` on another.

    Item layout: `email_id` (partition key), a few top-level attributes so the
    table is readable in the AWS console, and `data` = the full EmailResult as
    a JSON string. A string avoids DynamoDB's float -> Decimal conversion
    (confidence scores are floats) and the 400 KB item limit is far away.
    """

    def __init__(self, table_name: str, region: str | None = None, *, resource=None):
        if resource is None:
            import boto3
            resource = boto3.resource("dynamodb", region_name=region)
        self._table = resource.Table(table_name)

    @staticmethod
    def _item(r: EmailResult) -> dict:
        return {"email_id": r.email_id, "category": r.category.value, "status": r.status.value,
                "decided_by": r.decided_by, "data": r.model_dump_json()}

    def put(self, result):
        self._table.put_item(Item=self._item(result))

    def put_many(self, results):
        with self._table.batch_writer(overwrite_by_pkeys=["email_id"]) as batch:
            for r in results:
                batch.put_item(Item=self._item(r))

    def get(self, email_id):
        item = self._table.get_item(Key={"email_id": email_id}).get("Item")
        return EmailResult.model_validate_json(item["data"]) if item else None

    def all(self):
        out, kwargs = [], {}
        while True:                      # a scan returns at most 1 MB per page
            page = self._table.scan(**kwargs)
            out += [EmailResult.model_validate_json(i["data"]) for i in page["Items"]]
            if "LastEvaluatedKey" not in page:
                return out
            kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]

    def count(self):
        n, kwargs = 0, {"Select": "COUNT"}
        while True:
            page = self._table.scan(**kwargs)
            n += page["Count"]
            if "LastEvaluatedKey" not in page:
                return n
            kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def make_store(table: str, json_path: Path | str) -> ResultStore:
    """DynamoDB when a table name is configured, otherwise a local JSON file."""
    if table:
        return DynamoDBStore(table)
    return JsonFileStore(json_path)
