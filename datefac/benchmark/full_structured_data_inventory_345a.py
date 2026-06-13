from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345A = "FULL_STRUCTURED_DATA_INVENTORY_345A_READY"
NOT_READY_DECISION_345A = "FULL_STRUCTURED_DATA_INVENTORY_345A_NOT_READY"
INPUT_STAGE_345A = "POST_344F_FULL_STRUCTURED_INVENTORY"

DEFAULT_TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_DIR = Path(
    r"D:\_datefac\output\table_first_core_financial_extraction_342f"
)
DEFAULT_TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_DIR = Path(
    r"D:\_datefac\output\table_first_extraction_review_package_342g"
)
DEFAULT_TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_DIR = Path(
    r"D:\_datefac\output\table_first_human_review_apply_simulation_342h"
)
DEFAULT_REVIEW_QUEUE_STRICT_HUMAN_REVIEW_PACKAGE_344F_DIR = Path(
    r"D:\_datefac\output\review_queue_strict_human_review_package_344f"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\full_structured_data_inventory_345a")

MANIFEST_FILE_NAME = "full_structured_data_inventory_345a_manifest.json"
SOURCE_ARTIFACT_MAP_FILE_NAME = "full_structured_data_inventory_345a_source_artifact_map.json"
ROW_INVENTORY_JSON_FILE_NAME = "full_structured_data_inventory_345a_row_inventory.json"
ROW_INVENTORY_CSV_FILE_NAME = "full_structured_data_inventory_345a_row_inventory.csv"
STAGE_STATUS_SUMMARY_JSON_FILE_NAME = (
    "full_structured_data_inventory_345a_stage_status_summary.json"
)
STAGE_STATUS_SUMMARY_CSV_FILE_NAME = (
    "full_structured_data_inventory_345a_stage_status_summary.csv"
)
MISSING_FIELD_SUMMARY_JSON_FILE_NAME = (
    "full_structured_data_inventory_345a_missing_field_summary.json"
)
MISSING_FIELD_SUMMARY_CSV_FILE_NAME = (
    "full_structured_data_inventory_345a_missing_field_summary.csv"
)
DOWNSTREAM_READINESS_SUMMARY_FILE_NAME = (
    "full_structured_data_inventory_345a_downstream_readiness_summary.json"
)
EXECUTIVE_SUMMARY_FILE_NAME = "full_structured_data_inventory_345a_executive_summary.md"
ARTIFACT_INDEX_FILE_NAME = "full_structured_data_inventory_345a_artifact_index.md"
NEXT_PLAN_FILE_NAME = "full_structured_data_inventory_345a_next_plan.md"

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

FORBIDDEN_STAGE_PATHS = [
    "output",
    "temp",
    "input",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

ROW_INVENTORY_FIELDS = [
    "inventory_row_id",
    "source_artifact",
    "source_stage",
    "source_row_id",
    "pdf_id",
    "pdf_name",
    "table_id",
    "row_index",
    "column_name",
    "metric_name",
    "normalized_metric_name",
    "value_raw",
    "value_normalized",
    "unit",
    "period",
    "source_page",
    "confidence",
    "trust_status",
    "review_status",
    "human_review_status",
    "is_metric_candidate",
    "is_normalized_metric",
    "is_downstream_ready_candidate",
    "missing_required_field_count",
    "missing_required_fields",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_rows(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"expected JSON list at {path}")
    return payload


def _is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def _run_git(repo_root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_status_porcelain_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = _run_git(repo_root, ["status", "--porcelain", "--", *paths])
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_staged_names_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    lines = _git_status_porcelain_for_paths(paths, repo_root)
    staged: List[str] = []
    for line in lines:
        if line.startswith("__ERROR__::"):
            return [line]
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return normalize_text(value)


def _safe_number_text(value: Any) -> str:
    text = _safe_text(value)
    return text


def _load_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"required input file missing: {path}")
    return pd.read_excel(path, sheet_name=sheet_name)


def _sheet_exists(path: Path, sheet_name: str) -> bool:
    with pd.ExcelFile(path) as workbook:
        return sheet_name in workbook.sheet_names


def _required_missing_fields(row: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    if not _safe_text(row.get("metric_name")) and not _safe_text(row.get("normalized_metric_name")):
        missing.append("metric_name")
    if not _safe_text(row.get("value_raw")) and not _safe_text(row.get("value_normalized")):
        missing.append("value")
    if not _safe_text(row.get("unit")):
        missing.append("unit")
    if not _safe_text(row.get("period")):
        missing.append("period")
    if not _safe_text(row.get("source_page")):
        missing.append("source_page")
    return missing


def _downstream_ready_candidate(row: Dict[str, Any]) -> bool:
    has_metric = bool(_safe_text(row.get("metric_name")) or _safe_text(row.get("normalized_metric_name")))
    has_value = bool(_safe_text(row.get("value_raw")) or _safe_text(row.get("value_normalized")))
    review_status = _safe_text(row.get("review_status"))
    non_rejected = review_status not in {"REJECTED_OR_EXCLUDED", "REJECTED", "NOT_CORE_METRIC"}
    has_source_trace = bool(
        _safe_text(row.get("source_page"))
        or _safe_text(row.get("table_id"))
        or _safe_text(row.get("source_artifact"))
    )
    return has_metric and has_value and non_rejected and has_source_trace


def _finalize_inventory_row(row: Dict[str, Any]) -> Dict[str, Any]:
    finalized = {field: row.get(field, "") for field in ROW_INVENTORY_FIELDS}
    missing_fields = _required_missing_fields(finalized)
    finalized["missing_required_field_count"] = len(missing_fields)
    finalized["missing_required_fields"] = "|".join(missing_fields)
    finalized["is_downstream_ready_candidate"] = _downstream_ready_candidate(finalized)
    return finalized


def _inventory_row_id(prefix: str, index: int) -> str:
    return f"345a::{prefix}::{index:05d}"


def _records_from_dataframe(
    frame: pd.DataFrame,
    *,
    source_artifact: str,
    source_stage: str,
    source_row_id_field: str,
    pdf_id_field: str,
    pdf_name_field: str,
    table_id_field: str,
    row_index_field: str | None,
    metric_name_field: str,
    normalized_metric_name_field: str,
    value_raw_field: str,
    value_normalized_field: str,
    unit_field: str,
    period_field: str,
    source_page_field: str,
    confidence_field: str | None,
    trust_status_value: str,
    review_status_value: str,
    human_review_status_value: str,
    prefix: str,
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for index, record in enumerate(frame.to_dict(orient="records"), start=1):
        records.append(
            _finalize_inventory_row(
                {
                    "inventory_row_id": _inventory_row_id(prefix, index),
                    "source_artifact": source_artifact,
                    "source_stage": source_stage,
                    "source_row_id": _safe_text(record.get(source_row_id_field)),
                    "pdf_id": _safe_text(record.get(pdf_id_field)),
                    "pdf_name": _safe_text(record.get(pdf_name_field)),
                    "table_id": _safe_text(record.get(table_id_field)),
                    "row_index": _safe_text(record.get(row_index_field)) if row_index_field else "",
                    "column_name": "",
                    "metric_name": _safe_text(record.get(metric_name_field)),
                    "normalized_metric_name": _safe_text(record.get(normalized_metric_name_field)),
                    "value_raw": _safe_number_text(record.get(value_raw_field)),
                    "value_normalized": _safe_number_text(record.get(value_normalized_field)),
                    "unit": _safe_text(record.get(unit_field)),
                    "period": _safe_text(record.get(period_field)),
                    "source_page": _safe_text(record.get(source_page_field)),
                    "confidence": _safe_text(record.get(confidence_field)) if confidence_field else "",
                    "trust_status": trust_status_value,
                    "review_status": review_status_value,
                    "human_review_status": human_review_status_value,
                    "is_metric_candidate": bool(
                        _safe_text(record.get(metric_name_field))
                        or _safe_text(record.get(normalized_metric_name_field))
                    ),
                    "is_normalized_metric": bool(_safe_text(record.get(normalized_metric_name_field))),
                }
            )
        )
    return records


def _summary_from_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "row_count": len(rows),
        "downstream_ready_candidate_count": sum(
            1 for row in rows if row["is_downstream_ready_candidate"]
        ),
        "missing_metric_name_count": sum(
            1
            for row in rows
            if not _safe_text(row["metric_name"]) and not _safe_text(row["normalized_metric_name"])
        ),
        "missing_unit_count": sum(1 for row in rows if not _safe_text(row["unit"])),
        "missing_period_count": sum(1 for row in rows if not _safe_text(row["period"])),
        "missing_source_page_count": sum(1 for row in rows if not _safe_text(row["source_page"])),
    }


def _build_stage_status_summary(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(_safe_text(row["source_stage"]), []).append(row)
    summary_rows: List[Dict[str, Any]] = []
    for source_stage, stage_rows in sorted(grouped.items()):
        review_counter = Counter(_safe_text(row["review_status"]) for row in stage_rows)
        summary_rows.append(
            {
                "source_stage": source_stage,
                "row_count": len(stage_rows),
                "trusted_count": sum(1 for row in stage_rows if _safe_text(row["trust_status"]) == "TRUSTED"),
                "review_required_count": sum(
                    1 for row in stage_rows if _safe_text(row["review_status"]) == "REVIEW_REQUIRED"
                ),
                "rejected_or_excluded_count": sum(
                    1
                    for row in stage_rows
                    if _safe_text(row["review_status"]) == "REJECTED_OR_EXCLUDED"
                ),
                "human_review_applied_count": sum(
                    1 for row in stage_rows if _safe_text(row["source_stage"]) == "HUMAN_REVIEW_APPLIED"
                ),
                "strict_human_review_pending_row_count": sum(
                    1
                    for row in stage_rows
                    if _safe_text(row["source_stage"]) == "STRICT_HUMAN_REVIEW_PENDING_ROW"
                ),
                "downstream_ready_candidate_count": sum(
                    1 for row in stage_rows if row["is_downstream_ready_candidate"]
                ),
                "top_review_statuses": ", ".join(
                    f"{name}:{count}" for name, count in review_counter.most_common(3)
                ),
            }
        )
    return summary_rows


def _build_missing_field_summary(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(_safe_text(row["source_stage"]), []).append(row)
    summary_rows: List[Dict[str, Any]] = []
    for source_stage, stage_rows in sorted(grouped.items()):
        missing_counter = Counter()
        for row in stage_rows:
            for field in _safe_text(row["missing_required_fields"]).split("|"):
                if field:
                    missing_counter[field] += 1
        summary_rows.append(
            {
                "source_stage": source_stage,
                "row_count": len(stage_rows),
                "missing_metric_name_count": sum(
                    1
                    for row in stage_rows
                    if not _safe_text(row["metric_name"]) and not _safe_text(row["normalized_metric_name"])
                ),
                "missing_unit_count": sum(1 for row in stage_rows if not _safe_text(row["unit"])),
                "missing_period_count": sum(
                    1 for row in stage_rows if not _safe_text(row["period"])
                ),
                "missing_source_page_count": sum(
                    1 for row in stage_rows if not _safe_text(row["source_page"])
                ),
                "top_missing_fields": ", ".join(
                    f"{name}:{count}" for name, count in missing_counter.most_common(5)
                ),
            }
        )
    return summary_rows


def _build_downstream_readiness_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "downstream_ready_candidate_count": sum(
            1 for row in rows if row["is_downstream_ready_candidate"]
        ),
        "blocked_missing_metric_name_count": sum(
            1
            for row in rows
            if not row["is_downstream_ready_candidate"]
            and not _safe_text(row["metric_name"])
            and not _safe_text(row["normalized_metric_name"])
        ),
        "blocked_missing_value_count": sum(
            1
            for row in rows
            if not row["is_downstream_ready_candidate"]
            and not _safe_text(row["value_raw"])
            and not _safe_text(row["value_normalized"])
        ),
        "blocked_rejected_status_count": sum(
            1
            for row in rows
            if _safe_text(row["review_status"]) in {"REJECTED_OR_EXCLUDED", "REJECTED", "NOT_CORE_METRIC"}
        ),
        "blocked_missing_source_trace_count": sum(
            1
            for row in rows
            if not row["is_downstream_ready_candidate"]
            and not (
                _safe_text(row["source_page"])
                or _safe_text(row["table_id"])
                or _safe_text(row["source_artifact"])
            )
        ),
    }


def _artifact_row(name: str, path: Path, purpose: str, required: bool, readable: bool) -> Dict[str, Any]:
    return {
        "artifact_name": name,
        "path": str(path),
        "required": required,
        "exists": path.exists(),
        "readable": readable,
        "purpose": purpose,
    }


def build_full_structured_data_inventory_345a(
    *,
    table_first_core_financial_extraction_342f_dir: Path = DEFAULT_TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_DIR,
    table_first_extraction_review_package_342g_dir: Path = DEFAULT_TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_DIR,
    table_first_human_review_apply_simulation_342h_dir: Path = DEFAULT_TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_DIR,
    review_queue_strict_human_review_package_344f_dir: Path = DEFAULT_REVIEW_QUEUE_STRICT_HUMAN_REVIEW_PACKAGE_344F_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    warnings: List[str] = []
    files_read: List[str] = []
    source_artifact_map: List[Dict[str, Any]] = []
    inventory_rows: List[Dict[str, Any]] = []
    input_paths: List[Path] = []

    workbook_342f = table_first_core_financial_extraction_342f_dir / "table_first_core_financial_extraction_342f.xlsx"
    summary_342f = table_first_core_financial_extraction_342f_dir / "table_first_core_financial_extraction_342f_summary.json"
    workbook_342g = table_first_extraction_review_package_342g_dir / "table_first_extraction_review_package_342g.xlsx"
    summary_342g = table_first_extraction_review_package_342g_dir / "table_first_extraction_review_package_342g_summary.json"
    workbook_342h = table_first_human_review_apply_simulation_342h_dir / "table_first_human_review_apply_simulation_342h.xlsx"
    summary_342h = table_first_human_review_apply_simulation_342h_dir / "table_first_human_review_apply_simulation_342h_summary.json"
    rows_344f = review_queue_strict_human_review_package_344f_dir / "review_queue_strict_human_review_package_344f_review_rows.json"
    manifest_344f = review_queue_strict_human_review_package_344f_dir / "review_queue_strict_human_review_package_344f_manifest.json"

    required_anchor_exists = workbook_342f.exists() or workbook_342g.exists()
    if not required_anchor_exists:
        raise FileNotFoundError(
            f"345A requires at least one of 342F or 342G input dirs to exist: {workbook_342f} / {workbook_342g}"
        )

    optional_inputs = [
        ("342F workbook", workbook_342f, "Table-first long-form / trusted / review-required / rejected cell inventory base.", False),
        ("342F summary", summary_342f, "342F stage counts and status summary.", False),
        ("342G workbook", workbook_342g, "Review queue, trusted audit sample, and human-review template rows.", False),
        ("342G summary", summary_342g, "342G review package counts and readiness summary.", False),
        ("342H workbook", workbook_342h, "Human review apply simulation results and pending rows.", False),
        ("342H summary", summary_342h, "342H counts for human review simulation.", False),
        ("344F review rows", rows_344f, "Strict human review pending 29-row package rows.", False),
        ("344F manifest", manifest_344f, "344F gate and count summary.", False),
    ]

    for name, path, purpose, required in optional_inputs:
        readable = path.exists()
        if not path.exists():
            warnings.append(f"missing optional input: {path}")
        else:
            files_read.append(str(path))
            input_paths.append(path)
        source_artifact_map.append(_artifact_row(name, path, purpose, required, readable))

    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}

    summary_342f_json = _read_json(summary_342f) if summary_342f.exists() else {}
    summary_342g_json = _read_json(summary_342g) if summary_342g.exists() else {}
    summary_342h_json = _read_json(summary_342h) if summary_342h.exists() else {}
    manifest_344f_json = _read_json(manifest_344f) if manifest_344f.exists() else {}

    if workbook_342f.exists():
        long_form_df = _load_excel_sheet(workbook_342f, "03_LONG_FORM_CELLS")
        trusted_df = _load_excel_sheet(workbook_342f, "04_TRUSTED_CELLS")
        review_required_df = _load_excel_sheet(workbook_342f, "05_REVIEW_REQUIRED")
        rejected_df = _load_excel_sheet(workbook_342f, "06_REJECTED_CELLS")
        inventory_rows.extend(
            _records_from_dataframe(
                long_form_df,
                source_artifact="342F::03_LONG_FORM_CELLS",
                source_stage="LONG_FORM_CELL",
                source_row_id_field="long_cell_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field="row_index",
                metric_name_field="metric_raw",
                normalized_metric_name_field="metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="value_numeric",
                unit_field="normalized_unit",
                period_field="year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="LONG_FORM",
                review_status_value="LONG_FORM_CELL",
                human_review_status_value="NOT_REVIEWED",
                prefix="long_form",
            )
        )
        inventory_rows.extend(
            _records_from_dataframe(
                trusted_df,
                source_artifact="342F::04_TRUSTED_CELLS",
                source_stage="TRUSTED_CELL",
                source_row_id_field="long_cell_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field="row_index",
                metric_name_field="metric_raw",
                normalized_metric_name_field="metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="value_numeric",
                unit_field="normalized_unit",
                period_field="year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="TRUSTED",
                review_status_value="TRUSTED_CELL",
                human_review_status_value="NOT_REVIEWED",
                prefix="trusted",
            )
        )
        inventory_rows.extend(
            _records_from_dataframe(
                review_required_df,
                source_artifact="342F::05_REVIEW_REQUIRED",
                source_stage="REVIEW_REQUIRED",
                source_row_id_field="long_cell_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field="row_index",
                metric_name_field="metric_raw",
                normalized_metric_name_field="metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="value_numeric",
                unit_field="normalized_unit",
                period_field="year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="REVIEW_REQUIRED",
                review_status_value="REVIEW_REQUIRED",
                human_review_status_value="NOT_REVIEWED",
                prefix="review_required",
            )
        )
        inventory_rows.extend(
            _records_from_dataframe(
                rejected_df,
                source_artifact="342F::06_REJECTED_CELLS",
                source_stage="REJECTED_OR_EXCLUDED",
                source_row_id_field="long_cell_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field="row_index",
                metric_name_field="metric_raw",
                normalized_metric_name_field="metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="value_numeric",
                unit_field="normalized_unit",
                period_field="year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="REJECTED_OR_EXCLUDED",
                review_status_value="REJECTED_OR_EXCLUDED",
                human_review_status_value="NOT_REVIEWED",
                prefix="rejected",
            )
        )

    if workbook_342g.exists():
        review_queue_df = _load_excel_sheet(workbook_342g, "03_REVIEW_QUEUE")
        trusted_audit_df = _load_excel_sheet(workbook_342g, "04_TRUSTED_AUDIT")
        review_template_df = _load_excel_sheet(workbook_342g, "10_REVIEW_TEMPLATE")
        inventory_rows.extend(
            _records_from_dataframe(
                review_queue_df,
                source_artifact="342G::03_REVIEW_QUEUE",
                source_stage="REVIEW_REQUIRED",
                source_row_id_field="review_item_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field=None,
                metric_name_field="metric_raw",
                normalized_metric_name_field="metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="value_numeric",
                unit_field="normalized_unit",
                period_field="year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="REVIEW_QUEUE",
                review_status_value="REVIEW_REQUIRED",
                human_review_status_value="PENDING_HUMAN_REVIEW",
                prefix="342g_queue",
            )
        )
        inventory_rows.extend(
            _records_from_dataframe(
                trusted_audit_df,
                source_artifact="342G::04_TRUSTED_AUDIT",
                source_stage="TRUSTED_CELL",
                source_row_id_field="review_item_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field=None,
                metric_name_field="metric_raw",
                normalized_metric_name_field="metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="value_numeric",
                unit_field="normalized_unit",
                period_field="year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="TRUSTED_AUDIT_SAMPLE",
                review_status_value="TRUSTED_CELL",
                human_review_status_value="AUDIT_SAMPLE_ONLY",
                prefix="342g_trusted_audit",
            )
        )
        inventory_rows.extend(
            _records_from_dataframe(
                review_template_df,
                source_artifact="342G::10_REVIEW_TEMPLATE",
                source_stage="REVIEW_REQUIRED",
                source_row_id_field="review_item_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field=None,
                metric_name_field="metric_raw",
                normalized_metric_name_field="metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="value_numeric",
                unit_field="normalized_unit",
                period_field="year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="REVIEW_TEMPLATE",
                review_status_value="REVIEW_REQUIRED",
                human_review_status_value="FILLABLE_TEMPLATE",
                prefix="342g_template",
            )
        )

    if workbook_342h.exists():
        validated_df = _load_excel_sheet(workbook_342h, "03_VALIDATED_DECISIONS")
        confirmed_df = _load_excel_sheet(workbook_342h, "04_CONFIRMED_CELLS")
        corrected_df = _load_excel_sheet(workbook_342h, "05_CORRECTED_CELLS")
        rejected_df = _load_excel_sheet(workbook_342h, "06_REJECTED_CELLS")
        pending_df = _load_excel_sheet(workbook_342h, "09_PENDING_REVIEW")
        inventory_rows.extend(
            _records_from_dataframe(
                validated_df,
                source_artifact="342H::03_VALIDATED_DECISIONS",
                source_stage="HUMAN_REVIEW_APPLIED",
                source_row_id_field="review_item_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field=None,
                metric_name_field="metric_raw",
                normalized_metric_name_field="metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="value_numeric",
                unit_field="normalized_unit",
                period_field="year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="VALIDATED_HUMAN_REVIEW",
                review_status_value="HUMAN_REVIEW_APPLIED",
                human_review_status_value="VALIDATED_DECISION",
                prefix="342h_validated",
            )
        )
        inventory_rows.extend(
            _records_from_dataframe(
                confirmed_df,
                source_artifact="342H::04_CONFIRMED_CELLS",
                source_stage="HUMAN_REVIEW_APPLIED",
                source_row_id_field="review_item_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field=None,
                metric_name_field="metric_raw",
                normalized_metric_name_field="metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="value_numeric",
                unit_field="normalized_unit",
                period_field="year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="HUMAN_CONFIRMED",
                review_status_value="HUMAN_REVIEW_APPLIED",
                human_review_status_value="CONFIRMED",
                prefix="342h_confirmed",
            )
        )
        inventory_rows.extend(
            _records_from_dataframe(
                corrected_df,
                source_artifact="342H::05_CORRECTED_CELLS",
                source_stage="HUMAN_REVIEW_APPLIED",
                source_row_id_field="review_item_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field=None,
                metric_name_field="metric_raw",
                normalized_metric_name_field="reviewer_metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="reviewer_value_numeric",
                unit_field="reviewer_normalized_unit",
                period_field="reviewer_year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="HUMAN_CORRECTED",
                review_status_value="HUMAN_REVIEW_APPLIED",
                human_review_status_value="CORRECTED",
                prefix="342h_corrected",
            )
        )
        inventory_rows.extend(
            _records_from_dataframe(
                rejected_df,
                source_artifact="342H::06_REJECTED_CELLS",
                source_stage="REJECTED_OR_EXCLUDED",
                source_row_id_field="review_item_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field=None,
                metric_name_field="metric_raw",
                normalized_metric_name_field="metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="value_numeric",
                unit_field="normalized_unit",
                period_field="year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="HUMAN_REJECTED",
                review_status_value="REJECTED_OR_EXCLUDED",
                human_review_status_value="REJECTED",
                prefix="342h_rejected",
            )
        )
        inventory_rows.extend(
            _records_from_dataframe(
                pending_df,
                source_artifact="342H::09_PENDING_REVIEW",
                source_stage="REVIEW_REQUIRED",
                source_row_id_field="review_item_id",
                pdf_id_field="corpus_pdf_id",
                pdf_name_field="file_name",
                table_id_field="table_id",
                row_index_field=None,
                metric_name_field="metric_raw",
                normalized_metric_name_field="metric_standardized",
                value_raw_field="value_raw",
                value_normalized_field="value_numeric",
                unit_field="normalized_unit",
                period_field="year_standardized",
                source_page_field="source_page",
                confidence_field="confidence_signal",
                trust_status_value="PENDING_AFTER_PARTIAL_HUMAN_REVIEW",
                review_status_value="REVIEW_REQUIRED",
                human_review_status_value="PENDING",
                prefix="342h_pending",
            )
        )

    if rows_344f.exists():
        rows_344f_json = _read_json_rows(rows_344f)
        for index, row in enumerate(rows_344f_json, start=1):
            inventory_rows.append(
                _finalize_inventory_row(
                    {
                        "inventory_row_id": _inventory_row_id("344f_strict_pending", index),
                        "source_artifact": "344F::review_rows_json",
                        "source_stage": "STRICT_HUMAN_REVIEW_PENDING_ROW",
                        "source_row_id": _safe_text(row.get("source_row_id") or row.get("review_row_id")),
                        "pdf_id": "",
                        "pdf_name": _safe_text(row.get("source_document")),
                        "table_id": "",
                        "row_index": "",
                        "column_name": "",
                        "metric_name": _safe_text(row.get("metric_name")),
                        "normalized_metric_name": _safe_text(row.get("normalized_metric_name")),
                        "value_raw": _safe_text(row.get("reported_value")),
                        "value_normalized": _safe_text(row.get("normalized_value")),
                        "unit": _safe_text(row.get("unit")),
                        "period": _safe_text(row.get("period")),
                        "source_page": _safe_text(row.get("source_page")),
                        "confidence": "",
                        "trust_status": _safe_text(row.get("trust_status")),
                        "review_status": "STRICT_HUMAN_REVIEW_PENDING_ROW",
                        "human_review_status": "STRICT_REVIEW_NOT_FILLED",
                        "is_metric_candidate": bool(
                            _safe_text(row.get("metric_name"))
                            or _safe_text(row.get("normalized_metric_name"))
                        ),
                        "is_normalized_metric": bool(_safe_text(row.get("normalized_metric_name"))),
                    }
                )
            )

    stage_status_rows = _build_stage_status_summary(inventory_rows)
    missing_field_rows = _build_missing_field_summary(inventory_rows)
    downstream_readiness_summary = _build_downstream_readiness_summary(inventory_rows)

    long_form_cell_count = (
        int(summary_342f_json.get("long_form_cell_count"))
        if summary_342f_json
        else _summary_from_rows(
            [row for row in inventory_rows if _safe_text(row["source_stage"]) == "LONG_FORM_CELL"]
        )["row_count"]
    )
    trusted_cell_count = (
        int(summary_342f_json.get("trusted_cell_count"))
        if summary_342f_json
        else _summary_from_rows(
            [row for row in inventory_rows if _safe_text(row["source_stage"]) == "TRUSTED_CELL"]
        )["row_count"]
    )
    review_required_count = (
        int(summary_342f_json.get("review_required_cell_count"))
        if summary_342f_json
        else sum(1 for row in inventory_rows if _safe_text(row["source_stage"]) == "REVIEW_REQUIRED")
    )
    rejected_or_excluded_count = (
        int(summary_342f_json.get("rejected_cell_count"))
        if summary_342f_json
        else sum(
            1 for row in inventory_rows if _safe_text(row["source_stage"]) == "REJECTED_OR_EXCLUDED"
        )
    )
    human_review_applied_count = (
        int(summary_342h_json.get("reviewed_row_count"))
        if summary_342h_json
        else sum(
            1 for row in inventory_rows if _safe_text(row["source_stage"]) == "HUMAN_REVIEW_APPLIED"
        )
    )
    strict_human_review_pending_row_count = (
        int(manifest_344f_json.get("strict_review_row_count"))
        if manifest_344f_json
        else sum(
            1
            for row in inventory_rows
            if _safe_text(row["source_stage"]) == "STRICT_HUMAN_REVIEW_PENDING_ROW"
        )
    )

    missing_unit_count = sum(1 for row in inventory_rows if not _safe_text(row["unit"]))
    missing_period_count = sum(1 for row in inventory_rows if not _safe_text(row["period"]))
    missing_source_page_count = sum(1 for row in inventory_rows if not _safe_text(row["source_page"]))
    missing_metric_name_count = sum(
        1
        for row in inventory_rows
        if not _safe_text(row["metric_name"]) and not _safe_text(row["normalized_metric_name"])
    )

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="345A",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_345a")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    manifest: Dict[str, Any] = {
        "decision": NOT_READY_DECISION_345A,
        "input_stage": INPUT_STAGE_345A,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "total_input_artifact_count": len(source_artifact_map),
        "readable_input_artifact_count": sum(1 for row in source_artifact_map if row["readable"]),
        "missing_input_artifact_count": sum(1 for row in source_artifact_map if not row["exists"]),
        "total_inventory_row_count": len(inventory_rows),
        "long_form_cell_count": long_form_cell_count,
        "trusted_cell_count": trusted_cell_count,
        "review_required_count": review_required_count,
        "rejected_or_excluded_count": rejected_or_excluded_count,
        "human_review_applied_count": human_review_applied_count,
        "strict_human_review_pending_row_count": strict_human_review_pending_row_count,
        "metric_candidate_row_count": sum(1 for row in inventory_rows if row["is_metric_candidate"]),
        "normalized_metric_row_count": sum(1 for row in inventory_rows if row["is_normalized_metric"]),
        "downstream_ready_candidate_count": downstream_readiness_summary["downstream_ready_candidate_count"],
        "missing_unit_count": missing_unit_count,
        "missing_period_count": missing_period_count,
        "missing_source_page_count": missing_source_page_count,
        "missing_metric_name_count": missing_metric_name_count,
        "unknown_stage_count": sum(
            1 for row in inventory_rows if _safe_text(row["source_stage"]) == "UNKNOWN_STAGE"
        ),
        "metric_limitations": [],
        "warnings": warnings,
        "output_dir": str(output_dir),
    }

    checks = [
        {
            "check_name": "inputs::342f_or_342g_present",
            "status": "PASS" if required_anchor_exists else "FAIL",
            "detail": json.dumps(
                {
                    "342f_exists": workbook_342f.exists(),
                    "342g_exists": workbook_342g.exists(),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "outputs::inventory_rows_generated",
            "status": "PASS" if len(inventory_rows) > 0 else "FAIL",
            "detail": json.dumps({"total_inventory_row_count": len(inventory_rows)}, ensure_ascii=False),
        },
        {
            "check_name": "claims::all_export_client_production_flags_false",
            "status": "PASS"
            if not manifest["formal_client_export_allowed"]
            and not manifest["client_ready"]
            and not manifest["production_ready"]
            and not manifest["global_strict_human_review_completed"]
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready/global_strict_human_review_completed must remain false",
        },
        {
            "check_name": "safety::no_upstream_write_back",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::protected_dirty_status_preserved",
            "status": "PASS" if protected_before == protected_after else "FAIL",
            "detail": json.dumps(protected_after, ensure_ascii=False),
        },
        {
            "check_name": "safety::protected_dirty_files_not_staged",
            "status": "PASS" if not protected_staged else "FAIL",
            "detail": json.dumps(protected_staged, ensure_ascii=False),
        },
        {
            "check_name": "safety::forbidden_paths_not_staged",
            "status": "PASS" if not forbidden_staged else "FAIL",
            "detail": json.dumps(forbidden_staged, ensure_ascii=False),
        },
        {
            "check_name": "warnings::optional_missing_inputs_allowed",
            "status": "PASS",
            "detail": json.dumps({"warning_count": len(warnings)}, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {"no_write_back_proof_passed": no_write_back_proof_passed},
                ensure_ascii=False,
            ),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    manifest["qa_fail_count"] = qa_fail_count
    manifest["no_write_back_proof_passed"] = no_write_back_proof_passed
    manifest["decision"] = READY_DECISION_345A if qa_fail_count == 0 else NOT_READY_DECISION_345A

    artifact_index_rows = [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "345A manifest with counts, warnings, and final gate boundary.",
        },
        {
            "artifact_name": SOURCE_ARTIFACT_MAP_FILE_NAME,
            "path": str(output_dir / SOURCE_ARTIFACT_MAP_FILE_NAME),
            "purpose": "Map of every 345A input artifact, existence, readability, and purpose.",
        },
        {
            "artifact_name": ROW_INVENTORY_JSON_FILE_NAME,
            "path": str(output_dir / ROW_INVENTORY_JSON_FILE_NAME),
            "purpose": "Full structured row inventory in JSON.",
        },
        {
            "artifact_name": ROW_INVENTORY_CSV_FILE_NAME,
            "path": str(output_dir / ROW_INVENTORY_CSV_FILE_NAME),
            "purpose": "Full structured row inventory in CSV.",
        },
        {
            "artifact_name": STAGE_STATUS_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / STAGE_STATUS_SUMMARY_JSON_FILE_NAME),
            "purpose": "Stage/status distribution in JSON.",
        },
        {
            "artifact_name": STAGE_STATUS_SUMMARY_CSV_FILE_NAME,
            "path": str(output_dir / STAGE_STATUS_SUMMARY_CSV_FILE_NAME),
            "purpose": "Stage/status distribution in CSV.",
        },
        {
            "artifact_name": MISSING_FIELD_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / MISSING_FIELD_SUMMARY_JSON_FILE_NAME),
            "purpose": "Missing-field hotspot summary in JSON.",
        },
        {
            "artifact_name": MISSING_FIELD_SUMMARY_CSV_FILE_NAME,
            "path": str(output_dir / MISSING_FIELD_SUMMARY_CSV_FILE_NAME),
            "purpose": "Missing-field hotspot summary in CSV.",
        },
        {
            "artifact_name": DOWNSTREAM_READINESS_SUMMARY_FILE_NAME,
            "path": str(output_dir / DOWNSTREAM_READINESS_SUMMARY_FILE_NAME),
            "purpose": "Inventory-only downstream readiness candidate summary.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_FILE_NAME),
            "purpose": "Narrative summary of counts, hotspots, and next steps.",
        },
        {
            "artifact_name": ARTIFACT_INDEX_FILE_NAME,
            "path": str(output_dir / ARTIFACT_INDEX_FILE_NAME),
            "purpose": "Index of all 345A outputs and how to use them.",
        },
        {
            "artifact_name": NEXT_PLAN_FILE_NAME,
            "path": str(output_dir / NEXT_PLAN_FILE_NAME),
            "purpose": "Recommended 345B-345E follow-up plan while keeping 344G waiting.",
        },
    ]

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    return {
        "manifest": manifest,
        "source_artifact_map": source_artifact_map,
        "row_inventory": inventory_rows,
        "stage_status_summary": stage_status_rows,
        "missing_field_summary": missing_field_rows,
        "downstream_readiness_summary": downstream_readiness_summary,
        "artifact_index_rows": artifact_index_rows,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
    }

