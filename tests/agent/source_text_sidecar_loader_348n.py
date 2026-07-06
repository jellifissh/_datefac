"""Test-only source_text sidecar loader for R7AF fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from datefac_agent.schemas.audit_models import SourceTextEvidence

TOP_LEVEL_KEYS = frozenset({"schema_version", "fixture_scope", "records"})
RECORD_KEYS = frozenset(
    {
        "source_text_id",
        "source_document_id",
        "page_number",
        "locator",
        "text_kind",
        "text",
        "text_sha256",
        "char_count",
        "trusted_source",
        "extraction_method",
    }
)
ALLOWED_TEXT_KINDS = frozenset({"table_row", "table_row_text", "snippet_text"})


class SourceTextSidecarValidationError(ValueError):
    """Raised when a test-only source_text sidecar fails closed."""


def _fail(message: str) -> None:
    raise SourceTextSidecarValidationError(message)


def _validate_exact_keys(payload: dict[str, Any], allowed_keys: frozenset[str], label: str) -> None:
    missing = sorted(allowed_keys - set(payload))
    if missing:
        _fail(f"{label} missing required keys: {', '.join(missing)}")
    unknown = sorted(set(payload) - allowed_keys)
    if unknown:
        _fail(f"{label} has unknown keys: {', '.join(unknown)}")


def _require_non_empty_str(value: Any, field: str, record_index: int) -> str:
    if not isinstance(value, str):
        _fail(f"record {record_index} field {field} must be a string")
    if not value.strip():
        _fail(f"record {record_index} field {field} must be non-empty")
    return value


def _require_positive_int(value: Any, field: str, record_index: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(f"record {record_index} field {field} must be a positive integer")
    if value <= 0:
        _fail(f"record {record_index} field {field} must be a positive integer")
    return value


def _validate_record(record: Any, record_index: int, seen_ids: set[str]) -> SourceTextEvidence:
    if not isinstance(record, dict):
        _fail(f"record {record_index} must be an object")
    _validate_exact_keys(record, RECORD_KEYS, f"record {record_index}")

    source_text_id = _require_non_empty_str(record["source_text_id"], "source_text_id", record_index)
    if source_text_id in seen_ids:
        _fail(f"duplicate source_text_id: {source_text_id}")
    seen_ids.add(source_text_id)

    source_document_id = _require_non_empty_str(record["source_document_id"], "source_document_id", record_index)
    page_number = _require_positive_int(record["page_number"], "page_number", record_index)
    locator = _require_non_empty_str(record["locator"], "locator", record_index)
    text_kind = _require_non_empty_str(record["text_kind"], "text_kind", record_index)
    if text_kind not in ALLOWED_TEXT_KINDS:
        _fail(f"record {record_index} field text_kind is unsupported: {text_kind}")
    text = _require_non_empty_str(record["text"], "text", record_index)
    text_sha256 = _require_non_empty_str(record["text_sha256"], "text_sha256", record_index)
    char_count = _require_positive_int(record["char_count"], "char_count", record_index)
    if record["trusted_source"] is not True:
        _fail(f"record {record_index} field trusted_source must be true")
    extraction_method = _require_non_empty_str(record["extraction_method"], "extraction_method", record_index)

    computed_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if text_sha256 != computed_sha256:
        _fail(f"record {record_index} field text_sha256 mismatch")
    if char_count != len(text):
        _fail(f"record {record_index} field char_count mismatch")

    return SourceTextEvidence(
        source_text_id=source_text_id,
        source_document_id=source_document_id,
        page_number=page_number,
        locator=locator,
        text_kind=text_kind,
        text=text,
        text_sha256=computed_sha256,
        char_count=char_count,
        trusted_source=True,
        extraction_method=extraction_method,
    )


def load_source_text_sidecar_fixture(path: str | Path) -> list[SourceTextEvidence]:
    fixture_path = Path(path)
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(f"invalid JSON: {exc.msg}")

    if not isinstance(payload, dict):
        _fail("top-level payload must be an object")
    _validate_exact_keys(payload, TOP_LEVEL_KEYS, "top-level payload")

    if payload["schema_version"] != 1 or isinstance(payload["schema_version"], bool):
        _fail("schema_version must be 1")
    if payload["fixture_scope"] != "test_only":
        _fail("fixture_scope must be test_only")
    if not isinstance(payload["records"], list):
        _fail("records must be a list")

    seen_ids: set[str] = set()
    return [_validate_record(record, index, seen_ids) for index, record in enumerate(payload["records"])]
