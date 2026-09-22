# Roadmap

Where shipdoc goes after the hackathon. It comes from the limits the project already documents ([How shipdoc decides](/concepts/how-it-works), the [troubleshooting](/guide/troubleshooting) page and the release notes), so nothing here is a surprise. It is a statement of intent, not a promise, and it carries no dates on purpose.

| Label | Meaning |
|---|---|
| <Badge type="tip" text="Planned" /> | In the team's plan |
| <Badge type="info" text="Proposed" /> | An idea that follows from a known limit, not yet planned |
| <Badge type="warning" text="Needs input" /> | Cannot be finished without a decision from the people who would use it |

## Where it is today

- Sorts every email, reads SI and BL attachments (`.txt`, `.pdf`, `.docx`, `.xlsx`), compares seven fields, and names the exact fields that differ.
- Escalates what it cannot decide, with the reason: missing attachment, unreadable file, wrong document type, blank value.
- Uploads and a read-only IMAP mailbox import, a reviewer override with an audit trail, and a drafted reply for every mismatch and every escalation.
- A website, an Android app and an [HTTP API](/reference/api), deployed on AWS.

One limit to know about: the public demo has a **single shared workspace**. An email you upload or a mailbox you connect is visible to every visitor, so use test data and a throwaway mailbox. Private workspaces are the first item below.

## Next

Work that removes a documented limit.

| | Why | How |
|---|---|---|
| **A private workspace for every visitor** <Badge type="tip" text="Planned" /> | The public demo shares one workspace, so one visitor's upload or connected mailbox can be seen by the next. This is the main thing standing between the demo and safe use with real mail | Planned for after the hackathon's preliminary round. The intended design: each browser gets a random private session, the dataset stays shared and read-only, and a visitor's uploads, mailbox import, results and review overrides are kept separately in the database and expire after a day. A mailbox password would be used for one request and never stored |
| **OCR for scanned PDFs** <Badge type="tip" text="Planned" /> | A PDF that is only an image has no text layer, so today it is escalated as `unreadable` | A new `DocumentReader` using Amazon Textract or Tesseract. OCR'd values would carry lower confidence and show their evidence, and a doubtful read would still go to a person |
| **A queue for batch processing** <Badge type="tip" text="Planned" /> | `POST /process` runs the whole inbox inside one request, which is bounded by the function timeout | Enqueue one message per email (SQS) and process each in a worker Lambda that writes to DynamoDB. The pipeline is already stateless per email, so this is a wrapper, not a rewrite. The dashboard would show progress instead of waiting |
| **Learn from reviewer corrections** <Badge type="tip" text="Planned" /> | When a reviewer overrides a result because a label was not recognised, that knowledge is lost | Turn repeated corrections into suggested label synonyms. The intent is that a person approves a suggestion before it changes behaviour, in keeping with shipdoc's rule that AI recommends and a person decides |
| **Fuzzy party matching** <Badge type="warning" text="Needs input" /> | Company names match exactly after normalisation, so a one-letter typo is a mismatch | A similarity threshold. Where the line sits between a typo and a different company is a business decision, so it needs the people who send the corrections to agree it |
| **Run the AI layer on Amazon Bedrock** <Badge type="tip" text="Planned" /> | Keeps AI calls inside AWS, with a choice of models and no separate API key to manage | `BedrockClient` already exists, so this is a configuration change on the Lambda (`SDOC_LLM_PROVIDER=bedrock`) and one IAM permission, with no code to change. See [Deploy on AWS](/deploy/aws) |

## Later

| | Why | How |
|---|---|---|
| **Outlook add-in and Gmail add-on** <Badge type="tip" text="Planned" /> | Document staff work in their mail client, not in a browser tab | Run a check on the open email from inside the client, using the same API |
| **Sign in with Google or Microsoft** <Badge type="info" text="Proposed" /> | The mailbox import uses an App Password, and the password passes through the server for that one request | OAuth, so shipdoc never sees a password |
| **Accounts, roles and API authentication** <Badge type="info" text="Proposed" /> | The API is open and has no rate limiting. A reviewer's name is typed in, not verified | Real sign-in, roles (reviewer, admin), verified names in the audit trail, and rate limits |
| **Ready for a real inbox** <Badge type="tip" text="Planned" /> | Real mail carries names, phone numbers and business addresses. Private workspaces (above) come first | A written processing agreement, a notice under Malaysia's Personal Data Protection Act, data kept in the region the customer chooses, and a retention setting. See [Privacy and data handling](/concepts/privacy) |
| **Measured on real mail** <Badge type="warning" text="Needs input" /> | The 520-email dataset is synthetic and real mail is messier. The rules were tuned on the dataset's conventions and the AI fallback has seen far less real mail | An evaluation on anonymised real emails, with results published next to the synthetic ones |

## Decisions that will shape it

These are open questions rather than tasks, and the answers would change the order above:

- **Which mistake is worse?** Missing a real defect, or raising a false alarm. This sets how cautious the escalation rules should be.
- **Draft or only flag?** Whether staff want a drafted amendment email for every mismatch, or just the list of fields that differ.
- **Which mail client?** Outlook or Gmail decides which add-in is built first.
- **How much typo tolerance?** The threshold behind fuzzy party matching.

## Not planned

- **Letting AI decide a match.** The comparison stays plain, tested code. AI reads messy mail; it never decides.
- **Sending emails on its own.** shipdoc drafts an amendment or a resend request; a person sends it.
- **A chatbot.** The job is a queue of checks to review, not a conversation.

## Have an idea?

Open an issue on the [GitHub repository](https://github.com/VRP2206/Averis_hackathon_2026/issues), or use the contact details in the app's Privacy Policy. Concrete examples of an email that went wrong are the most useful thing you can send.

