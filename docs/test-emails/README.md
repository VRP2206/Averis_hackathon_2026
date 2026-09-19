# Test emails

Thirteen `.eml` files, one per situation SDOC has to handle. Inbox → **Upload .eml** → select them all (multi-select works). Each is then tagged *upload* in the inbox, with a **Why?** link showing how it was decided.

| File | Expected result | What it tests |
|---|---|---|
| 01-mismatch-port-and-containers | Mismatch: container_count, port_of_discharge | Two wrong fields; port name *and* UN/LOCODE changed |
| 02-mismatch-excel-and-word | Mismatch: consignee, gross_weight_kg | SI in Excel, BL in Word; company name and weight changed |
| 03-clean-pair-all-match | OK | Different labels (POD, To the Order of) for the same values: no false alarm |
| 04-wrong-document-invoice-not-bl | Needs review: wrong_doc_type | File named `_BL` is really a Commercial Invoice |
| 05-missing-attachment | Needs review: missing_attachment | Body says "attached", nothing is |
| 06-unreadable-empty-pdf | Needs review: unreadable | 0-byte PDF |
| 07-blank-field-in-si | Needs review: missing_value | SI has `TBA` and `???`: uncertainty, not a mismatch |
| 08-request-for-draft-no-files | OK (nothing to compare) | Asks for the draft BL; not an error |
| 09-si-request | SI request | Classification |
| 10-invoice-query | Invoice query | Classification; appears on the Invoices page with invoice no. and amount |
| 11-general-bot-notice | General | "Billing" in an automated notice is not an invoice query |
| 12-spam-phishing | Spam | Phishing wording and domain |
| 13-malay-email-mismatch | Mismatch: shipper | Malay-language body; try **Translate** on the compare screen |

Regenerate and self-check: `python scripts/make_test_emails.py` (prints PASS/FAIL per file).

## Prompt to get more test emails from another AI model

Paste this into any capable model (ChatGPT, Gemini, Claude). It returns a Python script that writes the files, because models cannot reliably hand back binary attachments directly.

```text
Write a single Python 3 script (standard library only, plus openpyxl and python-docx) that creates a folder
"sdoc-test-emails" containing realistic .eml files (RFC 822, built with email.message.EmailMessage) for
testing a shipping-documentation inbox tool. Context: a freight documentation team receives emails asking
them to check a carrier's draft Bill of Lading (BL) against the customer's Shipping Instruction (SI). The
tool compares exactly 7 fields: shipper, consignee, notify_party, port_of_loading, port_of_discharge,
container_count (e.g. "4 x 40'HC"), gross_weight_kg (e.g. "86,400 KG").
Ports are written like "PORT KLANG (WESTPORT), MALAYSIA (MYPKG)" with a UN/LOCODE in brackets.

Rules for the documents:
- SI and BL must label the same field differently. SI labels: "Shipper/Exporter", "Consignee", "Notify Party",
  "Port of Loading", "Discharge Port", "No. of Containers", "Gross Weight (KG)". BL labels: "SHIPPER",
  "To the Order of", "Notify", "POL", "Port of Discharge (POD)", "Container Count", "Gross Wt (kgs)".
- Plain-text documents use "Label: value" lines under a title line "SHIPPING INSTRUCTION" or
  "BILL OF LADING (DRAFT)". Word (.docx) BLs use a 2-column table (label | value). Excel (.xlsx) SIs use
  column A = label, column B = value.
- Attachment file names end in _SI.<ext> or _BL.<ext>.
- Use fictional companies and people only (no real brands). Use plausible ports and weights.

Create one email for each of these cases, with a filename that names the case and a print-out at the end
listing file -> expected result:
 1. BL mismatch on 1 field (txt + txt).
 2. BL mismatch on 2 fields, one of them a port whose name and LOCODE both change (txt + txt).
 3. BL mismatch where SI is .xlsx and BL is .docx.
 4. Clean pair: all 7 values identical despite different labels -> expected OK.
 5. Clean pair where only case/punctuation differs ("CO., LTD" vs "CO LTD") -> expected OK.
 6. Wrong document: the "_BL" file is actually a COMMERCIAL INVOICE or PACKING LIST -> NEEDS_REVIEW wrong_doc_type.
 7. Body says the SI and BL are attached but there are no attachments -> NEEDS_REVIEW missing_attachment.
 8. Only the SI is attached -> NEEDS_REVIEW missing_attachment.
 9. BL is a 0-byte .pdf -> NEEDS_REVIEW unreadable.
10. SI has placeholders "TBA", "???" or "_______" in required fields -> NEEDS_REVIEW missing_value.
11. Email asking the carrier to send the draft BL, no attachments -> category BL_COMPARISON, status OK.
12. Shipping Instruction request (subject like "REQUEST SI _ <OC> _ <POD> _ <CONSIGNEE> _ <BL no>") -> SI_REQUEST.
13. Invoice query mentioning an invoice number and an amount in USD -> INVOICE_QUERY.
14. Automated report such as "daily Berthing Report" or "_RPA_ ... Billing Process Completed" -> GENERAL.
15. Phishing email ("verify your account", suspicious link, odd sender domain) -> SPAM.
16. A BL-check email written in Bahasa Melayu with one mismatched field.
17. A BL-check email written in Chinese with all fields matching.
18. A forwarded thread: the real request is at the top, an older quoted message and a long signature below.

Subjects should look like real shipping inbox subjects, e.g. "TO CONFIRM DOCS _ 5RSG-00133 _ CALLAO_PERU _
<CONSIGNEE> _ <BL no>" or "AIE - <POD> - MSC(<BL no>) - <OC> - <INV> - <CUSTOMER> - CFR". Output only the script.
```
