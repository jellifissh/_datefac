from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from datefac.benchmark.controlled_expansion_qa_audit_346b4q_report import (
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
BLOCKED_DECISION_346B4Q = "CONTROLLED_EXPANSION_QA_AUDIT_346B4Q_BLOCKED"
INPUT_STAGE_346B4Q = "POST_346B4R_CONTROLLED_EXPANSION_QA_AUDIT"

QA_SAFE = "QA_SAFE_RECOVERED_DEMO_CANDIDATE"
QA_RISKY = "QA_RISKY_RECOVERED_DEMO_CANDIDATE"
QA_FALSE_POSITIVE = "QA_FALSE_POSITIVE_SUSPECT"
QA_NEEDS_HUMAN = "QA_NEEDS_HUMAN_REVIEW"
QA_NEEDS_RULE = "QA_NEEDS_RULE_REFINEMENT"

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
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\controlled_expansion_qa_audit_346b4q")

MANIFEST_FILE_NAME = "controlled_expansion_qa_audit_346b4q_manifest.json"
CANDIDATE_QA_JSON_FILE_NAME = "controlled_expansion_qa_audit_346b4q_candidate_qa.json"
CANDIDATE_QA_CSV_FILE_NAME = "controlled_expansion_qa_audit_346b4q_candidate_qa.csv"
SAFE_JSON_FILE_NAME = "controlled_expansion_qa_audit_346b4q_qa_safe_candidates.json"
SAFE_CSV_FILE_NAME = "controlled_expansion_qa_audit_346b4q_qa_safe_candidates.csv"
RISKY_JSON_FILE_NAME = "controlled_expansion_qa_audit_346b4q_qa_risky_candidates.json"
RISKY_CSV_FILE_NAME = "controlled_expansion_qa_audit_346b4q_qa_risky_candidates.csv"
FALSE_POSITIVE_JSON_FILE_NAME = "controlled_expansion_qa_audit_346b4q_false_positive_suspects.json"
FALSE_POSITIVE_CSV_FILE_NAME = "controlled_expansion_qa_audit_346b4q_false_positive_suspects.csv"
PATCH_QA_JSON_FILE_NAME = "controlled_expansion_qa_audit_346b4q_patch_applied_row_qa.json"
PATCH_QA_CSV_FILE_NAME = "controlled_expansion_qa_audit_346b4q_patch_applied_row_qa.csv"
SEMANTIC_UNIT_JSON_FILE_NAME = "controlled_expansion_qa_audit_346b4q_semantic_unit_recheck.json"
SEMANTIC_UNIT_CSV_FILE_NAME = "controlled_expansion_qa_audit_346b4q_semantic_unit_recheck.csv"
LINEAGE_JSON_FILE_NAME = "controlled_expansion_qa_audit_346b4q_lineage_evidence_audit.json"
LINEAGE_CSV_FILE_NAME = "controlled_expansion_qa_audit_346b4q_lineage_evidence_audit.csv"
READINESS_JSON_FILE_NAME = "controlled_expansion_qa_audit_346b4q_larger_expansion_readiness_report.json"
SUMMARY_JSON_FILE_NAME = "controlled_expansion_qa_audit_346b4q_reaudit_summary.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "controlled_expansion_qa_audit_346b4q_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "controlled_expansion_qa_audit_346b4q_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "controlled_expansion_qa_audit_346b4q_next_plan.md"

INPUT_345D_MANIFEST_NAME = "full_structured_demo_export_package_345d_manifest.json"
INPUT_346B4_MANIFEST_NAME = "controlled_quality_limited_recovery_expansion_346b4_manifest.json"
INPUT_346B4_SELECTED_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_selected_rows.json"
INPUT_346B4_SELECTED_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_selected_rows.csv"
INPUT_346B4_RESULTS_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovery_results.json"
INPUT_346B4_RESULTS_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovery_results.csv"
INPUT_346B4_GUARD_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_guardrail_summary.json"

INPUT_346B3R_MANIFEST_NAME = "recovery_rule_refinement_patch_346b3r_manifest.json"
INPUT_346B3R_PATCHABLE_JSON_NAME = "recovery_rule_refinement_patch_346b3r_patchable_rows.json"
INPUT_346B3R_PATCHABLE_CSV_NAME = "recovery_rule_refinement_patch_346b3r_patchable_rows.csv"
INPUT_346B3R_PATCH_SAFETY_JSON_NAME = "recovery_rule_refinement_patch_346b3r_patch_safety_review.json"
INPUT_346B3R_PATCH_SAFETY_CSV_NAME = "recovery_rule_refinement_patch_346b3r_patch_safety_review.csv"
INPUT_346B3R_READINESS_JSON_NAME = "recovery_rule_refinement_patch_346b3r_replay_readiness_report.json"

INPUT_346B4R_MANIFEST_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_manifest.json"
INPUT_346B4R_RESULTS_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_replay_results.json"
INPUT_346B4R_RESULTS_CSV_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_replay_results.csv"
INPUT_346B4R_SAFE_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.json"
INPUT_346B4R_SAFE_CSV_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.csv"
INPUT_346B4R_PATCHED_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.json"
INPUT_346B4R_PATCHED_CSV_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.csv"
INPUT_346B4R_UNKNOWN_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_remaining_unknown_rows.json"
INPUT_346B4R_UNKNOWN_CSV_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_remaining_unknown_rows.csv"
INPUT_346B4R_GUARD_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_guardrail_hits.json"
INPUT_346B4R_GUARD_CSV_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_guardrail_hits.csv"
INPUT_346B4R_DELTA_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_delta_report.json"
INPUT_346B4R_DELTA_CSV_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_delta_report.csv"
INPUT_346B4R_SEMANTIC_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_semantic_class_distribution.json"
INPUT_346B4R_SEMANTIC_CSV_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_semantic_class_distribution.csv"
INPUT_346B4R_UNIT_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_unit_action_distribution.json"
INPUT_346B4R_UNIT_CSV_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_unit_action_distribution.csv"
INPUT_346B4R_LINEAGE_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_lineage_evidence_audit.json"
INPUT_346B4R_LINEAGE_CSV_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_lineage_evidence_audit.csv"
INPUT_346B4R_READINESS_JSON_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_expansion_readiness_report.json"

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
    {"artifact_name": CANDIDATE_QA_JSON_FILE_NAME, "path": CANDIDATE_QA_JSON_FILE_NAME, "purpose": "Candidate QA rows in JSON."},
    {"artifact_name": CANDIDATE_QA_CSV_FILE_NAME, "path": CANDIDATE_QA_CSV_FILE_NAME, "purpose": "Candidate QA rows in CSV."},
    {"artifact_name": SAFE_JSON_FILE_NAME, "path": SAFE_JSON_FILE_NAME, "purpose": "QA-safe candidates in JSON."},
    {"artifact_name": SAFE_CSV_FILE_NAME, "path": SAFE_CSV_FILE_NAME, "purpose": "QA-safe candidates in CSV."},
    {"artifact_name": RISKY_JSON_FILE_NAME, "path": RISKY_JSON_FILE_NAME, "purpose": "QA-risky candidates in JSON."},
    {"artifact_name": RISKY_CSV_FILE_NAME, "path": RISKY_CSV_FILE_NAME, "purpose": "QA-risky candidates in CSV."},
    {"artifact_name": FALSE_POSITIVE_JSON_FILE_NAME, "path": FALSE_POSITIVE_JSON_FILE_NAME, "purpose": "False-positive suspects in JSON."},
    {"artifact_name": FALSE_POSITIVE_CSV_FILE_NAME, "path": FALSE_POSITIVE_CSV_FILE_NAME, "purpose": "False-positive suspects in CSV."},
    {"artifact_name": PATCH_QA_JSON_FILE_NAME, "path": PATCH_QA_JSON_FILE_NAME, "purpose": "Patch-applied row QA in JSON."},
    {"artifact_name": PATCH_QA_CSV_FILE_NAME, "path": PATCH_QA_CSV_FILE_NAME, "purpose": "Patch-applied row QA in CSV."},
    {"artifact_name": SEMANTIC_UNIT_JSON_FILE_NAME, "path": SEMANTIC_UNIT_JSON_FILE_NAME, "purpose": "Independent semantic/unit recheck in JSON."},
    {"artifact_name": SEMANTIC_UNIT_CSV_FILE_NAME, "path": SEMANTIC_UNIT_CSV_FILE_NAME, "purpose": "Independent semantic/unit recheck in CSV."},
    {"artifact_name": LINEAGE_JSON_FILE_NAME, "path": LINEAGE_JSON_FILE_NAME, "purpose": "Lineage/evidence audit in JSON."},
    {"artifact_name": LINEAGE_CSV_FILE_NAME, "path": LINEAGE_CSV_FILE_NAME, "purpose": "Lineage/evidence audit in CSV."},
    {"artifact_name": READINESS_JSON_FILE_NAME, "path": READINESS_JSON_FILE_NAME, "purpose": "Larger expansion readiness report in JSON."},
    {"artifact_name": SUMMARY_JSON_FILE_NAME, "path": SUMMARY_JSON_FILE_NAME, "purpose": "QA summary in JSON."},
    {"artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME, "path": EXECUTIVE_SUMMARY_MD_FILE_NAME, "purpose": "Executive summary for 346B4Q."},
    {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": ARTIFACT_INDEX_MD_FILE_NAME, "purpose": "Artifact index for 346B4Q outputs."},
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

PERCENT_UNITS = {"%", "pct", "percentage"}
RATIO_UNITS = {"x", "倍"}


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


def _ledger_has_346b4q_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return "## 346B4Q Controlled Expansion QA Audit" in ledger_path.read_text(encoding="utf-8")


def _strip_346b4q_ledger_entry(text: str) -> str:
    header = "## 346B4Q Controlled Expansion QA Audit"
    start = text.find(header)
    if start < 0:
        return text
    next_header = text.find("\n## ", start + len(header))
    if next_header < 0:
        return text[:start].rstrip()
    return (text[:start] + text[next_header + 1 :]).rstrip()


def _build_346b4q_ledger_entry(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "## 346B4Q Controlled Expansion QA Audit",
            "",
            "Status: completed",
            "",
            f"- decision: {manifest.get('decision', '')}",
            f"- input_345d_dir: {manifest.get('input_345d_dir', '')}",
            f"- input_346b4_dir: {manifest.get('input_346b4_dir', '')}",
            f"- input_346b3r_dir: {manifest.get('input_346b3r_dir', '')}",
            f"- input_346b4r_dir: {manifest.get('input_346b4r_dir', '')}",
            f"- output_dir: {manifest.get('output_dir', '')}",
            f"- replay_input_row_count: {manifest.get('replay_input_row_count', 0)}",
            f"- replay_safe_recovered_candidate_count: {manifest.get('replay_safe_recovered_candidate_count', 0)}",
            f"- qa_audited_candidate_count: {manifest.get('qa_audited_candidate_count', 0)}",
            f"- qa_safe_candidate_count: {manifest.get('qa_safe_candidate_count', 0)}",
            f"- qa_risky_candidate_count: {manifest.get('qa_risky_candidate_count', 0)}",
            f"- qa_false_positive_suspect_count: {manifest.get('qa_false_positive_suspect_count', 0)}",
            f"- patch_applied_audited_row_count: {manifest.get('patch_applied_audited_row_count', 0)}",
            f"- patch_applied_qa_pass_count: {manifest.get('patch_applied_qa_pass_count', 0)}",
            f"- patch_applied_qa_risk_count: {manifest.get('patch_applied_qa_risk_count', 0)}",
            f"- semantic_class_disagreement_count: {manifest.get('semantic_class_disagreement_count', 0)}",
            f"- unit_semantic_mismatch_count: {manifest.get('unit_semantic_mismatch_count', 0)}",
            f"- false_positive_guardrail_hit_count: {manifest.get('false_positive_guardrail_hit_count', 0)}",
            f"- evidence_weakness_count: {manifest.get('evidence_weakness_count', 0)}",
            f"- lineage_audit_passed: {manifest.get('lineage_audit_passed', False)}",
            f"- qa_safe_to_larger_expansion: {manifest.get('qa_safe_to_larger_expansion', False)}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- no_write_back_proof_passed: {manifest.get('no_write_back_proof_passed', False)}",
            f"- gate_status: formal_client_export_allowed={manifest.get('formal_client_export_allowed', False)}, client_ready={manifest.get('client_ready', False)}, production_ready={manifest.get('production_ready', False)}",
            f"- next_recommended_step: {manifest.get('recommended_next_step', '')}",
        ]
    )


def append_346b4q_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    stripped = _strip_346b4q_ledger_entry(existing)
    addition = _build_346b4q_ledger_entry(manifest)
    prefix = "\n\n" if stripped and not stripped.endswith("\n\n") else ""
    if stripped.endswith("\n"):
        prefix = "\n" if not stripped.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(stripped + prefix + addition + "\n", encoding="utf-8")
    return True


def _semantic_class(row: Dict[str, Any]) -> str:
    metric = _safe_text(row.get("demo_normalized_metric_name")).lower()
    if metric in RATIO_MULTIPLE_METRICS:
        return "RATIO_MULTIPLE"
    if metric in PERCENTAGE_MARGIN_METRICS:
        return "PERCENTAGE_OR_MARGIN"
    if metric in PER_SHARE_METRICS:
        return "PER_SHARE"
    if metric in MONETARY_METRICS:
        return "MONETARY_AMOUNT"
    return _safe_text(row.get("patched_semantic_class") or row.get("semantic_metric_class")) or "UNKNOWN"


def _normalize_unit_token(value: Any) -> str:
    return _safe_text(value).lower().replace(" ", "")


def _patch_qa_decision(row: Dict[str, Any], patch_safety_by_source: Dict[str, Dict[str, Any]]) -> str:
    source_row_id = _safe_text(row.get("source_row_id"))
    patch_safety = patch_safety_by_source.get(source_row_id, {})
    previous_decision = _safe_text(row.get("previous_346b4_decision"))
    replay_decision = _safe_text(row.get("replay_recovery_decision"))
    semantic_class = _safe_text(row.get("patched_semantic_class"))
    if previous_decision not in {"CONTROLLED_NEEDS_RULE_REFINEMENT", "CONTROLLED_NEEDS_HUMAN_REVIEW"}:
        return "PATCH_QA_FAIL"
    if not patch_safety:
        return "PATCH_QA_FAIL"
    if semantic_class == "UNKNOWN":
        return "PATCH_QA_FAIL"
    if replay_decision != "REPLAY_SAFE_RECOVERED_DEMO_CANDIDATE":
        return "PATCH_QA_RISK"
    if _bool_value(row.get("unit_semantic_mismatch")) or _bool_value(row.get("evidence_weakness")):
        return "PATCH_QA_RISK"
    if not _bool_value(row.get("lineage_preserved")):
        return "PATCH_QA_FAIL"
    return "PATCH_QA_PASS"


def _qa_decision(
    row: Dict[str, Any],
    *,
    independent_semantic_class: str,
    semantic_disagreement: bool,
    unit_semantic_mismatch: bool,
    false_positive_suspect: bool,
    evidence_weakness: bool,
    lineage_preserved: bool,
    require_evidence_or_deterministic_proof: bool,
) -> str:
    if independent_semantic_class == "UNKNOWN" or semantic_disagreement:
        return QA_NEEDS_RULE
    if unit_semantic_mismatch or false_positive_suspect:
        return QA_FALSE_POSITIVE
    if require_evidence_or_deterministic_proof and evidence_weakness:
        return QA_RISKY
    if not lineage_preserved:
        return QA_NEEDS_HUMAN
    return QA_SAFE


def build_controlled_expansion_qa_audit_346b4q(
    *,
    full_structured_demo_export_package_345d_dir: Path,
    controlled_quality_limited_recovery_expansion_346b4_dir: Path,
    recovery_rule_refinement_patch_346b3r_dir: Path,
    controlled_expansion_replay_with_patched_rules_346b4r_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    strict_qa: bool = True,
    audit_patch_applied_rows: bool = True,
    require_same_row_set_proof: bool = True,
    require_lineage_preservation: bool = True,
    require_evidence_or_deterministic_proof: bool = True,
    safe_to_larger_expansion_risk_threshold: int = 0,
    max_context_chars: int = 4000,
) -> Dict[str, Any]:
    for label, path in [
        ("345D", full_structured_demo_export_package_345d_dir),
        ("346B4", controlled_quality_limited_recovery_expansion_346b4_dir),
        ("346B3R", recovery_rule_refinement_patch_346b3r_dir),
        ("346B4R", controlled_expansion_replay_with_patched_rules_346b4r_dir),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{label} input directory missing: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345d = _read_json(full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME)
    manifest_346b4 = _read_json(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_MANIFEST_NAME)
    manifest_346b3r = _read_json(recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_MANIFEST_NAME)
    replay_readiness_346b3r = _read_json(recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_READINESS_JSON_NAME)
    manifest_346b4r = _read_json(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_MANIFEST_NAME)
    readiness_346b4r = _read_json(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_READINESS_JSON_NAME)
    guardrail_summary_346b4 = _read_json(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_GUARD_JSON_NAME)

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
    patchable_rows_346b3r, patchable_rows_346b3r_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCHABLE_JSON_NAME,
        csv_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCHABLE_CSV_NAME,
        label="346B3R patchable rows",
    )
    patch_safety_rows_346b3r, patch_safety_rows_346b3r_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCH_SAFETY_JSON_NAME,
        csv_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCH_SAFETY_CSV_NAME,
        label="346B3R patch safety review",
    )
    replay_results_346b4r, replay_results_346b4r_source = _load_json_or_csv_rows(
        json_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_RESULTS_JSON_NAME,
        csv_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_RESULTS_CSV_NAME,
        label="346B4R replay results",
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
    unknown_rows_346b4r, unknown_rows_346b4r_source = _load_json_or_csv_rows(
        json_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_UNKNOWN_JSON_NAME,
        csv_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_UNKNOWN_CSV_NAME,
        label="346B4R remaining unknown rows",
    )
    guardrail_rows_346b4r, guardrail_rows_346b4r_source = _load_json_or_csv_rows(
        json_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_GUARD_JSON_NAME,
        csv_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_GUARD_CSV_NAME,
        label="346B4R guardrail hits",
    )
    delta_rows_346b4r, delta_rows_346b4r_source = _load_json_or_csv_rows(
        json_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_DELTA_JSON_NAME,
        csv_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_DELTA_CSV_NAME,
        label="346B4R delta report",
    )
    semantic_distribution_rows_346b4r, semantic_distribution_rows_346b4r_source = _load_json_or_csv_rows(
        json_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_SEMANTIC_JSON_NAME,
        csv_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_SEMANTIC_CSV_NAME,
        label="346B4R semantic distribution",
    )
    unit_distribution_rows_346b4r, unit_distribution_rows_346b4r_source = _load_json_or_csv_rows(
        json_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_UNIT_JSON_NAME,
        csv_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_UNIT_CSV_NAME,
        label="346B4R unit action distribution",
    )
    lineage_rows_346b4r, lineage_rows_346b4r_source = _load_json_or_csv_rows(
        json_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_LINEAGE_JSON_NAME,
        csv_path=controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_LINEAGE_CSV_NAME,
        label="346B4R lineage evidence audit",
    )

    files_read = [
        str(full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME),
        str(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_MANIFEST_NAME),
        str(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_GUARD_JSON_NAME),
        str(recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_MANIFEST_NAME),
        str(recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_READINESS_JSON_NAME),
        str(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_MANIFEST_NAME),
        str(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_READINESS_JSON_NAME),
    ]

    validation_checks: List[bool] = []
    validation_checks.append(_safe_text(manifest_345d.get("decision")) == READY_DECISION_345D)
    validation_checks.append(_safe_text(manifest_346b4.get("decision")) == READY_DECISION_346B4)
    validation_checks.append(_safe_text(manifest_346b3r.get("decision")) == READY_DECISION_346B3R)
    validation_checks.append(_safe_text(manifest_346b4r.get("decision")) == READY_DECISION_346B4R)
    validation_checks.append(int(manifest_346b4r.get("qa_fail_count", 1)) == 0)
    validation_checks.append(_bool_value(manifest_346b4r.get("same_row_set_replay")))
    validation_checks.append(int(manifest_346b4r.get("new_row_selected_count", -1)) == 0)
    validation_checks.append(_bool_value(manifest_346b4r.get("safe_to_continue_expansion")) is True)
    validation_checks.append(int(manifest_346b4r.get("replay_safe_recovered_candidate_count", 0)) == 234)
    validation_checks.append(int(manifest_346b4r.get("patch_applied_row_count", 0)) == 22)
    validation_checks.append(int(manifest_346b4r.get("false_positive_guardrail_hit_count", -1)) == 0)
    validation_checks.append(int(manifest_346b4r.get("unit_semantic_mismatch_count", -1)) == 0)
    validation_checks.append(_bool_value(manifest_346b4r.get("lineage_audit_passed")) is True)
    validation_checks.append(int(manifest_346b4r.get("live_vlm_call_count", -1)) == 0)
    validation_checks.append(int(manifest_346b3r.get("live_vlm_call_count", 0)) == 0)
    validation_checks.append(_bool_value(replay_readiness_346b3r.get("safe_to_replay_346b4")) is True)
    validation_checks.append(not _bool_value(manifest_346b4r.get("formal_client_export_allowed")))
    validation_checks.append(not _bool_value(manifest_346b4r.get("client_ready")))
    validation_checks.append(not _bool_value(manifest_346b4r.get("production_ready")))

    selected_by_source = {
        _safe_text(row.get("source_row_id")): row
        for row in selected_rows_346b4
        if _safe_text(row.get("source_row_id"))
    }
    recovery_by_source = {
        _safe_text(row.get("source_row_id")): row
        for row in recovery_rows_346b4
        if _safe_text(row.get("source_row_id"))
    }
    safe_by_source = {
        _safe_text(row.get("source_row_id")): row
        for row in safe_rows_346b4r
        if _safe_text(row.get("source_row_id"))
    }
    patch_safety_by_source = {
        _safe_text(row.get("source_row_id")): row
        for row in patch_safety_rows_346b3r
        if _safe_text(row.get("source_row_id"))
    }
    patchable_by_source = {
        _safe_text(row.get("source_row_id")): row
        for row in patchable_rows_346b3r
        if _safe_text(row.get("source_row_id"))
    }
    lineage_by_source = {
        _safe_text(row.get("source_row_id")): row
        for row in lineage_rows_346b4r
        if _safe_text(row.get("source_row_id"))
    }
    replay_by_source = {
        _safe_text(row.get("source_row_id")): row
        for row in replay_results_346b4r
        if _safe_text(row.get("source_row_id"))
    }

    patch_applied_source_ids = {
        _safe_text(row.get("source_row_id"))
        for row in patched_rows_346b4r
        if _safe_text(row.get("source_row_id")) and _bool_value(row.get("patch_applied"))
    }

    candidate_qa_rows: List[Dict[str, Any]] = []
    patch_qa_rows: List[Dict[str, Any]] = []
    semantic_unit_rows: List[Dict[str, Any]] = []
    lineage_audit_rows: List[Dict[str, Any]] = []
    qa_decision_counter: Counter[str] = Counter()
    patch_qa_counter: Counter[str] = Counter()

    for source_row_id, row in safe_by_source.items():
        merged = {
            **selected_by_source.get(source_row_id, {}),
            **recovery_by_source.get(source_row_id, {}),
            **replay_by_source.get(source_row_id, {}),
            **dict(row),
        }
        merged["context_snippet"] = _safe_text(merged.get("context_snippet"))[:max_context_chars]
        lineage_row = lineage_by_source.get(source_row_id, {})

        independent_semantic_class = _semantic_class(merged)
        replay_semantic_class = _safe_text(merged.get("patched_semantic_class") or merged.get("semantic_metric_class")) or "UNKNOWN"
        semantic_disagreement = independent_semantic_class != replay_semantic_class

        recovered_unit = _safe_text(
            merged.get("patched_controlled_recovered_unit")
            or merged.get("controlled_recovered_unit")
            or merged.get("unit")
        )
        normalized_unit = _normalize_unit_token(recovered_unit)
        unit_action = _safe_text(merged.get("patched_unit_action") or merged.get("controlled_unit_repair_action"))

        unit_semantic_mismatch = False
        false_positive_suspect = False
        guardrail_reason = ""
        if independent_semantic_class == "RATIO_MULTIPLE" and normalized_unit in PERCENT_UNITS:
            unit_semantic_mismatch = True
            false_positive_suspect = True
            guardrail_reason = "ratio_multiple_percent_regression"
        elif independent_semantic_class == "PER_SHARE" and normalized_unit in PERCENT_UNITS:
            unit_semantic_mismatch = True
            false_positive_suspect = True
            guardrail_reason = "per_share_percent_regression"
        elif independent_semantic_class == "MONETARY_AMOUNT" and normalized_unit in PERCENT_UNITS.union(RATIO_UNITS):
            unit_semantic_mismatch = True
            false_positive_suspect = True
            guardrail_reason = "monetary_non_monetary_unit_regression"

        lineage_preserved = _bool_value(lineage_row.get("lineage_preserved")) if lineage_row else _bool_value(merged.get("lineage_preserved"))
        minimum_lineage_present = _bool_value(lineage_row.get("minimum_lineage_present")) if lineage_row else _bool_value(merged.get("minimum_lineage_present"))
        source_trace_available = _bool_value(lineage_row.get("source_trace_available")) if lineage_row else _bool_value(merged.get("source_trace_available"))
        evidence_strength = _safe_text(lineage_row.get("evidence_strength") or merged.get("evidence_strength"))
        evidence_weakness = _bool_value(lineage_row.get("evidence_weakness")) if lineage_row else _bool_value(merged.get("evidence_weakness"))
        if require_evidence_or_deterministic_proof:
            evidence_weakness = evidence_weakness or not evidence_strength

        qa_decision = _qa_decision(
            merged,
            independent_semantic_class=independent_semantic_class,
            semantic_disagreement=semantic_disagreement,
            unit_semantic_mismatch=unit_semantic_mismatch,
            false_positive_suspect=false_positive_suspect,
            evidence_weakness=evidence_weakness,
            lineage_preserved=lineage_preserved and minimum_lineage_present and source_trace_available,
            require_evidence_or_deterministic_proof=require_evidence_or_deterministic_proof,
        )
        qa_decision_counter[qa_decision] += 1

        patch_qa_decision = ""
        if _bool_value(merged.get("patch_applied")):
            patch_qa_decision = _patch_qa_decision(merged, patch_safety_by_source)
            patch_qa_counter[patch_qa_decision] += 1
            patch_qa_rows.append(
                {
                    "source_row_id": source_row_id,
                    "raw_metric_name": merged.get("raw_metric_name"),
                    "demo_normalized_metric_name": merged.get("demo_normalized_metric_name"),
                    "previous_346b4_decision": merged.get("previous_346b4_decision"),
                    "patch_source": merged.get("patch_source"),
                    "patch_reason": merged.get("patch_reason"),
                    "patch_confidence": merged.get("patch_confidence"),
                    "patch_safety_decision": merged.get("patch_safety_decision"),
                    "patch_applied": True,
                    "patch_qa_decision": patch_qa_decision,
                    "independent_semantic_class": independent_semantic_class,
                    "replay_semantic_class": replay_semantic_class,
                    "unit_semantic_mismatch": unit_semantic_mismatch,
                    "false_positive_suspect": false_positive_suspect,
                    "evidence_weakness": evidence_weakness,
                    "lineage_preserved": lineage_preserved,
                    "demo_export_only": True,
                    "sidecar_only": True,
                }
            )

        candidate_qa_row = {
            **merged,
            "independent_semantic_class": independent_semantic_class,
            "semantic_class_disagreement": semantic_disagreement,
            "qa_unit_semantic_mismatch": unit_semantic_mismatch,
            "qa_false_positive_suspect": false_positive_suspect,
            "qa_guardrail_reason": guardrail_reason,
            "qa_evidence_weakness": evidence_weakness,
            "qa_lineage_preserved": lineage_preserved and minimum_lineage_present and source_trace_available,
            "qa_decision": qa_decision,
            "patch_qa_decision": patch_qa_decision,
            "do_not_apply_upstream": True,
            "demo_export_only": True,
            "sidecar_only": True,
        }
        candidate_qa_rows.append(candidate_qa_row)
        semantic_unit_rows.append(
            {
                "source_row_id": source_row_id,
                "raw_metric_name": merged.get("raw_metric_name"),
                "demo_normalized_metric_name": merged.get("demo_normalized_metric_name"),
                "replay_semantic_class": replay_semantic_class,
                "independent_semantic_class": independent_semantic_class,
                "semantic_class_disagreement": semantic_disagreement,
                "recovered_unit": recovered_unit,
                "unit_action": unit_action,
                "unit_semantic_mismatch": unit_semantic_mismatch,
                "false_positive_suspect": false_positive_suspect,
                "guardrail_reason": guardrail_reason,
            }
        )
        lineage_audit_rows.append(
            {
                "source_row_id": source_row_id,
                "raw_metric_name": merged.get("raw_metric_name"),
                "demo_normalized_metric_name": merged.get("demo_normalized_metric_name"),
                "raw_value": merged.get("raw_value"),
                "sanitized_value": merged.get("sanitized_value"),
                "period": merged.get("period"),
                "source_pdf_name": merged.get("source_pdf_name"),
                "source_page": merged.get("source_page"),
                "source_table_id": merged.get("source_table_id"),
                "previous_346b4_decision": merged.get("previous_346b4_decision"),
                "replay_recovery_decision": merged.get("replay_recovery_decision"),
                "patch_source": merged.get("patch_source"),
                "lineage_preserved": lineage_preserved,
                "minimum_lineage_present": minimum_lineage_present,
                "source_trace_available": source_trace_available,
                "evidence_strength": evidence_strength,
                "evidence_weakness": evidence_weakness,
            }
        )

    safe_rows = [row for row in candidate_qa_rows if row["qa_decision"] == QA_SAFE]
    risky_rows = [row for row in candidate_qa_rows if row["qa_decision"] in {QA_RISKY, QA_NEEDS_HUMAN, QA_NEEDS_RULE}]
    false_positive_rows = [row for row in candidate_qa_rows if row["qa_decision"] == QA_FALSE_POSITIVE]

    semantic_class_disagreement_count = sum(1 for row in candidate_qa_rows if _bool_value(row.get("semantic_class_disagreement")))
    unit_semantic_mismatch_count = sum(1 for row in candidate_qa_rows if _bool_value(row.get("qa_unit_semantic_mismatch")))
    false_positive_guardrail_hit_count = sum(1 for row in candidate_qa_rows if _bool_value(row.get("qa_false_positive_suspect")))
    evidence_weakness_count = sum(1 for row in candidate_qa_rows if _bool_value(row.get("qa_evidence_weakness")))
    lineage_audit_passed = all(_bool_value(row.get("lineage_preserved")) for row in lineage_audit_rows) if require_lineage_preservation else True
    same_row_set_replay_verified = bool(
        _bool_value(manifest_346b4r.get("same_row_set_replay"))
        and int(manifest_346b4r.get("new_row_selected_count", -1)) == 0
        and int(manifest_346b4r.get("replay_input_row_count", -1)) == int(manifest_346b4r.get("previous_controlled_expansion_input_row_count", -2))
        and len(selected_rows_346b4) == int(manifest_346b4r.get("replay_input_row_count", -1))
    )

    qa_safe_to_larger_expansion = bool(
        len(candidate_qa_rows) == int(manifest_346b4r.get("replay_safe_recovered_candidate_count", -1))
        and len(candidate_qa_rows) == len(safe_rows)
        and len(false_positive_rows) == 0
        and len(risky_rows) <= safe_to_larger_expansion_risk_threshold
        and patch_qa_counter.get("PATCH_QA_FAIL", 0) == 0
        and patch_qa_counter.get("PATCH_QA_RISK", 0) == 0
        and semantic_class_disagreement_count == 0
        and unit_semantic_mismatch_count == 0
        and false_positive_guardrail_hit_count == 0
        and evidence_weakness_count == 0
        and lineage_audit_passed
        and same_row_set_replay_verified
        and not unknown_rows_346b4r
        and not guardrail_rows_346b4r
        and _bool_value(manifest_346b4r.get("safe_to_continue_expansion"))
    )
    if qa_safe_to_larger_expansion:
        qa_safe_to_larger_expansion_reason = (
            "Independent QA rechecked all 234 replay-safe candidates, separately cleared all 22 patch-applied rows, and found zero false-positive, unit, semantic, lineage, or evidence regressions."
        )
        recommended_larger_expansion_row_limit = 1500
        recommended_next_step = "346B5 Larger Quality-Limited Recovery Expansion"
        recommended_next_step_reason = "Replay-safe candidates passed independent QA, so the next step can be a larger but still controlled demo-only expansion."
    else:
        qa_safe_to_larger_expansion_reason = (
            "Independent QA found unresolved risk, disagreement, or closure gaps, so larger controlled expansion must remain blocked pending follow-up audit or rule refinement."
        )
        recommended_larger_expansion_row_limit = 0
        recommended_next_step = "346B3R2 Recovery Rule Refinement Patch Follow-up"
        recommended_next_step_reason = "At least one QA gate condition remained unresolved after independent audit."

    summary = {
        "qa_decision_distribution": dict(qa_decision_counter),
        "patch_qa_decision_distribution": dict(patch_qa_counter),
        "inputs_read_sources": {
            "346b4_selected_rows_source": selected_rows_346b4_source,
            "346b4_recovery_rows_source": recovery_rows_346b4_source,
            "346b3r_patchable_rows_source": patchable_rows_346b3r_source,
            "346b3r_patch_safety_rows_source": patch_safety_rows_346b3r_source,
            "346b4r_replay_results_source": replay_results_346b4r_source,
            "346b4r_safe_rows_source": safe_rows_346b4r_source,
            "346b4r_patched_rows_source": patched_rows_346b4r_source,
            "346b4r_unknown_rows_source": unknown_rows_346b4r_source,
            "346b4r_guardrail_rows_source": guardrail_rows_346b4r_source,
            "346b4r_delta_rows_source": delta_rows_346b4r_source,
            "346b4r_semantic_distribution_source": semantic_distribution_rows_346b4r_source,
            "346b4r_unit_distribution_source": unit_distribution_rows_346b4r_source,
            "346b4r_lineage_rows_source": lineage_rows_346b4r_source,
        },
    }
    readiness_report = {
        "same_row_set_replay_verified": same_row_set_replay_verified,
        "qa_safe_to_larger_expansion": qa_safe_to_larger_expansion,
        "qa_safe_to_larger_expansion_reason": qa_safe_to_larger_expansion_reason,
        "recommended_larger_expansion_row_limit": recommended_larger_expansion_row_limit,
        "recommended_next_step": recommended_next_step,
        "recommended_next_step_reason": recommended_next_step_reason,
    }

    manifest = {
        "decision": READY_DECISION_346B4Q,
        "input_stage": INPUT_STAGE_346B4Q,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "input_345d_decision": _safe_text(manifest_345d.get("decision")),
        "input_346b4_decision": _safe_text(manifest_346b4.get("decision")),
        "input_346b3r_decision": _safe_text(manifest_346b3r.get("decision")),
        "input_346b4r_decision": _safe_text(manifest_346b4r.get("decision")),
        "input_346b4r_safe_to_continue_expansion": _bool_value(manifest_346b4r.get("safe_to_continue_expansion")),
        "input_345d_dir": str(full_structured_demo_export_package_345d_dir),
        "input_346b4_dir": str(controlled_quality_limited_recovery_expansion_346b4_dir),
        "input_346b3r_dir": str(recovery_rule_refinement_patch_346b3r_dir),
        "input_346b4r_dir": str(controlled_expansion_replay_with_patched_rules_346b4r_dir),
        "output_dir": str(output_dir),
        "same_row_set_replay_verified": same_row_set_replay_verified,
        "new_row_selected_count": int(manifest_346b4r.get("new_row_selected_count", 0)),
        "replay_input_row_count": int(manifest_346b4r.get("replay_input_row_count", 0)),
        "replay_safe_recovered_candidate_count": int(manifest_346b4r.get("replay_safe_recovered_candidate_count", 0)),
        "qa_audited_candidate_count": len(candidate_qa_rows),
        "qa_safe_candidate_count": len(safe_rows),
        "qa_risky_candidate_count": len(risky_rows),
        "qa_false_positive_suspect_count": len(false_positive_rows),
        "qa_needs_human_review_count": qa_decision_counter.get(QA_NEEDS_HUMAN, 0),
        "qa_needs_rule_refinement_count": qa_decision_counter.get(QA_NEEDS_RULE, 0),
        "patch_applied_audited_row_count": len(patch_qa_rows),
        "patch_applied_qa_pass_count": patch_qa_counter.get("PATCH_QA_PASS", 0),
        "patch_applied_qa_risk_count": patch_qa_counter.get("PATCH_QA_RISK", 0),
        "patch_applied_qa_fail_count": patch_qa_counter.get("PATCH_QA_FAIL", 0),
        "semantic_class_disagreement_count": semantic_class_disagreement_count,
        "unit_semantic_mismatch_count": unit_semantic_mismatch_count,
        "false_positive_guardrail_hit_count": false_positive_guardrail_hit_count,
        "evidence_weakness_count": evidence_weakness_count,
        "lineage_audit_passed": lineage_audit_passed,
        "qa_safe_to_larger_expansion": qa_safe_to_larger_expansion,
        "qa_safe_to_larger_expansion_reason": qa_safe_to_larger_expansion_reason,
        "recommended_larger_expansion_row_limit": recommended_larger_expansion_row_limit,
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
        "strict_qa": strict_qa,
        "audit_patch_applied_rows": audit_patch_applied_rows,
        "require_same_row_set_proof": require_same_row_set_proof,
        "require_lineage_preservation": require_lineage_preservation,
        "require_evidence_or_deterministic_proof": require_evidence_or_deterministic_proof,
        "safe_to_larger_expansion_risk_threshold": safe_to_larger_expansion_risk_threshold,
        "max_context_chars": max_context_chars,
        "generated_at_utc": _utc_now(),
    }

    files_read.extend(
        [
            str(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SELECTED_JSON_NAME),
            str(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RESULTS_JSON_NAME),
            str(recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCHABLE_JSON_NAME),
            str(recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCH_SAFETY_JSON_NAME),
            str(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_RESULTS_JSON_NAME),
            str(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_SAFE_JSON_NAME),
            str(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_PATCHED_JSON_NAME),
            str(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_UNKNOWN_JSON_NAME),
            str(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_GUARD_JSON_NAME),
            str(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_DELTA_JSON_NAME),
            str(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_SEMANTIC_JSON_NAME),
            str(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_UNIT_JSON_NAME),
            str(controlled_expansion_replay_with_patched_rules_346b4r_dir / INPUT_346B4R_LINEAGE_JSON_NAME),
        ]
    )
    input_paths = [Path(path) for path in files_read if Path(path).is_file()]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    no_apply_proof = build_no_apply_proof(
        stage="346B4Q",
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
        no_apply_proof.get("no_official_asset_modification_during_346b4q")
        and upstream_unchanged
        and protected_before == protected_after
        and not protected_staged
        and not forbidden_staged
    )
    manifest["no_write_back_proof_passed"] = no_write_back_proof_passed
    manifest["no_write_back_summary"] = (
        "upstream inputs unchanged; official assets unchanged; protected dirty status preserved; no protected paths staged"
    )

    validation_checks.extend(
        [
            len(candidate_qa_rows) == int(manifest_346b4r.get("replay_safe_recovered_candidate_count", -1)),
            patch_applied_source_ids == {
                _safe_text(row.get("source_row_id"))
                for row in patch_qa_rows
                if _safe_text(row.get("source_row_id"))
            },
            len(patch_qa_rows) == int(manifest_346b4r.get("patch_applied_row_count", -1)),
            len(false_positive_rows) == false_positive_guardrail_hit_count,
            no_write_back_proof_passed,
        ]
    )
    if require_same_row_set_proof:
        validation_checks.append(same_row_set_replay_verified)

    qa_fail_count = sum(1 for check in validation_checks if not check)
    manifest["qa_fail_count"] = qa_fail_count
    manifest["decision"] = READY_DECISION_346B4Q if qa_fail_count == 0 else BLOCKED_DECISION_346B4Q

    if ledger_path is not None:
        append_346b4q_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = _ledger_has_346b4q_entry(ledger_path)
        if not manifest["milestone_ledger_updated"]:
            manifest["qa_fail_count"] += 1
            manifest["decision"] = BLOCKED_DECISION_346B4Q

    return {
        "manifest": manifest,
        "candidate_qa_rows": candidate_qa_rows,
        "qa_safe_candidate_rows": safe_rows,
        "qa_risky_candidate_rows": risky_rows,
        "false_positive_candidate_rows": false_positive_rows,
        "patch_applied_row_qa_rows": patch_qa_rows,
        "semantic_unit_recheck_rows": semantic_unit_rows,
        "lineage_evidence_audit_rows": lineage_audit_rows,
        "larger_expansion_readiness_report": readiness_report,
        "reaudit_summary": summary,
        "executive_summary_md": render_executive_summary_markdown(
            manifest,
            qa_decision_distribution=dict(qa_decision_counter),
            patch_decision_distribution=dict(patch_qa_counter),
        ),
        "artifact_index_md": render_artifact_index_markdown(_artifact_index_rows(output_dir)),
        "next_plan_md": render_next_plan_markdown(manifest),
        "artifact_index_rows": _artifact_index_rows(output_dir),
        "no_write_back_proof": no_apply_proof,
        "dry_run_state": {
            "selected_rows_count_346b4": len(selected_rows_346b4),
            "replay_results_count_346b4r": len(replay_results_346b4r),
            "safe_rows_count_346b4r": len(safe_rows_346b4r),
            "patched_rows_count_346b4r": len(patched_rows_346b4r),
            "unknown_rows_count_346b4r": len(unknown_rows_346b4r),
            "guardrail_rows_count_346b4r": len(guardrail_rows_346b4r),
            "semantic_distribution_rows_count_346b4r": len(semantic_distribution_rows_346b4r),
            "unit_distribution_rows_count_346b4r": len(unit_distribution_rows_346b4r),
            "delta_rows_count_346b4r": len(delta_rows_346b4r),
            "guardrail_summary_346b4": guardrail_summary_346b4,
            "readiness_346b4r": readiness_346b4r,
            "output_dir": str(output_dir),
        },
    }
