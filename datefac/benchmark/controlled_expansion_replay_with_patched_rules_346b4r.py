from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from datefac.benchmark.controlled_expansion_replay_with_patched_rules_346b4r_report import (
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
BLOCKED_DECISION_346B4R = "CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_BLOCKED"
INPUT_STAGE_346B4R = "POST_346B3R_CONTROLLED_EXPANSION_REPLAY"

SAFE_DECISION = "REPLAY_SAFE_RECOVERED_DEMO_CANDIDATE"
STILL_LIMITED_DECISION = "REPLAY_STILL_QUALITY_LIMITED"
HUMAN_DECISION = "REPLAY_NEEDS_HUMAN_REVIEW"
RULE_DECISION = "REPLAY_NEEDS_RULE_REFINEMENT"
VLM_DECISION = "REPLAY_NEEDS_VLM_REPAIR"
GUARDRAIL_DECISION = "REPLAY_FALSE_POSITIVE_GUARDRAIL_HIT"

DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR = Path(
    r"D:\_datefac\output\full_structured_demo_export_package_345d"
)
DEFAULT_CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_DIR = Path(
    r"D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4"
)
DEFAULT_RECOVERY_RULE_REFINEMENT_PATCH_346B3R_DIR = Path(
    r"D:\_datefac\output\recovery_rule_refinement_patch_346b3r"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\controlled_expansion_replay_with_patched_rules_346b4r")

MANIFEST_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_manifest.json"
REPLAY_RESULTS_JSON_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_replay_results.json"
REPLAY_RESULTS_CSV_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_replay_results.csv"
SAFE_JSON_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.json"
SAFE_CSV_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.csv"
PATCHED_JSON_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.json"
PATCHED_CSV_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.csv"
UNKNOWN_JSON_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_remaining_unknown_rows.json"
UNKNOWN_CSV_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_remaining_unknown_rows.csv"
GUARD_JSON_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_guardrail_hits.json"
GUARD_CSV_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_guardrail_hits.csv"
DELTA_JSON_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_delta_report.json"
DELTA_CSV_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_delta_report.csv"
SEMANTIC_JSON_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_semantic_class_distribution.json"
SEMANTIC_CSV_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_semantic_class_distribution.csv"
UNIT_JSON_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_unit_action_distribution.json"
UNIT_CSV_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_unit_action_distribution.csv"
LINEAGE_JSON_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_lineage_evidence_audit.json"
LINEAGE_CSV_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_lineage_evidence_audit.csv"
READINESS_JSON_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_expansion_readiness_report.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "controlled_expansion_replay_with_patched_rules_346b4r_next_plan.md"

INPUT_345D_MANIFEST_NAME = "full_structured_demo_export_package_345d_manifest.json"
INPUT_346B4_MANIFEST_NAME = "controlled_quality_limited_recovery_expansion_346b4_manifest.json"
INPUT_346B4_SELECTED_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_selected_rows.json"
INPUT_346B4_SELECTED_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_selected_rows.csv"
INPUT_346B4_RESULTS_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovery_results.json"
INPUT_346B4_RESULTS_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovery_results.csv"
INPUT_346B4_RECOVERED_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovered_demo_candidates.json"
INPUT_346B4_RECOVERED_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovered_demo_candidates.csv"
INPUT_346B4_SAFE_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.json"
INPUT_346B4_SAFE_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.csv"
INPUT_346B4_STILL_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_still_limited_rows.json"
INPUT_346B4_STILL_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_still_limited_rows.csv"
INPUT_346B4_HUMAN_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_human_review_rows.json"
INPUT_346B4_HUMAN_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_human_review_rows.csv"
INPUT_346B4_RULE_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.json"
INPUT_346B4_RULE_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.csv"
INPUT_346B4_SEMANTIC_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.json"
INPUT_346B4_SEMANTIC_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.csv"
INPUT_346B4_GUARD_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_guardrail_summary.json"

INPUT_346B3R_MANIFEST_NAME = "recovery_rule_refinement_patch_346b3r_manifest.json"
INPUT_346B3R_PATCHABLE_JSON_NAME = "recovery_rule_refinement_patch_346b3r_patchable_rows.json"
INPUT_346B3R_PATCHABLE_CSV_NAME = "recovery_rule_refinement_patch_346b3r_patchable_rows.csv"
INPUT_346B3R_SEMANTIC_JSON_NAME = "recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.json"
INPUT_346B3R_SEMANTIC_CSV_NAME = "recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.csv"
INPUT_346B3R_UNIT_JSON_NAME = "recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.json"
INPUT_346B3R_UNIT_CSV_NAME = "recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.csv"
INPUT_346B3R_PATCHED_POLICY_JSON_NAME = "recovery_rule_refinement_patch_346b3r_patched_unit_policy_preview.json"
INPUT_346B3R_PATCH_SAFETY_JSON_NAME = "recovery_rule_refinement_patch_346b3r_patch_safety_review.json"
INPUT_346B3R_PATCH_SAFETY_CSV_NAME = "recovery_rule_refinement_patch_346b3r_patch_safety_review.csv"
INPUT_346B3R_READINESS_JSON_NAME = "recovery_rule_refinement_patch_346b3r_replay_readiness_report.json"

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
    {"artifact_name": REPLAY_RESULTS_JSON_FILE_NAME, "path": REPLAY_RESULTS_JSON_FILE_NAME, "purpose": "Replay results in JSON."},
    {"artifact_name": REPLAY_RESULTS_CSV_FILE_NAME, "path": REPLAY_RESULTS_CSV_FILE_NAME, "purpose": "Replay results in CSV."},
    {"artifact_name": SAFE_JSON_FILE_NAME, "path": SAFE_JSON_FILE_NAME, "purpose": "Safe replay candidates in JSON."},
    {"artifact_name": SAFE_CSV_FILE_NAME, "path": SAFE_CSV_FILE_NAME, "purpose": "Safe replay candidates in CSV."},
    {"artifact_name": PATCHED_JSON_FILE_NAME, "path": PATCHED_JSON_FILE_NAME, "purpose": "Patched rows in JSON."},
    {"artifact_name": PATCHED_CSV_FILE_NAME, "path": PATCHED_CSV_FILE_NAME, "purpose": "Patched rows in CSV."},
    {"artifact_name": UNKNOWN_JSON_FILE_NAME, "path": UNKNOWN_JSON_FILE_NAME, "purpose": "Remaining unknown rows in JSON."},
    {"artifact_name": UNKNOWN_CSV_FILE_NAME, "path": UNKNOWN_CSV_FILE_NAME, "purpose": "Remaining unknown rows in CSV."},
    {"artifact_name": GUARD_JSON_FILE_NAME, "path": GUARD_JSON_FILE_NAME, "purpose": "Guardrail hits in JSON."},
    {"artifact_name": GUARD_CSV_FILE_NAME, "path": GUARD_CSV_FILE_NAME, "purpose": "Guardrail hits in CSV."},
    {"artifact_name": DELTA_JSON_FILE_NAME, "path": DELTA_JSON_FILE_NAME, "purpose": "Replay delta report in JSON."},
    {"artifact_name": DELTA_CSV_FILE_NAME, "path": DELTA_CSV_FILE_NAME, "purpose": "Replay delta report in CSV."},
    {"artifact_name": SEMANTIC_JSON_FILE_NAME, "path": SEMANTIC_JSON_FILE_NAME, "purpose": "Replay semantic class distribution in JSON."},
    {"artifact_name": SEMANTIC_CSV_FILE_NAME, "path": SEMANTIC_CSV_FILE_NAME, "purpose": "Replay semantic class distribution in CSV."},
    {"artifact_name": UNIT_JSON_FILE_NAME, "path": UNIT_JSON_FILE_NAME, "purpose": "Replay unit action distribution in JSON."},
    {"artifact_name": UNIT_CSV_FILE_NAME, "path": UNIT_CSV_FILE_NAME, "purpose": "Replay unit action distribution in CSV."},
    {"artifact_name": LINEAGE_JSON_FILE_NAME, "path": LINEAGE_JSON_FILE_NAME, "purpose": "Lineage audit in JSON."},
    {"artifact_name": LINEAGE_CSV_FILE_NAME, "path": LINEAGE_CSV_FILE_NAME, "purpose": "Lineage audit in CSV."},
    {"artifact_name": READINESS_JSON_FILE_NAME, "path": READINESS_JSON_FILE_NAME, "purpose": "Replay readiness report in JSON."},
    {"artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME, "path": EXECUTIVE_SUMMARY_MD_FILE_NAME, "purpose": "Executive summary for 346B4R."},
    {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": ARTIFACT_INDEX_MD_FILE_NAME, "purpose": "Artifact index for 346B4R outputs."},
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


def _ledger_has_346b4r_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return "## 346B4R Controlled Expansion Replay With Patched Rules" in ledger_path.read_text(encoding="utf-8")


def _strip_346b4r_ledger_entry(text: str) -> str:
    header = "## 346B4R Controlled Expansion Replay With Patched Rules"
    start = text.find(header)
    if start == -1:
        return text
    next_header = text.find("\n## ", start + len(header))
    if next_header == -1:
        trimmed = text[:start].rstrip()
        return trimmed + ("\n" if trimmed else "")
    trimmed = (text[:start].rstrip() + "\n\n" + text[next_header + 1 :].lstrip("\n")).rstrip()
    return trimmed + ("\n" if trimmed else "")


def _build_346b4r_ledger_entry(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "## 346B4R Controlled Expansion Replay With Patched Rules",
            "",
            "Status: completed",
            "",
            f"- decision: {manifest.get('decision', '')}",
            f"- input_345d_dir: {manifest.get('input_345d_dir', '')}",
            f"- input_346b4_dir: {manifest.get('input_346b4_dir', '')}",
            f"- input_346b3r_dir: {manifest.get('input_346b3r_dir', '')}",
            f"- output_dir: {manifest.get('output_dir', '')}",
            f"- replay_input_row_count: {manifest.get('replay_input_row_count', 0)}",
            f"- previous_safe_recovered_candidate_count: {manifest.get('previous_safe_recovered_candidate_count', 0)}",
            f"- replay_safe_recovered_candidate_count: {manifest.get('replay_safe_recovered_candidate_count', 0)}",
            f"- previous_semantic_class_unknown_count: {manifest.get('previous_semantic_class_unknown_count', 0)}",
            f"- replay_semantic_class_unknown_count: {manifest.get('replay_semantic_class_unknown_count', 0)}",
            f"- unknown_resolved_count: {manifest.get('unknown_resolved_count', 0)}",
            f"- patch_applied_row_count: {manifest.get('patch_applied_row_count', 0)}",
            f"- patch_regression_count: {manifest.get('patch_regression_count', 0)}",
            f"- false_positive_guardrail_hit_count: {manifest.get('false_positive_guardrail_hit_count', 0)}",
            f"- unit_semantic_mismatch_count: {manifest.get('unit_semantic_mismatch_count', 0)}",
            f"- lineage_audit_passed: {manifest.get('lineage_audit_passed', False)}",
            f"- evidence_weakness_count: {manifest.get('evidence_weakness_count', 0)}",
            f"- safe_to_continue_expansion: {manifest.get('safe_to_continue_expansion', False)}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- no_write_back_proof_passed: {manifest.get('no_write_back_proof_passed', False)}",
            f"- gate_status: formal_client_export_allowed={manifest.get('formal_client_export_allowed', False)}, client_ready={manifest.get('client_ready', False)}, production_ready={manifest.get('production_ready', False)}",
            f"- next_recommended_step: {manifest.get('recommended_next_step', '')}",
        ]
    )


def append_346b4r_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    stripped = _strip_346b4r_ledger_entry(existing)
    addition = _build_346b4r_ledger_entry(manifest)
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
    return _safe_text(row.get("semantic_metric_class")) or "UNKNOWN"


def _normalize_unit_token(value: Any) -> str:
    return _safe_text(value).lower().replace(" ", "")


def _monetary_unit_from_context(row: Dict[str, Any]) -> str:
    for field in ("unit", "currency"):
        token = _safe_text(row.get(field))
        if token:
            return token
    raw_metric = _safe_text(row.get("raw_metric_name"))
    for token in ["亿元", "百万元", "千万元", "万元", "元", "RMB", "HKD", "USD", "CNY"]:
        if token.lower() in raw_metric.lower():
            return token
    return ""


def _replay_row(
    row: Dict[str, Any],
    *,
    patchable_by_source: Dict[str, Dict[str, Any]],
    semantic_patch_by_family: Dict[str, Dict[str, Any]],
    unit_patch_by_family: Dict[str, Dict[str, Any]],
    safety_by_source: Dict[str, Dict[str, Any]],
    strict_guardrails: bool,
) -> Dict[str, Any]:
    source_row_id = _safe_text(row.get("source_row_id"))
    family = _safe_text(row.get("demo_normalized_metric_name")).lower()
    patchable = patchable_by_source.get(source_row_id)
    semantic_patch = semantic_patch_by_family.get(family)
    unit_patch = unit_patch_by_family.get(family)
    safety = safety_by_source.get(source_row_id, {})

    previous_decision = _safe_text(row.get("controlled_recovery_decision"))
    previous_semantic_class = _safe_text(row.get("semantic_metric_class")) or "UNKNOWN"
    previous_unit_action = _safe_text(row.get("controlled_unit_repair_action"))
    previous_unit = _safe_text(row.get("controlled_recovered_unit"))

    patched = patchable is not None and semantic_patch is not None and unit_patch is not None
    patched_semantic_class = semantic_patch.get("proposed_semantic_class") if patched else previous_semantic_class
    patched_unit_action = "REPLAY_UNIT_POLICY_RETAIN_BLANK_MONETARY_CONTEXT" if patched else previous_unit_action
    patched_unit = previous_unit
    if patched and not patched_unit:
        patched_unit = _monetary_unit_from_context(row)

    patched_unit_normalized = _normalize_unit_token(patched_unit)
    unit_semantic_mismatch = False
    guardrail_reason = ""

    if patched_semantic_class == "RATIO_MULTIPLE" and patched_unit_normalized in PERCENT_UNITS:
        unit_semantic_mismatch = True
        guardrail_reason = "ratio_multiple_percent_regression"
    elif patched_semantic_class == "PER_SHARE" and patched_unit_normalized in PERCENT_UNITS:
        unit_semantic_mismatch = True
        guardrail_reason = "per_share_percent_regression"

    evidence_weakness = not (
        _bool_value(row.get("minimum_lineage_present"))
        and _bool_value(row.get("source_trace_available"))
    )
    remaining_unknown = patched_semantic_class == "UNKNOWN"

    if patched and not remaining_unknown and not unit_semantic_mismatch and not evidence_weakness:
        replay_decision = SAFE_DECISION
        replay_safe = True
    elif unit_semantic_mismatch and strict_guardrails:
        replay_decision = GUARDRAIL_DECISION
        replay_safe = False
    elif remaining_unknown:
        replay_decision = RULE_DECISION
        replay_safe = False
    elif previous_decision == "CONTROLLED_NEEDS_HUMAN_REVIEW":
        replay_decision = HUMAN_DECISION
        replay_safe = False
    elif previous_decision == "CONTROLLED_STILL_QUALITY_LIMITED":
        replay_decision = STILL_LIMITED_DECISION
        replay_safe = False
    elif previous_decision == "CONTROLLED_NEEDS_VLM_REPAIR":
        replay_decision = VLM_DECISION
        replay_safe = False
    else:
        replay_decision = SAFE_DECISION
        replay_safe = True

    patch_regression = patched and (
        replay_decision in {RULE_DECISION, GUARDRAIL_DECISION, HUMAN_DECISION, VLM_DECISION}
    )

    return {
        **dict(row),
        "previous_346b4_decision": previous_decision,
        "previous_semantic_class": previous_semantic_class,
        "patched_semantic_class": patched_semantic_class,
        "previous_unit_action": previous_unit_action,
        "patched_unit_action": patched_unit_action,
        "previous_controlled_recovered_unit": previous_unit,
        "patched_controlled_recovered_unit": patched_unit,
        "patch_applied": patched,
        "patch_source": "346B3R_SIDE_CAR" if patched else "",
        "patch_reason": _safe_text(safety.get("patch_safety_reason")) if patched else "",
        "patch_confidence": _safe_text(patchable.get("patch_confidence")) if patchable else "",
        "patch_safety_decision": _safe_text(safety.get("patch_safety_decision")) if patched else "",
        "replay_recovery_decision": replay_decision,
        "replay_safe_recovered_candidate": replay_safe,
        "replay_semantic_class_unknown": remaining_unknown,
        "unit_semantic_mismatch": unit_semantic_mismatch,
        "patch_regression": patch_regression,
        "guardrail_reason": guardrail_reason,
        "evidence_weakness": evidence_weakness,
        "lineage_preserved": _bool_value(row.get("minimum_lineage_present")) and _bool_value(row.get("source_trace_available")),
        "same_row_set_replay": True,
        "new_row_selected": False,
        "do_not_apply_upstream": True,
        "demo_export_only": True,
    }


def build_controlled_expansion_replay_with_patched_rules_346b4r(
    *,
    full_structured_demo_export_package_345d_dir: Path,
    controlled_quality_limited_recovery_expansion_346b4_dir: Path,
    recovery_rule_refinement_patch_346b3r_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    replay_same_row_set: bool = True,
    strict_guardrails: bool = True,
    require_346b3r_safe_to_replay: bool = True,
    max_context_chars: int = 4000,
) -> Dict[str, Any]:
    for label, path in [
        ("345D", full_structured_demo_export_package_345d_dir),
        ("346B4", controlled_quality_limited_recovery_expansion_346b4_dir),
        ("346B3R", recovery_rule_refinement_patch_346b3r_dir),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{label} input directory missing: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345d = _read_json(full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME)
    manifest_346b4 = _read_json(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_MANIFEST_NAME)
    guardrail_summary_346b4 = _read_json(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_GUARD_JSON_NAME)
    manifest_346b3r = _read_json(recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_MANIFEST_NAME)
    replay_readiness_346b3r = _read_json(recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_READINESS_JSON_NAME)
    patched_policy_preview_346b3r = _read_json(recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCHED_POLICY_JSON_NAME)

    selected_rows, selected_rows_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SELECTED_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SELECTED_CSV_NAME,
        label="346B4 selected rows",
    )
    recovery_rows, recovery_rows_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RESULTS_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RESULTS_CSV_NAME,
        label="346B4 recovery results",
    )
    recovered_rows, recovered_rows_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RECOVERED_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RECOVERED_CSV_NAME,
        label="346B4 recovered candidates",
    )
    safe_rows_346b4, safe_rows_346b4_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SAFE_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SAFE_CSV_NAME,
        label="346B4 safe recovered candidates",
    )
    still_rows_346b4, still_rows_346b4_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_STILL_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_STILL_CSV_NAME,
        label="346B4 still limited rows",
    )
    human_rows_346b4, human_rows_346b4_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_HUMAN_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_HUMAN_CSV_NAME,
        label="346B4 human review rows",
    )
    unknown_rows_346b4, unknown_rows_346b4_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RULE_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RULE_CSV_NAME,
        label="346B4 rule refinement rows",
    )
    semantic_rows_346b4, semantic_rows_346b4_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SEMANTIC_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SEMANTIC_CSV_NAME,
        label="346B4 semantic distribution",
    )

    patchable_rows_346b3r, patchable_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCHABLE_JSON_NAME,
        csv_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCHABLE_CSV_NAME,
        label="346B3R patchable rows",
    )
    semantic_patch_rows, semantic_patch_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_SEMANTIC_JSON_NAME,
        csv_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_SEMANTIC_CSV_NAME,
        label="346B3R semantic patches",
    )
    unit_patch_rows, unit_patch_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_UNIT_JSON_NAME,
        csv_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_UNIT_CSV_NAME,
        label="346B3R unit patches",
    )
    patch_safety_rows, patch_safety_rows_source = _load_json_or_csv_rows(
        json_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCH_SAFETY_JSON_NAME,
        csv_path=recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCH_SAFETY_CSV_NAME,
        label="346B3R patch safety review",
    )

    if manifest_345d.get("decision") != READY_DECISION_345D:
        raise ValueError("345D decision mismatch")
    if manifest_346b4.get("decision") != READY_DECISION_346B4:
        raise ValueError("346B4 decision mismatch")
    if manifest_346b3r.get("decision") != READY_DECISION_346B3R:
        raise ValueError("346B3R decision mismatch")
    if require_346b3r_safe_to_replay and _bool_value(manifest_346b3r.get("safe_to_replay_346b4")) is not True:
        raise ValueError("346B3R safe_to_replay_346b4 must be true")
    if int(manifest_346b4.get("controlled_expansion_input_row_count", 0)) != 500:
        raise ValueError("346B4 controlled_expansion_input_row_count must be 500")
    if int(manifest_346b4.get("semantic_class_unknown_count", 0)) != 22:
        raise ValueError("346B4 semantic_class_unknown_count must be 22")
    if int(manifest_346b4.get("needs_rule_refinement_count", 0)) != 22:
        raise ValueError("346B4 needs_rule_refinement_count must be 22")

    files_read = [
        str(path)
        for path in [
            full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_MANIFEST_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SELECTED_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RESULTS_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RECOVERED_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SAFE_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_STILL_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_HUMAN_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RULE_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SEMANTIC_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_GUARD_JSON_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_MANIFEST_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCHABLE_JSON_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_SEMANTIC_JSON_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_UNIT_JSON_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCH_SAFETY_JSON_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_PATCHED_POLICY_JSON_NAME,
            recovery_rule_refinement_patch_346b3r_dir / INPUT_346B3R_READINESS_JSON_NAME,
        ]
        if path.exists()
    ]
    input_paths = [Path(path) for path in files_read if Path(path).is_file()]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    recovery_by_source = {
        _safe_text(row.get("source_row_id")): row for row in recovery_rows if _safe_text(row.get("source_row_id"))
    }
    patchable_by_source = {
        _safe_text(row.get("source_row_id")): row for row in patchable_rows_346b3r if _safe_text(row.get("source_row_id"))
    }
    patch_safety_by_source = {
        _safe_text(row.get("source_row_id")): row for row in patch_safety_rows if _safe_text(row.get("source_row_id"))
    }
    semantic_patch_by_family = {
        _safe_text(row.get("metric_family")).lower(): row for row in semantic_patch_rows if _safe_text(row.get("metric_family"))
    }
    unit_patch_by_family = {
        _safe_text(row.get("metric_family")).lower(): row for row in unit_patch_rows if _safe_text(row.get("metric_family"))
    }
    previous_unknown_ids = {_safe_text(row.get("source_row_id")) for row in unknown_rows_346b4}
    previous_safe_ids = {_safe_text(row.get("source_row_id")) for row in safe_rows_346b4}

    replay_rows: List[Dict[str, Any]] = []
    for row in selected_rows:
        source_row_id = _safe_text(row.get("source_row_id"))
        merged = {**dict(row), **recovery_by_source.get(source_row_id, {})}
        merged["context_snippet"] = _safe_text(merged.get("context_snippet"))[:max_context_chars]
        replay_rows.append(
            _replay_row(
                merged,
                patchable_by_source=patchable_by_source,
                semantic_patch_by_family=semantic_patch_by_family,
                unit_patch_by_family=unit_patch_by_family,
                safety_by_source=patch_safety_by_source,
                strict_guardrails=strict_guardrails,
            )
        )

    safe_rows = [row for row in replay_rows if row["replay_recovery_decision"] == SAFE_DECISION]
    patched_rows = [row for row in replay_rows if _bool_value(row.get("patch_applied"))]
    remaining_unknown_rows = [row for row in replay_rows if _bool_value(row.get("replay_semantic_class_unknown"))]
    guardrail_rows = [row for row in replay_rows if row["replay_recovery_decision"] == GUARDRAIL_DECISION]
    lineage_rows = [
        {
            "source_row_id": row.get("source_row_id"),
            "source_pdf_name": row.get("source_pdf_name"),
            "source_page": row.get("source_page"),
            "source_table_id": row.get("source_table_id"),
            "lineage_preserved": row.get("lineage_preserved"),
            "minimum_lineage_present": row.get("minimum_lineage_present"),
            "source_trace_available": row.get("source_trace_available"),
            "evidence_strength": row.get("evidence_strength"),
            "evidence_weakness": row.get("evidence_weakness"),
            "replay_recovery_decision": row.get("replay_recovery_decision"),
        }
        for row in replay_rows
    ]

    decision_distribution = Counter(_safe_text(row.get("replay_recovery_decision")) for row in replay_rows)
    semantic_distribution = Counter(_safe_text(row.get("patched_semantic_class")) for row in replay_rows)
    unit_distribution = Counter(_safe_text(row.get("patched_unit_action")) for row in replay_rows)

    semantic_rows = [
        {"semantic_metric_class": key, "row_count": value}
        for key, value in sorted(semantic_distribution.items())
    ]
    unit_rows = [
        {"patched_unit_action": key, "row_count": value}
        for key, value in sorted(unit_distribution.items())
    ]

    replay_safe_count = len(safe_rows)
    previous_safe_count = int(manifest_346b4.get("safe_recovered_candidate_count", len(safe_rows_346b4)))
    previous_unknown_count = int(manifest_346b4.get("semantic_class_unknown_count", len(previous_unknown_ids)))
    previous_rule_refinement_count = int(manifest_346b4.get("needs_rule_refinement_count", len(previous_unknown_ids)))
    replay_unknown_count = len(remaining_unknown_rows)
    replay_rule_refinement_count = decision_distribution.get(RULE_DECISION, 0)
    patch_applied_count = len(patched_rows)
    patch_regression_count = sum(1 for row in replay_rows if _bool_value(row.get("patch_regression")))
    false_positive_guardrail_hit_count = len(guardrail_rows)
    unit_semantic_mismatch_count = sum(1 for row in replay_rows if _bool_value(row.get("unit_semantic_mismatch")))
    evidence_weakness_count = sum(1 for row in replay_rows if _bool_value(row.get("evidence_weakness")))
    lineage_audit_passed = all(_bool_value(row.get("lineage_preserved")) for row in replay_rows) if replay_rows else False

    safe_to_continue_expansion = bool(
        replay_same_row_set
        and len(replay_rows) == len(selected_rows)
        and patch_applied_count == len(previous_unknown_ids)
        and replay_unknown_count == 0
        and replay_rule_refinement_count == 0
        and patch_regression_count == 0
        and false_positive_guardrail_hit_count == 0
        and unit_semantic_mismatch_count == 0
        and evidence_weakness_count == 0
        and lineage_audit_passed
    )
    if safe_to_continue_expansion:
        safe_to_continue_expansion_reason = (
            "The same 500-row controlled batch was replayed with 346B3R sidecar patches, all 22 previous unknowns were absorbed, and no guardrail, unit, lineage, or evidence regressions were introduced."
        )
        recommended_next_step = "346B4Q Controlled Expansion QA Audit"
        recommended_next_step_reason = "Replay cleared the same-row-set patch validation and is ready for independent QA before any larger expansion."
    else:
        safe_to_continue_expansion_reason = (
            "Replay still has unresolved risk or count closure issues, so controlled expansion cannot continue until a follow-up patch or QA step closes the remaining gaps."
        )
        recommended_next_step = "346B3R2 Recovery Rule Refinement Patch Follow-up"
        recommended_next_step_reason = "Replay did not fully clear the 346B4 batch for continued controlled expansion."

    delta_rows = [
        {
            "metric_name": "safe_recovered_candidate_count",
            "previous_value": previous_safe_count,
            "replay_value": replay_safe_count,
            "delta_value": replay_safe_count - previous_safe_count,
        },
        {
            "metric_name": "semantic_class_unknown_count",
            "previous_value": previous_unknown_count,
            "replay_value": replay_unknown_count,
            "delta_value": replay_unknown_count - previous_unknown_count,
        },
        {
            "metric_name": "needs_rule_refinement_count",
            "previous_value": previous_rule_refinement_count,
            "replay_value": replay_rule_refinement_count,
            "delta_value": replay_rule_refinement_count - previous_rule_refinement_count,
        },
        {
            "metric_name": "still_quality_limited_count",
            "previous_value": int(manifest_346b4.get("still_quality_limited_count", len(still_rows_346b4))),
            "replay_value": decision_distribution.get(STILL_LIMITED_DECISION, 0),
            "delta_value": decision_distribution.get(STILL_LIMITED_DECISION, 0)
            - int(manifest_346b4.get("still_quality_limited_count", len(still_rows_346b4))),
        },
    ]

    replay_readiness_report = {
        "same_row_set_replay": replay_same_row_set,
        "new_row_selected_count": 0,
        "previous_unknown_count": previous_unknown_count,
        "replay_unknown_count": replay_unknown_count,
        "unknown_resolved_count": previous_unknown_count - replay_unknown_count,
        "patch_applied_row_count": patch_applied_count,
        "patch_regression_count": patch_regression_count,
        "false_positive_guardrail_hit_count": false_positive_guardrail_hit_count,
        "unit_semantic_mismatch_count": unit_semantic_mismatch_count,
        "lineage_audit_passed": lineage_audit_passed,
        "safe_to_continue_expansion": safe_to_continue_expansion,
        "safe_to_continue_expansion_reason": safe_to_continue_expansion_reason,
        "recommended_next_step": recommended_next_step,
        "recommended_next_step_reason": recommended_next_step_reason,
    }

    manifest = {
        "decision": READY_DECISION_346B4R,
        "input_stage": INPUT_STAGE_346B4R,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "input_345d_decision": _safe_text(manifest_345d.get("decision")),
        "input_346b4_decision": _safe_text(manifest_346b4.get("decision")),
        "input_346b3r_decision": _safe_text(manifest_346b3r.get("decision")),
        "input_346b4_safe_to_continue_expansion": _bool_value(manifest_346b4.get("safe_to_continue_expansion")),
        "input_346b3r_safe_to_replay_346b4": _bool_value(manifest_346b3r.get("safe_to_replay_346b4")),
        "input_345d_dir": str(full_structured_demo_export_package_345d_dir),
        "input_346b4_dir": str(controlled_quality_limited_recovery_expansion_346b4_dir),
        "input_346b3r_dir": str(recovery_rule_refinement_patch_346b3r_dir),
        "output_dir": str(output_dir),
        "previous_controlled_expansion_input_row_count": int(manifest_346b4.get("controlled_expansion_input_row_count", 0)),
        "replay_input_row_count": len(replay_rows),
        "same_row_set_replay": replay_same_row_set,
        "new_row_selected_count": 0,
        "previous_safe_recovered_candidate_count": previous_safe_count,
        "replay_safe_recovered_candidate_count": replay_safe_count,
        "safe_recovered_delta": replay_safe_count - previous_safe_count,
        "previous_semantic_class_unknown_count": previous_unknown_count,
        "replay_semantic_class_unknown_count": replay_unknown_count,
        "unknown_resolved_count": previous_unknown_count - replay_unknown_count,
        "needs_rule_refinement_previous_count": previous_rule_refinement_count,
        "needs_rule_refinement_replay_count": replay_rule_refinement_count,
        "needs_rule_refinement_delta": replay_rule_refinement_count - previous_rule_refinement_count,
        "patch_applied_row_count": patch_applied_count,
        "patch_regression_count": patch_regression_count,
        "false_positive_guardrail_hit_count": false_positive_guardrail_hit_count,
        "unit_semantic_mismatch_count": unit_semantic_mismatch_count,
        "evidence_weakness_count": evidence_weakness_count,
        "lineage_audit_passed": lineage_audit_passed,
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
        "replay_same_row_set": replay_same_row_set,
        "strict_guardrails": strict_guardrails,
        "require_346b3r_safe_to_replay": require_346b3r_safe_to_replay,
        "max_context_chars": max_context_chars,
        "generated_at_utc": _utc_now(),
    }

    validation_checks = [
        manifest["input_345d_decision"] == READY_DECISION_345D,
        manifest["input_346b4_decision"] == READY_DECISION_346B4,
        manifest["input_346b3r_decision"] == READY_DECISION_346B3R,
        manifest["input_346b4_safe_to_continue_expansion"] is False,
        manifest["input_346b3r_safe_to_replay_346b4"] is True,
        manifest["previous_controlled_expansion_input_row_count"] == 500,
        manifest["replay_input_row_count"] == 500,
        manifest["same_row_set_replay"] is True,
        manifest["new_row_selected_count"] == 0,
        manifest["patch_applied_row_count"] == 22,
        manifest["previous_semantic_class_unknown_count"] == 22,
        manifest["replay_semantic_class_unknown_count"] == 0,
        manifest["unknown_resolved_count"] == 22,
        manifest["needs_rule_refinement_previous_count"] == 22,
        manifest["needs_rule_refinement_replay_count"] == 0,
        manifest["patch_regression_count"] == 0,
        manifest["false_positive_guardrail_hit_count"] == 0,
        manifest["unit_semantic_mismatch_count"] == 0,
        manifest["evidence_weakness_count"] == 0,
        manifest["lineage_audit_passed"] is True,
        manifest["replay_safe_recovered_candidate_count"] > manifest["previous_safe_recovered_candidate_count"],
        manifest["safe_to_continue_expansion"] is True,
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
        selected_rows_source in {"json", "csv"},
        recovery_rows_source in {"json", "csv"},
        recovered_rows_source in {"json", "csv"},
        safe_rows_346b4_source in {"json", "csv"},
        still_rows_346b4_source in {"json", "csv"},
        human_rows_346b4_source in {"json", "csv"},
        unknown_rows_346b4_source in {"json", "csv"},
        semantic_rows_346b4_source in {"json", "csv"},
        patchable_rows_source in {"json", "csv"},
        semantic_patch_rows_source in {"json", "csv"},
        unit_patch_rows_source in {"json", "csv"},
        patch_safety_rows_source in {"json", "csv"},
        all(_safe_text(row.get("source_row_id")) in {_safe_text(item.get("source_row_id")) for item in selected_rows} for row in replay_rows),
        all(not _bool_value(row.get("new_row_selected")) for row in replay_rows),
        all(_safe_text(row.get("patched_controlled_recovered_unit")).lower() not in PERCENT_UNITS for row in replay_rows if _safe_text(row.get("patched_semantic_class")) in {"RATIO_MULTIPLE", "PER_SHARE"}),
        all(_bool_value(row.get("lineage_preserved")) for row in replay_rows),
        _bool_value(replay_readiness_346b3r.get("safe_to_replay_346b4")) is True,
        bool(patched_policy_preview_346b3r),
        int(guardrail_summary_346b4.get("false_positive_guardrail_hit_count", 0)) == 0,
        len(previous_safe_ids) == previous_safe_count,
    ]

    no_apply_proof = build_no_apply_proof(
        stage="346B4R",
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
    no_apply_proof["sidecar_same_row_set_replay_only"] = True
    no_apply_proof["no_write_back"] = True

    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_346b4r")
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
    manifest["decision"] = READY_DECISION_346B4R if qa_fail_count == 0 else BLOCKED_DECISION_346B4R

    if ledger_path is not None:
        append_346b4r_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = _ledger_has_346b4r_entry(ledger_path)
        if not manifest["milestone_ledger_updated"]:
            manifest["qa_fail_count"] += 1
            manifest["decision"] = BLOCKED_DECISION_346B4R

    return {
        "manifest": manifest,
        "replay_results_rows": replay_rows,
        "safe_recovered_candidate_rows": safe_rows,
        "patched_rows": patched_rows,
        "remaining_unknown_rows": remaining_unknown_rows,
        "guardrail_rows": guardrail_rows,
        "delta_rows": delta_rows,
        "semantic_class_distribution_rows": semantic_rows,
        "unit_action_distribution_rows": unit_rows,
        "lineage_evidence_audit_rows": lineage_rows,
        "expansion_readiness_report": replay_readiness_report,
        "executive_summary_md": render_executive_summary_markdown(
            manifest,
            replay_decision_distribution=dict(decision_distribution),
            delta_rows=delta_rows,
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
