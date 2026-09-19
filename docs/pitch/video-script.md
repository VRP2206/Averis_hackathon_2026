# Demo video: script and shot list (target 4:30, hard cap 5:00)

Every 30 s over 5:00 costs a mark, so rehearse once with a timer. Record at 1080p with OBS (free): one scene = browser window + mic. Turn off notifications. Zoom the browser to 125 % so text is readable.

| Time | Shot | Say |
|---|---|---|
| 0:00–0:20 | Title slide | "Hi, we're **[Team]**: [names]. This is **SDOC**, a shipping document check for the Averis × Monash Hackathon." |
| 0:20–1:00 | Slide 2, then one real email + its two attachments open side by side | "Averis's documentation team gets hundreds of emails a day. Some ask them to confirm a carrier's draft Bill of Lading against the Shipping Instruction. Today that's a person comparing seven fields by eye, across files where the same field has different names. *Port of Discharge* here is *POD* there. A wrong port on a released BL means fees and delays." |
| 1:00–1:30 | Slide "How" | "Our rule: AI reads, code decides. Rules and label matching handle the regular cases free. Claude is the fallback for messy emails and missed fields. The comparison itself is plain, tested code, so it can't hallucinate." |
| 1:30–1:45 | Slide "Architecture" | "Python pipeline, FastAPI, a React dashboard that ships as a website and an Android app, all on the AWS free plan: Lambda, DynamoDB, Bedrock." |
| 1:45–3:45 | **Live demo** (browser) | see below |
| 3:45–4:15 | Slide "Results" | "On the 520-email dataset: every email classified correctly, all 46 defective BLs caught with the exact wrong fields, zero false alarms, all 20 edge cases escalated with the right reason. Final score 1.0 on the organisers' formula, reproducible with one command. The dataset is synthetic, so the LLM fallback is what carries this to a real inbox." |
| 4:15–4:30 | Slide "Roadmap" + Thank you | "Next: a live mailbox, OCR for scans, and learning label synonyms from reviewer corrections. Thank you." |

## Live demo steps (2 minutes, practise the clicks)

1. **Inbox** (0:15): "520 emails, already triaged." Click the status filter → MISMATCH. "Twenty-three need an amendment."
2. **Compare** (0:35): open `email_025`. "SI on the left, BL on the right. Two fields are flagged: container count, 3 versus 4, and port of discharge: the name changed but the LOCODE didn't. Hover shows the exact line each value came from." Click **Copy draft reply**: "The amendment email is drafted; a person sends it."
3. **NEEDS_REVIEW** (0:30): open `email_501`. "Here the second file is a Commercial Invoice, not a BL. We don't guess; we escalate with the reason." Open `email_512`: "Scanned image, no text layer: unreadable."
4. **Override** (0:20): on `email_001` click **Override result**, change nothing material, type a reviewer name, save. "Every human decision is recorded: who, what, when."
5. **Impact** (0:20): open the Impact tab. "These numbers are computed live from the API against the answer key, not typed in."

## Do / don't

- Do say "on the synthetic hackathon dataset" once. Don't claim production accuracy.
- Don't show Averis or APRIL logos; the app is a student prototype.
- Keep the terminal out of the video except for one `sdoc run` (optional, 10 s) if time allows.
- Upload as **Unlisted** on YouTube; check it plays without login.
