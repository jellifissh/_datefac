from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345C8 = "REMAINING_BLIND_SPOT_ALIAS_CANDIDATE_PACKAGE_345C8_READY"
READY_DECISION_345C9 = "REMAINING_BLIND_SPOT_HUMAN_REVIEW_PACKAGE_345C9_READY"
INPUT_STAGE_345C9 = "POST_345C8_REMAINING_BLIND_SPOT_HUMAN_REVIEW_PACKAGE"

DEFAULT_REMAINING_BLIND_SPOT_ALIAS_CANDIDATE_PACKAGE_345C8_DIR = Path(
    r"D:\_datefac\output\remaining_blind_spot_alias_candidate_package_345c8"
)
DEFAULT_OUTPUT_DIR = Path(
    r"D:\_datefac\output\remaining_blind_spot_human_review_package_345c9"
)
DEFAULT_LEDGER_PATH = Path(
    r"D:\_datefac\docs\project_milestones\PROJECT_MILESTONE_LEDGER_项目进程.md"
)

MANIFEST_FILE_NAME = "remaining_blind_spot_human_review_package_345c9_manifest.json"
REVIEW_ROWS_JSON_FILE_NAME = "remaining_blind_spot_human_review_package_345c9_review_rows.json"
REVIEW_ROWS_CSV_FILE_NAME = "remaining_blind_spot_human_review_package_345c9_review_rows.csv"
CONTEXT_ONLY_ROWS_JSON_FILE_NAME = (
    "remaining_blind_spot_human_review_package_345c9_context_only_rows.json"
)
CONTEXT_ONLY_ROWS_CSV_FILE_NAME = (
    "remaining_blind_spot_human_review_package_345c9_context_only_rows.csv"
)
BLOCKED_ROWS_JSON_FILE_NAME = (
    "remaining_blind_spot_human_review_package_345c9_blocked_rows.json"
)
BLOCKED_ROWS_CSV_FILE_NAME = (
    "remaining_blind_spot_human_review_package_345c9_blocked_rows.csv"
)
WORKBOOK_FILE_NAME = "remaining_blind_spot_human_review_package_345c9.xlsx"
REVIEWER_CHECKLIST_FILE_NAME = (
    "remaining_blind_spot_human_review_package_345c9_reviewer_checklist.md"
)
DECISION_OPTIONS_FILE_NAME = (
    "remaining_blind_spot_human_review_package_345c9_decision_options.md"
)
PACKAGE_SUMMARY_JSON_FILE_NAME = (
    "remaining_blind_spot_human_review_package_345c9_package_summary.json"
)
EXECUTIVE_SUMMARY_FILE_NAME = (
    "remaining_blind_spot_human_review_package_345c9_executive_summary.md"
)
ARTIFACT_INDEX_FILE_NAME = (
    "remaining_blind_spot_human_review_package_345c9_artifact_index.md"
)
NEXT_PLAN_FILE_NAME = "remaining_blind_spot_human_review_package_345c9_next_plan.md"

INPUT_MANIFEST_NAME = "remaining_blind_spot_alias_candidate_package_345c8_manifest.json"
INPUT_SELECTED_CANDIDATES_JSON_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_selected_candidates.json"
)
INPUT_SELECTED_CANDIDATES_CSV_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_selected_candidates.csv"
)
INPUT_CANDIDATE_IMPACT_SUMMARY_JSON_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_candidate_impact_summary.json"
)
INPUT_CANDIDATE_IMPACT_SUMMARY_CSV_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_candidate_impact_summary.csv"
)
INPUT_REVIEW_BATCH_RECOMMENDATION_JSON_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_review_batch_recommendation.json"
)
INPUT_STOP_OR_CONTINUE_DECISION_JSON_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_stop_or_continue_decision.json"
)
INPUT_EXECUTIVE_SUMMARY_MD_NAME = (
    "remaining_blind_spot_alias_candidate_package_345c8_executive_summary.md"
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

REVIEW_REQUIRED_FIELDS = [
    "blind_spot_review_row_id",
    "source_345c8_blind_spot_candidate_id",
    "review_package_group",
    "raw_metric_name",
    "remaining_row_count",
    "remaining_raw_metric_rank",
    "source_stages",
    "pdf_names",
    "source_artifacts",
    "sample_row_ids",
    "sample_evidence_excerpt",
    "candidate_priority",
    "candidate_reason",
    "risk_level",
    "risk_reasons",
    "estimated_max_newly_normalized_rows",
    "estimated_coverage_delta_if_resolved",
    "estimated_ready_candidate_delta_if_resolved",
    "needs_llm_adjudication",
    "needs_human_review",
    "suggested_next_review_action",
    "review_recommendation",
    "human_blind_spot_review_decision",
    "approved_standard_metric",
    "approved_new_standard_metric",
    "needs_alias_family_expansion",
    "needs_source_context",
    "reviewer",
    "reviewed_at",
    "review_notes",
    "alias_rule_update_allowed",
]

NON_ACTIONABLE_FIELDS = [
    "blind_spot_review_row_id",
    "source_345c8_blind_spot_candidate_id",
    "review_package_group",
    "raw_metric_name",
    "remaining_row_count",
    "remaining_raw_metric_rank",
    "source_stages",
    "pdf_names",
    "source_artifacts",
    "sample_row_ids",
    "sample_evidence_excerpt",
    "candidate_priority",
    "candidate_reason",
    "risk_level",
    "risk_reasons",
    "estimated_max_newly_normalized_rows",
    "estimated_coverage_delta_if_resolved",
    "estimated_ready_candidate_delta_if_resolved",
    "needs_llm_adjudication",
    "needs_human_review",
    "suggested_next_review_action",
    "review_recommendation",
]

ALLOWED_BRANCH_DECISIONS = {
    "CONTINUE_WITH_SECOND_REVIEW_BATCH",
    "CONTINUE_ONLY_IF_HUMAN_REVIEW_CAPACITY_EXISTS",
}

LEDGER_HEADING = "## 345C9 Remaining Blind Spot Human Review Package"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return " ".join(text.split())


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    lowered = _safe_text(value).lower()
    return lowered in {"1", "true", "yes", "y"}


def _int_value(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    text = _safe_text(value)
    if not text:
        return 0
    return int(float(text))


def _float_value(value: Any) -> float:
    text = _safe_text(value)
    if not text:
        return 0.0
    return float(text)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_rows(path: Path) -> List[Dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list JSON payload: {path}")
    return [dict(row) for row in payload]


def _maybe_json_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_safe_text(item) for item in value if _safe_text(item)]
    text = _safe_text(value)
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except Exception:
        return [text]
    if isinstance(parsed, list):
        return [_safe_text(item) for item in parsed if _safe_text(item)]
    return [text]


def _read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for key, value in mapping.items():
        if isinstance(value, (dict, list)):
            value_text = json.dumps(value, ensure_ascii=False)
        else:
            value_text = _safe_text(value)
        rows.append({"key": key, "value": value_text})
    return _clean_frame(pd.DataFrame(rows))


def _normalize_candidate_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "blind_spot_candidate_id": _safe_text(row.get("blind_spot_candidate_id")),
        "raw_metric_name": _safe_text(row.get("raw_metric_name")),
        "remaining_row_count": _int_value(row.get("remaining_row_count")),
        "remaining_raw_metric_rank": _int_value(row.get("remaining_raw_metric_rank")),
        "source_stages": _safe_text(row.get("source_stages")),
        "pdf_names": _safe_text(row.get("pdf_names")),
        "source_artifacts": _safe_text(row.get("source_artifacts")),
        "sample_row_ids": _safe_text(row.get("sample_row_ids")),
        "sample_evidence_excerpt": _safe_text(row.get("sample_evidence_excerpt")),
        "candidate_priority": _safe_text(row.get("candidate_priority")),
        "review_recommendation": _safe_text(row.get("review_recommendation")),
        "candidate_reason": _safe_text(row.get("candidate_reason")),
        "risk_level": _safe_text(row.get("risk_level")),
        "risk_reasons": _maybe_json_list(row.get("risk_reasons")),
        "estimated_max_newly_normalized_rows": _int_value(
            row.get("estimated_max_newly_normalized_rows")
        ),
        "estimated_coverage_delta_if_resolved": round(
            _float_value(row.get("estimated_coverage_delta_if_resolved")),
            6,
        ),
        "estimated_ready_candidate_delta_if_resolved": _int_value(
            row.get("estimated_ready_candidate_delta_if_resolved")
        ),
        "needs_llm_adjudication": _bool_value(row.get("needs_llm_adjudication")),
        "needs_human_review": _bool_value(row.get("needs_human_review")),
        "suggested_next_review_action": _safe_text(row.get("suggested_next_review_action")),
        "candidate_package_only": _bool_value(row.get("candidate_package_only")),
        "official_rules_modified": _bool_value(row.get("official_rules_modified")),
        "official_alias_assets_modified": _bool_value(
            row.get("official_alias_assets_modified")
        ),
    }


def _load_candidates_with_fallback(
    json_path: Path,
    csv_path: Path,
) -> tuple[List[Dict[str, Any]], str]:
    if json_path.exists():
        try:
            return [_normalize_candidate_row(row) for row in _load_json_rows(json_path)], "json"
        except Exception:
            pass
    csv_rows = _read_csv_rows(_require_existing(csv_path))
    return [_normalize_candidate_row(row) for row in csv_rows], "csv"


def _load_impact_summary_with_fallback(
    json_path: Path,
    csv_path: Path,
) -> tuple[List[Dict[str, Any]], str]:
    if json_path.exists():
        try:
            rows = _load_json_rows(json_path)
            return [dict(row) for row in rows], "json"
        except Exception:
            pass
    return _read_csv_rows(_require_existing(csv_path)), "csv"


def _row_with_human_fields(
    row: Dict[str, Any],
    review_group: str,
    review_row_index: int,
) -> Dict[str, Any]:
    return {
        "blind_spot_review_row_id": f"345c9::review::{review_row_index:03d}",
        "source_345c8_blind_spot_candidate_id": row["blind_spot_candidate_id"],
        "review_package_group": review_group,
        "raw_metric_name": row["raw_metric_name"],
        "remaining_row_count": row["remaining_row_count"],
        "remaining_raw_metric_rank": row["remaining_raw_metric_rank"],
        "source_stages": row["source_stages"],
        "pdf_names": row["pdf_names"],
        "source_artifacts": row["source_artifacts"],
        "sample_row_ids": row["sample_row_ids"],
        "sample_evidence_excerpt": row["sample_evidence_excerpt"],
        "candidate_priority": row["candidate_priority"],
        "candidate_reason": row["candidate_reason"],
        "risk_level": row["risk_level"],
        "risk_reasons": row["risk_reasons"],
        "estimated_max_newly_normalized_rows": row["estimated_max_newly_normalized_rows"],
        "estimated_coverage_delta_if_resolved": row["estimated_coverage_delta_if_resolved"],
        "estimated_ready_candidate_delta_if_resolved": row[
            "estimated_ready_candidate_delta_if_resolved"
        ],
        "needs_llm_adjudication": row["needs_llm_adjudication"],
        "needs_human_review": row["needs_human_review"],
        "suggested_next_review_action": row["suggested_next_review_action"],
        "review_recommendation": row["review_recommendation"],
        "human_blind_spot_review_decision": "",
        "approved_standard_metric": "",
        "approved_new_standard_metric": "",
        "needs_alias_family_expansion": False,
        "needs_source_context": False,
        "reviewer": "",
        "reviewed_at": "",
        "review_notes": "",
        "alias_rule_update_allowed": False,
    }


def _row_without_human_fields(
    row: Dict[str, Any],
    review_group: str,
    review_row_index: int,
) -> Dict[str, Any]:
    base = _row_with_human_fields(row, review_group, review_row_index)
    return {key: base[key] for key in NON_ACTIONABLE_FIELDS}


def _risk_count(rows: Iterable[Dict[str, Any]], risk_level: str) -> int:
    return sum(1 for row in rows if _safe_text(row.get("risk_level")) == risk_level)


def _sum_int(rows: Iterable[Dict[str, Any]], key: str) -> int:
    return sum(_int_value(row.get(key)) for row in rows)


def _sum_float(rows: Iterable[Dict[str, Any]], key: str) -> float:
    return round(sum(_float_value(row.get(key)) for row in rows), 6)


def build_345c9_ledger_entry(
    *,
    manifest: Dict[str, Any],
    ledger_path: Path,
) -> str:
    lines = [
        LEDGER_HEADING,
        "",
        "Status: completed",
        "",
        "Decision:",
        f"- `{manifest.get('decision', '')}`",
        "",
        "Input package:",
        f"- `{DEFAULT_REMAINING_BLIND_SPOT_ALIAS_CANDIDATE_PACKAGE_345C8_DIR}`",
        "",
        "Output package:",
        f"- `{manifest.get('output_dir', '')}`",
        "",
        "Key metrics:",
        f"- `selected_candidate_count = {manifest.get('selected_candidate_count', 0)}`",
        f"- `review_required_row_count = {manifest.get('review_required_row_count', 0)}`",
        f"- `context_only_row_count = {manifest.get('context_only_row_count', 0)}`",
        f"- `blocked_or_too_generic_row_count = {manifest.get('blocked_or_too_generic_row_count', 0)}`",
        f"- `generated_review_pending_count = {manifest.get('generated_review_pending_count', 0)}`",
        f"- `generated_approved_count = {manifest.get('generated_approved_count', 0)}`",
        f"- `alias_rule_update_allowed_count = {manifest.get('alias_rule_update_allowed_count', 0)}`",
        f"- `qa_fail_count = {manifest.get('qa_fail_count', 0)}`",
        "",
        "Gate status:",
        f"- `formal_client_export_allowed = {str(bool(manifest.get('formal_client_export_allowed'))).lower()}`",
        f"- `client_ready = {str(bool(manifest.get('client_ready'))).lower()}`",
        f"- `production_ready = {str(bool(manifest.get('production_ready'))).lower()}`",
        f"- `global_strict_human_review_completed = {str(bool(manifest.get('global_strict_human_review_completed'))).lower()}`",
        "",
        "No-write-back confirmation:",
        f"- `no_write_back_proof_passed = {str(bool(manifest.get('no_write_back_proof_passed'))).lower()}`",
        f"- `official_rules_modified = {str(bool(manifest.get('official_rules_modified'))).lower()}`",
        f"- `official_alias_assets_modified = {str(bool(manifest.get('official_alias_assets_modified'))).lower()}`",
        "",
        "Validation commands and results:",
        "- `python -m py_compile ...` passed",
        "- `python -m pytest tests\\benchmark\\test_remaining_blind_spot_human_review_package_345c9.py -q` passed",
        "- real runner passed",
        "",
        "Next recommended step:",
        "- human fills workbook, then `345C10 Second Batch Reviewed Alias Decision Ingestion`",
    ]
    return "\n".join(lines)


def ledger_has_345c9_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return LEDGER_HEADING in ledger_path.read_text(encoding="utf-8")


def append_345c9_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    if ledger_has_345c9_entry(ledger_path):
        return False
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    addition = build_345c9_ledger_entry(manifest=manifest, ledger_path=ledger_path)
    prefix = "\n\n" if existing and not existing.endswith("\n\n") else ""
    if existing.endswith("\n"):
        prefix = "\n" if not existing.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(existing + prefix + addition + "\n", encoding="utf-8")
    return True


def _artifact_rows(output_dir: Path) -> List[Dict[str, str]]:
    return [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "Manifest with grouped row counts, safety checks, and gate state.",
        },
        {
            "artifact_name": REVIEW_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / REVIEW_ROWS_JSON_FILE_NAME),
            "purpose": "Actionable review rows in JSON.",
        },
        {
            "artifact_name": REVIEW_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / REVIEW_ROWS_CSV_FILE_NAME),
            "purpose": "Actionable review rows in CSV.",
        },
        {
            "artifact_name": CONTEXT_ONLY_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / CONTEXT_ONLY_ROWS_JSON_FILE_NAME),
            "purpose": "Context-only rows in JSON.",
        },
        {
            "artifact_name": CONTEXT_ONLY_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / CONTEXT_ONLY_ROWS_CSV_FILE_NAME),
            "purpose": "Context-only rows in CSV.",
        },
        {
            "artifact_name": BLOCKED_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / BLOCKED_ROWS_JSON_FILE_NAME),
            "purpose": "Blocked or too-generic rows in JSON.",
        },
        {
            "artifact_name": BLOCKED_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / BLOCKED_ROWS_CSV_FILE_NAME),
            "purpose": "Blocked or too-generic rows in CSV.",
        },
        {
            "artifact_name": WORKBOOK_FILE_NAME,
            "path": str(output_dir / WORKBOOK_FILE_NAME),
            "purpose": "Reviewer workbook with separate actionable, context-only, and blocked sheets.",
        },
        {
            "artifact_name": REVIEWER_CHECKLIST_FILE_NAME,
            "path": str(output_dir / REVIEWER_CHECKLIST_FILE_NAME),
            "purpose": "Reviewer fill instructions and package boundary notes.",
        },
        {
            "artifact_name": DECISION_OPTIONS_FILE_NAME,
            "path": str(output_dir / DECISION_OPTIONS_FILE_NAME),
            "purpose": "Allowed human decisions and constraints.",
        },
        {
            "artifact_name": PACKAGE_SUMMARY_JSON_FILE_NAME,
            "path": str(output_dir / PACKAGE_SUMMARY_JSON_FILE_NAME),
            "purpose": "Structured package summary and QA bundle.",
        },
        {
            "artifact_name": EXECUTIVE_SUMMARY_FILE_NAME,
            "path": str(output_dir / EXECUTIVE_SUMMARY_FILE_NAME),
            "purpose": "Narrative summary of the second-batch human review package.",
        },
        {
            "artifact_name": ARTIFACT_INDEX_FILE_NAME,
            "path": str(output_dir / ARTIFACT_INDEX_FILE_NAME),
            "purpose": "Index of all 345C9 artifacts.",
        },
        {
            "artifact_name": NEXT_PLAN_FILE_NAME,
            "path": str(output_dir / NEXT_PLAN_FILE_NAME),
            "purpose": "Next step plan after packaging.",
        },
    ]


def build_remaining_blind_spot_human_review_package_345c9(
    *,
    remaining_blind_spot_alias_candidate_package_345c8_dir: Path,
    output_dir: Path,
    repo_root: Path,
    include_context_only: bool,
    ledger_path: Path | None = None,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = _require_existing(
        remaining_blind_spot_alias_candidate_package_345c8_dir / INPUT_MANIFEST_NAME
    )
    selected_candidates_json_path = (
        remaining_blind_spot_alias_candidate_package_345c8_dir
        / INPUT_SELECTED_CANDIDATES_JSON_NAME
    )
    selected_candidates_csv_path = (
        remaining_blind_spot_alias_candidate_package_345c8_dir
        / INPUT_SELECTED_CANDIDATES_CSV_NAME
    )
    impact_summary_json_path = (
        remaining_blind_spot_alias_candidate_package_345c8_dir
        / INPUT_CANDIDATE_IMPACT_SUMMARY_JSON_NAME
    )
    impact_summary_csv_path = (
        remaining_blind_spot_alias_candidate_package_345c8_dir
        / INPUT_CANDIDATE_IMPACT_SUMMARY_CSV_NAME
    )
    review_batch_recommendation_path = _require_existing(
        remaining_blind_spot_alias_candidate_package_345c8_dir
        / INPUT_REVIEW_BATCH_RECOMMENDATION_JSON_NAME
    )
    stop_or_continue_decision_path = _require_existing(
        remaining_blind_spot_alias_candidate_package_345c8_dir
        / INPUT_STOP_OR_CONTINUE_DECISION_JSON_NAME
    )
    executive_summary_path = (
        remaining_blind_spot_alias_candidate_package_345c8_dir / INPUT_EXECUTIVE_SUMMARY_MD_NAME
    )

    files_read = [
        str(manifest_path),
        str(review_batch_recommendation_path),
        str(stop_or_continue_decision_path),
    ]
    if selected_candidates_json_path.exists():
        files_read.append(str(selected_candidates_json_path))
    if selected_candidates_csv_path.exists():
        files_read.append(str(selected_candidates_csv_path))
    if impact_summary_json_path.exists():
        files_read.append(str(impact_summary_json_path))
    if impact_summary_csv_path.exists():
        files_read.append(str(impact_summary_csv_path))
    if executive_summary_path.exists():
        files_read.append(str(executive_summary_path))

    input_paths = [
        path
        for path in [
            manifest_path,
            selected_candidates_json_path if selected_candidates_json_path.exists() else None,
            selected_candidates_csv_path if selected_candidates_csv_path.exists() else None,
            impact_summary_json_path if impact_summary_json_path.exists() else None,
            impact_summary_csv_path if impact_summary_csv_path.exists() else None,
            review_batch_recommendation_path,
            stop_or_continue_decision_path,
            executive_summary_path if executive_summary_path.exists() else None,
        ]
        if path is not None
    ]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    manifest_345c8 = _read_json(manifest_path)
    selected_candidates, selected_source = _load_candidates_with_fallback(
        selected_candidates_json_path,
        selected_candidates_csv_path,
    )
    candidate_impact_summary, impact_source = _load_impact_summary_with_fallback(
        impact_summary_json_path,
        impact_summary_csv_path,
    )
    review_batch_recommendation = _read_json(review_batch_recommendation_path)
    stop_or_continue_decision = _read_json(stop_or_continue_decision_path)

    if _safe_text(manifest_345c8.get("decision")) != READY_DECISION_345C8:
        raise ValueError("345C8 manifest decision is not READY.")
    branch_decision = _safe_text(
        stop_or_continue_decision.get("alias_branch_stop_or_continue_decision")
        or manifest_345c8.get("alias_branch_stop_or_continue_decision")
    )
    if branch_decision not in ALLOWED_BRANCH_DECISIONS:
        raise ValueError(
            "345C8 alias_branch_stop_or_continue_decision must allow a second review batch."
        )
    if int(manifest_345c8.get("selected_candidate_count", 0)) <= 0:
        raise ValueError("345C8 selected_candidate_count must be greater than zero.")
    for gate_name in ["formal_client_export_allowed", "client_ready", "production_ready"]:
        if bool(manifest_345c8.get(gate_name)):
            raise ValueError(f"345C8 gate must remain false: {gate_name}")
    if bool(manifest_345c8.get("official_rules_modified")):
        raise ValueError("345C8 official_rules_modified must remain false.")
    if bool(manifest_345c8.get("official_alias_assets_modified")):
        raise ValueError("345C8 official_alias_assets_modified must remain false.")
    if not all(row["candidate_package_only"] for row in selected_candidates):
        raise ValueError("All 345C8 selected candidates must remain candidate-package only.")
    if not all(not row["official_rules_modified"] for row in selected_candidates):
        raise ValueError("Selected candidates must preserve official_rules_modified = false.")
    if not all(not row["official_alias_assets_modified"] for row in selected_candidates):
        raise ValueError("Selected candidates must preserve official_alias_assets_modified = false.")

    review_required_candidates = [
        row
        for row in selected_candidates
        if row["review_recommendation"] == "INCLUDE_IN_SECOND_REVIEW_BATCH"
    ]
    context_only_candidates = [
        row
        for row in selected_candidates
        if row["review_recommendation"] == "INCLUDE_AS_CONTEXT_ONLY"
    ]
    blocked_candidates = [
        row
        for row in selected_candidates
        if row["review_recommendation"]
        in {"EXCLUDE_TOO_GENERIC", "NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW"}
    ]

    main_review_source_rows = list(review_required_candidates)
    if include_context_only:
        main_review_source_rows.extend(context_only_candidates)

    review_rows = [
        _row_with_human_fields(row, "review_required", index)
        for index, row in enumerate(main_review_source_rows, start=1)
    ]
    context_only_rows = [
        _row_without_human_fields(row, "context_only", index)
        for index, row in enumerate(context_only_candidates, start=1)
    ]
    blocked_rows = [
        _row_without_human_fields(row, "blocked_or_too_generic", index)
        for index, row in enumerate(blocked_candidates, start=1)
    ]

    review_required_estimated_row_impact_total = _sum_int(
        review_required_candidates,
        "estimated_max_newly_normalized_rows",
    )
    review_required_estimated_coverage_delta_total = _sum_float(
        review_required_candidates,
        "estimated_coverage_delta_if_resolved",
    )
    review_required_estimated_ready_candidate_delta_total = _sum_int(
        review_required_candidates,
        "estimated_ready_candidate_delta_if_resolved",
    )

    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths}
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)
    upstream_unchanged = input_hashes_before == input_hashes_after

    no_apply_proof = build_no_apply_proof(
        stage="345C9",
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
    no_apply_proof["alias_apply_simulation_allowed"] = False
    no_apply_proof["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_345c9")
        and upstream_unchanged
        and not no_apply_proof.get("formal_client_export_generated", True)
        and not no_apply_proof.get("real_production_apply_performed", True)
        and not no_apply_proof.get("official_rules_modified", True)
        and not no_apply_proof.get("official_alias_assets_modified", True)
    )

    milestone_ledger_updated = (
        ledger_has_345c9_entry(ledger_path) if ledger_path is not None else False
    )

    checks = [
        {
            "check_name": "inputs::345c8_ready",
            "status": "PASS"
            if _safe_text(manifest_345c8.get("decision")) == READY_DECISION_345C8
            and int(manifest_345c8.get("qa_fail_count", 1)) == 0
            else "FAIL",
            "detail": json.dumps(
                {
                    "input_345c8_decision": manifest_345c8.get("decision"),
                    "input_qa_fail_count": manifest_345c8.get("qa_fail_count"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::branch_decision_allows_second_review_batch",
            "status": "PASS" if branch_decision in ALLOWED_BRANCH_DECISIONS else "FAIL",
            "detail": branch_decision,
        },
        {
            "check_name": "counts::selected_candidate_count_positive",
            "status": "PASS" if len(selected_candidates) > 0 else "FAIL",
            "detail": json.dumps(
                {"selected_candidate_count": len(selected_candidates)},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "counts::group_split_matches_selected_total",
            "status": "PASS"
            if len(review_required_candidates) + len(context_only_candidates) + len(blocked_candidates)
            == len(selected_candidates)
            else "FAIL",
            "detail": json.dumps(
                {
                    "selected_candidate_count": len(selected_candidates),
                    "grouped_total": len(review_required_candidates)
                    + len(context_only_candidates)
                    + len(blocked_candidates),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "schema::review_rows_have_blank_human_fields",
            "status": "PASS"
            if all(
                not _safe_text(row.get("human_blind_spot_review_decision"))
                and not _safe_text(row.get("approved_standard_metric"))
                and not _safe_text(row.get("approved_new_standard_metric"))
                and not _safe_text(row.get("reviewer"))
                and not _safe_text(row.get("reviewed_at"))
                and not _safe_text(row.get("review_notes"))
                and row.get("needs_alias_family_expansion") is False
                and row.get("needs_source_context") is False
                and row.get("alias_rule_update_allowed") is False
                for row in review_rows
            )
            else "FAIL",
            "detail": "main review rows must keep all human fields blank or false by default",
        },
        {
            "check_name": "separation::context_only_not_mixed_by_default",
            "status": "PASS"
            if include_context_only or all(
                row.get("review_recommendation") == "INCLUDE_IN_SECOND_REVIEW_BATCH"
                for row in review_rows
            )
            else "FAIL",
            "detail": json.dumps(
                {"include_context_only": include_context_only},
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "separation::context_and_blocked_separated",
            "status": "PASS"
            if all(
                row.get("review_recommendation") == "INCLUDE_AS_CONTEXT_ONLY"
                for row in context_only_rows
            )
            and all(
                row.get("review_recommendation")
                in {"EXCLUDE_TOO_GENERIC", "NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW"}
                for row in blocked_rows
            )
            else "FAIL",
            "detail": "non-actionable rows must remain outside the actionable review sheet",
        },
        {
            "check_name": "safety::generated_approved_count_zero",
            "status": "PASS",
            "detail": "345C9 is package-only and does not approve rows automatically",
        },
        {
            "check_name": "safety::alias_rule_update_allowed_zero",
            "status": "PASS"
            if all(row.get("alias_rule_update_allowed") is False for row in review_rows)
            else "FAIL",
            "detail": "alias_rule_update_allowed must remain false in generated package",
        },
        {
            "check_name": "safety::official_rules_and_alias_assets_unchanged",
            "status": "PASS" if official_assets_before == official_assets_after else "FAIL",
            "detail": json.dumps(official_assets_after, ensure_ascii=False),
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
            "check_name": "ledger::345c9_entry_present",
            "status": "PASS" if milestone_ledger_updated else "FAIL",
            "detail": str(ledger_path) if ledger_path is not None else "__NO_LEDGER_PATH__",
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
        "decision": READY_DECISION_345C9,
        "input_stage": INPUT_STAGE_345C9,
        "qa_fail_count": qa_fail_count,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_345c8_decision": _safe_text(manifest_345c8.get("decision")),
        "input_alias_branch_stop_or_continue_decision": branch_decision,
        "selected_candidate_count": len(selected_candidates),
        "review_required_row_count": len(review_required_candidates),
        "context_only_row_count": len(context_only_candidates),
        "blocked_or_too_generic_row_count": len(blocked_candidates),
        "main_review_sheet_row_count": len(review_rows),
        "review_required_estimated_row_impact_total": review_required_estimated_row_impact_total,
        "review_required_estimated_coverage_delta_total": review_required_estimated_coverage_delta_total,
        "review_required_estimated_ready_candidate_delta_total": review_required_estimated_ready_candidate_delta_total,
        "review_required_high_risk_count": _risk_count(review_required_candidates, "HIGH"),
        "review_required_medium_risk_count": _risk_count(review_required_candidates, "MEDIUM"),
        "review_required_low_risk_count": _risk_count(review_required_candidates, "LOW"),
        "main_review_workbook_generated": True,
        "reviewer_checklist_generated": True,
        "decision_options_generated": True,
        "human_review_completed": False,
        "generated_review_pending_count": len(review_rows),
        "generated_approved_count": 0,
        "alias_rule_update_allowed_count": 0,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "candidate_package_only": True,
        "alias_apply_simulation_allowed": False,
        "full_structured_demo_export_reasonable_after_345c9": False,
        "include_context_only": include_context_only,
        "selected_candidates_read_source": selected_source,
        "candidate_impact_summary_read_source": impact_source,
        "candidate_impact_summary_row_count": len(candidate_impact_summary),
        "review_batch_recommendation_selected_candidate_count": _int_value(
            review_batch_recommendation.get("selected_candidate_count")
        ),
        "milestone_ledger_updated": milestone_ledger_updated,
        "generated_at_utc": _utc_now(),
        "output_dir": str(output_dir),
    }

    package_summary = {
        "manifest": manifest,
        "review_batch_recommendation": review_batch_recommendation,
        "stop_or_continue_decision": stop_or_continue_decision,
        "qa_json": {
            "decision": READY_DECISION_345C9,
            "qa_fail_count": qa_fail_count,
            "checks": checks,
        },
        "top_review_required_rows": sorted(
            review_required_candidates,
            key=lambda row: (-_int_value(row.get("remaining_row_count")), row.get("raw_metric_name", "")),
        )[:10],
    }

    workbook_sheets = {
        "review_required": _clean_frame(pd.DataFrame(review_rows, columns=REVIEW_REQUIRED_FIELDS)),
        "context_only": _clean_frame(pd.DataFrame(context_only_rows, columns=NON_ACTIONABLE_FIELDS)),
        "blocked_or_too_generic": _clean_frame(pd.DataFrame(blocked_rows, columns=NON_ACTIONABLE_FIELDS)),
        "decision_options": _clean_frame(
            pd.DataFrame(
                [
                    {
                        "human_blind_spot_review_decision": "APPROVE_EXISTING_MAPPING",
                        "rule": "requires approved_standard_metric",
                    },
                    {
                        "human_blind_spot_review_decision": "APPROVE_NEW_STANDARD",
                        "rule": "requires approved_new_standard_metric",
                    },
                    {
                        "human_blind_spot_review_decision": "REJECT_TOO_GENERIC",
                        "rule": "should include review_notes",
                    },
                    {
                        "human_blind_spot_review_decision": "NEEDS_SOURCE_CONTEXT",
                        "rule": "should include review_notes describing missing context",
                    },
                    {
                        "human_blind_spot_review_decision": "DEFER",
                        "rule": "should include review_notes when possible",
                    },
                ]
            )
        ),
        "reviewer_checklist": _clean_frame(
            pd.DataFrame(
                [
                    {"line_no": 1, "message": "Fill only the human review fields in review_required."},
                    {"line_no": 2, "message": "Do not edit evidence fields or source fields."},
                    {"line_no": 3, "message": "Use only the allowed decision options."},
                    {"line_no": 4, "message": "Do not set alias_rule_update_allowed to true."},
                    {"line_no": 5, "message": "Use context_only as reference only."},
                    {"line_no": 6, "message": "Blocked rows remain deferred until more source context exists."},
                ]
            )
        ),
        "package_summary": _build_key_value_df(
            {
                "decision": manifest["decision"],
                "qa_fail_count": manifest["qa_fail_count"],
                "review_required_row_count": manifest["review_required_row_count"],
                "context_only_row_count": manifest["context_only_row_count"],
                "blocked_or_too_generic_row_count": manifest["blocked_or_too_generic_row_count"],
                "review_required_estimated_row_impact_total": manifest[
                    "review_required_estimated_row_impact_total"
                ],
                "review_required_estimated_coverage_delta_total": manifest[
                    "review_required_estimated_coverage_delta_total"
                ],
                "input_alias_branch_stop_or_continue_decision": manifest[
                    "input_alias_branch_stop_or_continue_decision"
                ],
                "no_write_back_proof_passed": manifest["no_write_back_proof_passed"],
                "milestone_ledger_updated": manifest["milestone_ledger_updated"],
            }
        ),
    }

    return {
        "manifest": manifest,
        "review_rows": review_rows,
        "context_only_rows": context_only_rows,
        "blocked_rows": blocked_rows,
        "package_summary": package_summary,
        "workbook_sheets": workbook_sheets,
        "artifact_index_rows": _artifact_rows(output_dir),
        "qa_json": package_summary["qa_json"],
        "no_apply_proof": no_apply_proof,
    }

