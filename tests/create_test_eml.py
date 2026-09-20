import os

files = {
    "clean_shipping_doc.eml": """From: shipping@logistics.com
To: user@sdoc.com
Subject: Shipping Confirmation - BOL #99281
Date: Sun, 20 Sep 2026 10:00:00 +0000
Content-Type: text/plain; charset="utf-8"

Dear Team,

Please find attached the clean shipping documentation for Order #99281.
Quantity: 150 units.
Origin: Port of Klang
Destination: Singapore
""",

    "mismatch_test.eml": """From: vendor@supplies.org
To: user@sdoc.com
Subject: Invoice & Shipping Mismatch Test
Date: Sun, 20 Sep 2026 11:30:00 +0000
Content-Type: text/plain; charset="utf-8"

Order ID: 88412
Declared Items: 50
Invoiced Items: 45
Total Amount: $1,200.00
Note: Intentional discrepancy created for QA mismatch testing.
""",

    "script_injection_xss.eml": """From: <script>alert('XSS')</script>@test.com
To: user@sdoc.com
Subject: <img src=x onerror=alert('Subject_XSS')>
Date: Sun, 20 Sep 2026 12:00:00 +0000
Content-Type: text/html; charset="utf-8"

<html>
  <body>
    <h1>Testing Script Injection</h1>
    <script>console.log("Testing XSS payload in EML parser");</script>
  </body>
</html>
""",

    "malformed_missing_headers.eml": """This email lacks standard RFC 822/5322 MIME headers.
Directly starting with plain text without From, To, or Subject fields.
Testing how the backend parser handles malformed input.
"""
}

for filename, content in files.items():
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {filename}")