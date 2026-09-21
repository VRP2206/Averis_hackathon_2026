# From the demo to the final round

Where shipdoc stands after the preliminary round, and what we intend to build for the final on 26 September. The final submission must be an extension and improvement of this entry, so nothing here restarts the work: every item builds on a seam that already exists in the code.

## Where we are

| | |
|---|---|
| Pipeline | Classify, read, extract, compare, escalate. **1.000** on the organisers' 520-email dataset: 46/46 defects caught with the exact fields, 0 false alarms, 20/20 escalations with the right reason |
| Quality | 59 automated tests; every bug we found became one |
| Email in | The dataset, a real mailbox over IMAP, or an uploaded `.eml` |
| Product | Web dashboard and Android app on one codebase; Inbox, Compare, Why?, Invoices, Impact, Help |
| Cloud | AWS Lambda + Function URL, DynamoDB, Amplify Hosting, ap-southeast-1, custom domain |
| AI | Gemini live; the same interface runs Claude API or Bedrock |

Known limits we are not hiding: image-only PDFs are escalated rather than read; the dataset is synthetic, so the rules do more of the work than they would on real mail; there is no sign-in, so every viewer sees the same queue; `POST /process` runs in one request rather than a queue.

## What we will build

Ordered by what the final rubric rewards most. Each item names the seam it plugs into, so the work is an extension rather than a rewrite.

### 1. Run the check from inside the mail client (Gmail add-on)

**Why:** the judges' criterion is end-to-end functionality, and the honest gap today is that a documentation officer still has to leave Outlook or Gmail and open our site. An add-on removes that step: open the email, press Check, see the seven-field comparison and the drafted amendment in the side panel.

**How:** a Google Workspace add-on (Apps Script card UI) that posts the message and its attachments to the existing `POST /upload` endpoint and renders the `EmailResult` we already return. No pipeline change.

**Risk:** Workspace add-ons need a Cloud project and, for anything beyond our own test accounts, OAuth verification. For the pitch we will demo it on our own Workspace account and say so plainly.

### 2. Read scanned documents instead of escalating them

**Why:** `unreadable` is our largest remaining escalation reason. Every scan we can read is an email a person no longer has to open.

**How:** an `OcrPdfReader` registered in `ReaderRegistry` (one class, one line to register). It runs only when a PDF has no text layer, so nothing else slows down. Amazon Textract fits the AWS story; Tesseract keeps it free. We will measure both on the 20 edge cases and report which we shipped and why.

**Risk:** OCR text is noisy. The field extractor already carries a confidence per field, so a low-confidence OCR read stays an escalation instead of becoming a wrong answer.

### 3. Sign-in and a real reviewer queue

**Why:** the override audit trail records a name typed into a box. That is fine for a demo and not fine for an operations tool.

**How:** Amazon Cognito in front of the API, with the reviewer identity taken from the token rather than a text field. Results gain an assignee, so the inbox becomes "my queue" and "everyone's queue". `ResultStore` already abstracts storage, so this is a schema addition rather than surgery.

### 4. Scale the batch path

**Why:** architecture and scalability is 15 marks, and today `POST /process` does 520 emails inside one request. It works, but it is the wrong shape for a real inbox.

**How:** the endpoint enqueues one SQS message per email; a worker Lambda consumes them and writes to DynamoDB. The pipeline is already stateless per email, so the code moves rather than changes. We will show a run of several thousand emails to prove it.

### 5. Learn from corrections

**Why:** it turns the human-in-the-loop from a safety net into an advantage, and it is the most differentiated thing we can demo.

**How:** when a reviewer overrides a field, store the label the document used next to the field it meant. Those pairs extend `LABEL_SYNONYMS` at load time, so the next document with that label is read correctly. Every learned pair is visible and removable: no silent model drift.

### 6. Measure what it saves

**Why:** impact is 10 marks and our current figure ("about 4 minutes per manual check") is an assumption we label as one.

**How:** time the reviewer flow with two or three people checking the same emails by hand, then with shipdoc, and report the real difference alongside the caveat that it is a small sample.

## Plan for the final week

| When | Work |
|---|---|
| Wed 24 Sep | OCR reader and its measurements; Cognito sign-in behind a flag |
| Thu 25 Sep | Gmail add-on against the live API; SQS and the worker Lambda |
| Fri 26 Sep, morning | Learned synonyms, the timing study, rehearse the pitch |
| Fri 26 Sep | Final pitch |

If we run short, the order above is the order we drop from the bottom. The Gmail add-on and OCR are the two that change what the product can do; the rest strengthen the story.

## What stays the same

The rule that makes this work does not change: **AI reads, code decides.** Extraction, classification and OCR may all be probabilistic; the comparison that produces a mismatch stays deterministic and unit-tested, and anything uncertain still goes to a person with the reason. Everything above is added inside that shape.
