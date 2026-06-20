"""Lightweight stdlib-only output schema guardrails for the 348A pilot.

These guardrails catch output boundary inversions (e.g. a TESTSET_SUPPORTING_ROW
leaking into clean_data) at build time instead of only in manual QA. R4/R5 found
exactly this class of bug in the qualitative_facts sheet; this validator encodes
the invariants so the next inversion fails the run loudly.

No external dependencies. Operates on the plain dicts the runner already builds
for clean_data.csv, review_queue.csv, and the manifest.
"""

from __future__ import annotations

from typing import Any


class OutputSchemaGuardrailError(ValueError):
    """Raised when an output boundary invariant is violated."""


# row_type values that must never appear in clean_data.
CLEAN_DATA_FORBIDDEN_ROW_TYPES = frozenset(
    {
        "TESTSET_SUPPORTING_ROW",
        "NORMALIZED_TESTSET_RECORD_ROW",
        "MARKET_REFERENCE_ROW",
        "UNKNOWN_ROW",
    }
)

# clean_candidate_type values that are the only ones allowed in clean_data.
CLEAN_DATA_ALLOWED_CANDIDATE_TYPES = frozenset(
    {
        "INTERNAL_CLEAN_CANDIDATE",
        "INTERNAL_REFERENCE_CANDIDATE",
    }
)

# review_queue rows must carry these fields non-empty.
REVIEW_QUEUE_REQUIRED_FIELDS = ("decision", "clean_candidate_type", "evidence_level")

# manifest readiness gates that must stay closed.
MANIFEST_CLOSED_GATES = {
    "client_ready": False,
    "production_ready": False,
    "formal_client_export_allowed": False,
    "demo_export_only": True,
}

# manifest external-call counters that must stay zero.
MANIFEST_ZERO_COUNTERS = {
    "llm_api_call_count": 0,
    "mineru_run_count": 0,
    "ocr_run_count": 0,
}

# manifest legacy-touch flags that must stay False.
MANIFEST_FALSE_FLAGS = {
    "legacy_datefac_touched": False,
    "legacy_outputs_touched": False,
}

# manifest count fields that must be present for count-consistency checks.
MANIFEST_REQUIRED_COUNT_FIELDS = (
    "clean_data_row_count",
    "review_queue_row_count",
    "unknown_row_count",
)


def _fail(message: str) -> None:
    raise OutputSchemaGuardrailError(message)


def _validate_clean_rows(clean_rows: list[dict[str, Any]]) -> None:
    for index, row in enumerate(clean_rows):
        row_type = row.get("row_type")
        if row_type is None:
            _fail(f"clean_data row {index} is missing required field 'row_type'")
        if row_type in CLEAN_DATA_FORBIDDEN_ROW_TYPES:
            sheet = row.get("sheet_name", "?")
            metric = row.get("metric_name", "?")
            _fail(
                f"clean_data boundary violation: row {index} "
                f"(sheet={sheet!r} metric={metric!r}) has forbidden row_type "
                f"{row_type!r}; clean_data must not contain "
                f"{sorted(CLEAN_DATA_FORBIDDEN_ROW_TYPES)}"
            )

        candidate_type = row.get("clean_candidate_type")
        if candidate_type is None:
            _fail(f"clean_data row {index} is missing required field 'clean_candidate_type'")
        if candidate_type not in CLEAN_DATA_ALLOWED_CANDIDATE_TYPES:
            sheet = row.get("sheet_name", "?")
            metric = row.get("metric_name", "?")
            _fail(
                f"clean_data boundary violation: row {index} "
                f"(sheet={sheet!r} metric={metric!r}) has clean_candidate_type "
                f"{candidate_type!r}; only {sorted(CLEAN_DATA_ALLOWED_CANDIDATE_TYPES)} "
                f"are allowed in clean_data"
            )


def _validate_count_consistency(
    clean_rows: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    for field in MANIFEST_REQUIRED_COUNT_FIELDS:
        if field not in manifest:
            _fail(f"manifest is missing required count field {field!r}")

    clean_count = len(clean_rows)
    manifest_clean_count = manifest["clean_data_row_count"]
    if clean_count != manifest_clean_count:
        _fail(
            f"clean_data count mismatch: clean_data.csv has {clean_count} rows but "
            f"manifest clean_data_row_count={manifest_clean_count}"
        )

    if "clean_data_csv_row_count" in manifest:
        manifest_clean_csv_count = manifest["clean_data_csv_row_count"]
        if clean_count != manifest_clean_csv_count:
            _fail(
                f"clean_data count mismatch: clean_data.csv has {clean_count} rows but "
                f"manifest clean_data_csv_row_count={manifest_clean_csv_count}"
            )

    review_count = len(review_rows)
    manifest_review_count = manifest.get("review_queue_csv_row_count", manifest["review_queue_row_count"])
    if review_count != manifest_review_count:
        count_field = "review_queue_csv_row_count" if "review_queue_csv_row_count" in manifest else "review_queue_row_count"
        _fail(
            f"review_queue count mismatch: review_queue.csv has {review_count} rows but "
            f"manifest {count_field}={manifest_review_count}"
        )


def _validate_review_rows(review_rows: list[dict[str, Any]]) -> None:
    for index, row in enumerate(review_rows):
        for field in REVIEW_QUEUE_REQUIRED_FIELDS:
            value = row.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                sheet = row.get("sheet_name", "?")
                _fail(
                    f"review_queue row {index} (sheet={sheet!r}) has empty/missing "
                    f"required field {field!r}"
                )


def _validate_manifest(manifest: dict[str, Any]) -> None:
    for field, expected in MANIFEST_CLOSED_GATES.items():
        actual = manifest.get(field)
        if actual is None:
            _fail(f"manifest is missing readiness gate {field!r}")
        if actual != expected:
            _fail(
                f"manifest readiness gate {field!r} must be {expected!r} but is {actual!r}"
            )

    for field, expected in MANIFEST_ZERO_COUNTERS.items():
        actual = manifest.get(field)
        if actual is None:
            _fail(f"manifest is missing external-call counter {field!r}")
        if actual != expected:
            _fail(
                f"manifest external-call counter {field!r} must be {expected!r} "
                f"but is {actual!r}"
            )

    for field, expected in MANIFEST_FALSE_FLAGS.items():
        if field not in manifest:
            # legacy flags may not be present in every manifest; enforce presence only
            # when the field exists (documented in the result report).
            continue
        actual = manifest[field]
        if actual != expected:
            _fail(
                f"manifest flag {field!r} must be {expected!r} but is {actual!r}"
            )


def validate_outputs(
    clean_rows: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    """Validate pilot outputs against the clean-data boundary invariants.

    Raises OutputSchemaGuardrailError on the first violation with a message
    naming the offending row/sheet/field. Returns None when all guardrails pass.
    """
    _validate_clean_rows(clean_rows)
    _validate_count_consistency(clean_rows, review_rows, manifest)
    _validate_review_rows(review_rows)
    _validate_manifest(manifest)
