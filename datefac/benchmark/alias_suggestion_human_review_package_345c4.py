from __future__ import annotations

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


READY_DECISION_345C2 = "LLM_ASSISTED_METRIC_ALIAS_ADJUDICATION_345C2_READY"
READY_DECISION_345C4 = "ALIAS_SUGGESTION_HUMAN_REVIEW_PACKAGE_345C4_READY"
INPUT_STAGE_345C4 = "POST_345C2_LIVE_ALIAS_SUGGESTION_REVIEW_PACKAGE"

DEFAULT_345C2_LIVE_DIR = Path(r"D:\_datefac\output\llm_assisted_metric_alias_adjudication_345c2_live")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_suggestion_human_review_package_345c4")

MANIFEST_FILE_NAME = "alias_suggestion_human_review_package_345c4_manifest.json"
REVIEW_ROWS_JSON_FILE_NAME = "alias_suggestion_human_review_package_345c4_review_rows.json"
REVIEW_ROWS_CSV_FILE_NAME = "alias_suggestion_human_review_package_345c4_review_rows.csv"
WORKBOOK_FILE_NAME = "alias_suggestion_human_review_package_345c4.xlsx"
REVIEWER_CHECKLIST_FILE_NAME = "alias_suggestion_human_review_package_345c4_reviewer_checklist.md"
DECISION_OPTIONS_FILE_NAME = "alias_suggestion_human_review_package_345c4_decision_options.md"
LLM_SUGGESTION_SUMMARY_FILE_NAME = "alias_suggestion_human_review_package_345c4_llm_suggestion_summary.json"
PRIORITY_SUMMARY_FILE_NAME = "alias_suggestion_human_review_package_345c4_priority_summary.json"
EXECUTIVE_SUMMARY_FILE_NAME = "alias_suggestion_human_review_package_345c4_executive_summary.md"
ARTIFACT_INDEX_FILE_NAME = "alias_suggestion_human_review_package_345c4_artifact_index.md"
NEXT_PLAN_FILE_NAME = "alias_suggestion_human_review_package_345c4_next_plan.md"

INPUT_MANIFEST_NAME = "llm_assisted_metric_alias_adjudication_345c2_manifest.json"
INPUT_SUGGESTIONS_JSON_NAME = "llm_assisted_metric_alias_adjudication_345c2_alias_suggestions.json"
INPUT_SUGGESTIONS_CSV_NAME = "llm_assisted_metric_alias_adjudication_345c2_alias_suggestions.csv"
INPUT_REVIEW_REQUIRED_JSON_NAME = "llm_assisted_metric_alias_adjudication_345c2_review_required.json"
INPUT_REVIEW_REQUIRED_CSV_NAME = "llm_assisted_metric_alias_adjudication_345c2_review_required.csv"
INPUT_RESPONSE_AUDIT_JSON_NAME = "llm_assisted_metric_alias_adjudication_345c2_response_audit.json"
INPUT_PROMPT_AUDIT_MD_NAME = "llm_assisted_metric_alias_adjudication_345c2_prompt_audit.md"

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

REVIEW_ROW_FIELDS = [
    "alias_review_row_id",
    "alias_adjudication_id",
    "raw_metric_name",
    "frequency",
    "alias_candidate_priority",
    "source_stages",
    "pdf_names",
    "sample_row_ids",
    "llm_suggested_action",
    "llm_suggested_standard_metric",
    "llm_suggested_new_standard_metric",
    "llm_confidence",
    "llm_reason",
    "llm_evidence_excerpt",
    "llm_risk_flags",
    "llm_needs_human_review",
    "response_parse_status",
    "response_validation_status",
    "review_priority",
    "recommended_human_focus",
    "human_alias_review_decision",
    "approved_standard_metric",
    "approved_new_standard_metric",
    "alias_reviewer",
    "alias_reviewed_at",
    "alias_review_notes",
    "alias_rule_update_allowed",
]

WORKBOOK_SHEETS = [
    "00_README",
    "01_REVIEW_SUMMARY",
    "02_REVIEW_ROWS",
    "03_DECISION_OPTIONS",
    "04_REVIEWER_CHECKLIST",
    "05_LLM_SUGGESTION_SUM",
    "06_PRIORITY_SUMMARY",
    "07_NO_WRITE_BACK",
    "08_NEXT_STEPS",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return " ".join(text.split())


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_rows(path: Path) -> List[Dict[str, Any]]:
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list JSON payload in {path}")
    return [dict(row) for row in payload]


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


def _require_existing(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required input file missing: {path}")
    return path


def _flatten_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return _safe_text(value)


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]
    ).astype(object).where(pd.notna(pd.DataFrame()), "")


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _review_priority(row: Dict[str, Any]) -> str:
    if row.get("llm_suggested_action") == "PROPOSE_NEW_STANDARD_METRIC":
        return "HIGH"
    if row.get("response_validation_status") != "VALID":
        return "HIGH"
    if row.get("llm_suggested_action") == "INSUFFICIENT_EVIDENCE":
        return "HIGH"
    if _safe_text(row.get("alias_candidate_priority")).upper() == "HIGH":
        return "HIGH"
    if _safe_text(row.get("llm_confidence")).upper() == "MEDIUM":
        return "MEDIUM"
    if int(row.get("frequency") or 0) >= 50:
        return "MEDIUM"
    return "LOW"


def _recommended_human_focus(row: Dict[str, Any]) -> str:
    if row.get("response_validation_status") != "VALID":
        return "inspect validation failure before deciding"
    if row.get("llm_suggested_action") == "PROPOSE_NEW_STANDARD_METRIC":
        return "confirm whether this should become a new standard metric"
    if row.get("llm_suggested_action") == "MAP_TO_EXISTING_STANDARD_METRIC":
        return "check if this can map to an existing standard metric"
    if row.get("llm_suggested_action") == "INSUFFICIENT_EVIDENCE":
        return "verify insufficient evidence before rejecting"
    return "review semantic meaning before any apply simulation"


def build_review_rows(suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(suggestions, start=1):
        review_row = {
            "alias_review_row_id": f"345c4::review::{index:03d}",
            "alias_adjudication_id": _safe_text(row.get("alias_adjudication_id")),
            "raw_metric_name": _safe_text(row.get("raw_metric_name")),
            "frequency": int(row.get("frequency") or 0),
            "alias_candidate_priority": _safe_text(row.get("alias_candidate_priority")),
            "source_stages": _safe_text(row.get("source_stages")),
            "pdf_names": _safe_text(row.get("pdf_names")),
            "sample_row_ids": _safe_text(row.get("sample_row_ids")),
            "llm_suggested_action": _safe_text(row.get("suggested_action")),
            "llm_suggested_standard_metric": _safe_text(row.get("suggested_standard_metric")),
            "llm_suggested_new_standard_metric": _safe_text(row.get("suggested_new_standard_metric")),
            "llm_confidence": _safe_text(row.get("confidence")),
            "llm_reason": _safe_text(row.get("reason")),
            "llm_evidence_excerpt": _safe_text(row.get("evidence_excerpt")),
            "llm_risk_flags": row.get("risk_flags", []),
            "llm_needs_human_review": bool(row.get("needs_human_review")),
            "response_parse_status": _safe_text(row.get("response_parse_status")),
            "response_validation_status": _safe_text(row.get("response_validation_status")),
            "review_priority": "",
            "recommended_human_focus": "",
            "human_alias_review_decision": "",
            "approved_standard_metric": "",
            "approved_new_standard_metric": "",
            "alias_reviewer": "",
            "alias_reviewed_at": "",
            "alias_review_notes": "",
            "alias_rule_update_allowed": False,
        }
        review_row["review_priority"] = _review_priority(review_row)
        review_row["recommended_human_focus"] = _recommended_human_focus(review_row)
        rows.append(review_row)
    return rows


def build_decision_options_rows() -> List[Dict[str, str]]:
    return [
        {
            "human_alias_review_decision": "APPROVE_EXISTING_MAPPING",
            "rule": "requires approved_standard_metric",
        },
        {
            "human_alias_review_decision": "APPROVE_NEW_STANDARD",
            "rule": "requires approved_new_standard_metric and should usually include notes",
        },
        {
            "human_alias_review_decision": "REJECT_ALIAS",
            "rule": "should include alias_review_notes",
        },
        {
            "human_alias_review_decision": "NEEDS_MORE_CONTEXT",
            "rule": "should explain what context is missing",
        },
        {
            "human_alias_review_decision": "DEFER",
            "rule": "do not use this row in later apply simulation until revisited",
        },
    ]


def build_llm_suggestion_summary(review_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for row in review_rows:
        key = _safe_text(row.get("llm_suggested_action")) or "UNKNOWN"
        counts[key] = counts.get(key, 0) + 1
    return [
        {"llm_suggested_action": key, "row_count": value}
        for key, value in sorted(counts.items())
    ]


def build_priority_summary(review_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for row in review_rows:
        key = _safe_text(row.get("review_priority")) or "UNKNOWN"
        counts[key] = counts.get(key, 0) + 1
    return [
        {"review_priority": key, "row_count": value}
        for key, value in sorted(counts.items())
    ]


def _artifact_rows(output_dir: Path) -> List[Dict[str, str]]:
    return [
        {
            "artifact_name": MANIFEST_FILE_NAME,
            "path": str(output_dir / MANIFEST_FILE_NAME),
            "purpose": "Manifest and gate summary.",
        },
        {
            "artifact_name": REVIEW_ROWS_JSON_FILE_NAME,
            "path": str(output_dir / REVIEW_ROWS_JSON_FILE_NAME),
            "purpose": "Human review package rows in JSON.",
        },
        {
            "artifact_name": REVIEW_ROWS_CSV_FILE_NAME,
            "path": str(output_dir / REVIEW_ROWS_CSV_FILE_NAME),
            "purpose": "Human review package rows in CSV.",
        },
        {
            "artifact_name": WORKBOOK_FILE_NAME,
            "path": str(output_dir / WORKBOOK_FILE_NAME),
            "purpose": "Fillable human review workbook.",
        },
        {
            "artifact_name": REVIEWER_CHECKLIST_FILE_NAME,
            "path": str(output_dir / REVIEWER_CHECKLIST_FILE_NAME),
            "purpose": "Reviewer checklist and boundary notes.",
        },
        {
            "artifact_name": DECISION_OPTIONS_FILE_NAME,
            "path": str(output_dir / DECISION_OPTIONS_FILE_NAME),
            "purpose": "Allowed human decision options.",
        },
    ]


def build_alias_suggestion_human_review_package_345c4(
    *,
    llm_assisted_metric_alias_adjudication_345c2_live_dir: Path,
    output_dir: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    manifest_345c2_path = _require_existing(
        llm_assisted_metric_alias_adjudication_345c2_live_dir / INPUT_MANIFEST_NAME
    )
    suggestions_path = _require_existing(
        llm_assisted_metric_alias_adjudication_345c2_live_dir / INPUT_SUGGESTIONS_JSON_NAME
    )
    review_required_path = _require_existing(
        llm_assisted_metric_alias_adjudication_345c2_live_dir / INPUT_REVIEW_REQUIRED_JSON_NAME
    )
    response_audit_path = llm_assisted_metric_alias_adjudication_345c2_live_dir / INPUT_RESPONSE_AUDIT_JSON_NAME
    prompt_audit_path = llm_assisted_metric_alias_adjudication_345c2_live_dir / INPUT_PROMPT_AUDIT_MD_NAME

    official_assets_before = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged_before = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    files_read = [str(manifest_345c2_path), str(suggestions_path), str(review_required_path)]
    if response_audit_path.exists():
        files_read.append(str(response_audit_path))
    if prompt_audit_path.exists():
        files_read.append(str(prompt_audit_path))

    input_hashes_before = {
        str(path): sha256_file(path)
        for path in [manifest_345c2_path, suggestions_path, review_required_path]
    }

    manifest_345c2 = _read_json(manifest_345c2_path)
    suggestions = _load_json_rows(suggestions_path)
    _ = _load_json_rows(review_required_path)

    if _safe_text(manifest_345c2.get("decision")) != READY_DECISION_345C2:
        raise ValueError("345C2 live manifest decision is not READY.")
    if _safe_text(manifest_345c2.get("llm_mode")).lower() != "live":
        raise ValueError("345C2 input must be live mode.")
    if int(manifest_345c2.get("suggestion_row_count") or 0) <= 0:
        raise ValueError("345C2 live suggestion_row_count must be > 0.")
    if bool(manifest_345c2.get("formal_client_export_allowed")):
        raise ValueError("345C2 live input has forbidden formal_client_export_allowed=true.")
    if bool(manifest_345c2.get("client_ready")):
        raise ValueError("345C2 live input has forbidden client_ready=true.")
    if bool(manifest_345c2.get("production_ready")):
        raise ValueError("345C2 live input has forbidden production_ready=true.")

    review_rows = build_review_rows(suggestions)
    llm_suggestion_summary = build_llm_suggestion_summary(review_rows)
    priority_summary = build_priority_summary(review_rows)

    parse_failed_count = sum(1 for row in review_rows if row.get("response_parse_status") != "PARSED")
    validation_failed_count = sum(
        1 for row in review_rows if row.get("response_validation_status") != "VALID"
    )
    llm_map_to_existing_count = sum(1 for row in review_rows if row.get("llm_suggested_action") == "MAP_TO_EXISTING_STANDARD_METRIC")
    llm_propose_new_standard_count = sum(1 for row in review_rows if row.get("llm_suggested_action") == "PROPOSE_NEW_STANDARD_METRIC")
    llm_exclude_non_core_count = sum(1 for row in review_rows if row.get("llm_suggested_action") == "EXCLUDE_NON_CORE_METRIC")
    llm_needs_human_review_count = sum(1 for row in review_rows if row.get("llm_suggested_action") == "NEEDS_HUMAN_REVIEW")
    llm_insufficient_evidence_count = sum(1 for row in review_rows if row.get("llm_suggested_action") == "INSUFFICIENT_EVIDENCE")
    llm_high_confidence_count = sum(1 for row in review_rows if _safe_text(row.get("llm_confidence")).upper() == "HIGH")
    llm_medium_confidence_count = sum(1 for row in review_rows if _safe_text(row.get("llm_confidence")).upper() == "MEDIUM")
    llm_low_confidence_count = sum(1 for row in review_rows if _safe_text(row.get("llm_confidence")).upper() == "LOW")
    generated_review_pending_count = len(review_rows)
    generated_approved_count = 0
    alias_rule_update_allowed_count = 0

    input_hashes_after = {
        str(path): sha256_file(path)
        for path in [manifest_345c2_path, suggestions_path, review_required_path]
    }
    official_assets_after = capture_official_asset_hashes(
        [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]
    )
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged_after = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    qa_checks = [
        {"check": "input_manifest_exists", "passed": manifest_345c2_path.exists()},
        {"check": "input_suggestions_exist", "passed": suggestions_path.exists()},
        {"check": "input_review_required_exists", "passed": review_required_path.exists()},
        {"check": "input_345c2_decision_ready", "passed": _safe_text(manifest_345c2.get("decision")) == READY_DECISION_345C2},
        {"check": "input_llm_mode_live", "passed": _safe_text(manifest_345c2.get("llm_mode")).lower() == "live"},
        {"check": "input_suggestion_row_count_positive", "passed": int(manifest_345c2.get("suggestion_row_count") or 0) > 0},
        {"check": "review_row_count_matches_suggestions", "passed": len(review_rows) == int(manifest_345c2.get("suggestion_row_count") or 0)},
        {"check": "all_human_review_fields_blank_by_default", "passed": all(not _safe_text(row.get("human_alias_review_decision")) and not _safe_text(row.get("approved_standard_metric")) and not _safe_text(row.get("approved_new_standard_metric")) and not _safe_text(row.get("alias_reviewer")) and not _safe_text(row.get("alias_reviewed_at")) and not _safe_text(row.get("alias_review_notes")) for row in review_rows)},
        {"check": "alias_rule_update_allowed_false", "passed": all(row.get("alias_rule_update_allowed") is False for row in review_rows)},
        {"check": "no_write_back_to_345c2_inputs", "passed": input_hashes_before == input_hashes_after},
        {"check": "official_assets_unchanged", "passed": official_assets_before == official_assets_after},
        {"check": "protected_dirty_status_unchanged", "passed": protected_before == protected_after},
        {"check": "forbidden_paths_not_staged", "passed": forbidden_staged_before == forbidden_staged_after},
        {"check": "formal_client_export_allowed_false", "passed": True},
        {"check": "client_ready_false", "passed": True},
        {"check": "production_ready_false", "passed": True},
    ]
    qa_fail_count = sum(1 for row in qa_checks if not row["passed"])

    no_apply_proof = build_no_apply_proof(
        stage="345C4",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    manifest = {
        "decision": READY_DECISION_345C4,
        "input_stage": INPUT_STAGE_345C4,
        "qa_fail_count": qa_fail_count,
        "no_write_back_proof_passed": (
            input_hashes_before == input_hashes_after
            and official_assets_before == official_assets_after
            and protected_before == protected_after
        ),
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_345c2_decision": _safe_text(manifest_345c2.get("decision")),
        "input_llm_mode": _safe_text(manifest_345c2.get("llm_mode")),
        "input_suggestion_row_count": int(manifest_345c2.get("suggestion_row_count") or 0),
        "review_row_count": len(review_rows),
        "llm_map_to_existing_count": llm_map_to_existing_count,
        "llm_propose_new_standard_count": llm_propose_new_standard_count,
        "llm_exclude_non_core_count": llm_exclude_non_core_count,
        "llm_needs_human_review_count": llm_needs_human_review_count,
        "llm_insufficient_evidence_count": llm_insufficient_evidence_count,
        "llm_high_confidence_count": llm_high_confidence_count,
        "llm_medium_confidence_count": llm_medium_confidence_count,
        "llm_low_confidence_count": llm_low_confidence_count,
        "parse_failed_count": parse_failed_count,
        "validation_failed_count": validation_failed_count,
        "generated_review_pending_count": generated_review_pending_count,
        "generated_approved_count": generated_approved_count,
        "alias_rule_update_allowed_count": alias_rule_update_allowed_count,
        "alias_apply_simulation_allowed": False,
        "generated_at_utc": _utc_now(),
        "output_dir": str(output_dir),
    }

    workbook_sheets = {
        "00_README": _clean_frame(
            pd.DataFrame(
                [
                    {
                        "section": "positioning",
                        "message": "345C4 creates a strict human review package for 345C2 live alias suggestions only.",
                    },
                    {
                        "section": "boundary",
                        "message": "No alias suggestion is approved by default and no normalization rule is changed here.",
                    },
                    {
                        "section": "decision",
                        "message": manifest["decision"],
                    },
                ]
            )
        ),
        "01_REVIEW_SUMMARY": _clean_frame(
            pd.DataFrame(
                [{"key": key, "value": _flatten_value(value)} for key, value in manifest.items()]
            )
        ),
        "02_REVIEW_ROWS": _clean_frame(pd.DataFrame(review_rows)),
        "03_DECISION_OPTIONS": _clean_frame(pd.DataFrame(build_decision_options_rows())),
        "04_REVIEWER_CHECKLIST": _clean_frame(
            pd.DataFrame(
                [
                    {
                        "line_no": index + 1,
                        "message": line,
                    }
                    for index, line in enumerate(
                        [
                            "This package is for human review of LLM alias suggestions only.",
                            "LLM suggestions are not approved by default.",
                            "Review raw metric name, frequency, source stages, sample row ids, LLM action, reason, evidence excerpt, confidence, and validation status.",
                            "Fill only the human review fields.",
                            "Do not edit LLM evidence fields or source fields.",
                            "This task does not modify normalization rules or official alias assets.",
                            "345C5 or later should ingest reviewed decisions.",
                        ]
                    )
                ]
            )
        ),
        "05_LLM_SUGGESTION_SUM": _clean_frame(pd.DataFrame(llm_suggestion_summary)),
        "06_PRIORITY_SUMMARY": _clean_frame(pd.DataFrame(priority_summary)),
        "07_NO_WRITE_BACK": _clean_frame(
            pd.DataFrame(
                [{"key": key, "value": _flatten_value(value)} for key, value in no_apply_proof.items()]
            )
        ),
        "08_NEXT_STEPS": _clean_frame(
            pd.DataFrame(
                [
                    {"step": "345C5 Reviewed Alias Decision Ingestion"},
                    {"step": "345C6 Reviewed Alias Apply Simulation"},
                    {"step": "345D Full Structured Demo Export Package only after reviewed alias impact is measured"},
                    {"step": "344G still waits for a genuinely human-filled 344F workbook"},
                ]
            )
        ),
    }

    return {
        "manifest": manifest,
        "review_rows": review_rows,
        "llm_suggestion_summary": llm_suggestion_summary,
        "priority_summary": priority_summary,
        "no_apply_proof": no_apply_proof,
        "qa_json": {
            "decision": manifest["decision"],
            "qa_fail_count": qa_fail_count,
            "checks": qa_checks,
        },
        "workbook_sheets": workbook_sheets,
        "artifact_index_rows": _artifact_rows(output_dir),
    }
