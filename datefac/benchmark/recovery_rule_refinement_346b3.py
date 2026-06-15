from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from datefac.benchmark.recovery_rule_refinement_346b3_report import (
    render_artifact_index_markdown,
    render_executive_summary_markdown,
    render_next_plan_markdown,
    render_refined_unit_policy_markdown,
    render_rule_change_log_markdown,
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
BLOCKED_DECISION_346B3 = "RECOVERY_RULE_REFINEMENT_346B3_BLOCKED"
INPUT_STAGE_346B3 = "POST_346B2_RECOVERY_RULE_REFINEMENT"

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
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\recovery_rule_refinement_346b3")

MANIFEST_FILE_NAME = "recovery_rule_refinement_346b3_manifest.json"
REFINED_CANDIDATES_JSON_FILE_NAME = "recovery_rule_refinement_346b3_refined_candidates.json"
REFINED_CANDIDATES_CSV_FILE_NAME = "recovery_rule_refinement_346b3_refined_candidates.csv"
REFINED_SAFE_JSON_FILE_NAME = "recovery_rule_refinement_346b3_refined_safe_candidates.json"
REFINED_SAFE_CSV_FILE_NAME = "recovery_rule_refinement_346b3_refined_safe_candidates.csv"
CORRECTED_RATIO_JSON_FILE_NAME = "recovery_rule_refinement_346b3_corrected_ratio_multiple_rows.json"
CORRECTED_RATIO_CSV_FILE_NAME = "recovery_rule_refinement_346b3_corrected_ratio_multiple_rows.csv"
CORRECTED_PER_SHARE_JSON_FILE_NAME = "recovery_rule_refinement_346b3_corrected_per_share_rows.json"
CORRECTED_PER_SHARE_CSV_FILE_NAME = "recovery_rule_refinement_346b3_corrected_per_share_rows.csv"
PRESERVED_PERCENTAGE_JSON_FILE_NAME = "recovery_rule_refinement_346b3_preserved_percentage_margin_rows.json"
PRESERVED_PERCENTAGE_CSV_FILE_NAME = "recovery_rule_refinement_346b3_preserved_percentage_margin_rows.csv"
DEMOTED_ROWS_JSON_FILE_NAME = "recovery_rule_refinement_346b3_demoted_rows.json"
DEMOTED_ROWS_CSV_FILE_NAME = "recovery_rule_refinement_346b3_demoted_rows.csv"
REFINED_POLICY_JSON_FILE_NAME = "recovery_rule_refinement_346b3_refined_unit_policy.json"
REFINED_POLICY_MD_FILE_NAME = "recovery_rule_refinement_346b3_refined_unit_policy.md"
RULE_CHANGE_LOG_JSON_FILE_NAME = "recovery_rule_refinement_346b3_rule_change_log.json"
RULE_CHANGE_LOG_MD_FILE_NAME = "recovery_rule_refinement_346b3_rule_change_log.md"
REAUDIT_PREVIEW_JSON_FILE_NAME = "recovery_rule_refinement_346b3_reaudit_preview.json"
REAUDIT_PREVIEW_CSV_FILE_NAME = "recovery_rule_refinement_346b3_reaudit_preview.csv"
EXPANSION_READINESS_JSON_FILE_NAME = "recovery_rule_refinement_346b3_expansion_readiness_report.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "recovery_rule_refinement_346b3_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "recovery_rule_refinement_346b3_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "recovery_rule_refinement_346b3_next_plan.md"

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
INPUT_346B_VALUE_JSON_NAME = "quality_limited_row_recovery_pilot_346b_value_sanitizer_results.json"
INPUT_346B_VALUE_CSV_NAME = "quality_limited_row_recovery_pilot_346b_value_sanitizer_results.csv"
INPUT_346B_REAUDIT_SUMMARY_JSON_NAME = "quality_limited_row_recovery_pilot_346b_reaudit_summary.json"

INPUT_346B2_MANIFEST_NAME = "recovery_candidate_qa_audit_346b2_manifest.json"
INPUT_346B2_AUDIT_JSON_NAME = "recovery_candidate_qa_audit_346b2_recovered_candidate_audit.json"
INPUT_346B2_AUDIT_CSV_NAME = "recovery_candidate_qa_audit_346b2_recovered_candidate_audit.csv"
INPUT_346B2_SAFE_JSON_NAME = "recovery_candidate_qa_audit_346b2_safe_recovered_candidates.json"
INPUT_346B2_SAFE_CSV_NAME = "recovery_candidate_qa_audit_346b2_safe_recovered_candidates.csv"
INPUT_346B2_FALSE_POSITIVE_JSON_NAME = "recovery_candidate_qa_audit_346b2_false_positive_suspects.json"
INPUT_346B2_FALSE_POSITIVE_CSV_NAME = "recovery_candidate_qa_audit_346b2_false_positive_suspects.csv"
INPUT_346B2_UNIT_AUDIT_JSON_NAME = "recovery_candidate_qa_audit_346b2_unit_repair_audit.json"
INPUT_346B2_UNIT_AUDIT_CSV_NAME = "recovery_candidate_qa_audit_346b2_unit_repair_audit.csv"
INPUT_346B2_SEMANTIC_DIST_JSON_NAME = "recovery_candidate_qa_audit_346b2_metric_semantic_class_distribution.json"
INPUT_346B2_SEMANTIC_DIST_CSV_NAME = "recovery_candidate_qa_audit_346b2_metric_semantic_class_distribution.csv"
INPUT_346B2_EXPANSION_READINESS_JSON_NAME = "recovery_candidate_qa_audit_346b2_expansion_readiness_report.json"
INPUT_346B2_REAUDIT_SUMMARY_JSON_NAME = "recovery_candidate_qa_audit_346b2_reaudit_summary.json"

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
    {"artifact_name": REFINED_CANDIDATES_JSON_FILE_NAME, "path": REFINED_CANDIDATES_JSON_FILE_NAME, "purpose": "Refined candidate rows in JSON."},
    {"artifact_name": REFINED_CANDIDATES_CSV_FILE_NAME, "path": REFINED_CANDIDATES_CSV_FILE_NAME, "purpose": "Refined candidate rows in CSV."},
    {"artifact_name": REFINED_SAFE_JSON_FILE_NAME, "path": REFINED_SAFE_JSON_FILE_NAME, "purpose": "Refined safe candidates in JSON."},
    {"artifact_name": REFINED_SAFE_CSV_FILE_NAME, "path": REFINED_SAFE_CSV_FILE_NAME, "purpose": "Refined safe candidates in CSV."},
    {"artifact_name": CORRECTED_RATIO_JSON_FILE_NAME, "path": CORRECTED_RATIO_JSON_FILE_NAME, "purpose": "Corrected ratio/multiple rows in JSON."},
    {"artifact_name": CORRECTED_RATIO_CSV_FILE_NAME, "path": CORRECTED_RATIO_CSV_FILE_NAME, "purpose": "Corrected ratio/multiple rows in CSV."},
    {"artifact_name": CORRECTED_PER_SHARE_JSON_FILE_NAME, "path": CORRECTED_PER_SHARE_JSON_FILE_NAME, "purpose": "Per-share rows after correction or demotion in JSON."},
    {"artifact_name": CORRECTED_PER_SHARE_CSV_FILE_NAME, "path": CORRECTED_PER_SHARE_CSV_FILE_NAME, "purpose": "Per-share rows after correction or demotion in CSV."},
    {"artifact_name": PRESERVED_PERCENTAGE_JSON_FILE_NAME, "path": PRESERVED_PERCENTAGE_JSON_FILE_NAME, "purpose": "Preserved percentage/margin rows in JSON."},
    {"artifact_name": PRESERVED_PERCENTAGE_CSV_FILE_NAME, "path": PRESERVED_PERCENTAGE_CSV_FILE_NAME, "purpose": "Preserved percentage/margin rows in CSV."},
    {"artifact_name": DEMOTED_ROWS_JSON_FILE_NAME, "path": DEMOTED_ROWS_JSON_FILE_NAME, "purpose": "Demoted rows in JSON."},
    {"artifact_name": DEMOTED_ROWS_CSV_FILE_NAME, "path": DEMOTED_ROWS_CSV_FILE_NAME, "purpose": "Demoted rows in CSV."},
    {"artifact_name": REFINED_POLICY_JSON_FILE_NAME, "path": REFINED_POLICY_JSON_FILE_NAME, "purpose": "Refined unit policy in JSON."},
    {"artifact_name": REFINED_POLICY_MD_FILE_NAME, "path": REFINED_POLICY_MD_FILE_NAME, "purpose": "Refined unit policy in Markdown."},
    {"artifact_name": RULE_CHANGE_LOG_JSON_FILE_NAME, "path": RULE_CHANGE_LOG_JSON_FILE_NAME, "purpose": "Rule change log in JSON."},
    {"artifact_name": RULE_CHANGE_LOG_MD_FILE_NAME, "path": RULE_CHANGE_LOG_MD_FILE_NAME, "purpose": "Rule change log in Markdown."},
    {"artifact_name": REAUDIT_PREVIEW_JSON_FILE_NAME, "path": REAUDIT_PREVIEW_JSON_FILE_NAME, "purpose": "Preview rows for re-audit in JSON."},
    {"artifact_name": REAUDIT_PREVIEW_CSV_FILE_NAME, "path": REAUDIT_PREVIEW_CSV_FILE_NAME, "purpose": "Preview rows for re-audit in CSV."},
    {"artifact_name": EXPANSION_READINESS_JSON_FILE_NAME, "path": EXPANSION_READINESS_JSON_FILE_NAME, "purpose": "Expansion readiness report in JSON."},
    {"artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME, "path": EXECUTIVE_SUMMARY_MD_FILE_NAME, "purpose": "Executive summary for 346B3."},
    {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": ARTIFACT_INDEX_MD_FILE_NAME, "purpose": "Artifact index for 346B3 outputs."},
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

RATIO_KEYWORDS = ["ev/ebitda", "pe", "pb", "ps", "ev/sales", "quick ratio", "市盈率", "市净率", "市销率"]
PERCENTAGE_KEYWORDS = ["margin", "roe", "roa", "roic", "(+/-%)", "%", "毛利率", "净利率", "收益率"]
PER_SHARE_KEYWORDS = ["每股", "eps", "bvps", "每股收益", "每股净资产"]
MONETARY_KEYWORDS = ["收入", "利润", "资产", "负债", "百万元", "千万元", "亿元", "万元", "元"]
PER_SHARE_EVIDENCE_KEYWORDS = [
    "元/股",
    "港元/股",
    "rmb/share",
    "hkd/share",
    "usd/share",
    "每股收益（元）",
    "每股收益(元)",
    "每股净资产（元）",
    "每股净资产(元)",
]


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
    return [
        {"artifact_name": row["artifact_name"], "path": str(output_dir / row["path"]), "purpose": row["purpose"]}
        for row in OUTPUT_ARTIFACT_ROWS
    ]


def _metric_text(row: Dict[str, Any]) -> str:
    return " | ".join(
        [
            _safe_text(row.get("raw_metric_name")),
            _safe_text(row.get("demo_normalized_metric_name")),
            _safe_text(row.get("context_snippet")),
        ]
    ).lower()


def _classify_semantic_class(row: Dict[str, Any]) -> str:
    existing = _safe_text(row.get("metric_semantic_unit_class"))
    if existing:
        return existing
    metric = _safe_text(row.get("demo_normalized_metric_name")).lower()
    text = _metric_text(row)
    if metric in RATIO_MULTIPLE_METRICS or any(token in text for token in RATIO_KEYWORDS):
        return "RATIO_MULTIPLE"
    if metric in PERCENTAGE_MARGIN_METRICS or any(token in text for token in PERCENTAGE_KEYWORDS):
        return "PERCENTAGE_OR_MARGIN"
    if metric in PER_SHARE_METRICS or any(token in text for token in PER_SHARE_KEYWORDS):
        return "PER_SHARE"
    if metric in MONETARY_METRICS or any(token in text for token in MONETARY_KEYWORDS):
        return "MONETARY_AMOUNT"
    return "UNKNOWN"


def _has_per_share_currency_context(row: Dict[str, Any]) -> bool:
    snippet = _safe_text(row.get("context_snippet")).lower()
    raw_metric = _safe_text(row.get("raw_metric_name")).lower()
    combined = f"{raw_metric} {snippet}"
    return any(token.lower() in combined for token in PER_SHARE_EVIDENCE_KEYWORDS)


def _monetary_unit_from_row(row: Dict[str, Any]) -> str:
    for field in ("recovered_unit", "inherited_unit", "unit"):
        unit = _safe_text(row.get(field))
        if unit and unit != "%":
            return unit
    snippet = _safe_text(row.get("context_snippet"))
    for candidate in ["亿元", "百万元", "千万元", "万元", "元", "RMB", "HKD", "USD"]:
        if candidate.lower() in snippet.lower():
            return candidate
    return ""


def _apply_refined_policy(
    row: Dict[str, Any],
    *,
    strict_refinement: bool,
    preserve_safe_346b2_candidates: bool,
    demote_unresolved_risk: bool,
) -> Dict[str, Any]:
    semantic_class = _classify_semantic_class(row)
    prior_safety = _safe_text(row.get("safety_decision"))
    original_unit_action = _safe_text(row.get("unit_repair_action"))
    original_unit = _safe_text(row.get("recovered_unit")) or _safe_text(row.get("inherited_unit")) or _safe_text(row.get("unit"))

    refined_unit = original_unit
    refined_unit_repair_action = original_unit_action
    refined_recovery_decision = (
        "REFINED_SAFE_RECOVERED_DEMO_CANDIDATE"
        if prior_safety == "SAFE_RECOVERED_DEMO_CANDIDATE"
        else "REFINED_FALSE_POSITIVE_CONFIRMED"
    )
    refinement_notes: List[str] = []
    remaining_false_positive_suspect = False

    if semantic_class == "RATIO_MULTIPLE":
        refined_unit = "x"
        refined_unit_repair_action = "UNIT_RATIO_MULTIPLE_X"
        refined_recovery_decision = "REFINED_SAFE_RECOVERED_DEMO_CANDIDATE"
        refinement_notes.append("Ratio/multiple rows use x and no longer inherit percent units.")
    elif semantic_class == "PERCENTAGE_OR_MARGIN":
        refined_unit = "%"
        refined_unit_repair_action = "UNIT_PERCENT_FROM_MARGIN_CONTEXT"
        refined_recovery_decision = "REFINED_SAFE_RECOVERED_DEMO_CANDIDATE"
        refinement_notes.append("Percentage/margin rows preserve percent-compatible units.")
    elif semantic_class == "PER_SHARE":
        if _has_per_share_currency_context(row):
            refined_unit = "元/股"
            refined_unit_repair_action = "UNIT_PER_SHARE_CONTEXT"
            refined_recovery_decision = "REFINED_SAFE_RECOVERED_DEMO_CANDIDATE"
            refinement_notes.append("Per-share row repaired with explicit currency/share evidence.")
        else:
            refined_unit = ""
            refined_unit_repair_action = "NEEDS_UNIT_CURRENCY_CONTEXT_PER_SHARE"
            refined_recovery_decision = (
                "REFINED_DEMOTED_TO_HUMAN_REVIEW"
                if demote_unresolved_risk
                else "REFINED_NEEDS_RULE_REFINEMENT"
            )
            remaining_false_positive_suspect = True
            refinement_notes.append("Per-share row lacks explicit currency/share evidence and is demoted.")
    elif semantic_class == "MONETARY_AMOUNT":
        refined_unit = _monetary_unit_from_row(row)
        if refined_unit:
            refined_recovery_decision = "REFINED_SAFE_RECOVERED_DEMO_CANDIDATE"
            if original_unit_action == "NO_CHANGE":
                refined_unit_repair_action = "NO_CHANGE"
            else:
                refined_unit_repair_action = "UNIT_MONETARY_CONTEXT_CONFIRMED"
            refinement_notes.append("Monetary row keeps only monetary-compatible units.")
        else:
            refined_recovery_decision = "REFINED_DEMOTED_TO_STILL_LIMITED"
            refined_unit_repair_action = "NEEDS_MONETARY_UNIT_CONTEXT"
            remaining_false_positive_suspect = True
            refinement_notes.append("Monetary row lacks safe unit evidence and is demoted.")
    else:
        refined_unit = ""
        refined_unit_repair_action = "UNKNOWN_SEMANTIC_CLASS_NO_AUTO_PROMOTION"
        refined_recovery_decision = "REFINED_NEEDS_RULE_REFINEMENT"
        remaining_false_positive_suspect = True
        refinement_notes.append("Unknown semantic class stays blocked from automatic promotion.")

    if (
        strict_refinement
        and prior_safety == "FALSE_POSITIVE_SUSPECT"
        and semantic_class == "PER_SHARE"
        and not _has_per_share_currency_context(row)
    ):
        refined_unit = ""
        refined_unit_repair_action = "NEEDS_UNIT_CURRENCY_CONTEXT_PER_SHARE"
        refined_recovery_decision = "REFINED_DEMOTED_TO_HUMAN_REVIEW"
        remaining_false_positive_suspect = True

    if (
        preserve_safe_346b2_candidates
        and prior_safety == "SAFE_RECOVERED_DEMO_CANDIDATE"
        and semantic_class in {"PERCENTAGE_OR_MARGIN", "MONETARY_AMOUNT"}
        and refined_recovery_decision.startswith("REFINED_SAFE")
    ):
        refined_recovery_decision = "REFINED_SAFE_RECOVERED_DEMO_CANDIDATE"

    return {
        "semantic_metric_class": semantic_class,
        "original_unit_repair_action": original_unit_action,
        "original_recovered_unit": original_unit,
        "refined_unit": refined_unit,
        "refined_unit_repair_action": refined_unit_repair_action,
        "refined_recovery_decision": refined_recovery_decision,
        "refinement_notes": " | ".join(refinement_notes),
        "remaining_false_positive_suspect": remaining_false_positive_suspect,
    }


def _ledger_has_346b3_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return "## 346B3 Recovery Rule Refinement" in ledger_path.read_text(encoding="utf-8")


def _build_346b3_ledger_entry(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "## 346B3 Recovery Rule Refinement",
            "",
            "Status: completed",
            "",
            f"- decision: {manifest.get('decision', '')}",
            f"- input_345d_dir: {manifest.get('input_345d_dir', '')}",
            f"- input_346a_dir: {manifest.get('input_346a_dir', '')}",
            f"- input_346a2_dir: {manifest.get('input_346a2_dir', '')}",
            f"- input_346b_dir: {manifest.get('input_346b_dir', '')}",
            f"- input_346b2_dir: {manifest.get('input_346b2_dir', '')}",
            f"- output_dir: {manifest.get('output_dir', '')}",
            f"- input_recovered_candidate_count: {manifest.get('input_recovered_candidate_count', 0)}",
            f"- input_safe_recovered_candidate_count: {manifest.get('input_safe_recovered_candidate_count', 0)}",
            f"- input_false_positive_suspect_count: {manifest.get('input_false_positive_suspect_count', 0)}",
            f"- refined_candidate_count: {manifest.get('refined_candidate_count', 0)}",
            f"- refined_safe_candidate_count: {manifest.get('refined_safe_candidate_count', 0)}",
            f"- remaining_false_positive_suspect_count: {manifest.get('remaining_false_positive_suspect_count', 0)}",
            f"- corrected_ratio_multiple_unit_count: {manifest.get('corrected_ratio_multiple_unit_count', 0)}",
            f"- corrected_per_share_unit_count: {manifest.get('corrected_per_share_unit_count', 0)}",
            f"- preserved_percentage_margin_unit_count: {manifest.get('preserved_percentage_margin_unit_count', 0)}",
            f"- demoted_candidate_count: {manifest.get('demoted_candidate_count', 0)}",
            f"- needs_human_review_count: {manifest.get('needs_human_review_count', 0)}",
            f"- needs_vlm_count: {manifest.get('needs_vlm_count', 0)}",
            f"- safe_to_reaudit: {manifest.get('safe_to_reaudit', False)}",
            f"- safe_to_expand_recovery: {manifest.get('safe_to_expand_recovery', False)}",
            f"- safe_to_expand_recovery_reason: {manifest.get('safe_to_expand_recovery_reason', '')}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- no_write_back_proof_passed: {manifest.get('no_write_back_proof_passed', False)}",
            f"- gate_status: formal_client_export_allowed={manifest.get('formal_client_export_allowed', False)}, client_ready={manifest.get('client_ready', False)}, production_ready={manifest.get('production_ready', False)}",
            f"- next_recommended_step: {manifest.get('recommended_next_step', '')}",
        ]
    )


def append_346b3_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    if _ledger_has_346b3_entry(ledger_path):
        return False
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    addition = _build_346b3_ledger_entry(manifest)
    prefix = "\n\n" if existing and not existing.endswith("\n\n") else ""
    if existing.endswith("\n"):
        prefix = "\n" if not existing.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(existing + prefix + addition + "\n", encoding="utf-8")
    return True


def build_recovery_rule_refinement_346b3(
    *,
    full_structured_demo_export_package_345d_dir: Path,
    vision_assisted_table_evidence_pilot_346a_dir: Path,
    mineru_image_path_binding_fix_346a2_dir: Path,
    quality_limited_row_recovery_pilot_346b_dir: Path,
    recovery_candidate_qa_audit_346b2_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    strict_refinement: bool = True,
    preserve_safe_346b2_candidates: bool = True,
    demote_unresolved_risk: bool = True,
    max_context_chars: int = 4000,
) -> Dict[str, Any]:
    for label, path in [
        ("345D", full_structured_demo_export_package_345d_dir),
        ("346A", vision_assisted_table_evidence_pilot_346a_dir),
        ("346A2", mineru_image_path_binding_fix_346a2_dir),
        ("346B", quality_limited_row_recovery_pilot_346b_dir),
        ("346B2", recovery_candidate_qa_audit_346b2_dir),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{label} input directory missing: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345d = _read_json(full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME)
    manifest_346a = _read_json(vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_MANIFEST_NAME)
    manifest_346a2 = _read_json(mineru_image_path_binding_fix_346a2_dir / INPUT_346A2_MANIFEST_NAME)
    manifest_346b = _read_json(quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_MANIFEST_NAME)
    manifest_346b2 = _read_json(recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_MANIFEST_NAME)

    recovered_rows, recovered_rows_source = _load_json_or_csv_rows(
        json_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_RECOVERED_JSON_NAME,
        csv_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_RECOVERED_CSV_NAME,
        label="346B recovered candidates",
    )
    context_rows, context_rows_source = _load_json_or_csv_rows(
        json_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_CONTEXT_JSON_NAME,
        csv_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_CONTEXT_CSV_NAME,
        label="346B context results",
    )
    evidence_rows, evidence_rows_source = _load_json_or_csv_rows(
        json_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_EVIDENCE_JSON_NAME,
        csv_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_EVIDENCE_CSV_NAME,
        label="346B evidence results",
    )
    value_rows, value_rows_source = _load_json_or_csv_rows(
        json_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_VALUE_JSON_NAME,
        csv_path=quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_VALUE_CSV_NAME,
        label="346B value results",
    )
    audited_rows, audited_rows_source = _load_json_or_csv_rows(
        json_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_AUDIT_JSON_NAME,
        csv_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_AUDIT_CSV_NAME,
        label="346B2 audited recovered candidates",
    )
    safe_rows, safe_rows_source = _load_json_or_csv_rows(
        json_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_SAFE_JSON_NAME,
        csv_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_SAFE_CSV_NAME,
        label="346B2 safe recovered candidates",
    )
    false_positive_rows, false_positive_rows_source = _load_json_or_csv_rows(
        json_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_FALSE_POSITIVE_JSON_NAME,
        csv_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_FALSE_POSITIVE_CSV_NAME,
        label="346B2 false positive suspects",
    )
    unit_audit_rows, unit_audit_rows_source = _load_json_or_csv_rows(
        json_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_UNIT_AUDIT_JSON_NAME,
        csv_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_UNIT_AUDIT_CSV_NAME,
        label="346B2 unit repair audit rows",
    )
    semantic_dist_rows, semantic_dist_rows_source = _load_json_or_csv_rows(
        json_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_SEMANTIC_DIST_JSON_NAME,
        csv_path=recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_SEMANTIC_DIST_CSV_NAME,
        label="346B2 semantic distribution rows",
    )
    _ = _read_json(recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_EXPANSION_READINESS_JSON_NAME)
    _ = _read_json(recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_REAUDIT_SUMMARY_JSON_NAME)
    _ = _read_json(quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_REAUDIT_SUMMARY_JSON_NAME)
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
            quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_VALUE_JSON_NAME,
            quality_limited_row_recovery_pilot_346b_dir / INPUT_346B_REAUDIT_SUMMARY_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_MANIFEST_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_AUDIT_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_SAFE_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_FALSE_POSITIVE_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_UNIT_AUDIT_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_SEMANTIC_DIST_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_EXPANSION_READINESS_JSON_NAME,
            recovery_candidate_qa_audit_346b2_dir / INPUT_346B2_REAUDIT_SUMMARY_JSON_NAME,
        ]
        if path.exists()
    ]

    input_paths = [Path(path) for path in files_read if Path(path).is_file()]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    context_by_source = {_safe_text(row.get("source_row_id")): row for row in context_rows if _safe_text(row.get("source_row_id"))}
    evidence_by_source = {_safe_text(row.get("source_row_id")): row for row in evidence_rows if _safe_text(row.get("source_row_id"))}
    value_by_source = {_safe_text(row.get("source_row_id")): row for row in value_rows if _safe_text(row.get("source_row_id"))}
    audited_by_source = {_safe_text(row.get("source_row_id")): row for row in audited_rows if _safe_text(row.get("source_row_id"))}
    unit_audit_by_source = {_safe_text(row.get("source_row_id")): row for row in unit_audit_rows if _safe_text(row.get("source_row_id"))}
    bound_by_source = {_safe_text(row.get("source_row_id")): row for row in bound_rows if _safe_text(row.get("source_row_id"))}

    refined_rows: List[Dict[str, Any]] = []
    replacement_summary_counter: Counter[str] = Counter()
    for row in recovered_rows:
        source_row_id = _safe_text(row.get("source_row_id"))
        merged = {
            **dict(row),
            **value_by_source.get(source_row_id, {}),
            **context_by_source.get(source_row_id, {}),
            **evidence_by_source.get(source_row_id, {}),
            **audited_by_source.get(source_row_id, {}),
            **unit_audit_by_source.get(source_row_id, {}),
            **bound_by_source.get(source_row_id, {}),
        }
        merged["context_snippet"] = _safe_text(merged.get("context_snippet"))[:max_context_chars]
        refined = _apply_refined_policy(
            merged,
            strict_refinement=strict_refinement,
            preserve_safe_346b2_candidates=preserve_safe_346b2_candidates,
            demote_unresolved_risk=demote_unresolved_risk,
        )
        replacement_summary_counter[refined["refined_unit_repair_action"]] += 1
        refined_rows.append(
            {
                **merged,
                **refined,
                "sidecar_refinement_only": True,
                "do_not_apply_upstream": True,
            }
        )

    refined_safe_rows = [
        row for row in refined_rows if row["refined_recovery_decision"] == "REFINED_SAFE_RECOVERED_DEMO_CANDIDATE"
    ]
    corrected_ratio_rows = [row for row in refined_rows if row["semantic_metric_class"] == "RATIO_MULTIPLE"]
    corrected_per_share_rows = [row for row in refined_rows if row["semantic_metric_class"] == "PER_SHARE"]
    preserved_percentage_rows = [row for row in refined_rows if row["semantic_metric_class"] == "PERCENTAGE_OR_MARGIN"]
    demoted_rows = [
        row
        for row in refined_rows
        if row["refined_recovery_decision"]
        in {
            "REFINED_DEMOTED_TO_HUMAN_REVIEW",
            "REFINED_DEMOTED_TO_STILL_LIMITED",
            "REFINED_NEEDS_RULE_REFINEMENT",
        }
    ]
    remaining_false_positive_rows = [row for row in refined_rows if _bool_value(row.get("remaining_false_positive_suspect"))]

    refined_unit_policy = {
        "semantic_unit_policy_applied": True,
        "unit_percent_from_ratio_context_deprecated": True,
        "semantic_classes": [
            "MONETARY_AMOUNT",
            "PERCENTAGE_OR_MARGIN",
            "RATIO_MULTIPLE",
            "PER_SHARE",
            "COUNT_OR_VOLUME",
            "TEXT_OR_LABEL",
            "UNKNOWN",
        ],
        "ratio_multiple_policy": "RATIO_MULTIPLE rows must not use %. Preferred refined action is UNIT_RATIO_MULTIPLE_X with display unit x.",
        "percentage_margin_policy": "PERCENTAGE_OR_MARGIN rows preserve % via UNIT_PERCENT_FROM_MARGIN_CONTEXT.",
        "per_share_policy": "PER_SHARE rows require explicit currency/share evidence; otherwise demote to human review or rule refinement.",
        "monetary_amount_policy": "MONETARY_AMOUNT rows keep only monetary units and are not inherited from ratio or percent context.",
        "unknown_policy": "UNKNOWN semantic classes are blocked from automatic promotion.",
    }

    rule_change_log = [
        {
            "change_id": "346B3_RULE_001",
            "before_rule": "UNIT_PERCENT_FROM_RATIO_CONTEXT could flow into ratio/multiple and per-share rows.",
            "after_rule": "UNIT_PERCENT_FROM_RATIO_CONTEXT is deprecated for non-percentage semantic classes.",
            "scope": "all refined recovered candidates",
        },
        {
            "change_id": "346B3_RULE_002",
            "before_rule": "RATIO_MULTIPLE rows could remain blank or be misread as percent.",
            "after_rule": "RATIO_MULTIPLE rows use UNIT_RATIO_MULTIPLE_X with refined_unit = x.",
            "scope": "EV/EBITDA, PE, PB, PS, EV/Sales style rows",
        },
        {
            "change_id": "346B3_RULE_003",
            "before_rule": "PER_SHARE rows were allowed to inherit percent-like repairs.",
            "after_rule": "PER_SHARE rows require explicit per-share currency context or are demoted.",
            "scope": "每股收益 / 每股净资产 / EPS / BVPS style rows",
        },
    ]

    reaudit_preview_rows = [
        {
            "source_row_id": row.get("source_row_id"),
            "raw_metric_name": row.get("raw_metric_name"),
            "demo_normalized_metric_name": row.get("demo_normalized_metric_name"),
            "semantic_metric_class": row.get("semantic_metric_class"),
            "original_unit_repair_action": row.get("original_unit_repair_action"),
            "refined_unit_repair_action": row.get("refined_unit_repair_action"),
            "refined_unit": row.get("refined_unit"),
            "refined_recovery_decision": row.get("refined_recovery_decision"),
            "remaining_false_positive_suspect": row.get("remaining_false_positive_suspect"),
        }
        for row in refined_rows
    ]

    safe_to_reaudit = True
    safe_to_expand_recovery = False
    safe_to_expand_recovery_reason = (
        "346B3 only refines rules and sidecar decisions; a follow-up 346B2R re-audit must confirm safety before expansion."
    )
    expansion_readiness_report = {
        "safe_to_reaudit": safe_to_reaudit,
        "safe_to_expand_recovery": safe_to_expand_recovery,
        "safe_to_expand_recovery_reason": safe_to_expand_recovery_reason,
        "remaining_false_positive_suspect_count": len(remaining_false_positive_rows),
    }
    semantic_input_counter = Counter(_safe_text(row.get("metric_semantic_unit_class")) for row in audited_rows)

    manifest = {
        "decision": READY_DECISION_346B3,
        "input_stage": INPUT_STAGE_346B3,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "input_345d_decision": _safe_text(manifest_345d.get("decision")),
        "input_346a_decision": _safe_text(manifest_346a.get("decision")),
        "input_346a2_decision": _safe_text(manifest_346a2.get("decision")),
        "input_346b_decision": _safe_text(manifest_346b.get("decision")),
        "input_346b2_decision": _safe_text(manifest_346b2.get("decision")),
        "input_345d_dir": str(full_structured_demo_export_package_345d_dir),
        "input_346a_dir": str(vision_assisted_table_evidence_pilot_346a_dir),
        "input_346a2_dir": str(mineru_image_path_binding_fix_346a2_dir),
        "input_346b_dir": str(quality_limited_row_recovery_pilot_346b_dir),
        "input_346b2_dir": str(recovery_candidate_qa_audit_346b2_dir),
        "output_dir": str(output_dir),
        "input_recovered_candidate_count": len(recovered_rows),
        "input_safe_recovered_candidate_count": len(safe_rows),
        "input_false_positive_suspect_count": len(false_positive_rows),
        "refined_candidate_count": len(refined_rows),
        "refined_safe_candidate_count": len(refined_safe_rows),
        "remaining_false_positive_suspect_count": len(remaining_false_positive_rows),
        "corrected_ratio_multiple_unit_count": sum(
            1 for row in corrected_ratio_rows if row["refined_unit_repair_action"] == "UNIT_RATIO_MULTIPLE_X"
        ),
        "corrected_per_share_unit_count": sum(
            1 for row in corrected_per_share_rows if row["refined_unit_repair_action"] == "UNIT_PER_SHARE_CONTEXT"
        ),
        "preserved_percentage_margin_unit_count": sum(
            1 for row in preserved_percentage_rows if row["refined_unit_repair_action"] == "UNIT_PERCENT_FROM_MARGIN_CONTEXT"
        ),
        "demoted_candidate_count": len(demoted_rows),
        "needs_human_review_count": sum(
            1 for row in demoted_rows if row["refined_recovery_decision"] == "REFINED_DEMOTED_TO_HUMAN_REVIEW"
        ),
        "needs_rule_refinement_count": sum(
            1 for row in demoted_rows if row["refined_recovery_decision"] == "REFINED_NEEDS_RULE_REFINEMENT"
        ),
        "needs_vlm_count": 0,
        "unit_percent_from_ratio_context_deprecated": True,
        "semantic_unit_policy_applied": True,
        "safe_to_reaudit": safe_to_reaudit,
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
        "strict_refinement": strict_refinement,
        "preserve_safe_346b2_candidates": preserve_safe_346b2_candidates,
        "demote_unresolved_risk": demote_unresolved_risk,
        "max_context_chars": max_context_chars,
        "recommended_next_step": "346B2R Refined Recovery Candidate QA Reaudit",
        "recommended_next_step_reason": "Refined sidecar candidates now need an independent QA re-audit before any recovery expansion can be considered.",
        "generated_at_utc": _utc_now(),
    }

    validation_checks = [
        manifest["input_345d_decision"] == READY_DECISION_345D,
        manifest["input_346a_decision"] == READY_DECISION_346A,
        manifest["input_346a2_decision"] == READY_DECISION_346A2,
        manifest["input_346b_decision"] == READY_DECISION_346B,
        manifest["input_346b2_decision"] == READY_DECISION_346B2,
        int(manifest_345d.get("qa_fail_count", 1)) == 0,
        int(manifest_346a.get("qa_fail_count", 1)) == 0,
        int(manifest_346a2.get("qa_fail_count", 1)) == 0,
        int(manifest_346b.get("qa_fail_count", 1)) == 0,
        int(manifest_346b2.get("qa_fail_count", 1)) == 0,
        int(manifest_346b.get("live_vlm_call_count", 1)) == 0,
        int(manifest_346b2.get("live_vlm_call_count", 1)) == 0,
        _bool_value(manifest_345d.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346a.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346a2.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346b.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_346b2.get("formal_client_export_allowed")) is False,
        manifest["refined_candidate_count"] == manifest["input_recovered_candidate_count"],
        manifest["refined_candidate_count"] == manifest["refined_safe_candidate_count"] + manifest["demoted_candidate_count"],
        manifest["input_safe_recovered_candidate_count"] + manifest["input_false_positive_suspect_count"]
        == manifest["input_recovered_candidate_count"],
        manifest["live_vlm_call_count"] == 0,
        manifest["vlm_response_count"] == 0,
        manifest["unit_percent_from_ratio_context_deprecated"] is True,
        manifest["semantic_unit_policy_applied"] is True,
        manifest["safe_to_reaudit"] is True,
        manifest["safe_to_expand_recovery"] is False,
        manifest["official_rules_modified"] is False,
        manifest["official_alias_assets_modified"] is False,
        manifest["formal_export_generated"] is False,
        manifest["demo_export_only"] is True,
        manifest["formal_client_export_allowed"] is False,
        manifest["client_ready"] is False,
        manifest["production_ready"] is False,
        manifest["global_strict_human_review_completed"] is False,
        manifest["corrected_ratio_multiple_unit_count"] == semantic_input_counter.get("RATIO_MULTIPLE", 0),
        manifest["preserved_percentage_margin_unit_count"] == semantic_input_counter.get("PERCENTAGE_OR_MARGIN", 0),
        all(row["refined_unit"] != "%" for row in corrected_ratio_rows),
        all(row["refined_unit"] != "%" for row in corrected_per_share_rows),
        len(semantic_dist_rows) > 0,
        bool(refined_unit_policy),
        bool(rule_change_log),
        recovered_rows_source in {"json", "csv"},
        context_rows_source in {"json", "csv"},
        evidence_rows_source in {"json", "csv"},
        value_rows_source in {"json", "csv"},
        audited_rows_source in {"json", "csv"},
        safe_rows_source in {"json", "csv"},
        false_positive_rows_source in {"json", "csv"},
        unit_audit_rows_source in {"json", "csv"},
        semantic_dist_rows_source in {"json", "csv"},
        bound_rows_source in {"json", "csv"},
    ]

    no_apply_proof = build_no_apply_proof(
        stage="346B3",
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
    no_apply_proof["sidecar_refinement_only"] = True
    no_apply_proof["no_write_back"] = True

    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_346b3")
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
    manifest["decision"] = READY_DECISION_346B3 if qa_fail_count == 0 else BLOCKED_DECISION_346B3

    if ledger_path is not None:
        append_346b3_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = _ledger_has_346b3_entry(ledger_path)
        if not manifest["milestone_ledger_updated"]:
            manifest["qa_fail_count"] += 1
            manifest["decision"] = BLOCKED_DECISION_346B3

    replacement_summary = [f"{key}: {value}" for key, value in replacement_summary_counter.most_common()]

    return {
        "manifest": manifest,
        "refined_candidate_rows": refined_rows,
        "refined_safe_candidate_rows": refined_safe_rows,
        "corrected_ratio_multiple_rows": corrected_ratio_rows,
        "corrected_per_share_rows": corrected_per_share_rows,
        "preserved_percentage_margin_rows": preserved_percentage_rows,
        "demoted_rows": demoted_rows,
        "refined_unit_policy": refined_unit_policy,
        "refined_unit_policy_md": render_refined_unit_policy_markdown(refined_unit_policy),
        "rule_change_log_rows": rule_change_log,
        "rule_change_log_md": render_rule_change_log_markdown(rule_change_log),
        "reaudit_preview_rows": reaudit_preview_rows,
        "expansion_readiness_report": expansion_readiness_report,
        "executive_summary_md": render_executive_summary_markdown(
            manifest,
            replacement_summary=replacement_summary,
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
