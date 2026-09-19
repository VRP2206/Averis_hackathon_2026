"""Readers, doc-type detection and heuristic extraction on real sample files."""
import pytest

from sdoc.doctype import DocTypeDetector
from sdoc.extract import HeuristicExtractor, is_blank
from sdoc.models import COMPARE_FIELDS, DocType
from sdoc.readers import ReaderRegistry


@pytest.mark.parametrize("value,blank", [("???", True), ("_______", True), ("TBA", True), ("", True),
                                         ("____MT", True), ("21,577 KG", False), ("CALLAO, PERU", False)])
def test_blank_tokens(value, blank):
    assert is_blank(value) is blank


def test_unreadable_inputs_do_not_raise():
    rr = ReaderRegistry()
    assert rr.read("a.pdf", b"").readable is False
    assert rr.read("a.pdf", b"%PDF-1.4 garbage").readable is False
    assert rr.read("a.docx", b"not a zip").readable is False
    assert rr.read("a.exe", b"xx").readable is False


@pytest.mark.parametrize("email_id", ["email_001", "email_059", "email_055", "email_005", "email_171"])
def test_all_seven_fields_found_in_every_format(inbox, email_id):
    """txt, pdf, xlsx+docx and xlsx+xlsx pairs all yield the 7 fields."""
    rr, dt, ex = ReaderRegistry(), DocTypeDetector(), HeuristicExtractor()
    mail = inbox.get(email_id)
    types = set()
    for path in mail.attachments:
        doc = rr.read(path, inbox.read_bytes(path))
        doc.doc_type = dt.detect(doc)
        types.add(doc.doc_type)
        found = ex.extract(doc).fields
        missing = [f for f in COMPARE_FIELDS if not found[f].usable]
        assert not missing, f"{path}: missing {missing}"
    assert types == {DocType.SI, DocType.BL}


def test_wrong_doc_type_detected_by_content(inbox):
    rr, dt = ReaderRegistry(), DocTypeDetector()
    path = "attachments/email_501_BL.txt"     # named BL, actually a Commercial Invoice
    doc = rr.read(path, inbox.read_bytes(path))
    assert dt.detect(doc) == DocType.COMMERCIAL_INVOICE


def test_image_only_pdf_is_unreadable(inbox):
    path = "attachments/email_512_BL.pdf"
    assert ReaderRegistry().read(path, inbox.read_bytes(path)).readable is False
