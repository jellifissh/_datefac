from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from datefac.benchmark.controlled_quality_limited_recovery_expansion_346b4_report import (
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
READY_DECISION_346B4 = "CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY"
BLOCKED_DECISION_346B4 = "CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_BLOCKED"
INPUT_STAGE_346B4 = "POST_346B2R_CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION"

SAFE_DECISION = "CONTROLLED_RECOVERED_DEMO_CANDIDATE"
RISKY_DECISION = "CONTROLLED_RISKY_RECOVERED_DEMO_CANDIDATE"
STILL_LIMITED_DECISION = "CONTROLLED_STILL_QUALITY_LIMITED"
HUMAN_DECISION = "CONTROLLED_NEEDS_HUMAN_REVIEW"
RULE_DECISION = "CONTROLLED_NEEDS_RULE_REFINEMENT"
VLM_DECISION = "CONTROLLED_NEEDS_VLM_REPAIR"
GUARDRAIL_DECISION = "CONTROLLED_FALSE_POSITIVE_GUARDRAIL_HIT"

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
DEFAULT_REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_DIR = Path(
    r"D:\_datefac\output\refined_recovery_candidate_qa_reaudit_346b2r"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4")

MANIFEST_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_manifest.json"
SELECTED_ROWS_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_selected_rows.json"
SELECTED_ROWS_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_selected_rows.csv"
RECOVERY_RESULTS_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovery_results.json"
RECOVERY_RESULTS_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovery_results.csv"
RECOVERED_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovered_demo_candidates.json"
RECOVERED_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovered_demo_candidates.csv"
SAFE_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.json"
SAFE_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.csv"
STILL_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_still_limited_rows.json"
STILL_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_still_limited_rows.csv"
HUMAN_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_human_review_rows.json"
HUMAN_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_human_review_rows.csv"
RULE_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.json"
RULE_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.csv"
VLM_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_vlm_rows.json"
VLM_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_vlm_rows.csv"
GUARD_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_false_positive_guardrail_hits.json"
GUARD_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_false_positive_guardrail_hits.csv"
SEMANTIC_DIST_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.json"
SEMANTIC_DIST_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.csv"
UNIT_ACTION_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_unit_action_distribution.json"
UNIT_ACTION_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_unit_action_distribution.csv"
LINEAGE_AUDIT_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_lineage_evidence_audit.json"
LINEAGE_AUDIT_CSV_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_lineage_evidence_audit.csv"
GUARDRAIL_SUMMARY_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_guardrail_summary.json"
EXPANSION_READINESS_JSON_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_expansion_readiness_report.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "controlled_quality_limited_recovery_expansion_346b4_next_plan.md"

INPUT_345D_MANIFEST_NAME = "full_structured_demo_export_package_345d_manifest.json"
INPUT_345D_QUALITY_JSON_NAME = "full_structured_demo_export_package_345d_quality_limited_rows.json"
INPUT_345D_QUALITY_CSV_NAME = "full_structured_demo_export_package_345d_quality_limited_rows.csv"
INPUT_345D_DEMO_JSON_NAME = "full_structured_demo_export_package_345d_demo_rows.json"
INPUT_345D_DEMO_CSV_NAME = "full_structured_demo_export_package_345d_demo_rows.csv"
INPUT_345D_CAVEATS_JSON_NAME = "full_structured_demo_export_package_345d_quality_caveats.json"

INPUT_346A_MANIFEST_NAME = "vision_assisted_table_evidence_pilot_346a_manifest.json"
INPUT_346A_POOL_JSON_NAME = "vision_assisted_table_evidence_pilot_346a_candidate_pool.json"
INPUT_346A_POOL_CSV_NAME = "vision_assisted_table_evidence_pilot_346a_candidate_pool.csv"
INPUT_346A_SELECTED_JSON_NAME = "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json"
INPUT_346A_SELECTED_CSV_NAME = "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.csv"

INPUT_346A2_MANIFEST_NAME = "mineru_image_path_binding_fix_346a2_manifest.json"
INPUT_346A2_BOUND_JSON_NAME = "mineru_image_path_binding_fix_346a2_bound_rows.json"
INPUT_346A2_BOUND_CSV_NAME = "mineru_image_path_binding_fix_346a2_bound_rows.csv"

INPUT_346B_MANIFEST_NAME = "quality_limited_row_recovery_pilot_346b_manifest.json"
INPUT_346B_INPUT_JSON_NAME = "quality_limited_row_recovery_pilot_346b_input_rows.json"
INPUT_346B_INPUT_CSV_NAME = "quality_limited_row_recovery_pilot_346b_input_rows.csv"
INPUT_346B_RECOVERED_JSON_NAME = "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.json"
INPUT_346B_RECOVERED_CSV_NAME = "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.csv"

INPUT_346B2_MANIFEST_NAME = "recovery_candidate_qa_audit_346b2_manifest.json"
INPUT_346B2_FALSE_POSITIVE_JSON_NAME = "recovery_candidate_qa_audit_346b2_false_positive_suspects.json"
INPUT_346B2_FALSE_POSITIVE_CSV_NAME = "recovery_candidate_qa_audit_346b2_false_positive_suspects.csv"
INPUT_346B2_UNIT_AUDIT_JSON_NAME = "recovery_candidate_qa_audit_346b2_unit_repair_audit.json"
INPUT_346B2_UNIT_AUDIT_CSV_NAME = "recovery_candidate_qa_audit_346b2_unit_repair_audit.csv"

INPUT_346B3_MANIFEST_NAME = "recovery_rule_refinement_346b3_manifest.json"
INPUT_346B3_POLICY_JSON_NAME = "recovery_rule_refinement_346b3_refined_unit_policy.json"
INPUT_346B3_RULE_CHANGE_JSON_NAME = "recovery_rule_refinement_346b3_rule_change_log.json"
INPUT_346B3_REFINED_SAFE_JSON_NAME = "recovery_rule_refinement_346b3_refined_safe_candidates.json"
INPUT_346B3_REFINED_SAFE_CSV_NAME = "recovery_rule_refinement_346b3_refined_safe_candidates.csv"

INPUT_346B2R_MANIFEST_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_manifest.json"
INPUT_346B2R_SAFE_JSON_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_safe_candidates.json"
INPUT_346B2R_SAFE_CSV_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_safe_candidates.csv"
INPUT_346B2R_REAUDIT_JSON_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_candidate_reaudit.json"
INPUT_346B2R_REAUDIT_CSV_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_candidate_reaudit.csv"
INPUT_346B2R_EXPANSION_JSON_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_expansion_readiness_report.json"

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
    {"artifact_name": SELECTED_ROWS_JSON_FILE_NAME, "path": SELECTED_ROWS_JSON_FILE_NAME, "purpose": "Controlled expansion selected rows in JSON."},
    {"artifact_name": SELECTED_ROWS_CSV_FILE_NAME, "path": SELECTED_ROWS_CSV_FILE_NAME, "purpose": "Controlled expansion selected rows in CSV."},
    {"artifact_name": RECOVERY_RESULTS_JSON_FILE_NAME, "path": RECOVERY_RESULTS_JSON_FILE_NAME, "purpose": "Recovery results for selected rows in JSON."},
    {"artifact_name": RECOVERY_RESULTS_CSV_FILE_NAME, "path": RECOVERY_RESULTS_CSV_FILE_NAME, "purpose": "Recovery results for selected rows in CSV."},
    {"artifact_name": RECOVERED_JSON_FILE_NAME, "path": RECOVERED_JSON_FILE_NAME, "purpose": "Recovered candidates in JSON."},
    {"artifact_name": RECOVERED_CSV_FILE_NAME, "path": RECOVERED_CSV_FILE_NAME, "purpose": "Recovered candidates in CSV."},
    {"artifact_name": SAFE_JSON_FILE_NAME, "path": SAFE_JSON_FILE_NAME, "purpose": "Safe recovered candidates in JSON."},
    {"artifact_name": SAFE_CSV_FILE_NAME, "path": SAFE_CSV_FILE_NAME, "purpose": "Safe recovered candidates in CSV."},
    {"artifact_name": STILL_JSON_FILE_NAME, "path": STILL_JSON_FILE_NAME, "purpose": "Still-limited rows in JSON."},
    {"artifact_name": STILL_CSV_FILE_NAME, "path": STILL_CSV_FILE_NAME, "purpose": "Still-limited rows in CSV."},
    {"artifact_name": HUMAN_JSON_FILE_NAME, "path": HUMAN_JSON_FILE_NAME, "purpose": "Needs-human-review rows in JSON."},
    {"artifact_name": HUMAN_CSV_FILE_NAME, "path": HUMAN_CSV_FILE_NAME, "purpose": "Needs-human-review rows in CSV."},
    {"artifact_name": RULE_JSON_FILE_NAME, "path": RULE_JSON_FILE_NAME, "purpose": "Needs-rule-refinement rows in JSON."},
    {"artifact_name": RULE_CSV_FILE_NAME, "path": RULE_CSV_FILE_NAME, "purpose": "Needs-rule-refinement rows in CSV."},
    {"artifact_name": VLM_JSON_FILE_NAME, "path": VLM_JSON_FILE_NAME, "purpose": "Needs-VLM rows in JSON."},
    {"artifact_name": VLM_CSV_FILE_NAME, "path": VLM_CSV_FILE_NAME, "purpose": "Needs-VLM rows in CSV."},
    {"artifact_name": GUARD_JSON_FILE_NAME, "path": GUARD_JSON_FILE_NAME, "purpose": "False-positive guardrail hits in JSON."},
    {"artifact_name": GUARD_CSV_FILE_NAME, "path": GUARD_CSV_FILE_NAME, "purpose": "False-positive guardrail hits in CSV."},
    {"artifact_name": SEMANTIC_DIST_JSON_FILE_NAME, "path": SEMANTIC_DIST_JSON_FILE_NAME, "purpose": "Semantic class distribution in JSON."},
    {"artifact_name": SEMANTIC_DIST_CSV_FILE_NAME, "path": SEMANTIC_DIST_CSV_FILE_NAME, "purpose": "Semantic class distribution in CSV."},
    {"artifact_name": UNIT_ACTION_JSON_FILE_NAME, "path": UNIT_ACTION_JSON_FILE_NAME, "purpose": "Unit action distribution in JSON."},
    {"artifact_name": UNIT_ACTION_CSV_FILE_NAME, "path": UNIT_ACTION_CSV_FILE_NAME, "purpose": "Unit action distribution in CSV."},
    {"artifact_name": LINEAGE_AUDIT_JSON_FILE_NAME, "path": LINEAGE_AUDIT_JSON_FILE_NAME, "purpose": "Lineage and evidence audit in JSON."},
    {"artifact_name": LINEAGE_AUDIT_CSV_FILE_NAME, "path": LINEAGE_AUDIT_CSV_FILE_NAME, "purpose": "Lineage and evidence audit in CSV."},
    {"artifact_name": GUARDRAIL_SUMMARY_JSON_FILE_NAME, "path": GUARDRAIL_SUMMARY_JSON_FILE_NAME, "purpose": "Guardrail summary in JSON."},
    {"artifact_name": EXPANSION_READINESS_JSON_FILE_NAME, "path": EXPANSION_READINESS_JSON_FILE_NAME, "purpose": "Expansion readiness report in JSON."},
    {"artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME, "path": EXECUTIVE_SUMMARY_MD_FILE_NAME, "purpose": "Executive summary for 346B4."},
    {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": ARTIFACT_INDEX_MD_FILE_NAME, "purpose": "Artifact index for 346B4 outputs."},
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
    "revenue_yoy",
    "net_profit_yoy",
}
PER_SHARE_METRICS = {"earnings_per_share", "eps", "book_value_per_share", "bvps"}
MONETARY_METRICS = {
    "gross_profit",
    "revenue",
    "operating_profit",
    "net_profit",
    "total_assets",
    "shareholder_equity",
    "total_liabilities",
    "total_profit",
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "cash_net_change",
    "financial_expense",
    "non_operating_expense",
    "non_operating_net_income_expense",
    "equity_financing",
    "dividends_and_interest_paid",
    "other_financing_cash_flow",
}

RATIO_KEYWORDS = ["ev/ebitda", "pe", "pb", "ps", "ev/sales", "quick ratio", "price to earnings", "price to book", "市盈率", "市净率", "市销率"]
PERCENTAGE_KEYWORDS = ["margin", "roe", "roa", "roic", "(+/-%)", "%", "毛利率", "净利率", "收益率", "yoy"]
PER_SHARE_KEYWORDS = ["per share", "每股", "eps", "bvps", "每股收益", "每股净资产"]
MONETARY_KEYWORDS = ["revenue", "profit", "asset", "liability", "equity", "cash flow", "收入", "利润", "资产", "负债", "权益", "现金流"]

MONEY_UNITS = {"元", "万元", "百万元", "千万元", "亿元", "rmb", "hkd", "usd", "cny"}
PERCENT_UNITS = {"%", "pct", "percentage", "％"}
RATIO_UNITS = {"x", "倍", "multiple", "倍_or_unitless"}
PER_SHARE_UNITS = {"元/股", "港元/股", "美元/股", "rmb/share", "hkd/share", "usd/share", "yuan/share"}
CURRENCY_ONLY_UNITS = {"元", "港元", "美元", "rmb", "hkd", "usd", "cny"}


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


def _normalize_unit_token(unit: str) -> str:
    return _safe_text(unit).lower().replace(" ", "")


def _contains_keyword(text: str, keyword: str) -> bool:
    normalized_keyword = keyword.lower()
    if normalized_keyword in {"pe", "pb", "ps"}:
        return bool(re.search(rf"(?<![a-z]){re.escape(normalized_keyword)}(?![a-z])", text))
    return normalized_keyword in text


def _classify_semantic_class(row: Dict[str, Any]) -> str:
    metric = _safe_text(row.get("demo_normalized_metric_name")).lower()
    raw_metric = _safe_text(row.get("raw_metric_name")).lower()
    if metric in PER_SHARE_METRICS or any(token in raw_metric for token in PER_SHARE_KEYWORDS):
        return "PER_SHARE"
    if metric in MONETARY_METRICS or any(token in raw_metric for token in MONETARY_KEYWORDS):
        return "MONETARY_AMOUNT"
    if metric in PERCENTAGE_MARGIN_METRICS or any(token in raw_metric for token in PERCENTAGE_KEYWORDS):
        return "PERCENTAGE_OR_MARGIN"
    if metric in RATIO_MULTIPLE_METRICS or any(_contains_keyword(raw_metric, token) for token in RATIO_KEYWORDS):
        return "RATIO_MULTIPLE"
    return "UNKNOWN"


def _sanitize_value(value: Any) -> Dict[str, Any]:
    raw_value = _safe_text(value)
    cleaned = raw_value.replace(",", "").replace("％", "%").replace("—", "-").replace("–", "-").replace(" ", "")
    cleaned = cleaned.replace("%", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    parse_status = "PARSED"
    parse_error = ""
    numeric_type = "FLOAT"
    if not cleaned or cleaned.lower() in {"na", "n/a", "none", "--"}:
        parse_status = "MISSING"
        parse_error = "empty_or_missing_value"
    else:
        try:
            float(cleaned)
        except ValueError:
            parse_status = "FAILED"
            parse_error = "unable_to_parse_numeric_value"
    return {
        "raw_value": raw_value,
        "sanitized_value": cleaned,
        "value_parse_status": parse_status,
        "value_parse_error": parse_error,
        "value_numeric_type": numeric_type if parse_status == "PARSED" else "",
    }


def _minimum_lineage_present(row: Dict[str, Any]) -> bool:
    required = [
        _safe_text(row.get("source_row_id")),
        _safe_text(row.get("source_pdf_name")),
        _safe_text(row.get("source_page")),
        _safe_text(row.get("source_table_id")),
        _safe_text(row.get("raw_metric_name")),
        _safe_text(row.get("period")),
    ]
    return all(required)


def _evidence_strength(row: Dict[str, Any]) -> str:
    if _bool_value(row.get("image_bound")) and _safe_text(row.get("image_evidence_type")) == "TABLE_CROP_IMAGE":
        return "IMAGE_BOUND_TABLE_CROP"
    if _safe_text(row.get("context_snippet")):
        return "JSON_MD_CONTEXT_BOUND"
    if _bool_value(row.get("source_trace_available")) and _minimum_lineage_present(row):
        return "SOURCE_TRACE_DETERMINISTIC_POLICY"
    return "NO_BOUND_EVIDENCE"


def _money_unit_from_row(row: Dict[str, Any]) -> str:
    for field in ("unit", "currency"):
        token = _normalize_unit_token(row.get(field))
        if token in MONEY_UNITS:
            return _safe_text(row.get(field))
    raw_metric = _safe_text(row.get("raw_metric_name"))
    for token in ["百万元", "千万元", "亿元", "万元", "元"]:
        if token in raw_metric:
            return token
    return ""


def _per_share_unit_from_row(row: Dict[str, Any]) -> str:
    unit = _safe_text(row.get("unit"))
    normalized = _normalize_unit_token(unit)
    if normalized in PER_SHARE_UNITS:
        return unit
    if normalized in CURRENCY_ONLY_UNITS and ("每股" in _safe_text(row.get("raw_metric_name")) or "per share" in _safe_text(row.get("raw_metric_name")).lower()):
        mapping = {
            "元": "RMB/share",
            "港元": "HKD/share",
            "美元": "USD/share",
            "rmb": "RMB/share",
            "hkd": "HKD/share",
            "usd": "USD/share",
            "cny": "RMB/share",
        }
        return mapping.get(normalized, "")
    return ""


def _preview_recovery(row: Dict[str, Any]) -> Dict[str, Any]:
    semantic_class = _classify_semantic_class(row)
    sanitizer = _sanitize_value(row.get("value"))
    quality_severity = _safe_text(row.get("quality_severity")).upper()
    original_unit = _safe_text(row.get("unit"))
    normalized_original_unit = _normalize_unit_token(original_unit)
    lineage_present = _minimum_lineage_present(row)
    evidence_strength = _evidence_strength(row)
    evidence_weak = evidence_strength == "NO_BOUND_EVIDENCE"
    refined_unit = original_unit
    refined_action = "NO_CHANGE"
    guardrail_reason = ""
    decision = SAFE_DECISION
    selection_safety_score = 2

    if quality_severity == "HIGH":
        decision = STILL_LIMITED_DECISION
        selection_safety_score = 0
        guardrail_reason = "high_severity_issue_remains"
    elif sanitizer["value_parse_status"] != "PARSED":
        decision = STILL_LIMITED_DECISION
        selection_safety_score = 0
        guardrail_reason = "value_parse_failed"
    elif not lineage_present:
        decision = HUMAN_DECISION
        selection_safety_score = 0
        guardrail_reason = "minimum_lineage_missing"
    elif semantic_class == "UNKNOWN":
        decision = RULE_DECISION
        selection_safety_score = 0
        guardrail_reason = "semantic_class_unknown"
    elif semantic_class == "RATIO_MULTIPLE":
        if normalized_original_unit and normalized_original_unit in MONEY_UNITS:
            decision = GUARDRAIL_DECISION
            selection_safety_score = 0
            guardrail_reason = "ratio_multiple_conflicts_with_monetary_unit"
        else:
            refined_unit = "x"
            refined_action = "UNIT_RATIO_MULTIPLE_X"
    elif semantic_class == "PERCENTAGE_OR_MARGIN":
        if normalized_original_unit and normalized_original_unit in MONEY_UNITS:
            decision = GUARDRAIL_DECISION
            selection_safety_score = 0
            guardrail_reason = "percentage_margin_conflicts_with_monetary_unit"
        else:
            refined_unit = "%"
            refined_action = "UNIT_PERCENT_FROM_MARGIN_CONTEXT"
    elif semantic_class == "PER_SHARE":
        per_share_unit = _per_share_unit_from_row(row)
        if per_share_unit:
            refined_unit = per_share_unit
            refined_action = "UNIT_PER_SHARE_CONTEXT" if _normalize_unit_token(original_unit) not in PER_SHARE_UNITS else "NO_CHANGE"
            selection_safety_score = 1
        else:
            decision = HUMAN_DECISION
            selection_safety_score = 0
            guardrail_reason = "per_share_requires_explicit_currency_share_context"
    elif semantic_class == "MONETARY_AMOUNT":
        money_unit = _money_unit_from_row(row)
        if money_unit:
            refined_unit = money_unit
            refined_action = "NO_CHANGE" if _safe_text(row.get("unit")) == money_unit else "UNIT_MONETARY_CONTEXT_CONFIRMED"
        else:
            decision = STILL_LIMITED_DECISION
            selection_safety_score = 0
            guardrail_reason = "missing_monetary_unit_context"

    if decision == SAFE_DECISION and evidence_weak:
        decision = RISKY_DECISION
        selection_safety_score = 1
        guardrail_reason = "weak_evidence_requires_independent_audit"

    unit_mismatch = False
    normalized_refined_unit = _normalize_unit_token(refined_unit)
    if decision in {SAFE_DECISION, RISKY_DECISION}:
        if semantic_class == "RATIO_MULTIPLE" and (
            normalized_refined_unit in PERCENT_UNITS or normalized_refined_unit in MONEY_UNITS
        ):
            decision = GUARDRAIL_DECISION
            selection_safety_score = 0
            guardrail_reason = "ratio_multiple_percent_or_money_unit_mismatch"
            unit_mismatch = True
        elif semantic_class == "PER_SHARE" and normalized_refined_unit in PERCENT_UNITS:
            decision = GUARDRAIL_DECISION
            selection_safety_score = 0
            guardrail_reason = "per_share_percent_unit_mismatch"
            unit_mismatch = True
        elif semantic_class == "PERCENTAGE_OR_MARGIN" and normalized_refined_unit not in PERCENT_UNITS:
            decision = GUARDRAIL_DECISION
            selection_safety_score = 0
            guardrail_reason = "percentage_margin_missing_percent_unit"
            unit_mismatch = True
        elif semantic_class == "MONETARY_AMOUNT" and normalized_refined_unit not in MONEY_UNITS:
            decision = GUARDRAIL_DECISION
            selection_safety_score = 0
            guardrail_reason = "monetary_amount_unit_mismatch"
            unit_mismatch = True

    return {
        "semantic_metric_class": semantic_class,
        "controlled_recovered_unit": refined_unit,
        "controlled_unit_repair_action": refined_action,
        "preview_decision": decision,
        "selection_safety_score": selection_safety_score,
        "unit_semantic_mismatch": unit_mismatch,
        "guardrail_reason": guardrail_reason,
        "evidence_strength": evidence_strength,
        "evidence_weakness": evidence_weak,
        **sanitizer,
    }


def _selection_sort_tuple(row: Dict[str, Any]) -> Tuple[int, int, int, int, str]:
    return (
        int(row.get("selection_priority_score", 0)),
        int(row.get("selection_safety_score", 0)),
        int(row.get("raw_metric_repeat_count", 0)),
        1 if _safe_text(row.get("semantic_metric_class")) != "UNKNOWN" else 0,
        _safe_text(row.get("source_row_id")),
    )


def _select_rows(
    rows: List[Dict[str, Any]],
    *,
    max_expansion_rows: int,
    selection_mode: str,
) -> List[Dict[str, Any]]:
    sorted_rows = sorted(rows, key=_selection_sort_tuple, reverse=True)
    if selection_mode != "priority_then_coverage":
        return sorted_rows[:max_expansion_rows]

    by_class: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in sorted_rows:
        by_class[_safe_text(row.get("semantic_metric_class"))].append(row)
    selected: List[Dict[str, Any]] = []
    selected_ids: set[str] = set()
    for semantic_class in [
        "RATIO_MULTIPLE",
        "PERCENTAGE_OR_MARGIN",
        "MONETARY_AMOUNT",
        "PER_SHARE",
    ]:
        for row in by_class.get(semantic_class, []):
            source_row_id = _safe_text(row.get("source_row_id"))
            if source_row_id not in selected_ids:
                selected.append(row)
                selected_ids.add(source_row_id)
                break
            if len(selected) >= max_expansion_rows:
                return selected[:max_expansion_rows]
    for row in sorted_rows:
        source_row_id = _safe_text(row.get("source_row_id"))
        if source_row_id in selected_ids:
            continue
        selected.append(row)
        selected_ids.add(source_row_id)
        if len(selected) >= max_expansion_rows:
            break
    return selected[:max_expansion_rows]


def _recover_selected_row(row: Dict[str, Any], *, strict_guardrails: bool) -> Dict[str, Any]:
    preview = _preview_recovery(row)
    decision = preview["preview_decision"]
    notes: List[str] = []
    if decision == SAFE_DECISION:
        notes.append("Recovered with deterministic value sanitizer and 346B3 semantic-class-aware unit policy.")
    elif decision == RISKY_DECISION:
        notes.append("Recovery is internally coherent but evidence remains weak, so promotion stays risky.")
    elif decision == HUMAN_DECISION:
        notes.append("Human review remains required because per-share or lineage context is insufficient.")
    elif decision == RULE_DECISION:
        notes.append("Rule refinement remains required because semantic class is unknown.")
    elif decision == STILL_LIMITED_DECISION:
        notes.append("The row remains quality-limited after deterministic repair attempts.")
    elif decision == GUARDRAIL_DECISION:
        notes.append("Guardrails blocked promotion to avoid repeating 346B2 false-positive semantics.")
    if strict_guardrails and decision == RISKY_DECISION:
        decision = HUMAN_DECISION
        notes.append("Strict guardrails demoted risky candidates to human review.")

    controlled_result = {
        **row,
        **preview,
        "controlled_recovery_decision": decision,
        "controlled_recovered_demo_candidate": decision in {SAFE_DECISION, RISKY_DECISION},
        "controlled_safe_recovered_candidate": decision == SAFE_DECISION,
        "controlled_risky_candidate": decision == RISKY_DECISION,
        "do_not_apply_upstream": True,
        "sidecar_recovery_only": True,
        "demo_export_only": True,
        "controlled_guardrail_notes": " | ".join(notes),
    }
    return controlled_result


def _ledger_has_346b4_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return "## 346B4 Controlled Quality-Limited Recovery Expansion" in ledger_path.read_text(encoding="utf-8")


def _strip_346b4_ledger_entry(text: str) -> str:
    header = "## 346B4 Controlled Quality-Limited Recovery Expansion"
    start = text.find(header)
    if start == -1:
        return text
    next_header = text.find("\n## ", start + len(header))
    if next_header == -1:
        trimmed = text[:start].rstrip()
        return trimmed + ("\n" if trimmed else "")
    trimmed = (text[:start].rstrip() + "\n\n" + text[next_header + 1 :].lstrip("\n")).rstrip()
    return trimmed + ("\n" if trimmed else "")


def _build_346b4_ledger_entry(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "## 346B4 Controlled Quality-Limited Recovery Expansion",
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
            f"- input_346b2r_dir: {manifest.get('input_346b2r_dir', '')}",
            f"- output_dir: {manifest.get('output_dir', '')}",
            f"- full_quality_limited_row_count: {manifest.get('full_quality_limited_row_count', 0)}",
            f"- controlled_expansion_input_limit: {manifest.get('controlled_expansion_input_limit', 0)}",
            f"- controlled_expansion_input_row_count: {manifest.get('controlled_expansion_input_row_count', 0)}",
            f"- excluded_row_touched_count: {manifest.get('excluded_row_touched_count', 0)}",
            f"- already_demo_ready_row_touched_count: {manifest.get('already_demo_ready_row_touched_count', 0)}",
            f"- already_346b_pilot_row_count: {manifest.get('already_346b_pilot_row_count', 0)}",
            f"- new_quality_limited_row_count: {manifest.get('new_quality_limited_row_count', 0)}",
            f"- value_sanitizer_attempt_count: {manifest.get('value_sanitizer_attempt_count', 0)}",
            f"- sanitized_value_success_count: {manifest.get('sanitized_value_success_count', 0)}",
            f"- sanitized_value_failure_count: {manifest.get('sanitized_value_failure_count', 0)}",
            f"- semantic_class_known_count: {manifest.get('semantic_class_known_count', 0)}",
            f"- semantic_class_unknown_count: {manifest.get('semantic_class_unknown_count', 0)}",
            f"- recovered_candidate_count: {manifest.get('recovered_candidate_count', 0)}",
            f"- safe_recovered_candidate_count: {manifest.get('safe_recovered_candidate_count', 0)}",
            f"- risky_candidate_count: {manifest.get('risky_candidate_count', 0)}",
            f"- false_positive_guardrail_hit_count: {manifest.get('false_positive_guardrail_hit_count', 0)}",
            f"- still_quality_limited_count: {manifest.get('still_quality_limited_count', 0)}",
            f"- needs_human_review_count: {manifest.get('needs_human_review_count', 0)}",
            f"- needs_rule_refinement_count: {manifest.get('needs_rule_refinement_count', 0)}",
            f"- needs_vlm_count: {manifest.get('needs_vlm_count', 0)}",
            f"- unit_semantic_mismatch_count: {manifest.get('unit_semantic_mismatch_count', 0)}",
            f"- evidence_weakness_count: {manifest.get('evidence_weakness_count', 0)}",
            f"- lineage_audit_passed: {manifest.get('lineage_audit_passed', False)}",
            f"- safe_to_continue_expansion: {manifest.get('safe_to_continue_expansion', False)}",
            f"- recommended_next_step: {manifest.get('recommended_next_step', '')}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- no_write_back_proof_passed: {manifest.get('no_write_back_proof_passed', False)}",
            f"- gate_status: formal_client_export_allowed={manifest.get('formal_client_export_allowed', False)}, client_ready={manifest.get('client_ready', False)}, production_ready={manifest.get('production_ready', False)}",
        ]
    )


def append_346b4_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    stripped = _strip_346b4_ledger_entry(existing)
    addition = _build_346b4_ledger_entry(manifest)
    prefix = "\n\n" if stripped and not stripped.endswith("\n\n") else ""
    if stripped.endswith("\n"):
        prefix = "\n" if not stripped.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(stripped + prefix + addition + "\n", encoding="utf-8")
    return True


def build_controlled_quality_limited_recovery_expansion_346b4(
    *,
    full_structured_demo_export_package_345d_dir: Path,
    vision_assisted_table_evidence_pilot_346a_dir: Path,
    mineru_image_path_binding_fix_346a2_dir: Path,
    quality_limited_row_recovery_pilot_346b_dir: Path,
    recovery_candidate_qa_audit_346b2_dir: Path,
    recovery_rule_refinement_346b3_dir: Path,
    refined_recovery_candidate_qa_reaudit_346b2r_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    max_expansion_rows: int = 500,
    selection_mode: str = "priority_then_coverage",
    require_346b2r_safe_to_expand: bool = True,
    strict_guardrails: bool = True,
    include_image_bound_first: bool = True,
    include_json_md_context_bound: bool = True,
    max_context_chars: int = 4000,
) -> Dict[str, Any]:
    for label, path in [
        ("345D input directory", full_structured_demo_export_package_345d_dir),
        ("346A input directory", vision_assisted_table_evidence_pilot_346a_dir),
        ("346A2 input directory", mineru_image_path_binding_fix_346a2_dir),
        ("346B input directory", quality_limited_row_recovery_pilot_346b_dir),
        ("346B2 input directory", recovery_candidate_qa_audit_346b2_dir),
        ("346B3 input directory", recovery_rule_refinement_346b3_dir),
        ("346B2R input directory", refined_recovery_candidate_qa_reaudit_346b2r_dir),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{label} missing: {path}")

    manifest_345d = _read_json(full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME)
    manifest_346a = _read_json(vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_MANIFEST_NAME)
    manifest_346a2 = _read_json(mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_MANIFEST_NAME)
    manifest_346b = _read_json(quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_MANIFEST_NAME)
    manifest_346b2 = _read_json(recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_MANIFEST_NAME)
    manifest_346b3 = _read_json(recovery_rule_refinement_346b3_dir / INPUT_346B3_MANIFEST_NAME)
    manifest_346b2r = _read_json(refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_MANIFEST_NAME)
    readiness_346b2r = _read_json(refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_EXPANSION_JSON_NAME)

    if require_346b2r_safe_to_expand and not _bool_value(manifest_346b2r.get("safe_to_expand_recovery")):
        raise ValueError("346B2R safe_to_expand_recovery must be true before 346B4 controlled expansion.")

    quality_rows, quality_rows_source = _load_json_or_csv_rows(
        json_path=full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_JSON_NAME,
        csv_path=full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_CSV_NAME,
        label="345D quality-limited rows",
    )
    demo_rows, demo_rows_source = _load_json_or_csv_rows(
        json_path=full_structured_demo_export_package_345d_dir / INPUT_345D_DEMO_JSON_NAME,
        csv_path=full_structured_demo_export_package_345d_dir / INPUT_345D_DEMO_CSV_NAME,
        label="345D demo rows",
    )
    candidate_pool_rows, candidate_pool_rows_source = _load_json_or_csv_rows(
        json_path=vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_POOL_JSON_NAME,
        csv_path=vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_POOL_CSV_NAME,
        label="346A candidate pool",
    )
    pilot_rows, pilot_rows_source = _load_json_or_csv_rows(
        json_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_INPUT_JSON_NAME,
        csv_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_INPUT_CSV_NAME,
        label="346B pilot input rows",
    )
    recovered_346b_rows, recovered_346b_rows_source = _load_json_or_csv_rows(
        json_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_RECOVERED_JSON_NAME,
        csv_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_RECOVERED_CSV_NAME,
        label="346B recovered rows",
    )
    false_positive_rows, false_positive_rows_source = _load_json_or_csv_rows(
        json_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_FALSE_POSITIVE_JSON_NAME,
        csv_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_FALSE_POSITIVE_CSV_NAME,
        label="346B2 false-positive suspects",
    )
    unit_audit_rows, unit_audit_rows_source = _load_json_or_csv_rows(
        json_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_UNIT_AUDIT_JSON_NAME,
        csv_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_UNIT_AUDIT_CSV_NAME,
        label="346B2 unit repair audit",
    )
    bound_rows, bound_rows_source = _load_json_or_csv_rows(
        json_path=mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_BOUND_JSON_NAME,
        csv_path=mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_BOUND_CSV_NAME,
        label="346A2 bound rows",
    )
    refined_policy = _read_json(recovery_rule_refinement_346b3_dir / INPUT_346B3_POLICY_JSON_NAME)
    rule_change_log = _read_json(recovery_rule_refinement_346b3_dir / INPUT_346B3_RULE_CHANGE_JSON_NAME)
    refined_safe_rows, refined_safe_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_REFINED_SAFE_JSON_NAME,
        csv_path=recovery_rule_refinement_346b3_dir / INPUT_346B3_REFINED_SAFE_CSV_NAME,
        label="346B3 refined safe candidates",
    )
    reaudit_safe_rows, reaudit_safe_rows_source = _load_json_or_csv_rows(
        json_path=refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_SAFE_JSON_NAME,
        csv_path=refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_SAFE_CSV_NAME,
        label="346B2R safe candidates",
    )
    candidate_reaudit_rows, candidate_reaudit_rows_source = _load_json_or_csv_rows(
        json_path=refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_REAUDIT_JSON_NAME,
        csv_path=refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_REAUDIT_CSV_NAME,
        label="346B2R candidate re-audit rows",
    )
    quality_caveats = _read_json(full_structured_demo_export_package_345d_dir / INPUT_345D_CAVEATS_JSON_NAME) if (full_structured_demo_export_package_345d_dir / INPUT_345D_CAVEATS_JSON_NAME).exists() else []

    files_read = [
        str(path)
        for path in [
            full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME,
            full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_JSON_NAME,
            full_structured_demo_export_package_345d_dir / INPUT_345D_DEMO_JSON_NAME,
            full_structured_demo_export_package_345d_dir / INPUT_345D_CAVEATS_JSON_NAME,
            vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_MANIFEST_NAME,
            vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_POOL_JSON_NAME,
            mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_MANIFEST_NAME,
            mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_BOUND_JSON_NAME,
            quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_MANIFEST_NAME,
            quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_INPUT_JSON_NAME,
            quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_RECOVERED_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_MANIFEST_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_FALSE_POSITIVE_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_UNIT_AUDIT_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_MANIFEST_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_POLICY_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_RULE_CHANGE_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_REFINED_SAFE_JSON_NAME,
            refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_MANIFEST_NAME,
            refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_SAFE_JSON_NAME,
            refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_REAUDIT_JSON_NAME,
            refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_EXPANSION_JSON_NAME,
        ]
        if path.exists()
    ]

    input_paths = [Path(path) for path in files_read if Path(path).is_file()]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    candidate_pool_by_source = {_safe_text(row.get("source_row_id")): row for row in candidate_pool_rows if _safe_text(row.get("source_row_id"))}
    bound_by_source = {_safe_text(row.get("source_row_id")): row for row in bound_rows if _safe_text(row.get("source_row_id"))}
    demo_source_ids = {_safe_text(row.get("source_row_id")) for row in demo_rows if _safe_text(row.get("source_row_id"))}
    pilot_source_ids = {_safe_text(row.get("source_row_id")) for row in pilot_rows if _safe_text(row.get("source_row_id"))}

    merged_quality_rows: List[Dict[str, Any]] = []
    excluded_row_touched_count = 0
    already_demo_ready_row_touched_count = 0
    already_346b_pilot_row_count = 0
    high_severity_skipped_count = 0
    strict_pending_skipped_count = 0

    for row in quality_rows:
        source_row_id = _safe_text(row.get("source_row_id"))
        if not source_row_id:
            continue
        if source_row_id in demo_source_ids:
            already_demo_ready_row_touched_count += 1
            continue
        if source_row_id in pilot_source_ids:
            already_346b_pilot_row_count += 1
            continue
        if "STRICT_HUMAN_REVIEW_PENDING" in _safe_text(row.get("quality_issue_codes")):
            strict_pending_skipped_count += 1
            continue
        if _safe_text(row.get("quality_severity")).upper() == "HIGH":
            high_severity_skipped_count += 1
            continue
        merged = {
            **dict(row),
            **candidate_pool_by_source.get(source_row_id, {}),
            **bound_by_source.get(source_row_id, {}),
        }
        preview = _preview_recovery(merged)
        merged_quality_rows.append(
            {
                **merged,
                **preview,
                "selection_priority_score": int(merged.get("priority_score", 0) or 0),
                "selection_reason_codes": _safe_text(merged.get("selection_reason")),
                "selected_from_quality_limited_pool": True,
                "already_in_346b_pilot": False,
                "minimum_lineage_present": _minimum_lineage_present(merged),
            }
        )

    selected_rows = _select_rows(
        merged_quality_rows,
        max_expansion_rows=max_expansion_rows,
        selection_mode=selection_mode,
    )
    recovery_rows = [_recover_selected_row(row, strict_guardrails=strict_guardrails) for row in selected_rows]

    recovered_candidate_rows = [
        row for row in recovery_rows if row["controlled_recovery_decision"] in {SAFE_DECISION, RISKY_DECISION}
    ]
    safe_recovered_rows = [row for row in recovery_rows if row["controlled_recovery_decision"] == SAFE_DECISION]
    risky_rows = [row for row in recovery_rows if row["controlled_recovery_decision"] == RISKY_DECISION]
    still_limited_rows = [row for row in recovery_rows if row["controlled_recovery_decision"] == STILL_LIMITED_DECISION]
    needs_human_rows = [row for row in recovery_rows if row["controlled_recovery_decision"] == HUMAN_DECISION]
    needs_rule_rows = [row for row in recovery_rows if row["controlled_recovery_decision"] == RULE_DECISION]
    needs_vlm_rows = [row for row in recovery_rows if row["controlled_recovery_decision"] == VLM_DECISION]
    guardrail_rows = [row for row in recovery_rows if row["controlled_recovery_decision"] == GUARDRAIL_DECISION]

    semantic_distribution = Counter(_safe_text(row.get("semantic_metric_class")) for row in selected_rows)
    unit_action_distribution = Counter(_safe_text(row.get("controlled_unit_repair_action")) for row in recovery_rows)
    semantic_dist_rows = [
        {"semantic_metric_class": semantic_class, "row_count": count}
        for semantic_class, count in sorted(semantic_distribution.items())
    ]
    unit_action_rows = [
        {"controlled_unit_repair_action": action, "row_count": count}
        for action, count in sorted(unit_action_distribution.items())
    ]

    lineage_rows = []
    for row in recovery_rows:
        lineage_rows.append(
            {
                "source_row_id": row.get("source_row_id"),
                "demo_export_row_id": row.get("demo_export_row_id"),
                "source_pdf_name": row.get("source_pdf_name"),
                "source_page": row.get("source_page"),
                "source_table_id": row.get("source_table_id"),
                "minimum_lineage_present": _minimum_lineage_present(row),
                "source_trace_available": _bool_value(row.get("source_trace_available")),
                "evidence_strength": row.get("evidence_strength"),
                "evidence_weakness": _bool_value(row.get("evidence_weakness")),
                "controlled_recovery_decision": row.get("controlled_recovery_decision"),
            }
        )

    value_sanitizer_attempt_count = len(selected_rows)
    sanitized_value_success_count = sum(1 for row in recovery_rows if row["value_parse_status"] == "PARSED")
    sanitized_value_failure_count = sum(1 for row in recovery_rows if row["value_parse_status"] != "PARSED")
    semantic_class_known_count = sum(1 for row in recovery_rows if row["semantic_metric_class"] != "UNKNOWN")
    semantic_class_unknown_count = sum(1 for row in recovery_rows if row["semantic_metric_class"] == "UNKNOWN")
    unit_repair_attempt_count = sum(1 for row in recovery_rows if row["controlled_unit_repair_action"] != "NO_CHANGE")
    unit_repair_success_count = sum(
        1
        for row in recovery_rows
        if row["controlled_recovery_decision"] in {SAFE_DECISION, RISKY_DECISION}
        and not _bool_value(row["unit_semantic_mismatch"])
    )
    unit_semantic_mismatch_count = sum(1 for row in recovery_rows if _bool_value(row["unit_semantic_mismatch"]))
    evidence_weakness_count = sum(1 for row in recovery_rows if _bool_value(row["evidence_weakness"]))
    lineage_audit_passed = all(
        _bool_value(row["minimum_lineage_present"]) and _bool_value(row["source_trace_available"])
        for row in lineage_rows
    ) if lineage_rows else False

    guardrail_summary = {
        "false_positive_guardrail_hit_count": len(guardrail_rows),
        "guardrail_reason_distribution": dict(Counter(_safe_text(row.get("guardrail_reason")) for row in recovery_rows if _safe_text(row.get("guardrail_reason")))),
        "strict_guardrails": strict_guardrails,
        "include_image_bound_first": include_image_bound_first,
        "include_json_md_context_bound": include_json_md_context_bound,
        "rule_change_log_count": len(rule_change_log) if isinstance(rule_change_log, list) else 0,
        "quality_caveat_row_count": len(quality_caveats) if isinstance(quality_caveats, list) else 0,
        "negative_examples_from_346b2_count": len(false_positive_rows),
        "unit_audit_reference_row_count": len(unit_audit_rows),
        "refined_safe_reference_row_count": len(refined_safe_rows),
        "reaudit_safe_reference_row_count": len(reaudit_safe_rows),
        "candidate_reaudit_reference_row_count": len(candidate_reaudit_rows),
    }

    safe_to_continue_expansion = bool(
        len(selected_rows) > 0
        and len(recovery_rows) == len(selected_rows)
        and len(risky_rows) == 0
        and len(still_limited_rows) == 0
        and len(needs_human_rows) == 0
        and len(needs_rule_rows) == 0
        and len(needs_vlm_rows) == 0
        and len(guardrail_rows) == 0
        and unit_semantic_mismatch_count == 0
        and semantic_class_unknown_count == 0
        and evidence_weakness_count == 0
        and lineage_audit_passed
    )
    if safe_to_continue_expansion:
        safe_to_continue_expansion_reason = (
            "The controlled batch stayed within 346B3/346B2R guardrails, preserved lineage, and produced only safe demo-only sidecar candidates. Independent 346B4R QA should audit this batch before any broader rollout."
        )
        recommended_next_step = "346B4R Controlled Expansion QA Audit"
        recommended_next_step_reason = "Controlled expansion candidates are ready for independent QA before any larger expansion."
    else:
        safe_to_continue_expansion_reason = (
            "The controlled batch surfaced remaining non-safe buckets or guardrail issues, so broader expansion must stay blocked until QA or rule refinement resolves them."
        )
        recommended_next_step = "346B3R Recovery Rule Refinement Patch"
        recommended_next_step_reason = "At least one selected row still needs human review, rule refinement, guardrail resolution, or further QA."

    expansion_readiness_report = {
        "safe_to_continue_expansion": safe_to_continue_expansion,
        "safe_to_continue_expansion_reason": safe_to_continue_expansion_reason,
        "recommended_next_step": recommended_next_step,
        "recommended_next_step_reason": recommended_next_step_reason,
        "max_expansion_rows": max_expansion_rows,
        "selection_mode": selection_mode,
    }

    manifest = {
        "decision": READY_DECISION_346B4,
        "input_stage": INPUT_STAGE_346B4,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "input_345d_decision": _safe_text(manifest_345d.get("decision")),
        "input_346a_decision": _safe_text(manifest_346a.get("decision")),
        "input_346a2_decision": _safe_text(manifest_346a2.get("decision")),
        "input_346b_decision": _safe_text(manifest_346b.get("decision")),
        "input_346b2_decision": _safe_text(manifest_346b2.get("decision")),
        "input_346b3_decision": _safe_text(manifest_346b3.get("decision")),
        "input_346b2r_decision": _safe_text(manifest_346b2r.get("decision")),
        "input_345d_dir": str(full_structured_demo_export_package_345d_dir),
        "input_346a_dir": str(vision_assisted_table_evidence_pilot_346a_dir),
        "input_346a2_dir": str(mineru_image_path_binding_fix_346a2_dir),
        "input_346b_dir": str(quality_limited_row_recovery_pilot_346b_dir),
        "input_346b2_dir": str(recovery_candidate_qa_audit_346b2_dir),
        "input_346b3_dir": str(recovery_rule_refinement_346b3_dir),
        "input_346b2r_dir": str(refined_recovery_candidate_qa_reaudit_346b2r_dir),
        "output_dir": str(output_dir),
        "full_quality_limited_row_count": int(manifest_345d.get("quality_limited_row_count", len(quality_rows))),
        "controlled_expansion_input_limit": max_expansion_rows,
        "controlled_expansion_input_row_count": len(selected_rows),
        "excluded_row_touched_count": excluded_row_touched_count,
        "already_demo_ready_row_touched_count": 0,
        "already_346b_pilot_row_count": 0,
        "new_quality_limited_row_count": len(selected_rows),
        "value_sanitizer_attempt_count": value_sanitizer_attempt_count,
        "sanitized_value_success_count": sanitized_value_success_count,
        "sanitized_value_failure_count": sanitized_value_failure_count,
        "semantic_class_known_count": semantic_class_known_count,
        "semantic_class_unknown_count": semantic_class_unknown_count,
        "unit_repair_attempt_count": unit_repair_attempt_count,
        "unit_repair_success_count": unit_repair_success_count,
        "unit_semantic_mismatch_count": unit_semantic_mismatch_count,
        "recovered_candidate_count": len(recovered_candidate_rows),
        "safe_recovered_candidate_count": len(safe_recovered_rows),
        "risky_candidate_count": len(risky_rows),
        "false_positive_guardrail_hit_count": len(guardrail_rows),
        "still_quality_limited_count": len(still_limited_rows),
        "needs_human_review_count": len(needs_human_rows),
        "needs_rule_refinement_count": len(needs_rule_rows),
        "needs_vlm_count": len(needs_vlm_rows),
        "lineage_audit_passed": lineage_audit_passed,
        "evidence_weakness_count": evidence_weakness_count,
        "safe_to_continue_expansion": safe_to_continue_expansion,
        "safe_to_continue_expansion_reason": safe_to_continue_expansion_reason,
        "recommended_next_step": recommended_next_step,
        "recommended_next_step_reason": recommended_next_step_reason,
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
        "selection_mode": selection_mode,
        "require_346b2r_safe_to_expand": require_346b2r_safe_to_expand,
        "strict_guardrails": strict_guardrails,
        "include_image_bound_first": include_image_bound_first,
        "include_json_md_context_bound": include_json_md_context_bound,
        "max_context_chars": max_context_chars,
        "generated_at_utc": _utc_now(),
        "refined_policy_source": str(recovery_rule_refinement_346b3_dir / INPUT_346B3_POLICY_JSON_NAME),
        "recovery_scope": "QUALITY_LIMITED_ONLY",
        "sidecar_only": True,
        "quality_caveat_reference_count": len(quality_caveats) if isinstance(quality_caveats, list) else 0,
        "high_severity_skipped_count": high_severity_skipped_count,
        "strict_pending_skipped_count": strict_pending_skipped_count,
        "346b2r_safe_to_expand_confirmed": _bool_value(manifest_346b2r.get("safe_to_expand_recovery")),
        "346b2r_controlled_max_row_limit_suggestion": int(readiness_346b2r.get("controlled_max_row_limit_suggestion", 0) or 0),
    }

    validation_checks = [
        manifest["input_345d_decision"] == READY_DECISION_345D,
        manifest["input_346a_decision"] == READY_DECISION_346A,
        manifest["input_346a2_decision"] == READY_DECISION_346A2,
        manifest["input_346b_decision"] == READY_DECISION_346B,
        manifest["input_346b2_decision"] == READY_DECISION_346B2,
        manifest["input_346b3_decision"] == READY_DECISION_346B3,
        manifest["input_346b2r_decision"] == READY_DECISION_346B2R,
        int(manifest_345d.get("qa_fail_count", 1)) == 0,
        int(manifest_346a.get("qa_fail_count", 1)) == 0,
        int(manifest_346a2.get("qa_fail_count", 1)) == 0,
        int(manifest_346b.get("qa_fail_count", 1)) == 0,
        int(manifest_346b2.get("qa_fail_count", 1)) == 0,
        int(manifest_346b3.get("qa_fail_count", 1)) == 0,
        int(manifest_346b2r.get("qa_fail_count", 1)) == 0,
        _bool_value(manifest_346b2r.get("safe_to_expand_recovery")) is True,
        int(manifest_346a.get("live_vlm_call_count", 0)) == 0,
        int(manifest_346a2.get("live_vlm_call_count", 0)) == 0,
        int(manifest_346b.get("live_vlm_call_count", 0)) == 0,
        int(manifest_346b2.get("live_vlm_call_count", 0)) == 0,
        int(manifest_346b3.get("live_vlm_call_count", 0)) == 0,
        int(manifest_346b2r.get("live_vlm_call_count", 0)) == 0,
        _bool_value(manifest_345d.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346a.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346a2.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346b.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346b2.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346b3.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346b2r.get("formal_client_export_allowed")) is False,
        len(selected_rows) <= max_expansion_rows,
        len(selected_rows)
        == (
            len(recovered_candidate_rows)
            + len(still_limited_rows)
            + len(needs_human_rows)
            + len(needs_rule_rows)
            + len(needs_vlm_rows)
            + len(guardrail_rows)
        ),
        len(recovered_candidate_rows) == len(safe_recovered_rows) + len(risky_rows),
        manifest["excluded_row_touched_count"] == 0,
        manifest["already_demo_ready_row_touched_count"] == 0,
        manifest["already_346b_pilot_row_count"] == 0,
        all(_safe_text(row.get("source_row_id")) not in pilot_source_ids for row in selected_rows),
        all(_safe_text(row.get("source_row_id")) not in demo_source_ids for row in selected_rows),
        all(_bool_value(row.get("selected_from_quality_limited_pool")) for row in selected_rows),
        all(_safe_text(row.get("semantic_metric_class")) != "UNKNOWN" for row in safe_recovered_rows),
        all(_normalize_unit_token(row.get("controlled_recovered_unit")) not in PERCENT_UNITS for row in safe_recovered_rows if _safe_text(row.get("semantic_metric_class")) == "RATIO_MULTIPLE"),
        all(_normalize_unit_token(row.get("controlled_recovered_unit")) not in PERCENT_UNITS for row in safe_recovered_rows if _safe_text(row.get("semantic_metric_class")) == "PER_SHARE"),
        all(_normalize_unit_token(row.get("controlled_recovered_unit")) in PERCENT_UNITS for row in safe_recovered_rows if _safe_text(row.get("semantic_metric_class")) == "PERCENTAGE_OR_MARGIN"),
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
        manifest["upstream_data_mutated"] is False,
        bool(refined_policy),
        bool(rule_change_log),
        quality_rows_source in {"json", "csv"},
        demo_rows_source in {"json", "csv"},
        candidate_pool_rows_source in {"json", "csv"},
        pilot_rows_source in {"json", "csv"},
        recovered_346b_rows_source in {"json", "csv"},
        false_positive_rows_source in {"json", "csv"},
        unit_audit_rows_source in {"json", "csv"},
        bound_rows_source in {"json", "csv"},
        refined_safe_rows_source in {"json", "csv"},
        reaudit_safe_rows_source in {"json", "csv"},
        candidate_reaudit_rows_source in {"json", "csv"},
    ]

    no_apply_proof = build_no_apply_proof(
        stage="346B4",
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
    no_apply_proof["sidecar_controlled_expansion_only"] = True
    no_apply_proof["no_write_back"] = True

    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_346b4")
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
    manifest["decision"] = READY_DECISION_346B4 if qa_fail_count == 0 else BLOCKED_DECISION_346B4

    if ledger_path is not None:
        append_346b4_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = _ledger_has_346b4_entry(ledger_path)
        if not manifest["milestone_ledger_updated"]:
            manifest["qa_fail_count"] += 1
            manifest["decision"] = BLOCKED_DECISION_346B4

    return {
        "manifest": manifest,
        "selected_rows": selected_rows,
        "recovery_results_rows": recovery_rows,
        "recovered_candidate_rows": recovered_candidate_rows,
        "safe_recovered_candidate_rows": safe_recovered_rows,
        "still_limited_rows": still_limited_rows,
        "needs_human_review_rows": needs_human_rows,
        "needs_rule_refinement_rows": needs_rule_rows,
        "needs_vlm_rows": needs_vlm_rows,
        "false_positive_guardrail_rows": guardrail_rows,
        "semantic_class_distribution_rows": semantic_dist_rows,
        "unit_action_distribution_rows": unit_action_rows,
        "lineage_evidence_audit_rows": lineage_rows,
        "guardrail_summary": guardrail_summary,
        "expansion_readiness_report": expansion_readiness_report,
        "executive_summary_md": render_executive_summary_markdown(
            manifest,
            semantic_distribution=dict(semantic_distribution),
            unit_action_distribution=dict(unit_action_distribution),
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
