"""Real-mail path: .eml parsing, attachment caching, upload + composite inbox."""
from email.message import EmailMessage

from sdoc.mail import CompositeInbox, UploadInbox
from sdoc.models import Category, Status
from sdoc.pipeline import build_pipeline
from sdoc.config import settings


def _eml(inbox, email_id: str) -> bytes:
    """Wrap a dataset email and its attachments as a real RFC-822 message."""
    src = inbox.get(email_id)
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = src.sender, "docs@example.com", src.subject
    m.set_content(src.body)
    for path in src.attachments:
        name = path.split("/")[-1]
        m.add_attachment(inbox.read_bytes(path), maintype="application", subtype="octet-stream", filename=name)
    return m.as_bytes()


def test_uploaded_eml_runs_through_pipeline(inbox, tmp_path):
    comp = CompositeInbox(inbox)
    up = UploadInbox(tmp_path / "up")
    comp.add_source("upload", up)
    pipe = build_pipeline(settings, comp)

    e = up.add(_eml(inbox, "email_025"))          # a MISMATCH in the dataset
    assert e.email_id.startswith("upload_") and len(e.attachments) == 2
    r = pipe.process(comp.get(e.email_id))
    assert r.category == Category.BL_COMPARISON
    assert r.status == Status.MISMATCH
    assert set(r.defect_fields) == {"container_count", "port_of_discharge"}
    assert comp.source_of(e.email_id) == "upload"


def test_html_only_body_is_flattened(tmp_path):
    m = EmailMessage()
    m["From"], m["Subject"] = "a@b.com", "REQUEST TO CANCEL INVOICE -5250075931"
    m.set_content("<p>Please <b>cancel</b> invoice 5250075931.</p><br>Thanks", subtype="html")
    up = UploadInbox(tmp_path)
    e = up.add(m.as_bytes())
    assert "cancel invoice 5250075931" in e.body.lower()
    assert "<" not in e.body
