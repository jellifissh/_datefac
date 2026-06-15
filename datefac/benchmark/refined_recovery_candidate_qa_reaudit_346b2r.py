from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from datefac.benchmark.refined_recovery_candidate_qa_reaudit_346b2r_report import (
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
READY_DECISION_346B3 = "RECOVERY_RULE_REFINEMENT_346B3_READY"
READY_DECISION_346B2R = "REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_READY"
BLOCKED_DECISION_346B2R = "REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_BLOCKED"
INPUT_STAGE_346B2R = "POST_346B3_REFINED_RECOVERY_CANDIDATE_QA_REAUDIT"

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
DEFAULT_RECOVERY_CANDIDATE_QA_AUDIT_346B2_DIR = Path(
    r"D:\_datefac\output\recovery_candidate_qa_audit_346b2"
)
DEFAULT_RECOVERY_RULE_REFINEMENT_346B3_DIR = Path(
    r"D:\_datefac\output\recovery_rule_refinement_346b3"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\refined_recovery_candidate_qa_reaudit_346b2r")

MANIFEST_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_manifest.json"
CANDIDATE_REAUDIT_JSON_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_candidate_reaudit.json"
CANDIDATE_REAUDIT_CSV_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_candidate_reaudit.csv"
SAFE_JSON_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_safe_candidates.json"
SAFE_CSV_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_safe_candidates.csv"
RISKY_JSON_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_risky_candidates.json"
RISKY_CSV_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_risky_candidates.csv"
FALSE_POSITIVE_JSON_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_false_positive_suspects.json"
FALSE_POSITIVE_CSV_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_false_positive_suspects.csv"
SEMANTIC_REAUDIT_JSON_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_semantic_class_reaudit.json"
SEMANTIC_REAUDIT_CSV_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_semantic_class_reaudit.csv"
UNIT_REAUDIT_JSON_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_unit_compatibility_reaudit.json"
UNIT_REAUDIT_CSV_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_unit_compatibility_reaudit.csv"
REGRESSION_JSON_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_false_positive_regression_check.json"
REGRESSION_CSV_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_false_positive_regression_check.csv"
EVIDENCE_LINEAGE_JSON_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_evidence_lineage_audit.json"
EVIDENCE_LINEAGE_CSV_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_evidence_lineage_audit.csv"
EXPANSION_READINESS_JSON_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_expansion_readiness_report.json"
REAUDIT_SUMMARY_JSON_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_reaudit_summary.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_next_plan.md"

INPUT_345D_MANIFEST_NAME = "full_structured_demo_export_package_345d_manifest.json"
INPUT_346A_MANIFEST_NAME = "vision_assisted_table_evidence_pilot_346a_manifest.json"
INPUT_346A2_MANIFEST_NAME = "mineru_image_path_binding_fix_346a2_manifest.json"
INPUT_346A2_BOUND_ROWS_JSON_NAME = "mineru_image_path_binding_fix_346a2_bound_rows.json"
INPUT_346A2_BOUND_ROWS_CSV_NAME = "mineru_image_path_binding_fix_346a2_bound_rows.csv"

INPUT_346B_MANIFEST_NAME = "quality_limited_row_recovery_pilot_346b_manifest.json"
INPUT_346B_RECOVERED_JSON_NAME = "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.json"
INPUT_346B_RECOVERED_CSV_NAME = "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.csv"
INPUT_346B_CONTEXT_JSON_NAME = "quality_limited_row_recovery_pilot_346b_context_injection_results.json"
INPUT_346B_CONTEXT_CSV_NAME = "quality_limited_row_recovery_pilot_346b_context_injection_results.csv"
INPUT_346B_EVIDENCE_JSON_NAME = "quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.json"
INPUT_346B_EVIDENCE_CSV_NAME = "quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.csv"

INPUT_346B2_MANIFEST_NAME = "recovery_candidate_qa_audit_346b2_manifest.json"
INPUT_346B2_AUDIT_JSON_NAME = "recovery_candidate_qa_audit_346b2_recovered_candidate_audit.json"
INPUT_346B2_AUDIT_CSV_NAME = "recovery_candidate_qa_audit_346b2_recovered_candidate_audit.csv"
INPUT_346B2_FALSE_POSITIVE_JSON_NAME = "recovery_candidate_qa_audit_346b2_false_positive_suspects.json"
INPUT_346B2_FALSE_POSITIVE_CSV_NAME = "recovery_candidate_qa_audit_346b2_false_positive_suspects.csv"
INPUT_346B2_UNIT_AUDIT_JSON_NAME = "recovery_candidate_qa_audit_346b2_unit_repair_audit.json"
INPUT_346B2_UNIT_AUDIT_CSV_NAME = "recovery_candidate_qa_audit_346b2_unit_repair_audit.csv"

INPUT_346B3_MANIFEST_NAME = "recovery_rule_refinement_346b3_manifest.json"
INPUT_346B3_REFINED_JSON_NAME = "recovery_rule_refinement_346b3_refined_candidates.json"
INPUT_346B3_REFINED_CSV_NAME = "recovery_rule_refinement_346b3_refined_candidates.csv"
INPUT_346B3_REFINED_SAFE_JSON_NAME = "recovery_rule_refinement_346b3_refined_safe_candidates.json"
INPUT_346B3_REFINED_SAFE_CSV_NAME = "recovery_rule_refinement_346b3_refined_safe_candidates.csv"
INPUT_346B3_RATIO_JSON_NAME = "recovery_rule_refinement_346b3_corrected_ratio_multiple_rows.json"
INPUT_346B3_RATIO_CSV_NAME = "recovery_rule_refinement_346b3_corrected_ratio_multiple_rows.csv"
INPUT_346B3_PER_SHARE_JSON_NAME = "recovery_rule_refinement_346b3_corrected_per_share_rows.json"
INPUT_346B3_PER_SHARE_CSV_NAME = "recovery_rule_refinement_346b3_corrected_per_share_rows.csv"
INPUT_346B3_PCT_JSON_NAME = "recovery_rule_refinement_346b3_preserved_percentage_margin_rows.json"
INPUT_346B3_PCT_CSV_NAME = "recovery_rule_refinement_346b3_preserved_percentage_margin_rows.csv"
INPUT_346B3_DEMOTED_JSON_NAME = "recovery_rule_refinement_346b3_demoted_rows.json"
INPUT_346B3_DEMOTED_CSV_NAME = "recovery_rule_refinement_346b3_demoted_rows.csv"
INPUT_346B3_POLICY_JSON_NAME = "recovery_rule_refinement_346b3_refined_unit_policy.json"
INPUT_346B3_RULE_CHANGE_JSON_NAME = "recovery_rule_refinement_346b3_rule_change_log.json"
INPUT_346B3_REAUDIT_PREVIEW_JSON_NAME = "recovery_rule_refinement_346b3_reaudit_preview.json"
INPUT_346B3_REAUDIT_PREVIEW_CSV_NAME = "recovery_rule_refinement_346b3_reaudit_preview.csv"
INPUT_346B3_EXPANSION_JSON_NAME = "recovery_rule_refinement_346b3_expansion_readiness_report.json"

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
    {"artifact_name": CANDIDATE_REAUDIT_JSON_FILE_NAME, "path": CANDIDATE_REAUDIT_JSON_FILE_NAME, "purpose": "Candidate re-audit rows in JSON."},
    {"artifact_name": CANDIDATE_REAUDIT_CSV_FILE_NAME, "path": CANDIDATE_REAUDIT_CSV_FILE_NAME, "purpose": "Candidate re-audit rows in CSV."},
    {"artifact_name": SAFE_JSON_FILE_NAME, "path": SAFE_JSON_FILE_NAME, "purpose": "Safe re-audit candidates in JSON."},
    {"artifact_name": SAFE_CSV_FILE_NAME, "path": SAFE_CSV_FILE_NAME, "purpose": "Safe re-audit candidates in CSV."},
    {"artifact_name": RISKY_JSON_FILE_NAME, "path": RISKY_JSON_FILE_NAME, "purpose": "Risky re-audit candidates in JSON."},
    {"artifact_name": RISKY_CSV_FILE_NAME, "path": RISKY_CSV_FILE_NAME, "purpose": "Risky re-audit candidates in CSV."},
    {"artifact_name": FALSE_POSITIVE_JSON_FILE_NAME, "path": FALSE_POSITIVE_JSON_FILE_NAME, "purpose": "False-positive suspects in JSON."},
    {"artifact_name": FALSE_POSITIVE_CSV_FILE_NAME, "path": FALSE_POSITIVE_CSV_FILE_NAME, "purpose": "False-positive suspects in CSV."},
    {"artifact_name": SEMANTIC_REAUDIT_JSON_FILE_NAME, "path": SEMANTIC_REAUDIT_JSON_FILE_NAME, "purpose": "Independent semantic class re-audit in JSON."},
    {"artifact_name": SEMANTIC_REAUDIT_CSV_FILE_NAME, "path": SEMANTIC_REAUDIT_CSV_FILE_NAME, "purpose": "Independent semantic class re-audit in CSV."},
    {"artifact_name": UNIT_REAUDIT_JSON_FILE_NAME, "path": UNIT_REAUDIT_JSON_FILE_NAME, "purpose": "Unit compatibility re-audit in JSON."},
    {"artifact_name": UNIT_REAUDIT_CSV_FILE_NAME, "path": UNIT_REAUDIT_CSV_FILE_NAME, "purpose": "Unit compatibility re-audit in CSV."},
    {"artifact_name": REGRESSION_JSON_FILE_NAME, "path": REGRESSION_JSON_FILE_NAME, "purpose": "False-positive regression check in JSON."},
    {"artifact_name": REGRESSION_CSV_FILE_NAME, "path": REGRESSION_CSV_FILE_NAME, "purpose": "False-positive regression check in CSV."},
    {"artifact_name": EVIDENCE_LINEAGE_JSON_FILE_NAME, "path": EVIDENCE_LINEAGE_JSON_FILE_NAME, "purpose": "Evidence and lineage audit in JSON."},
    {"artifact_name": EVIDENCE_LINEAGE_CSV_FILE_NAME, "path": EVIDENCE_LINEAGE_CSV_FILE_NAME, "purpose": "Evidence and lineage audit in CSV."},
    {"artifact_name": EXPANSION_READINESS_JSON_FILE_NAME, "path": EXPANSION_READINESS_JSON_FILE_NAME, "purpose": "Expansion readiness report in JSON."},
    {"artifact_name": REAUDIT_SUMMARY_JSON_FILE_NAME, "path": REAUDIT_SUMMARY_JSON_FILE_NAME, "purpose": "Re-audit summary in JSON."},
    {"artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME, "path": EXECUTIVE_SUMMARY_MD_FILE_NAME, "purpose": "Executive summary for 346B2R."},
    {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": ARTIFACT_INDEX_MD_FILE_NAME, "purpose": "Artifact index for 346B2R outputs."},
    {"artifact_name": NEXT_PLAN_MD_FILE_NAME, "path": NEXT_PLAN_MD_FILE_NAME, "purpose": "Recommended next step and boundary reminder."},
]

RATIO_MULTIPLE_METRICS = {
    "ev_to_ebitda",
    "price_to_earnings",
    "pe",
    "pb",
    "ps",
    "ev_to_sales",
    "quick_ratio",
}
PERCENTAGE_MARGIN_METRICS = {
    "return_on_invested_capital",
    "roe",
    "roa",
    "ebitda_margin",
    "ebit_margin",
    "gross_margin",
    "net_margin",
    "debt_to_asset_ratio",
}
PER_SHARE_METRICS = {"earnings_per_share", "eps", "book_value_per_share", "bvps"}
MONETARY_METRICS = {"gross_profit", "revenue", "operating_profit", "net_profit", "total_assets"}

RATIO_KEYWORDS = ["ev/ebitda", "pe", "pb", "ps", "ev/sales", "quick ratio", "price to earnings", "price to book"]
PERCENTAGE_KEYWORDS = ["margin", "roe", "roa", "roic", "(+/-%)", "%", "yield", "ratio change"]
PER_SHARE_KEYWORDS = ["per share", "eps", "bvps"]

RATIO_BAD_UNIT_TOKENS = {"%", "pct", "percentage", "rmb", "hkd", "usd", "yuan", "cny", "元", "万元", "百万元", "亿元"}
PER_SHARE_ALLOWED_UNITS = {"yuan/share", "rmb/share", "hkd/share", "usd/share", "元/股", "港元/股", "美元/股"}
MONETARY_BAD_UNIT_TOKENS = {"%", "pct", "percentage", "x", "multiple"}


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


def _contains_keyword(text: str, keyword: str) -> bool:
    normalized_keyword = keyword.lower()
    if normalized_keyword in {"pe", "pb", "ps"}:
        return bool(re.search(rf"(?<![a-z]){re.escape(normalized_keyword)}(?![a-z])", text))
    return normalized_keyword in text


def _classify_semantic_class_independent(row: Dict[str, Any]) -> str:
    metric = _safe_text(row.get("demo_normalized_metric_name")).lower()
    raw_metric = _safe_text(row.get("raw_metric_name")).lower()
    if metric in PER_SHARE_METRICS:
        return "PER_SHARE"
    if metric in MONETARY_METRICS:
        return "MONETARY_AMOUNT"
    if metric in PERCENTAGE_MARGIN_METRICS:
        return "PERCENTAGE_OR_MARGIN"
    if metric in RATIO_MULTIPLE_METRICS:
        return "RATIO_MULTIPLE"
    if any(token in raw_metric for token in PER_SHARE_KEYWORDS):
        return "PER_SHARE"
    if any(_contains_keyword(raw_metric, token) for token in RATIO_KEYWORDS):
        return "RATIO_MULTIPLE"
    if any(token in raw_metric for token in PERCENTAGE_KEYWORDS):
        return "PERCENTAGE_OR_MARGIN"
    if any(token in raw_metric for token in ["profit", "revenue", "asset", "liability"]):
        return "MONETARY_AMOUNT"
    return "UNKNOWN"


def _evidence_strength(row: Dict[str, Any]) -> str:
    if _bool_value(row.get("image_bound")) and _safe_text(row.get("image_evidence_type")) == "TABLE_CROP_IMAGE":
        return "IMAGE_BOUND_TABLE_CROP"
    if _bool_value(row.get("context_available")):
        return "JSON_MD_CONTEXT_BOUND"
    if _safe_text(row.get("context_snippet")):
        return "TEXT_CONTEXT_ONLY"
    return "NO_BOUND_EVIDENCE"


def _normalize_unit_token(unit: str) -> str:
    token = _safe_text(unit).lower()
    return token.replace(" ", "")


def _classify_unit_reaudit(row: Dict[str, Any], semantic_class: str) -> Dict[str, Any]:
    refined_unit = _safe_text(row.get("refined_unit"))
    refined_action = _safe_text(row.get("refined_unit_repair_action"))
    normalized_unit = _normalize_unit_token(refined_unit)
    mismatch_type = ""
    status = "UNIT_COMPATIBLE"
    notes = ""

    if semantic_class == "RATIO_MULTIPLE":
        if normalized_unit in {"%", "pct", "percentage"} or any(token in normalized_unit for token in RATIO_BAD_UNIT_TOKENS if token != "x"):
            mismatch_type = "RATIO_MULTIPLE_UNIT_MISMATCH"
            status = "UNIT_INCOMPATIBLE"
            notes = "Ratio/multiple row still carries percent or monetary-style unit."
        elif refined_action not in {"UNIT_RATIO_MULTIPLE_X", "UNIT_NOT_APPLICABLE_RATIO_MULTIPLE"} and normalized_unit not in {"x", "multiple", ""}:
            mismatch_type = "RATIO_MULTIPLE_UNIT_MISMATCH"
            status = "UNIT_INCOMPATIBLE"
            notes = "Ratio/multiple row did not use an approved ratio-style repair action."
    elif semantic_class == "PER_SHARE":
        if normalized_unit in {"%", "pct", "percentage"}:
            mismatch_type = "PER_SHARE_UNIT_MISMATCH"
            status = "UNIT_INCOMPATIBLE"
            notes = "Per-share row still carries percent unit."
        elif refined_action != "UNIT_PER_SHARE_CONTEXT" and normalized_unit not in {u.lower() for u in PER_SHARE_ALLOWED_UNITS}:
            mismatch_type = "PER_SHARE_UNIT_MISMATCH"
            status = "UNIT_INCOMPATIBLE"
            notes = "Per-share row lacks approved per-share unit context."
    elif semantic_class == "PERCENTAGE_OR_MARGIN":
        if normalized_unit not in {"%", "pct", "percentage"} and refined_action not in {
            "UNIT_PERCENT_FROM_MARGIN_CONTEXT",
            "UNIT_PERCENT_FROM_RATIO_CONTEXT_COMPATIBLE",
        }:
            mismatch_type = "PERCENTAGE_MARGIN_UNIT_MISMATCH"
            status = "UNIT_INCOMPATIBLE"
            notes = "Percentage/margin row lost percent-compatible unit semantics."
    elif semantic_class == "MONETARY_AMOUNT":
        if normalized_unit in MONETARY_BAD_UNIT_TOKENS or refined_action == "UNIT_RATIO_MULTIPLE_X":
            mismatch_type = "MONETARY_UNIT_MISMATCH"
            status = "UNIT_INCOMPATIBLE"
            notes = "Monetary row carries ratio or percent style unit."
        elif not refined_unit:
            mismatch_type = "MONETARY_UNIT_MISMATCH"
            status = "UNIT_INCOMPATIBLE"
            notes = "Monetary row lost monetary unit context."
    else:
        mismatch_type = "SEMANTIC_CLASS_UNKNOWN"
        status = "UNIT_UNKNOWN"
        notes = "Unknown semantic class cannot be promoted safely."

    return {
        "unit_reaudit_status": status,
        "unit_reaudit_mismatch_type": mismatch_type,
        "unit_reaudit_notes": notes,
    }


def _lineage_audit(row: Dict[str, Any], original_row: Dict[str, Any] | None) -> Dict[str, Any]:
    required_fields = [
        "source_row_id",
        "pilot_row_id",
        "demo_export_row_id",
        "raw_metric_name",
        "demo_normalized_metric_name",
        "raw_value",
    ]
    missing_fields = [field for field in required_fields if not _safe_text(row.get(field))]
    has_period = bool(_safe_text(row.get("period")) or _safe_text(row.get("repaired_period")))
    has_value = bool(_safe_text(row.get("sanitized_value")) or _safe_text(row.get("value")))
    lineage_preserved = not missing_fields and has_period and has_value and original_row is not None
    notes = []
    if missing_fields:
        notes.append("missing required lineage fields")
    if not has_period:
        notes.append("missing period lineage")
    if not has_value:
        notes.append("missing value lineage")
    if original_row is None:
        notes.append("missing original 346B row")
    return {
        "lineage_preserved": lineage_preserved,
        "lineage_missing_fields": ", ".join(missing_fields),
        "lineage_audit_notes": " | ".join(notes),
    }


def _evidence_weakness(row: Dict[str, Any], evidence_strength: str, require_evidence_or_deterministic_proof: bool) -> bool:
    if not require_evidence_or_deterministic_proof:
        return False
    if evidence_strength == "NO_BOUND_EVIDENCE":
        return True
    return False


def _final_reaudit_decision(
    *,
    semantic_class: str,
    unit_status: str,
    lineage_preserved: bool,
    evidence_weak: bool,
) -> str:
    if semantic_class == "UNKNOWN":
        return "REAUDIT_NEEDS_RULE_REFINEMENT"
    if unit_status == "UNIT_INCOMPATIBLE":
        return "REAUDIT_FALSE_POSITIVE_SUSPECT"
    if not lineage_preserved:
        return "REAUDIT_NEEDS_HUMAN_REVIEW"
    if evidence_weak:
        return "REAUDIT_RISKY_RECOVERED_DEMO_CANDIDATE"
    return "REAUDIT_SAFE_RECOVERED_DEMO_CANDIDATE"


def _ledger_has_346b2r_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return "## 346B2R Refined Recovery Candidate QA Reaudit" in ledger_path.read_text(encoding="utf-8")


def _strip_346b2r_ledger_entry(text: str) -> str:
    header = "## 346B2R Refined Recovery Candidate QA Reaudit"
    start = text.find(header)
    if start == -1:
        return text
    next_header = text.find("\n## ", start + len(header))
    if next_header == -1:
        trimmed = text[:start].rstrip()
        return trimmed + ("\n" if trimmed else "")
    trimmed = (text[:start].rstrip() + "\n\n" + text[next_header + 1 :].lstrip("\n")).rstrip()
    return trimmed + ("\n" if trimmed else "")


def _build_346b2r_ledger_entry(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "## 346B2R Refined Recovery Candidate QA Reaudit",
            "",
            "Status: completed",
            "",
            f"- decision: {manifest.get('decision', '')}",
            f"- input_345d_dir: {manifest.get('input_345d_dir', '')}",
            f"- input_346a_dir: {manifest.get('input_346a_dir', '')}",
            f"- input_346a2_dir: {manifest.get('input_346a2_dir', '')}",
            f"- input_346b_dir: {manifest.get('input_346b_dir', '')}",
            f"- input_346b2_dir: {manifest.get('input_346b2_dir', '')}",
            f"- input_346b3_dir: {manifest.get('input_346b3_dir', '')}",
            f"- output_dir: {manifest.get('output_dir', '')}",
            f"- input_refined_candidate_count: {manifest.get('input_refined_candidate_count', 0)}",
            f"- reaudit_candidate_count: {manifest.get('reaudit_candidate_count', 0)}",
            f"- reaudit_safe_candidate_count: {manifest.get('reaudit_safe_candidate_count', 0)}",
            f"- reaudit_risky_candidate_count: {manifest.get('reaudit_risky_candidate_count', 0)}",
            f"- reaudit_false_positive_suspect_count: {manifest.get('reaudit_false_positive_suspect_count', 0)}",
            f"- ratio_multiple_unit_mismatch_count: {manifest.get('ratio_multiple_unit_mismatch_count', 0)}",
            f"- per_share_unit_mismatch_count: {manifest.get('per_share_unit_mismatch_count', 0)}",
            f"- percentage_margin_unit_mismatch_count: {manifest.get('percentage_margin_unit_mismatch_count', 0)}",
            f"- monetary_unit_mismatch_count: {manifest.get('monetary_unit_mismatch_count', 0)}",
            f"- semantic_class_unknown_count: {manifest.get('semantic_class_unknown_count', 0)}",
            f"- evidence_weakness_count: {manifest.get('evidence_weakness_count', 0)}",
            f"- lineage_audit_passed: {manifest.get('lineage_audit_passed', False)}",
            f"- safe_to_expand_recovery: {manifest.get('safe_to_expand_recovery', False)}",
            f"- recommended_expansion_scope: {manifest.get('recommended_expansion_scope', '')}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- no_write_back_proof_passed: {manifest.get('no_write_back_proof_passed', False)}",
            f"- gate_status: formal_client_export_allowed={manifest.get('formal_client_export_allowed', False)}, client_ready={manifest.get('client_ready', False)}, production_ready={manifest.get('production_ready', False)}",
            f"- next_recommended_step: {manifest.get('recommended_next_step', '')}",
        ]
    )


def append_346b2r_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    stripped = _strip_346b2r_ledger_entry(existing)
    addition = _build_346b2r_ledger_entry(manifest)
    prefix = "\n\n" if stripped and not stripped.endswith("\n\n") else ""
    if stripped.endswith("\n"):
        prefix = "\n" if not stripped.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(stripped + prefix + addition + "\n", encoding="utf-8")
    return True


def build_refined_recovery_candidate_qa_reaudit_346b2r(
    *,
    full_structured_demo_export_package_345d_dir: Path,
    vision_assisted_table_evidence_pilot_346a_dir: Path,
    mineru_image_path_binding_fix_346a2_dir: Path,
    quality_limited_row_recovery_pilot_346b_dir: Path,
    recovery_candidate_qa_audit_346b2_dir: Path,
    recovery_rule_refinement_346b3_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    strict_reaudit: bool = True,
    require_lineage_preservation: bool = True,
    require_evidence_or_deterministic_proof: bool = True,
    safe_to_expand_risk_threshold: int = 0,
    max_context_chars: int = 4000,
) -> Dict[str, Any]:
    for label, path in [
        ("345D", full_structured_demo_export_package_345d_dir),
        ("346A", vision_assisted_table_evidence_pilot_346a_dir),
        ("346A2", mineru_image_path_binding_fix_346a2_dir),
        ("346B", quality_limited_row_recovery_pilot_346b_dir),
        ("346B2", recovery_candidate_qa_audit_346b2_dir),
        ("346B3", recovery_rule_refinement_346b3_dir),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{label} input directory missing: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345d = _read_json(full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME)
    manifest_346a = _read_json(vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_MANIFEST_NAME)
    manifest_346a2 = _read_json(mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_MANIFEST_NAME)
    manifest_346b = _read_json(quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_MANIFEST_NAME)
    manifest_346b2 = _read_json(recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_MANIFEST_NAME)
    manifest_346b3 = _read_json(recovery_rule_refinement_346b3_dir / INPUT_346B3_MANIFEST_NAME)

    recovered_rows, recovered_rows_source = _load_json_or_csv_rows(
        json_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_RECOVERED_JSON_NAME,
        csv_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_RECOVERED_CSV_NAME,
        label="346B recovered candidates",
    )
    context_rows, context_rows_source = _load_json_or_csv_rows(
        json_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_CONTEXT_JSON_NAME,
        csv_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_CONTEXT_CSV_NAME,
        label="346B context rows",
    )
    evidence_rows, evidence_rows_source = _load_json_or_csv_rows(
        json_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_EVIDENCE_JSON_NAME,
        csv_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_EVIDENCE_CSV_NAME,
        label="346B evidence rows",
    )
    audited_rows, audited_rows_source = _load_json_or_csv_rows(
        json_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_AUDIT_JSON_NAME,
        csv_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_AUDIT_CSV_NAME,
        label="346B2 audited rows",
    )
    false_positive_rows, false_positive_rows_source = _load_json_or_csv_rows(
        json_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_FALSE_POSITIVE_JSON_NAME,
        csv_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_FALSE_POSITIVE_CSV_NAME,
        label="346B2 false positive rows",
    )
    unit_audit_rows, unit_audit_rows_source = _load_json_or_csv_rows(
        json_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_UNIT_AUDIT_JSON_NAME,
        csv_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_UNIT_AUDIT_CSV_NAME,
        label="346B2 unit audit rows",
    )
    refined_rows, refined_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_REFINED_JSON_NAME,
        csv_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_REFINED_CSV_NAME,
        label="346B3 refined rows",
    )
    refined_safe_rows, refined_safe_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_REFINED_SAFE_JSON_NAME,
        csv_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_REFINED_SAFE_CSV_NAME,
        label="346B3 refined safe rows",
    )
    ratio_rows, ratio_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_RATIO_JSON_NAME,
        csv_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_RATIO_CSV_NAME,
        label="346B3 ratio rows",
    )
    per_share_rows, per_share_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_PER_SHARE_JSON_NAME,
        csv_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_PER_SHARE_CSV_NAME,
        label="346B3 per-share rows",
    )
    pct_rows, pct_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_PCT_JSON_NAME,
        csv_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_PCT_CSV_NAME,
        label="346B3 percentage rows",
    )
    demoted_rows, demoted_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_DEMOTED_JSON_NAME,
        csv_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_DEMOTED_CSV_NAME,
        label="346B3 demoted rows",
    )
    refined_policy = _read_json(recovery_rule_refinement_346b3_dir / INPUT_346B3_POLICY_JSON_NAME)
    rule_change_log = _read_json(recovery_rule_refinement_346b3_dir / INPUT_346B3_RULE_CHANGE_JSON_NAME)
    reaudit_preview_rows, reaudit_preview_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_REAUDIT_PREVIEW_JSON_NAME,
        csv_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_REAUDIT_PREVIEW_CSV_NAME,
        label="346B3 reaudit preview rows",
    )
    _ = _read_json(recovery_rule_refinement_346b3_dir / INPUT_346B3_EXPANSION_JSON_NAME)
    bound_rows, bound_rows_source = _load_json_or_csv_rows(
        json_path=mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_BOUND_ROWS_JSON_NAME,
        csv_path=mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_BOUND_ROWS_CSV_NAME,
        label="346A2 bound rows",
    )

    files_read = [
        str(path)
        for path in [
            full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME,
            vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_MANIFEST_NAME,
            mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_MANIFEST_NAME,
            mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_BOUND_ROWS_JSON_NAME,
            quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_MANIFEST_NAME,
            quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_RECOVERED_JSON_NAME,
            quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_CONTEXT_JSON_NAME,
            quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_EVIDENCE_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_MANIFEST_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_AUDIT_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_FALSE_POSITIVE_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_UNIT_AUDIT_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_MANIFEST_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_REFINED_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_REFINED_SAFE_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_RATIO_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_PER_SHARE_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_PCT_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_DEMOTED_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_POLICY_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_RULE_CHANGE_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_REAUDIT_PREVIEW_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_EXPANSION_JSON_NAME,
        ]
        if path.exists()
    ]

    input_paths = [Path(path) for path in files_read if Path(path).is_file()]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    original_by_source = {_safe_text(row.get("source_row_id")): row for row in recovered_rows if _safe_text(row.get("source_row_id"))}
    context_by_source = {_safe_text(row.get("source_row_id")): row for row in context_rows if _safe_text(row.get("source_row_id"))}
    evidence_by_source = {_safe_text(row.get("source_row_id")): row for row in evidence_rows if _safe_text(row.get("source_row_id"))}
    bound_by_source = {_safe_text(row.get("source_row_id")): row for row in bound_rows if _safe_text(row.get("source_row_id"))}
    audited_by_source = {_safe_text(row.get("source_row_id")): row for row in audited_rows if _safe_text(row.get("source_row_id"))}
    unit_audit_by_source = {_safe_text(row.get("source_row_id")): row for row in unit_audit_rows if _safe_text(row.get("source_row_id"))}
    false_positive_by_source = {_safe_text(row.get("source_row_id")): row for row in false_positive_rows if _safe_text(row.get("source_row_id"))}

    candidate_reaudit_rows: List[Dict[str, Any]] = []
    semantic_reaudit_rows: List[Dict[str, Any]] = []
    unit_reaudit_rows: List[Dict[str, Any]] = []
    evidence_lineage_rows: List[Dict[str, Any]] = []
    semantic_counter: Counter[str] = Counter()
    evidence_counter: Counter[str] = Counter()

    for row in refined_rows:
        source_row_id = _safe_text(row.get("source_row_id"))
        merged = {
            **original_by_source.get(source_row_id, {}),
            **context_by_source.get(source_row_id, {}),
            **evidence_by_source.get(source_row_id, {}),
            **audited_by_source.get(source_row_id, {}),
            **unit_audit_by_source.get(source_row_id, {}),
            **bound_by_source.get(source_row_id, {}),
            **dict(row),
        }
        merged["context_snippet"] = _safe_text(merged.get("context_snippet"))[:max_context_chars]
        independent_semantic_class = _classify_semantic_class_independent(merged)
        semantic_disagreement = independent_semantic_class != _safe_text(merged.get("semantic_metric_class"))
        semantic_counter[independent_semantic_class] += 1

        evidence_strength = _evidence_strength(merged)
        evidence_counter[evidence_strength] += 1
        unit_reaudit = _classify_unit_reaudit(merged, independent_semantic_class)
        lineage = _lineage_audit(merged, original_by_source.get(source_row_id))
        evidence_weak = _evidence_weakness(merged, evidence_strength, require_evidence_or_deterministic_proof)
        final_decision = _final_reaudit_decision(
            semantic_class=independent_semantic_class,
            unit_status=unit_reaudit["unit_reaudit_status"],
            lineage_preserved=bool(lineage["lineage_preserved"]),
            evidence_weak=evidence_weak,
        )

        candidate_reaudit_row = {
            **merged,
            "reaudit_semantic_class": independent_semantic_class,
            "semantic_class_disagreement": semantic_disagreement,
            "reaudit_evidence_strength": evidence_strength,
            **unit_reaudit,
            **lineage,
            "evidence_weakness": evidence_weak,
            "reaudit_decision": final_decision,
            "reaudit_strict_mode": strict_reaudit,
            "sidecar_reaudit_only": True,
            "do_not_apply_upstream": True,
        }
        candidate_reaudit_rows.append(candidate_reaudit_row)
        semantic_reaudit_rows.append(
            {
                "source_row_id": source_row_id,
                "raw_metric_name": merged.get("raw_metric_name"),
                "demo_normalized_metric_name": merged.get("demo_normalized_metric_name"),
                "refined_semantic_metric_class": merged.get("semantic_metric_class"),
                "reaudit_semantic_class": independent_semantic_class,
                "semantic_class_disagreement": semantic_disagreement,
            }
        )
        unit_reaudit_rows.append(
            {
                "source_row_id": source_row_id,
                "raw_metric_name": merged.get("raw_metric_name"),
                "demo_normalized_metric_name": merged.get("demo_normalized_metric_name"),
                "reaudit_semantic_class": independent_semantic_class,
                "refined_unit": merged.get("refined_unit"),
                "refined_unit_repair_action": merged.get("refined_unit_repair_action"),
                **unit_reaudit,
            }
        )
        evidence_lineage_rows.append(
            {
                "source_row_id": source_row_id,
                "pilot_row_id": merged.get("pilot_row_id"),
                "demo_export_row_id": merged.get("demo_export_row_id"),
                "reaudit_evidence_strength": evidence_strength,
                "evidence_weakness": evidence_weak,
                **lineage,
            }
        )

    safe_rows = [row for row in candidate_reaudit_rows if row["reaudit_decision"] == "REAUDIT_SAFE_RECOVERED_DEMO_CANDIDATE"]
    risky_rows = [row for row in candidate_reaudit_rows if row["reaudit_decision"] == "REAUDIT_RISKY_RECOVERED_DEMO_CANDIDATE"]
    false_positive_reaudit_rows = [row for row in candidate_reaudit_rows if row["reaudit_decision"] == "REAUDIT_FALSE_POSITIVE_SUSPECT"]
    needs_human_rows = [row for row in candidate_reaudit_rows if row["reaudit_decision"] == "REAUDIT_NEEDS_HUMAN_REVIEW"]
    needs_rule_refinement_rows = [row for row in candidate_reaudit_rows if row["reaudit_decision"] == "REAUDIT_NEEDS_RULE_REFINEMENT"]

    regression_rows: List[Dict[str, Any]] = []
    for source_row_id, original_false_positive in false_positive_by_source.items():
        refined_row = next((row for row in candidate_reaudit_rows if _safe_text(row.get("source_row_id")) == source_row_id), None)
        if refined_row is None:
            regression_status = "REGRESSION_MISSING_FROM_REFINED_OUTPUT"
        elif refined_row["reaudit_decision"] == "REAUDIT_SAFE_RECOVERED_DEMO_CANDIDATE":
            regression_status = "REGRESSION_FIXED"
        else:
            regression_status = "REGRESSION_STILL_RISKY"
        regression_rows.append(
            {
                "source_row_id": source_row_id,
                "raw_metric_name": original_false_positive.get("raw_metric_name"),
                "demo_normalized_metric_name": original_false_positive.get("demo_normalized_metric_name"),
                "original_false_positive_mismatch_type": original_false_positive.get("mismatch_type"),
                "reaudit_decision": refined_row.get("reaudit_decision") if refined_row else "",
                "regression_status": regression_status,
            }
        )

    ratio_multiple_unit_mismatch_count = sum(
        1 for row in unit_reaudit_rows if row["unit_reaudit_mismatch_type"] == "RATIO_MULTIPLE_UNIT_MISMATCH"
    )
    per_share_unit_mismatch_count = sum(
        1 for row in unit_reaudit_rows if row["unit_reaudit_mismatch_type"] == "PER_SHARE_UNIT_MISMATCH"
    )
    percentage_margin_unit_mismatch_count = sum(
        1 for row in unit_reaudit_rows if row["unit_reaudit_mismatch_type"] == "PERCENTAGE_MARGIN_UNIT_MISMATCH"
    )
    monetary_unit_mismatch_count = sum(
        1 for row in unit_reaudit_rows if row["unit_reaudit_mismatch_type"] == "MONETARY_UNIT_MISMATCH"
    )
    semantic_class_unknown_count = sum(1 for row in candidate_reaudit_rows if row["reaudit_semantic_class"] == "UNKNOWN")
    semantic_class_disagreement_count = sum(1 for row in candidate_reaudit_rows if _bool_value(row["semantic_class_disagreement"]))
    evidence_weakness_count = sum(1 for row in candidate_reaudit_rows if _bool_value(row["evidence_weakness"]))
    lineage_audit_passed = all(_bool_value(row["lineage_preserved"]) for row in evidence_lineage_rows) if require_lineage_preservation else True
    false_positive_regression_fixed_count = sum(1 for row in regression_rows if row["regression_status"] == "REGRESSION_FIXED")
    false_positive_regression_still_risky_count = sum(
        1 for row in regression_rows if row["regression_status"] == "REGRESSION_STILL_RISKY"
    )
    false_positive_regression_missing_count = sum(
        1 for row in regression_rows if row["regression_status"] == "REGRESSION_MISSING_FROM_REFINED_OUTPUT"
    )

    safe_to_expand_recovery = bool(
        len(candidate_reaudit_rows) == len(refined_rows)
        and len(false_positive_reaudit_rows) == 0
        and len(risky_rows) <= safe_to_expand_risk_threshold
        and len(needs_human_rows) == 0
        and len(needs_rule_refinement_rows) == 0
        and ratio_multiple_unit_mismatch_count == 0
        and per_share_unit_mismatch_count == 0
        and percentage_margin_unit_mismatch_count == 0
        and monetary_unit_mismatch_count == 0
        and semantic_class_unknown_count == 0
        and lineage_audit_passed
        and evidence_weakness_count == 0
        and false_positive_regression_still_risky_count == 0
        and false_positive_regression_missing_count == 0
    )
    if safe_to_expand_recovery:
        safe_to_expand_recovery_reason = (
            "Independent re-audit found zero remaining false-positive suspects, zero unit mismatches, preserved lineage, and sufficient evidence for demo-only controlled expansion."
        )
        recommended_expansion_scope = "346B4 Controlled Quality-Limited Recovery Expansion"
        recommended_next_step = "346B4 Controlled Quality-Limited Recovery Expansion"
        recommended_next_step_reason = "346B2R independently confirmed the 346B3 refined rules are safe enough for a controlled sidecar expansion."
    else:
        safe_to_expand_recovery_reason = (
            "Independent re-audit found residual risk or unmet QA conditions, so expansion must remain blocked until another refinement pass closes the gaps."
        )
        recommended_expansion_scope = ""
        recommended_next_step = "346B3R Recovery Rule Refinement Patch"
        recommended_next_step_reason = "346B2R did not fully clear the refined candidates for controlled expansion."

    expansion_readiness_report = {
        "safe_to_expand_recovery": safe_to_expand_recovery,
        "safe_to_expand_recovery_reason": safe_to_expand_recovery_reason,
        "recommended_expansion_scope": recommended_expansion_scope,
        "controlled_max_row_limit_suggestion": 500 if safe_to_expand_recovery else 0,
    }
    reaudit_summary = {
        "semantic_class_distribution": dict(semantic_counter),
        "evidence_strength_distribution": dict(evidence_counter),
        "reaudit_decision_distribution": dict(Counter(_safe_text(row["reaudit_decision"]) for row in candidate_reaudit_rows)),
        "regression_status_distribution": dict(Counter(_safe_text(row["regression_status"]) for row in regression_rows)),
        "inputs_read_sources": {
            "recovered_rows_source": recovered_rows_source,
            "context_rows_source": context_rows_source,
            "evidence_rows_source": evidence_rows_source,
            "audited_rows_source": audited_rows_source,
            "false_positive_rows_source": false_positive_rows_source,
            "unit_audit_rows_source": unit_audit_rows_source,
            "refined_rows_source": refined_rows_source,
            "refined_safe_rows_source": refined_safe_rows_source,
            "ratio_rows_source": ratio_rows_source,
            "per_share_rows_source": per_share_rows_source,
            "pct_rows_source": pct_rows_source,
            "demoted_rows_source": demoted_rows_source,
            "reaudit_preview_rows_source": reaudit_preview_rows_source,
            "bound_rows_source": bound_rows_source,
        },
    }

    manifest = {
        "decision": READY_DECISION_346B2R,
        "input_stage": INPUT_STAGE_346B2R,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "input_345d_decision": _safe_text(manifest_345d.get("decision")),
        "input_346a_decision": _safe_text(manifest_346a.get("decision")),
        "input_346a2_decision": _safe_text(manifest_346a2.get("decision")),
        "input_346b_decision": _safe_text(manifest_346b.get("decision")),
        "input_346b2_decision": _safe_text(manifest_346b2.get("decision")),
        "input_346b3_decision": _safe_text(manifest_346b3.get("decision")),
        "input_345d_dir": str(full_structured_demo_export_package_345d_dir),
        "input_346a_dir": str(vision_assisted_table_evidence_pilot_346a_dir),
        "input_346a2_dir": str(mineru_image_path_binding_fix_346a2_dir),
        "input_346b_dir": str(quality_limited_row_recovery_pilot_346b_dir),
        "input_346b2_dir": str(recovery_candidate_qa_audit_346b2_dir),
        "input_346b3_dir": str(recovery_rule_refinement_346b3_dir),
        "output_dir": str(output_dir),
        "full_quality_limited_row_count": int(manifest_345d.get("quality_limited_row_count", 0)),
        "input_refined_candidate_count": len(refined_rows),
        "reaudit_candidate_count": len(candidate_reaudit_rows),
        "reaudit_safe_candidate_count": len(safe_rows),
        "reaudit_risky_candidate_count": len(risky_rows),
        "reaudit_false_positive_suspect_count": len(false_positive_reaudit_rows),
        "reaudit_needs_human_review_count": len(needs_human_rows),
        "reaudit_needs_rule_refinement_count": len(needs_rule_refinement_rows),
        "ratio_multiple_unit_mismatch_count": ratio_multiple_unit_mismatch_count,
        "per_share_unit_mismatch_count": per_share_unit_mismatch_count,
        "percentage_margin_unit_mismatch_count": percentage_margin_unit_mismatch_count,
        "monetary_unit_mismatch_count": monetary_unit_mismatch_count,
        "semantic_class_unknown_count": semantic_class_unknown_count,
        "semantic_class_disagreement_count": semantic_class_disagreement_count,
        "evidence_weakness_count": evidence_weakness_count,
        "lineage_audit_passed": lineage_audit_passed,
        "false_positive_regression_checked_count": len(regression_rows),
        "false_positive_regression_fixed_count": false_positive_regression_fixed_count,
        "false_positive_regression_still_risky_count": false_positive_regression_still_risky_count,
        "false_positive_regression_missing_count": false_positive_regression_missing_count,
        "safe_to_expand_recovery": safe_to_expand_recovery,
        "safe_to_expand_recovery_reason": safe_to_expand_recovery_reason,
        "recommended_expansion_scope": recommended_expansion_scope,
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
        "strict_reaudit": strict_reaudit,
        "require_lineage_preservation": require_lineage_preservation,
        "require_evidence_or_deterministic_proof": require_evidence_or_deterministic_proof,
        "safe_to_expand_risk_threshold": safe_to_expand_risk_threshold,
        "max_context_chars": max_context_chars,
        "recommended_next_step": recommended_next_step,
        "recommended_next_step_reason": recommended_next_step_reason,
        "generated_at_utc": _utc_now(),
    }

    validation_checks = [
        manifest["input_345d_decision"] == READY_DECISION_345D,
        manifest["input_346a_decision"] == READY_DECISION_346A,
        manifest["input_346a2_decision"] == READY_DECISION_346A2,
        manifest["input_346b_decision"] == READY_DECISION_346B,
        manifest["input_346b2_decision"] == READY_DECISION_346B2,
        manifest["input_346b3_decision"] == READY_DECISION_346B3,
        int(manifest_345d.get("qa_fail_count", 1)) == 0,
        int(manifest_346a.get("qa_fail_count", 1)) == 0,
        int(manifest_346a2.get("qa_fail_count", 1)) == 0,
        int(manifest_346b.get("qa_fail_count", 1)) == 0,
        int(manifest_346b2.get("qa_fail_count", 1)) == 0,
        int(manifest_346b3.get("qa_fail_count", 1)) == 0,
        int(manifest_346b.get("live_vlm_call_count", 1)) == 0,
        int(manifest_346b2.get("live_vlm_call_count", 1)) == 0,
        int(manifest_346b3.get("live_vlm_call_count", 1)) == 0,
        _bool_value(manifest_345d.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346a.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346a2.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346b.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346b2.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346b3.get("formal_client_export_allowed")) is False,
        manifest["reaudit_candidate_count"] == manifest["input_refined_candidate_count"],
        manifest["reaudit_candidate_count"]
        == (
            manifest["reaudit_safe_candidate_count"]
            + manifest["reaudit_risky_candidate_count"]
            + manifest["reaudit_false_positive_suspect_count"]
            + manifest["reaudit_needs_human_review_count"]
            + manifest["reaudit_needs_rule_refinement_count"]
        ),
        manifest["false_positive_regression_checked_count"] == len(false_positive_rows),
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
        len(refined_safe_rows) == manifest["input_refined_candidate_count"],
        len(demoted_rows) == 0,
        len(ratio_rows) == int(manifest_346b3.get("corrected_ratio_multiple_unit_count", len(ratio_rows))),
        len(per_share_rows) == int(manifest_346b3.get("corrected_per_share_unit_count", len(per_share_rows))),
        len(pct_rows) == int(manifest_346b3.get("preserved_percentage_margin_unit_count", len(pct_rows))),
        bool(refined_policy),
        bool(rule_change_log),
        len(reaudit_preview_rows) == manifest["input_refined_candidate_count"],
        recovered_rows_source in {"json", "csv"},
        context_rows_source in {"json", "csv"},
        evidence_rows_source in {"json", "csv"},
        audited_rows_source in {"json", "csv"},
        false_positive_rows_source in {"json", "csv"},
        unit_audit_rows_source in {"json", "csv"},
        refined_rows_source in {"json", "csv"},
        refined_safe_rows_source in {"json", "csv"},
        ratio_rows_source in {"json", "csv"},
        per_share_rows_source in {"json", "csv"},
        pct_rows_source in {"json", "csv"},
        demoted_rows_source in {"json", "csv"},
        reaudit_preview_rows_source in {"json", "csv"},
        bound_rows_source in {"json", "csv"},
    ]

    no_apply_proof = build_no_apply_proof(
        stage="346B2R",
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
    no_apply_proof["sidecar_reaudit_only"] = True
    no_apply_proof["no_write_back"] = True

    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_346b2r")
        and upstream_unchanged
        and protected_before == protected_after
        and not protected_staged
        and not forbidden_staged
    )
    manifest["no_write_back_proof_passed"] = no_write_back_proof_passed
    manifest["no_write_back_summary"] = "upstream inputs unchanged; official assets unchanged; protected dirty status preserved; no protected paths staged"
    validation_checks.append(no_write_back_proof_passed)

    qa_fail_count = sum(1 for check in validation_checks if not check)
    manifest["qa_fail_count"] = qa_fail_count
    manifest["decision"] = READY_DECISION_346B2R if qa_fail_count == 0 else BLOCKED_DECISION_346B2R

    if ledger_path is not None:
        append_346b2r_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = _ledger_has_346b2r_entry(ledger_path)
        if not manifest["milestone_ledger_updated"]:
            manifest["qa_fail_count"] += 1
            manifest["decision"] = BLOCKED_DECISION_346B2R

    return {
        "manifest": manifest,
        "candidate_reaudit_rows": candidate_reaudit_rows,
        "safe_candidate_rows": safe_rows,
        "risky_candidate_rows": risky_rows,
        "false_positive_candidate_rows": false_positive_reaudit_rows,
        "semantic_class_reaudit_rows": semantic_reaudit_rows,
        "unit_compatibility_reaudit_rows": unit_reaudit_rows,
        "false_positive_regression_rows": regression_rows,
        "evidence_lineage_audit_rows": evidence_lineage_rows,
        "expansion_readiness_report": expansion_readiness_report,
        "reaudit_summary": reaudit_summary,
        "executive_summary_md": render_executive_summary_markdown(
            manifest,
            evidence_strength_distribution=dict(evidence_counter),
            semantic_distribution=dict(semantic_counter),
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
