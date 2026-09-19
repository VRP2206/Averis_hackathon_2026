# SDOC Build Plan

As of 20 Sep 2026. Tick items off in the backlog as we go.

## TL;DR

We build a **web app** for Averis's shipping-document team. It reads the inbox, sorts every email, checks each draft Bill of Lading (BL) against its Shipping Instruction (SI), and shows a reviewer exactly which fields are wrong.

- **What it is:** a deployed website (reviewer dashboard) on top of a cloud API that runs the AI pipeline.
- **Where AI goes:** reading messy emails and documents. **Where plain code goes:** the actual field comparison, so it's exact and testable.
- **The hook:** it never guesses. Unclear cases go to a human with a reason, and every mismatch comes with a drafted amendment email.
- **Cloud:** Google Cloud Run + Cloud Storage + Firestore, with the Claude API for the AI.
- **Deadline:** preliminary submission Tue 22 Sep, 12:00 PM.

## Non-negotiables

Whatever idea we pick, it must do all of these. Missing any one costs marks or gets us disqualified.

| Must have | Why | Source |
| --- | --- | --- |
| Classify all 520 emails into the 5 categories | 30% of the automated score | Scorer |
| Extract the 7 fields from SI and BL in txt, PDF, DOCX and XLSX | Needed for any comparison | Dataset README |
| Name the **exact** set of mismatched fields | 50% of the automated score (end-to-end) | Scorer |
| Return NEEDS_REVIEW with a reason instead of guessing | Reliability axis; false alarms hurt | Scorer, README |
| Output a `submission.json` in the sample format | How the scorer reads us | Participant README |
| AI as a key component | Required | Rules |
| Runs on cloud infrastructure | "Significantly reduced scores" without it | Rules |
| Public live demo link that stays up | Mandatory deliverable | Rules |
| Works end-to-end, not mock-ups | 25 of 100 judge marks | Rubric |
| Public GitHub repo with setup README | Mandatory deliverable | Rules |
| Demo video of 5 minutes or less | −1 mark per 30 s over | Rules |
| Slides: architecture, implementation, challenges, roadmap | Mandatory deliverable | Rules |
| Our own measured results (hand-labelled test set) | "Validation" (15) and "Impact: metrics" in the video | Rubric, Rules |

## App, website or something else?

**Build a web app.** Judges need a public link they can open, and Averis's document staff work at desks in Outlook, not on phones.

| Option | Verdict | Reason |
| --- | --- | --- |
| Web app (dashboard + API) | **Build this** | Public link for judges, works on any laptop, fastest to build and demo |
| Mobile app | Skip | Nobody checks a Bill of Lading on a phone; app-store setup wastes days |
| Script / CLI only | Skip as the product | A script-only entry scores poorly on UX; keep the script for making `submission.json` |
| Outlook add-in | Roadmap slide | Where the users actually work; good "future potential" story for the finals |
| Chatbot | Skip | The job is a queue of checks, not a conversation |

The web app has three screens:

1. **Inbox:** every email with its category and a status chip (OK, MISMATCH, NEEDS_REVIEW).
2. **Compare view:** SI and BL side by side, wrong fields highlighted, the source line for each value, and Approve / Override buttons.
3. **Draft reply:** the amendment email to the carrier, ready to edit and send.

## How we use AI

AI reads; code decides. The LLM turns messy emails and documents into clean structured data, and plain code does the comparison, so the result is exact and we can test it.

```mermaid
flowchart LR
  A[Email] --> B{Subject rule<br/>matches?}
  B -- yes --> C[Category]
  B -- no --> D[LLM classify]
  D --> C
  C -- BL_COMPARISON --> E[Gatekeeper checks]
  E -- problem --> R[NEEDS_REVIEW<br/>+ reason]
  E -- ok --> F[LLM extract<br/>7 fields]
  F --> G[Code: normalise<br/>+ compare]
  G --> H[OK / MISMATCH]
  H -- MISMATCH --> I[LLM drafts<br/>amendment email]
```

| Step | Who does it | How |
| --- | --- | --- |
| Classify | Rules first, AI fallback | Regex on subject codes (`TO CONFIRM DOCS`, `SI -`, `CANCEL INVOICE`). Only unmatched emails go to a small, cheap model (Claude Haiku 4.5), with signatures and forwarded threads stripped. Log `decided_by: rule` or `llm`. |
| Read files | Code | `pdfplumber`, `python-docx`, `openpyxl`. No text layer, 0-byte or corrupt file → `unreadable`. |
| Gatekeeper | Code + AI | Code: no BL attached, placeholders (`???`, `TBA`, `____`). AI: "is this second file really a BL, or an invoice / packing list?" |
| Extract | AI | Claude Sonnet 5 with a strict JSON schema: for each of the 7 fields, the value, the exact source line, and a confidence. This handles the label synonyms (`POD` = `Discharge Port`). |
| Compare | Code | Ports by UN/LOCODE (`MYPKG`), containers to a count, weights to whole kg, company names case- and punctuation-insensitive. Low extraction confidence → NEEDS_REVIEW. |
| Draft reply | AI | For each MISMATCH, write the amendment request to the carrier. A person approves before sending. |

**Why this split wins marks:** the rubric rewards "technology integration" and "robustness". An LLM deciding matches can hallucinate. Code deciding matches is testable, and we can show the tests.

## Cloud architecture

Use Google Cloud (to confirm: switch to AWS if a teammate already knows it). Cloud Run scales to zero, so it costs almost nothing between demos, and new accounts get free trial credit.

```mermaid
flowchart LR
  U[Reviewer<br/>browser] --> W[Web app<br/>Cloud Run]
  W --> API[Pipeline API<br/>FastAPI on Cloud Run]
  API --> S[(Cloud Storage<br/>attachments)]
  API --> DB[(Firestore<br/>results + audit log)]
  API --> L[Claude API]
  API --> Q[Pub/Sub queue]
  Q --> WK[Worker<br/>Cloud Run job]
  WK --> DB
```

| Piece | Service | Job |
| --- | --- | --- |
| Web app | Cloud Run (or Firebase Hosting) | Inbox, compare view, draft reply |
| Pipeline API | Cloud Run, Python FastAPI | Classify, extract, compare; serves results |
| File store | Cloud Storage | Original emails and attachments |
| Database | Firestore | Results per email, reviewer decisions, audit trail |
| Queue + worker | Pub/Sub + Cloud Run job | Processes a batch of 520 emails in parallel; our scaling story |
| Secrets | Secret Manager | Claude API key, never in the repo |
| AI | Claude API (Haiku 4.5 + Sonnet 5) | Classification fallback, extraction, doc-type check, drafted replies |

For the prelim, the queue + worker can be one endpoint that processes emails in a loop. Add Pub/Sub for the finals, when "Architecture & Scalability" is judged. AWS works equally well (App Runner or Lambda, S3, DynamoDB, SQS).

## Product backlog

Everything marked Must is needed for the 22 Sep preliminary submission. Should items are what make us stand out; Finals items wait until after 24 Sep.

| Done | Epic | Priority | Earns marks on |
| --- | --- | --- | --- |
| [ ] | Hand-label a 40-email test set (mix of categories and formats) | Must | Validation, impact metrics |
| [ ] | Load emails; subject-code rules for classification | Must | Stage 1 score (30%) |
| [ ] | LLM fallback classifier for emails rules can't place | Must | Stage 1, AI requirement |
| [ ] | File readers: txt, PDF, DOCX, XLSX | Must | Working prototype |
| [ ] | LLM extraction of the 7 fields (JSON schema, source line, confidence) | Must | Tech integration |
| [ ] | Normalise + compare fields in code | Must | End-to-end (50%) |
| [ ] | Gatekeeper: 4 NEEDS_REVIEW reasons | Must | Reliability, robustness |
| [ ] | Generate submission.json; score against our test set | Must | Validation |
| [ ] | Deploy API to Cloud Run with Secret Manager | Must | Cloud requirement |
| [ ] | Web dashboard: inbox + side-by-side compare view | Must | Working prototype, UX |
| [ ] | Submission pack: README, slides, 5-min video, form | Must | Mandatory |
| [ ] | Drafted amendment email for each MISMATCH | Should | Differentiation, user value |
| [ ] | Audit trail: decided_by, source lines, reviewer decisions | Should | Engineering quality |
| [ ] | Unit tests for normaliser and comparer | Should | Engineering quality |
| [ ] | Impact panel: accuracy, false alarms, minutes saved | Should | Impact |
| [ ] | Live Gmail/Outlook mailbox connection | Finals | End-to-end (finals) |
| [ ] | Pub/Sub worker for parallel batch processing | Finals | Architecture & scalability |
| [ ] | Learn from reviewer corrections (new label synonyms) | Finals | Future potential |
| [ ] | Outlook add-in | Could | Roadmap slide |

## Who does what, and when

Split into four roles so nobody waits on anyone. With fewer than four people, one person takes two roles, and the pitch role merges into whoever finishes first.

| Role | Owns | First deliverable |
| --- | --- | --- |
| Pipeline | Classify, extract, compare, gatekeeper | `submission.json` for all 520 emails |
| Backend + cloud | FastAPI, Cloud Run, Firestore, secrets | Public API URL |
| Frontend | Inbox, compare view, draft reply | Dashboard reading the API |
| Quality + pitch | Test set, scoring script, slides, video | 40 labelled emails, then our accuracy numbers |

| When | Goal |
| --- | --- |
| Sun 20 Sep (today) | Test set labelled; rules classifier + file readers + extraction running locally. Workshop 1 at 12 PM. |
| Mon 21 Sep | Compare + gatekeeper done; API deployed; dashboard shows real results. Workshop 2 (Averis) at 7 PM: ask what matters most. |
| Tue 22 Sep, by 10 AM | Drafted replies, measured results, README, slides, video recorded. |
| Tue 22 Sep, 12:00 PM | **Submit.** Aim to send the form by 11:00 AM. |

**Open questions**
- Which cloud account and Claude API key do we use, and who pays? Settle it today, because deployment blocks the live demo link.
- Google Cloud or AWS?
