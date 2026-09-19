---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-family: "Segoe UI", system-ui, sans-serif; padding: 56px; }
  h1 { font-size: 44px; color: #0B3D5C; }
  h2 { font-size: 34px; color: #0B3D5C; }
  table { font-size: 22px; }
  .small { font-size: 20px; color: #444; }
  .big { font-size: 64px; font-weight: 700; color: #0B5E8E; }
---

# SDOC — Shipping Document Check
## Averis × Monash Hackathon 2026

**Team Claude's Plan** · [Member 1] · [Member 2] · [Member 3]

<span class="small">AI-assisted triage of a shipping-documentation inbox, with a deterministic SI-vs-BL check and a human in the loop.</span>

---

## The problem

Averis's documentation team receives hundreds of emails a day. Mixed in are requests to confirm a carrier's **draft Bill of Lading** against the **Shipping Instruction**.

- Today a person opens both files and compares 7 fields by eye
- The same field has different labels on each document: *POD* vs *Discharge Port*, *To the Order of* vs *Consignee*
- One wrong port or container count on a released BL means amendment fees, delays and detention charges

**Who it affects:** documentation staff, customers waiting on cargo, finance absorbing the fees.

---

## What we built

A pipeline plus a reviewer dashboard (web + Android) that reads a **real mailbox over IMAP** (Gmail, Outlook) or an uploaded `.eml`, as well as the hackathon dataset:

1. **Classify** every email: BL comparison, SI request, invoice query, general, spam
2. **Read** the attachments: txt, PDF, Word, Excel
3. **Extract** the 7 fields, whatever they are labelled
4. **Compare** and name the exact fields that differ
5. **Escalate** anything it cannot decide, with the reason
6. **Draft** the amendment email for a person to send

---

## Results on the 520-email dataset

<span class="big">1.000</span> organisers' final score (0.30 classify + 0.20 defect-F1 + 0.50 end-to-end)

| Metric | Result |
|---|---|
| Classification accuracy, 5 categories | 100 % |
| Defective BLs caught with the exact wrong fields | 46 / 46 |
| False alarms on clean pairs | 0 |
| Edge cases escalated with the right reason | 20 / 20 |
| Tests | 49 passing |

<span class="small">Dataset is synthetic, provided by the organisers. Numbers are reproducible with `sdoc run`.</span>

---

## How: AI reads, code decides

```
email -> classify -> gate -> read SI + BL -> extract 7 fields -> compare -> OK / MISMATCH
          rules first,   NEEDS_REVIEW:        heuristics first,    deterministic,
          LLM fallback   missing attachment,  LLM fills gaps        unit-tested
                         unreadable, wrong
                         doc type, blank value
```

- Rules and label-synonym matching handle the regular cases for free
- An LLM (Gemini, Claude API or Amazon Bedrock) is a drop-in fallback in two places, never in the comparison
- The comparison cannot hallucinate: ports match on name **and** UN/LOCODE, weights in kg, parties normalised

---

## Architecture

- **Pipeline** (Python): one class per stage behind an abstract base; `build_pipeline()` injects them
- **API** (FastAPI): inbox, results with evidence, reviewer override, live metrics
- **Dashboard** (React + Capacitor): Inbox, Compare, Invoices, Impact, translation; same code ships as a web app and an Android APK
- **Cloud** (AWS Free Plan, $0): Lambda + Function URL, DynamoDB, S3, Amplify Hosting, Bedrock

Stateless per email → maps straight onto SQS + Lambda workers for scale.

---

## Validation: how we found our own bugs

We measured against the answer key after every change.

| Iteration | Score | What was wrong |
|---|---|---|
| First run | 0.76 | "BILL OF LADING INSTRUCTION" typed as a BL; ports compared by code only; bot notices with "Billing" in the subject |
| Second | 0.97 | PDF labels physically overlapping values: `ConsCigEnReIEeX` |
| Third | 1.00 | Split PDF lines by font weight |

Every fix became a unit test.

---

## Never guesses

| Situation | What the tool does |
|---|---|
| Body says "attached" but nothing is | NEEDS_REVIEW · missing_attachment |
| Scanned image-only PDF, empty or corrupt file | NEEDS_REVIEW · unreadable |
| A Commercial Invoice sent as the "BL" | NEEDS_REVIEW · wrong_doc_type |
| SI field left as `???` or `TBA` | NEEDS_REVIEW · missing_value |
| "Please send the draft BL" (nothing to compare yet) | OK, no comparison |

A blank is uncertainty, not a discrepancy. The reviewer sees the reason and the evidence line for every value.

---

## Live demo

1. Inbox: 520 emails triaged, filter to MISMATCH
2. Open one: SI and BL side by side, two fields highlighted, hover shows the source line
3. Copy the drafted amendment email
4. Open a NEEDS_REVIEW case: wrong document type, with the reason
5. Override a result as a reviewer; audit trail records who
6. Impact panel: live metrics from `/metrics`

---

## Impact and roadmap

**Now:** minutes per email → seconds; zero false alarms means reviewers trust the queue.

**Next (finals):** Gmail add-on / Outlook add-in · SQS workers · OCR for scanned PDFs · learn new label synonyms from reviewer corrections · Outlook add-in.

**Measures of success:** end-to-end catch rate, false-alarm rate, % auto-handled vs escalated, reviewer minutes saved.

---

## Challenges

- Same information, different labels and file formats
- PDF text layers that interleave label and value glyphs
- Deciding *when not to decide*: distinguishing "send me the draft" from "the attachment was dropped"
- Keeping the cloud bill at $0

---

# Thank you

Repo: github.com/VRP2206/Averis_hackathon_2026
Demo: [URL]

<span class="small">Student prototype for the Averis × Monash Hackathon 2026. Not an Averis product.</span>
