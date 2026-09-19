# Averis × Monash Hackathon 2026: SDOC

An AI pipeline that triages a shipping-documentation inbox and checks each draft Bill of Lading (BL) against its Shipping Instruction (SI).

**Team brief** (challenge summary, scoring, deliverables and ideas): https://claude.ai/artifact/U4DB6zMHCuCw8cUT9shVoP

## The task
For each of the 520 emails, output:
- `category`: `BL_COMPARISON` | `SI_REQUEST` | `INVOICE_QUERY` | `GENERAL` | `SPAM`
- `status`: `OK` | `MISMATCH` | `NEEDS_REVIEW`
- `defect_fields`: which of the 7 fields differ between SI and BL (`shipper`, `consignee`, `notify_party`, `port_of_loading`, `port_of_discharge`, `container_count`, `gross_weight_kg`)
- `review_reason` when `NEEDS_REVIEW`: `wrong_doc_type` | `missing_attachment` | `unreadable` | `missing_value`

The full spec is in [Provided Information/Participant Info/README.md](Provided%20Information/Participant%20Info/README.md).

## Repo layout
```
Provided Information/Participant Info/   dataset (inbox/, attachments/), loader.py,
                                         sample_submission.json, rules, rubrics, infopack
.claude/settings.json                    Claude Code plugins for the team
```

## Key dates
| | |
|---|---|
| Workshop 1 | 20 Sep, 12:00–1:00 PM |
| Workshop 2 (Averis) | 21 Sep, 7:00–8:00 PM |
| **Preliminary submission** | **22 Sep, 12:00 PM** |
| Final pitch | 26 Sep |

## Claude Code setup
Open this folder in Claude Code and accept the prompt to install the project plugins: ponytail, superpowers, security-guidance, pyright-lsp, typescript-lsp, frontend-design and playwright.

## Ground rules
- We don't have the answer key and don't use one. To validate, hand-label our own test set from the participant inbox.
- Never commit API keys. Put them in `.env`, which is gitignored.
