# Getting started

shipdoc checks the paperwork that arrives in a shipping-documentation inbox. For each email it decides what kind of email it is, and for emails that ask someone to check a draft **Bill of Lading (BL)** against the customer's **Shipping Instruction (SI)** it compares seven fields and tells you exactly which ones differ. Anything it cannot decide goes to a person as **Needs review**, with the reason.

## Try it in two minutes

1. Open **[shipdoc.org](https://shipdoc.org)**. The inbox shows the 520 emails of the hackathon dataset (synthetic data provided by the organisers). The first load after a quiet period can take a few seconds. If the counts show zero, click **Process inbox**.
2. Click the red **Mismatches to amend** tile, then open one email. The **Compare** screen shows the SI and the BL side by side, with the differing fields highlighted. Hover any value to see the line it was read from.
3. Click **Why?** on any email for the full trail: which words classified it, each safety check, what each attachment was detected as, and how the final call was made.

![The inbox](/screenshots/inbox.png)

## Bring your own email

| You want to | Do this |
|---|---|
| See it work in ten seconds | **Help → Run this sample**. Three samples ship with the app |
| Try a specific situation | Download a file from [Test emails](/guide/test-emails) and use **Upload .eml** |
| Use a real mailbox | **Connect mailbox**, with an App Password. See the [user guide](/guide/user-guide) |
| Use it on a phone | Install the [Android app](/guide/android) |

::: warning Use test data on the public demo
The live demo has one shared workspace: an email you upload or a mailbox you connect can be seen by other visitors. Use a throwaway mailbox and do not upload real customer emails to it. Private workspaces are on the [roadmap](/roadmap). See [Privacy and data handling](/concepts/privacy).
:::

## What you see

| Status | Meaning |
|---|---|
| <span class="status-ok">OK</span> | Nothing to fix. The documents match, or there was nothing to compare |
| <span class="status-mismatch">Mismatch</span> | The BL differs from the SI. The exact fields are named and an amendment email is drafted |
| <span class="status-review">Needs review</span> | shipdoc will not guess. A person decides, and the reason is shown |

The full list of categories, statuses and reasons is in [Categories, statuses and reasons](/concepts/statuses).

![Compare screen](/screenshots/compare.png)

## Where next

- [User guide](/guide/user-guide): every screen and how to connect a mailbox
- [How shipdoc decides](/concepts/how-it-works): the pipeline, stage by stage
- [API reference](/reference/api): use the pipeline from your own code
- [Run it locally](/deploy/run-locally) or [deploy it on AWS](/deploy/aws)
