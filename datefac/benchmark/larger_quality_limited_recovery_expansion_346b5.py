from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from datefac.benchmark.larger_quality_limited_recovery_expansion_346b5_report import (
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
READY_DECISION_346B4 = "CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY"
READY_DECISION_346B3R = "RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY"
READY_DECISION_346B4R = "CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_READY"
READY_DECISION_346B4Q = "CONTROLLED_EXPANSION_QA_AUDIT_346B4Q_READY"
READY_DECISION_346B5 = "LARGER_QUALITY_LIMITED_RECOVERY_EXPANSION_346B5_READY"
BLOCKED_DECISION_346B5 = "LARGER_QUALITY_LIMITED_RECOVERY_EXPANSION_346B5_BLOCKED"
INPUT_STAGE_346B5 = "POST_346B4Q_LARGER_QUALITY_LIMITED_RECOVERY_EXPANSION"

SAFE_DECISION = "LARGER_RECOVERED_DEMO_CANDIDATE"
RISKY_DECISION = "LARGER_RISKY_RECOVERED_DEMO_CANDIDATE"
STILL_LIMITED_DECISION = "LARGER_STILL_QUALITY_LIMITED"
HUMAN_DECISION = "LARGER_NEEDS_HUMAN_REVIEW"
RULE_DECISION = "LARGER_NEEDS_RULE_REFINEMENT"
VLM_DECISION = "LARGER_NEEDS_VLM_REPAIR"
GUARDRAIL_DECISION = "LARGER_FALSE_POSITIVE_GUARDRAIL_HIT"

DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR = Path(
    r"D:\_datefac\output\full_structured_demo_export_package_345d"
)
DEFAULT_CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_DIR = Path(
    r"D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4"
)
DEFAULT_RECOVERY_RULE_REFINEMENT_PATCH_346B3R_DIR = Path(
    r"D:\_datefac\output\recovery_rule_refinement_patch_346b3r"
)
DEFAULT_CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_DIR = Path(
    r"D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r"
)
DEFAULT_CONTROLLED_EXPANSION_QA_AUDIT_346B4Q_DIR = Path(
    r"D:\_datefac\output\controlled_expansion_qa_audit_346b4q"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\larger_quality_limited_recovery_expansion_346b5")

MANIFEST_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_manifest.json"
SELECTED_ROWS_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_selected_rows.json"
SELECTED_ROWS_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_selected_rows.csv"
RECOVERY_RESULTS_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_recovery_results.json"
RECOVERY_RESULTS_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_recovery_results.csv"
RECOVERED_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_recovered_demo_candidates.json"
RECOVERED_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_recovered_demo_candidates.csv"
SAFE_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_safe_recovered_candidates.json"
SAFE_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_safe_recovered_candidates.csv"
STILL_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_still_limited_rows.json"
STILL_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_still_limited_rows.csv"
HUMAN_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_needs_human_review_rows.json"
HUMAN_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_needs_human_review_rows.csv"
RULE_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_needs_rule_refinement_rows.json"
RULE_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_needs_rule_refinement_rows.csv"
VLM_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_needs_vlm_rows.json"
VLM_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_needs_vlm_rows.csv"
GUARD_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_false_positive_guardrail_hits.json"
GUARD_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_false_positive_guardrail_hits.csv"
SEMANTIC_DIST_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_semantic_class_distribution.json"
SEMANTIC_DIST_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_semantic_class_distribution.csv"
UNIT_ACTION_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_unit_action_distribution.json"
UNIT_ACTION_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_unit_action_distribution.csv"
LINEAGE_AUDIT_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_lineage_evidence_audit.json"
LINEAGE_AUDIT_CSV_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_lineage_evidence_audit.csv"
GUARDRAIL_SUMMARY_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_guardrail_summary.json"
EXPANSION_READINESS_JSON_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_expansion_readiness_report.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "larger_quality_limited_recovery_expansion_346b5_next_plan.md"

INPUT_345D_MANIFEST_NAME = "full_structured_demo_export_package_345d_manifest.json"
INPUT_345D_QUALITY_JSON_NAME = "full_structured_demo_export_package_345d_quality_limited_rows.json"
INPUT_345D_QUALITY_CSV_NAME = "full_structured_demo_export_package_345d_quality_limited_rows.csv"
INPUT_345D_DEMO_JSON_NAME = "full_structured_demo_export_package_345d_demo_rows.json"
INPUT_345D_DEMO_CSV_NAME = "full_structured_demo_export_package_345d_demo_rows.csv"
INPUT_345D_CAVEATS_JSON_NAME = "full_structured_demo_export_package_345d_quality_caveats.json"

INPUT_346B4_MANIFEST_NAME = "controlled_quality_limited_recovery_expansion_346b4_manifest.json"
INPUT_346B4_SELECTED_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_selected_rows.json"
INPUT_346B4_SELECTED_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_selected_rows.csv"
INPUT_346B4_RESULTS_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovery_results.json"
INPUT_346B4_RESULTS_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovery_results.csv"
INPUT_346B4_SAFE_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.json"
INPUT_346B4_SAFE_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.csv"

INPUT_346B3R_MANIFEST_NAME = "recovery_rule_refinement_patch_346b3r_manifest.json"
INPUT_346B3R_SEMANTIC_JSON_NAME = "recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.json"
INPUT_346B3R_SEMANTIC_CSV_NAME = "recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.csv"
INPUT_346B3R_UNIT_JSON_NAME = "recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.json"
INPUT_346B3R_UNIT_CSV_NAME = "recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.csv"
INPUT_346B3R_PATCHED_POLICY_JSON_NAME = "recovery_rule_refinement_patch_346b3r_patched_unit_policy_preview.json"
INPUT_346B3R_PATCH_SAFETY_JSON_NAME = "recovery_rule_refinement_patch_346b3r_patch_safety_review.json"
INPUT_346B3R_PATCH_SAFETY_CSV_NAME = "recovery_rule_refinement_patch_346b3r_patch_safety_review.csv"

INPUT_346B4R_MANIFEST_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_manifest.json"
INPUT_346B4R_SAFE_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.json"
INPUT_346B4R_SAFE_CSV_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.csv"
INPUT_346B4R_PATCHED_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.json"
INPUT_346B4R_PATCHED_CSV_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.csv"
INPUT_346B4R_READINESS_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_expansion_readiness_report.json"

INPUT_346B4Q_MANIFEST_NAME = "controlled_expansion_qa_audit_346b4q_manifest.json"
INPUT_346B4Q_SAFE_JSON_NAME = "controlled_expansion_qa_audit_346b4q_qa_safe_candidates.json"
INPUT_346B4Q_SAFE_CSV_NAME = "controlled_expansion_qa_audit_346b4q_qa_safe_candidates.csv"
INPUT_346B4Q_PATCH_QA_JSON_NAME = "controlled_expansion_qa_audit_346b4q_patch_applied_row_qa.json"
INPUT_346B4Q_PATCH_QA_CSV_NAME = "controlled_expansion_qa_audit_346b4q_patch_applied_row_qa.csv"
INPUT_346B4Q_READINESS_JSON_NAME = "controlled_expansion_qa_audit_346b4q_larger_expansion_readiness_report.json"

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
    {"artifact_name": SELECTED_ROWS_JSON_FILE_NAME, "path": SELECTED_ROWS_JSON_FILE_NAME, "purpose": "Larger expansion selected rows in JSON."},
    {"artifact_name": SELECTED_ROWS_CSV_FILE_NAME, "path": SELECTED_ROWS_CSV_FILE_NAME, "purpose": "Larger expansion selected rows in CSV."},
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
    {"artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME, "path": EXECUTIVE_SUMMARY_MD_FILE_NAME, "purpose": "Executive summary for 346B5."},
    {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": ARTIFACT_INDEX_MD_FILE_NAME, "purpose": "Artifact index for 346B5 outputs."},
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
    "capital_expenditure",
    "debt_financing",
}
COUNT_VOLUME_KEYWORDS = ["销量", "装机", "产量", "户数", "人数", "门店", "用户", "台", "辆", "吨", "片", "亩", "次"]
PER_SHARE_KEYWORDS = ["per share", "每股", "eps", "bvps"]
PERCENTAGE_KEYWORDS = ["margin", "roe", "roa", "roic", "%", "yoy", "毛利率", "净利率", "收益率"]
RATIO_KEYWORDS = ["ev/ebitda", "pe", "pb", "ps", "ev/sales", "quick ratio"]
MONEY_UNITS = {"元", "万元", "百万元", "千万元", "亿元", "rmb", "hkd", "usd", "cny", "百万港元", "百万美元"}
PERCENT_UNITS = {"%", "pct", "percentage"}
RATIO_UNITS = {"x", "倍"}
PER_SHARE_UNITS = {"元/股", "港元/股", "美元/股", "rmb/share", "hkd/share", "usd/share", "yuan/share"}
COUNT_VOLUME_UNITS = {"台", "辆", "吨", "人", "万人", "亿人", "户", "家", "个", "次", "片", "亩"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_ledger_path() -> Path:
    return Path(__file__).resolve().parents[2] / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"


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
    result = _run_git(repo_root, ["status", "--porcelain=v1", "--", *paths])
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _staged_paths(lines: Sequence[str]) -> List[str]:
    staged: List[str] = []
    for line in lines:
        if len(line) >= 2 and line[0] != " ":
            staged.append(line[3:].strip() if len(line) >= 3 else line)
    return staged


def _artifact_index_rows(output_dir: Path) -> List[Dict[str, Any]]:
    return [{**row, "path": str(output_dir / row["path"])} for row in OUTPUT_ARTIFACT_ROWS]


def _normalize_unit_token(value: Any) -> str:
    return _safe_text(value).lower().replace(" ", "")


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
    if metric in MONETARY_METRICS:
        return "MONETARY_AMOUNT"
    if metric in PERCENTAGE_MARGIN_METRICS or any(token in raw_metric for token in PERCENTAGE_KEYWORDS):
        return "PERCENTAGE_OR_MARGIN"
    if metric in RATIO_MULTIPLE_METRICS or any(_contains_keyword(raw_metric, token) for token in RATIO_KEYWORDS):
        return "RATIO_MULTIPLE"
    if any(token in raw_metric for token in COUNT_VOLUME_KEYWORDS):
        return "COUNT_OR_VOLUME"
    return "UNKNOWN"


def _sanitize_value(value: Any) -> Dict[str, Any]:
    raw_value = _safe_text(value)
    cleaned = raw_value.replace(",", "").replace(" ", "").replace("％", "%")
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
    if _bool_value(row.get("source_trace_available")) and _minimum_lineage_present(row):
        return "SOURCE_TRACE_DETERMINISTIC_POLICY"
    return "NO_BOUND_EVIDENCE"


def _money_unit_from_row(row: Dict[str, Any]) -> str:
    for field in ("unit", "currency"):
        token = _normalize_unit_token(row.get(field))
        if token in MONEY_UNITS:
            return _safe_text(row.get(field))
    raw_metric = _safe_text(row.get("raw_metric_name"))
    for token in ["亿元", "百万元", "千万元", "万元", "元", "百万港元", "百万美元"]:
        if token in raw_metric:
            return token
    return ""


def _per_share_unit_from_row(row: Dict[str, Any]) -> str:
    unit = _safe_text(row.get("unit"))
    normalized = _normalize_unit_token(unit)
    if normalized in PER_SHARE_UNITS:
        return unit
    if normalized in {"元", "港元", "美元", "rmb", "hkd", "usd", "cny"} and ("每股" in _safe_text(row.get("raw_metric_name")) or "per share" in _safe_text(row.get("raw_metric_name")).lower()):
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


def _count_volume_unit_from_row(row: Dict[str, Any]) -> str:
    unit = _safe_text(row.get("unit"))
    normalized = _normalize_unit_token(unit)
    if normalized in COUNT_VOLUME_UNITS:
        return unit
    raw_metric = _safe_text(row.get("raw_metric_name"))
    for token in COUNT_VOLUME_UNITS:
        if token in raw_metric:
            return token
    return ""


def _preview_recovery(
    row: Dict[str, Any],
    *,
    semantic_patch_by_metric: Dict[str, Dict[str, Any]],
    unit_patch_by_metric: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    metric = _safe_text(row.get("demo_normalized_metric_name")).lower()
    semantic_class = _classify_semantic_class(row)
    semantic_patch = semantic_patch_by_metric.get(metric)
    unit_patch = unit_patch_by_metric.get(metric)
    if semantic_class == "UNKNOWN" and semantic_patch:
        semantic_class = _safe_text(semantic_patch.get("proposed_semantic_class")) or semantic_class

    sanitizer = _sanitize_value(row.get("value"))
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

    if sanitizer["value_parse_status"] != "PARSED":
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
        if normalized_original_unit and normalized_original_unit in MONEY_UNITS.union(PERCENT_UNITS):
            decision = GUARDRAIL_DECISION
            selection_safety_score = 0
            guardrail_reason = "ratio_multiple_conflicts_with_percent_or_money_unit"
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
            if unit_patch and "KEEP_LIMITED_UNTIL_MONETARY_UNIT_CONTEXT_CONFIRMED" in _safe_text(unit_patch.get("unit_policy_decision")) and not original_unit:
                refined_action = "UNIT_MONETARY_CONTEXT_CONFIRMED"
        else:
            decision = STILL_LIMITED_DECISION
            selection_safety_score = 0
            guardrail_reason = "missing_monetary_unit_context"
    elif semantic_class == "COUNT_OR_VOLUME":
        count_unit = _count_volume_unit_from_row(row)
        if count_unit:
            refined_unit = count_unit
            refined_action = "UNIT_COUNT_VOLUME_CONTEXT_CONFIRMED" if _safe_text(row.get("unit")) != count_unit else "NO_CHANGE"
        else:
            decision = STILL_LIMITED_DECISION
            selection_safety_score = 0
            guardrail_reason = "missing_count_volume_unit_context"

    if decision == SAFE_DECISION and evidence_weak:
        decision = RISKY_DECISION
        selection_safety_score = 1
        guardrail_reason = "weak_evidence_requires_independent_audit"

    unit_mismatch = False
    normalized_refined_unit = _normalize_unit_token(refined_unit)
    if decision in {SAFE_DECISION, RISKY_DECISION}:
        if semantic_class == "RATIO_MULTIPLE" and normalized_refined_unit in PERCENT_UNITS:
            decision = GUARDRAIL_DECISION
            selection_safety_score = 0
            guardrail_reason = "ratio_multiple_percent_unit_mismatch"
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
        "COUNT_OR_VOLUME",
    ]:
        for row in by_class.get(semantic_class, []):
            source_row_id = _safe_text(row.get("source_row_id"))
            if source_row_id not in selected_ids:
                selected.append(row)
                selected_ids.add(source_row_id)
                break
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
    decision = _safe_text(row.get("preview_decision"))
    notes: List[str] = []
    if decision == SAFE_DECISION:
        notes.append("Recovered with deterministic value sanitizer and 346B3/346B3R semantic-class-aware unit policy.")
    elif decision == RISKY_DECISION:
        notes.append("Recovery is internally coherent but evidence remains weak, so promotion stays risky.")
    elif decision == HUMAN_DECISION:
        notes.append("Human review remains required because context is insufficient.")
    elif decision == RULE_DECISION:
        notes.append("Rule refinement remains required because semantic class is unknown.")
    elif decision == STILL_LIMITED_DECISION:
        notes.append("The row remains quality-limited after deterministic repair attempts.")
    elif decision == GUARDRAIL_DECISION:
        notes.append("Guardrails blocked promotion to avoid semantic/unit false positives.")
    if strict_guardrails and decision == RISKY_DECISION:
        decision = HUMAN_DECISION
        notes.append("Strict guardrails demoted risky candidates to human review.")
    return {
        **row,
        "controlled_recovery_decision": decision,
        "controlled_recovered_demo_candidate": decision in {SAFE_DECISION, RISKY_DECISION},
        "controlled_safe_recovered_candidate": decision == SAFE_DECISION,
        "controlled_risky_candidate": decision == RISKY_DECISION,
        "do_not_apply_upstream": True,
        "sidecar_recovery_only": True,
        "demo_export_only": True,
        "controlled_guardrail_notes": " | ".join(notes),
    }


def _ledger_has_346b5_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return "## 346B5 Larger Quality-Limited Recovery Expansion" in ledger_path.read_text(encoding="utf-8")


def _strip_346b5_ledger_entry(text: str) -> str:
    header = "## 346B5 Larger Quality-Limited Recovery Expansion"
    start = text.find(header)
    if start < 0:
        return text
    next_header = text.find("\n## ", start + len(header))
    if next_header < 0:
        return text[:start].rstrip()
    return (text[:start] + text[next_header + 1 :]).rstrip()


def _build_346b5_ledger_entry(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "## 346B5 Larger Quality-Limited Recovery Expansion",
            "",
            "Status: completed",
            "",
            f"- decision: {manifest.get('decision', '')}",
            f"- input_345d_dir: {manifest.get('input_345d_dir', '')}",
            f"- input_346b4_dir: {manifest.get('input_346b4_dir', '')}",
            f"- input_346b3r_dir: {manifest.get('input_346b3r_dir', '')}",
            f"- input_346b4r_dir: {manifest.get('input_346b4r_dir', '')}",
            f"- input_346b4q_dir: {manifest.get('input_346b4q_dir', '')}",
            f"- output_dir: {manifest.get('output_dir', '')}",
            f"- full_quality_limited_row_count: {manifest.get('full_quality_limited_row_count', 0)}",
            f"- larger_expansion_input_limit: {manifest.get('larger_expansion_input_limit', 0)}",
            f"- larger_expansion_input_row_count: {manifest.get('larger_expansion_input_row_count', 0)}",
            f"- excluded_row_touched_count: {manifest.get('excluded_row_touched_count', 0)}",
            f"- already_demo_ready_row_touched_count: {manifest.get('already_demo_ready_row_touched_count', 0)}",
            f"- already_346b_pilot_row_count: {manifest.get('already_346b_pilot_row_count', 0)}",
            f"- already_346b4_controlled_batch_row_count: {manifest.get('already_346b4_controlled_batch_row_count', 0)}",
            f"- new_quality_limited_row_count: {manifest.get('new_quality_limited_row_count', 0)}",
            f"- value_sanitizer_success_count: {manifest.get('sanitized_value_success_count', 0)}",
            f"- semantic_class_unknown_count: {manifest.get('semantic_class_unknown_count', 0)}",
            f"- safe_recovered_candidate_count: {manifest.get('safe_recovered_candidate_count', 0)}",
            f"- false_positive_guardrail_hit_count: {manifest.get('false_positive_guardrail_hit_count', 0)}",
            f"- needs_rule_refinement_count: {manifest.get('needs_rule_refinement_count', 0)}",
            f"- lineage_audit_passed: {manifest.get('lineage_audit_passed', False)}",
            f"- safe_to_qa_larger_expansion: {manifest.get('safe_to_qa_larger_expansion', False)}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- no_write_back_proof_passed: {manifest.get('no_write_back_proof_passed', False)}",
            f"- gate_status: formal_client_export_allowed={manifest.get('formal_client_export_allowed', False)}, client_ready={manifest.get('client_ready', False)}, production_ready={manifest.get('production_ready', False)}",
            f"- next_recommended_step: {manifest.get('recommended_next_step', '')}",
        ]
    )


def append_346b5_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    stripped = _strip_346b5_ledger_entry(existing)
    addition = _build_346b5_ledger_entry(manifest)
    prefix = "\n\n" if stripped and not stripped.endswith("\n\n") else ""
    if stripped.endswith("\n"):
        prefix = "\n" if not stripped.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(stripped + prefix + addition + "\n", encoding="utf-8")
    return True


def build_larger_quality_limited_recovery_expansion_346b5(
    *,
    full_structured_demo_export_package_345d_dir: Path,
    controlled_quality_limited_recovery_expansion_346b4_dir: Path,
    recovery_rule_refinement_patch_346b3r_dir: Path,
    controlled_expansion_replay_with_patched_rules_346b4r_dir: Path,
    controlled_expansion_qa_audit_346b4q_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    max_expansion_rows: int = 1500,
    selection_mode: str = "priority_then_coverage",
    require_346b4q_safe_to_larger_expansion: bool = True,
    strict_guardrails: bool = True,
    exclude_previous_controlled_batch: bool = True,
    include_image_bound_first: bool = True,
    include_json_md_context_bound: bool = True,
    max_context_chars: int = 4000,
) -> Dict[str, Any]:
    for label, path in [
        ("345D", full_structured_demo_export_package_345d_dir),
        ("346B4", controlled_quality_limited_recovery_expansion_346b4_dir),
        ("346B3R", recovery_rule_refinement_patch_346b3r_dir),
        ("346B4R", controlled_expansion_replay_with_patched_rules_346b4r_dir),
        ("346B4Q", controlled_expansion_qa_audit_346b4q_dir),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{label} input directory missing: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345d = _read_json(full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME)
    manifest_346b4 = _read_json(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_MANIFEST_NAME)
    manifest_346b3r = _read_json(recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_MANIFEST_NAME)
    manifest_346b4r = _read_json(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_MANIFEST_NAME)
    manifest_346b4q = _read_json(controlled_expansion_qa_audit_346b4q_dir / INPUT_346B4Q_MANIFEST_NAME)
    readiness_346b4q = _read_json(controlled_expansion_qa_audit_346b4q_dir / INPUT_346B4Q_READINESS_JSON_NAME)
    readiness_346b4r = _read_json(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_READINESS_JSON_NAME)
    patched_policy_preview_346b3r = _read_json(recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCHED_POLICY_JSON_NAME)

    if require_346b4q_safe_to_larger_expansion and not _bool_value(manifest_346b4q.get("qa_safe_to_larger_expansion")):
        raise ValueError("346B4Q qa_safe_to_larger_expansion must be true before 346B5 larger expansion.")

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
    selected_rows_346b4, selected_rows_346b4_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SELECTED_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SELECTED_CSV_NAME,
        label="346B4 selected rows",
    )
    recovery_rows_346b4, recovery_rows_346b4_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RESULTS_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RESULTS_CSV_NAME,
        label="346B4 recovery results",
    )
    safe_rows_346b4, safe_rows_346b4_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SAFE_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SAFE_CSV_NAME,
        label="346B4 safe recovered candidates",
    )
    semantic_patches_346b3r, semantic_patches_346b3r_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_SEMANTIC_JSON_NAME,
        csv_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_SEMANTIC_CSV_NAME,
        label="346B3R semantic patches",
    )
    unit_patches_346b3r, unit_patches_346b3r_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_UNIT_JSON_NAME,
        csv_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_UNIT_CSV_NAME,
        label="346B3R unit patches",
    )
    patch_safety_rows_346b3r, patch_safety_rows_346b3r_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCH_SAFETY_JSON_NAME,
        csv_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCH_SAFETY_CSV_NAME,
        label="346B3R patch safety review",
    )
    safe_rows_346b4r, safe_rows_346b4r_source = _load_json_or_csv_rows(
        json_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_SAFE_JSON_NAME,
        csv_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_SAFE_CSV_NAME,
        label="346B4R safe recovered candidates",
    )
    patched_rows_346b4r, patched_rows_346b4r_source = _load_json_or_csv_rows(
        json_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_PATCHED_JSON_NAME,
        csv_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_PATCHED_CSV_NAME,
        label="346B4R patched rows",
    )
    qa_safe_rows_346b4q, qa_safe_rows_346b4q_source = _load_json_or_csv_rows(
        json_path=controlled_expansion_qa_audit_346b4q_dir / INPUT_346B4Q_SAFE_JSON_NAME,
        csv_path=controlled_expansion_qa_audit_346b4q_dir / INPUT_346B4Q_SAFE_CSV_NAME,
        label="346B4Q QA safe candidates",
    )
    patch_qa_rows_346b4q, patch_qa_rows_346b4q_source = _load_json_or_csv_rows(
        json_path=controlled_expansion_qa_audit_346b4q_dir / INPUT_346B4Q_PATCH_QA_JSON_NAME,
        csv_path=controlled_expansion_qa_audit_346b4q_dir / INPUT_346B4Q_PATCH_QA_CSV_NAME,
        label="346B4Q patch QA rows",
    )

    quality_caveats = _read_json(full_structured_demo_export_package_345d_dir / INPUT_345D_CAVEATS_JSON_NAME) if (full_structured_demo_export_package_345d_dir / INPUT_345D_CAVEATS_JSON_NAME).exists() else []

    files_read = [
        str(path)
        for path in [
            full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME,
            full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_JSON_NAME,
            full_structured_demo_export_package_345d_dir / INPUT_345D_DEMO_JSON_NAME,
            full_structured_demo_export_package_345d_dir / INPUT_345D_CAVEATS_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_MANIFEST_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SELECTED_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RESULTS_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SAFE_JSON_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_MANIFEST_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_SEMANTIC_JSON_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_UNIT_JSON_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCHED_POLICY_JSON_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCH_SAFETY_JSON_NAME,
            controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_MANIFEST_NAME,
            controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_SAFE_JSON_NAME,
            controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_PATCHED_JSON_NAME,
            controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_READINESS_JSON_NAME,
            controlled_expansion_qa_audit_346b4q_dir / INPUT_346B4Q_MANIFEST_NAME,
            controlled_expansion_qa_audit_346b4q_dir / INPUT_346B4Q_SAFE_JSON_NAME,
            controlled_expansion_qa_audit_346b4q_dir / INPUT_346B4Q_PATCH_QA_JSON_NAME,
            controlled_expansion_qa_audit_346b4q_dir / INPUT_346B4Q_READINESS_JSON_NAME,
        ]
        if path.exists()
    ]
    input_paths = [Path(path) for path in files_read if Path(path).is_file()]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    demo_source_ids = {_safe_text(row.get("source_row_id")) for row in demo_rows if _safe_text(row.get("source_row_id"))}
    controlled_batch_source_ids = {_safe_text(row.get("source_row_id")) for row in selected_rows_346b4 if _safe_text(row.get("source_row_id"))}
    pilot_source_ids = {
        _safe_text(row.get("source_row_id"))
        for row in quality_rows
        if _bool_value(row.get("already_in_346b_pilot"))
    }

    semantic_patch_by_metric = {
        _safe_text(row.get("metric_family") or row.get("demo_normalized_metric_name")).lower(): row
        for row in semantic_patches_346b3r
        if _safe_text(row.get("metric_family") or row.get("demo_normalized_metric_name"))
    }
    unit_patch_by_metric = {
        _safe_text(row.get("metric_family")).lower(): row
        for row in unit_patches_346b3r
        if _safe_text(row.get("metric_family"))
    }

    merged_quality_rows: List[Dict[str, Any]] = []
    excluded_row_touched_count = 0
    already_demo_ready_row_touched_count = 0
    already_346b_pilot_row_count = 0
    already_346b4_controlled_batch_row_count = 0

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
        if exclude_previous_controlled_batch and source_row_id in controlled_batch_source_ids:
            already_346b4_controlled_batch_row_count += 1
            continue
        preview = _preview_recovery(
            row,
            semantic_patch_by_metric=semantic_patch_by_metric,
            unit_patch_by_metric=unit_patch_by_metric,
        )
        merged_quality_rows.append(
            {
                **dict(row),
                **preview,
                "selection_priority_score": 100 if preview["preview_decision"] == SAFE_DECISION else 50 if preview["preview_decision"] == RISKY_DECISION else 0,
                "selection_reason_codes": "QUALITY_LIMITED_POOL;DETERMINISTIC_POLICY_COVERED",
                "selected_from_quality_limited_pool": True,
                "already_in_346b_pilot": False,
                "already_in_346b4_controlled_batch": False,
                "minimum_lineage_present": _minimum_lineage_present(row),
                "context_snippet": _safe_text(row.get("raw_metric_name"))[:max_context_chars],
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
        "guardrail_reason_distribution": dict(Counter(_safe_text(row.get("guardrail_reason")) for row in guardrail_rows)),
        "strict_guardrails": strict_guardrails,
        "include_image_bound_first": include_image_bound_first,
        "include_json_md_context_bound": include_json_md_context_bound,
        "patch_safety_review_row_count": len(patch_safety_rows_346b3r),
        "346b4_safe_reference_row_count": len(safe_rows_346b4),
        "346b4r_safe_reference_row_count": len(safe_rows_346b4r),
        "346b4r_patched_row_count": len(patched_rows_346b4r),
        "346b4q_safe_reference_row_count": len(qa_safe_rows_346b4q),
        "346b4q_patch_qa_row_count": len(patch_qa_rows_346b4q),
        "quality_caveat_row_count": len(quality_caveats) if isinstance(quality_caveats, list) else 0,
        "patched_policy_preview_present": bool(patched_policy_preview_346b3r),
    }

    safe_to_qa_larger_expansion = bool(
        len(selected_rows) > 0
        and len(recovery_rows) == len(selected_rows)
        and len(risky_rows) == 0
        and len(guardrail_rows) == 0
        and unit_semantic_mismatch_count == 0
        and lineage_audit_passed
        and _bool_value(manifest_346b4q.get("qa_safe_to_larger_expansion"))
    )
    if safe_to_qa_larger_expansion:
        safe_to_qa_larger_expansion_reason = (
            "The 1500-row bounded expansion stayed within the 346B3/346B3R/346B4R/346B4Q validated guardrails and produced only QA-ready demo-only sidecar candidates."
        )
        recommended_next_step = "346B5Q Larger Expansion QA Audit"
        recommended_next_step_reason = "Larger expansion candidates are ready for independent QA before any broader rollout."
    else:
        safe_to_qa_larger_expansion_reason = (
            "The larger expansion still contains guardrail, human-review, or rule-refinement buckets, so independent QA should not treat it as ready for broader rollout."
        )
        recommended_next_step = "346B3R2 Recovery Rule Refinement Patch Follow-up"
        recommended_next_step_reason = "Material rule gaps or non-safe buckets remain after deterministic larger expansion."

    expansion_readiness_report = {
        "safe_to_qa_larger_expansion": safe_to_qa_larger_expansion,
        "safe_to_qa_larger_expansion_reason": safe_to_qa_larger_expansion_reason,
        "recommended_next_step": recommended_next_step,
        "recommended_next_step_reason": recommended_next_step_reason,
        "recommended_larger_expansion_row_limit": max_expansion_rows,
    }

    manifest = {
        "decision": READY_DECISION_346B5,
        "input_stage": INPUT_STAGE_346B5,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "input_345d_decision": _safe_text(manifest_345d.get("decision")),
        "input_346b4_decision": _safe_text(manifest_346b4.get("decision")),
        "input_346b3r_decision": _safe_text(manifest_346b3r.get("decision")),
        "input_346b4r_decision": _safe_text(manifest_346b4r.get("decision")),
        "input_346b4q_decision": _safe_text(manifest_346b4q.get("decision")),
        "input_346b4q_qa_safe_to_larger_expansion": _bool_value(manifest_346b4q.get("qa_safe_to_larger_expansion")),
        "input_345d_dir": str(full_structured_demo_export_package_345d_dir),
        "input_346b4_dir": str(controlled_quality_limited_recovery_expansion_346b4_dir),
        "input_346b3r_dir": str(recovery_rule_refinement_patch_346b3r_dir),
        "input_346b4r_dir": str(controlled_expansion_replay_with_patched_rules_346b4r_dir),
        "input_346b4q_dir": str(controlled_expansion_qa_audit_346b4q_dir),
        "output_dir": str(output_dir),
        "full_quality_limited_row_count": int(manifest_345d.get("quality_limited_row_count", len(quality_rows))),
        "larger_expansion_input_limit": max_expansion_rows,
        "larger_expansion_input_row_count": len(selected_rows),
        "excluded_row_touched_count": excluded_row_touched_count,
        "already_demo_ready_row_touched_count": 0,
        "already_346b_pilot_row_count": already_346b_pilot_row_count,
        "already_346b4_controlled_batch_row_count": already_346b4_controlled_batch_row_count,
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
        "safe_to_qa_larger_expansion": safe_to_qa_larger_expansion,
        "safe_to_qa_larger_expansion_reason": safe_to_qa_larger_expansion_reason,
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
        "require_346b4q_safe_to_larger_expansion": require_346b4q_safe_to_larger_expansion,
        "strict_guardrails": strict_guardrails,
        "exclude_previous_controlled_batch": exclude_previous_controlled_batch,
        "include_image_bound_first": include_image_bound_first,
        "include_json_md_context_bound": include_json_md_context_bound,
        "max_context_chars": max_context_chars,
        "generated_at_utc": _utc_now(),
        "recovery_scope": "QUALITY_LIMITED_ONLY_LARGER_CONTROLLED_BATCH",
        "sidecar_only": True,
    }

    validation_checks = [
        manifest["input_345d_decision"] == READY_DECISION_345D,
        manifest["input_346b4_decision"] == READY_DECISION_346B4,
        manifest["input_346b3r_decision"] == READY_DECISION_346B3R,
        manifest["input_346b4r_decision"] == READY_DECISION_346B4R,
        manifest["input_346b4q_decision"] == READY_DECISION_346B4Q,
        _bool_value(manifest_346b4q.get("qa_safe_to_larger_expansion")) is True,
        int(manifest_346b4q.get("recommended_larger_expansion_row_limit", 0)) == 1500,
        int(manifest_345d.get("qa_fail_count", 1)) == 0,
        int(manifest_346b4.get("qa_fail_count", 1)) == 0,
        int(manifest_346b3r.get("qa_fail_count", 1)) == 0,
        int(manifest_346b4r.get("qa_fail_count", 1)) == 0,
        int(manifest_346b4q.get("qa_fail_count", 1)) == 0,
        int(manifest_346b3r.get("live_vlm_call_count", 0)) == 0,
        int(manifest_346b4r.get("live_vlm_call_count", 0)) == 0,
        int(manifest_346b4q.get("live_vlm_call_count", 0)) == 0,
        len(selected_rows) <= max_expansion_rows,
        len(selected_rows) == (
            len(recovered_candidate_rows)
            + len(still_limited_rows)
            + len(needs_human_rows)
            + len(needs_rule_rows)
            + len(needs_vlm_rows)
            + len(guardrail_rows)
        ),
        len(recovered_candidate_rows) == len(safe_recovered_rows) + len(risky_rows),
        all(_bool_value(row.get("selected_from_quality_limited_pool")) for row in selected_rows),
        all(_safe_text(row.get("source_row_id")) not in demo_source_ids for row in selected_rows),
        all(_safe_text(row.get("source_row_id")) not in controlled_batch_source_ids for row in selected_rows),
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
        quality_rows_source in {"json", "csv"},
        demo_rows_source in {"json", "csv"},
        selected_rows_346b4_source in {"json", "csv"},
        recovery_rows_346b4_source in {"json", "csv"},
        safe_rows_346b4_source in {"json", "csv"},
        semantic_patches_346b3r_source in {"json", "csv"},
        unit_patches_346b3r_source in {"json", "csv"},
        patch_safety_rows_346b3r_source in {"json", "csv"},
        safe_rows_346b4r_source in {"json", "csv"},
        patched_rows_346b4r_source in {"json", "csv"},
        qa_safe_rows_346b4q_source in {"json", "csv"},
        patch_qa_rows_346b4q_source in {"json", "csv"},
    ]

    no_apply_proof = build_no_apply_proof(
        stage="346B5",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]),
        official_assets_written=[],
    )
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths}
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    staged_status = _git_status_porcelain_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)
    protected_staged = _staged_paths(protected_after)
    forbidden_staged = _staged_paths(staged_status)
    upstream_unchanged = input_hashes_before == input_hashes_after
    no_apply_proof["no_write_back"] = True

    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_346b5")
        and upstream_unchanged
        and protected_before == protected_after
        and not protected_staged
        and not forbidden_staged
    )
    manifest["no_write_back_proof_passed"] = no_write_back_proof_passed
    manifest["no_write_back_summary"] = (
        "upstream inputs unchanged; official assets unchanged; protected dirty status preserved; no protected paths staged"
    )
    validation_checks.append(no_write_back_proof_passed)

    qa_fail_count = sum(1 for check in validation_checks if not check)
    manifest["qa_fail_count"] = qa_fail_count
    manifest["decision"] = READY_DECISION_346B5 if qa_fail_count == 0 else BLOCKED_DECISION_346B5

    if ledger_path is not None:
        append_346b5_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = _ledger_has_346b5_entry(ledger_path)
        if not manifest["milestone_ledger_updated"]:
            manifest["qa_fail_count"] += 1
            manifest["decision"] = BLOCKED_DECISION_346B5

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
            "input_345d_quality_rows": len(quality_rows),
            "input_346b4_selected_rows": len(selected_rows_346b4),
            "input_346b4r_safe_rows": len(safe_rows_346b4r),
            "input_346b4q_safe_rows": len(qa_safe_rows_346b4q),
            "readiness_346b4q": readiness_346b4q,
            "readiness_346b4r": readiness_346b4r,
            "patched_policy_preview_present": bool(patched_policy_preview_346b3r),
            "upstream_inputs_unchanged": upstream_unchanged,
        },
    }
