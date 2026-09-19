"""SDOC: shipping-document inbox triage and SI/BL discrepancy detection.

Pipeline: email -> classify -> gate -> read attachments -> extract fields
-> compare -> result (OK | MISMATCH | NEEDS_REVIEW).
"""
from .pipeline import Pipeline, build_pipeline

__all__ = ["Pipeline", "build_pipeline"]
