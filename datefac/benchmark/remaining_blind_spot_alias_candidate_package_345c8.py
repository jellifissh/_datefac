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


READY_DECISION_345C6 = "REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY"
READY_DECISION_345C7 = "OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE_345C7_READY"
READY_DECISION_345C8 = "REMAINING_BLIND_SPOT_ALIAS_CANDIDATE_PACKAGE_345C8_READY"
INPUT_STAGE_345C8 = "POST_345C7_REMAINING_BLIND_SPOT_CANDIDATE_SELECTION"

DEFAULT_REVIEWED_ALIAS_APPLY_SIMULATION_345C6_DIR = Path(
    r"D:\_datefac\output\reviewed_alias_apply_simulation_345c6"
)
DEFAULT_OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE_345C7_DIR = Path(
    r"D:\_datefac\output\official_alias_rule_update_candidate_package_345c7"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\remaining_blind_spot_alias_candidate_package_345c8"
)
DEFAULT_MAX_BLIND_SPOT_CANDIDATES = 30
DEFAULT_MIN_ROW_IMPACT = 10

MANIFEST_FILE_NAME = "remaining_blind_spot_alias_candidate_package_345c8_manifest.json"
SELECTED_CANDIDATES_JSON_FILE_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_selected_candidates.json"
)
SELECTED_CANDIDATES_CSV_FILE_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_selected_candidates.csv"
)
UNSELECTED_BLIND_SPOTS_JSON_FILE_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_unselected_blind_spots.json"
)
UNSELECTED_BLIND_SPOTS_CSV_FILE_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_unselected_blind_spots.csv"
)
CANDIDATE_IMPACT_SUMMARY_JSON_FILE_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_candidate_impact_summary.json"
)
CANDIDATE_IMPACT_SUMMARY_CSV_FILE_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_candidate_impact_summary.csv"
)
REVIEW_BATCH_RECOMMENDATION_JSON_FILE_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_review_batch_recommendation.json"
)
STOP_OR_CONTINUE_DECISION_JSON_FILE_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_stop_or_continue_decision.json"
)
EXECUTIVE_SUMMARY_MD_FILE_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_executive_summary.md"
)
ARTIFACT_INDEX_MD_FILE_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_artifact_index.md"
)
NEXT_PLAN_MD_FILE_NAME = "remaining_blind_spot_alias_candidate_package_345c8_next_plan.md"

INPUT_345C6_MANIFEST_NAME = "reviewed_alias_apply_simulation_345c6_manifest.json"
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
INPUT_345C6_COVERAGE_BEFORE_AFTER_JSON_NAME = (
    "reviewed_alias_apply_simulation_345c6_coverage_before_after.json"
)
INPUT_345C6_COVERAGE_BEFORE_AFTER_CSV_NAME = (
    "reviewed_alias_apply_simulation_345c6_coverage_before_after.csv"
)
INPUT_345C6_SIMULATED_METRIC_ROWS_JSON_NAME = (
    "reviewed_alias_apply_simulation_345c6_simulated_metric_rows.json"
)

INPUT_345C7_MANIFEST_NAME = "official_alias_rule_update_candidate_package_345c7_manifest.json"
INPUT_345C7_REMAINING_BLIND_SPOT_SUMMARY_JSON_NAME = (
    "official_alias_rule_update_candidate_package_345c7_remaining_blind_spot_summary.json"
)
INPUT_345C7_REMAINING_BLIND_SPOT_SUMMARY_CSV_NAME = (
    "official_alias_rule_update_candidate_package_345c7_remaining_blind_spot_summary.csv"
)
INPUT_345C7_RISK_REVIEW_JSON_NAME = (
    "official_alias_rule_update_candidate_package_345c7_risk_review.json"
)
INPUT_345C7_RISK_REVIEW_CSV_NAME = (
    "official_alias_rule_update_candidate_package_345c7_risk_review.csv"
)
INPUT_345C7_EXECUTIVE_SUMMARY_MD_NAME = (
    "official_alias_rule_update_candidate_package_345c7_executive_summary.md"
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

SELECTED_CANDIDATE_FIELDS = [
    "blind_spot_candidate_id",
    "raw_metric_name",
    "remaining_row_count",
    "remaining_raw_metric_rank",
    "source_stages",
    "pdf_names",
    "source_artifacts",
    "sample_row_ids",
    "sample_evidence_excerpt",
    "candidate_priority",
    "review_recommendation",
    "candidate_reason",
    "risk_level",
    "risk_reasons",
    "estimated_max_newly_normalized_rows",
    "estimated_coverage_delta_if_resolved",
    "estimated_ready_candidate_delta_if_resolved",
    "needs_llm_adjudication",
    "needs_human_review",
    "suggested_next_review_action",
    "candidate_package_only",
    "official_rules_modified",
    "official_alias_assets_modified",
]

UNSELECTED_FIELDS = [
    "raw_metric_name",
    "remaining_row_count",
    "remaining_raw_metric_rank",
    "review_recommendation",
    "candidate_reason",
    "risk_level",
    "risk_reasons",
]

CANDIDATE_IMPACT_SUMMARY_FIELDS = [
    "blind_spot_candidate_id",
    "raw_metric_name",
    "estimated_max_newly_normalized_rows",
    "estimated_coverage_delta_if_resolved",
    "estimated_ready_candidate_delta_if_resolved",
    "candidate_priority",
    "review_recommendation",
]

GENERIC_EXCLUDE_NAMES = {
    "",
    "现",
    "变化",
}
GENERIC_TOKENS = {
    "其他",
    "其它",
    "成本",
    "变动",
    "项目",
    "其中",
    "单位",
}
CONTEXT_ONLY_TOKENS = {
    "同比",
    "yoy",
    "margin",
    "ratio",
    "%",
    "增速",
    "周转率",
}
CONCRETE_METRIC_TOKENS = {
    "利润",
    "费用",
    "收益",
    "资产",
    "负债",
    "现金流",
    "借款",
    "股本",
    "税",
    "资本",
    "ebitda",
    "roe",
    "roic",
    "市值",
}
HIGH_VALUE_STAGE_TOKENS = {"HUMAN_REVIEW_APPLIED", "TRUSTED_CELL", "REVIEW_REQUIRED"}


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


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def _rank_score(row: Dict[str, Any], concrete_bonus: int, generic_penalty: int, evidence_bonus: int) -> int:
    source_stage_count = len(
        [part for part in _safe_text(row.get("source_stages")).split("|") if part]
    )
    pdf_count = len([part for part in _safe_text(row.get("pdf_names")).split("|") if part])
    return (
        int(row.get("remaining_row_count", 0)) * 10
        + source_stage_count * 4
        + pdf_count * 2
        + concrete_bonus
        + evidence_bonus
        - generic_penalty
    )


def _sample_evidence_excerpt(row: Dict[str, Any], sample_source_rows: List[Dict[str, Any]]) -> str:
    if sample_source_rows:
        snippets = []
        for source_row in sample_source_rows[:2]:
            snippets.append(
                "|".join(
                    filter(
                        None,
                        [
                            _safe_text(source_row.get("pdf_name")),
                            _safe_text(source_row.get("source_stage")),
                            _safe_text(source_row.get("quality_severity")),
                            _safe_text(source_row.get("quality_issues")),
                        ],
                    )
                )
            )
        return " || ".join(snippets)
    return "|".join(
        filter(
            None,
            [
                _safe_text(row.get("source_stages")),
                _safe_text(row.get("quality_severity_distribution")),
                _safe_text(row.get("pdf_names")),
            ],
        )
    )


def _select_review_recommendation(
    *,
    raw_metric_name: str,
    remaining_row_count: int,
    generic: bool,
    context_only: bool,
    concrete: bool,
) -> tuple[str, str, str, List[str]]:
    reasons: List[str] = []
    candidate_reason = "remaining_blind_spot_high_impact"
    risk_level = "MEDIUM"
    review_recommendation = "INCLUDE_IN_SECOND_REVIEW_BATCH"

    if raw_metric_name in GENERIC_EXCLUDE_NAMES or not raw_metric_name.strip():
        review_recommendation = "EXCLUDE_TOO_GENERIC"
        risk_level = "HIGH"
        reasons.append("blank_or_fragment_like_metric_name")
        candidate_reason = "generic_fragment_excluded"
        return review_recommendation, candidate_reason, risk_level, reasons

    if generic and not concrete:
        review_recommendation = "EXCLUDE_TOO_GENERIC"
        risk_level = "HIGH"
        reasons.append("generic_or_ambiguous_metric_name_without_concrete_semantic_anchor")
        candidate_reason = "too_generic_without_context"
        if remaining_row_count >= 80:
            review_recommendation = "NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW"
            candidate_reason = "large_impact_but_too_generic_without_context"
        return review_recommendation, candidate_reason, risk_level, reasons

    if generic and concrete:
        review_recommendation = "NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW"
        risk_level = "HIGH"
        reasons.append("contains_other_or_generic_modifier_despite_concrete_metric_family")
        candidate_reason = "generic_modifier_requires_context_before_review"
        return review_recommendation, candidate_reason, risk_level, reasons

    if context_only:
        review_recommendation = "INCLUDE_AS_CONTEXT_ONLY"
        risk_level = "HIGH"
        reasons.append("likely_ratio_growth_or_suffix_metric_needing_context")
        candidate_reason = "needs_context_not_direct_alias_update"
        return review_recommendation, candidate_reason, risk_level, reasons

    if not concrete:
        review_recommendation = "NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW"
        risk_level = "HIGH"
        reasons.append("insufficient_concrete_financial_metric_signal")
        candidate_reason = "context_needed_before_review"
        return review_recommendation, candidate_reason, risk_level, reasons

    if remaining_row_count < 15:
        review_recommendation = "DEFER_LOW_IMPACT"
        risk_level = "MEDIUM"
        reasons.append("below_high_value_frequency_threshold")
        candidate_reason = "defer_lower_impact_candidate"
        return review_recommendation, candidate_reason, risk_level, reasons

    if remaining_row_count >= 80:
        risk_level = "MEDIUM"
        reasons.append("high_remaining_row_count_with_concrete_metric_signal")
        candidate_reason = "strong_second_batch_candidate"
    else:
        risk_level = "MEDIUM"
        reasons.append("moderate_remaining_row_count_with_concrete_metric_signal")
        candidate_reason = "reviewable_second_batch_candidate"
    return review_recommendation, candidate_reason, risk_level, reasons


def _is_problematic_generic_name(raw_metric_name: str) -> bool:
    lower_name = raw_metric_name.lower()
    if raw_metric_name in GENERIC_EXCLUDE_NAMES or not raw_metric_name.strip():
        return True
    if raw_metric_name in {"成本", "变化"}:
        return True
    return any(token in raw_metric_name or token in lower_name for token in {"其他", "其它", "项目", "单位"})


def _determine_branch_decision(
    *,
    selected_candidate_count: int,
    selected_estimated_row_impact_total: int,
    selected_estimated_coverage_delta_total: float | None,
    include_in_second_review_batch_count: int,
    include_as_context_only_count: int,
    high_risk_candidate_count: int,
) -> tuple[str, bool, str]:
    if (
        selected_candidate_count == 0
        or include_in_second_review_batch_count == 0
        or selected_estimated_row_impact_total < 300
        or (selected_estimated_coverage_delta_total is not None and selected_estimated_coverage_delta_total < 0.02)
    ):
        return (
            "STOP_ALIAS_BRANCH_AND_RETURN_TO_345D",
            True,
            "345D Full Structured Demo Export Package",
        )
    if high_risk_candidate_count > include_in_second_review_batch_count:
        return (
            "CONTINUE_ONLY_IF_HUMAN_REVIEW_CAPACITY_EXISTS",
            False,
            "345D with alias-risk caveat",
        )
    if include_in_second_review_batch_count >= 10 and include_as_context_only_count <= 10:
        return (
            "CONTINUE_WITH_SECOND_REVIEW_BATCH",
            False,
            "345C9 Remaining Blind Spot Human Review Package",
        )
    return (
        "CONTINUE_ONLY_IF_HUMAN_REVIEW_CAPACITY_EXISTS",
        False,
        "345D with alias-risk caveat",
    )


def build_remaining_blind_spot_alias_candidate_package_345c8(
    *,
    reviewed_alias_apply_simulation_345c6_dir: Path,
    official_alias_rule_update_candidate_package_345c7_dir: Path,
    output_dir: Path,
    max_blind_spot_candidates: int,
    min_row_impact: int,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_MANIFEST_NAME
    )
    remaining_blind_spots_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_REMAINING_BLIND_SPOTS_JSON_NAME
    )
    non_applied_aliases_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_NON_APPLIED_ALIASES_JSON_NAME
    )
    coverage_before_after_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_COVERAGE_BEFORE_AFTER_JSON_NAME
    )
    simulated_metric_rows_345c6_path = _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_SIMULATED_METRIC_ROWS_JSON_NAME
    )
    _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_REMAINING_BLIND_SPOTS_CSV_NAME
    )
    _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_NON_APPLIED_ALIASES_CSV_NAME
    )
    _require_existing(
        reviewed_alias_apply_simulation_345c6_dir / INPUT_345C6_COVERAGE_BEFORE_AFTER_CSV_NAME
    )

    manifest_345c7_path = _require_existing(
        official_alias_rule_update_candidate_package_345c7_dir / INPUT_345C7_MANIFEST_NAME
    )
    remaining_blind_spot_summary_345c7_path = _require_existing(
        official_alias_rule_update_candidate_package_345c7_dir
        / INPUT_345C7_REMAINING_BLIND_SPOT_SUMMARY_JSON_NAME
    )
    risk_review_345c7_path = _require_existing(
        official_alias_rule_update_candidate_package_345c7_dir / INPUT_345C7_RISK_REVIEW_JSON_NAME
    )
    executive_summary_345c7_path = _require_existing(
        official_alias_rule_update_candidate_package_345c7_dir / INPUT_345C7_EXECUTIVE_SUMMARY_MD_NAME
    )
    _require_existing(
        official_alias_rule_update_candidate_package_345c7_dir
        / INPUT_345C7_REMAINING_BLIND_SPOT_SUMMARY_CSV_NAME
    )
    _require_existing(
        official_alias_rule_update_candidate_package_345c7_dir / INPUT_345C7_RISK_REVIEW_CSV_NAME
    )

    files_read = [
        str(manifest_345c6_path),
        str(remaining_blind_spots_345c6_path),
        str(non_applied_aliases_345c6_path),
        str(coverage_before_after_345c6_path),
        str(simulated_metric_rows_345c6_path),
        str(manifest_345c7_path),
        str(remaining_blind_spot_summary_345c7_path),
        str(risk_review_345c7_path),
        str(executive_summary_345c7_path),
    ]
    input_paths = [
        manifest_345c6_path,
        remaining_blind_spots_345c6_path,
        non_applied_aliases_345c6_path,
        coverage_before_after_345c6_path,
        simulated_metric_rows_345c6_path,
        manifest_345c7_path,
        remaining_blind_spot_summary_345c7_path,
        risk_review_345c7_path,
        executive_summary_345c7_path,
    ]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    manifest_345c6 = _read_json(manifest_345c6_path)
    remaining_blind_spots_345c6 = _load_required_json_list(
        remaining_blind_spots_345c6_path, "345C6 remaining blind spots"
    )
    non_applied_aliases_345c6 = _load_required_json_list(
        non_applied_aliases_345c6_path, "345C6 non-applied aliases"
    )
    coverage_before_after_345c6 = _read_json(coverage_before_after_345c6_path)
    simulated_metric_rows_345c6 = _load_required_json_list(
        simulated_metric_rows_345c6_path, "345C6 simulated metric rows"
    )
    manifest_345c7 = _read_json(manifest_345c7_path)
    remaining_blind_spot_summary_345c7 = _load_required_json_list(
        remaining_blind_spot_summary_345c7_path, "345C7 remaining blind spot summary"
    )
    risk_review_345c7 = _load_required_json_list(
        risk_review_345c7_path, "345C7 risk review"
    )
    executive_summary_345c7 = executive_summary_345c7_path.read_text(encoding="utf-8")

    if _safe_text(manifest_345c6.get("decision")) != READY_DECISION_345C6:
        raise ValueError("345C6 manifest decision is not READY.")
    if _safe_text(manifest_345c7.get("decision")) != READY_DECISION_345C7:
        raise ValueError("345C7 manifest decision is not READY.")
    if int(manifest_345c6.get("remaining_unnormalized_metric_row_count", 0)) <= 0:
        raise ValueError("345C6 remaining_unnormalized_metric_row_count must be greater than zero.")
    for gate_name in [
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
    ]:
        if bool(manifest_345c6.get(gate_name)) or bool(manifest_345c7.get(gate_name)):
            raise ValueError(f"Input gate must remain false: {gate_name}")
    if bool(manifest_345c7.get("official_rules_modified")):
        raise ValueError("345C7 official_rules_modified must remain false.")
    if bool(manifest_345c7.get("official_alias_assets_modified")):
        raise ValueError("345C7 official_alias_assets_modified must remain false.")

    source_rows_by_name: Dict[str, List[Dict[str, Any]]] = {}
    source_artifacts_by_name: Dict[str, set[str]] = {}
    ready_candidate_by_name: Dict[str, int] = {}
    for row in simulated_metric_rows_345c6:
        if _safe_text(row.get("normalization_status_after_simulation")) != "UNNORMALIZED_WITH_RAW_NAME":
            continue
        raw_metric_name = _safe_text(row.get("raw_metric_name"))
        if not raw_metric_name:
            continue
        source_rows_by_name.setdefault(raw_metric_name, []).append(row)
        source_artifacts_by_name.setdefault(raw_metric_name, set()).add(
            _safe_text(row.get("source_artifact"))
        )
        if bool(row.get("downstream_ready_after_alias_simulation")):
            ready_candidate_by_name[raw_metric_name] = ready_candidate_by_name.get(raw_metric_name, 0) + 1

    risk_review_names = {_safe_text(row.get("raw_metric_name")) for row in risk_review_345c7}
    combined_remaining_rows = remaining_blind_spot_summary_345c7 or remaining_blind_spots_345c6

    scored_rows: List[Dict[str, Any]] = []
    for row in combined_remaining_rows:
        raw_metric_name = _safe_text(row.get("raw_metric_name"))
        remaining_row_count = int(row.get("remaining_row_count", 0) or 0)
        lower_name = raw_metric_name.lower()
        generic = (
            raw_metric_name in GENERIC_EXCLUDE_NAMES
            or any(token in raw_metric_name or token in lower_name for token in GENERIC_TOKENS)
        )
        context_only = any(
            token in raw_metric_name or token in lower_name for token in CONTEXT_ONLY_TOKENS
        )
        concrete = any(
            token in raw_metric_name or token in lower_name for token in CONCRETE_METRIC_TOKENS
        )
        high_value_stage_hit = any(
            token in _safe_text(row.get("source_stages")) for token in HIGH_VALUE_STAGE_TOKENS
        )
        evidence_bonus = 5 if high_value_stage_hit else 0
        evidence_bonus += 5 if ready_candidate_by_name.get(raw_metric_name, 0) > 0 else 0
        evidence_bonus += 3 if raw_metric_name in risk_review_names else 0
        score = _rank_score(
            row,
            concrete_bonus=12 if concrete else 0,
            generic_penalty=15 if generic else 0,
            evidence_bonus=evidence_bonus,
        )
        scored = dict(row)
        scored["_generic"] = generic
        scored["_context_only"] = context_only
        scored["_concrete"] = concrete
        scored["_score"] = score
        scored_rows.append(scored)

    scored_rows.sort(
        key=lambda row: (
            -int(row.get("remaining_row_count", 0)),
            -int(row.get("_score", 0)),
            _safe_text(row.get("raw_metric_name")),
        )
    )

    total_metric_rows = int(coverage_before_after_345c6.get("metric_candidate_row_count_before", 0))
    selected_candidates: List[Dict[str, Any]] = []
    selected_names: set[str] = set()
    review_batch_rows: List[Dict[str, Any]] = []

    for rank, row in enumerate(scored_rows, start=1):
        raw_metric_name = _safe_text(row.get("raw_metric_name"))
        if raw_metric_name in selected_names:
            continue
        remaining_row_count = int(row.get("remaining_row_count", 0) or 0)
        review_recommendation, candidate_reason, risk_level, risk_reasons = _select_review_recommendation(
            raw_metric_name=raw_metric_name,
            remaining_row_count=remaining_row_count,
            generic=bool(row.get("_generic")),
            context_only=bool(row.get("_context_only")),
            concrete=bool(row.get("_concrete")),
        )

        if remaining_row_count < min_row_impact:
            if len(selected_candidates) >= max_blind_spot_candidates:
                continue
            review_recommendation = "DEFER_LOW_IMPACT"
            candidate_reason = "below_min_row_impact_threshold"
            risk_level = "MEDIUM"
            risk_reasons.append("below_configured_min_row_impact")
            if len(selected_candidates) < max_blind_spot_candidates // 2:
                candidate_reason = "included_for_batch_fill_despite_low_impact"

        should_include = review_recommendation in {
            "INCLUDE_IN_SECOND_REVIEW_BATCH",
            "INCLUDE_AS_CONTEXT_ONLY",
            "NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW",
        }
        if not should_include:
            continue
        if len(selected_candidates) >= max_blind_spot_candidates:
            continue

        sample_source_rows = source_rows_by_name.get(raw_metric_name, [])
        sample_evidence_excerpt = _sample_evidence_excerpt(row, sample_source_rows)
        estimated_ready_candidate_delta_if_resolved = ready_candidate_by_name.get(raw_metric_name, 0)
        selected_candidate = {
            "blind_spot_candidate_id": f"345c8::candidate::{len(selected_candidates)+1:03d}",
            "raw_metric_name": raw_metric_name,
            "remaining_row_count": remaining_row_count,
            "remaining_raw_metric_rank": rank,
            "source_stages": _safe_text(row.get("source_stages")),
            "pdf_names": _safe_text(row.get("pdf_names")),
            "source_artifacts": "|".join(
                sorted(
                    artifact
                    for artifact in source_artifacts_by_name.get(raw_metric_name, set())
                    if artifact
                )
            ),
            "sample_row_ids": _safe_text(row.get("sample_row_ids")),
            "sample_evidence_excerpt": sample_evidence_excerpt,
            "candidate_priority": "HIGH"
            if remaining_row_count >= 80
            else "MEDIUM"
            if remaining_row_count >= 30
            else "LOW",
            "review_recommendation": review_recommendation,
            "candidate_reason": candidate_reason,
            "risk_level": risk_level,
            "risk_reasons": risk_reasons,
            "estimated_max_newly_normalized_rows": remaining_row_count,
            "estimated_coverage_delta_if_resolved": _ratio(remaining_row_count, total_metric_rows),
            "estimated_ready_candidate_delta_if_resolved": estimated_ready_candidate_delta_if_resolved,
            "needs_llm_adjudication": False,
            "needs_human_review": True,
            "suggested_next_review_action": "bounded_alias_review"
            if review_recommendation == "INCLUDE_IN_SECOND_REVIEW_BATCH"
            else "collect_more_source_context_before_alias_review"
            if review_recommendation == "NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW"
            else "context_reference_only",
            "candidate_package_only": True,
            "official_rules_modified": False,
            "official_alias_assets_modified": False,
        }
        selected_candidates.append(selected_candidate)
        selected_names.add(raw_metric_name)
        review_batch_rows.append(
            {
                "blind_spot_candidate_id": selected_candidate["blind_spot_candidate_id"],
                "raw_metric_name": raw_metric_name,
                "estimated_max_newly_normalized_rows": remaining_row_count,
                "estimated_coverage_delta_if_resolved": selected_candidate[
                    "estimated_coverage_delta_if_resolved"
                ],
                "estimated_ready_candidate_delta_if_resolved": estimated_ready_candidate_delta_if_resolved,
                "candidate_priority": selected_candidate["candidate_priority"],
                "review_recommendation": review_recommendation,
            }
        )

    unselected_blind_spots: List[Dict[str, Any]] = []
    for rank, row in enumerate(scored_rows, start=1):
        raw_metric_name = _safe_text(row.get("raw_metric_name"))
        if raw_metric_name in selected_names:
            continue
        remaining_row_count = int(row.get("remaining_row_count", 0) or 0)
        review_recommendation, candidate_reason, risk_level, risk_reasons = _select_review_recommendation(
            raw_metric_name=raw_metric_name,
            remaining_row_count=remaining_row_count,
            generic=bool(row.get("_generic")),
            context_only=bool(row.get("_context_only")),
            concrete=bool(row.get("_concrete")),
        )
        if remaining_row_count < min_row_impact and review_recommendation == "INCLUDE_IN_SECOND_REVIEW_BATCH":
            review_recommendation = "DEFER_LOW_IMPACT"
            candidate_reason = "below_min_row_impact_threshold"
            risk_level = "MEDIUM"
            risk_reasons.append("below_configured_min_row_impact")
        unselected_blind_spots.append(
            {
                "raw_metric_name": raw_metric_name,
                "remaining_row_count": remaining_row_count,
                "remaining_raw_metric_rank": rank,
                "review_recommendation": review_recommendation,
                "candidate_reason": candidate_reason,
                "risk_level": risk_level,
                "risk_reasons": risk_reasons,
            }
        )

    selected_estimated_row_impact_total = sum(
        int(row["estimated_max_newly_normalized_rows"]) for row in selected_candidates
    )
    selected_estimated_coverage_delta_total = round(
        sum(
            float(row["estimated_coverage_delta_if_resolved"] or 0)
            for row in selected_candidates
        ),
        6,
    )
    selected_estimated_ready_candidate_delta_total = sum(
        int(row["estimated_ready_candidate_delta_if_resolved"] or 0)
        for row in selected_candidates
    )

    high_priority_candidate_count = sum(
        1 for row in selected_candidates if row["candidate_priority"] == "HIGH"
    )
    medium_priority_candidate_count = sum(
        1 for row in selected_candidates if row["candidate_priority"] == "MEDIUM"
    )
    low_priority_candidate_count = sum(
        1 for row in selected_candidates if row["candidate_priority"] == "LOW"
    )

    include_in_second_review_batch_count = sum(
        1
        for row in selected_candidates
        if row["review_recommendation"] == "INCLUDE_IN_SECOND_REVIEW_BATCH"
    )
    include_as_context_only_count = sum(
        1
        for row in selected_candidates
        if row["review_recommendation"] == "INCLUDE_AS_CONTEXT_ONLY"
    )
    defer_low_impact_count = sum(
        1
        for row in selected_candidates
        if row["review_recommendation"] == "DEFER_LOW_IMPACT"
    )
    exclude_too_generic_count = sum(
        1
        for row in unselected_blind_spots
        if row["review_recommendation"] == "EXCLUDE_TOO_GENERIC"
    )
    needs_source_context_before_review_count = sum(
        1
        for row in selected_candidates
        if row["review_recommendation"] == "NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW"
    )

    low_risk_candidate_count = sum(
        1 for row in selected_candidates if row["risk_level"] == "LOW"
    )
    medium_risk_candidate_count = sum(
        1 for row in selected_candidates if row["risk_level"] == "MEDIUM"
    )
    high_risk_candidate_count = sum(
        1 for row in selected_candidates if row["risk_level"] == "HIGH"
    )

    branch_decision, full_structured_demo_export_reasonable_after_345c8, next_plan_recommendation = _determine_branch_decision(
        selected_candidate_count=len(selected_candidates),
        selected_estimated_row_impact_total=selected_estimated_row_impact_total,
        selected_estimated_coverage_delta_total=selected_estimated_coverage_delta_total,
        include_in_second_review_batch_count=include_in_second_review_batch_count,
        include_as_context_only_count=include_as_context_only_count,
        high_risk_candidate_count=high_risk_candidate_count,
    )

    review_batch_recommendation_json = {
        "selected_candidate_count": len(selected_candidates),
        "max_blind_spot_candidates": max_blind_spot_candidates,
        "min_row_impact": min_row_impact,
        "top_selected_candidates": [
            {
                "raw_metric_name": row["raw_metric_name"],
                "remaining_row_count": row["remaining_row_count"],
                "candidate_priority": row["candidate_priority"],
                "review_recommendation": row["review_recommendation"],
            }
            for row in selected_candidates[:10]
        ],
        "include_in_second_review_batch_count": include_in_second_review_batch_count,
        "include_as_context_only_count": include_as_context_only_count,
        "needs_source_context_before_review_count": needs_source_context_before_review_count,
    }
    stop_or_continue_decision_json = {
        "alias_branch_stop_or_continue_decision": branch_decision,
        "reason": (
            "selected candidates still show meaningful batchable impact"
            if branch_decision == "CONTINUE_WITH_SECOND_REVIEW_BATCH"
            else "selected candidates are mixed and only worth continuing when human review capacity exists"
            if branch_decision == "CONTINUE_ONLY_IF_HUMAN_REVIEW_CAPACITY_EXISTS"
            else "remaining blind spots are too fragmented or too generic for another high-value alias batch"
        ),
        "full_structured_demo_export_reasonable_after_345c8": full_structured_demo_export_reasonable_after_345c8,
        "next_plan_recommendation": next_plan_recommendation,
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
        stage="345C8",
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
        no_apply_proof.get("no_official_asset_modification_during_345c8")
        and upstream_unchanged
        and not no_apply_proof.get("formal_client_export_generated", True)
        and not no_apply_proof.get("real_production_apply_performed", True)
        and not no_apply_proof.get("official_rules_modified", True)
        and not no_apply_proof.get("official_alias_assets_modified", True)
    )

    checks = [
        {
            "check_name": "inputs::345c6_and_345c7_ready",
            "status": "PASS"
            if _safe_text(manifest_345c6.get("decision")) == READY_DECISION_345C6
            and _safe_text(manifest_345c7.get("decision")) == READY_DECISION_345C7
            and int(manifest_345c6.get("qa_fail_count", 1)) == 0
            and int(manifest_345c7.get("qa_fail_count", 1)) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "input_345c6_decision": manifest_345c6.get("decision"),
                    "input_345c7_decision": manifest_345c7.get("decision"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "selection::respects_max_limit",
            "status": "PASS" if len(selected_candidates) <= max_blind_spot_candidates else "FAIL",
            "detail": json.dumps(
                {
                    "selected_candidate_count": len(selected_candidates),
                    "max_blind_spot_candidates": max_blind_spot_candidates,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "selection::below_min_impact_handled_explicitly",
            "status": "PASS"
            if all(
                int(row["remaining_row_count"]) >= min_row_impact
                or "low_impact" in _safe_text(row.get("candidate_reason"))
                for row in selected_candidates
            )
            else "FAIL",
            "detail": "selected low-impact candidates must be explicitly marked",
        },
        {
            "check_name": "selection::generic_names_not_silently_accepted",
            "status": "PASS"
            if all(
                not (
                    _is_problematic_generic_name(_safe_text(row.get("raw_metric_name")))
                    and row["review_recommendation"] == "INCLUDE_IN_SECOND_REVIEW_BATCH"
                )
                for row in selected_candidates
            )
            else "FAIL",
            "detail": "generic names must not be silently accepted as safe second-batch candidates",
        },
        {
            "check_name": "schema::selected_candidates_have_required_fields",
            "status": "PASS"
            if all(
                _safe_text(row.get("candidate_priority")) in {"HIGH", "MEDIUM", "LOW"}
                and _safe_text(row.get("review_recommendation"))
                in {
                    "INCLUDE_IN_SECOND_REVIEW_BATCH",
                    "INCLUDE_AS_CONTEXT_ONLY",
                    "DEFER_LOW_IMPACT",
                    "EXCLUDE_TOO_GENERIC",
                    "NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW",
                }
                and _safe_text(row.get("risk_level")) in {"LOW", "MEDIUM", "HIGH"}
                for row in selected_candidates
            )
            else "FAIL",
            "detail": "selected candidates must include valid priority/risk/recommendation fields",
        },
        {
            "check_name": "decision::stop_or_continue_generated",
            "status": "PASS"
            if branch_decision
            in {
                "CONTINUE_WITH_SECOND_REVIEW_BATCH",
                "STOP_ALIAS_BRANCH_AND_RETURN_TO_345D",
                "CONTINUE_ONLY_IF_HUMAN_REVIEW_CAPACITY_EXISTS",
            }
            else "FAIL",
            "detail": json.dumps(stop_or_continue_decision_json, ensure_ascii=False),
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
                row["candidate_package_only"] is True
                and row["official_rules_modified"] is False
                and row["official_alias_assets_modified"] is False
                for row in selected_candidates
            )
            else "FAIL",
            "detail": "selected candidates must remain package-only with no official asset mutation",
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
        "decision": READY_DECISION_345C8,
        "input_stage": INPUT_STAGE_345C8,
        "qa_fail_count": qa_fail_count,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_345c6_decision": _safe_text(manifest_345c6.get("decision")),
        "input_345c7_decision": _safe_text(manifest_345c7.get("decision")),
        "remaining_unnormalized_raw_metric_name_count": int(
            manifest_345c6.get("remaining_unnormalized_raw_metric_name_count", 0)
        ),
        "remaining_unnormalized_metric_row_count": int(
            manifest_345c6.get("remaining_unnormalized_metric_row_count", 0)
        ),
        "max_blind_spot_candidates": max_blind_spot_candidates,
        "min_row_impact": min_row_impact,
        "selected_candidate_count": len(selected_candidates),
        "unselected_blind_spot_count": len(unselected_blind_spots),
        "selected_estimated_row_impact_total": selected_estimated_row_impact_total,
        "selected_estimated_coverage_delta_total": selected_estimated_coverage_delta_total,
        "selected_estimated_ready_candidate_delta_total": selected_estimated_ready_candidate_delta_total,
        "high_priority_candidate_count": high_priority_candidate_count,
        "medium_priority_candidate_count": medium_priority_candidate_count,
        "low_priority_candidate_count": low_priority_candidate_count,
        "include_in_second_review_batch_count": include_in_second_review_batch_count,
        "include_as_context_only_count": include_as_context_only_count,
        "defer_low_impact_count": defer_low_impact_count,
        "exclude_too_generic_count": exclude_too_generic_count,
        "needs_source_context_before_review_count": needs_source_context_before_review_count,
        "low_risk_candidate_count": low_risk_candidate_count,
        "medium_risk_candidate_count": medium_risk_candidate_count,
        "high_risk_candidate_count": high_risk_candidate_count,
        "alias_branch_stop_or_continue_decision": branch_decision,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "candidate_package_only": True,
        "full_structured_demo_export_reasonable_after_345c8": full_structured_demo_export_reasonable_after_345c8,
        "generated_at_utc": _utc_now(),
        "output_dir": str(output_dir),
    }

    artifact_index_rows = [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "345C8 manifest with batch selection and branch decision summary.",
        },
        {
            "artifact_name": SELECTED_CANDIDATES_JSON_FILE_NAME,
            "path": str(output_dir / SELECTED_CANDIDATES_JSON_FILE_NAME),
            "purpose": "Selected Top N remaining blind spot candidates in JSON.",
        },
        {
            "artifact_name": SELECTED_CANDIDATES_CSV_FILE_NAME,
            "path": str(output_dir / SELECTED_CANDIDATES_CSV_FILE_NAME),
            "purpose": "Selected Top N remaining blind spot candidates in CSV.",
        },
        {
            "artifact_name": UNSELECTED_BLIND_SPOTS_JSON_FILE_NAME,
            "path": str(output_dir / UNSELECTED_BLIND_SPOTS_JSON_FILE_NAME),
            "purpose": "Unselected remaining blind spots with deferral/exclusion reasoning.",
        },
        {
            "artifact_name": UNSELECTED_BLIND_SPOTS_CSV_FILE_NAME,
            "path": str(output_dir / UNSELECTED_BLIND_SPOTS_CSV_FILE_NAME),
            "purpose": "Unselected remaining blind spots in CSV.",
        },
        {
            "artifact_name": CANDIDATE_IMPACT_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / CANDIDATE_IMPACT_SUMMARY_JSON_FILE_NAME),
            "purpose": "Impact summary for selected 345C8 candidates in JSON.",
        },
        {
            "artifact_name": CANDIDATE_IMPACT_SUMMARY_CSV_FILE_NAME,
            "path": str(output_dir / CANDIDATE_IMPACT_SUMMARY_CSV_FILE_NAME),
            "purpose": "Impact summary for selected 345C8 candidates in CSV.",
        },
        {
            "artifact_name": REVIEW_BATCH_RECOMMENDATION_JSON_FILE_NAME,
            "path": str(output_dir / REVIEW_BATCH_RECOMMENDATION_JSON_FILE_NAME),
            "purpose": "Recommendation summary for a possible second blind-spot review batch.",
        },
        {
            "artifact_name": STOP_OR_CONTINUE_DECISION_JSON_FILE_NAME,
            "path": str(output_dir / STOP_OR_CONTINUE_DECISION_JSON_FILE_NAME),
            "purpose": "Branch stop-or-continue decision for alias governance.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME),
            "purpose": "Narrative summary of candidate selection and branch decision.",
        },
        {
            "artifact_name": ARTIFACT_INDEX_MD_FILE_NAME,
            "path": str(output_dir / ARTIFACT_INDEX_MD_FILE_NAME),
            "purpose": "Index of all 345C8 outputs.",
        },
        {
            "artifact_name": NEXT_PLAN_MD_FILE_NAME,
            "path": str(output_dir / NEXT_PLAN_MD_FILE_NAME),
            "purpose": "Recommended next step after 345C8.",
        },
    ]

    return {
        "manifest": manifest,
        "selected_candidates": selected_candidates,
        "unselected_blind_spots": unselected_blind_spots,
        "candidate_impact_summary_rows": review_batch_rows,
        "review_batch_recommendation": review_batch_recommendation_json,
        "stop_or_continue_decision": stop_or_continue_decision_json,
        "artifact_index_rows": artifact_index_rows,
        "qa_json": {
            "qa_fail_count": qa_fail_count,
            "checks": checks,
            "warnings": [],
        },
        "no_apply_proof": no_apply_proof,
    }
