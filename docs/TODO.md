# What's left (as of 20 Sep 2026)

Deadline: **Tue 22 Sep, 12:00 PM**. Aim to submit the form by 11:00.

## Done

- [x] Core pipeline, 1.000 on the dataset, 49 tests (`sdoc/`, `tests/`)
- [x] HTTP API with reviewer override (`sdoc/api.py`)
- [x] Web dashboard: Inbox, Compare, Invoices, Impact, translation + legal/accessibility pages (`web/`)
- [x] Real mail in: IMAP connector + .eml upload (`sdoc/mail.py`)
- [x] Android wrapper via Capacitor (`web/android/`), prebuilt `apk/sdoc-debug.apk`, `scripts/demo-android.ps1`, `docs/DEMO-ANDROID.md`
- [x] Help page + `docs/USER-GUIDE.md`: sample emails, Gmail/Outlook connection steps
- [x] Docs: README, PLAN, ARCHITECTURE, HANDOFF, COMPLIANCE, pitch deck, video script

## Must do before submitting

| # | Task | Owner | Notes |
|---|---|---|---|
| 1 | Create the team AWS account, do the 5 credit tasks, set a $10 budget alert | backend | Today. Blocks the public demo link. |
| 2 | Deploy the API: Lambda + Mangum + Function URL, data in S3 or bundled | backend | `docs/HANDOFF.md` → Backend. Test `/health`, `/emails`, `POST /process`. |
| 3 | `DynamoDBStore(ResultStore)` and switch `api.py` to it | backend | 3 methods. `JsonFileStore` works meanwhile. |
| 4 | Set `VITE_API_URL` to the deployed API and build the web app; deploy to Amplify Hosting (or Netlify/Vercel free) | frontend | `cd web && npm run build` |
| 5 | Fill placeholders: member names, contact email (team name done: Claude's Plan) in `web/src/content/business.ts`, deck title slide | all | Search for `TODO` and `[TEAM NAME]` |
| 6 | Build the APK: `cd web && npm run build && npx cap sync android && cd android && ./gradlew assembleDebug` | frontend | Needs `JAVA_HOME` = Android Studio's `jbr`. Upload APK to Drive, link in slides. |
| 7 | Export slides: `npx @marp-team/marp-cli docs/pitch/deck.md --pdf` → upload PDF to Drive (Anyone with link → Viewer) | pitch | Or paste into Google Slides. |
| 8 | Record the video (≤ 5:00) following `docs/pitch/video-script.md`; upload Unlisted | pitch | Rehearse the 2-min demo twice. |
| 9 | Make the GitHub repo public; check README setup works on a clean clone | all | Last step. |
| 10 | Submit the Google Form: description, repo, live link, slides, video | rep | https://forms.gle/nnam5eXrf5cjXdf3 |

## Should do if time allows

- [ ] Run the LLM path on the ~30 emails rules are least confident about and report the delta (needs an Anthropic key or Bedrock access). Even "no change" is a good validation slide.
- [ ] Restrict API CORS to the dashboard origin.
- [ ] Add `sdoc run --source http://<organisers-server>` in README once the organisers publish the scoring URL.
- [ ] Screenshot the dashboard for the README.

## Finals (after 24 Sep, if shortlisted)

- [ ] SQS + worker Lambda for `POST /process`
- [ ] OCR reader for image-only PDFs (Textract or Tesseract) as a `DocumentReader`
- [ ] Gmail add-on / Outlook add-in so staff trigger a check from inside their mail client (IMAP connector already done)
- [ ] Learn label synonyms from reviewer corrections
- [ ] Move AWS region to ap-southeast-1 for PDPA cross-border reasons

## Open questions for Workshop 2 (Averis, 21 Sep 7 PM)

1. Catching every defect vs never raising a false alarm: which matters more to them?
2. Do they want the tool to draft the amendment email, or only flag?
3. Will the organisers' scoring server be available, and at what URL?
