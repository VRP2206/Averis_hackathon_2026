"""Stage 1: put each email in one of five categories.

`RuleClassifier` scores explicit signals in the subject and cleaned body.
When no rule is confident, `CascadeClassifier` asks the LLM (if configured),
otherwise falls back to the best-scoring rule category.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Optional

from .llm import LLMClient, try_llm
from .models import Category, Classification, Email
from .textnorm import strip_noise


class Classifier(ABC):
    @abstractmethod
    def classify(self, email: Email) -> Classification: ...


class RuleClassifier(Classifier):
    """Weighted keyword / pattern rules. Each hit adds to a category score;
    the winner needs a clear margin to count as confident."""

    CONFIDENT = 3.0

    SPAM_SENDER = re.compile(r"(verify|secure-mailbox|parcel-track|crypto|lottery|prize|promo|deals?)[\w.-]*\.", re.I)
    SPAM_WORDS = re.compile(
        r"\b(you have won|gift card|claim now|claim your|verify (your )?account|confirm (your )?bank|"
        r"bank details|storage (is )?full|exceeded its storage|avoid (suspension|deactivation)|"
        r"undelivered messages|parcel is on hold|confirm payment of|weird trick|hot singles|"
        r"bitcoin|guaranteed \d+% returns|\d+% off|exclusive offer|dear (valued customer|user))\b", re.I)

    # Subject shapes seen in the real SDOC inbox.
    BL_SUBJECT = re.compile(
        r"(to confirm docs|request bl draft|draft bl\b|amend bl|bl draft|\bdraft b/?l\b)", re.I)
    CODED_SUBJECT = re.compile(
        r"^(re_?\s*)?[A-Z]{2,8}\s-\s.+\s-\s[A-Z]+\([A-Z0-9]+\)\s-\s", re.I)   # DEPT - POD - CARRIER(BL#) - OC - ...
    SI_SUBJECT = re.compile(
        r"(^\s*(re_?\s*)?si\s-\s|\bcust si\b|request si\b|si needed|shipping instruction|\bsi\s*_)", re.I)
    INVOICE_SUBJECT = re.compile(
        r"(\binvoice\b|billing|\bcharges?\b|d\s*&\s*d\b|total freight|missing gr|local charges|telex release)", re.I)
    GENERAL_SUBJECT = re.compile(
        r"(update summary|berthing report|_reminder_|_rpa_|outstanding bl|pending bl release|time off|"
        r"new year|miss connection|delivery planning|approval required)", re.I)

    BL_BODY = re.compile(r"(draft bl|si and (the )?(draft )?bl|compare the si|confirm the bl|bl is in order|check the details and confirm)", re.I)
    SI_BODY = re.compile(r"(shipping instruction|please find si\b|\bsi for\b|\bsi attached)", re.I)
    INVOICE_BODY = re.compile(r"(invoice|charge|billing|freight|debit note|credit note)", re.I)

    def classify(self, email: Email) -> Classification:
        subject = email.subject or ""
        body = strip_noise(email.body)
        scores: dict[Category, float] = {c: 0.0 for c in Category}
        signals: list[str] = []
        evidence: list[str] = []

        def hit(cat: Category, weight: float, name: str, why: str = ""):
            scores[cat] += weight
            signals.append(name)
            evidence.append(f"+{weight:g} {cat.value}: {why or name}")

        def found(rx: re.Pattern, text: str) -> str:
            m = rx.search(text)
            return f'"{m.group(0).strip()}"' if m else ""

        # SPAM: content signals + untrusted sender.
        spam_hits = len(self.SPAM_WORDS.findall(subject + "\n" + body))
        if spam_hits:
            hit(Category.SPAM, 2.0 * spam_hits, f"spam_words={spam_hits}", f"{spam_hits} scam phrase(s), e.g. {found(self.SPAM_WORDS, subject + chr(10) + body)}")
        if self.SPAM_SENDER.search(email.sender.split("@")[-1]):
            hit(Category.SPAM, 2.0, "spam_sender", f"untrusted sender domain {email.sender.split('@')[-1]}")
        if re.search(r"https?://", body) and spam_hits:
            hit(Category.SPAM, 1.0, "spam_link", "link in a message that already looks like a scam")

        # Subject-line codes are the strongest business signal.
        if self.SI_SUBJECT.search(subject):
            hit(Category.SI_REQUEST, 4.0, "si_subject", f"subject has SI code {found(self.SI_SUBJECT, subject)}")
        if self.BL_SUBJECT.search(subject):
            hit(Category.BL_COMPARISON, 4.0, "bl_subject", f"subject asks about a BL {found(self.BL_SUBJECT, subject)}")
        if self.CODED_SUBJECT.search(subject) and not self.SI_SUBJECT.search(subject):
            hit(Category.BL_COMPARISON, 3.0, "coded_subject", "subject uses the DEPT - POD - CARRIER(BL no.) shipment code")
        # Automated reports / bot notices ("_RPA_ ... Billing Process Completed")
        # mention billing but are not invoice queries, so they win outright.
        if self.GENERAL_SUBJECT.search(subject):
            hit(Category.GENERAL, 5.0, "general_subject", f"subject is a report / bot notice {found(self.GENERAL_SUBJECT, subject)}")
        elif self.INVOICE_SUBJECT.search(subject):
            hit(Category.INVOICE_QUERY, 3.5, "invoice_subject", f"subject mentions billing {found(self.INVOICE_SUBJECT, subject)}")

        # Body corroboration.
        if self.BL_BODY.search(body):
            hit(Category.BL_COMPARISON, 2.0, "bl_body", f"body asks to check a draft BL {found(self.BL_BODY, body)}")
        if self.SI_BODY.search(body):
            hit(Category.SI_REQUEST, 2.0, "si_body", f"body talks about a Shipping Instruction {found(self.SI_BODY, body)}")
        if self.INVOICE_BODY.search(body):
            hit(Category.INVOICE_QUERY, 1.0, "invoice_body", f"body mentions {found(self.INVOICE_BODY, body)}")
        if any(a.upper().endswith(("_SI.TXT", "_BL.TXT", "_SI.PDF", "_BL.PDF", "_BL.DOCX", "_SI.XLSX", "_BL.XLSX"))
               for a in email.attachments):
            hit(Category.BL_COMPARISON, 1.5, "si_bl_attachments", "attachments are named as an SI and a BL")

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        best, best_score = ranked[0]
        margin = best_score - ranked[1][1]
        if best_score == 0:
            best, best_score, margin = Category.GENERAL, 0.0, 0.0
        confidence = min(1.0, (best_score / 6.0) * (0.5 + min(margin, 3.0) / 6.0)) if best_score else 0.2
        return Classification(category=best, decided_by="rule", confidence=confidence, signals=signals,
                              scores={c.value: v for c, v in scores.items() if v}, evidence=evidence)


class LLMClassifier(Classifier):
    SYSTEM = (
        "You triage a shipping-documentation inbox for a paper exporter. "
        "Categories: BL_COMPARISON (asks to check/confirm a draft Bill of Lading against a Shipping "
        "Instruction, or asks for a draft BL), SI_REQUEST (sends or requests a Shipping Instruction), "
        "INVOICE_QUERY (invoices, billing, charges, freight costs), GENERAL (reports, reminders, "
        "bot notices, HR, anything else operational), SPAM (phishing, scams, marketing). "
        'Reply with JSON only: {"category": "...", "confidence": 0.0-1.0, "reason": "..."}')

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def classify(self, email: Email) -> Classification:
        user = (f"From: {email.sender}\nSubject: {email.subject}\n"
                f"Attachments: {', '.join(email.attachments) or 'none'}\n\n{strip_noise(email.body)[:2500]}")
        reply = try_llm(self.llm, self.SYSTEM, user, max_tokens=200)
        if not reply or reply.get("category") not in Category.__members__:
            return Classification(category=Category.GENERAL, decided_by="llm", confidence=0.0,
                                  signals=["llm_unavailable"])
        return Classification(category=Category(reply["category"]), decided_by="llm",
                              confidence=float(reply.get("confidence", 0.5)),
                              signals=[f"llm:{reply.get('reason', '')[:80]}"],
                              evidence=[f"AI model: {reply.get('reason', '')[:200]}"])


class CascadeClassifier(Classifier):
    """Rules first; LLM only when rules are not confident."""

    def __init__(self, rules: RuleClassifier, llm: Optional[LLMClassifier] = None,
                 min_rule_confidence: float = 0.5):
        self.rules, self.llm, self.min_rule_confidence = rules, llm, min_rule_confidence

    def classify(self, email: Email) -> Classification:
        rule = self.rules.classify(email)
        if rule.confidence >= self.min_rule_confidence or self.llm is None:
            return rule
        llm = self.llm.classify(email)
        if llm.confidence <= 0.0:
            return rule
        llm.signals = rule.signals + llm.signals
        llm.scores = rule.scores
        llm.evidence = rule.evidence + [f"Rules were unsure (confidence {rule.confidence:.0%}), so the AI model decided."] + llm.evidence
        return llm
