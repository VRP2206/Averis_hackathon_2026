import pytest

from sdoc.classify import CascadeClassifier, LLMClassifier, RuleClassifier
from sdoc.llm import LLMClient
from sdoc.models import Category, Email


def email(subject, body="", sender="docs@aprilasia.com", attachments=()):
    return Email(email_id="t", **{"from": sender}, subject=subject, body=body, attachments=list(attachments))


@pytest.mark.parametrize("mail,expected", [
    (email("TO CONFIRM DOCS _ 5RSG-00133 _ CALLAO_PERU _ X _ MEDUUD104332",
           "Attached are the SI and draft BL. Please check and confirm."), Category.BL_COMPARISON),
    (email("AIE - CALLAO_PERU - EVER(EGLV577449160936) - 5RUS-1 - INV - CUST - FOB",
           "Please compare the SI and draft BL"), Category.BL_COMPARISON),
    (email("SI - MEDUUD1 - DIRECT(MSC) - 5RSG-1 - CALLAO_PERU - SEAWAY - AIE - 3-Jan-26",
           "Please find Shipping instruction for 5RSG-1"), Category.SI_REQUEST),
    (email("REQUEST TO CANCEL INVOICE -5250075931 - X - 5AKR-1", "Please cancel invoice"), Category.INVOICE_QUERY),
    (email("_RPA_ India HSS SD Billing Process Completed - LE HAVRE V.QI540A",
           "This is an automated notification. No action required.", "rpa.bot@aprilasia.com"), Category.GENERAL),
    (email("daily Berthing Report - 12 JAN 2026", "Kindly find the daily berthing report attached."), Category.GENERAL),
    (email("Congratulations! You have WON a $1,000 Gift Card - CLAIM NOW",
           "Verify your account: http://webmail-verify.co", "info@webmail-verify.co"), Category.SPAM),
])
def test_rules(mail, expected):
    assert RuleClassifier().classify(mail).category == expected


class FakeLLM(LLMClient):
    def __init__(self, reply):
        self.reply, self.calls = reply, 0

    def complete_json(self, system, user, *, strong=False, max_tokens=1024):
        self.calls += 1
        return self.reply


def test_cascade_uses_llm_only_when_rules_unsure():
    fake = FakeLLM({"category": "INVOICE_QUERY", "confidence": 0.9, "reason": "asks about a charge"})
    clf = CascadeClassifier(RuleClassifier(), LLMClassifier(fake))
    sure = clf.classify(email("TO CONFIRM DOCS _ X", "Attached are the SI and draft BL"))
    assert sure.decided_by == "rule" and fake.calls == 0
    unsure = clf.classify(email("Question", "Can you tell me why we were debited twice?"))
    assert unsure.category == Category.INVOICE_QUERY and unsure.decided_by == "llm" and fake.calls == 1
