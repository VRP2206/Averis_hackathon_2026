# SDOC user guide

SDOC reads a shipping-documentation inbox, sorts every email, checks each draft Bill of Lading (BL) against its Shipping Instruction (SI), and sends anything it cannot decide to a person with the reason. This guide covers the website; the Android app is the same screens.

## Screens

| Screen | What you do there |
|---|---|
| **Inbox** | See every email with its category and status. Filter, search, and open one. Connect a mailbox or upload an email in the *Email sources* bar. |
| **Compare** | Read the email, see SI vs BL field by field with mismatches highlighted, hover a value for the source line, approve or override, copy the drafted reply, translate the email. |
| **Invoices** | Billing emails with the invoice numbers, order refs and amounts found in them. |
| **Impact** | Live counts (auto-handled vs escalated) and accuracy against the answer key. |
| **Help** | Sample emails you can run with one click, and the mailbox connection steps below. |

## Getting emails in

### A. Run a sample (10 seconds)
Help → *Run this sample*. Three samples ship with the app: a mismatch, a clean pair, and a wrong document. Each is a real `.eml` with attachments.

### B. Upload one email
Inbox → **Upload .eml**. To get an `.eml`: in Gmail open the message → ⋮ → *Download message*; in Outlook drag the message to the desktop. Attachments are inside the file.

### C. Connect Gmail (read-only)
1. Google Account → **Security** → turn on **2-Step Verification**.
2. Security → **App passwords** → name it *SDOC* → *Create*. Copy the 16-character password.
3. Inbox → **Connect mailbox** → Provider *Gmail*, your address, the app password. Folder `INBOX`, latest `50`.
4. Tick the authorisation box → **Connect and fetch**. Emails arrive tagged *mailbox*.
5. **Fetch new mail** pulls anything new. **Disconnect** forgets the credentials.

Outlook / Microsoft 365: host `outlook.office365.com`. Yahoo: `imap.mail.yahoo.com`. Anything else: pick Gmail, then overwrite the host.

Demo tip: email yourself the two attachments from `sample-mismatch.eml` with subject `TO CONFIRM DOCS _ demo`, then *Fetch new mail*.

## Reading a result

| Status | Meaning | What to do |
|---|---|---|
| **OK** (green) | All 7 fields match, or it was a request with nothing to compare | Nothing |
| **Mismatch** (red) | Named fields differ between SI and BL | Check the highlighted rows, copy the drafted amendment email, send it |
| **Needs review** (yellow) | Could not decide: missing attachment, unreadable file, wrong document type, blank value | Read the reason, get the right document, re-run |

Every value shows the line it was read from when you hover it. *Approve* records your agreement; *Override* lets you change status and fields, with your name kept in the audit trail.

## Settings

Gear icon → **API server**. Only needed when the dashboard runs somewhere other than the API (Android emulator: `http://10.0.2.2:8000`; phone: your laptop's IP).

## Languages

Compare → *Translate to* → pick a language → *Translate*. The detected language and the translation appear above the original. Needs an AI provider configured on the server (`SDOC_LLM_PROVIDER`).
