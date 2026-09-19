"""Score a submission against ground truth.

The metric definitions follow the organisers' `scoring.py` (SDOC hackathon
kit) so our numbers match theirs:
final = 0.30 * stage1 macro-F1 + 0.20 * stage3 defect-F1 + 0.50 * end-to-end.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .models import COMPARE_FIELDS, Category, ReviewReason

CATEGORIES = [c.value for c in Category]
WEIGHTS = {"stage1": 0.30, "stage3": 0.20, "end_to_end": 0.50}


def _prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


class Evaluator:
    def __init__(self, ground_truth: dict | Path | str):
        self.truth = (json.loads(Path(ground_truth).read_text(encoding="utf-8"))
                      if not isinstance(ground_truth, dict) else ground_truth)

    def score(self, sub: dict) -> dict:
        s1, s3, rel, e2e = self._stage1(sub), self._stage3(sub), self._reliability(sub), self._end_to_end(sub)
        final = (WEIGHTS["stage1"] * s1["macro_f1"] + WEIGHTS["stage3"] * s3["defect_f1"]
                 + WEIGHTS["end_to_end"] * e2e["rate"])
        return {"final_score": final, "stage1": s1, "stage3": s3, "reliability": rel,
                "end_to_end": e2e, "n_emails": len(self.truth)}

    def mistakes(self, sub: dict) -> list[dict]:
        """Every email where we differ from ground truth, for error analysis."""
        out = []
        for eid, t in self.truth.items():
            s = sub.get(eid, {})
            diff = {k: (s.get(k), t.get(k)) for k in ("category", "status", "review_reason")
                    if s.get(k) != t.get(k)}
            if set(s.get("defect_fields", [])) != set(t.get("defect_fields", [])):
                diff["defect_fields"] = (sorted(s.get("defect_fields", [])), sorted(t["defect_fields"]))
            if diff:
                out.append({"email_id": eid, **{k: {"ours": v[0], "truth": v[1]} for k, v in diff.items()}})
        return out

    # -- axes ------------------------------------------------------------------
    def _stage1(self, sub):
        per = {c: {"tp": 0, "fp": 0, "fn": 0} for c in CATEGORIES}
        confusion = defaultdict(lambda: defaultdict(int))
        correct = 0
        for eid, t in self.truth.items():
            actual, pred = t["category"], sub.get(eid, {}).get("category", "GENERAL")
            confusion[actual][pred] += 1
            if pred == actual:
                correct += 1; per[actual]["tp"] += 1
            else:
                per[actual]["fn"] += 1
                if pred in per: per[pred]["fp"] += 1
        return {"accuracy": correct / len(self.truth),
                "macro_f1": sum(_prf(**per[c])[2] for c in CATEGORIES) / len(CATEGORIES),
                "per_category": {c: dict(zip(("precision", "recall", "f1"), _prf(**per[c]))) for c in CATEGORIES},
                "confusion": {a: dict(d) for a, d in confusion.items()}}

    def _stage3(self, sub):
        tp = fp = fn = 0; f_tp = f_fp = f_fn = 0; exact = total = 0
        for eid, t in self.truth.items():
            if t["category"] != "BL_COMPARISON" or t.get("status") == "NEEDS_REVIEW":
                continue
            total += 1
            s = sub.get(eid, {})
            routed = s.get("category") == "BL_COMPARISON"
            pred_defect = bool(s.get("has_defect")) and routed
            pred_fields = set(s.get("defect_fields", [])) if routed else set()
            gold_fields = set(t["defect_fields"])
            if t["has_defect"] and pred_defect: tp += 1
            elif t["has_defect"]: fn += 1
            elif pred_defect: fp += 1
            exact += pred_fields == gold_fields
            f_tp += len(pred_fields & gold_fields); f_fp += len(pred_fields - gold_fields); f_fn += len(gold_fields - pred_fields)
        p, r, f = _prf(tp, fp, fn)
        return {"defect_precision": p, "defect_recall": r, "defect_f1": f,
                "field_f1": _prf(f_tp, f_fp, f_fn)[2], "exact_match_rate": exact / total if total else 0.0,
                "doc_total": total}

    def _reliability(self, sub):
        per = {r.value: {"total": 0, "caught": 0} for r in ReviewReason}
        gold = pred = both = 0
        for eid, t in self.truth.items():
            p_needs = sub.get(eid, {}).get("status") == "NEEDS_REVIEW"
            g_needs = t.get("status") == "NEEDS_REVIEW"
            pred += p_needs; gold += g_needs; both += p_needs and g_needs
            if g_needs and t.get("review_reason") in per:
                per[t["review_reason"]]["total"] += 1
                per[t["review_reason"]]["caught"] += p_needs
        recall = both / gold if gold else 0.0
        precision = both / pred if pred else 0.0
        return {"escalation_recall": recall, "escalation_precision": precision,
                "escalation_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
                "gold_review": gold, "pred_review": pred, "per_reason": per}

    def _end_to_end(self, sub):
        total = success = 0
        for eid, t in self.truth.items():
            if not (t["category"] == "BL_COMPARISON" and t.get("has_defect")):
                continue
            total += 1
            s = sub.get(eid, {})
            success += (s.get("category") == "BL_COMPARISON" and bool(s.get("has_defect"))
                        and set(s.get("defect_fields", [])) == set(t["defect_fields"]))
        return {"success": success, "total": total, "rate": success / total if total else 0.0}


def format_report(score: dict) -> str:
    s1, s3, rel, e2e = score["stage1"], score["stage3"], score["reliability"], score["end_to_end"]
    lines = [
        f"FINAL SCORE            {score['final_score']:.4f}   (n={score['n_emails']})",
        f"  stage1 macro-F1      {s1['macro_f1']:.4f}   accuracy {s1['accuracy']:.4f}",
        f"  stage3 defect-F1     {s3['defect_f1']:.4f}   P {s3['defect_precision']:.3f}  R {s3['defect_recall']:.3f}  field-F1 {s3['field_f1']:.3f}  exact {s3['exact_match_rate']:.3f}",
        f"  end-to-end           {e2e['rate']:.4f}   ({e2e['success']}/{e2e['total']} defective emails fully caught)",
        f"  reliability          esc-recall {rel['escalation_recall']:.3f}  esc-precision {rel['escalation_precision']:.3f}  "
        f"(predicted {rel['pred_review']}, gold {rel['gold_review']})",
        "  per category F1      " + "  ".join(f"{c}={v['f1']:.3f}" for c, v in s1["per_category"].items()),
        "  per review reason    " + "  ".join(f"{r}={v['caught']}/{v['total']}" for r, v in rel["per_reason"].items()),
    ]
    return "\n".join(lines)
