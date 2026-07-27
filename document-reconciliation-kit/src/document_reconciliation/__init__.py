"""Deterministic reconciliation for structured document outputs."""

from .models import ComparisonRecord, NormalizedRecord
from .reconciliation import PUBLIC_IDENTITY_FIELDS, reconcile_records

__version__ = "0.1.1"

__all__ = ["__version__", "ComparisonRecord", "NormalizedRecord", "PUBLIC_IDENTITY_FIELDS", "reconcile_records"]
