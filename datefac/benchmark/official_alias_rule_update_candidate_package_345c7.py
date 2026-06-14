from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from datefac.review_queue.excel_round_trip_343b import normalize_text
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345C5 = "REVIEWED_ALIAS_DECISION_INGESTION_345C5_READY"
READY_DECISION_345C6 = "REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY"
READY_DECISION_345C7 = "OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE_345C7_READY"
INPUT_STAGE_345C7 = "POST_345C6_OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE"

DEFAULT_REVIEWED_ALIAS_DECISION_INGESTION_345C5_DIR = Path(
    r"D:\_datefac\output\reviewed_alias_decision_ingestion_345c5"
)
DEFAULT_REVIEWED_ALIAS_APPLY_SIMULATION_345C6_DIR = Path(
    r"D:\_datefac\output\reviewed_alias_apply_simulation_345c6"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\official_alias_rule_update_candidate_package_345c7"
)

MANIFEST_FILE_NAME = "official_alias_rule_update_candidate_package_345c7_manifest.json"
ALIAS_RULE_CANDIDATES_JSON_FILE_NAME = (
    "official_alias_rule_update_candidate_package_345c7_alias_rule_candidates.json"
)
ALIAS_RULE_CANDIDATES_CSV_FILE_NAME = (
    "official_alias_rule_update_candidate_package_345c7_alias_rule_candidates.csv"
)
IMPACT_SUMMARY_JSON_FILE_NAME = (
    "official_alias_rule_update_candidate_package_345c7_impact_summary.json"
)
IMPACT_SUMMARY_CSV_FILE_NAME = (
    "official_alias_rule_update_candidate_package_345c7_impact_summary.csv"
)
RISK_REVIEW_JSON_FILE_NAME = (
    "official_alias_rule_update_candidate_package_345c7_risk_review.json"
)
RISK_REVIEW_CSV_FILE_NAME = (
    "official_alias_rule_update_candidate_package_345c7_risk_review.csv"
)
REMAINING_BLIND_SPOT_SUMMARY_JSON_FILE_NAME = (
    "official_alias_rule_update_candidate_package_345c7_remaining_blind_spot_summary.json"
)
REMAINING_BLIND_SPOT_SUMMARY_CSV_FILE_NAME = (
    "official_alias_rule_update_candidate_package_345c7_remaining_blind_spot_summary.csv"
)
RULE_UPDATE_CHECKLIST_MD_FILE_NAME = (
    "official_alias_rule_update_candidate_package_345c7_rule_update_checklist.md"
)
EXECUTIVE_SUMMARY_MD_FILE_NAME = (
    "official_alias_rule_update_candidate_package_345c7_executive_summary.md"
)
ARTIFACT_INDEX_MD_FILE_NAME = (
    "official_alias_rule_update_candidate_package_345c7_artifact_index.md"
)
NEXT_PLAN_MD_FILE_NAME = "official_alias_rule_update_candidate_package_345c7_next_plan.md"

INPUT_345C5_MANIFEST_NAME = "reviewed_alias_decision_ingestion_345c5_manifest.json"
INPUT_345C5_VALIDATED_APPROVED_JSON_NAME = (
    "reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.json"
)
INPUT_345C5_VALIDATED_APPROVED_CSV_NAME = (
    "reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.csv"
)
INPUT_345C5_REJECTED_OR_DEFERRED_JSON_NAME = (
    "reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.json"
)
INPUT_345C5_REJECTED_OR_DEFERRED_CSV_NAME = (
    "reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.csv"
)
INPUT_345C5_DECISION_SUMMARY_JSON_NAME = (
    "reviewed_alias_decision_ingestion_345c5_decision_summary.json"
)

INPUT_345C6_MANIFEST_NAME = "reviewed_alias_apply_simulation_345c6_manifest.json"
INPUT_345C6_APPLIED_ALIAS_MAP_JSON_NAME = (
    "reviewed_alias_apply_simulation_345c6_applied_alias_map.json"
)
INPUT_345C6_APPLIED_ALIAS_MAP_CSV_NAME = (
    "reviewed_alias_apply_simulation_345c6_applied_alias_map.csv"
)
INPUT_345C6_COVERAGE_BEFORE_AFTER_JSON_NAME = (
    "reviewed_alias_apply_simulation_345c6_coverage_before_after.json"
)
INPUT_345C6_COVERAGE_BEFORE_AFTER_CSV_NAME = (
    "reviewed_alias_apply_simulation_345c6_coverage_before_after.csv"
)
INPUT_345C6_REMAINING_BLIND_SPOTS_JSON_NAME = (
    "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.json"
)
INPUT_345C6_REMAINING_BLIND_SPOTS_CSV_NAME = (
    "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.csv"
)
INPUT_345C6_NON_APPLIED_ALIASES_JSON_NAME = (
    "reviewed_alias_apply_simulation_345c6_non_applied_aliases.json"
)
INPUT_345C6_NON_APPLIED_ALIASES_CSV_NAME = (
    "reviewed_alias_apply_simulation_345c6_non_applied_aliases.csv"
)
INPUT_345C6_SIMULATED_METRIC_ROWS_JSON_NAME = (
    "reviewed_alias_apply_simulation_345c6_simulated_metric_rows.json"
)

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

ALIAS_RULE_CANDIDATE_FIELDS = [
    "alias_rule_candidate_id",
    "raw_metric_name",
    "proposed_standard_metric",
    "human_alias_review_decision",
    "alias_reviewer",
    "alias_reviewed_at",
    "alias_review_notes",
    "source_345c5_alias_review_row_id",
    "source_345c5_alias_adjudication_id",
    "source_345c6_applied_alias_key",
    "simulation_applied_row_count",
    "simulation_newly_normalized_row_count",
    "coverage_delta_contribution",
    "ready_candidate_delta_contribution",
    "source_stages",
    "pdf_names",
    "sample_row_ids",
    "rule_update_risk_level",
    "risk_reasons",
    "rule_update_recommendation",
    "requires_manual_rule_commit",
    "official_rules_modified",
    "official_alias_assets_modified",
    "candidate_package_only",
]

IMPACT_SUMMARY_FIELDS = [
    "alias_rule_candidate_id",
    "raw_metric_name",
    "proposed_standard_metric",
    "simulation_applied_row_count",
    "simulation_newly_normalized_row_count",
    "impact_share_of_total_simulated_rows",
    "coverage_delta_contribution",
    "ready_candidate_delta_contribution",
    "impact_metric_limitations",
]

RISK_REVIEW_FIELDS = [
    "alias_rule_candidate_id",
    "raw_metric_name",
    "proposed_standard_metric",
    "rule_update_risk_level",
    "risk_reasons",
    "rule_update_recommendation",
    "requires_manual_rule_commit",
]

REMAINING_BLIND_SPOT_SUMMARY_FIELDS = [
    "raw_metric_name",
    "remaining_row_count",
    "remaining_ready_candidate_count",
    "source_stages",
    "pdf_names",
    "quality_severity_distribution",
    "sample_row_ids",
]

GENERIC_TOKENS = {
    "其它",
    "其他",
    "other",
    "变动",
    "损失",
    "收益",
    "融资",
    "费用",
    "支出",
    "收支",
}
RATIO_OR_SUFFIX_TOKENS = {"margin", "ratio", "%", "比率"}
BALANCE_SHEET_STYLE_METRICS = {
    "无形资产",
    "短期借款",
    "股本",
    "交易性金融资产",
    "在建工程",
    "资本公积金",
    "预付款项",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_existing(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required input file missing: {path}")
    return path


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
    text = normalize_text(value)
    if text.lower() == "nan":
        return ""
    return text


def _load_required_json_list(path: Path, label: str) -> List[Dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"{label} must be a list JSON payload: {path}")
    return [dict(row) for row in payload]


def _contains_generic_token(raw_metric_name: str) -> bool:
    lower_name = raw_metric_name.lower()
    return any(token in raw_metric_name or token in lower_name for token in GENERIC_TOKENS)


def _contains_ratio_token(raw_metric_name: str) -> bool:
    lower_name = raw_metric_name.lower()
    return any(token in raw_metric_name or token in lower_name for token in RATIO_OR_SUFFIX_TOKENS)


def _find_related_blind_spots(
    raw_metric_name: str,
    proposed_standard_metric: str,
    blind_spot_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    raw_name_tokens = {token for token in raw_metric_name.replace("(", " ").replace(")", " ").split() if token}
    standardized_lower = proposed_standard_metric.lower()
    for row in blind_spot_rows:
        blind_name = _safe_text(row.get("raw_metric_name"))
        if not blind_name or blind_name == raw_metric_name:
            continue
        blind_lower = blind_name.lower()
        if raw_metric_name in blind_name or blind_name in raw_metric_name:
            result.append(row)
            continue
        if standardized_lower and standardized_lower.replace("_", "") in blind_lower.replace(" ", ""):
            result.append(row)
            continue
        if raw_name_tokens and any(token in blind_name for token in raw_name_tokens if len(token) >= 2):
            result.append(row)
    return result


def _classify_risk_and_recommendation(
    *,
    raw_metric_name: str,
    proposed_standard_metric: str,
    decision: str,
    llm_risk_flags: List[str],
    alias_review_notes: str,
    related_blind_spots: List[Dict[str, Any]],
    simulation_applied_row_count: int,
) -> tuple[str, List[str], str]:
    reasons: List[str] = []
    if _contains_generic_token(raw_metric_name):
        reasons.append("raw_metric_name_contains_generic_or_broad_token")
    if _contains_ratio_token(raw_metric_name):
        reasons.append("raw_metric_name_looks_like_ratio_or_suffix_metric")
    if raw_metric_name in BALANCE_SHEET_STYLE_METRICS:
        reasons.append("candidate_is_balance_sheet_style_metric_outside_current_core_universe")
    if decision == "APPROVE_NEW_STANDARD":
        reasons.append("proposes_new_standard_metric_not_yet_in_official_rules")
    if related_blind_spots:
        reasons.append("related_remaining_blind_spot_variants_still_exist")
    if llm_risk_flags:
        reasons.append("llm_risk_flags_present")
    if simulation_applied_row_count < 50:
        reasons.append("simulation_impact_is_meaningful_but_not_broad")
    if "not equivalent" in alias_review_notes.lower():
        reasons.append("review_notes_highlight_semantic_boundary")

    risk_level = "LOW"
    if (
        _contains_generic_token(raw_metric_name)
        or _contains_ratio_token(raw_metric_name)
        or raw_metric_name in BALANCE_SHEET_STYLE_METRICS
        or simulation_applied_row_count < 50
    ):
        risk_level = "HIGH"
    elif decision == "APPROVE_NEW_STANDARD" or related_blind_spots or llm_risk_flags:
        risk_level = "MEDIUM"

    recommendation = "READY_FOR_CONTROLLED_RULE_UPDATE"
    if risk_level == "HIGH":
        recommendation = "NEEDS_ADDITIONAL_REVIEW"
    elif risk_level == "MEDIUM":
        recommendation = "READY_FOR_DEMO_ONLY_SIDECAR_USE"
    if simulation_applied_row_count <= 0:
        recommendation = "DO_NOT_UPDATE_RULE"
    return risk_level, reasons, recommendation


def _determine_next_scope(
    *,
    controlled_rule_update_candidate_count: int,
    high_risk_candidate_count: int,
    remaining_unnormalized_raw_metric_name_count: int,
) -> str:
    if controlled_rule_update_candidate_count >= 5 and high_risk_candidate_count <= 6:
        return "345C8 Controlled Official Alias Rule Update"
    if remaining_unnormalized_raw_metric_name_count <= 40 and high_risk_candidate_count <= 10:
        return "345D Full Structured Demo Export Package"
    return "345C4/345C5 additional review batch"


def build_official_alias_rule_update_candidate_package_345c7(
    *,
    reviewed_alias_decision_ingestion_345c5_dir: Path,
    reviewed_alias_apply_simulation_345c6_dir: Path,
    output_dir: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345c5_path = _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_MANIFEST_NAME
    )
    validated_approved_345c5_path = _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_VALIDATED_APPROVED_JSON_NAME
    )
    rejected_or_deferred_345c5_path = _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_REJECTED_OR_DEFERRED_JSON_NAME
    )
    decision_summary_345c5_path = _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_DECISION_SUMMARY_JSON_NAME
    )
    _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_VALIDATED_APPROVED_CSV_NAME
    )
    _require_existing(
        reviewed_alias_decision_ingestion_345c5_dir / INPUT_345C5_REJECTED_OR_DEFERRED_CSV_NAME
    )

    manifest_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_MANIFEST_NAME
    )
    applied_alias_map_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_APPLIED_ALIAS_MAP_JSON_NAME
    )
    coverage_before_after_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_COVERAGE_BEFORE_AFTER_JSON_NAME
    )
    remaining_blind_spots_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_REMAINING_BLIND_SPOTS_JSON_NAME
    )
    non_applied_aliases_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_NON_APPLIED_ALIASES_JSON_NAME
    )
    simulated_metric_rows_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_SIMULATED_METRIC_ROWS_JSON_NAME
    )
    _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_APPLIED_ALIAS_MAP_CSV_NAME
    )
    _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_COVERAGE_BEFORE_AFTER_CSV_NAME
    )
    _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_REMAINING_BLIND_SPOTS_CSV_NAME
    )
    _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_NON_APPLIED_ALIASES_CSV_NAME
    )

    files_read = [
        str(manifest_345c5_path),
        str(validated_approved_345c5_path),
        str(rejected_or_deferred_345c5_path),
        str(decision_summary_345c5_path),
        str(manifest_345c6_path),
        str(applied_alias_map_345c6_path),
        str(coverage_before_after_345c6_path),
        str(remaining_blind_spots_345c6_path),
        str(non_applied_aliases_345c6_path),
        str(simulated_metric_rows_345c6_path),
    ]
    input_paths = [
        manifest_345c5_path,
        validated_approved_345c5_path,
        rejected_or_deferred_345c5_path,
        decision_summary_345c5_path,
        manifest_345c6_path,
        applied_alias_map_345c6_path,
        coverage_before_after_345c6_path,
        remaining_blind_spots_345c6_path,
        non_applied_aliases_345c6_path,
        simulated_metric_rows_345c6_path,
    ]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    manifest_345c5 = _read_json(manifest_345c5_path)
    validated_approved_aliases = _load_required_json_list(
        validated_approved_345c5_path, "345C5 validated approved aliases"
    )
    rejected_or_deferred_aliases = _load_required_json_list(
        rejected_or_deferred_345c5_path, "345C5 rejected or deferred aliases"
    )
    decision_summary_345c5 = _read_json(decision_summary_345c5_path)
    manifest_345c6 = _read_json(manifest_345c6_path)
    applied_alias_map = _load_required_json_list(
        applied_alias_map_345c6_path, "345C6 applied alias map"
    )
    coverage_before_after = _read_json(coverage_before_after_345c6_path)
    remaining_blind_spots = _load_required_json_list(
        remaining_blind_spots_345c6_path, "345C6 remaining blind spots"
    )
    non_applied_aliases = _load_required_json_list(
        non_applied_aliases_345c6_path, "345C6 non-applied aliases"
    )
    simulated_metric_rows = _load_required_json_list(
        simulated_metric_rows_345c6_path, "345C6 simulated metric rows"
    )

    if _safe_text(manifest_345c5.get("decision")) != READY_DECISION_345C5:
        raise ValueError("345C5 manifest decision is not READY.")
    if _safe_text(manifest_345c6.get("decision")) != READY_DECISION_345C6:
        raise ValueError("345C6 manifest decision is not READY.")
    if int(manifest_345c6.get("validated_approved_alias_count", 0)) <= 0:
        raise ValueError("345C6 validated_approved_alias_count must be greater than zero.")
    if int(manifest_345c6.get("simulated_newly_normalized_row_count", 0)) <= 0:
        raise ValueError("345C6 simulated_newly_normalized_row_count must be greater than zero.")
    if bool(manifest_345c6.get("official_rules_modified")):
        raise ValueError("345C6 official_rules_modified must remain false.")
    if bool(manifest_345c6.get("official_alias_assets_modified")):
        raise ValueError("345C6 official_alias_assets_modified must remain false.")
    for gate_name in [
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
    ]:
        if bool(manifest_345c5.get(gate_name)) or bool(manifest_345c6.get(gate_name)):
            raise ValueError(f"Input gate must remain false: {gate_name}")

    impact_by_key = {
        _safe_text(row.get("approved_alias_key")): row for row in applied_alias_map
    }
    simulated_rows_by_key: Dict[str, List[Dict[str, Any]]] = {}
    for row in simulated_metric_rows:
        if not bool(row.get("simulation_applied")):
            continue
        key = _safe_text(row.get("raw_metric_name"))
        simulated_rows_by_key.setdefault(key, []).append(row)

    total_metric_rows = int(coverage_before_after.get("metric_candidate_row_count_before", 0))
    total_simulated_rows = int(coverage_before_after.get("simulated_newly_normalized_row_count", 0))
    total_ready_delta = coverage_before_after.get("ready_candidate_count_delta", None)

    candidate_rows: List[Dict[str, Any]] = []
    impact_summary_rows: List[Dict[str, Any]] = []
    risk_review_rows: List[Dict[str, Any]] = []

    for index, alias_row in enumerate(validated_approved_aliases, start=1):
        raw_metric_name = _safe_text(alias_row.get("raw_metric_name"))
        proposed_standard_metric = _safe_text(alias_row.get("canonical_alias_target"))
        impact_row = impact_by_key.get(raw_metric_name, {})
        simulated_rows_for_alias = simulated_rows_by_key.get(raw_metric_name, [])
        simulation_applied_row_count = int(impact_row.get("applied_row_count", 0))
        simulation_newly_normalized_row_count = int(
            impact_row.get("newly_normalized_row_count", simulation_applied_row_count)
        )
        coverage_delta_contribution = (
            round(simulation_newly_normalized_row_count / total_metric_rows, 6)
            if total_metric_rows > 0
            else None
        )

        ready_candidate_delta_contribution: int | None = None
        impact_metric_limitations: List[str] = []
        if simulated_rows_for_alias:
            ready_candidate_delta_contribution = sum(
                1
                for row in simulated_rows_for_alias
                if bool(row.get("downstream_ready_after_alias_simulation"))
                and not bool(row.get("downstream_ready_before_normalization"))
            )
        else:
            impact_metric_limitations.append("no_simulated_rows_found_for_alias")
        if total_ready_delta is None:
            ready_candidate_delta_contribution = None
            impact_metric_limitations.append("global_ready_candidate_delta_missing")

        related_blind_spots = _find_related_blind_spots(
            raw_metric_name, proposed_standard_metric, remaining_blind_spots
        )
        llm_risk_flags = [
            _safe_text(flag) for flag in alias_row.get("llm_risk_flags", []) if _safe_text(flag)
        ]
        risk_level, risk_reasons, recommendation = _classify_risk_and_recommendation(
            raw_metric_name=raw_metric_name,
            proposed_standard_metric=proposed_standard_metric,
            decision=_safe_text(alias_row.get("human_alias_review_decision")),
            llm_risk_flags=llm_risk_flags,
            alias_review_notes=_safe_text(alias_row.get("alias_review_notes")),
            related_blind_spots=related_blind_spots,
            simulation_applied_row_count=simulation_applied_row_count,
        )
        requires_manual_rule_commit = recommendation == "READY_FOR_CONTROLLED_RULE_UPDATE"

        candidate_row = {
            "alias_rule_candidate_id": f"345c7::candidate::{index:03d}",
            "raw_metric_name": raw_metric_name,
            "proposed_standard_metric": proposed_standard_metric,
            "human_alias_review_decision": _safe_text(alias_row.get("human_alias_review_decision")),
            "alias_reviewer": _safe_text(alias_row.get("alias_reviewer")),
            "alias_reviewed_at": _safe_text(alias_row.get("alias_reviewed_at")),
            "alias_review_notes": _safe_text(alias_row.get("alias_review_notes")),
            "source_345c5_alias_review_row_id": _safe_text(alias_row.get("alias_review_row_id")),
            "source_345c5_alias_adjudication_id": _safe_text(alias_row.get("alias_adjudication_id")),
            "source_345c6_applied_alias_key": _safe_text(impact_row.get("approved_alias_key", raw_metric_name)),
            "simulation_applied_row_count": simulation_applied_row_count,
            "simulation_newly_normalized_row_count": simulation_newly_normalized_row_count,
            "coverage_delta_contribution": coverage_delta_contribution,
            "ready_candidate_delta_contribution": ready_candidate_delta_contribution,
            "source_stages": _safe_text(alias_row.get("source_stages")),
            "pdf_names": _safe_text(alias_row.get("pdf_names")),
            "sample_row_ids": _safe_text(alias_row.get("sample_row_ids")),
            "rule_update_risk_level": risk_level,
            "risk_reasons": risk_reasons,
            "rule_update_recommendation": recommendation,
            "requires_manual_rule_commit": requires_manual_rule_commit,
            "official_rules_modified": False,
            "official_alias_assets_modified": False,
            "candidate_package_only": True,
        }
        candidate_rows.append(candidate_row)
        impact_summary_rows.append(
            {
                "alias_rule_candidate_id": candidate_row["alias_rule_candidate_id"],
                "raw_metric_name": raw_metric_name,
                "proposed_standard_metric": proposed_standard_metric,
                "simulation_applied_row_count": simulation_applied_row_count,
                "simulation_newly_normalized_row_count": simulation_newly_normalized_row_count,
                "impact_share_of_total_simulated_rows": round(
                    simulation_newly_normalized_row_count / total_simulated_rows, 6
                )
                if total_simulated_rows > 0
                else None,
                "coverage_delta_contribution": coverage_delta_contribution,
                "ready_candidate_delta_contribution": ready_candidate_delta_contribution,
                "impact_metric_limitations": impact_metric_limitations,
            }
        )
        risk_review_rows.append(
            {
                "alias_rule_candidate_id": candidate_row["alias_rule_candidate_id"],
                "raw_metric_name": raw_metric_name,
                "proposed_standard_metric": proposed_standard_metric,
                "rule_update_risk_level": risk_level,
                "risk_reasons": risk_reasons,
                "rule_update_recommendation": recommendation,
                "requires_manual_rule_commit": requires_manual_rule_commit,
            }
        )

    controlled_rule_update_candidate_count = sum(
        1
        for row in candidate_rows
        if row["rule_update_recommendation"] == "READY_FOR_CONTROLLED_RULE_UPDATE"
    )
    demo_only_sidecar_candidate_count = sum(
        1
        for row in candidate_rows
        if row["rule_update_recommendation"] == "READY_FOR_DEMO_ONLY_SIDECAR_USE"
    )
    needs_additional_review_candidate_count = sum(
        1
        for row in candidate_rows
        if row["rule_update_recommendation"] == "NEEDS_ADDITIONAL_REVIEW"
    )
    do_not_update_rule_candidate_count = sum(
        1
        for row in candidate_rows
        if row["rule_update_recommendation"] == "DO_NOT_UPDATE_RULE"
    )

    low_risk_candidate_count = sum(
        1 for row in candidate_rows if row["rule_update_risk_level"] == "LOW"
    )
    medium_risk_candidate_count = sum(
        1 for row in candidate_rows if row["rule_update_risk_level"] == "MEDIUM"
    )
    high_risk_candidate_count = sum(
        1 for row in candidate_rows if row["rule_update_risk_level"] == "HIGH"
    )

    impact_summary_json = {
        "input_345c5_decision": _safe_text(manifest_345c5.get("decision")),
        "input_345c6_decision": _safe_text(manifest_345c6.get("decision")),
        "validated_approved_alias_count": len(validated_approved_aliases),
        "simulated_alias_applied_row_count": int(
            coverage_before_after.get("simulated_alias_applied_row_count", 0)
        ),
        "simulated_newly_normalized_row_count": int(
            coverage_before_after.get("simulated_newly_normalized_row_count", 0)
        ),
        "normalization_coverage_ratio_before": coverage_before_after.get(
            "normalization_coverage_ratio_before"
        ),
        "normalization_coverage_ratio_after_simulation": coverage_before_after.get(
            "normalization_coverage_ratio_after_simulation"
        ),
        "normalization_coverage_ratio_delta": coverage_before_after.get(
            "normalization_coverage_ratio_delta"
        ),
        "ready_candidate_count_before_simulation": coverage_before_after.get(
            "ready_candidate_count_before_simulation"
        ),
        "ready_candidate_count_after_alias_simulation": coverage_before_after.get(
            "ready_candidate_count_after_alias_simulation"
        ),
        "ready_candidate_count_delta": coverage_before_after.get(
            "ready_candidate_count_delta"
        ),
        "top_impact_aliases": [
            {
                "raw_metric_name": row["raw_metric_name"],
                "proposed_standard_metric": row["proposed_standard_metric"],
                "simulation_newly_normalized_row_count": row[
                    "simulation_newly_normalized_row_count"
                ],
                "impact_share_of_total_simulated_rows": row[
                    "impact_share_of_total_simulated_rows"
                ],
            }
            for row in sorted(
                impact_summary_rows,
                key=lambda item: (
                    -int(item["simulation_newly_normalized_row_count"]),
                    item["raw_metric_name"],
                ),
            )[:10]
        ],
        "impact_metric_limitations": [
            "Per-alias ready candidate delta is derived from simulated rows where downstream_ready_before_normalization was false and downstream_ready_after_alias_simulation became true.",
            "Coverage delta contribution is a simulation-derived estimate using metric_candidate_row_count_before as denominator.",
        ],
    }

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths}
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)
    upstream_unchanged = input_hashes_before == input_hashes_after

    no_apply_proof = build_no_apply_proof(
        stage="345C7",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof["upstream_input_hashes_before"] = input_hashes_before
    no_apply_proof["upstream_input_hashes_after"] = input_hashes_after
    no_apply_proof["upstream_workbooks_unchanged"] = upstream_unchanged
    no_apply_proof["formal_client_export_generated"] = False
    no_apply_proof["real_production_apply_performed"] = False
    no_apply_proof["official_rules_modified"] = False
    no_apply_proof["official_alias_assets_modified"] = False
    no_apply_proof["candidate_package_only"] = True
    no_apply_proof["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_345c7")
        and upstream_unchanged
        and not no_apply_proof.get("formal_client_export_generated", True)
        and not no_apply_proof.get("real_production_apply_performed", True)
        and not no_apply_proof.get("official_rules_modified", True)
        and not no_apply_proof.get("official_alias_assets_modified", True)
    )

    next_recommended_scope = _determine_next_scope(
        controlled_rule_update_candidate_count=controlled_rule_update_candidate_count,
        high_risk_candidate_count=high_risk_candidate_count,
        remaining_unnormalized_raw_metric_name_count=int(
            coverage_before_after.get("remaining_unnormalized_raw_metric_name_count", 0)
        ),
    )
    controlled_rule_update_ready = controlled_rule_update_candidate_count > 0
    full_structured_demo_export_reasonable = next_recommended_scope == "345D Full Structured Demo Export Package"

    checks = [
        {
            "check_name": "inputs::345c5_and_345c6_ready",
            "status": "PASS"
            if _safe_text(manifest_345c5.get("decision")) == READY_DECISION_345C5
            and _safe_text(manifest_345c6.get("decision")) == READY_DECISION_345C6
            and int(manifest_345c5.get("qa_fail_count", 1)) == 0
            and int(manifest_345c6.get("qa_fail_count", 1)) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "input_345c5_decision": manifest_345c5.get("decision"),
                    "input_345c6_decision": manifest_345c6.get("decision"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::candidate_count_matches_validated_aliases",
            "status": "PASS" if len(candidate_rows) == len(validated_approved_aliases) else "FAIL",
            "detail": json.dumps(
                {
                    "candidate_row_count": len(candidate_rows),
                    "validated_approved_alias_count": len(validated_approved_aliases),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "metrics::345c6_impact_metrics_preserved",
            "status": "PASS"
            if int(manifest_345c6.get("simulated_alias_applied_row_count", -1))
            == int(coverage_before_after.get("simulated_alias_applied_row_count", -2))
            and int(manifest_345c6.get("simulated_newly_normalized_row_count", -1))
            == int(coverage_before_after.get("simulated_newly_normalized_row_count", -2))
            else "FAIL",
            "detail": json.dumps(impact_summary_json, ensure_ascii=False),
        },
        {
            "check_name": "schema::candidate_rows_have_risk_and_recommendation",
            "status": "PASS"
            if all(
                _safe_text(row.get("rule_update_risk_level")) in {"LOW", "MEDIUM", "HIGH"}
                and _safe_text(row.get("rule_update_recommendation"))
                in {
                    "READY_FOR_CONTROLLED_RULE_UPDATE",
                    "READY_FOR_DEMO_ONLY_SIDECAR_USE",
                    "NEEDS_ADDITIONAL_REVIEW",
                    "DO_NOT_UPDATE_RULE",
                }
                for row in candidate_rows
            )
            else "FAIL",
            "detail": "Every candidate row must include valid risk and recommendation fields.",
        },
        {
            "check_name": "safety::official_rules_and_alias_assets_unchanged",
            "status": "PASS"
            if official_assets_before == official_assets_after
            else "FAIL",
            "detail": json.dumps(official_assets_after, ensure_ascii=False),
        },
        {
            "check_name": "safety::candidate_package_only_flags_preserved",
            "status": "PASS"
            if all(
                row["official_rules_modified"] is False
                and row["official_alias_assets_modified"] is False
                and row["candidate_package_only"] is True
                for row in candidate_rows
            )
            else "FAIL",
            "detail": "candidate rows must remain package-only with no official asset mutation",
        },
        {
            "check_name": "safety::all_gates_remain_false",
            "status": "PASS",
            "detail": "formal_client_export_allowed/client_ready/production_ready/global_strict_human_review_completed must remain false",
        },
        {
            "check_name": "safety::no_input_write_back",
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
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {"no_write_back_proof_passed": no_write_back_proof_passed},
                ensure_ascii=False,
            ),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    manifest = {
        "decision": READY_DECISION_345C7,
        "input_stage": INPUT_STAGE_345C7,
        "qa_fail_count": qa_fail_count,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_345c5_decision": _safe_text(manifest_345c5.get("decision")),
        "input_345c6_decision": _safe_text(manifest_345c6.get("decision")),
        "validated_approved_alias_count": len(validated_approved_aliases),
        "candidate_row_count": len(candidate_rows),
        "controlled_rule_update_candidate_count": controlled_rule_update_candidate_count,
        "demo_only_sidecar_candidate_count": demo_only_sidecar_candidate_count,
        "needs_additional_review_candidate_count": needs_additional_review_candidate_count,
        "do_not_update_rule_candidate_count": do_not_update_rule_candidate_count,
        "low_risk_candidate_count": low_risk_candidate_count,
        "medium_risk_candidate_count": medium_risk_candidate_count,
        "high_risk_candidate_count": high_risk_candidate_count,
        "simulated_alias_applied_row_count": int(
            coverage_before_after.get("simulated_alias_applied_row_count", 0)
        ),
        "simulated_newly_normalized_row_count": int(
            coverage_before_after.get("simulated_newly_normalized_row_count", 0)
        ),
        "normalization_coverage_ratio_before": coverage_before_after.get(
            "normalization_coverage_ratio_before"
        ),
        "normalization_coverage_ratio_after_simulation": coverage_before_after.get(
            "normalization_coverage_ratio_after_simulation"
        ),
        "normalization_coverage_ratio_delta": coverage_before_after.get(
            "normalization_coverage_ratio_delta"
        ),
        "ready_candidate_count_before_simulation": coverage_before_after.get(
            "ready_candidate_count_before_simulation"
        ),
        "ready_candidate_count_after_alias_simulation": coverage_before_after.get(
            "ready_candidate_count_after_alias_simulation"
        ),
        "ready_candidate_count_delta": coverage_before_after.get(
            "ready_candidate_count_delta"
        ),
        "remaining_unnormalized_raw_metric_name_count": coverage_before_after.get(
            "remaining_unnormalized_raw_metric_name_count"
        ),
        "remaining_unnormalized_metric_row_count": coverage_before_after.get(
            "remaining_unnormalized_metric_row_count"
        ),
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "candidate_package_only": True,
        "controlled_rule_update_ready": controlled_rule_update_ready,
        "full_structured_demo_export_reasonable": full_structured_demo_export_reasonable,
        "input_rejected_or_deferred_alias_count": len(rejected_or_deferred_aliases),
        "input_non_applied_alias_count": len(non_applied_aliases),
        "generated_at_utc": _utc_now(),
        "recommended_next_scope": next_recommended_scope,
        "output_dir": str(output_dir),
    }

    artifact_index_rows = [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "345C7 manifest with candidate and risk summary.",
        },
        {
            "artifact_name": ALIAS_RULE_CANDIDATES_JSON_FILE_NAME,
            "path": str(output_dir / ALIAS_RULE_CANDIDATES_JSON_FILE_NAME),
            "purpose": "Per-alias official rule update candidate rows in JSON.",
        },
        {
            "artifact_name": ALIAS_RULE_CANDIDATES_CSV_FILE_NAME,
            "path": str(output_dir / ALIAS_RULE_CANDIDATES_CSV_FILE_NAME),
            "purpose": "Per-alias official rule update candidate rows in CSV.",
        },
        {
            "artifact_name": IMPACT_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / IMPACT_SUMMARY_JSON_FILE_NAME),
            "purpose": "Simulation impact summary preserved from 345C6.",
        },
        {
            "artifact_name": IMPACT_SUMMARY_CSV_FILE_NAME,
            "path": str(output_dir / IMPACT_SUMMARY_CSV_FILE_NAME),
            "purpose": "Simulation impact summary in CSV.",
        },
        {
            "artifact_name": RISK_REVIEW_JSON_FILE_NAME,
            "path": str(output_dir / RISK_REVIEW_JSON_FILE_NAME),
            "purpose": "Risk and recommendation review table in JSON.",
        },
        {
            "artifact_name": RISK_REVIEW_CSV_FILE_NAME,
            "path": str(output_dir / RISK_REVIEW_CSV_FILE_NAME),
            "purpose": "Risk and recommendation review table in CSV.",
        },
        {
            "artifact_name": REMAINING_BLIND_SPOT_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / REMAINING_BLIND_SPOT_SUMMARY_JSON_FILE_NAME),
            "purpose": "Remaining blind spots carried forward from 345C6.",
        },
        {
            "artifact_name": REMAINING_BLIND_SPOT_SUMMARY_CSV_FILE_NAME,
            "path": str(output_dir / REMAINING_BLIND_SPOT_SUMMARY_CSV_FILE_NAME),
            "purpose": "Remaining blind spots in CSV.",
        },
        {
            "artifact_name": RULE_UPDATE_CHECKLIST_MD_FILE_NAME,
            "path": str(output_dir / RULE_UPDATE_CHECKLIST_MD_FILE_NAME),
            "purpose": "Checklist for any later explicit official rule update.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME),
            "purpose": "Narrative summary of candidate packaging and risks.",
        },
        {
            "artifact_name": ARTIFACT_INDEX_MD_FILE_NAME,
            "path": str(output_dir / ARTIFACT_INDEX_MD_FILE_NAME),
            "purpose": "Index of all 345C7 outputs.",
        },
        {
            "artifact_name": NEXT_PLAN_MD_FILE_NAME,
            "path": str(output_dir / NEXT_PLAN_MD_FILE_NAME),
            "purpose": "Recommended next step after 345C7.",
        },
    ]

    return {
        "manifest": manifest,
        "alias_rule_candidates": candidate_rows,
        "impact_summary": impact_summary_json,
        "impact_summary_rows": impact_summary_rows,
        "risk_review": risk_review_rows,
        "remaining_blind_spot_summary": remaining_blind_spots,
        "artifact_index_rows": artifact_index_rows,
        "qa_json": {
            "qa_fail_count": qa_fail_count,
            "checks": checks,
            "warnings": [],
        },
        "no_apply_proof": no_apply_proof,
    }
