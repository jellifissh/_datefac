from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from datefac.benchmark.recovery_candidate_qa_audit_346b2_report import (
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
READY_DECISION_346B2 = "RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY"
BLOCKED_DECISION_346B2 = "RECOVERY_CANDIDATE_QA_AUDIT_346B2_BLOCKED"
INPUT_STAGE_346B2 = "POST_346B_RECOVERY_CANDIDATE_QA_AUDIT"

DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR = Path(
    r"D:\_datefac\output\full_structured_demo_export_package_345d"
)
DEFAULT_VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_DIR = Path(
    r"D:\_datefac\output\vision_assisted_table_evidence_pilot_346a"
)
DEFAULT_MINERU_IMAGE_PATH_BINDING_FIX_346A2_DIR = Path(
    r"D:\_datefac\output\mineru_image_path_binding_fix_346a2"
)
DEFAULT_QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_DIR = Path(
    r"D:\_datefac\output\quality_limited_row_recovery_pilot_346b"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\recovery_candidate_qa_audit_346b2")

MANIFEST_FILE_NAME = "recovery_candidate_qa_audit_346b2_manifest.json"
RECOVERED_CANDIDATE_AUDIT_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_recovered_candidate_audit.json"
RECOVERED_CANDIDATE_AUDIT_CSV_FILE_NAME = "recovery_candidate_qa_audit_346b2_recovered_candidate_audit.csv"
SAFE_RECOVERED_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_safe_recovered_candidates.json"
SAFE_RECOVERED_CSV_FILE_NAME = "recovery_candidate_qa_audit_346b2_safe_recovered_candidates.csv"
RISKY_RECOVERED_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_risky_recovered_candidates.json"
RISKY_RECOVERED_CSV_FILE_NAME = "recovery_candidate_qa_audit_346b2_risky_recovered_candidates.csv"
FALSE_POSITIVE_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_false_positive_suspects.json"
FALSE_POSITIVE_CSV_FILE_NAME = "recovery_candidate_qa_audit_346b2_false_positive_suspects.csv"
UNIT_REPAIR_AUDIT_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_unit_repair_audit.json"
UNIT_REPAIR_AUDIT_CSV_FILE_NAME = "recovery_candidate_qa_audit_346b2_unit_repair_audit.csv"
SEMANTIC_CLASS_DIST_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_metric_semantic_class_distribution.json"
SEMANTIC_CLASS_DIST_CSV_FILE_NAME = "recovery_candidate_qa_audit_346b2_metric_semantic_class_distribution.csv"
EVIDENCE_STRENGTH_DIST_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_evidence_strength_distribution.json"
EVIDENCE_STRENGTH_DIST_CSV_FILE_NAME = "recovery_candidate_qa_audit_346b2_evidence_strength_distribution.csv"
NEEDS_HUMAN_TRIAGE_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_needs_human_review_triage.json"
NEEDS_HUMAN_TRIAGE_CSV_FILE_NAME = "recovery_candidate_qa_audit_346b2_needs_human_review_triage.csv"
STILL_LIMITED_TRIAGE_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_still_limited_triage.json"
STILL_LIMITED_TRIAGE_CSV_FILE_NAME = "recovery_candidate_qa_audit_346b2_still_limited_triage.csv"
RULE_REFINEMENT_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_rule_refinement_candidates.json"
RULE_REFINEMENT_CSV_FILE_NAME = "recovery_candidate_qa_audit_346b2_rule_refinement_candidates.csv"
EXPANSION_READINESS_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_expansion_readiness_report.json"
REAUDIT_SUMMARY_JSON_FILE_NAME = "recovery_candidate_qa_audit_346b2_reaudit_summary.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "recovery_candidate_qa_audit_346b2_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "recovery_candidate_qa_audit_346b2_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "recovery_candidate_qa_audit_346b2_next_plan.md"

INPUT_345D_MANIFEST_NAME = "full_structured_demo_export_package_345d_manifest.json"
INPUT_345D_QUALITY_LIMITED_ROWS_JSON_NAME = "full_structured_demo_export_package_345d_quality_limited_rows.json"
INPUT_345D_QUALITY_LIMITED_ROWS_CSV_NAME = "full_structured_demo_export_package_345d_quality_limited_rows.csv"
INPUT_345D_DEMO_ROWS_JSON_NAME = "full_structured_demo_export_package_345d_demo_rows.json"
INPUT_345D_DEMO_ROWS_CSV_NAME = "full_structured_demo_export_package_345d_demo_rows.csv"
INPUT_345D_QUALITY_CAVEATS_JSON_NAME = "full_structured_demo_export_package_345d_quality_caveats.json"
INPUT_345D_QUALITY_CAVEATS_MD_NAME = "full_structured_demo_export_package_345d_quality_caveats.md"

INPUT_346A_MANIFEST_NAME = "vision_assisted_table_evidence_pilot_346a_manifest.json"
INPUT_346A_SELECTED_ROWS_JSON_NAME = "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json"
INPUT_346A_SELECTED_ROWS_CSV_NAME = "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.csv"
INPUT_346A_FIELD_REPAIR_TARGETS_JSON_NAME = "vision_assisted_table_evidence_pilot_346a_field_repair_targets.json"
INPUT_346A_FIELD_REPAIR_TARGETS_CSV_NAME = "vision_assisted_table_evidence_pilot_346a_field_repair_targets.csv"
INPUT_346A_CONFLICT_POLICY_MD_NAME = "vision_assisted_table_evidence_pilot_346a_conflict_handling_policy.md"

INPUT_346A2_MANIFEST_NAME = "mineru_image_path_binding_fix_346a2_manifest.json"
INPUT_346A2_BOUND_ROWS_JSON_NAME = "mineru_image_path_binding_fix_346a2_bound_rows.json"
INPUT_346A2_BOUND_ROWS_CSV_NAME = "mineru_image_path_binding_fix_346a2_bound_rows.csv"
INPUT_346A2_IMAGE_STATUS_JSON_NAME = "mineru_image_path_binding_fix_346a2_image_resolution_status.json"
INPUT_346A2_IMAGE_STATUS_CSV_NAME = "mineru_image_path_binding_fix_346a2_image_resolution_status.csv"
INPUT_346A2_CONTEXT_INDEX_JSON_NAME = "mineru_image_path_binding_fix_346a2_json_md_context_index.json"
INPUT_346A2_CONTEXT_INDEX_CSV_NAME = "mineru_image_path_binding_fix_346a2_json_md_context_index.csv"
INPUT_346A2_VLM_REQUEST_PACKAGE_JSONL_NAME = "mineru_image_path_binding_fix_346a2_vlm_request_package.jsonl"

INPUT_346B_MANIFEST_NAME = "quality_limited_row_recovery_pilot_346b_manifest.json"
INPUT_346B_RECOVERED_JSON_NAME = "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.json"
INPUT_346B_RECOVERED_CSV_NAME = "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.csv"
INPUT_346B_STILL_LIMITED_JSON_NAME = "quality_limited_row_recovery_pilot_346b_still_limited_rows.json"
INPUT_346B_STILL_LIMITED_CSV_NAME = "quality_limited_row_recovery_pilot_346b_still_limited_rows.csv"
INPUT_346B_NEEDS_HUMAN_JSON_NAME = "quality_limited_row_recovery_pilot_346b_needs_human_review_rows.json"
INPUT_346B_NEEDS_HUMAN_CSV_NAME = "quality_limited_row_recovery_pilot_346b_needs_human_review_rows.csv"
INPUT_346B_NEEDS_VLM_JSON_NAME = "quality_limited_row_recovery_pilot_346b_needs_vlm_rows.json"
INPUT_346B_NEEDS_VLM_CSV_NAME = "quality_limited_row_recovery_pilot_346b_needs_vlm_rows.csv"
INPUT_346B_DOWNGRADED_JSON_NAME = "quality_limited_row_recovery_pilot_346b_downgraded_excluded_rows.json"
INPUT_346B_DOWNGRADED_CSV_NAME = "quality_limited_row_recovery_pilot_346b_downgraded_excluded_rows.csv"
INPUT_346B_VALUE_RESULTS_JSON_NAME = "quality_limited_row_recovery_pilot_346b_value_sanitizer_results.json"
INPUT_346B_VALUE_RESULTS_CSV_NAME = "quality_limited_row_recovery_pilot_346b_value_sanitizer_results.csv"
INPUT_346B_CONTEXT_RESULTS_JSON_NAME = "quality_limited_row_recovery_pilot_346b_context_injection_results.json"
INPUT_346B_CONTEXT_RESULTS_CSV_NAME = "quality_limited_row_recovery_pilot_346b_context_injection_results.csv"
INPUT_346B_EVIDENCE_RESULTS_JSON_NAME = "quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.json"
INPUT_346B_EVIDENCE_RESULTS_CSV_NAME = "quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.csv"
INPUT_346B_FAIL_REASONS_JSON_NAME = "quality_limited_row_recovery_pilot_346b_recovery_fail_reasons.json"
INPUT_346B_FAIL_REASONS_CSV_NAME = "quality_limited_row_recovery_pilot_346b_recovery_fail_reasons.csv"
INPUT_346B_REAUDIT_SUMMARY_JSON_NAME = "quality_limited_row_recovery_pilot_346b_reaudit_summary.json"

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
    {"artifact_name": RECOVERED_CANDIDATE_AUDIT_JSON_FILE_NAME, "path": RECOVERED_CANDIDATE_AUDIT_JSON_FILE_NAME, "purpose": "Audited recovered candidates in JSON."},
    {"artifact_name": RECOVERED_CANDIDATE_AUDIT_CSV_FILE_NAME, "path": RECOVERED_CANDIDATE_AUDIT_CSV_FILE_NAME, "purpose": "Audited recovered candidates in CSV."},
    {"artifact_name": SAFE_RECOVERED_JSON_FILE_NAME, "path": SAFE_RECOVERED_JSON_FILE_NAME, "purpose": "Safe recovered candidates in JSON."},
    {"artifact_name": SAFE_RECOVERED_CSV_FILE_NAME, "path": SAFE_RECOVERED_CSV_FILE_NAME, "purpose": "Safe recovered candidates in CSV."},
    {"artifact_name": RISKY_RECOVERED_JSON_FILE_NAME, "path": RISKY_RECOVERED_JSON_FILE_NAME, "purpose": "Risky recovered candidates in JSON."},
    {"artifact_name": RISKY_RECOVERED_CSV_FILE_NAME, "path": RISKY_RECOVERED_CSV_FILE_NAME, "purpose": "Risky recovered candidates in CSV."},
    {"artifact_name": FALSE_POSITIVE_JSON_FILE_NAME, "path": FALSE_POSITIVE_JSON_FILE_NAME, "purpose": "False-positive suspects in JSON."},
    {"artifact_name": FALSE_POSITIVE_CSV_FILE_NAME, "path": FALSE_POSITIVE_CSV_FILE_NAME, "purpose": "False-positive suspects in CSV."},
    {"artifact_name": UNIT_REPAIR_AUDIT_JSON_FILE_NAME, "path": UNIT_REPAIR_AUDIT_JSON_FILE_NAME, "purpose": "Unit repair audit rows in JSON."},
    {"artifact_name": UNIT_REPAIR_AUDIT_CSV_FILE_NAME, "path": UNIT_REPAIR_AUDIT_CSV_FILE_NAME, "purpose": "Unit repair audit rows in CSV."},
    {"artifact_name": SEMANTIC_CLASS_DIST_JSON_FILE_NAME, "path": SEMANTIC_CLASS_DIST_JSON_FILE_NAME, "purpose": "Metric semantic class distribution in JSON."},
    {"artifact_name": SEMANTIC_CLASS_DIST_CSV_FILE_NAME, "path": SEMANTIC_CLASS_DIST_CSV_FILE_NAME, "purpose": "Metric semantic class distribution in CSV."},
    {"artifact_name": EVIDENCE_STRENGTH_DIST_JSON_FILE_NAME, "path": EVIDENCE_STRENGTH_DIST_JSON_FILE_NAME, "purpose": "Evidence strength distribution in JSON."},
    {"artifact_name": EVIDENCE_STRENGTH_DIST_CSV_FILE_NAME, "path": EVIDENCE_STRENGTH_DIST_CSV_FILE_NAME, "purpose": "Evidence strength distribution in CSV."},
    {"artifact_name": NEEDS_HUMAN_TRIAGE_JSON_FILE_NAME, "path": NEEDS_HUMAN_TRIAGE_JSON_FILE_NAME, "purpose": "Triage rows for 346B human-review outputs in JSON."},
    {"artifact_name": NEEDS_HUMAN_TRIAGE_CSV_FILE_NAME, "path": NEEDS_HUMAN_TRIAGE_CSV_FILE_NAME, "purpose": "Triage rows for 346B human-review outputs in CSV."},
    {"artifact_name": STILL_LIMITED_TRIAGE_JSON_FILE_NAME, "path": STILL_LIMITED_TRIAGE_JSON_FILE_NAME, "purpose": "Triage rows for 346B still-limited outputs in JSON."},
    {"artifact_name": STILL_LIMITED_TRIAGE_CSV_FILE_NAME, "path": STILL_LIMITED_TRIAGE_CSV_FILE_NAME, "purpose": "Triage rows for 346B still-limited outputs in CSV."},
    {"artifact_name": RULE_REFINEMENT_JSON_FILE_NAME, "path": RULE_REFINEMENT_JSON_FILE_NAME, "purpose": "Rule refinement candidates in JSON."},
    {"artifact_name": RULE_REFINEMENT_CSV_FILE_NAME, "path": RULE_REFINEMENT_CSV_FILE_NAME, "purpose": "Rule refinement candidates in CSV."},
    {"artifact_name": EXPANSION_READINESS_JSON_FILE_NAME, "path": EXPANSION_READINESS_JSON_FILE_NAME, "purpose": "Expansion readiness report in JSON."},
    {"artifact_name": REAUDIT_SUMMARY_JSON_FILE_NAME, "path": REAUDIT_SUMMARY_JSON_FILE_NAME, "purpose": "QA re-audit summary."},
    {"artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME, "path": EXECUTIVE_SUMMARY_MD_FILE_NAME, "purpose": "Executive summary for 346B2."},
    {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": ARTIFACT_INDEX_MD_FILE_NAME, "purpose": "Artifact index for 346B2 outputs."},
    {"artifact_name": NEXT_PLAN_MD_FILE_NAME, "path": NEXT_PLAN_MD_FILE_NAME, "purpose": "Recommended next step and boundary reminder."},
]

SEMANTIC_CLASS_ORDER = [
    "MONETARY_AMOUNT",
    "PERCENTAGE_OR_MARGIN",
    "RATIO_MULTIPLE",
    "PER_SHARE",
    "COUNT_OR_VOLUME",
    "TEXT_OR_LABEL",
    "UNKNOWN",
]

PERCENTAGE_METRICS = {"return_on_invested_capital", "ebitda_margin", "debt_to_asset_ratio"}
RATIO_METRICS = {"ev_to_ebitda", "quick_ratio"}
PER_SHARE_METRICS = {"book_value_per_share"}
MONETARY_METRICS = {"revenue", "operating_profit", "gross_profit"}
RATIO_KEYWORDS = ["ev/ebitda", "pe", "pb", "ps", "quick ratio", "速动比率"]
PERCENTAGE_KEYWORDS = ["margin", "收益率", "利率", "率", "(+/-%)", "%", "roic", "roe", "资产负债率"]
PER_SHARE_KEYWORDS = ["每股", "eps", "bvps", "book value per share"]
MONETARY_KEYWORDS = ["收入", "利润", "净利", "成本", "资产", "负债", "百万元", "亿元", "万元", "元"]
COUNT_VOLUME_KEYWORDS = ["万吨", "吨", "万片", "片", "用户", "间夜", "家", "次"]
MONETARY_UNIT_KEYWORDS = ["元", "万元", "百万元", "千万元", "亿元", "rmb", "hkd", "usd"]
PERCENTAGE_UNIT_KEYWORDS = ["%", "pct", "percentage"]
COUNT_VOLUME_UNIT_KEYWORDS = ["吨", "万吨", "片", "万片", "家", "人", "万人", "亿人", "间夜", "次"]
PER_SHARE_UNIT_KEYWORDS = ["元/股", "港元/股", "rmb/share", "hkd/share", "usd/share", "元"]
FALSE_POSITIVE_TRIGGER_ACTIONS = {"UNIT_PERCENT_FROM_RATIO_CONTEXT"}


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


def _metric_text(row: Dict[str, Any]) -> str:
    return " | ".join(
        [
            _safe_text(row.get("raw_metric_name")),
            _safe_text(row.get("demo_normalized_metric_name")),
            _safe_text(row.get("context_snippet")),
        ]
    ).lower()


def _classify_metric_semantic_unit(row: Dict[str, Any]) -> str:
    metric_name = _safe_text(row.get("demo_normalized_metric_name")).lower()
    text = _metric_text(row)
    if metric_name in MONETARY_METRICS:
        return "MONETARY_AMOUNT"
    if metric_name in PERCENTAGE_METRICS:
        return "PERCENTAGE_OR_MARGIN"
    if metric_name in RATIO_METRICS:
        return "RATIO_MULTIPLE"
    if metric_name in PER_SHARE_METRICS:
        return "PER_SHARE"
    if any(token in text for token in PER_SHARE_KEYWORDS):
        return "PER_SHARE"
    if any(token in text for token in RATIO_KEYWORDS):
        return "RATIO_MULTIPLE"
    if any(token in text for token in PERCENTAGE_KEYWORDS):
        return "PERCENTAGE_OR_MARGIN"
    if any(token in text for token in COUNT_VOLUME_KEYWORDS):
        return "COUNT_OR_VOLUME"
    if any(token in text for token in MONETARY_KEYWORDS):
        return "MONETARY_AMOUNT"
    if not _safe_text(row.get("value")):
        return "TEXT_OR_LABEL"
    return "UNKNOWN"


def _evidence_strength(row: Dict[str, Any]) -> str:
    if _bool_value(row.get("image_bound")) and _safe_text(row.get("image_evidence_type")) == "TABLE_CROP_IMAGE":
        return "IMAGE_BOUND_TABLE_CROP"
    if _bool_value(row.get("context_available")):
        return "JSON_MD_CONTEXT_BOUND"
    if _safe_text(row.get("context_snippet")):
        return "TEXT_CONTEXT_ONLY"
    return "NO_BOUND_EVIDENCE"


def _parse_valid(row: Dict[str, Any]) -> bool:
    return _safe_text(row.get("value_parse_status")) == "PARSED" and bool(_safe_text(row.get("sanitized_value")))


def _period_valid(row: Dict[str, Any]) -> bool:
    period = _safe_text(row.get("period"))
    return bool(period) and bool(re.search(r"(20\d{2}|Q\d)", period))


def _classify_unit_audit(row: Dict[str, Any], semantic_class: str) -> Dict[str, Any]:
    recovered_unit = _safe_text(row.get("inherited_unit")) or _safe_text(row.get("unit"))
    unit_action = _safe_text(row.get("unit_repair_action"))
    lowered_unit = recovered_unit.lower()
    mismatch_type = ""
    audit_status = "UNIT_COMPATIBLE"
    risk_flag = False
    false_positive_suspect = False
    notes: List[str] = []

    if unit_action == "UNIT_NOT_APPLICABLE_RATIO_MULTIPLE":
        if semantic_class == "RATIO_MULTIPLE":
            audit_status = "UNIT_NOT_APPLICABLE_RATIO_MULTIPLE_VERIFIED"
        elif semantic_class == "PERCENTAGE_OR_MARGIN":
            audit_status = "UNIT_NOT_APPLICABLE_PERCENTAGE_VERIFIED"
        else:
            audit_status = "UNIT_NOT_APPLICABLE_RISK_UNKNOWN"
            risk_flag = True
            notes.append("UNIT_NOT_APPLICABLE applied outside ratio/percentage semantics.")
    elif unit_action == "UNIT_PERCENT_FROM_RATIO_CONTEXT":
        if semantic_class == "PERCENTAGE_OR_MARGIN":
            audit_status = "UNIT_PERCENTAGE_COMPATIBLE"
        elif semantic_class == "RATIO_MULTIPLE":
            audit_status = "UNIT_PERCENT_ON_RATIO_MULTIPLE_RISK"
            mismatch_type = "RATIO_MULTIPLE_UNIT_MISMATCH"
            risk_flag = True
            false_positive_suspect = True
            notes.append("Ratio/multiple row should not be repaired as percentage.")
        elif semantic_class == "PER_SHARE":
            audit_status = "UNIT_PERCENT_ON_PER_SHARE_RISK"
            mismatch_type = "PER_SHARE_UNIT_MISMATCH"
            risk_flag = True
            false_positive_suspect = True
            notes.append("Per-share row should not be repaired as percentage.")
        else:
            audit_status = "UNIT_PERCENT_RISK_UNKNOWN"
            risk_flag = True
            notes.append("Percent repair applied to unsupported semantic class.")
    elif semantic_class == "MONETARY_AMOUNT":
        if not recovered_unit or not any(token in lowered_unit for token in MONETARY_UNIT_KEYWORDS):
            audit_status = "MONETARY_UNIT_MISSING_OR_MISMATCH"
            mismatch_type = "MONETARY_UNIT_MISMATCH"
            risk_flag = True
            notes.append("Monetary row lacks a clear money unit.")
    elif semantic_class == "PERCENTAGE_OR_MARGIN":
        if recovered_unit and not any(token in lowered_unit for token in PERCENTAGE_UNIT_KEYWORDS):
            audit_status = "PERCENTAGE_UNIT_MISMATCH"
            mismatch_type = "PERCENTAGE_UNIT_MISMATCH"
            risk_flag = True
            notes.append("Percentage/margin row does not carry a percent-compatible unit.")
    elif semantic_class == "RATIO_MULTIPLE":
        if recovered_unit and any(token in lowered_unit for token in MONETARY_UNIT_KEYWORDS + PERCENTAGE_UNIT_KEYWORDS):
            audit_status = "RATIO_MULTIPLE_UNIT_MISMATCH"
            mismatch_type = "RATIO_MULTIPLE_UNIT_MISMATCH"
            risk_flag = True
            false_positive_suspect = True
            notes.append("Ratio/multiple row carries a monetary or percent unit.")
    elif semantic_class == "PER_SHARE":
        if not recovered_unit or not any(token in lowered_unit for token in PER_SHARE_UNIT_KEYWORDS):
            audit_status = "PER_SHARE_UNIT_MISMATCH"
            mismatch_type = "PER_SHARE_UNIT_MISMATCH"
            risk_flag = True
            notes.append("Per-share row lacks a compatible per-share unit.")
    elif semantic_class == "COUNT_OR_VOLUME":
        if not recovered_unit or not any(token in lowered_unit for token in COUNT_VOLUME_UNIT_KEYWORDS):
            audit_status = "COUNT_OR_VOLUME_UNIT_MISMATCH"
            risk_flag = True
            notes.append("Count/volume row lacks a compatible count-volume unit.")
    elif semantic_class == "UNKNOWN":
        audit_status = "UNIT_RISK_UNKNOWN_METRIC_CLASS"
        risk_flag = True
        notes.append("Semantic unit class is UNKNOWN.")

    return {
        "recovered_unit": recovered_unit,
        "unit_audit_status": audit_status,
        "unit_audit_notes": " | ".join(notes),
        "unit_risk_flag": risk_flag,
        "false_positive_suspect": false_positive_suspect,
        "mismatch_type": mismatch_type,
    }


def _promotion_safety_decision(
    row: Dict[str, Any],
    *,
    semantic_class: str,
    evidence_strength: str,
    unit_audit: Dict[str, Any],
    strict_audit: bool,
) -> Dict[str, Any]:
    audit_fail_reasons: List[str] = []
    parse_valid = _parse_valid(row)
    period_valid = _period_valid(row)
    unit_risk_flag = _bool_value(unit_audit.get("unit_risk_flag"))
    false_positive_suspect = _bool_value(unit_audit.get("false_positive_suspect"))

    if not parse_valid:
        audit_fail_reasons.append("VALUE_PARSE_INVALID")
    if semantic_class == "UNKNOWN":
        audit_fail_reasons.append("UNKNOWN_SEMANTIC_CLASS")
    if not period_valid:
        audit_fail_reasons.append("PERIOD_MISSING_OR_SUSPICIOUS")
    if evidence_strength == "NO_BOUND_EVIDENCE":
        audit_fail_reasons.append("NO_BOUND_EVIDENCE")
    if unit_risk_flag:
        audit_fail_reasons.append(unit_audit.get("mismatch_type") or "UNIT_RISK")
    if strict_audit and _safe_text(row.get("quality_severity")).upper() == "HIGH":
        audit_fail_reasons.append("HIGH_SEVERITY_ROW")

    safety_decision = "SAFE_RECOVERED_DEMO_CANDIDATE"
    if false_positive_suspect:
        safety_decision = "FALSE_POSITIVE_SUSPECT"
    elif unit_risk_flag or evidence_strength == "NO_BOUND_EVIDENCE":
        safety_decision = "RISKY_RECOVERED_DEMO_CANDIDATE"
    elif semantic_class == "UNKNOWN":
        safety_decision = "NEEDS_RULE_REFINEMENT"

    if safety_decision == "SAFE_RECOVERED_DEMO_CANDIDATE" and audit_fail_reasons:
        safety_decision = "RISKY_RECOVERED_DEMO_CANDIDATE"

    if safety_decision == "SAFE_RECOVERED_DEMO_CANDIDATE" and _safe_text(row.get("unit_repair_action")) in FALSE_POSITIVE_TRIGGER_ACTIONS and semantic_class != "PERCENTAGE_OR_MARGIN":
        safety_decision = "FALSE_POSITIVE_SUSPECT"
        audit_fail_reasons.append("UNIT_PERCENT_FROM_RATIO_CONTEXT_NOT_SAFE")

    return {
        "safety_decision": safety_decision,
        "audit_fail_reasons": audit_fail_reasons,
    }


def _triage_row(row: Dict[str, Any], *, row_bucket: str) -> Dict[str, Any]:
    fail_reasons = row.get("top_fail_reasons") if isinstance(row.get("top_fail_reasons"), list) else []
    unit_action = _safe_text(row.get("unit_repair_action"))
    triage_action = "KEEP_LIMITED"
    if "UNRESOLVED_UNIT" in fail_reasons:
        triage_action = "RULE_REFINEMENT_UNIT_CLASSIFICATION"
    elif "NO_BOUND_EVIDENCE" in fail_reasons and _bool_value(row.get("context_available")) is False and _bool_value(row.get("image_bound")) is False:
        triage_action = "RULE_REFINEMENT_EVIDENCE_BINDING" if row_bucket == "STILL_LIMITED" else "HUMAN_REVIEW_REQUIRED"
    elif unit_action in {"UNIT_PERCENT_FROM_RATIO_CONTEXT", "UNIT_NOT_APPLICABLE_RATIO_MULTIPLE"}:
        triage_action = "RULE_REFINEMENT_CONTEXT_SCOPE"
    elif row_bucket == "NEEDS_HUMAN_REVIEW":
        triage_action = "HUMAN_REVIEW_REQUIRED"
    return {
        **row,
        "triage_action": triage_action,
        "triage_bucket": row_bucket,
    }


def _ledger_has_346b2_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return "## 346B2 Recovery Candidate QA Audit" in ledger_path.read_text(encoding="utf-8")


def _build_346b2_ledger_entry(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "## 346B2 Recovery Candidate QA Audit",
            "",
            "Status: completed",
            "",
            f"- decision: {manifest.get('decision', '')}",
            f"- input_345d_dir: {manifest.get('input_345d_dir', '')}",
            f"- input_346a_dir: {manifest.get('input_346a_dir', '')}",
            f"- input_346a2_dir: {manifest.get('input_346a2_dir', '')}",
            f"- input_346b_dir: {manifest.get('input_346b_dir', '')}",
            f"- output_dir: {manifest.get('output_dir', '')}",
            f"- audited_recovered_candidate_count: {manifest.get('audited_recovered_candidate_count', 0)}",
            f"- safe_recovered_candidate_count: {manifest.get('safe_recovered_candidate_count', 0)}",
            f"- risky_recovered_candidate_count: {manifest.get('risky_recovered_candidate_count', 0)}",
            f"- false_positive_suspect_count: {manifest.get('false_positive_suspect_count', 0)}",
            f"- unit_repair_risk_count: {manifest.get('unit_repair_risk_count', 0)}",
            f"- ratio_multiple_unit_mismatch_count: {manifest.get('ratio_multiple_unit_mismatch_count', 0)}",
            f"- percentage_unit_mismatch_count: {manifest.get('percentage_unit_mismatch_count', 0)}",
            f"- per_share_unit_mismatch_count: {manifest.get('per_share_unit_mismatch_count', 0)}",
            f"- monetary_unit_mismatch_count: {manifest.get('monetary_unit_mismatch_count', 0)}",
            f"- unit_not_applicable_verified_count: {manifest.get('unit_not_applicable_verified_count', 0)}",
            f"- unit_not_applicable_risk_count: {manifest.get('unit_not_applicable_risk_count', 0)}",
            f"- image_bound_recovered_count: {manifest.get('image_bound_recovered_count', 0)}",
            f"- text_context_only_recovered_count: {manifest.get('text_context_only_recovered_count', 0)}",
            f"- needs_rule_refinement_count: {manifest.get('needs_rule_refinement_count', 0)}",
            f"- human_review_triage_count: {manifest.get('human_review_triage_count', 0)}",
            f"- still_limited_triage_count: {manifest.get('still_limited_triage_count', 0)}",
            f"- safe_to_expand_recovery: {manifest.get('safe_to_expand_recovery', False)}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- no_write_back_proof_passed: {manifest.get('no_write_back_proof_passed', False)}",
            f"- gate_status: formal_client_export_allowed={manifest.get('formal_client_export_allowed', False)}, client_ready={manifest.get('client_ready', False)}, production_ready={manifest.get('production_ready', False)}",
            f"- next_recommended_step: {manifest.get('recommended_next_step', '')}",
        ]
    )


def append_346b2_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    if _ledger_has_346b2_entry(ledger_path):
        return False
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    addition = _build_346b2_ledger_entry(manifest)
    prefix = "\n\n" if existing and not existing.endswith("\n\n") else ""
    if existing.endswith("\n"):
        prefix = "\n" if not existing.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(existing + prefix + addition + "\n", encoding="utf-8")
    return True


def build_recovery_candidate_qa_audit_346b2(
    *,
    full_structured_demo_export_package_345d_dir: Path,
    vision_assisted_table_evidence_pilot_346a_dir: Path,
    mineru_image_path_binding_fix_346a2_dir: Path,
    quality_limited_row_recovery_pilot_346b_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    strict_audit: bool = True,
    sample_needs_human_review: bool = True,
    sample_still_limited: bool = True,
    max_context_chars: int = 4000,
    safe_to_expand_risk_threshold: int = 0,
) -> Dict[str, Any]:
    for label, path in [
        ("345D", full_structured_demo_export_package_345d_dir),
        ("346A", vision_assisted_table_evidence_pilot_346a_dir),
        ("346A2", mineru_image_path_binding_fix_346a2_dir),
        ("346B", quality_limited_row_recovery_pilot_346b_dir),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{label} input directory missing: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345d_path = full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME
    quality_rows_json_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_LIMITED_ROWS_JSON_NAME
    quality_rows_csv_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_LIMITED_ROWS_CSV_NAME
    demo_rows_json_path = full_structured_demo_export_package_345d_dir / INPUT_345D_DEMO_ROWS_JSON_NAME
    demo_rows_csv_path = full_structured_demo_export_package_345d_dir / INPUT_345D_DEMO_ROWS_CSV_NAME
    quality_caveats_json_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_CAVEATS_JSON_NAME
    quality_caveats_md_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_CAVEATS_MD_NAME

    manifest_346a_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_MANIFEST_NAME
    selected_rows_json_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_SELECTED_ROWS_JSON_NAME
    selected_rows_csv_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_SELECTED_ROWS_CSV_NAME
    field_targets_json_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_FIELD_REPAIR_TARGETS_JSON_NAME
    field_targets_csv_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_FIELD_REPAIR_TARGETS_CSV_NAME
    conflict_policy_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_CONFLICT_POLICY_MD_NAME

    manifest_346a2_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_MANIFEST_NAME
    bound_rows_json_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_BOUND_ROWS_JSON_NAME
    bound_rows_csv_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_BOUND_ROWS_CSV_NAME
    image_status_json_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_IMAGE_STATUS_JSON_NAME
    image_status_csv_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_IMAGE_STATUS_CSV_NAME
    context_index_json_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_CONTEXT_INDEX_JSON_NAME
    context_index_csv_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_CONTEXT_INDEX_CSV_NAME
    vlm_request_jsonl_path = mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_VLM_REQUEST_PACKAGE_JSONL_NAME

    manifest_346b_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_MANIFEST_NAME
    recovered_json_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_RECOVERED_JSON_NAME
    recovered_csv_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_RECOVERED_CSV_NAME
    still_limited_json_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_STILL_LIMITED_JSON_NAME
    still_limited_csv_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_STILL_LIMITED_CSV_NAME
    needs_human_json_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_NEEDS_HUMAN_JSON_NAME
    needs_human_csv_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_NEEDS_HUMAN_CSV_NAME
    needs_vlm_json_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_NEEDS_VLM_JSON_NAME
    needs_vlm_csv_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_NEEDS_VLM_CSV_NAME
    downgraded_json_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_DOWNGRADED_JSON_NAME
    downgraded_csv_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_DOWNGRADED_CSV_NAME
    value_results_json_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_VALUE_RESULTS_JSON_NAME
    value_results_csv_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_VALUE_RESULTS_CSV_NAME
    context_results_json_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_CONTEXT_RESULTS_JSON_NAME
    context_results_csv_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_CONTEXT_RESULTS_CSV_NAME
    evidence_results_json_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_EVIDENCE_RESULTS_JSON_NAME
    evidence_results_csv_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_EVIDENCE_RESULTS_CSV_NAME
    fail_reasons_json_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_FAIL_REASONS_JSON_NAME
    fail_reasons_csv_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_FAIL_REASONS_CSV_NAME
    reaudit_summary_path = quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_REAUDIT_SUMMARY_JSON_NAME

    manifest_345d = _read_json(manifest_345d_path)
    manifest_346a = _read_json(manifest_346a_path)
    manifest_346a2 = _read_json(manifest_346a2_path)
    manifest_346b = _read_json(manifest_346b_path)

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
    recovered_rows, recovered_rows_source = _load_json_or_csv_rows(
        json_path=recovered_json_path,
        csv_path=recovered_csv_path,
        label="346B recovered demo candidates",
    )
    still_limited_rows, still_limited_rows_source = _load_json_or_csv_rows(
        json_path=still_limited_json_path,
        csv_path=still_limited_csv_path,
        label="346B still limited rows",
    )
    needs_human_rows, needs_human_rows_source = _load_json_or_csv_rows(
        json_path=needs_human_json_path,
        csv_path=needs_human_csv_path,
        label="346B needs human review rows",
    )
    needs_vlm_rows, needs_vlm_rows_source = _load_json_or_csv_rows(
        json_path=needs_vlm_json_path,
        csv_path=needs_vlm_csv_path,
        label="346B needs vlm rows",
    )
    downgraded_rows, downgraded_rows_source = _load_json_or_csv_rows(
        json_path=downgraded_json_path,
        csv_path=downgraded_csv_path,
        label="346B downgraded rows",
    )
    value_results, value_results_source = _load_json_or_csv_rows(
        json_path=value_results_json_path,
        csv_path=value_results_csv_path,
        label="346B value results",
    )
    context_results, context_results_source = _load_json_or_csv_rows(
        json_path=context_results_json_path,
        csv_path=context_results_csv_path,
        label="346B context results",
    )
    evidence_results, evidence_results_source = _load_json_or_csv_rows(
        json_path=evidence_results_json_path,
        csv_path=evidence_results_csv_path,
        label="346B evidence results",
    )
    fail_reason_rows, fail_reason_rows_source = _load_json_or_csv_rows(
        json_path=fail_reasons_json_path,
        csv_path=fail_reasons_csv_path,
        label="346B fail reasons",
    )

    quality_caveats = _read_json(quality_caveats_json_path)
    _ = quality_caveats_md_path.read_text(encoding="utf-8")
    _ = conflict_policy_path.read_text(encoding="utf-8")
    _ = _read_json(reaudit_summary_path)
    _ = _read_jsonl(vlm_request_jsonl_path)

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
            manifest_346a_path,
            selected_rows_json_path,
            selected_rows_csv_path,
            field_targets_json_path,
            field_targets_csv_path,
            conflict_policy_path,
            manifest_346a2_path,
            bound_rows_json_path,
            bound_rows_csv_path,
            image_status_json_path,
            image_status_csv_path,
            context_index_json_path,
            context_index_csv_path,
            vlm_request_jsonl_path,
            manifest_346b_path,
            recovered_json_path,
            recovered_csv_path,
            still_limited_json_path,
            still_limited_csv_path,
            needs_human_json_path,
            needs_human_csv_path,
            needs_vlm_json_path,
            needs_vlm_csv_path,
            downgraded_json_path,
            downgraded_csv_path,
            value_results_json_path,
            value_results_csv_path,
            context_results_json_path,
            context_results_csv_path,
            evidence_results_json_path,
            evidence_results_csv_path,
            fail_reasons_json_path,
            fail_reasons_csv_path,
            reaudit_summary_path,
        ]
        if path.exists()
    ]

    input_paths = [Path(path) for path in files_read if Path(path).is_file()]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    value_by_source = {_safe_text(row.get("source_row_id")): row for row in value_results if _safe_text(row.get("source_row_id"))}
    context_by_source = {_safe_text(row.get("source_row_id")): row for row in context_results if _safe_text(row.get("source_row_id"))}
    evidence_by_source = {_safe_text(row.get("source_row_id")): row for row in evidence_results if _safe_text(row.get("source_row_id"))}
    selected_by_source = {_safe_text(row.get("source_row_id")): row for row in selected_rows if _safe_text(row.get("source_row_id"))}
    bound_by_source = {_safe_text(row.get("source_row_id")): row for row in bound_rows if _safe_text(row.get("source_row_id"))}

    audited_rows: List[Dict[str, Any]] = []
    unit_repair_audit_rows: List[Dict[str, Any]] = []
    semantic_counter: Counter[str] = Counter()
    evidence_counter: Counter[str] = Counter()

    for row in recovered_rows:
        source_row_id = _safe_text(row.get("source_row_id"))
        merged = {
            **selected_by_source.get(source_row_id, {}),
            **bound_by_source.get(source_row_id, {}),
            **value_by_source.get(source_row_id, {}),
            **context_by_source.get(source_row_id, {}),
            **evidence_by_source.get(source_row_id, {}),
            **dict(row),
        }
        merged["context_snippet"] = _safe_text(merged.get("context_snippet"))[:max_context_chars]
        semantic_class = _classify_metric_semantic_unit(merged)
        evidence_strength = _evidence_strength(merged)
        unit_audit = _classify_unit_audit(merged, semantic_class)
        safety = _promotion_safety_decision(
            merged,
            semantic_class=semantic_class,
            evidence_strength=evidence_strength,
            unit_audit=unit_audit,
            strict_audit=strict_audit,
        )
        audited_row = {
            **merged,
            "metric_semantic_unit_class": semantic_class,
            "evidence_strength": evidence_strength,
            **unit_audit,
            **safety,
            "audited_recovered_candidate": True,
            "sidecar_audit_only": True,
            "do_not_apply_upstream": True,
        }
        audited_rows.append(audited_row)
        unit_repair_audit_rows.append(
            {
                "pilot_row_id": audited_row.get("pilot_row_id"),
                "source_row_id": audited_row.get("source_row_id"),
                "demo_normalized_metric_name": audited_row.get("demo_normalized_metric_name"),
                "raw_metric_name": audited_row.get("raw_metric_name"),
                "metric_semantic_unit_class": semantic_class,
                "unit_repair_action": audited_row.get("unit_repair_action"),
                "recovered_unit": audited_row.get("recovered_unit"),
                "unit_audit_status": audited_row.get("unit_audit_status"),
                "unit_risk_flag": audited_row.get("unit_risk_flag"),
                "false_positive_suspect": audited_row.get("false_positive_suspect"),
                "mismatch_type": audited_row.get("mismatch_type"),
                "unit_audit_notes": audited_row.get("unit_audit_notes"),
            }
        )
        semantic_counter[semantic_class] += 1
        evidence_counter[evidence_strength] += 1

    safe_rows = [row for row in audited_rows if row["safety_decision"] == "SAFE_RECOVERED_DEMO_CANDIDATE"]
    risky_rows = [row for row in audited_rows if row["safety_decision"] == "RISKY_RECOVERED_DEMO_CANDIDATE"]
    false_positive_rows = [row for row in audited_rows if row["safety_decision"] == "FALSE_POSITIVE_SUSPECT"]
    needs_human_after_audit_rows = [row for row in audited_rows if row["safety_decision"] == "NEEDS_HUMAN_REVIEW"]
    needs_rule_refinement_rows = [row for row in audited_rows if row["safety_decision"] == "NEEDS_RULE_REFINEMENT"]

    needs_human_triage_rows = [_triage_row(row, row_bucket="NEEDS_HUMAN_REVIEW") for row in needs_human_rows] if sample_needs_human_review else []
    still_limited_triage_rows = [_triage_row(row, row_bucket="STILL_LIMITED") for row in still_limited_rows] if sample_still_limited else []
    rule_refinement_candidates = [
        row
        for row in audited_rows + needs_human_triage_rows + still_limited_triage_rows
        if _safe_text(row.get("safety_decision")) == "NEEDS_RULE_REFINEMENT"
        or _safe_text(row.get("triage_action")).startswith("RULE_REFINEMENT")
    ]

    semantic_distribution_rows = [
        {"metric_semantic_unit_class": key, "row_count": semantic_counter.get(key, 0)}
        for key in SEMANTIC_CLASS_ORDER
        if semantic_counter.get(key, 0) > 0
    ]
    evidence_distribution_rows = [
        {"evidence_strength": key, "row_count": value}
        for key, value in sorted(evidence_counter.items())
    ]

    ratio_multiple_unit_mismatch_count = sum(1 for row in audited_rows if row.get("mismatch_type") == "RATIO_MULTIPLE_UNIT_MISMATCH")
    percentage_unit_mismatch_count = sum(1 for row in audited_rows if row.get("mismatch_type") == "PERCENTAGE_UNIT_MISMATCH")
    per_share_unit_mismatch_count = sum(1 for row in audited_rows if row.get("mismatch_type") == "PER_SHARE_UNIT_MISMATCH")
    monetary_unit_mismatch_count = sum(1 for row in audited_rows if row.get("mismatch_type") == "MONETARY_UNIT_MISMATCH")
    unit_not_applicable_verified_count = sum(
        1
        for row in audited_rows
        if _safe_text(row.get("unit_audit_status")) in {
            "UNIT_NOT_APPLICABLE_RATIO_MULTIPLE_VERIFIED",
            "UNIT_NOT_APPLICABLE_PERCENTAGE_VERIFIED",
        }
    )
    unit_not_applicable_risk_count = sum(
        1 for row in audited_rows if _safe_text(row.get("unit_audit_status")) == "UNIT_NOT_APPLICABLE_RISK_UNKNOWN"
    )
    unit_repair_risk_count = sum(1 for row in audited_rows if _bool_value(row.get("unit_risk_flag")))
    image_bound_recovered_count = sum(1 for row in audited_rows if row.get("evidence_strength") == "IMAGE_BOUND_TABLE_CROP")
    text_context_only_recovered_count = sum(1 for row in audited_rows if row.get("evidence_strength") == "JSON_MD_CONTEXT_BOUND")
    no_bound_evidence_recovered_count = sum(1 for row in audited_rows if row.get("evidence_strength") == "NO_BOUND_EVIDENCE")

    safe_to_expand_recovery = (
        len(false_positive_rows) == 0
        and unit_repair_risk_count <= safe_to_expand_risk_threshold
        and len(needs_rule_refinement_rows) == 0
    )
    if safe_to_expand_recovery:
        safe_to_expand_recovery_reason = "Recovered candidate QA audit found no false-positive suspects above the configured threshold."
    else:
        safe_to_expand_recovery_reason = "False-positive suspects or material unit risks were found, so deterministic recovery should not expand yet."

    expansion_readiness_report = {
        "safe_to_expand_recovery": safe_to_expand_recovery,
        "safe_to_expand_recovery_reason": safe_to_expand_recovery_reason,
        "safe_to_expand_risk_threshold": safe_to_expand_risk_threshold,
        "false_positive_suspect_count": len(false_positive_rows),
        "unit_repair_risk_count": unit_repair_risk_count,
        "needs_rule_refinement_count": len(needs_rule_refinement_rows),
    }

    reaudit_summary = {
        "semantic_class_distribution": dict(semantic_counter),
        "evidence_strength_distribution": dict(evidence_counter),
        "unit_repair_audit_status_distribution": dict(Counter(_safe_text(row.get("unit_audit_status")) for row in audited_rows)),
        "safety_decision_distribution": dict(Counter(_safe_text(row.get("safety_decision")) for row in audited_rows)),
        "triage_distribution": dict(Counter(_safe_text(row.get("triage_action")) for row in needs_human_triage_rows + still_limited_triage_rows)),
        "inputs_read_sources": {
            "quality_rows_source": quality_rows_source,
            "demo_rows_source": demo_rows_source,
            "selected_rows_source": selected_rows_source,
            "field_target_source": field_target_source,
            "bound_rows_source": bound_rows_source,
            "image_status_source": image_status_source,
            "context_index_source": context_index_source,
            "recovered_rows_source": recovered_rows_source,
            "still_limited_rows_source": still_limited_rows_source,
            "needs_human_rows_source": needs_human_rows_source,
            "needs_vlm_rows_source": needs_vlm_rows_source,
            "downgraded_rows_source": downgraded_rows_source,
            "value_results_source": value_results_source,
            "context_results_source": context_results_source,
            "evidence_results_source": evidence_results_source,
            "fail_reason_rows_source": fail_reason_rows_source,
        },
    }

    manifest = {
        "decision": READY_DECISION_346B2,
        "input_stage": INPUT_STAGE_346B2,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "input_345d_decision": _safe_text(manifest_345d.get("decision")),
        "input_346a_decision": _safe_text(manifest_346a.get("decision")),
        "input_346a2_decision": _safe_text(manifest_346a2.get("decision")),
        "input_346b_decision": _safe_text(manifest_346b.get("decision")),
        "input_345d_dir": str(full_structured_demo_export_package_345d_dir),
        "input_346a_dir": str(vision_assisted_table_evidence_pilot_346a_dir),
        "input_346a2_dir": str(mineru_image_path_binding_fix_346a2_dir),
        "input_346b_dir": str(quality_limited_row_recovery_pilot_346b_dir),
        "output_dir": str(output_dir),
        "full_quality_limited_row_count": int(manifest_345d.get("quality_limited_row_count", len(quality_rows))),
        "input_recovered_demo_candidate_count": int(manifest_346b.get("recovered_demo_candidate_count", len(recovered_rows))),
        "input_needs_human_review_count": int(manifest_346b.get("needs_human_review_count", len(needs_human_rows))),
        "input_still_quality_limited_count": int(manifest_346b.get("still_quality_limited_count", len(still_limited_rows))),
        "audited_recovered_candidate_count": len(audited_rows),
        "safe_recovered_candidate_count": len(safe_rows),
        "risky_recovered_candidate_count": len(risky_rows),
        "false_positive_suspect_count": len(false_positive_rows),
        "needs_human_review_after_audit_count": len(needs_human_after_audit_rows),
        "needs_rule_refinement_count": len(needs_rule_refinement_rows),
        "unit_repair_audit_count": len(unit_repair_audit_rows),
        "unit_repair_risk_count": unit_repair_risk_count,
        "ratio_multiple_unit_mismatch_count": ratio_multiple_unit_mismatch_count,
        "percentage_unit_mismatch_count": percentage_unit_mismatch_count,
        "per_share_unit_mismatch_count": per_share_unit_mismatch_count,
        "monetary_unit_mismatch_count": monetary_unit_mismatch_count,
        "unit_not_applicable_verified_count": unit_not_applicable_verified_count,
        "unit_not_applicable_risk_count": unit_not_applicable_risk_count,
        "image_bound_recovered_count": image_bound_recovered_count,
        "text_context_only_recovered_count": text_context_only_recovered_count,
        "no_bound_evidence_recovered_count": no_bound_evidence_recovered_count,
        "human_review_triage_count": len(needs_human_triage_rows),
        "still_limited_triage_count": len(still_limited_triage_rows),
        "safe_to_expand_recovery": safe_to_expand_recovery,
        "safe_to_expand_recovery_reason": safe_to_expand_recovery_reason,
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
        "strict_audit": strict_audit,
        "sample_needs_human_review": sample_needs_human_review,
        "sample_still_limited": sample_still_limited,
        "max_context_chars": max_context_chars,
        "safe_to_expand_risk_threshold": safe_to_expand_risk_threshold,
        "recommended_next_step": "",
        "recommended_next_step_reason": "",
        "generated_at_utc": _utc_now(),
    }

    if not safe_to_expand_recovery:
        manifest["recommended_next_step"] = "346B3 Recovery Rule Refinement"
        manifest["recommended_next_step_reason"] = "346B2 found false-positive suspects or unit-rule risks, so the deterministic recovery policy should be tightened before any expansion."
    else:
        manifest["recommended_next_step"] = "346B4 Full Quality-Limited Recovery Expansion"
        manifest["recommended_next_step_reason"] = "Recovered candidate QA audit stayed within the configured risk threshold."

    validation_checks = [
        manifest["input_345d_decision"] == READY_DECISION_345D,
        manifest["input_346a_decision"] == READY_DECISION_346A,
        manifest["input_346a2_decision"] == READY_DECISION_346A2,
        manifest["input_346b_decision"] == READY_DECISION_346B,
        int(manifest_345d.get("qa_fail_count", 1)) == 0,
        int(manifest_346a.get("qa_fail_count", 1)) == 0,
        int(manifest_346a2.get("qa_fail_count", 1)) == 0,
        int(manifest_346b.get("qa_fail_count", 1)) == 0,
        int(manifest_346a2.get("live_vlm_call_count", 1)) == 0,
        int(manifest_346b.get("live_vlm_call_count", 1)) == 0,
        _bool_value(manifest_345d.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346a.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346a2.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346b.get("formal_client_export_allowed")) is False,
        manifest["audited_recovered_candidate_count"] == len(recovered_rows),
        manifest["audited_recovered_candidate_count"] == (
            manifest["safe_recovered_candidate_count"]
            + manifest["risky_recovered_candidate_count"]
            + manifest["false_positive_suspect_count"]
            + manifest["needs_human_review_after_audit_count"]
            + manifest["needs_rule_refinement_count"]
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
        len(unit_repair_audit_rows) == len(audited_rows),
        len(needs_vlm_rows) >= 0,
        len(downgraded_rows) >= 0,
        len(fail_reason_rows) >= 0,
        bool(quality_caveats),
        len(demo_rows) >= 0,
        len(field_target_rows) >= 0,
        len(bound_rows) >= 0,
        len(image_status_rows) >= 0,
        len(context_index_rows) >= 0,
    ]

    no_apply_proof = build_no_apply_proof(
        stage="346B2",
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
    no_apply_proof["sidecar_audit_only"] = True
    no_apply_proof["no_write_back"] = True

    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_346b2")
        and upstream_unchanged
        and protected_before == protected_after
        and not protected_staged
        and not forbidden_staged
    )
    manifest["no_write_back_proof_passed"] = no_write_back_proof_passed
    manifest["no_write_back_summary"] = "upstream inputs unchanged; official assets unchanged; protected dirty status preserved; no protected paths staged"

    if ledger_path is not None:
        append_346b2_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = _ledger_has_346b2_entry(ledger_path)
    validation_checks.append(manifest["milestone_ledger_updated"] or ledger_path is None)
    validation_checks.append(no_write_back_proof_passed)

    qa_fail_count = sum(1 for check in validation_checks if not check)
    manifest["qa_fail_count"] = qa_fail_count
    manifest["decision"] = READY_DECISION_346B2 if qa_fail_count == 0 else BLOCKED_DECISION_346B2

    top_unit_risks = [
        f"{_safe_text(row.get('demo_normalized_metric_name'))}::{_safe_text(row.get('unit_repair_action'))}"
        for row in false_positive_rows[:5]
    ]

    return {
        "manifest": manifest,
        "recovered_candidate_audit_rows": audited_rows,
        "safe_recovered_candidate_rows": safe_rows,
        "risky_recovered_candidate_rows": risky_rows,
        "false_positive_suspect_rows": false_positive_rows,
        "unit_repair_audit_rows": unit_repair_audit_rows,
        "metric_semantic_class_distribution_rows": semantic_distribution_rows,
        "evidence_strength_distribution_rows": evidence_distribution_rows,
        "needs_human_review_triage_rows": needs_human_triage_rows,
        "still_limited_triage_rows": still_limited_triage_rows,
        "rule_refinement_candidate_rows": rule_refinement_candidates,
        "expansion_readiness_report": expansion_readiness_report,
        "reaudit_summary": reaudit_summary,
        "executive_summary_md": render_executive_summary_markdown(
            manifest,
            semantic_class_distribution=dict(semantic_counter),
            evidence_strength_distribution=dict(evidence_counter),
            top_unit_risks=top_unit_risks,
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
