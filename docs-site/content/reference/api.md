# API reference

The dashboard, the Android app and the command line all use one HTTP API. You can call it from your own code too.

| | |
|---|---|
| Base URL (live demo) | `https://j2mwf375qvy2xpf3xdqs4wai6y0rvrqd.lambda-url.ap-southeast-1.on.aws` |
| Base URL (local) | `http://127.0.0.1:8000` (start it with `sdoc serve`) |
| Interactive docs | `/docs` (Swagger UI) and `/openapi.json` |
| Format | JSON over HTTPS, `application/json` (uploads use `multipart/form-data`) |
| Authentication | None. It is a prototype API with open CORS. Do not send real customer data to the public demo |

Errors come back as `{"detail": "message"}` with a matching HTTP status (`400`, `404`, `422`).

## Endpoints

| Method | Path | What it does |
|---|---|---|
| `GET` | `/health` | Is the API up, which AI provider is configured, how many results are stored |
| `GET` | `/emails` | Inbox summary: id, sender, subject, source, attachments, and a short result |
| `GET` | `/emails/{email_id}` | One email in full, including its body |
| `POST` | `/process` | Run the pipeline over the whole inbox |
| `POST` | `/process/{email_id}` | Run one email and return its result |
| `GET` | `/results` | Every stored result, in full detail |
| `GET` | `/results/{email_id}` | One result |
| `PATCH` | `/results/{email_id}/review` | A reviewer overrides a result |
| `GET` | `/submission` | Results in the scorer's shape |
| `GET` | `/metrics` | Score against the organisers' scoring data, if that data is present |
| `GET` | `/invoices` | Invoice numbers, order references and amounts from billing emails |
| `POST` | `/translate/{email_id}` | Detect an email's language and translate it |
| `POST` | `/upload` | Upload one `.eml`; it is processed at once |
| `POST` | `/mailbox/connect` | Import the latest messages from an IMAP mailbox and process them |
| `POST` | `/mailbox/refresh` | Fetch new mail from the connected mailbox |
| `GET` | `/mailbox` | Is a mailbox connected |
| `DELETE` | `/mailbox` | Disconnect the mailbox |

## Health

```bash
curl https://<base-url>/health
```

```json
{ "ok": true, "llm_provider": "none", "results": 520 }
```

`llm_provider` is `none`, `gemini`, `anthropic` or `bedrock`. It only reports the setting. To see that AI is really answering, call `/translate`.

## Emails

`GET /emails` returns one entry per email. `source` is `dataset`, `upload` or `mailbox`.

```json
{
  "email_id": "email_004",
  "from": "docs@example-forwarder.test",
  "subject": "REQUEST BL DRAFT _ PO 26067",
  "source": "dataset",
  "attachments": ["attachments/email_004_SI.txt", "attachments/email_004_BL.txt"],
  "result": {
    "category": "BL_COMPARISON",
    "status": "MISMATCH",
    "review_reason": null,
    "defect_fields": ["consignee", "notify_party"]
  }
}
```

`result` is a placeholder (`GENERAL`, `OK`) until the email has been processed.

`GET /emails/{email_id}` adds the message text:

```json
{ "email_id": "email_004", "from": "docs@example-forwarder.test", "subject": "REQUEST BL DRAFT _ PO 26067",
  "body": "Please check the attached SI and draft BL...", "attachments": ["..."] }
```

## Processing

```bash
curl -X POST "https://<base-url>/process"
# {"processed": 520}

curl -X POST "https://<base-url>/process/email_004"
# a full result, see below
```

`POST /process` accepts `?workers=8` (threads). It recomputes everything and stores the results.

## Results

`GET /results/{email_id}` returns everything shipdoc knows about one email. The values below are illustrative.

```json
{
  "email_id": "email_004",
  "category": "BL_COMPARISON",
  "status": "MISMATCH",
  "review_reason": null,
  "has_defect": true,
  "defect_fields": ["consignee", "notify_party"],
  "decided_by": "rule",
  "classification": {
    "category": "BL_COMPARISON",
    "decided_by": "rule",
    "confidence": 1.0,
    "signals": ["bl_subject", "bl_body", "si_bl_attachments"],
    "evidence": ["+4 BL_COMPARISON: subject asks about a BL"]
  },
  "comparisons": [
    { "field": "consignee",
      "si_value": "ACME TRADING FZ-LLC", "bl_value": "NORTHWIND IMPORTS LTD",
      "si_normalised": "ACME TRADING FZ LLC", "bl_normalised": "NORTHWIND IMPORTS LTD",
      "match": false }
  ],
  "extractions": [
    { "doc_path": "attachments/email_004_SI.txt", "doc_type": "SI",
      "fields": { "consignee": { "field": "consignee", "value": "ACME TRADING FZ-LLC",
                                 "source": "Consignee: ACME TRADING FZ-LLC", "confidence": 0.95, "blank": false } } }
  ],
  "notes": [],
  "draft_reply": "Dear ..., the draft BL differs from the SI in: consignee, notify party ...",
  "trace": [ { "stage": "classify", "title": "...", "outcome": "pass", "detail": "...", "evidence": ["..."] } ]
}
```

| Field | Meaning |
|---|---|
| `category`, `status`, `review_reason` | See [Categories, statuses and reasons](/concepts/statuses) |
| `has_defect`, `defect_fields` | True and the field names when the BL differs from the SI |
| `decided_by` | `rule`, `llm` or `human` |
| `comparisons` | One entry per field: the raw and the normalised values and whether they match |
| `extractions` | What was read from each attachment, and the source line for every value |
| `draft_reply` | A drafted amendment email (mismatch) or resend request (needs review) |
| `trace` | The steps shown on the **Why?** page, in order |

## Reviewer override

```bash
curl -X PATCH "https://<base-url>/results/email_004/review" \
  -H "Content-Type: application/json" \
  -d '{"status": "OK", "defect_fields": [], "reviewer": "Ana"}'
```

`status` is `OK`, `MISMATCH` or `NEEDS_REVIEW`. The result is updated, its `decided_by` becomes `human`, and `overridden by Ana` is added to `notes`. `404` if the email has not been processed yet.

## Scorer format

`GET /submission` returns one small object per email:

```json
{ "email_004": { "category": "BL_COMPARISON", "status": "MISMATCH", "review_reason": null,
                 "has_defect": true, "defect_fields": ["consignee", "notify_party"], "decided_by": "rule" } }
```

`GET /metrics` scores that against the organisers' scoring data. It answers `404` when that data is not on the server, which is the case on the public deployment.

## Invoices

```json
[ { "email_id": "email_002", "sender": "billing@example.test", "subject": "INVOICE QUERY ...",
    "topic": "cancellation", "invoice_numbers": ["5250075931"], "order_refs": [], "amounts": ["USD 1,250.00"],
    "evidence": ["..."] } ]
```

## Translate

```bash
curl -X POST "https://<base-url>/translate/email_013" \
  -H "Content-Type: application/json" -d '{"target": "en"}'
```

```json
{ "email_id": "email_013", "source_language": "ms", "target_language": "en", "translated": true,
  "text": "Please check the attached documents...", "note": "", "llm_provider": "bedrock" }
```

`target` is an ISO 639-1 code. Without an AI provider, shipdoc can still detect the language, but `translated` is `false` and `note` says a provider is needed.

## Upload one email

```bash
curl -X POST "https://<base-url>/upload" -F "file=@01-mismatch-port-and-containers.eml;type=message/rfc822"
```

The response is the full result for that email. Its id looks like `upload_ab12cd34`.

## Connect a mailbox

```bash
curl -X POST "https://<base-url>/mailbox/connect" -H "Content-Type: application/json" \
  -d '{"host": "imap.gmail.com", "user": "me@gmail.com", "password": "<app password>", "folder": "INBOX", "limit": 50}'
```

```json
{ "connected": true, "host": "imap.gmail.com", "user": "me@gmail.com", "folder": "INBOX",
  "messages_in_folder": 132, "fetched": 50, "processed": 50 }
```

Access is read-only. Use an App Password on a test mailbox (see the [user guide](/guide/user-guide)). A failed connection answers `400` with `could not connect: ...`.

::: warning The public demo shares one workspace
On the public deployment every visitor sees the same inbox, including anything uploaded or imported. Do not send real customer data there. Run your own copy ([locally](/deploy/run-locally) or [on AWS](/deploy/aws)) for real mail.
:::
