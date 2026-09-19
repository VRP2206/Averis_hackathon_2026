# Handoff: frontend and backend

The core pipeline is done and scores 1.000 on the dataset. What is left is the product around it. Below: the API you build against, what each screen needs, and what the backend has to deploy.

## Run the API locally

```bash
.venv\Scripts\activate
sdoc serve --reload            # http://127.0.0.1:8000  — interactive docs at /docs
curl -X POST http://127.0.0.1:8000/process     # processes all 520 emails (~5 s), persists to output/results.json
```

## API contract

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | `{ok, llm_provider, results}` |
| GET | `/emails` | list of `{email_id, from, subject, attachments[], result:{category,status,review_reason,defect_fields}}` — the inbox screen |
| GET | `/emails/{id}` | raw email `{email_id, from, subject, body, attachments[]}` |
| POST | `/process` | run everything → `{processed: 520}` |
| POST | `/process/{id}` | run one → full `EmailResult` |
| GET | `/results` | all `EmailResult`s |
| GET | `/results/{id}` | one `EmailResult` (404 if not processed) |
| PATCH | `/results/{id}/review` | body `{status, defect_fields, reviewer}` → updated result, `decided_by: "human"` |
| GET | `/submission` | scorer-shaped JSON for the organisers |
| GET | `/metrics` | score vs ground truth (for the Impact panel) |

`EmailResult` (what the compare screen renders):

```json
{
  "email_id": "email_025",
  "category": "BL_COMPARISON",
  "status": "MISMATCH",
  "review_reason": null,
  "has_defect": true,
  "defect_fields": ["container_count", "port_of_discharge"],
  "decided_by": "rule",
  "classification": {"category": "BL_COMPARISON", "decided_by": "rule", "confidence": 0.9, "signals": ["bl_subject", "bl_body"]},
  "comparisons": [
    {"field": "port_of_discharge", "si_value": "FREMANTLE, AUSTRALIA (AUFRE)", "bl_value": "BUSAN, SOUTH KOREA (AUFRE)",
     "si_normalised": "FREMANTLE AUSTRALIA|AUFRE", "bl_normalised": "BUSAN SOUTH KOREA|AUFRE", "match": false}
  ],
  "extractions": [
    {"doc_path": "attachments/email_025_SI.txt", "doc_type": "SI", "method": "heuristic",
     "fields": {"port_of_discharge": {"value": "FREMANTLE, AUSTRALIA (AUFRE)", "source": "Discharge Port: FREMANTLE, AUSTRALIA (AUFRE)", "confidence": 0.95, "blank": false}}}
  ],
  "notes": [],
  "draft_reply": "Subject: RE: ...\n\nPlease amend the draft BL. The following fields do not match the SI: ..."
}
```

## Frontend (three screens)

1. **Inbox** — `GET /emails`. Table: sender, subject, category chip, status chip (OK green / MISMATCH red / NEEDS_REVIEW amber), defect count. Filters by category and status. A "Process inbox" button → `POST /process`.
2. **Compare** — `GET /results/{id}` + `GET /emails/{id}`. Left: email body. Centre: 7-row table, SI value vs BL value, mismatched rows highlighted, hover shows `source` line (the evidence). For NEEDS_REVIEW show the reason and `notes`. Buttons: **Approve** (`PATCH` with current status), **Override** (pick status + fields), **Copy draft reply** (`draft_reply`).
3. **Impact** — `GET /metrics` + `GET /results`. Tiles: emails auto-handled vs escalated, mismatches found, accuracy vs ground truth, `decided_by` split (rule / llm / human).

Keep it a static build (React/Vite or Next static export) so it can sit on Amplify Hosting; point it at the API base URL via an env var. CORS is already open on the API.

## Backend (cloud)

Target per `PLAN.md`: AWS Free Plan, $0 out of pocket.

1. **Lambda** for the API. Wrap `sdoc.api:app` with [Mangum](https://mangum.io) (`handler = Mangum(app)`), package with the `Provided Information/Participant Info` data or read it from **S3** (set `SDOC_DATA_DIR` to a local copy synced at cold start, or implement an `S3Inbox(InboxRepository)`). Expose with a Lambda Function URL.
2. **DynamoDB** store: implement `ResultStore` (`put`, `get`, `all`) in `sdoc/store.py` — table key `email_id`, item = `EmailResult.model_dump(mode="json")`. Swap it in `api.py`.
3. **Bedrock** (optional, adds the AI story): give the Lambda role `bedrock:InvokeModel`, set `SDOC_LLM_PROVIDER=bedrock`. No API key needed. Confirm Haiku 4.5 access in the region first.
4. **Budget**: AWS Budget alert at $10; never create EC2/RDS/NAT beyond the credit tasks.
5. Later (finals): **SQS + worker Lambda** so `POST /process` enqueues 520 messages instead of running in-request.

## Definition of done for the prelim (22 Sep 12:00)

- [ ] Public API URL responding on `/health` and `/emails`
- [ ] Dashboard deployed, Inbox + Compare screens working against it
- [ ] `output/submission.json` attached to the form
- [ ] README setup instructions verified on a clean machine
- [ ] Slides (architecture diagram from `docs/ARCHITECTURE.md`, results table from README, challenges, roadmap)
- [ ] ≤5-min video: intro → problem → stack → live demo (inbox → mismatch → draft reply → NEEDS_REVIEW case) → metrics
