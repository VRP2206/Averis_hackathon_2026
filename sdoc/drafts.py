"""Draft the follow-up email a reviewer would send. Deterministic template;
a person edits and sends it."""
from __future__ import annotations

from .models import EmailResult, ReviewReason, Status

_FIELD_NAMES = {
    "shipper": "Shipper", "consignee": "Consignee", "notify_party": "Notify Party",
    "port_of_loading": "Port of Loading", "port_of_discharge": "Port of Discharge",
    "container_count": "Container Count", "gross_weight_kg": "Gross Weight (KG)",
}
_REVIEW_TEXT = {
    ReviewReason.MISSING_ATTACHMENT: "the SI and/or draft BL were not attached. Please resend both documents.",
    ReviewReason.UNREADABLE: "one of the attached files could not be read (empty, corrupt or image-only scan). Please resend a text-readable copy.",
    ReviewReason.WRONG_DOC_TYPE: "the second attachment is not a Bill of Lading. Please send the draft BL.",
    ReviewReason.MISSING_VALUE: "some required fields are blank or missing. Please complete them and resend.",
}


class ReplyDrafter:
    def draft(self, result: EmailResult, subject: str) -> str | None:
        if result.status == Status.MISMATCH:
            lines = [f"Subject: RE: {subject}", "", "Dear Team,", "",
                     "Please amend the draft BL. The following fields do not match the SI:", ""]
            for c in result.comparisons:
                if not c.match:
                    lines.append(f"  - {_FIELD_NAMES[c.field]}: BL shows \"{c.bl_value}\" but SI shows \"{c.si_value}\"")
            lines += ["", "Kindly resend the corrected draft for confirmation.", "", "Best regards,"]
            return "\n".join(lines)
        if result.status == Status.NEEDS_REVIEW and result.review_reason:
            return "\n".join([f"Subject: RE: {subject}", "", "Dear Team,", "",
                              f"We could not complete the SI/BL check because {_REVIEW_TEXT[result.review_reason]}",
                              "", "Best regards,"])
        return None
