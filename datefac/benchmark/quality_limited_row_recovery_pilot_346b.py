from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from datefac.benchmark.quality_limited_row_recovery_pilot_346b_report import (
    render_artifact_index_markdown,
    render_executive_summary_markdown,
    render_next_plan_markdown,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345D = "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY"
READY_DECISION_346A = "VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY"
READY_DECISION_346A2 = "MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY"
READY_DECISION_346B = "QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY"
BLOCKED_DECISION_346B = "QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_BLOCKED"
INPUT_STAGE_346B = "POST_346A2_QUALITY_LIMITED_ROW_RECOVERY_PILOT"

DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR = Path(
    r"D:\_datefac\output\full_structured_demo_export_package_345d"
)
DEFAULT_VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_DIR = Path(
    r"D:\_datefac\output\vision_assisted_table_evidence_pilot_346a"
)
DEFAULT_MINERU_IMAGE_PATH_BINDING_FIX_346A2_DIR = Path(
    r"D:\_datefac\output\mineru_image_path_binding_fix_346a2"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\quality_limited_row_recovery_pilot_346b")

MANIFEST_FILE_NAME = "quality_limited_row_recovery_pilot_346b_manifest.json"
INPUT_ROWS_JSON_FILE_NAME = "quality_limited_row_recovery_pilot_346b_input_rows.json"
INPUT_ROWS_CSV_FILE_NAME = "quality_limited_row_recovery_pilot_346b_input_rows.csv"
VALUE_SANITIZER_RESULTS_JSON_FILE_NAME = "quality_limited_row_recovery_pilot_346b_value_sanitizer_results.json"
VALUE_SANITIZER_RESULTS_CSV_FILE_NAME = "quality_limited_row_recovery_pilot_346b_value_sanitizer_results.csv"
CONTEXT_INJECTION_RESULTS_JSON_FILE_NAME = "quality_limited_row_recovery_pilot_346b_context_injection_results.json"
CONTEXT_INJECTION_RESULTS_CSV_FILE_NAME = "quality_limited_row_recovery_pilot_346b_context_injection_results.csv"
EVIDENCE_ASSISTED_RESULTS_JSON_FILE_NAME = "quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.json"
EVIDENCE_ASSISTED_RESULTS_CSV_FILE_NAME = "quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.csv"
RECOVERED_ROWS_JSON_FILE_NAME = "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.json"
RECOVERED_ROWS_CSV_FILE_NAME = "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.csv"
STILL_LIMITED_ROWS_JSON_FILE_NAME = "quality_limited_row_recovery_pilot_346b_still_limited_rows.json"
STILL_LIMITED_ROWS_CSV_FILE_NAME = "quality_limited_row_recovery_pilot_346b_still_limited_rows.csv"
NEEDS_VLM_ROWS_JSON_FILE_NAME = "quality_limited_row_recovery_pilot_346b_needs_vlm_rows.json"
NEEDS_VLM_ROWS_CSV_FILE_NAME = "quality_limited_row_recovery_pilot_346b_needs_vlm_rows.csv"
NEEDS_HUMAN_ROWS_JSON_FILE_NAME = "quality_limited_row_recovery_pilot_346b_needs_human_review_rows.json"
NEEDS_HUMAN_ROWS_CSV_FILE_NAME = "quality_limited_row_recovery_pilot_346b_needs_human_review_rows.csv"
DOWNGRADED_ROWS_JSON_FILE_NAME = "quality_limited_row_recovery_pilot_346b_downgraded_excluded_rows.json"
DOWNGRADED_ROWS_CSV_FILE_NAME = "quality_limited_row_recovery_pilot_346b_downgraded_excluded_rows.csv"
RECOVERY_FAIL_REASONS_JSON_FILE_NAME = "quality_limited_row_recovery_pilot_346b_recovery_fail_reasons.json"
RECOVERY_FAIL_REASONS_CSV_FILE_NAME = "quality_limited_row_recovery_pilot_346b_recovery_fail_reasons.csv"
REAUDIT_SUMMARY_JSON_FILE_NAME = "quality_limited_row_recovery_pilot_346b_reaudit_summary.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "quality_limited_row_recovery_pilot_346b_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "quality_limited_row_recovery_pilot_346b_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "quality_limited_row_recovery_pilot_346b_next_plan.md"

INPUT_345D_MANIFEST_NAME = "full_structured_demo_export_package_345d_manifest.json"
INPUT_345D_QUALITY_LIMITED_ROWS_JSON_NAME = "full_structured_demo_export_package_345d_quality_limited_rows.json"
INPUT_345D_QUALITY_LIMITED_ROWS_CSV_NAME = "full_structured_demo_export_package_345d_quality_limited_rows.csv"
INPUT_345D_DEMO_ROWS_JSON_NAME = "full_structured_demo_export_package_345d_demo_rows.json"
INPUT_345D_DEMO_ROWS_CSV_NAME = "full_structured_demo_export_package_345d_demo_rows.csv"
INPUT_345D_QUALITY_CAVEATS_JSON_NAME = "full_structured_demo_export_package_345d_quality_caveats.json"
INPUT_345D_QUALITY_CAVEATS_MD_NAME = "full_structured_demo_export_package_345d_quality_caveats.md"
INPUT_345D_ALIAS_SIMULATION_SIDECAR_JSON_NAME = "full_structured_demo_export_package_345d_alias_simulation_sidecar.json"
INPUT_345D_ALIAS_SIMULATION_SIDECAR_CSV_NAME = "full_structured_demo_export_package_345d_alias_simulation_sidecar.csv"

INPUT_346A_MANIFEST_NAME = "vision_assisted_table_evidence_pilot_346a_manifest.json"
INPUT_346A_SELECTED_ROWS_JSON_NAME = "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json"
INPUT_346A_SELECTED_ROWS_CSV_NAME = "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.csv"
INPUT_346A_FIELD_REPAIR_TARGETS_JSON_NAME = "vision_assisted_table_evidence_pilot_346a_field_repair_targets.json"
INPUT_346A_FIELD_REPAIR_TARGETS_CSV_NAME = "vision_assisted_table_evidence_pilot_346a_field_repair_targets.csv"
INPUT_346A_CONFLICT_POLICY_MD_NAME = "vision_assisted_table_evidence_pilot_346a_conflict_handling_policy.md"

INPUT_346A2_MANIFEST_NAME = "mineru_image_path_binding_fix_346a2_manifest.json"
INPUT_346A2_BOUND_ROWS_JSON_NAME = "mineru_image_path_binding_fix_346a2_bound_rows.json"
INPUT_346A2_BOUND_ROWS_CSV_NAME = "mineru_image_path_binding_fix_346a2_bound_rows.csv"
INPUT_346A2_UNRESOLVED_ROWS_JSON_NAME = "mineru_image_path_binding_fix_346a2_unresolved_rows.json"
INPUT_346A2_UNRESOLVED_ROWS_CSV_NAME = "mineru_image_path_binding_fix_346a2_unresolved_rows.csv"
INPUT_346A2_IMAGE_STATUS_JSON_NAME = "mineru_image_path_binding_fix_346a2_image_resolution_status.json"
INPUT_346A2_IMAGE_STATUS_CSV_NAME = "mineru_image_path_binding_fix_346a2_image_resolution_status.csv"
INPUT_346A2_CONTEXT_INDEX_JSON_NAME = "mineru_image_path_binding_fix_346a2_json_md_context_index.json"
INPUT_346A2_CONTEXT_INDEX_CSV_NAME = "mineru_image_path_binding_fix_346a2_json_md_context_index.csv"
INPUT_346A2_VLM_REQUEST_PACKAGE_JSONL_NAME = "mineru_image_path_binding_fix_346a2_vlm_request_package.jsonl"
INPUT_346A2_BINDING_SUMMARY_JSON_NAME = "mineru_image_path_binding_fix_346a2_binding_summary.json"

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

FORBIDDEN_STAGE_PATHS = [
    "output",
    "temp",
    "input",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

OUTPUT_ARTIFACT_ROWS = [
    {"artifact_name": MANIFEST_FILE_NAME, "path": MANIFEST_FILE_NAME, "purpose": "Decision and QA manifest."},
    {"artifact_name": INPUT_ROWS_JSON_FILE_NAME, "path": INPUT_ROWS_JSON_FILE_NAME, "purpose": "Merged pilot input rows in JSON."},
    {"artifact_name": INPUT_ROWS_CSV_FILE_NAME, "path": INPUT_ROWS_CSV_FILE_NAME, "purpose": "Merged pilot input rows in CSV."},
    {"artifact_name": VALUE_SANITIZER_RESULTS_JSON_FILE_NAME, "path": VALUE_SANITIZER_RESULTS_JSON_FILE_NAME, "purpose": "Deterministic value sanitizer results in JSON."},
    {"artifact_name": VALUE_SANITIZER_RESULTS_CSV_FILE_NAME, "path": VALUE_SANITIZER_RESULTS_CSV_FILE_NAME, "purpose": "Deterministic value sanitizer results in CSV."},
    {"artifact_name": CONTEXT_INJECTION_RESULTS_JSON_FILE_NAME, "path": CONTEXT_INJECTION_RESULTS_JSON_FILE_NAME, "purpose": "Context inheritance results in JSON."},
    {"artifact_name": CONTEXT_INJECTION_RESULTS_CSV_FILE_NAME, "path": CONTEXT_INJECTION_RESULTS_CSV_FILE_NAME, "purpose": "Context inheritance results in CSV."},
    {"artifact_name": EVIDENCE_ASSISTED_RESULTS_JSON_FILE_NAME, "path": EVIDENCE_ASSISTED_RESULTS_JSON_FILE_NAME, "purpose": "Evidence-assisted recovery results in JSON."},
    {"artifact_name": EVIDENCE_ASSISTED_RESULTS_CSV_FILE_NAME, "path": EVIDENCE_ASSISTED_RESULTS_CSV_FILE_NAME, "purpose": "Evidence-assisted recovery results in CSV."},
    {"artifact_name": RECOVERED_ROWS_JSON_FILE_NAME, "path": RECOVERED_ROWS_JSON_FILE_NAME, "purpose": "Recovered demo candidate rows in JSON."},
    {"artifact_name": RECOVERED_ROWS_CSV_FILE_NAME, "path": RECOVERED_ROWS_CSV_FILE_NAME, "purpose": "Recovered demo candidate rows in CSV."},
    {"artifact_name": STILL_LIMITED_ROWS_JSON_FILE_NAME, "path": STILL_LIMITED_ROWS_JSON_FILE_NAME, "purpose": "Still quality-limited rows in JSON."},
    {"artifact_name": STILL_LIMITED_ROWS_CSV_FILE_NAME, "path": STILL_LIMITED_ROWS_CSV_FILE_NAME, "purpose": "Still quality-limited rows in CSV."},
    {"artifact_name": NEEDS_VLM_ROWS_JSON_FILE_NAME, "path": NEEDS_VLM_ROWS_JSON_FILE_NAME, "purpose": "Rows needing future VLM repair in JSON."},
    {"artifact_name": NEEDS_VLM_ROWS_CSV_FILE_NAME, "path": NEEDS_VLM_ROWS_CSV_FILE_NAME, "purpose": "Rows needing future VLM repair in CSV."},
    {"artifact_name": NEEDS_HUMAN_ROWS_JSON_FILE_NAME, "path": NEEDS_HUMAN_ROWS_JSON_FILE_NAME, "purpose": "Rows needing human review in JSON."},
    {"artifact_name": NEEDS_HUMAN_ROWS_CSV_FILE_NAME, "path": NEEDS_HUMAN_ROWS_CSV_FILE_NAME, "purpose": "Rows needing human review in CSV."},
    {"artifact_name": DOWNGRADED_ROWS_JSON_FILE_NAME, "path": DOWNGRADED_ROWS_JSON_FILE_NAME, "purpose": "Downgraded excluded rows in JSON."},
    {"artifact_name": DOWNGRADED_ROWS_CSV_FILE_NAME, "path": DOWNGRADED_ROWS_CSV_FILE_NAME, "purpose": "Downgraded excluded rows in CSV."},
    {"artifact_name": RECOVERY_FAIL_REASONS_JSON_FILE_NAME, "path": RECOVERY_FAIL_REASONS_JSON_FILE_NAME, "purpose": "Recovery fail reasons in JSON."},
    {"artifact_name": RECOVERY_FAIL_REASONS_CSV_FILE_NAME, "path": RECOVERY_FAIL_REASONS_CSV_FILE_NAME, "purpose": "Recovery fail reasons in CSV."},
    {"artifact_name": REAUDIT_SUMMARY_JSON_FILE_NAME, "path": REAUDIT_SUMMARY_JSON_FILE_NAME, "purpose": "Re-audit summary metrics and distributions."},
    {"artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME, "path": EXECUTIVE_SUMMARY_MD_FILE_NAME, "purpose": "Executive summary for 346B."},
    {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": ARTIFACT_INDEX_MD_FILE_NAME, "purpose": "Artifact index for 346B outputs."},
    {"artifact_name": NEXT_PLAN_MD_FILE_NAME, "path": NEXT_PLAN_MD_FILE_NAME, "purpose": "Recommended next step and boundary reminder."},
]

RATIO_MULTIPLE_METRICS = {
    "ev_to_ebitda",
    "quick_ratio",
    "debt_to_asset_ratio",
    "return_on_invested_capital",
    "ebitda_margin",
}
RATIO_MULTIPLE_KEYWORDS = [
    "ev/ebitda",
    "市盈率",
    "市净率",
    "净资产收益率",
    "roic",
    "roe",
    "margin",
    "比率",
    "收益率",
    "周转率",
    "回报率",
]
PER_SHARE_KEYWORDS = ["每股", "per share", "bps", "book value per share", "eps"]
PERCENT_UNIT_METRICS = {"return_on_invested_capital", "ebitda_margin", "debt_to_asset_ratio"}
PER_SHARE_METRICS = {"book_value_per_share"}
MISSING_MARKERS = {"", "--", "-", "—", "–", "n/a", "na", "不适用", "nan", "none"}
MISSING_UNIT_MARKERS = {"", "nan", "none", "null"}
PERCENT_ROW_KEYWORDS = ["margin", "收益率", "比率", "%", "周转率", "回报率"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_ledger_path() -> Path:
    milestone_dir = Path(r"D:\_datefac\docs\project_milestones")
    matches = sorted(milestone_dir.glob("PROJECT_MILESTONE_LEDGER_*.md"))
    if matches:
        return matches[0]
    return milestone_dir / "PROJECT_MILESTONE_LEDGER.md"


DEFAULT_LEDGER_PATH = _default_ledger_path()


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).strip().split())
    return "" if text.lower() == "nan" else text


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _safe_text(value).lower() in {"1", "true", "yes", "y"}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _load_json_or_csv_rows(*, json_path: Path, csv_path: Path, label: str) -> tuple[List[Dict[str, Any]], str]:
    if json_path.exists():
        payload = _read_json(json_path)
        if isinstance(payload, list):
            return [dict(row) for row in payload], "json"
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            return [dict(row) for row in payload["rows"]], "json"
        raise ValueError(f"{label} must be a JSON list or row package: {json_path}")
    if csv_path.exists():
        return _read_csv_rows(csv_path), "csv"
    raise FileNotFoundError(f"required row artifact missing for {label}: {json_path} / {csv_path}")


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


def _artifact_index_rows(output_dir: Path) -> List[Dict[str, str]]:
    return [{"artifact_name": row["artifact_name"], "path": str(output_dir / row["path"]), "purpose": row["purpose"]} for row in OUTPUT_ARTIFACT_ROWS]


def _normalize_text(value: Any) -> str:
    return _safe_text(value).lower()


def _split_issue_codes(value: Any) -> List[str]:
    text = _safe_text(value)
    if not text:
        return []
    tokens: List[str] = []
    for chunk in text.replace("|", ",").replace(";", ",").split(","):
        item = _safe_text(chunk).upper()
        if item:
            tokens.append(item)
    return tokens


def _is_missing(value: Any) -> bool:
    return _normalize_text(value) in MISSING_MARKERS


def _sanitize_numeric_value(raw_value: Any) -> Dict[str, Any]:
    raw_text = _safe_text(raw_value)
    normalized_text = (
        raw_text.replace("\u3000", " ")
        .replace("\xa0", " ")
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("，", ",")
    )
    stripped_text = normalized_text.strip()
    if _normalize_text(stripped_text) in MISSING_MARKERS:
        return {
            "raw_value": raw_text,
            "sanitized_value": "",
            "value_parse_status": "MISSING",
            "value_parse_error": "",
            "value_numeric_type": "MISSING",
            "percent_marker_detected": False,
            "parentheses_negative_detected": False,
        }

    percent_marker_detected = "%" in stripped_text or "pct" in stripped_text.lower()
    parentheses_negative_detected = stripped_text.startswith("(") and stripped_text.endswith(")")
    cleaned = stripped_text.replace(",", "")
    cleaned = cleaned.replace("%", "")
    cleaned = re.sub(r"\bpct\b", "", cleaned, flags=re.IGNORECASE).strip()
    if parentheses_negative_detected:
        cleaned = "-" + cleaned[1:-1].strip()

    normalized_number = cleaned
    try:
        number = float(normalized_number)
    except ValueError:
        return {
            "raw_value": raw_text,
            "sanitized_value": normalized_text,
            "value_parse_status": "FAILED",
            "value_parse_error": f"unparseable numeric token: {normalized_text}",
            "value_numeric_type": "UNKNOWN",
            "percent_marker_detected": percent_marker_detected,
            "parentheses_negative_detected": parentheses_negative_detected,
        }

    numeric_type = "INTEGER" if number.is_integer() else "FLOAT"
    sanitized_value = f"{int(number)}" if number.is_integer() else f"{number}"
    return {
        "raw_value": raw_text,
        "sanitized_value": sanitized_value,
        "value_parse_status": "PARSED",
        "value_parse_error": "",
        "value_numeric_type": numeric_type,
        "percent_marker_detected": percent_marker_detected,
        "parentheses_negative_detected": parentheses_negative_detected,
    }


def _metric_text(row: Dict[str, Any]) -> str:
    return " | ".join(
        [
            _safe_text(row.get("raw_metric_name")),
            _safe_text(row.get("demo_normalized_metric_name")),
            _safe_text(row.get("context_snippet")),
        ]
    ).lower()


def _metric_label_text(row: Dict[str, Any]) -> str:
    return " | ".join(
        [
            _safe_text(row.get("raw_metric_name")),
            _safe_text(row.get("demo_normalized_metric_name")),
        ]
    ).lower()


def _is_ratio_multiple_row(row: Dict[str, Any]) -> bool:
    metric_name = _normalize_text(row.get("demo_normalized_metric_name"))
    if metric_name in RATIO_MULTIPLE_METRICS:
        return True
    label_text = _metric_label_text(row)
    full_text = _metric_text(row)
    if any(keyword in label_text for keyword in RATIO_MULTIPLE_KEYWORDS):
        return True
    return bool(re.search(r"(?<![a-z0-9])(pe|pb|roe)(?![a-z0-9])", full_text))


def _is_per_share_row(row: Dict[str, Any]) -> bool:
    metric_name = _normalize_text(row.get("demo_normalized_metric_name"))
    if metric_name in PER_SHARE_METRICS:
        return True
    text = _metric_text(row)
    return any(keyword in text for keyword in PER_SHARE_KEYWORDS)


def _row_supports_percent(row: Dict[str, Any], sanitizer_result: Dict[str, Any]) -> bool:
    metric_name = _normalize_text(row.get("demo_normalized_metric_name"))
    if metric_name in PERCENT_UNIT_METRICS:
        return True
    if sanitizer_result.get("percent_marker_detected"):
        return True
    text = _metric_text(row)
    return any(keyword in text for keyword in PERCENT_ROW_KEYWORDS)


def _table_body_from_context(row: Dict[str, Any]) -> str:
    snippet = _safe_text(row.get("context_snippet"))
    return snippet.lower()


def _extract_header_period_tokens(row: Dict[str, Any]) -> List[str]:
    table_body = _table_body_from_context(row)
    tokens = sorted(set(re.findall(r"(20\d{2}(?:[AE])?)", table_body)))
    period = _safe_text(row.get("period"))
    if period and period not in tokens:
        tokens.append(period)
    return tokens


def _unit_missing(row: Dict[str, Any]) -> bool:
    return _normalize_text(row.get("unit")) in MISSING_UNIT_MARKERS


def _apply_context_inheritance(row: Dict[str, Any], sanitizer_result: Dict[str, Any]) -> Dict[str, Any]:
    inherited_unit = _safe_text(row.get("unit"))
    unit_repair_action = "NO_CHANGE"
    unit_repair_source = "EXISTING_ROW"
    unit_repair_confidence = "UNCHANGED" if inherited_unit else "LOW"
    context_notes: List[str] = []

    if _unit_missing(row):
        if _is_ratio_multiple_row(row):
            inherited_unit = "%" if _row_supports_percent(row, sanitizer_result) else ""
            unit_repair_action = "UNIT_NOT_APPLICABLE_RATIO_MULTIPLE" if not inherited_unit else "UNIT_PERCENT_FROM_RATIO_CONTEXT"
            unit_repair_source = "ROW_METRIC_RULE"
            unit_repair_confidence = "HIGH"
            context_notes.append("Ratio/multiple row kept free of monetary unit.")
        elif _is_per_share_row(row):
            table_body = _table_body_from_context(row)
            if "每股收益（元）" in table_body or "每股净资产" in table_body or "（元）" in _safe_text(row.get("raw_metric_name")):
                inherited_unit = "元"
                unit_repair_action = "UNIT_INFERRED_PER_SHARE"
                unit_repair_source = "ROW_LABEL_OR_TABLE_BODY"
                unit_repair_confidence = "MEDIUM"
                context_notes.append("Per-share metric inherited row-level currency unit.")
            else:
                unit_repair_action = "UNIT_REQUIRES_HUMAN_CONFIRMATION"
                unit_repair_source = "INSUFFICIENT_PER_SHARE_CONTEXT"
                unit_repair_confidence = "LOW"
                context_notes.append("Per-share metric lacks safe unit evidence.")
        else:
            table_body = _table_body_from_context(row)
            label_text = _safe_text(row.get("raw_metric_name"))
            if "（百万元）" in label_text or "(百万元)" in label_text or "百万元" in table_body:
                inherited_unit = "百万元"
                unit_repair_action = "UNIT_INFERRED_MONETARY"
                unit_repair_source = "ROW_LABEL_OR_TABLE_BODY"
                unit_repair_confidence = "MEDIUM"
                context_notes.append("Monetary unit inferred from row label/table body.")
            elif "（亿元）" in label_text or "(亿元)" in label_text or "亿元" in table_body:
                inherited_unit = "亿元"
                unit_repair_action = "UNIT_INFERRED_MONETARY"
                unit_repair_source = "ROW_LABEL_OR_TABLE_BODY"
                unit_repair_confidence = "MEDIUM"
                context_notes.append("Monetary unit inferred from row label/table body.")
            else:
                unit_repair_action = "UNIT_UNRESOLVED"
                unit_repair_source = "NO_SAFE_CONTEXT"
                unit_repair_confidence = "LOW"
                context_notes.append("No safe deterministic unit context found.")

    period_repair_action = "NO_CHANGE"
    period_repair_source = "EXISTING_ROW"
    period_repair_confidence = "UNCHANGED" if _safe_text(row.get("period")) else "LOW"
    repaired_period = _safe_text(row.get("period"))
    header_period_tokens = _extract_header_period_tokens(row)
    if not repaired_period and header_period_tokens:
        repaired_period = header_period_tokens[0]
        period_repair_action = "PERIOD_INFERRED_FROM_HEADER"
        period_repair_source = "TABLE_HEADER_CONTEXT"
        period_repair_confidence = "MEDIUM"
        context_notes.append("Period inherited from table header tokens.")

    return {
        "inherited_unit": inherited_unit,
        "unit_repair_action": unit_repair_action,
        "unit_repair_source": unit_repair_source,
        "unit_repair_confidence": unit_repair_confidence,
        "repaired_period": repaired_period,
        "period_repair_action": period_repair_action,
        "period_repair_source": period_repair_source,
        "period_repair_confidence": period_repair_confidence,
        "header_period_tokens": header_period_tokens,
        "context_notes": " | ".join(context_notes),
    }


def _evidence_row_from_inputs(row: Dict[str, Any], has_vlm_request: bool) -> Dict[str, Any]:
    image_bound = _bool_value(row.get("image_bound"))
    context_available = _bool_value(row.get("context_available"))
    image_evidence_type = _safe_text(row.get("image_evidence_type"))
    chosen_image_path = _safe_text(row.get("chosen_image_path"))
    json_context_path = _safe_text(row.get("json_context_path"))
    md_context_path = _safe_text(row.get("md_context_path"))
    neighbor_rows = row.get("neighbor_context_rows") if isinstance(row.get("neighbor_context_rows"), list) else []

    if image_bound:
        recovery_action = "IMAGE_AND_CONTEXT_BOUND"
        evidence_confidence = "HIGH"
    elif context_available:
        recovery_action = "TEXT_CONTEXT_ONLY"
        evidence_confidence = "MEDIUM"
    else:
        recovery_action = "NO_BOUND_EVIDENCE"
        evidence_confidence = "LOW"

    return {
        "image_bound": image_bound,
        "image_evidence_type": image_evidence_type,
        "chosen_image_path": chosen_image_path,
        "json_context_path": json_context_path,
        "md_context_path": md_context_path,
        "context_available": context_available,
        "neighbor_context_rows_count": len(neighbor_rows),
        "evidence_assisted_recovery_action": recovery_action,
        "evidence_confidence": evidence_confidence,
        "future_vlm_request_available": has_vlm_request,
    }


def _rerank_row(
    row: Dict[str, Any],
    sanitizer_result: Dict[str, Any],
    context_result: Dict[str, Any],
    evidence_result: Dict[str, Any],
    *,
    strict_promotion: bool,
) -> Dict[str, Any]:
    fail_reasons: List[str] = []
    recovery_actions: List[str] = []
    parse_ok = sanitizer_result.get("value_parse_status") in {"PARSED", "MISSING"} and not (
        sanitizer_result.get("value_parse_status") == "MISSING" and not _is_missing(row.get("value"))
    )
    metric_usable = bool(_safe_text(row.get("demo_normalized_metric_name")))
    period_available = bool(context_result.get("repaired_period"))
    evidence_available = evidence_result.get("image_bound") or evidence_result.get("context_available")
    high_severity = _normalize_text(row.get("quality_severity")) == "high"
    has_human_pending = "HUMAN_REVIEW_PENDING" in _split_issue_codes(row.get("quality_issue_codes"))

    repaired_unit = _safe_text(context_result.get("inherited_unit"))
    unit_action = _safe_text(context_result.get("unit_repair_action"))
    unit_ok = bool(repaired_unit) or unit_action in {
        "UNIT_NOT_APPLICABLE_RATIO_MULTIPLE",
        "UNIT_PERCENT_FROM_RATIO_CONTEXT",
    }

    if sanitizer_result.get("value_parse_status") == "PARSED":
        recovery_actions.append("VALUE_SANITIZED")
    if unit_action in {"UNIT_INFERRED_PER_SHARE", "UNIT_INFERRED_MONETARY", "UNIT_PERCENT_FROM_RATIO_CONTEXT"}:
        recovery_actions.append(unit_action)
    if unit_action == "UNIT_NOT_APPLICABLE_RATIO_MULTIPLE":
        recovery_actions.append("UNIT_NOT_APPLICABLE")
    if context_result.get("period_repair_action") == "PERIOD_INFERRED_FROM_HEADER":
        recovery_actions.append("PERIOD_INHERITED")
    if evidence_result.get("image_bound"):
        recovery_actions.append("IMAGE_EVIDENCE_BOUND")
    elif evidence_result.get("context_available"):
        recovery_actions.append("TEXT_CONTEXT_BOUND")

    if not parse_ok:
        fail_reasons.append("UNPARSEABLE_VALUE")
    if not metric_usable:
        fail_reasons.append("MISSING_NORMALIZED_METRIC")
    if not unit_ok:
        fail_reasons.append("UNRESOLVED_UNIT")
    if not period_available:
        fail_reasons.append("UNRESOLVED_PERIOD")
    if not evidence_available:
        fail_reasons.append("NO_BOUND_EVIDENCE")

    if high_severity and strict_promotion:
        fail_reasons.append("STRICT_PROMOTION_BLOCKED_HIGH_SEVERITY")

    rerank_status = "STILL_QUALITY_LIMITED"
    promotion_reason = "quality-limited row still has deterministic gaps"

    if evidence_result.get("image_bound") and evidence_result.get("future_vlm_request_available"):
        if parse_ok and metric_usable and unit_ok and period_available and not strict_promotion:
            rerank_status = "RECOVERED_DEMO_CANDIDATE"
            promotion_reason = "bounded image/context evidence plus deterministic repairs made the row demo-safe"
        elif parse_ok and metric_usable and period_available and not unit_ok:
            rerank_status = "NEEDS_VLM_REPAIR"
            promotion_reason = "image evidence exists but unit/header alignment still needs bounded vision review"
    elif evidence_result.get("context_available"):
        if parse_ok and metric_usable and unit_ok and period_available and not high_severity and not strict_promotion:
            rerank_status = "RECOVERED_DEMO_CANDIDATE"
            promotion_reason = "json/md context plus deterministic repair made the row demo-safe"
        elif not unit_ok:
            rerank_status = "STILL_QUALITY_LIMITED"
            promotion_reason = "context exists but unit remains unresolved"
    else:
        if parse_ok and metric_usable and unit_ok and period_available and has_human_pending:
            rerank_status = "NEEDS_HUMAN_REVIEW"
            promotion_reason = "deterministic repair worked but source evidence remains too weak"

    if rerank_status == "STILL_QUALITY_LIMITED" and evidence_result.get("image_bound") and evidence_result.get("future_vlm_request_available"):
        rerank_status = "NEEDS_VLM_REPAIR"
        promotion_reason = "bounded image exists and unresolved repair should wait for future vision response ingestion"

    if rerank_status == "STILL_QUALITY_LIMITED" and not evidence_available and unit_ok and metric_usable and parse_ok:
        rerank_status = "NEEDS_HUMAN_REVIEW"
        promotion_reason = "deterministic repair is plausible but there is no bound evidence to safely promote"

    if rerank_status == "RECOVERED_DEMO_CANDIDATE" and has_human_pending:
        recovery_actions.append("DEMO_ONLY_PROMOTION")

    return {
        "final_status": rerank_status,
        "promotion_reason": promotion_reason,
        "top_recovery_actions": recovery_actions,
        "top_fail_reasons": fail_reasons,
    }


def _default_ledger_entry_present(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return "## 346B Quality-Limited Row Recovery Pilot" in ledger_path.read_text(encoding="utf-8")


def _build_346b_ledger_entry(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "## 346B Quality-Limited Row Recovery Pilot",
            "",
            "Status: completed",
            "",
            f"- decision: {manifest.get('decision', '')}",
            f"- input_345d_dir: {manifest.get('input_345d_dir', '')}",
            f"- input_346a_dir: {manifest.get('input_346a_dir', '')}",
            f"- input_346a2_dir: {manifest.get('input_346a2_dir', '')}",
            f"- output_dir: {manifest.get('output_dir', '')}",
            f"- full_quality_limited_row_count: {manifest.get('full_quality_limited_row_count', 0)}",
            f"- pilot_input_row_count: {manifest.get('pilot_input_row_count', 0)}",
            f"- image_bound_input_count: {manifest.get('image_bound_input_count', 0)}",
            f"- json_md_context_bound_input_count: {manifest.get('json_md_context_bound_input_count', 0)}",
            f"- sanitized_value_success_count: {manifest.get('sanitized_value_success_count', 0)}",
            f"- unit_injection_success_count: {manifest.get('unit_injection_success_count', 0)}",
            f"- period_injection_success_count: {manifest.get('period_injection_success_count', 0)}",
            f"- evidence_assisted_recovery_success_count: {manifest.get('evidence_assisted_recovery_success_count', 0)}",
            f"- recovered_demo_candidate_count: {manifest.get('recovered_demo_candidate_count', 0)}",
            f"- still_quality_limited_count: {manifest.get('still_quality_limited_count', 0)}",
            f"- needs_vlm_count: {manifest.get('needs_vlm_count', 0)}",
            f"- needs_human_review_count: {manifest.get('needs_human_review_count', 0)}",
            f"- downgraded_excluded_count: {manifest.get('downgraded_excluded_count', 0)}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- no_write_back_proof_passed: {manifest.get('no_write_back_proof_passed', False)}",
            f"- gate_status: formal_client_export_allowed={manifest.get('formal_client_export_allowed', False)}, client_ready={manifest.get('client_ready', False)}, production_ready={manifest.get('production_ready', False)}",
            f"- next_recommended_step: {manifest.get('recommended_next_step', '')}",
        ]
    )


def append_346b_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    if _default_ledger_entry_present(ledger_path):
        return False
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    addition = _build_346b_ledger_entry(manifest)
    prefix = "\n\n" if existing and not existing.endswith("\n\n") else ""
    if existing.endswith("\n"):
        prefix = "\n" if not existing.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(existing + prefix + addition + "\n", encoding="utf-8")
    return True


def build_quality_limited_row_recovery_pilot_346b(
    *,
    full_structured_demo_export_package_345d_dir: Path,
    vision_assisted_table_evidence_pilot_346a_dir: Path,
    mineru_image_path_binding_fix_346a2_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    max_pilot_rows: int = 100,
    require_image_bound: bool = False,
    include_json_md_context_only: bool = True,
    strict_promotion: bool = False,
    max_context_chars: int = 4000,
) -> Dict[str, Any]:
    if not full_structured_demo_export_package_345d_dir.exists():
        raise FileNotFoundError(f"345D input directory missing: {full_structured_demo_export_package_345d_dir}")
    if not vision_assisted_table_evidence_pilot_346a_dir.exists():
        raise FileNotFoundError(f"346A input directory missing: {vision_assisted_table_evidence_pilot_346a_dir}")
    if not mineru_image_path_binding_fix_346a2_dir.exists():
        raise FileNotFoundError(f"346A2 input directory missing: {mineru_image_path_binding_fix_346a2_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345d_path = full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME
    quality_rows_json_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_LIMITED_ROWS_JSON_NAME
    quality_rows_csv_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_LIMITED_ROWS_CSV_NAME
    demo_rows_json_path = full_structured_demo_export_package_345d_dir / INPUT_345D_DEMO_ROWS_JSON_NAME
    demo_rows_csv_path = full_structured_demo_export_package_345d_dir / INPUT_345D_DEMO_ROWS_CSV_NAME
    quality_caveats_json_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_CAVEATS_JSON_NAME
    quality_caveats_md_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_CAVEATS_MD_NAME
    alias_sidecar_json_path = full_structured_demo_export_package_345d_dir / INPUT_345D_ALIAS_SIMULATION_SIDECAR_JSON_NAME
    alias_sidecar_csv_path = full_structured_demo_export_package_345d_dir / INPUT_345D_ALIAS_SIMULATION_SIDECAR_CSV_NAME

    manifest_346a_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_MANIFEST_NAME
    selected_rows_json_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_SELECTED_ROWS_JSON_NAME
    selected_rows_csv_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_SELECTED_ROWS_CSV_NAME
    field_targets_json_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_FIELD_REPAIR_TARGETS_JSON_NAME
    field_targets_csv_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_FIELD_REPAIR_TARGETS_CSV_NAME
    conflict_policy_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_CONFLICT_POLICY_MD_NAME

    manifest_346a2_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_MANIFEST_NAME
    bound_rows_json_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_BOUND_ROWS_JSON_NAME
    bound_rows_csv_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_BOUND_ROWS_CSV_NAME
    unresolved_rows_json_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_UNRESOLVED_ROWS_JSON_NAME
    unresolved_rows_csv_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_UNRESOLVED_ROWS_CSV_NAME
    image_status_json_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_IMAGE_STATUS_JSON_NAME
    image_status_csv_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_IMAGE_STATUS_CSV_NAME
    context_index_json_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_CONTEXT_INDEX_JSON_NAME
    context_index_csv_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_CONTEXT_INDEX_CSV_NAME
    vlm_request_jsonl_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_VLM_REQUEST_PACKAGE_JSONL_NAME
    binding_summary_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_BINDING_SUMMARY_JSON_NAME

    manifest_345d = _read_json(manifest_345d_path)
    manifest_346a = _read_json(manifest_346a_path)
    manifest_346a2 = _read_json(manifest_346a2_path)

    quality_rows, quality_rows_source = _load_json_or_csv_rows(
        json_path=quality_rows_json_path,
        csv_path=quality_rows_csv_path,
        label="345D quality-limited rows",
    )
    demo_rows, demo_rows_source = _load_json_or_csv_rows(
        json_path=demo_rows_json_path,
        csv_path=demo_rows_csv_path,
        label="345D demo rows",
    )
    selected_rows, selected_rows_source = _load_json_or_csv_rows(
        json_path=selected_rows_json_path,
        csv_path=selected_rows_csv_path,
        label="346A selected pilot rows",
    )
    field_target_rows, field_target_source = _load_json_or_csv_rows(
        json_path=field_targets_json_path,
        csv_path=field_targets_csv_path,
        label="346A field repair targets",
    )
    bound_rows, bound_rows_source = _load_json_or_csv_rows(
        json_path=bound_rows_json_path,
        csv_path=bound_rows_csv_path,
        label="346A2 bound rows",
    )
    unresolved_rows, unresolved_rows_source = _load_json_or_csv_rows(
        json_path=unresolved_rows_json_path,
        csv_path=unresolved_rows_csv_path,
        label="346A2 unresolved rows",
    )
    image_status_rows, image_status_source = _load_json_or_csv_rows(
        json_path=image_status_json_path,
        csv_path=image_status_csv_path,
        label="346A2 image status rows",
    )
    context_index_rows, context_index_source = _load_json_or_csv_rows(
        json_path=context_index_json_path,
        csv_path=context_index_csv_path,
        label="346A2 context index rows",
    )

    quality_caveats = _read_json(quality_caveats_json_path)
    _ = quality_caveats_md_path.read_text(encoding="utf-8")
    _ = conflict_policy_path.read_text(encoding="utf-8")
    alias_sidecar_rows, alias_sidecar_source = _load_json_or_csv_rows(
        json_path=alias_sidecar_json_path,
        csv_path=alias_sidecar_csv_path,
        label="345D alias simulation sidecar",
    )
    binding_summary = _read_json(binding_summary_path)
    vlm_request_rows = _read_jsonl(vlm_request_jsonl_path)

    files_read = [
        str(path)
        for path in [
            manifest_345d_path,
            quality_rows_json_path,
            quality_rows_csv_path,
            demo_rows_json_path,
            demo_rows_csv_path,
            quality_caveats_json_path,
            quality_caveats_md_path,
            alias_sidecar_json_path,
            alias_sidecar_csv_path,
            manifest_346a_path,
            selected_rows_json_path,
            selected_rows_csv_path,
            field_targets_json_path,
            field_targets_csv_path,
            conflict_policy_path,
            manifest_346a2_path,
            bound_rows_json_path,
            bound_rows_csv_path,
            unresolved_rows_json_path,
            unresolved_rows_csv_path,
            image_status_json_path,
            image_status_csv_path,
            context_index_json_path,
            context_index_csv_path,
            vlm_request_jsonl_path,
            binding_summary_path,
        ]
        if path.exists()
    ]

    input_paths = [Path(path) for path in files_read if Path(path).is_file()]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    quality_rows_by_source = {_safe_text(row.get("source_row_id")): row for row in quality_rows if _safe_text(row.get("source_row_id"))}
    selected_rows_by_source = {_safe_text(row.get("source_row_id")): row for row in selected_rows if _safe_text(row.get("source_row_id"))}
    field_targets_by_pilot: Dict[str, List[str]] = {}
    for row in field_target_rows:
        pilot_row_id = _safe_text(row.get("pilot_row_id"))
        if pilot_row_id:
            field_targets_by_pilot.setdefault(pilot_row_id, []).append(_safe_text(row.get("target_field_type")))
    vlm_request_ids = {_safe_text(row.get("pilot_row_id")) for row in vlm_request_rows if _safe_text(row.get("pilot_row_id"))}

    candidate_rows = bound_rows[:]
    if include_json_md_context_only:
        candidate_rows.extend(unresolved_rows)

    merged_input_rows: List[Dict[str, Any]] = []
    used_source_ids: set[str] = set()
    for row in candidate_rows:
        source_row_id = _safe_text(row.get("source_row_id"))
        if source_row_id in used_source_ids:
            continue
        used_source_ids.add(source_row_id)
        base_row = dict(quality_rows_by_source.get(source_row_id, {}))
        selected_row = dict(selected_rows_by_source.get(source_row_id, {}))
        merged = {**base_row, **selected_row, **dict(row)}
        if require_image_bound and not _bool_value(merged.get("image_bound")):
            continue
        merged["target_field_types"] = field_targets_by_pilot.get(_safe_text(merged.get("pilot_row_id")), merged.get("target_field_types", []))
        merged["future_vlm_request_available"] = _safe_text(merged.get("pilot_row_id")) in vlm_request_ids
        context_snippet = _safe_text(merged.get("context_snippet"))
        merged["context_snippet"] = context_snippet[:max_context_chars]
        merged_input_rows.append(merged)
        if len(merged_input_rows) >= max_pilot_rows:
            break

    value_results: List[Dict[str, Any]] = []
    context_results: List[Dict[str, Any]] = []
    evidence_results: List[Dict[str, Any]] = []
    final_rows: List[Dict[str, Any]] = []
    fail_reason_rows: List[Dict[str, Any]] = []

    status_counter: Counter[str] = Counter()
    recovery_action_counter: Counter[str] = Counter()
    fail_reason_counter: Counter[str] = Counter()

    for row in merged_input_rows:
        sanitizer_result = _sanitize_numeric_value(row.get("value"))
        value_row = {**row, **sanitizer_result}
        value_results.append(value_row)

        context_result = _apply_context_inheritance(row, sanitizer_result)
        context_row = {**row, **sanitizer_result, **context_result}
        context_results.append(context_row)

        evidence_result = _evidence_row_from_inputs(row, _bool_value(row.get("future_vlm_request_available")))
        evidence_row = {**row, **sanitizer_result, **context_result, **evidence_result}
        evidence_results.append(evidence_row)

        rerank_result = _rerank_row(
            row,
            sanitizer_result,
            context_result,
            evidence_result,
            strict_promotion=strict_promotion,
        )
        final_row = {
            **row,
            **sanitizer_result,
            **context_result,
            **evidence_result,
            **rerank_result,
            "recovered_demo_candidate": rerank_result["final_status"] == "RECOVERED_DEMO_CANDIDATE",
            "sidecar_suggestion_only": True,
            "do_not_apply_upstream": True,
        }
        final_rows.append(final_row)
        status_counter[rerank_result["final_status"]] += 1
        for action in rerank_result["top_recovery_actions"]:
            recovery_action_counter[action] += 1
        for reason in rerank_result["top_fail_reasons"]:
            fail_reason_counter[reason] += 1
        for reason in rerank_result["top_fail_reasons"]:
            fail_reason_rows.append(
                {
                    "pilot_row_id": row.get("pilot_row_id"),
                    "source_row_id": row.get("source_row_id"),
                    "source_pdf_name": row.get("source_pdf_name"),
                    "final_status": rerank_result["final_status"],
                    "fail_reason": reason,
                }
            )

    recovered_rows = [row for row in final_rows if row["final_status"] == "RECOVERED_DEMO_CANDIDATE"]
    still_limited_rows = [row for row in final_rows if row["final_status"] == "STILL_QUALITY_LIMITED"]
    needs_vlm_rows = [row for row in final_rows if row["final_status"] == "NEEDS_VLM_REPAIR"]
    needs_human_rows = [row for row in final_rows if row["final_status"] == "NEEDS_HUMAN_REVIEW"]
    downgraded_rows = [row for row in final_rows if row["final_status"] == "DOWNGRADED_EXCLUDED"]

    image_bound_input_count = sum(1 for row in merged_input_rows if _bool_value(row.get("image_bound")))
    json_md_context_bound_input_count = sum(1 for row in merged_input_rows if _bool_value(row.get("context_available")))
    unit_injection_attempt_count = sum(1 for row in merged_input_rows if _unit_missing(row))
    unit_injection_success_count = sum(
        1
        for row in final_rows
        if _safe_text(row.get("unit_repair_action")) in {
            "UNIT_INFERRED_PER_SHARE",
            "UNIT_INFERRED_MONETARY",
            "UNIT_PERCENT_FROM_RATIO_CONTEXT",
        }
    )
    unit_not_applicable_count = sum(
        1 for row in final_rows if _safe_text(row.get("unit_repair_action")) == "UNIT_NOT_APPLICABLE_RATIO_MULTIPLE"
    )
    period_injection_attempt_count = sum(1 for row in merged_input_rows if not _safe_text(row.get("period")))
    period_injection_success_count = sum(
        1 for row in final_rows if _safe_text(row.get("period_repair_action")) == "PERIOD_INFERRED_FROM_HEADER"
    )
    evidence_assisted_recovery_success_count = sum(
        1 for row in final_rows if row["final_status"] == "RECOVERED_DEMO_CANDIDATE" and (_bool_value(row.get("image_bound")) or _bool_value(row.get("context_available")))
    )

    reaudit_summary = {
        "status_distribution": dict(sorted(status_counter.items())),
        "top_recovery_actions": dict(recovery_action_counter.most_common(10)),
        "top_fail_reasons": dict(fail_reason_counter.most_common(10)),
        "pilot_input_row_count": len(merged_input_rows),
        "bound_row_count_from_346a2": len(bound_rows),
        "unresolved_row_count_from_346a2": len(unresolved_rows),
        "quality_rows_source": quality_rows_source,
        "demo_rows_source": demo_rows_source,
        "selected_rows_source": selected_rows_source,
        "field_target_source": field_target_source,
        "bound_rows_source": bound_rows_source,
        "unresolved_rows_source": unresolved_rows_source,
        "image_status_source": image_status_source,
        "context_index_source": context_index_source,
        "alias_sidecar_source": alias_sidecar_source,
    }

    manifest = {
        "decision": READY_DECISION_346B,
        "input_stage": INPUT_STAGE_346B,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "input_345d_decision": _safe_text(manifest_345d.get("decision")),
        "input_346a_decision": _safe_text(manifest_346a.get("decision")),
        "input_346a2_decision": _safe_text(manifest_346a2.get("decision")),
        "input_345d_dir": str(full_structured_demo_export_package_345d_dir),
        "input_346a_dir": str(vision_assisted_table_evidence_pilot_346a_dir),
        "input_346a2_dir": str(mineru_image_path_binding_fix_346a2_dir),
        "output_dir": str(output_dir),
        "full_quality_limited_row_count": int(manifest_345d.get("quality_limited_row_count", len(quality_rows))),
        "pilot_input_row_count": len(merged_input_rows),
        "image_bound_input_count": image_bound_input_count,
        "json_md_context_bound_input_count": json_md_context_bound_input_count,
        "value_sanitizer_attempt_count": len(merged_input_rows),
        "sanitized_value_success_count": sum(1 for row in value_results if row["value_parse_status"] == "PARSED"),
        "sanitized_value_failure_count": sum(1 for row in value_results if row["value_parse_status"] == "FAILED"),
        "unit_injection_attempt_count": unit_injection_attempt_count,
        "unit_injection_success_count": unit_injection_success_count,
        "unit_not_applicable_count": unit_not_applicable_count,
        "period_injection_attempt_count": period_injection_attempt_count,
        "period_injection_success_count": period_injection_success_count,
        "evidence_assisted_recovery_attempt_count": len(merged_input_rows),
        "evidence_assisted_recovery_success_count": evidence_assisted_recovery_success_count,
        "recovered_demo_candidate_count": len(recovered_rows),
        "still_quality_limited_count": len(still_limited_rows),
        "needs_vlm_count": len(needs_vlm_rows),
        "needs_human_review_count": len(needs_human_rows),
        "downgraded_excluded_count": len(downgraded_rows),
        "live_vlm_call_count": 0,
        "vlm_response_count": 0,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_export_generated": False,
        "demo_export_only": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "upstream_data_mutated": False,
        "milestone_ledger_updated": False,
        "max_pilot_rows": max_pilot_rows,
        "require_image_bound": require_image_bound,
        "include_json_md_context_only": include_json_md_context_only,
        "strict_promotion": strict_promotion,
        "max_context_chars": max_context_chars,
        "recommended_next_step": "",
        "recommended_next_step_reason": "",
        "generated_at_utc": _utc_now(),
    }

    if len(recovered_rows) == 0:
        manifest["recommended_next_step"] = "346B2 Recovery Rule Refinement"
        manifest["recommended_next_step_reason"] = "Deterministic/context recovery closed few pilot rows, so rule refinement should precede any live vision spend."
    elif len(needs_vlm_rows) > 0:
        manifest["recommended_next_step"] = "346C0 Live VLM Pilot Request Execution"
        manifest["recommended_next_step_reason"] = "Bound image rows remain and future vision repair can be considered only after explicit approval."
    else:
        manifest["recommended_next_step"] = "345G Demo Presentation Slide Outline"
        manifest["recommended_next_step_reason"] = "Recovered pilot rows are demo-only and can feed narrative/presentation work without opening formal export gates."

    validation_checks = [
        manifest["input_345d_decision"] == READY_DECISION_345D,
        int(manifest_345d.get("qa_fail_count", 1)) == 0,
        _bool_value(manifest_345d.get("demo_export_only")) is True,
        _bool_value(manifest_345d.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_345d.get("client_ready")) is False,
        _bool_value(manifest_345d.get("production_ready")) is False,
        manifest["input_346a_decision"] == READY_DECISION_346A,
        int(manifest_346a.get("qa_fail_count", 1)) == 0,
        manifest["input_346a2_decision"] == READY_DECISION_346A2,
        int(manifest_346a2.get("qa_fail_count", 1)) == 0,
        int(manifest_346a2.get("live_vlm_call_count", 1)) == 0,
        _bool_value(manifest_346a2.get("upstream_data_mutated")) is False,
        manifest["pilot_input_row_count"] <= max_pilot_rows,
        manifest["pilot_input_row_count"] == len(final_rows),
        manifest["pilot_input_row_count"] == len(value_results),
        manifest["pilot_input_row_count"] == len(context_results),
        manifest["pilot_input_row_count"] == len(evidence_results),
        manifest["pilot_input_row_count"] == (
            manifest["recovered_demo_candidate_count"]
            + manifest["still_quality_limited_count"]
            + manifest["needs_vlm_count"]
            + manifest["needs_human_review_count"]
            + manifest["downgraded_excluded_count"]
        ),
        manifest["live_vlm_call_count"] == 0,
        manifest["vlm_response_count"] == 0,
        manifest["official_rules_modified"] is False,
        manifest["official_alias_assets_modified"] is False,
        manifest["formal_export_generated"] is False,
        manifest["demo_export_only"] is True,
        manifest["formal_client_export_allowed"] is False,
        manifest["client_ready"] is False,
        manifest["production_ready"] is False,
        manifest["global_strict_human_review_completed"] is False,
        len(context_index_rows) >= 0,
        len(image_status_rows) >= 0,
        len(alias_sidecar_rows) >= 0,
        bool(binding_summary),
        bool(quality_caveats),
        len(demo_rows) >= 0,
    ]

    no_apply_proof = build_no_apply_proof(
        stage="346B",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]),
        official_assets_written=[],
    )
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths}
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)
    upstream_unchanged = input_hashes_before == input_hashes_after

    no_apply_proof["upstream_input_hashes_before"] = input_hashes_before
    no_apply_proof["upstream_input_hashes_after"] = input_hashes_after
    no_apply_proof["upstream_inputs_unchanged"] = upstream_unchanged
    no_apply_proof["formal_client_export_generated"] = False
    no_apply_proof["real_production_apply_performed"] = False
    no_apply_proof["official_rules_modified"] = False
    no_apply_proof["official_alias_assets_modified"] = False
    no_apply_proof["sidecar_suggestion_only"] = True
    no_apply_proof["no_write_back"] = True

    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_346b")
        and upstream_unchanged
        and protected_before == protected_after
        and not protected_staged
        and not forbidden_staged
    )
    manifest["no_write_back_proof_passed"] = no_write_back_proof_passed
    manifest["no_write_back_summary"] = "upstream inputs unchanged; official assets unchanged; protected dirty status preserved; no protected paths staged"

    if ledger_path is not None:
        append_346b_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = _default_ledger_entry_present(ledger_path)
    validation_checks.append(manifest["milestone_ledger_updated"] or ledger_path is None)
    validation_checks.append(no_write_back_proof_passed)

    qa_fail_count = sum(1 for check in validation_checks if not check)
    manifest["qa_fail_count"] = qa_fail_count
    manifest["decision"] = READY_DECISION_346B if qa_fail_count == 0 else BLOCKED_DECISION_346B

    top_recovery_actions = [f"{key}: {value}" for key, value in recovery_action_counter.most_common(5)]
    top_fail_reasons = [f"{key}: {value}" for key, value in fail_reason_counter.most_common(5)]

    return {
        "manifest": manifest,
        "input_rows": merged_input_rows,
        "value_sanitizer_results": value_results,
        "context_injection_results": context_results,
        "evidence_assisted_recovery_results": evidence_results,
        "recovered_demo_candidates": recovered_rows,
        "still_limited_rows": still_limited_rows,
        "needs_vlm_rows": needs_vlm_rows,
        "needs_human_review_rows": needs_human_rows,
        "downgraded_excluded_rows": downgraded_rows,
        "recovery_fail_reasons": fail_reason_rows,
        "reaudit_summary": reaudit_summary,
        "executive_summary_md": render_executive_summary_markdown(
            manifest,
            top_recovery_actions=top_recovery_actions,
            top_fail_reasons=top_fail_reasons,
        ),
        "artifact_index_md": render_artifact_index_markdown(_artifact_index_rows(output_dir)),
        "next_plan_md": render_next_plan_markdown(manifest),
        "artifact_index_rows": _artifact_index_rows(output_dir),
        "no_write_back_proof": no_apply_proof,
        "dry_run_state": {
            "upstream_inputs_unchanged": upstream_unchanged,
            "protected_before": protected_before,
            "protected_after": protected_after,
            "protected_staged": protected_staged,
            "forbidden_staged": forbidden_staged,
        },
    }
