# Compliance and risk review

Scope: the SDOC web app (`web/`), the Android app (same code via Capacitor) and the API. Reviewed 20 Sep 2026 against Malaysian law first (the hackathon and the team are in Malaysia), with GDPR notes where shipping counterparties may be in the EU.

**Important framing.** This is a student hackathon prototype built for the Averis × Monash Hackathon 2026. It is **not** an Averis product and must never present itself as one: no Averis or APRIL logos, no "official" wording, and the footer says who built it. Impersonating a real organisation is the single biggest legal risk for a project like this.

## What the product actually does with data

| Data | Where it comes from | Where it goes | Kept? |
|---|---|---|---|
| Email records + attachments | Organisers' synthetic dataset (fictional senders, real-looking company names) | Read by the pipeline; served by the API to the dashboard | In the repo and on the server |
| Pipeline results (category, status, evidence lines) | Generated | `output/results.json` / DynamoDB | Yes |
| Reviewer overrides (`status`, `defect_fields`, `reviewer` name) | Typed by the reviewer | API → store | Yes; the reviewer name is personal data |
| UI preferences (theme, filters) | The browser | `localStorage` only | On the device |
| Mailbox credentials (IMAP host, address, app password) | Typed by the operator | Server memory for the session; used only to read the folder | Never written to disk or logs |
| Emails and attachments from a connected mailbox or uploaded .eml | The operator's mailbox | Attachments cached on the server so the pipeline can read them; results stored | Until disconnect/cleanup |
| Analytics, ads, tracking pixels | none | none | — |

Personal data actually collected from real people: **only the reviewer's display name** on an override. Everything else in the dataset is synthetic. If the system is later pointed at a real inbox, it will process names, phone numbers and business addresses of shipping staff and customers, and the notes below become mandatory rather than advisory.

## Pages added and why

| Page | Required by | Status |
|---|---|---|
| Privacy Policy | PDPA 2010 s.7 (notice and choice principle) once any personal data is processed; GDPR Art. 13 if EU data subjects | Added: `/privacy` |
| Terms of Use | Good practice; limits liability for a prototype that makes document decisions | Added: `/terms` |
| Cookie Policy | Not specifically required in Malaysia; GDPR/ePrivacy only for non-essential cookies | Added: `/cookies` (explains there are none) |
| Cookie consent banner | Only if non-essential cookies or trackers are set | **Not needed**: no analytics, no third-party embeds, no cookies. `localStorage` holds only UI preferences, which is "strictly necessary". Do not add analytics without revisiting this. |
| Refund policy | Only if goods/services are sold (Consumer Protection Act 1999, Electronic Commerce Act 2006) | **Not applicable**: nothing is sold. Terms state there are no purchases. Do not add a fake refund policy. |
| Form consent | PDPA notice at the point of collection | Added: consent note on the reviewer override form |
| Accessibility statement | Good practice; WCAG 2.1 AA | Added: `/accessibility` |
| Business / contact details | PDPA requires a contact for data access requests | Added in footer and Privacy page: **fill in team name and a contact email** |

## Checklist from the brief

- [x] Privacy policy, terms, cookie policy pages
- [x] Cookie consent: assessed, not required (see above); documented on the cookie page
- [x] Refund policy: assessed, not applicable; stated in Terms
- [x] Form consent on the only form that collects personal data (reviewer name)
- [x] Collect only necessary data: reviewer name is optional and defaults to "reviewer"
- [x] Analytics tracking: none included; `web/index.html` has no third-party scripts
- [x] Third-party embeds: none; fonts (Fredoka, Nunito, OFL) are self-hosted via Fontsource, so no request goes to a font CDN
- [x] Accessibility: semantic landmarks, skip link, focus rings, labelled controls, `aria-live` on status changes, keyboard-operable table and forms, `prefers-reduced-motion` respected
- [x] Alt text: all meaningful images/icons labelled; decorative icons `aria-hidden`
- [x] Colour contrast: status colours checked at ≥ 4.5:1 on both themes; status is never conveyed by colour alone (text label + icon)
- [x] Keyboard-friendly forms: native controls, visible focus, Enter submits, Escape closes dialogs
- [x] Clear button labels: "Approve result", "Override result", "Copy draft reply", "Process inbox"
- [x] No fake reviews / testimonials anywhere
- [x] No unsupported claims: the metrics shown are computed live from `/metrics` on the provided dataset and labelled "on the hackathon dataset (synthetic)"
- [x] Business details: footer block, placeholders marked `TODO`
- [x] Image copyright: no stock photos. Icons are Lucide (ISC licence). 21st.dev components are MIT-licensed; the licence file is kept in `web/LICENSES.md`
- [x] Local laws checked: PDPA 2010 and 2024 amendments, Copyright Act 1987, Computer Crimes Act 1997, Consumer Protection Act 1999, ECA 2006; GDPR for EU counterparties

## Risks flagged

0. **Connecting a real mailbox** turns the demo into processing of real personal data (senders, phone numbers, addresses). The connect form requires the operator to confirm they are authorised; use a dedicated test mailbox for the demo, and an App Password rather than the account password. IMAP access is read-only.

1. **Impersonation.** Do not use Averis/APRIL branding or imply endorsement. Keep the "student prototype" footer.
2. **Real inbox use.** If connected to a real mailbox (finals roadmap), you become a data processor for Averis. You need: a written processing agreement, a PDPA notice to staff, breach notification within 72 h (PDPA Amendment Act 2024, in force 2025), and a data protection officer if processing is large-scale. Cross-border storage on AWS us-east-1 is a PDPA s.129 transfer; use an ap-southeast region (Singapore/Malaysia) to avoid the issue.
3. **Automated decisions.** The tool recommends; a human approves. Keep it that way in the UI copy ("recommended", "review") to avoid GDPR Art. 22 concerns and to match the rubric's human-in-the-loop story.
4. **LLM data sharing.** With `SDOC_LLM_PROVIDER` set, document text is sent to Anthropic or AWS Bedrock. Disclosed in the Privacy Policy. Bedrock keeps data in-region and does not train on it; use that for any real data.
5. **Dataset licence.** The dataset is provided for the hackathon. Do not redistribute it beyond the repo required for submission; the rules grant organisers a licence to showcase your project, not the reverse.
6. **API keys.** The 21st.dev key was pasted in a chat; rotate it after the event. Never commit `.env`.
7. **Open CORS** on the API is fine for a demo; restrict `allow_origins` to the deployed dashboard URL before any real use.
8. **App store.** Google Play requires a privacy policy URL and a Data Safety form; the `/privacy` page satisfies the URL. A hackathon demo APK can be side-loaded and does not need Play listing.

## What I did not do

- No lawyer reviewed this. For anything beyond the hackathon, have the policies checked by counsel.
- Accessibility was checked by inspection and keyboard walkthrough, not by users of assistive technology.
