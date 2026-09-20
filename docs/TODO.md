# What's left

Team **Claude's Plan** · preliminary deadline **Tue 22 Sep, 12:00 PM** (aim to submit by 11:00).

## Submission checklist

| | Item | Link / where | Status |
|---|---|---|---|
| 1 | Project description (≤150 words) | in the Google Form | ready, paste it in |
| 2 | GitHub repo, public, README with setup | github.com/VRP2206/Averis_hackathon_2026 | **make it public last** |
| 3 | Live prototype link | https://shipdoc.org · https://www.shipdoc.org | live |
| 4 | Demo video ≤ 5:00, unlisted | https://youtu.be/6k3d8YqbmIU | uploaded, 4:56 |
| 5 | Slide deck / documentation link | deck kept outside the repo | **upload to Drive, "Anyone with the link → Viewer"** |
| 6 | Submit the form | https://forms.gle/nnam5eXrf5cjXdf3 | **not submitted** |

## Must fix before submitting

| | Task | Owner | Notes |
|---|---|---|---|
| A | Submit the **locally generated** `output/submission.json` (scores 1.000), not `cloud.json` (0.9869) | anyone | `sdoc run` writes it |
| B | Redeploy the Lambda image so the pinned PDF libraries take effect, then regenerate `cloud.json` | backend | Pins are in `pyproject.toml`; on the old image `email_499_BL.pdf` raised `PdfminerException` and was wrongly escalated |
| C | Reset the live data: `POST /process`, then delete the leftover `upload_*` rows and the two test overrides (`email_517`, `email_519`) from DynamoDB | backend | Impact currently shows 624 emails and 45 mismatches; should be 520 and 46 |
| D | Deck fixes: check the demo link, "WHATSDOCDOES" heading, the run-together words on the validation slide, 58 → **59 tests**, names matching the last slide | pitch | |
| E | `docs/demo_to_final.md`: what we plan to build for the final round, linked from the README | Rahul | Planned |

## Nice to have if time allows

- [ ] Restrict API CORS to the shipdoc.org / Amplify origin (currently `*`)
- [ ] Throwaway Gmail with an App Password for a live "Connect mailbox" moment
- [ ] Run the LLM path on the emails the rules are least sure about and report the difference
- [ ] Rotate the Gemini and 21st.dev keys after the event (both were pasted into chat)

## Already done

- [x] Pipeline: classify, read txt/pdf/docx/xlsx, extract 7 fields, compare, escalate. **1.000** on the 520-email set, 59 tests
- [x] AI layer: Gemini / Claude API / Bedrock for classification fallback, extraction and translation, disk-cached
- [x] Real mail in: IMAP (Gmail, Outlook, any host), single or bulk `.eml` upload, 3 one-click samples, 13 verified test emails
- [x] Web dashboard: Inbox, Compare, **Why?** audit trail, Invoices, Impact, Help, plus Privacy / Terms / Cookies / Accessibility
- [x] UI in English, Bahasa Melayu and Chinese; light and dark themes; keyboard and screen-reader support
- [x] Android app via Capacitor, prebuilt APK pointing at the live API, `scripts/demo-android.ps1`
- [x] Deployed on AWS: Lambda + Function URL, DynamoDB, Amplify Hosting, custom domain shipdoc.org
- [x] Docker: `docker compose up --build` runs API + dashboard
- [x] Docs: README, PLAN, ARCHITECTURE, HANDOFF, USER-GUIDE, DEMO-ANDROID, COMPLIANCE, AWS-DEPLOYMENT
- [x] Team details in the app footer and legal pages

## Final round (after 24 Sep, if shortlisted)

- [ ] Gmail add-on / Outlook add-in so staff run a check inside their mail client
- [ ] SQS + worker Lambda for `POST /process`
- [ ] OCR for scanned PDFs instead of escalating them
- [ ] Learn new label synonyms from reviewer corrections
- [ ] Multi-user support with sign-in
- [ ] Screen-reader pass with a real user

## Open questions for the organisers

1. Catching every defect vs never raising a false alarm: which matters more to Averis?
2. Should the tool draft the amendment email, or only flag the mismatch?
3. Will the organisers' scoring server be available, and at what URL?
