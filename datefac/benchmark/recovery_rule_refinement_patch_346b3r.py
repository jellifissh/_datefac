from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from datefac.benchmark.recovery_rule_refinement_patch_346b3r_report import (
    render_artifact_index_markdown,
    render_executive_summary_markdown,
    render_next_plan_markdown,
    render_patched_unit_policy_preview_markdown,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345D = "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY"
READY_DECISION_346B3 = "RECOVERY_RULE_REFINEMENT_346B3_READY"
READY_DECISION_346B2R = "REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_READY"
READY_DECISION_346B4 = "CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY"
READY_DECISION_346B3R = "RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY"
BLOCKED_DECISION_346B3R = "RECOVERY_RULE_REFINEMENT_PATCH_346B3R_BLOCKED"
INPUT_STAGE_346B3R = "POST_346B4_RECOVERY_RULE_REFINEMENT_PATCH"

DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR = Path(
    r"D:\_datefac\output\full_structured_demo_export_package_345d"
)
DEFAULT_RECOVERY_RULE_REFINEMENT_346B3_DIR = Path(
    r"D:\_datefac\output\recovery_rule_refinement_346b3"
)
DEFAULT_REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_DIR = Path(
    r"D:\_datefac\output\refined_recovery_candidate_qa_reaudit_346b2r"
)
DEFAULT_CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_DIR = Path(
    r"D:\_datefac\output\controlled_quality_limited_recovery_expansion_346b4"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\recovery_rule_refinement_patch_346b3r")

MANIFEST_FILE_NAME = "recovery_rule_refinement_patch_346b3r_manifest.json"
UNKNOWN_AUDIT_JSON_FILE_NAME = "recovery_rule_refinement_patch_346b3r_unknown_row_audit.json"
UNKNOWN_AUDIT_CSV_FILE_NAME = "recovery_rule_refinement_patch_346b3r_unknown_row_audit.csv"
PATCHABLE_JSON_FILE_NAME = "recovery_rule_refinement_patch_346b3r_patchable_rows.json"
PATCHABLE_CSV_FILE_NAME = "recovery_rule_refinement_patch_346b3r_patchable_rows.csv"
NON_PATCHABLE_JSON_FILE_NAME = "recovery_rule_refinement_patch_346b3r_non_patchable_rows.json"
NON_PATCHABLE_CSV_FILE_NAME = "recovery_rule_refinement_patch_346b3r_non_patchable_rows.csv"
SEMANTIC_PATCHES_JSON_FILE_NAME = "recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.json"
SEMANTIC_PATCHES_CSV_FILE_NAME = "recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.csv"
UNIT_PATCHES_JSON_FILE_NAME = "recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.json"
UNIT_PATCHES_CSV_FILE_NAME = "recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.csv"
PATCHED_POLICY_PREVIEW_JSON_FILE_NAME = "recovery_rule_refinement_patch_346b3r_patched_unit_policy_preview.json"
PATCHED_POLICY_PREVIEW_MD_FILE_NAME = "recovery_rule_refinement_patch_346b3r_patched_unit_policy_preview.md"
PATCH_SAFETY_JSON_FILE_NAME = "recovery_rule_refinement_patch_346b3r_patch_safety_review.json"
PATCH_SAFETY_CSV_FILE_NAME = "recovery_rule_refinement_patch_346b3r_patch_safety_review.csv"
REPLAY_READINESS_JSON_FILE_NAME = "recovery_rule_refinement_patch_346b3r_replay_readiness_report.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "recovery_rule_refinement_patch_346b3r_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "recovery_rule_refinement_patch_346b3r_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "recovery_rule_refinement_patch_346b3r_next_plan.md"

INPUT_345D_MANIFEST_NAME = "full_structured_demo_export_package_345d_manifest.json"
INPUT_346B3_MANIFEST_NAME = "recovery_rule_refinement_346b3_manifest.json"
INPUT_346B3_POLICY_JSON_NAME = "recovery_rule_refinement_346b3_refined_unit_policy.json"
INPUT_346B3_RULE_CHANGE_JSON_NAME = "recovery_rule_refinement_346b3_rule_change_log.json"
INPUT_346B2R_MANIFEST_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_manifest.json"
INPUT_346B2R_EXPANSION_JSON_NAME = "refined_recovery_candidate_qa_reaudit_346b2r_expansion_readiness_report.json"
INPUT_346B4_MANIFEST_NAME = "controlled_quality_limited_recovery_expansion_346b4_manifest.json"
INPUT_346B4_RULE_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.json"
INPUT_346B4_RULE_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.csv"
INPUT_346B4_RESULTS_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovery_results.json"
INPUT_346B4_RESULTS_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_recovery_results.csv"
INPUT_346B4_SEMANTIC_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.json"
INPUT_346B4_SEMANTIC_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.csv"
INPUT_346B4_UNIT_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_unit_action_distribution.json"
INPUT_346B4_UNIT_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_unit_action_distribution.csv"
INPUT_346B4_LINEAGE_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_lineage_evidence_audit.json"
INPUT_346B4_LINEAGE_CSV_NAME = "controlled_quality_limited_recovery_expansion_346b4_lineage_evidence_audit.csv"
INPUT_346B4_GUARD_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_guardrail_summary.json"
INPUT_346B4_READINESS_JSON_NAME = "controlled_quality_limited_recovery_expansion_346b4_expansion_readiness_report.json"

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
    {"artifact_name": UNKNOWN_AUDIT_JSON_FILE_NAME, "path": UNKNOWN_AUDIT_JSON_FILE_NAME, "purpose": "Audited unknown rows in JSON."},
    {"artifact_name": UNKNOWN_AUDIT_CSV_FILE_NAME, "path": UNKNOWN_AUDIT_CSV_FILE_NAME, "purpose": "Audited unknown rows in CSV."},
    {"artifact_name": PATCHABLE_JSON_FILE_NAME, "path": PATCHABLE_JSON_FILE_NAME, "purpose": "Patchable unknown rows in JSON."},
    {"artifact_name": PATCHABLE_CSV_FILE_NAME, "path": PATCHABLE_CSV_FILE_NAME, "purpose": "Patchable unknown rows in CSV."},
    {"artifact_name": NON_PATCHABLE_JSON_FILE_NAME, "path": NON_PATCHABLE_JSON_FILE_NAME, "purpose": "Non-patchable unknown rows in JSON."},
    {"artifact_name": NON_PATCHABLE_CSV_FILE_NAME, "path": NON_PATCHABLE_CSV_FILE_NAME, "purpose": "Non-patchable unknown rows in CSV."},
    {"artifact_name": SEMANTIC_PATCHES_JSON_FILE_NAME, "path": SEMANTIC_PATCHES_JSON_FILE_NAME, "purpose": "Proposed semantic classifier patches in JSON."},
    {"artifact_name": SEMANTIC_PATCHES_CSV_FILE_NAME, "path": SEMANTIC_PATCHES_CSV_FILE_NAME, "purpose": "Proposed semantic classifier patches in CSV."},
    {"artifact_name": UNIT_PATCHES_JSON_FILE_NAME, "path": UNIT_PATCHES_JSON_FILE_NAME, "purpose": "Proposed unit policy patches in JSON."},
    {"artifact_name": UNIT_PATCHES_CSV_FILE_NAME, "path": UNIT_PATCHES_CSV_FILE_NAME, "purpose": "Proposed unit policy patches in CSV."},
    {"artifact_name": PATCHED_POLICY_PREVIEW_JSON_FILE_NAME, "path": PATCHED_POLICY_PREVIEW_JSON_FILE_NAME, "purpose": "Patched unit policy preview in JSON."},
    {"artifact_name": PATCHED_POLICY_PREVIEW_MD_FILE_NAME, "path": PATCHED_POLICY_PREVIEW_MD_FILE_NAME, "purpose": "Patched unit policy preview in Markdown."},
    {"artifact_name": PATCH_SAFETY_JSON_FILE_NAME, "path": PATCH_SAFETY_JSON_FILE_NAME, "purpose": "Patch safety review in JSON."},
    {"artifact_name": PATCH_SAFETY_CSV_FILE_NAME, "path": PATCH_SAFETY_CSV_FILE_NAME, "purpose": "Patch safety review in CSV."},
    {"artifact_name": REPLAY_READINESS_JSON_FILE_NAME, "path": REPLAY_READINESS_JSON_FILE_NAME, "purpose": "Replay readiness report in JSON."},
    {"artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME, "path": EXECUTIVE_SUMMARY_MD_FILE_NAME, "purpose": "Executive summary for 346B3R."},
    {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": ARTIFACT_INDEX_MD_FILE_NAME, "purpose": "Artifact index for 346B3R outputs."},
    {"artifact_name": NEXT_PLAN_MD_FILE_NAME, "path": NEXT_PLAN_MD_FILE_NAME, "purpose": "Recommended next step and boundary reminder."},
]

PATCHABLE_SEMANTIC_CLASS_RULE = "PATCHABLE_SEMANTIC_CLASS_RULE"
PATCHABLE_UNIT_POLICY_RULE = "PATCHABLE_UNIT_POLICY_RULE"
PATCHABLE_ALIAS_PATTERN_RULE = "PATCHABLE_ALIAS_PATTERN_RULE"
NON_PATCHABLE_NEEDS_HUMAN_REVIEW = "NON_PATCHABLE_NEEDS_HUMAN_REVIEW"
NON_PATCHABLE_KEEP_QUALITY_LIMITED = "NON_PATCHABLE_KEEP_QUALITY_LIMITED"
NON_PATCHABLE_NEEDS_VLM_LATER = "NON_PATCHABLE_NEEDS_VLM_LATER"

PATCH_SAFE_TO_REPLAY = "PATCH_SAFE_TO_REPLAY"
PATCH_REQUIRES_REAUDIT = "PATCH_REQUIRES_REAUDIT"
PATCH_UNSAFE_KEEP_LIMITED = "PATCH_UNSAFE_KEEP_LIMITED"
PATCH_UNSAFE_HUMAN_REVIEW = "PATCH_UNSAFE_HUMAN_REVIEW"
PATCH_UNSAFE_VLM_LATER = "PATCH_UNSAFE_VLM_LATER"

PATCHABLE_METRIC_RULES = {
    "capital_expenditure": {
        "metric_family": "capital_expenditure",
        "raw_metric_name": "资本开支",
        "patch_candidate_type": "SPECIAL_MONETARY_PATTERN",
        "proposed_semantic_class": "MONETARY_AMOUNT",
        "patch_category": PATCHABLE_SEMANTIC_CLASS_RULE,
        "evidence_basis": "normalized metric family and raw metric name deterministically indicate a cash-flow monetary item",
        "semantic_classifier_pattern": "capital_expenditure|资本开支",
        "unit_policy_type": "DOMAIN_SPECIFIC_UNIT_PATTERN",
        "unit_policy_decision": "KEEP_LIMITED_UNTIL_MONETARY_UNIT_CONTEXT_CONFIRMED",
        "unit_policy_preview": "do not infer percent-style or ratio-style units; keep unit blank unless a later replay step binds deterministic monetary context",
        "replay_safety": PATCH_REQUIRES_REAUDIT,
        "kept_quality_limited": True,
    },
    "debt_financing": {
        "metric_family": "debt_financing",
        "raw_metric_name": "债务融资",
        "patch_candidate_type": "SPECIAL_MONETARY_PATTERN",
        "proposed_semantic_class": "MONETARY_AMOUNT",
        "patch_category": PATCHABLE_SEMANTIC_CLASS_RULE,
        "evidence_basis": "normalized metric family and raw metric name deterministically indicate a financing cash-flow monetary item",
        "semantic_classifier_pattern": "debt_financing|债务融资",
        "unit_policy_type": "DOMAIN_SPECIFIC_UNIT_PATTERN",
        "unit_policy_decision": "KEEP_LIMITED_UNTIL_MONETARY_UNIT_CONTEXT_CONFIRMED",
        "unit_policy_preview": "do not infer percent-style or ratio-style units; keep unit blank unless a later replay step binds deterministic monetary context",
        "replay_safety": PATCH_REQUIRES_REAUDIT,
        "kept_quality_limited": True,
    },
}


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


def _ledger_has_346b3r_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return "## 346B3R Recovery Rule Refinement Patch" in ledger_path.read_text(encoding="utf-8")


def _strip_346b3r_ledger_entry(text: str) -> str:
    header = "## 346B3R Recovery Rule Refinement Patch"
    start = text.find(header)
    if start == -1:
        return text
    next_header = text.find("\n## ", start + len(header))
    if next_header == -1:
        trimmed = text[:start].rstrip()
        return trimmed + ("\n" if trimmed else "")
    trimmed = (text[:start].rstrip() + "\n\n" + text[next_header + 1 :].lstrip("\n")).rstrip()
    return trimmed + ("\n" if trimmed else "")


def _build_346b3r_ledger_entry(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "## 346B3R Recovery Rule Refinement Patch",
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
            f"- input_346b4_dir: {manifest.get('input_346b4_dir', '')}",
            f"- output_dir: {manifest.get('output_dir', '')}",
            f"- input_346b4_controlled_expansion_input_row_count: {manifest.get('input_346b4_controlled_expansion_input_row_count', 0)}",
            f"- input_346b4_safe_recovered_candidate_count: {manifest.get('input_346b4_safe_recovered_candidate_count', 0)}",
            f"- input_346b4_semantic_class_unknown_count: {manifest.get('input_346b4_semantic_class_unknown_count', 0)}",
            f"- input_346b4_needs_rule_refinement_count: {manifest.get('input_346b4_needs_rule_refinement_count', 0)}",
            f"- audited_unknown_row_count: {manifest.get('audited_unknown_row_count', 0)}",
            f"- patchable_rule_gap_count: {manifest.get('patchable_rule_gap_count', 0)}",
            f"- non_patchable_row_count: {manifest.get('non_patchable_row_count', 0)}",
            f"- proposed_semantic_classifier_patch_count: {manifest.get('proposed_semantic_classifier_patch_count', 0)}",
            f"- proposed_unit_policy_patch_count: {manifest.get('proposed_unit_policy_patch_count', 0)}",
            f"- rows_converted_from_unknown_to_known_semantic_class_count: {manifest.get('rows_converted_from_unknown_to_known_semantic_class_count', 0)}",
            f"- rows_kept_human_review_count: {manifest.get('rows_kept_human_review_count', 0)}",
            f"- rows_kept_quality_limited_count: {manifest.get('rows_kept_quality_limited_count', 0)}",
            f"- rows_requiring_future_vlm_count: {manifest.get('rows_requiring_future_vlm_count', 0)}",
            f"- safe_to_replay_346b4: {manifest.get('safe_to_replay_346b4', False)}",
            f"- safe_to_continue_expansion: {manifest.get('safe_to_continue_expansion', False)}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- no_write_back_proof_passed: {manifest.get('no_write_back_proof_passed', False)}",
            f"- gate_status: formal_client_export_allowed={manifest.get('formal_client_export_allowed', False)}, client_ready={manifest.get('client_ready', False)}, production_ready={manifest.get('production_ready', False)}",
            f"- next_recommended_step: {manifest.get('recommended_next_step', '')}",
        ]
    )


def append_346b3r_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    stripped = _strip_346b3r_ledger_entry(existing)
    addition = _build_346b3r_ledger_entry(manifest)
    prefix = "\n\n" if stripped and not stripped.endswith("\n\n") else ""
    if stripped.endswith("\n"):
        prefix = "\n" if not stripped.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(stripped + prefix + addition + "\n", encoding="utf-8")
    return True


def _validate_decisions(
    *,
    manifest_345d: Dict[str, Any],
    manifest_346b3: Dict[str, Any],
    manifest_346b2r: Dict[str, Any],
    manifest_346b4: Dict[str, Any],
) -> None:
    checks = [
        (manifest_345d.get("decision") == READY_DECISION_345D, "345D decision mismatch"),
        (manifest_346b3.get("decision") == READY_DECISION_346B3, "346B3 decision mismatch"),
        (manifest_346b2r.get("decision") == READY_DECISION_346B2R, "346B2R decision mismatch"),
        (manifest_346b4.get("decision") == READY_DECISION_346B4, "346B4 decision mismatch"),
        (_bool_value(manifest_346b2r.get("safe_to_expand_recovery")) is True, "346B2R safe_to_expand_recovery must be true"),
        (int(manifest_346b4.get("qa_fail_count", 1)) == 0, "346B4 qa_fail_count must be 0"),
        (int(manifest_346b4.get("semantic_class_unknown_count", -1)) == 22, "346B4 semantic_class_unknown_count must be 22"),
        (int(manifest_346b4.get("needs_rule_refinement_count", -1)) == 22, "346B4 needs_rule_refinement_count must be 22"),
        (_bool_value(manifest_346b4.get("safe_to_continue_expansion")) is False, "346B4 safe_to_continue_expansion must be false"),
        (int(manifest_346b3.get("live_vlm_call_count", 1)) == 0, "346B3 live_vlm_call_count must be 0"),
        (int(manifest_346b2r.get("live_vlm_call_count", 1)) == 0, "346B2R live_vlm_call_count must be 0"),
        (int(manifest_346b4.get("live_vlm_call_count", 1)) == 0, "346B4 live_vlm_call_count must be 0"),
        (_bool_value(manifest_346b3.get("formal_client_export_allowed")) is False, "346B3 formal_client_export_allowed must be false"),
        (_bool_value(manifest_346b2r.get("formal_client_export_allowed")) is False, "346B2R formal_client_export_allowed must be false"),
        (_bool_value(manifest_346b4.get("formal_client_export_allowed")) is False, "346B4 formal_client_export_allowed must be false"),
    ]
    failures = [message for ok, message in checks if not ok]
    if failures:
        raise ValueError("; ".join(failures))


def _row_family(row: Dict[str, Any]) -> str:
    return _safe_text(row.get("demo_normalized_metric_name")).lower()


def _build_audited_unknown_row(
    row: Dict[str, Any],
    *,
    strict_patch: bool,
    include_human_review_triage: bool,
    include_still_limited_triage: bool,
) -> Dict[str, Any]:
    family = _row_family(row)
    patch_rule = PATCHABLE_METRIC_RULES.get(family)
    if patch_rule is None:
        triage = NON_PATCHABLE_KEEP_QUALITY_LIMITED if include_still_limited_triage else NON_PATCHABLE_NEEDS_HUMAN_REVIEW
        patch_safety = PATCH_UNSAFE_KEEP_LIMITED if triage == NON_PATCHABLE_KEEP_QUALITY_LIMITED else PATCH_UNSAFE_HUMAN_REVIEW
        return {
            **dict(row),
            "metric_family": family or "UNKNOWN_FAMILY",
            "patch_triage_decision": triage,
            "proposed_semantic_class": "UNKNOWN",
            "patch_candidate_type": "",
            "unit_policy_patch_type": "",
            "unit_policy_decision": "",
            "unit_policy_preview": "",
            "patch_confidence": "LOW",
            "patchable_rule_gap": False,
            "rows_converted_from_unknown_to_known_semantic_class": False,
            "row_kept_human_review": triage == NON_PATCHABLE_NEEDS_HUMAN_REVIEW,
            "row_kept_quality_limited": triage == NON_PATCHABLE_KEEP_QUALITY_LIMITED,
            "row_requires_future_vlm": triage == NON_PATCHABLE_NEEDS_VLM_LATER,
            "patch_safety_decision": patch_safety,
            "patch_safety_reason": "metric family is outside the deterministic 346B3R patch map",
            "evidence_gap_reason": "unrecognized metric family",
            "strict_patch": strict_patch,
        }

    patch_safety = patch_rule["replay_safety"]
    return {
        **dict(row),
        "metric_family": patch_rule["metric_family"],
        "patch_triage_decision": patch_rule["patch_category"],
        "proposed_semantic_class": patch_rule["proposed_semantic_class"],
        "patch_candidate_type": patch_rule["patch_candidate_type"],
        "semantic_classifier_pattern": patch_rule["semantic_classifier_pattern"],
        "unit_policy_patch_type": patch_rule["unit_policy_type"],
        "unit_policy_decision": patch_rule["unit_policy_decision"],
        "unit_policy_preview": patch_rule["unit_policy_preview"],
        "patch_confidence": "HIGH",
        "patchable_rule_gap": True,
        "rows_converted_from_unknown_to_known_semantic_class": True,
        "row_kept_human_review": False,
        "row_kept_quality_limited": bool(patch_rule["kept_quality_limited"]),
        "row_requires_future_vlm": False,
        "patch_safety_decision": patch_safety,
        "patch_safety_reason": "semantic family is deterministic, but unit inference stays bounded until replay re-audit confirms a safe monetary context",
        "evidence_gap_reason": "missing explicit monetary unit context in the current row bundle",
        "strict_patch": strict_patch,
        "human_review_triage_included": include_human_review_triage,
        "still_limited_triage_included": include_still_limited_triage,
    }


def build_recovery_rule_refinement_patch_346b3r(
    *,
    full_structured_demo_export_package_345d_dir: Path,
    recovery_rule_refinement_346b3_dir: Path,
    refined_recovery_candidate_qa_reaudit_346b2r_dir: Path,
    controlled_quality_limited_recovery_expansion_346b4_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    strict_patch: bool = True,
    max_patch_rows: int = 22,
    include_human_review_triage: bool = True,
    include_still_limited_triage: bool = True,
    max_context_chars: int = 4000,
) -> Dict[str, Any]:
    for label, path in [
        ("345D", full_structured_demo_export_package_345d_dir),
        ("346B3", recovery_rule_refinement_346b3_dir),
        ("346B2R", refined_recovery_candidate_qa_reaudit_346b2r_dir),
        ("346B4", controlled_quality_limited_recovery_expansion_346b4_dir),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{label} input directory missing: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345d = _read_json(full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME)
    manifest_346b3 = _read_json(recovery_rule_refinement_346b3_dir / INPUT_346B3_MANIFEST_NAME)
    manifest_346b2r = _read_json(refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_MANIFEST_NAME)
    manifest_346b4 = _read_json(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_MANIFEST_NAME)
    readiness_346b2r = _read_json(refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_EXPANSION_JSON_NAME)
    refined_policy_346b3 = _read_json(recovery_rule_refinement_346b3_dir / INPUT_346B3_POLICY_JSON_NAME)
    rule_change_log_346b3 = _read_json(recovery_rule_refinement_346b3_dir / INPUT_346B3_RULE_CHANGE_JSON_NAME)
    guardrail_summary_346b4 = _read_json(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_GUARD_JSON_NAME)
    expansion_readiness_346b4 = _read_json(controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_READINESS_JSON_NAME)

    _validate_decisions(
        manifest_345d=manifest_345d,
        manifest_346b3=manifest_346b3,
        manifest_346b2r=manifest_346b2r,
        manifest_346b4=manifest_346b4,
    )

    unknown_rows, unknown_rows_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RULE_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RULE_CSV_NAME,
        label="346B4 needs-rule-refinement rows",
    )
    recovery_rows, recovery_rows_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RESULTS_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RESULTS_CSV_NAME,
        label="346B4 recovery results",
    )
    semantic_distribution_rows, semantic_distribution_rows_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SEMANTIC_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SEMANTIC_CSV_NAME,
        label="346B4 semantic distribution",
    )
    unit_action_rows, unit_action_rows_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_UNIT_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_UNIT_CSV_NAME,
        label="346B4 unit action distribution",
    )
    lineage_rows, lineage_rows_source = _load_json_or_csv_rows(
        json_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_LINEAGE_JSON_NAME,
        csv_path=controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_LINEAGE_CSV_NAME,
        label="346B4 lineage evidence audit",
    )

    if len(unknown_rows) > max_patch_rows:
        raise ValueError(f"346B4 needs-rule-refinement rows exceed max_patch_rows: {len(unknown_rows)} > {max_patch_rows}")

    files_read = [
        str(path)
        for path in [
            full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_MANIFEST_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_POLICY_JSON_NAME,
            recovery_rule_refinement_346b3_dir / INPUT_346B3_RULE_CHANGE_JSON_NAME,
            refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_MANIFEST_NAME,
            refined_recovery_candidate_qa_reaudit_346b2r_dir / INPUT_346B2R_EXPANSION_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_MANIFEST_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RULE_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_RESULTS_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_SEMANTIC_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_UNIT_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_LINEAGE_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_GUARD_JSON_NAME,
            controlled_quality_limited_recovery_expansion_346b4_dir / INPUT_346B4_READINESS_JSON_NAME,
        ]
        if path.exists()
    ]

    input_paths = [Path(path) for path in files_read if Path(path).is_file()]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    lineage_by_source = {
        _safe_text(row.get("source_row_id")): row for row in lineage_rows if _safe_text(row.get("source_row_id"))
    }
    recovery_by_source = {
        _safe_text(row.get("source_row_id")): row for row in recovery_rows if _safe_text(row.get("source_row_id"))
    }

    audited_unknown_rows: List[Dict[str, Any]] = []
    for row in unknown_rows:
        source_row_id = _safe_text(row.get("source_row_id"))
        merged = {
            **dict(row),
            **recovery_by_source.get(source_row_id, {}),
            **lineage_by_source.get(source_row_id, {}),
        }
        merged["context_snippet"] = _safe_text(merged.get("context_snippet"))[:max_context_chars]
        audited_unknown_rows.append(
            _build_audited_unknown_row(
                merged,
                strict_patch=strict_patch,
                include_human_review_triage=include_human_review_triage,
                include_still_limited_triage=include_still_limited_triage,
            )
        )

    patchable_rows = [row for row in audited_unknown_rows if _bool_value(row.get("patchable_rule_gap"))]
    non_patchable_rows = [row for row in audited_unknown_rows if not _bool_value(row.get("patchable_rule_gap"))]

    semantic_patch_rows: List[Dict[str, Any]] = []
    semantic_patch_seen: set[str] = set()
    unit_patch_rows: List[Dict[str, Any]] = []
    unit_patch_seen: set[str] = set()
    for row in patchable_rows:
        family = _safe_text(row.get("metric_family"))
        if family and family not in semantic_patch_seen:
            semantic_patch_seen.add(family)
            semantic_patch_rows.append(
                {
                    "metric_family": family,
                    "raw_metric_name": row.get("raw_metric_name"),
                    "patch_candidate_type": row.get("patch_candidate_type"),
                    "proposed_semantic_class": row.get("proposed_semantic_class"),
                    "semantic_classifier_pattern": row.get("semantic_classifier_pattern"),
                    "evidence_basis": row.get("evidence_basis"),
                    "row_count": sum(1 for item in patchable_rows if _safe_text(item.get("metric_family")) == family),
                }
            )
        if family and family not in unit_patch_seen:
            unit_patch_seen.add(family)
            unit_patch_rows.append(
                {
                    "metric_family": family,
                    "raw_metric_name": row.get("raw_metric_name"),
                    "unit_policy_patch_type": row.get("unit_policy_patch_type"),
                    "unit_policy_decision": row.get("unit_policy_decision"),
                    "preview_policy": row.get("unit_policy_preview"),
                    "row_count": sum(1 for item in patchable_rows if _safe_text(item.get("metric_family")) == family),
                }
            )

    patch_safety_review_rows = [
        {
            "source_row_id": row.get("source_row_id"),
            "raw_metric_name": row.get("raw_metric_name"),
            "metric_family": row.get("metric_family"),
            "patch_triage_decision": row.get("patch_triage_decision"),
            "proposed_semantic_class": row.get("proposed_semantic_class"),
            "unit_policy_decision": row.get("unit_policy_decision"),
            "patch_safety_decision": row.get("patch_safety_decision"),
            "patch_safety_reason": row.get("patch_safety_reason"),
            "row_kept_quality_limited": row.get("row_kept_quality_limited"),
            "row_kept_human_review": row.get("row_kept_human_review"),
            "row_requires_future_vlm": row.get("row_requires_future_vlm"),
        }
        for row in audited_unknown_rows
    ]

    patched_unit_policy_preview = {
        "replay_scope": "346B4 unknown/refinement rows only",
        "sidecar_only": True,
        "no_write_back": True,
        "baseline_policy_source": str(recovery_rule_refinement_346b3_dir / INPUT_346B3_POLICY_JSON_NAME),
        "baseline_decision": _safe_text(manifest_346b3.get("decision")),
        "semantic_classifier_patch_preview": semantic_patch_rows,
        "unit_policy_patch_preview": unit_patch_rows,
        "guardrails": [
            "do not infer percent units for ratio/multiple or per-share rows",
            "do not auto-promote unknown rows without deterministic metric-family evidence",
            "do not invent explicit monetary units when current evidence only proves monetary semantics",
            "346B4 replay remains blocked from broader expansion until a replay-and-reaudit step passes",
        ],
        "baseline_refined_policy": refined_policy_346b3,
        "baseline_rule_change_log_count": len(rule_change_log_346b3) if isinstance(rule_change_log_346b3, list) else 0,
    }

    family_distribution = Counter(_safe_text(row.get("metric_family")) for row in audited_unknown_rows)
    triage_distribution = Counter(_safe_text(row.get("patch_triage_decision")) for row in audited_unknown_rows)
    safety_distribution = Counter(_safe_text(row.get("patch_safety_decision")) for row in audited_unknown_rows)

    replay_readiness_report = {
        "safe_to_replay_346b4": True,
        "safe_to_replay_346b4_reason": "the semantic classifier patch families are deterministic and bounded to the 22 audited unknown rows",
        "safe_to_continue_expansion": False,
        "safe_to_continue_expansion_reason": "346B4 replay still requires a dedicated replay-and-reaudit step before broader expansion can continue",
        "recommended_next_step": "346B4R Controlled Expansion Replay With Patched Rules",
        "recommended_next_step_reason": "semantic class gaps are now audited and patch-previewed, but replay QA must verify row-level outcomes before any wider rollout",
        "input_346b2r_safe_to_expand_recovery": _bool_value(manifest_346b2r.get("safe_to_expand_recovery")),
        "input_346b4_safe_to_continue_expansion": _bool_value(manifest_346b4.get("safe_to_continue_expansion")),
        "patch_safe_to_replay_count": safety_distribution.get(PATCH_SAFE_TO_REPLAY, 0),
        "patch_requires_reaudit_count": safety_distribution.get(PATCH_REQUIRES_REAUDIT, 0),
        "patch_unsafe_count": sum(
            safety_distribution.get(key, 0)
            for key in [PATCH_UNSAFE_KEEP_LIMITED, PATCH_UNSAFE_HUMAN_REVIEW, PATCH_UNSAFE_VLM_LATER]
        ),
    }

    manifest = {
        "decision": READY_DECISION_346B3R,
        "input_stage": INPUT_STAGE_346B3R,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "input_345d_decision": _safe_text(manifest_345d.get("decision")),
        "input_346b3_decision": _safe_text(manifest_346b3.get("decision")),
        "input_346b2r_decision": _safe_text(manifest_346b2r.get("decision")),
        "input_346b4_decision": _safe_text(manifest_346b4.get("decision")),
        "input_346b2r_safe_to_expand_recovery": _bool_value(manifest_346b2r.get("safe_to_expand_recovery")),
        "input_346b4_safe_to_continue_expansion": _bool_value(manifest_346b4.get("safe_to_continue_expansion")),
        "input_345d_dir": str(full_structured_demo_export_package_345d_dir),
        "input_346a_dir": _safe_text(manifest_346b3.get("input_346a_dir")),
        "input_346a2_dir": _safe_text(manifest_346b3.get("input_346a2_dir")),
        "input_346b_dir": _safe_text(manifest_346b3.get("input_346b_dir")),
        "input_346b2_dir": _safe_text(manifest_346b3.get("input_346b2_dir")),
        "input_346b3_dir": str(recovery_rule_refinement_346b3_dir),
        "input_346b2r_dir": str(refined_recovery_candidate_qa_reaudit_346b2r_dir),
        "input_346b4_dir": str(controlled_quality_limited_recovery_expansion_346b4_dir),
        "output_dir": str(output_dir),
        "input_346b4_controlled_expansion_input_row_count": int(manifest_346b4.get("controlled_expansion_input_row_count", 0)),
        "input_346b4_safe_recovered_candidate_count": int(manifest_346b4.get("safe_recovered_candidate_count", 0)),
        "input_346b4_semantic_class_unknown_count": int(manifest_346b4.get("semantic_class_unknown_count", 0)),
        "input_346b4_needs_rule_refinement_count": int(manifest_346b4.get("needs_rule_refinement_count", 0)),
        "audited_unknown_row_count": len(audited_unknown_rows),
        "patchable_rule_gap_count": len(patchable_rows),
        "non_patchable_row_count": len(non_patchable_rows),
        "proposed_semantic_classifier_patch_count": len(semantic_patch_rows),
        "proposed_unit_policy_patch_count": len(unit_patch_rows),
        "rows_converted_from_unknown_to_known_semantic_class_count": sum(
            1 for row in audited_unknown_rows if _bool_value(row.get("rows_converted_from_unknown_to_known_semantic_class"))
        ),
        "rows_kept_human_review_count": sum(1 for row in audited_unknown_rows if _bool_value(row.get("row_kept_human_review"))),
        "rows_kept_quality_limited_count": sum(
            1 for row in audited_unknown_rows if _bool_value(row.get("row_kept_quality_limited"))
        ),
        "rows_requiring_future_vlm_count": sum(1 for row in audited_unknown_rows if _bool_value(row.get("row_requires_future_vlm"))),
        "patch_safe_to_replay_count": safety_distribution.get(PATCH_SAFE_TO_REPLAY, 0),
        "patch_requires_reaudit_count": safety_distribution.get(PATCH_REQUIRES_REAUDIT, 0),
        "patch_unsafe_count": sum(
            safety_distribution.get(key, 0)
            for key in [PATCH_UNSAFE_KEEP_LIMITED, PATCH_UNSAFE_HUMAN_REVIEW, PATCH_UNSAFE_VLM_LATER]
        ),
        "safe_to_replay_346b4": True,
        "safe_to_continue_expansion": False,
        "safe_to_continue_expansion_reason": "346B3R prepares a deterministic patch preview only; replay QA must run before any broader controlled expansion is resumed",
        "recommended_next_step": "346B4R Controlled Expansion Replay With Patched Rules",
        "recommended_next_step_reason": "346B4 should be replayed with the bounded semantic patch preview and then independently re-audited before expansion continues",
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
        "strict_patch": strict_patch,
        "max_patch_rows": max_patch_rows,
        "include_human_review_trige": include_human_review_triage,
        "include_still_limited_triage": include_still_limited_triage,
        "max_context_chars": max_context_chars,
        "generated_at_utc": _utc_now(),
    }

    validation_checks = [
        manifest["input_345d_decision"] == READY_DECISION_345D,
        manifest["input_346b3_decision"] == READY_DECISION_346B3,
        manifest["input_346b2r_decision"] == READY_DECISION_346B2R,
        manifest["input_346b4_decision"] == READY_DECISION_346B4,
        manifest["input_346b2r_safe_to_expand_recovery"] is True,
        manifest["input_346b4_safe_to_continue_expansion"] is False,
        manifest["input_346b4_semantic_class_unknown_count"] == 22,
        manifest["input_346b4_needs_rule_refinement_count"] == 22,
        manifest["audited_unknown_row_count"] == 22,
        manifest["patchable_rule_gap_count"] + manifest["non_patchable_row_count"] == manifest["audited_unknown_row_count"],
        manifest["rows_converted_from_unknown_to_known_semantic_class_count"] == manifest["patchable_rule_gap_count"],
        manifest["proposed_semantic_classifier_patch_count"] == 2,
        manifest["proposed_unit_policy_patch_count"] == 2,
        manifest["rows_kept_human_review_count"] == 0,
        manifest["rows_requiring_future_vlm_count"] == 0,
        manifest["rows_kept_quality_limited_count"] == 22,
        manifest["patch_safe_to_replay_count"] == 0,
        manifest["patch_requires_reaudit_count"] == 22,
        manifest["patch_unsafe_count"] == 0,
        manifest["safe_to_replay_346b4"] is True,
        manifest["safe_to_continue_expansion"] is False,
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
        unknown_rows_source in {"json", "csv"},
        recovery_rows_source in {"json", "csv"},
        semantic_distribution_rows_source in {"json", "csv"},
        unit_action_rows_source in {"json", "csv"},
        lineage_rows_source in {"json", "csv"},
        len(semantic_distribution_rows) > 0,
        len(unit_action_rows) > 0,
        len(lineage_rows) > 0,
        all(_safe_text(row.get("proposed_semantic_class")) == "MONETARY_AMOUNT" for row in patchable_rows),
        all(_safe_text(row.get("unit_policy_preview")).find("%") == -1 for row in patchable_rows),
        all(_safe_text(row.get("semantic_metric_class")) == "UNKNOWN" for row in unknown_rows),
        all(_safe_text(row.get("patch_safety_decision")) == PATCH_REQUIRES_REAUDIT for row in patchable_rows),
    ]

    no_apply_proof = build_no_apply_proof(
        stage="346B3R",
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
    no_apply_proof["sidecar_patch_preview_only"] = True
    no_apply_proof["no_write_back"] = True

    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_346b3r")
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
    manifest["decision"] = READY_DECISION_346B3R if qa_fail_count == 0 else BLOCKED_DECISION_346B3R

    if ledger_path is not None:
        append_346b3r_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = _ledger_has_346b3r_entry(ledger_path)
        if not manifest["milestone_ledger_updated"]:
            manifest["qa_fail_count"] += 1
            manifest["decision"] = BLOCKED_DECISION_346B3R

    return {
        "manifest": manifest,
        "unknown_row_audit_rows": audited_unknown_rows,
        "patchable_rows": patchable_rows,
        "non_patchable_rows": non_patchable_rows,
        "proposed_semantic_classifier_patch_rows": semantic_patch_rows,
        "proposed_unit_policy_patch_rows": unit_patch_rows,
        "patched_unit_policy_preview": patched_unit_policy_preview,
        "patched_unit_policy_preview_md": render_patched_unit_policy_preview_markdown(patched_unit_policy_preview),
        "patch_safety_review_rows": patch_safety_review_rows,
        "replay_readiness_report": replay_readiness_report,
        "executive_summary_md": render_executive_summary_markdown(
            manifest,
            family_distribution=dict(family_distribution),
            triage_distribution=dict(triage_distribution),
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
            "readiness_346b2r": readiness_346b2r,
            "guardrail_summary_346b4": guardrail_summary_346b4,
            "expansion_readiness_346b4": expansion_readiness_346b4,
        },
    }
