# What's left (as of 20 Sep 2026, evening)

Deadline: **Tue 22 Sep, 12:00 PM**. Aim to submit the form by 11:00. Team: **Claude's Plan**.

## Done

- [x] Core pipeline: classify, read txt/pdf/docx/xlsx, extract 7 fields, compare, escalate; **1.000** on the 520-email set; 51 tests
- [x] LLM cascade for classification, extraction and translation (Gemini / Claude API / Bedrock), disk-cached
- [x] Real mail in: IMAP connector (Gmail, Outlook, any) and `.eml` upload; three one-click sample emails
- [x] API (`sdoc serve`): inbox, results with evidence, override with audit trail, invoices, translate, mailbox, upload, metrics
- [x] Web dashboard: Inbox (clickable KPI tiles, filters, source, sort), Compare, Invoices, Impact, Help; Privacy / Terms / Cookies / Accessibility
- [x] Redesign: Gmail-white, Google colours, big Fredoka type with sheen, hover lift, animated blobs, self-hosted fonts, hero/logo art
- [x] Android: Capacitor project, runtime API-URL setting, prebuilt `apk/sdoc-debug.apk`, `scripts/demo-android.ps1`, `docs/DEMO-ANDROID.md`
- [x] Docs: README, PLAN, ARCHITECTURE, HANDOFF, COMPLIANCE, USER-GUIDE, pitch deck (md + pdf), video script, coverage page

## Must do before submitting

| # | Task | Owner | How / notes |
|---|---|---|---|
| [x] | Create the team AWS account; do the 5 credit tasks; set a $10 budget alert | backend | Blocks the public demo link. `PLAN.md` -> Budget rules |
| [x] | Deploy the API (Lambda + Mangum + Function URL); data bundled or in S3 | backend | `docs/HANDOFF.md` -> Backend. Set `SDOC_LLM_PROVIDER=gemini` + `GEMINI_API_KEY` as Lambda env vars |
| [x] | `DynamoDBStore(ResultStore)` and switch `api.py` to it (3 methods) | backend | `JsonFileStore` works meanwhile; Lambda's disk is ephemeral, so this matters for the live link |
| [x] | Build the website with `VITE_API_URL=<Lambda URL>` and deploy `web/dist` (Amplify Hosting, Netlify or Vercel free) | frontend | `cd web && npm run build` |
| 5 | Fill member names and contact email in `web/src/content/business.ts`; deck title slide; Thank-you slide demo URL | frontend / pitch | Search `[Member` and `[URL]` |
| [x] | Rebuild the APK once the public API exists, or set the URL in the app's gear menu during the demo; upload APK to Drive, link in slides | frontend | `docs/DEMO-ANDROID.md` -> Rebuilding |
| 7 | Upload `docs/pitch/deck.pdf` to Drive (Anyone with link -> Viewer); or import into Google Slides | pitch | Regenerate: `npx @marp-team/marp-cli docs/pitch/deck.md --pdf` |
| 8 | Record the video (<= 5:00) following `docs/pitch/video-script.md`; include the hover sheen, a KPI-tile click, one sample run, one mailbox fetch if a test Gmail is ready; upload Unlisted | pitch | Rehearse twice with a timer |
| 9 | Make the GitHub repo public; verify the README setup on a clean clone | all | Last step before the form |
| 10 | Submit the Google Form: description, repo, live link, slides, video | rep | https://forms.gle/nnam5eXrf5cjXdf3 |

## Should do if time allows

- [ ] Create a throwaway Gmail with an App Password for the live "Connect mailbox" moment; send it the two sample attachments beforehand
- [ ] Run the LLM path on the ~30 emails rules are least confident about and report the delta on a slide (Gemini key is configured locally)
- [ ] Restrict API CORS to the dashboard origin before going public
- [ ] Rotate the Gemini and 21st.dev keys after the event (both passed through chat)
- [ ] Ask the organisers for the scoring-server URL

## Finals (after 24 Sep, if shortlisted)

- [ ] Gmail add-on / Outlook add-in so staff trigger a check from inside the mail client
- [ ] SQS + worker Lambda for `POST /process`; move region to ap-southeast-1 (PDPA)
- [ ] OCR reader for image-only PDFs (Textract or Tesseract) as a `DocumentReader`
- [ ] Learn label synonyms from reviewer corrections
- [ ] Screen-reader pass with a real user; Play-store Data Safety form if publishing

## Open questions for Workshop 2 (Averis, 21 Sep 7 PM)

1. Catching every defect vs never raising a false alarm: which matters more to them?
2. Do they want the tool to draft the amendment email, or only flag?
3. Will the organisers' scoring server be available, and at what URL?
4. Which mail client do their documentation staff use (Outlook desktop? Gmail?) so the add-in roadmap targets the right one.
