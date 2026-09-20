"""AWS glue: DynamoDBStore (against moto) and the Lambda handler (Function URL event)."""
import json

import pytest

pytest.importorskip("moto")
pytest.importorskip("mangum")
boto3 = pytest.importorskip("boto3")
from moto import mock_aws  # noqa: E402

from sdoc.models import EmailResult, Status  # noqa: E402
from sdoc.store import DynamoDBStore, make_store  # noqa: E402


@pytest.fixture
def table(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    with mock_aws():
        boto3.client("dynamodb").create_table(
            TableName="sdoc-results", BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[{"AttributeName": "email_id", "AttributeType": "S"}],
            KeySchema=[{"AttributeName": "email_id", "KeyType": "HASH"}])
        yield "sdoc-results"


def _result(i: int, status=Status.OK) -> EmailResult:
    return EmailResult(email_id=f"email_{i:03d}", category="BL_COMPARISON", status=status,
                       notes=[f"note {i}"])


def test_roundtrip_keeps_every_field(table):
    store = DynamoDBStore(table)
    r = _result(1, Status.MISMATCH)
    r.defect_fields, r.has_defect = ["consignee"], True
    store.put(r)
    assert store.get("email_001") == r
    assert store.get("email_999") is None


def test_all_pages_and_count(table):
    store = DynamoDBStore(table)
    store.put_many(_result(i) for i in range(60))     # > 25 exercises batch_writer flushing
    assert store.count() == 60
    assert sorted(x.email_id for x in store.all()) == [f"email_{i:03d}" for i in range(60)]
    assert list(store.submission())[0] == "email_000"


def test_put_overwrites(table):
    store = DynamoDBStore(table)
    store.put(_result(1))
    store.put(_result(1, Status.NEEDS_REVIEW))
    assert store.count() == 1 and store.get("email_001").status == Status.NEEDS_REVIEW


def test_make_store_picks_backend(table, tmp_path):
    from sdoc.store import JsonFileStore
    assert isinstance(make_store(table, tmp_path / "r.json"), DynamoDBStore)
    assert isinstance(make_store("", tmp_path / "r.json"), JsonFileStore)


def _event(method: str, path: str, body: dict | None = None) -> dict:
    """A Lambda Function URL request (payload format 2.0)."""
    return {"version": "2.0", "routeKey": "$default", "rawPath": path, "rawQueryString": "",
            "headers": {"content-type": "application/json", "host": "abc.lambda-url.us-east-1.on.aws"},
            "requestContext": {"http": {"method": method, "path": path, "protocol": "HTTP/1.1",
                                        "sourceIp": "1.2.3.4", "userAgent": "pytest"}},
            "body": json.dumps(body) if body else None, "isBase64Encoded": False}


def test_lambda_handler_end_to_end(table, inbox, monkeypatch):
    import sdoc.api as api
    from sdoc.lambda_handler import handler
    monkeypatch.setattr(api, "_store", DynamoDBStore(table))
    monkeypatch.setattr(api, "_pipeline", None)

    health = handler(_event("GET", "/health"), None)
    assert health["statusCode"] == 200 and json.loads(health["body"])["results"] == 0

    done = handler(_event("POST", "/process/email_001"), None)
    assert done["statusCode"] == 200

    health = handler(_event("GET", "/health"), None)
    assert json.loads(health["body"])["results"] == 1
    emails = json.loads(handler(_event("GET", "/emails"), None)["body"])
    assert len(emails) == 520
    assert emails[0]["result"]["status"] == "OK"
    assert handler(_event("GET", "/results/email_001"), None)["statusCode"] == 200
