"""Domain model shared by every stage of the pipeline and by the API."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Category(str, Enum):
    BL_COMPARISON = "BL_COMPARISON"
    SI_REQUEST = "SI_REQUEST"
    INVOICE_QUERY = "INVOICE_QUERY"
    GENERAL = "GENERAL"
    SPAM = "SPAM"


class Status(str, Enum):
    OK = "OK"
    MISMATCH = "MISMATCH"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ReviewReason(str, Enum):
    WRONG_DOC_TYPE = "wrong_doc_type"
    MISSING_ATTACHMENT = "missing_attachment"
    UNREADABLE = "unreadable"
    MISSING_VALUE = "missing_value"


class DocType(str, Enum):
    SI = "SI"
    BL = "BL"
    COMMERCIAL_INVOICE = "COMMERCIAL_INVOICE"
    PACKING_LIST = "PACKING_LIST"
    CERTIFICATE_OF_ORIGIN = "CERTIFICATE_OF_ORIGIN"
    UNKNOWN = "UNKNOWN"


# The 7 fields the SI and BL are compared on, in canonical order.
COMPARE_FIELDS: tuple[str, ...] = (
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg",
)


class Email(BaseModel):
    email_id: str
    sender: str = Field(alias="from")
    subject: str = ""
    body: str = ""
    attachments: list[str] = []

    model_config = {"populate_by_name": True}


class Document(BaseModel):
    """An attachment after reading: raw text plus label/value pairs when the
    format has an explicit table structure (DOCX, XLSX)."""
    path: str
    kind: str                       # file extension: txt / pdf / docx / xlsx
    text: str = ""
    pairs: list[tuple[str, str]] = []
    readable: bool = True
    error: Optional[str] = None
    doc_type: DocType = DocType.UNKNOWN

    @property
    def lines(self) -> list[str]:
        return [ln.rstrip() for ln in self.text.splitlines() if ln.strip()]


class ExtractedField(BaseModel):
    field: str
    value: Optional[str] = None      # raw text as written in the document
    source: Optional[str] = None     # the line it came from (evidence)
    confidence: float = 0.0
    blank: bool = False              # present but a placeholder (???, TBA)

    @property
    def usable(self) -> bool:
        return self.value is not None and not self.blank


class Extraction(BaseModel):
    doc_path: str
    doc_type: DocType
    fields: dict[str, ExtractedField]
    method: str = "heuristic"        # heuristic | llm


class FieldComparison(BaseModel):
    field: str
    si_value: Optional[str]
    bl_value: Optional[str]
    si_normalised: Optional[str]
    bl_normalised: Optional[str]
    match: bool


class Classification(BaseModel):
    category: Category
    decided_by: str                  # rule | llm
    confidence: float
    signals: list[str] = []
    scores: dict[str, float] = {}    # points per category (rules only)
    evidence: list[str] = []         # human-readable "why" lines


class TraceStep(BaseModel):
    """One step of the audit trail shown on the "Why?" page."""
    stage: str                       # classify | read | gate | extract | compare | decide
    title: str
    outcome: str = "info"            # pass | fail | info | decision
    detail: str = ""
    evidence: list[str] = []


class EmailResult(BaseModel):
    """One email's outcome. `to_submission()` gives the scorer's shape."""
    email_id: str
    category: Category
    status: Status = Status.OK
    review_reason: Optional[ReviewReason] = None
    has_defect: bool = False
    defect_fields: list[str] = []
    decided_by: str = "rule"
    classification: Optional[Classification] = None
    comparisons: list[FieldComparison] = []
    extractions: list[Extraction] = []
    notes: list[str] = []
    draft_reply: Optional[str] = None
    trace: list[TraceStep] = []

    def to_submission(self) -> dict:
        return {
            "category": self.category.value,
            "status": self.status.value,
            "review_reason": self.review_reason.value if self.review_reason else None,
            "has_defect": self.has_defect,
            "defect_fields": list(self.defect_fields),
            "decided_by": self.decided_by,
        }
