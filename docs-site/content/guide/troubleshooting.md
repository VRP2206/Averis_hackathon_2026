# Troubleshooting

## The inbox is empty, or "Could not reach the API"

The app is a thin shell around the API and shows nothing if it cannot reach it.

- **Website:** open the gear icon and check the API address. On the live site it should be the deployment's Function URL. Clear it to fall back to the address built into the site.
- **Android app:** an emulator reaches your laptop at `http://10.0.2.2:8000`. A real phone needs `http://<your-laptop-ip>:8000` on the same Wi-Fi. See the [Android guide](/guide/android).
- **Locally:** check that `sdoc serve` is running and that `http://127.0.0.1:8000/health` answers.

## The counts show zero

The dataset is loaded but no results exist yet. Click **Process inbox**. On a fresh deployment this takes a few seconds.

## The first click is slow

The API on AWS goes to sleep when idle. The first request after a quiet period takes a few seconds while it starts; the next ones are fast. Open `/health` a minute before a demo.

## Connecting Gmail fails

Gmail does not accept your normal password from other apps.

1. Turn on **2-Step Verification** (Google Account → Security).
2. Create an **App Password** at <https://myaccount.google.com/apppasswords>.
3. Use the 16-letter App Password, with your full address, host `imap.gmail.com` and folder `INBOX`.

| Message | Likely cause |
|---|---|
| `AUTHENTICATIONFAILED` or "application-specific password required" | Normal password used, mistyped App Password, or none created yet |
| The App passwords page is missing | 2-Step Verification is off, or a work/school account whose admin disabled it |
| Works locally, fails on the live site | Google may flag a sign-in from a data-centre address. Check for a "Critical security alert" email and confirm it was you |

Use a test mailbox. Most real emails are classified as General or Spam: shipdoc only compares documents when an email carries a Shipping Instruction and a draft Bill of Lading.

## An upload is rejected

Upload a raw email file (`.eml`). In Gmail open the message, then ⋮ → **Download message**; in Outlook drag the message to the desktop. Very large emails may be refused by the server; try one without a big attachment.

## Everything is "Needs review"

That is shipdoc refusing to guess. Open the email and read the reason, and the **Why?** page for the step that stopped it. The reasons are listed in [Categories, statuses and reasons](/concepts/statuses): a missing attachment, an unreadable or scanned file, a file that is not an SI or BL by content, or a blank value.

## A scanned PDF is "unreadable"

shipdoc reads text, not pixels. A PDF that is only an image has no text layer, so it is escalated. Adding OCR is a change to one reader class.

## Translate returns the original text

No AI provider is configured on that server, so shipdoc can detect the language but not translate. Set `SDOC_LLM_PROVIDER` (see [Configuration](/reference/configuration)).

## The accuracy panel on the Impact page is missing

It needs the organisers' scoring data, which is not on the public deployment. The counts on the Impact page still work.

## Deployment problems

See the table at the end of [Deploy on AWS](/deploy/aws).
