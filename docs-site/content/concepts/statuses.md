# Categories, statuses and reasons

Every email gets a **category**. Emails that ask for a BL check also get a **status**, and a **reason** when a person has to look.

## Categories

| Category | What it is |
|---|---|
| `BL_COMPARISON` | Someone wants a draft Bill of Lading checked against the Shipping Instruction |
| `SI_REQUEST` | A request for the Shipping Instruction |
| `INVOICE_QUERY` | A billing question. Invoice numbers, order references and amounts are pulled out for the Invoices page |
| `GENERAL` | Everything else, including automated notices that merely mention billing |
| `SPAM` | Phishing and junk |

Classification is rules first. The rules score weighted signals in the subject and body, and only when they are not confident (below 0.5) is an AI model asked. The **Why?** page lists every signal and its points.

## Statuses

| Status | Meaning | `has_defect` |
|---|---|---|
| `OK` | The documents match, or there was nothing to compare | `false` |
| `MISMATCH` | At least one of the seven fields differs. `defect_fields` names them | `true` |
| `NEEDS_REVIEW` | shipdoc will not guess. `review_reason` says why | `false` |

## Reasons for review

| `review_reason` | When it happens |
|---|---|
| `missing_attachment` | The email says documents are attached (or still missing) but fewer than two files arrived |
| `unreadable` | An attachment is empty, corrupt, or has no text layer (a scan). shipdoc does not run OCR |
| `wrong_doc_type` | The email does not carry exactly one SI and one BL, judged by the content of each file, not its name. A file called `_BL` that is really a commercial invoice is caught here |
| `missing_value` | One of the seven fields is blank or holds a placeholder such as `TBA`, `???` or `____` |

A request to *send* the draft BL, with no files, is not an error: it is `OK`, because there is nothing to compare.

## The seven fields

| Field | Compared as |
|---|---|
| `shipper` | Company name, ignoring case, punctuation and legal suffixes |
| `consignee` | Company name (the SI calls it *Consignee*, a BL may say *To the Order of*) |
| `notify_party` | Company name |
| `port_of_loading` | Port name **and** UN/LOCODE, e.g. `NANTONG, CHINA (CNNTG)` |
| `port_of_discharge` | Port name and UN/LOCODE (*POD*, *Discharge Port* mean the same) |
| `container_count` | The number, e.g. `6` from `6 x 40'HC` |
| `gross_weight_kg` | The number in kilograms, e.g. `131058` from `131,058 KG` |

Labels vary between an SI and a BL, so fields are matched by meaning, not by position. The comparison itself is plain code and never uses AI.

## Who decided

Every result carries `decided_by`:

| Value | Meaning |
|---|---|
| `rule` | Deterministic rules decided |
| `llm` | The rules were not confident and an AI model classified the email |
| `human` | A reviewer overrode the result |

Overrides are recorded with the reviewer's name in the result's `notes`.

## Next

See [How shipdoc decides](/concepts/how-it-works) for the step-by-step flow, or the [API reference](/reference/api) for the result format.
