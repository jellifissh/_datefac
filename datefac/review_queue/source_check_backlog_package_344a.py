from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

from datefac.review_queue.excel_round_trip_343b import normalize_bool, normalize_text
from datefac.review_queue.ingest_strict_review_343j import FORBIDDEN_STAGE_PATHS, PROTECTED_DIRTY_PATHS
from datefac.review_queue.demo_audit_snapshot_343o import READY_DECISION_343O
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


WAITING_DECISION_344A = "SOURCE_CHECK_BACKLOG_PACKAGE_344A_WAITING_FOR_SOURCE_CHECK_REVIEW"
NOT_READY_DECISION_344A = "SOURCE_CHECK_BACKLOG_PACKAGE_344A_NOT_READY"
RECOMMENDED_344B_SCOPE_344A = "source_check_backlog_result_ingestion_after_user_fills_workbook"

EVIDENCE_RESOLUTION_RESOLVED = "RESOLVED"
EVIDENCE_RESOLUTION_PARTIAL = "PARTIAL"
EVIDENCE_RESOLUTION_UNRESOLVED = "UNRESOLVED"

ALLOWED_SOURCE_CHECK_DECISIONS = [
    "SOURCE_CONFIRM",
    "SOURCE_CORRECT",
    "SOURCE_REJECT",
    "SOURCE_STILL_INSUFFICIENT",
    "SOURCE_DEFER",
]

REQUIRED_IDENTITY_COLUMNS_344A = [
    "queue_item_id",
    "review_item_id",
    "backlog_item_key",
    "source_status",
    "priority_tier",
]

EVIDENCE_COLUMNS_344A = [
    "source_pdf_name",
    "source_pdf_path",
    "source_pdf_id",
    "page_number",
    "table_id",
    "cell_id",
    "bbox",
    "image_path",
    "source_text_snippet",
    "source_html_snippet",
    "metric_candidate_raw",
    "metric_standardized",
    "year_standardized",
    "value_numeric",
    "normalized_unit",
    "evidence_source_stage",
    "evidence_source_artifact",
    "evidence_resolution_status",
    "evidence_gap_reason",
]

EDITABLE_SOURCE_CHECK_COLUMNS_344A = [
    "source_check_decision",
    "source_check_metric_standardized",
    "source_check_year_standardized",
    "source_check_value_numeric",
    "source_check_normalized_unit",
    "source_check_note",
    "source_checker_id",
    "source_checked_at",
    "source_evidence_checked",
    "source_evidence_sufficient",
]

SOURCE_CORRECT_REQUIRED_COLUMNS_344A = [
    "source_check_metric_standardized",
    "source_check_year_standardized",
    "source_check_value_numeric",
    "source_check_normalized_unit",
]

WORKBOOK_SHEETS_344A = [
    "00_README",
    "01_PACKAGE_SUMMARY",
    "02_INPUT_343O_SUMMARY",
    "03_BACKLOG_ITEMS",
    "04_REVIEW_TEMPLATE",
    "05_EVIDENCE_MAP",
    "06_DECISION_RULES",
    "07_IMPORT_CONTRACT",
    "08_SCOPE_BOUNDARY",
    "09_NO_WRITE_BACK",
    "10_NEXT_STEPS",
]

TEMPLATE_WORKBOOK_SHEETS_344A = [
    "00_README",
    "04_REVIEW_TEMPLATE",
    "06_DECISION_RULES",
    "07_IMPORT_CONTRACT",
    "08_SCOPE_BOUNDARY",
    "10_NEXT_STEPS",
]

INPUT_343O_SUMMARY_NAME = "review_queue_demo_audit_snapshot_343o_summary.json"
INPUT_343O_QA_NAME = "review_queue_demo_audit_snapshot_343o_qa.json"
INPUT_343O_BACKLOG_SUMMARY_NAME = "review_queue_demo_audit_snapshot_343o_backlog_summary.json"
INPUT_343O_EXPORT_GATE_SNAPSHOT_NAME = "review_queue_demo_audit_snapshot_343o_export_gate_snapshot.json"
INPUT_343O_NEXT_ACTION_PLAN_NAME = "review_queue_demo_audit_snapshot_343o_next_action_plan.json"
INPUT_343O_NO_WRITE_BACK_NAME = "review_queue_demo_audit_snapshot_343o_no_write_back_proof.json"

INPUT_343N_REMAINING_BACKLOG_NAME = "review_queue_limited_demo_export_package_343n_remaining_backlog.jsonl"
INPUT_343N_SCOPE_BOUNDARY_NAME = "review_queue_limited_demo_export_package_343n_scope_boundary.md"
INPUT_343M_REMAINING_BACKLOG_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_remaining_backlog.jsonl"
INPUT_343M_GATE_NAME = "review_queue_human_confirmed_sidecar_simulation_343m_limited_export_gate.json"
INPUT_343H_BACKLOG_NAME = "review_queue_audit_summary_343h_source_check_backlog.jsonl"
INPUT_343H_GAP_ITEMS_NAME = "review_queue_audit_summary_343h_gap_items.jsonl"
INPUT_343H_SUMMARY_NAME = "review_queue_audit_summary_343h_summary.json"
INPUT_343H_GAP_REPORT_NAME = "review_queue_audit_summary_343h_strict_human_gap_report.md"
INPUT_343G_RESULT_NAME = "review_queue_spot_check_ingestion_343g_result.jsonl"
INPUT_343F_TODO_NAME = "review_queue_spot_check_package_343f_source_check_todo.jsonl"
INPUT_343F_SUMMARY_NAME = "review_queue_spot_check_package_343f_summary.json"
INPUT_343A_SCHEMA_NAME = "review_queue_schema_343a_schema.json"
INPUT_343A_SUMMARY_NAME = "review_queue_schema_343a_summary.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _flatten_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return normalize_text(value)


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    rows = [{"key": key, "value": _flatten_value(value)} for key, value in mapping.items()]
    return _clean_frame(pd.DataFrame(rows))


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def _build_readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    return _clean_frame(
        pd.DataFrame(
            [
                {
                    "section": "positioning",
                    "message": "344A packages the remaining source-check backlog rows for reviewer follow-up after the 343O demo arc closed.",
                },
                {
                    "section": "scope",
                    "message": "344A works only on backlog rows outside the 10-row trusted demo package.",
                },
                {
                    "section": "boundary",
                    "message": "This package is waiting for review input and is not a formal client export or production artifact.",
                },
                {
                    "section": "decision",
                    "message": summary.get("decision", ""),
                },
            ]
        )
    )


def _stable_backlog_key(row: Dict[str, Any]) -> str:
    queue_item_id = normalize_text(row.get("queue_item_id"))
    review_item_id = normalize_text(row.get("review_item_id"))
    if queue_item_id or review_item_id:
        return f"{queue_item_id}::{review_item_id}"
    return "fallback::" + "::".join(
        [
            normalize_text(row.get("metric_standardized")),
            normalize_text(row.get("year_standardized")),
            normalize_text(row.get("value_numeric")),
            normalize_text(row.get("source_pdf_name")),
            normalize_text(row.get("page_number")),
        ]
    )


def _classify_evidence_resolution(item: Dict[str, Any]) -> tuple[str, str]:
    has_pdf_name = normalize_text(item.get("source_pdf_name")) != ""
    has_pdf_path = normalize_text(item.get("source_pdf_path")) != ""
    has_pdf_id = normalize_text(item.get("source_pdf_id")) != ""
    has_page = normalize_text(item.get("page_number")) != ""
    has_locator = any(
        normalize_text(item.get(field)) != ""
        for field in ["table_id", "cell_id", "bbox", "image_path", "source_text_snippet", "source_html_snippet"]
    )
    if (has_pdf_name or has_pdf_path or has_pdf_id) and has_page and has_locator:
        return (EVIDENCE_RESOLUTION_RESOLVED, "")
    if any(
        normalize_text(item.get(field)) != ""
        for field in ["source_pdf_name", "source_pdf_path", "source_pdf_id", "page_number", "table_id", "cell_id", "bbox", "image_path", "source_text_snippet", "source_html_snippet"]
    ):
        missing: List[str] = []
        if not (has_pdf_name or has_pdf_path or has_pdf_id):
            missing.append("source_pdf locator")
        if not has_page:
            missing.append("page_number")
        if not has_locator:
            missing.append("table/cell/snippet locator")
        return (
            EVIDENCE_RESOLUTION_PARTIAL,
            "missing key source locator fields: " + ", ".join(missing),
        )
    return (
        EVIDENCE_RESOLUTION_UNRESOLVED,
        "source evidence not available in selected backlog artifact",
    )


def _merge_prefer_existing(base: Dict[str, Any], update: Dict[str, Any], fields: Iterable[str]) -> None:
    for field in fields:
        if normalize_text(base.get(field)) == "" and normalize_text(update.get(field)) != "":
            base[field] = update.get(field)


def _init_backlog_item(row: Dict[str, Any], source_name: str, artifact_path: Path) -> Dict[str, Any]:
    item = {
        "backlog_item_key": _stable_backlog_key(row),
        "queue_item_id": normalize_text(row.get("queue_item_id")),
        "review_item_id": normalize_text(row.get("review_item_id")),
        "source_status": normalize_text(row.get("resulting_spot_check_status"))
        or normalize_text(row.get("resulting_status"))
        or normalize_text(row.get("spot_check_decision"))
        or normalize_text(row.get("suggested_action"))
        or "SOURCE_CHECK_REQUIRED",
        "priority_tier": normalize_text(row.get("priority_tier")) or "P0_SOURCE_CHECK_REQUIRED",
        "backlog_reason": normalize_text(row.get("reason"))
        or normalize_text(row.get("reason_for_source_check"))
        or normalize_text(row.get("gap_reason"))
        or normalize_text(row.get("spot_check_note")),
        "review_source_type": normalize_text(row.get("review_source_type")) or "AI_ASSISTED_REVIEW",
        "spot_check_source_type": normalize_text(row.get("spot_check_source_type")) or "AI_ASSISTED_SPOT_CHECK",
        "not_pure_human_review": normalize_bool(row.get("not_pure_human_review", True)),
        "strict_human_review_completed": normalize_bool(row.get("strict_human_review_completed", False)),
        "requires_strict_human_review": normalize_bool(row.get("requires_strict_human_review", True)),
        "requires_human_spot_check": normalize_bool(row.get("requires_human_spot_check", True)),
        "apply_mode": normalize_text(row.get("apply_mode")) or "SIMULATION_ONLY",
        "source_pdf_name": normalize_text(row.get("source_pdf_name")),
        "source_pdf_path": normalize_text(row.get("source_pdf_path")),
        "source_pdf_id": normalize_text(row.get("source_pdf_id")),
        "page_number": row.get("page_number", ""),
        "table_id": normalize_text(row.get("table_id")),
        "cell_id": normalize_text(row.get("cell_id")),
        "bbox": normalize_text(row.get("bbox")),
        "image_path": normalize_text(row.get("image_path")),
        "source_text_snippet": normalize_text(row.get("source_text_snippet")),
        "source_html_snippet": normalize_text(row.get("source_html_snippet")),
        "metric_candidate_raw": normalize_text(row.get("metric_candidate_raw")),
        "metric_standardized": normalize_text(row.get("metric_standardized"))
        or normalize_text(row.get("final_metric_standardized")),
        "year_standardized": normalize_text(row.get("year_standardized"))
        or normalize_text(row.get("final_year_standardized")),
        "value_numeric": row.get("value_numeric", row.get("final_value_numeric", "")),
        "normalized_unit": normalize_text(row.get("normalized_unit"))
        or normalize_text(row.get("final_normalized_unit")),
        "evidence_source_stage": source_name,
        "evidence_source_artifact": str(artifact_path),
        "source_artifact_path": normalize_text(row.get("source_artifact_path")),
        "source_artifact_sheet": normalize_text(row.get("source_artifact_sheet")),
        "source_row_id": normalize_text(row.get("source_row_id")),
        "backlog_sources": [source_name],
        "source_check_decision": "",
        "source_check_metric_standardized": "",
        "source_check_year_standardized": "",
        "source_check_value_numeric": "",
        "source_check_normalized_unit": "",
        "source_check_note": "",
        "source_checker_id": "",
        "source_checked_at": "",
        "source_evidence_checked": "",
        "source_evidence_sufficient": "",
    }
    status, gap_reason = _classify_evidence_resolution(item)
    item["evidence_resolution_status"] = status
    item["evidence_gap_reason"] = gap_reason
    return item


def _merge_backlog_item(base: Dict[str, Any], row: Dict[str, Any], source_name: str, artifact_path: Path) -> None:
    _merge_prefer_existing(
        base,
        {
            "source_status": normalize_text(row.get("resulting_spot_check_status"))
            or normalize_text(row.get("resulting_status"))
            or normalize_text(row.get("spot_check_decision"))
            or normalize_text(row.get("suggested_action")),
            "priority_tier": normalize_text(row.get("priority_tier")),
            "backlog_reason": normalize_text(row.get("reason"))
            or normalize_text(row.get("reason_for_source_check"))
            or normalize_text(row.get("gap_reason"))
            or normalize_text(row.get("spot_check_note")),
            "source_pdf_name": normalize_text(row.get("source_pdf_name")),
            "source_pdf_path": normalize_text(row.get("source_pdf_path")),
            "source_pdf_id": normalize_text(row.get("source_pdf_id")),
            "page_number": row.get("page_number", ""),
            "table_id": normalize_text(row.get("table_id")),
            "cell_id": normalize_text(row.get("cell_id")),
            "bbox": normalize_text(row.get("bbox")),
            "image_path": normalize_text(row.get("image_path")),
            "source_text_snippet": normalize_text(row.get("source_text_snippet")),
            "source_html_snippet": normalize_text(row.get("source_html_snippet")),
            "metric_candidate_raw": normalize_text(row.get("metric_candidate_raw")),
            "metric_standardized": normalize_text(row.get("metric_standardized"))
            or normalize_text(row.get("final_metric_standardized")),
            "year_standardized": normalize_text(row.get("year_standardized"))
            or normalize_text(row.get("final_year_standardized")),
            "value_numeric": row.get("value_numeric", row.get("final_value_numeric", "")),
            "normalized_unit": normalize_text(row.get("normalized_unit"))
            or normalize_text(row.get("final_normalized_unit")),
            "source_artifact_path": normalize_text(row.get("source_artifact_path")),
            "source_artifact_sheet": normalize_text(row.get("source_artifact_sheet")),
            "source_row_id": normalize_text(row.get("source_row_id")),
        },
        [
            "source_status",
            "priority_tier",
            "backlog_reason",
            "source_pdf_name",
            "source_pdf_path",
            "source_pdf_id",
            "page_number",
            "table_id",
            "cell_id",
            "bbox",
            "image_path",
            "source_text_snippet",
            "source_html_snippet",
            "metric_candidate_raw",
            "metric_standardized",
            "year_standardized",
            "value_numeric",
            "normalized_unit",
            "source_artifact_path",
            "source_artifact_sheet",
            "source_row_id",
        ],
    )
    if source_name not in base["backlog_sources"]:
        base["backlog_sources"].append(source_name)
    if normalize_text(base.get("evidence_source_artifact")) == "":
        base["evidence_source_artifact"] = str(artifact_path)
    if normalize_text(base.get("evidence_source_stage")) == "":
        base["evidence_source_stage"] = source_name
    status, gap_reason = _classify_evidence_resolution(base)
    base["evidence_resolution_status"] = status
    base["evidence_gap_reason"] = gap_reason


def _build_backlog_items(
    source_rows_by_name: List[tuple[str, Path, List[Dict[str, Any]]]],
) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    items_by_key: Dict[str, Dict[str, Any]] = {}
    counts_by_source: Dict[str, int] = {}
    for source_name, artifact_path, rows in source_rows_by_name:
        counts_by_source[source_name] = len(rows)
        for row in rows:
            key = _stable_backlog_key(row)
            if key not in items_by_key:
                items_by_key[key] = _init_backlog_item(row, source_name, artifact_path)
            else:
                _merge_backlog_item(items_by_key[key], row, source_name, artifact_path)
    return (
        sorted(items_by_key.values(), key=lambda item: (item.get("queue_item_id", ""), item.get("review_item_id", ""))),
        counts_by_source,
    )


def _build_decision_rule_rows() -> List[Dict[str, Any]]:
    return [
        {
            "decision": "SOURCE_CONFIRM",
            "required_fields": "source_checker_id, source_checked_at, source_evidence_checked=true, source_evidence_sufficient=true",
            "notes": "Use only when source evidence is sufficient and the row can be confirmed without correction.",
        },
        {
            "decision": "SOURCE_CORRECT",
            "required_fields": ", ".join(SOURCE_CORRECT_REQUIRED_COLUMNS_344A + ["source_check_note", "source_checker_id", "source_checked_at"]),
            "notes": "Corrected metric/year/value/unit are mandatory.",
        },
        {
            "decision": "SOURCE_REJECT",
            "required_fields": "source_check_note, source_checker_id, source_checked_at, source_evidence_checked=true",
            "notes": "Use when evidence disproves the row or confirms it should be excluded.",
        },
        {
            "decision": "SOURCE_STILL_INSUFFICIENT",
            "required_fields": "source_check_note, source_checker_id, source_checked_at",
            "notes": "Use when evidence remains insufficient after review.",
        },
        {
            "decision": "SOURCE_DEFER",
            "required_fields": "source_checker_id, source_checked_at",
            "notes": "Use when the row should be deferred for later follow-up.",
        },
    ]


def _build_expected_import_contract(review_queue_schema_version: str) -> Dict[str, Any]:
    return {
        "contract_version": "344A.source_check_backlog.v1",
        "source_review_queue_schema_version": review_queue_schema_version,
        "required_sheet_name": "04_REVIEW_TEMPLATE",
        "required_identity_columns": REQUIRED_IDENTITY_COLUMNS_344A,
        "source_evidence_columns": EVIDENCE_COLUMNS_344A,
        "editable_source_check_columns": EDITABLE_SOURCE_CHECK_COLUMNS_344A,
        "allowed_source_check_decisions": ALLOWED_SOURCE_CHECK_DECISIONS,
        "source_correct_required_columns": SOURCE_CORRECT_REQUIRED_COLUMNS_344A,
        "expected_input_path_pattern": "D:/_datefac/input/review_queue_source_check_backlog_344a_filled/*.xlsx",
        "waiting_for_source_check_review": True,
        "source_check_result_ingested": False,
        "recommended_output_dir_hint": r"D:\_datefac\output\review_queue_source_check_backlog_package_344a",
    }


def _build_scope_boundary_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 344A Scope Boundary",
            "",
            "## 中文说明",
            "- 344A 只处理 343O 之外剩余的 19 条 source-check backlog。",
            "- 343O 的 10-row demo arc 已经闭合，这里不会回写或修改它。",
            "- 当前只生成待填写模板，不导入结果，不做正式导出，也不做真实写回。",
            "",
            "## Current Boundary",
            f"- source_check_backlog_item_count: {summary.get('source_check_backlog_item_count', 0)}",
            f"- source_check_result_ingested: {summary.get('source_check_result_ingested', False)}",
            f"- source_check_backlog_resolved: {summary.get('source_check_backlog_resolved', False)}",
            f"- formal_client_export_allowed: {summary.get('formal_client_export_allowed', False)}",
            f"- client_ready: {summary.get('client_ready', False)}",
            f"- production_ready: {summary.get('production_ready', False)}",
        ]
    )


def _build_reviewer_instructions_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 344A Reviewer Instructions",
            "",
            "## 中文说明",
            "- 这个包只用于处理剩余的 19 条 source-check backlog。",
            "- 343O 的 10-row trusted demo package 已经闭合，不在本包中修改。",
            "- 请优先查看证据定位字段；如果源证据仍然不足，请明确填 `SOURCE_STILL_INSUFFICIENT` 或 `SOURCE_DEFER`。",
            "- `SOURCE_CORRECT` 必须补全 corrected metric/year/value/unit，并写明说明。",
            "- formal client export 仍被禁止，当前任何结论都只是 backlog review 输入。",
            f"- 填写后请保存到 `D:/_datefac/input/review_queue_source_check_backlog_344a_filled/`，供后续 344B 导入。",
            "",
            "## English Note",
            "- This package resolves the 19 remaining source-check backlog rows only.",
            "- Do not treat this as a formal export approval step.",
        ]
    )


def _build_fill_guide_markdown() -> str:
    return "\n".join(
        [
            "# 344A Fill Guide",
            "",
            "## 中文步骤",
            "1. 打开 `04_REVIEW_TEMPLATE`。",
            "2. 先看 `source_pdf_* / page_number / table_id / bbox / image_path / source_*_snippet`。",
            "3. 根据证据填写 `source_check_decision`。",
            "4. 如选 `SOURCE_CORRECT`，必须补全 corrected metric/year/value/unit。",
            "5. 填写 `source_checker_id`、`source_checked_at`，并根据实际情况填 `source_evidence_checked` / `source_evidence_sufficient`。",
            "6. 不要修改 identity 字段。",
            "",
            "## Allowed Decisions",
            "- SOURCE_CONFIRM",
            "- SOURCE_CORRECT",
            "- SOURCE_REJECT",
            "- SOURCE_STILL_INSUFFICIENT",
            "- SOURCE_DEFER",
        ]
    )


def _build_next_steps_rows() -> List[Dict[str, str]]:
    return [
        {
            "step": "open_review_template",
            "recommendation": "Open the 344A review template workbook and inspect evidence resolution status first.",
        },
        {
            "step": "resolve_source_backlog",
            "recommendation": "Fill source_check_decision fields conservatively; unresolved evidence should remain unresolved rather than guessed.",
        },
        {
            "step": "save_filled_copy_for_344b",
            "recommendation": "Save the filled workbook under D:/_datefac/input/review_queue_source_check_backlog_344a_filled/ for later 344B ingestion.",
        },
    ]


def _build_evidence_map(items: List[Dict[str, Any]], counts_by_source: Dict[str, int]) -> Dict[str, Any]:
    rows = []
    for item in items:
        rows.append(
            {
                "backlog_item_key": item.get("backlog_item_key", ""),
                "queue_item_id": item.get("queue_item_id", ""),
                "review_item_id": item.get("review_item_id", ""),
                "evidence_resolution_status": item.get("evidence_resolution_status", ""),
                "evidence_gap_reason": item.get("evidence_gap_reason", ""),
                "source_pdf_name": item.get("source_pdf_name", ""),
                "page_number": item.get("page_number", ""),
                "table_id": item.get("table_id", ""),
                "image_path": item.get("image_path", ""),
                "backlog_sources": item.get("backlog_sources", []),
            }
        )
    return {
        "counts_by_source": counts_by_source,
        "resolved_count": sum(1 for item in items if item.get("evidence_resolution_status") == EVIDENCE_RESOLUTION_RESOLVED),
        "partial_count": sum(1 for item in items if item.get("evidence_resolution_status") == EVIDENCE_RESOLUTION_PARTIAL),
        "unresolved_count": sum(1 for item in items if item.get("evidence_resolution_status") == EVIDENCE_RESOLUTION_UNRESOLVED),
        "items": rows,
    }


def build_review_queue_source_check_backlog_package_344a(
    *,
    demo_audit_snapshot_343o_dir: Path,
    limited_demo_export_package_343n_dir: Path,
    human_confirmed_sidecar_simulation_343m_dir: Path,
    audit_summary_343h_dir: Path,
    spot_check_ingestion_343g_dir: Path,
    spot_check_package_343f_dir: Path,
    review_queue_schema_343a_dir: Path,
    output_dir: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    required_input_paths = [
        demo_audit_snapshot_343o_dir / INPUT_343O_SUMMARY_NAME,
        demo_audit_snapshot_343o_dir / INPUT_343O_QA_NAME,
        demo_audit_snapshot_343o_dir / INPUT_343O_BACKLOG_SUMMARY_NAME,
        demo_audit_snapshot_343o_dir / INPUT_343O_EXPORT_GATE_SNAPSHOT_NAME,
        demo_audit_snapshot_343o_dir / INPUT_343O_NEXT_ACTION_PLAN_NAME,
        demo_audit_snapshot_343o_dir / INPUT_343O_NO_WRITE_BACK_NAME,
        human_confirmed_sidecar_simulation_343m_dir / INPUT_343M_REMAINING_BACKLOG_NAME,
        limited_demo_export_package_343n_dir / INPUT_343N_REMAINING_BACKLOG_NAME,
        audit_summary_343h_dir / INPUT_343H_BACKLOG_NAME,
        spot_check_ingestion_343g_dir / INPUT_343G_RESULT_NAME,
        spot_check_package_343f_dir / INPUT_343F_TODO_NAME,
        review_queue_schema_343a_dir / INPUT_343A_SCHEMA_NAME,
        review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME,
    ]

    files_read: List[str] = []
    missing_required_inputs: List[str] = []
    for path in required_input_paths:
        if path.exists():
            files_read.append(str(path))
        else:
            missing_required_inputs.append(str(path))

    summary_343o = _read_json(demo_audit_snapshot_343o_dir / INPUT_343O_SUMMARY_NAME)
    qa_343o = _read_json(demo_audit_snapshot_343o_dir / INPUT_343O_QA_NAME)
    backlog_summary_343o = _read_json(demo_audit_snapshot_343o_dir / INPUT_343O_BACKLOG_SUMMARY_NAME)
    export_gate_snapshot_343o = _read_json(demo_audit_snapshot_343o_dir / INPUT_343O_EXPORT_GATE_SNAPSHOT_NAME)
    next_action_plan_343o = _read_json(demo_audit_snapshot_343o_dir / INPUT_343O_NEXT_ACTION_PLAN_NAME)
    summary_343h = _read_json(audit_summary_343h_dir / INPUT_343H_SUMMARY_NAME)
    summary_343f = _read_json(spot_check_package_343f_dir / INPUT_343F_SUMMARY_NAME)
    gate_343m = _read_json(human_confirmed_sidecar_simulation_343m_dir / INPUT_343M_GATE_NAME)
    summary_343a = _read_json(review_queue_schema_343a_dir / INPUT_343A_SUMMARY_NAME)
    gap_report_343h = _read_text(audit_summary_343h_dir / INPUT_343H_GAP_REPORT_NAME)
    scope_boundary_343n = _read_text(limited_demo_export_package_343n_dir / INPUT_343N_SCOPE_BOUNDARY_NAME)

    source_rows_by_name: List[tuple[str, Path, List[Dict[str, Any]]]] = []
    for source_name, artifact_path in [
        ("343M_REMAINING_BACKLOG", human_confirmed_sidecar_simulation_343m_dir / INPUT_343M_REMAINING_BACKLOG_NAME),
        ("343N_REMAINING_BACKLOG", limited_demo_export_package_343n_dir / INPUT_343N_REMAINING_BACKLOG_NAME),
        ("343H_SOURCE_BACKLOG", audit_summary_343h_dir / INPUT_343H_BACKLOG_NAME),
        ("343F_SOURCE_TODO", spot_check_package_343f_dir / INPUT_343F_TODO_NAME),
        ("343H_GAP_ITEMS", audit_summary_343h_dir / INPUT_343H_GAP_ITEMS_NAME),
        ("343G_RESULT", spot_check_ingestion_343g_dir / INPUT_343G_RESULT_NAME),
    ]:
        if artifact_path.exists():
            rows = _read_jsonl(artifact_path)
            if source_name == "343H_GAP_ITEMS":
                rows = [row for row in rows if normalize_text(row.get("gap_category")) == "SOURCE_CHECK_BACKLOG"]
            if source_name == "343G_RESULT":
                rows = [row for row in rows if normalize_text(row.get("resulting_status")) == "NEEDS_SOURCE_CHECK"]
            source_rows_by_name.append((source_name, artifact_path, rows))
            files_read.append(str(artifact_path))

    input_hashes_before = {str(path): sha256_file(path) for path in required_input_paths if path.exists()}

    input_ready = bool(
        not missing_required_inputs
        and summary_343o.get("decision") == READY_DECISION_343O
        and int(summary_343o.get("qa_fail_count", 1)) == 0
        and normalize_bool(summary_343o.get("demo_arc_closed"))
        and int(summary_343o.get("remaining_source_check_backlog_count", -1)) == 19
        and not normalize_bool(summary_343o.get("formal_client_export_allowed"))
        and not normalize_bool(summary_343o.get("client_ready"))
        and not normalize_bool(summary_343o.get("production_ready"))
        and not normalize_bool(summary_343o.get("global_strict_human_review_completed"))
        and normalize_bool(summary_343o.get("ready_for_344a"))
        and not normalize_bool(export_gate_snapshot_343o.get("formal_client_export_allowed"))
        and not normalize_bool(gate_343m.get("formal_client_export_allowed"))
    )

    backlog_items, counts_by_source = _build_backlog_items(source_rows_by_name)
    evidence_map = _build_evidence_map(backlog_items, counts_by_source)

    input_remaining_source_check_backlog_count = int(summary_343o.get("remaining_source_check_backlog_count", 0))
    source_check_backlog_item_count = len(backlog_items)
    deduplicated_backlog_item_count = len(backlog_items)
    evidence_resolved_count = evidence_map["resolved_count"]
    evidence_partial_count = evidence_map["partial_count"]
    evidence_unresolved_count = evidence_map["unresolved_count"]
    source_pdf_name_available_count = sum(1 for item in backlog_items if normalize_text(item.get("source_pdf_name")) != "")
    source_text_snippet_available_count = sum(1 for item in backlog_items if normalize_text(item.get("source_text_snippet")) != "")

    warnings: List[str] = []
    if counts_by_source and len(set(counts_by_source.values())) > 1:
        warnings.append(f"backlog source count mismatch: {counts_by_source}")
    if deduplicated_backlog_item_count != input_remaining_source_check_backlog_count:
        warnings.append(
            f"deduplicated backlog count {deduplicated_backlog_item_count} does not match 343O remaining backlog count {input_remaining_source_check_backlog_count}"
        )

    summary = {
        "generated_at_utc": _utc_now(),
        "source_milestone": "343O",
        "decision": NOT_READY_DECISION_344A,
        "review_queue_schema_version": summary_343a.get("review_queue_schema_version", ""),
        "input_remaining_source_check_backlog_count": input_remaining_source_check_backlog_count,
        "source_check_backlog_item_count": source_check_backlog_item_count,
        "deduplicated_backlog_item_count": deduplicated_backlog_item_count,
        "evidence_resolved_count": evidence_resolved_count,
        "evidence_partial_count": evidence_partial_count,
        "evidence_unresolved_count": evidence_unresolved_count,
        "source_pdf_name_available_count": source_pdf_name_available_count,
        "source_text_snippet_available_count": source_text_snippet_available_count,
        "source_check_backlog_package_generated": False,
        "review_template_generated": False,
        "reviewer_instructions_generated": False,
        "fill_guide_generated": False,
        "expected_import_contract_generated": False,
        "waiting_for_source_check_review": False,
        "source_check_result_ingested": False,
        "source_check_backlog_resolved": False,
        "demo_arc_closed": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "ready_for_344b": False,
        "recommended_344b_scope": RECOMMENDED_344B_SCOPE_344A,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "output_directory": str(output_dir),
    }

    expected_import_contract = _build_expected_import_contract(summary["review_queue_schema_version"])
    scope_boundary_markdown = _build_scope_boundary_markdown(summary)
    reviewer_instructions_markdown = _build_reviewer_instructions_markdown(summary)
    fill_guide_markdown = _build_fill_guide_markdown()

    official_assets_after = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    input_hashes_after = {str(path): sha256_file(path) for path in required_input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="344A",
        files_read=list(dict.fromkeys(files_read)),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["real_production_apply_performed"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_344a")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
        and not no_write_back_json.get("real_production_apply_performed", True)
    )

    checks = [
        {
            "check_name": "inputs::343o_input_exists_and_ready",
            "status": "PASS" if input_ready else "FAIL",
            "detail": json.dumps(
                {
                    "missing_required_inputs": missing_required_inputs,
                    "decision": summary_343o.get("decision", ""),
                    "qa_fail_count": summary_343o.get("qa_fail_count", 0),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "inputs::backlog_source_exists_and_is_readable",
            "status": "PASS" if source_rows_by_name else "FAIL",
            "detail": json.dumps({name: count for name, count in counts_by_source.items()}, ensure_ascii=False),
        },
        {
            "check_name": "counts::deduplicated_backlog_count_matches_expected_19",
            "status": "PASS" if deduplicated_backlog_item_count == 19 else "FAIL",
            "detail": json.dumps(
                {
                    "input_remaining_source_check_backlog_count": input_remaining_source_check_backlog_count,
                    "deduplicated_backlog_item_count": deduplicated_backlog_item_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "identity::every_backlog_item_has_identity_or_fallback_key",
            "status": "PASS" if all(normalize_text(item.get("backlog_item_key")) != "" for item in backlog_items) else "FAIL",
            "detail": "All backlog items must have stable keys",
        },
        {
            "check_name": "evidence::every_backlog_item_has_evidence_resolution_status",
            "status": "PASS" if all(normalize_text(item.get("evidence_resolution_status")) != "" for item in backlog_items) else "FAIL",
            "detail": json.dumps(
                {
                    "resolved": evidence_resolved_count,
                    "partial": evidence_partial_count,
                    "unresolved": evidence_unresolved_count,
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "evidence::unresolved_evidence_explicitly_disclosed",
            "status": "PASS" if all(normalize_text(item.get("evidence_gap_reason")) != "" for item in backlog_items if item.get("evidence_resolution_status") == EVIDENCE_RESOLUTION_UNRESOLVED) else "FAIL",
            "detail": "UNRESOLVED items must disclose evidence_gap_reason",
        },
        {
            "check_name": "outputs::review_template_generated",
            "status": "PASS" if bool(backlog_items) else "FAIL",
            "detail": "review template rows prepared from deduplicated backlog items",
        },
        {
            "check_name": "outputs::reviewer_instructions_generated",
            "status": "PASS" if bool(reviewer_instructions_markdown.strip()) else "FAIL",
            "detail": "reviewer instructions markdown generated",
        },
        {
            "check_name": "outputs::fill_guide_generated",
            "status": "PASS" if bool(fill_guide_markdown.strip()) else "FAIL",
            "detail": "fill guide markdown generated",
        },
        {
            "check_name": "outputs::expected_import_contract_generated",
            "status": "PASS" if bool(expected_import_contract) else "FAIL",
            "detail": json.dumps(expected_import_contract, ensure_ascii=False),
        },
        {
            "check_name": "template::editable_source_check_columns_exist",
            "status": (
                "PASS"
                if backlog_items and all(field in backlog_items[0] for field in EDITABLE_SOURCE_CHECK_COLUMNS_344A)
                else "FAIL"
            ),
            "detail": json.dumps(EDITABLE_SOURCE_CHECK_COLUMNS_344A, ensure_ascii=False),
        },
        {
            "check_name": "template::allowed_source_check_decision_list_exists",
            "status": "PASS" if bool(ALLOWED_SOURCE_CHECK_DECISIONS) else "FAIL",
            "detail": json.dumps(ALLOWED_SOURCE_CHECK_DECISIONS, ensure_ascii=False),
        },
        {
            "check_name": "template::source_check_decisions_not_prefilled_as_completed",
            "status": "PASS" if all(normalize_text(item.get("source_check_decision")) == "" for item in backlog_items) else "FAIL",
            "detail": "source_check_decision must remain blank",
        },
        {
            "check_name": "state::waiting_for_source_check_review_true",
            "status": "PASS",
            "detail": "344A is intentionally a waiting-for-review package",
        },
        {
            "check_name": "state::source_check_result_ingested_false",
            "status": "PASS",
            "detail": "344A must not ingest source-check results",
        },
        {
            "check_name": "state::source_check_backlog_resolved_false",
            "status": "PASS",
            "detail": "backlog remains unresolved until a later ingestion step",
        },
        {
            "check_name": "claims::formal_client_production_flags_remain_false",
            "status": "PASS"
            if not normalize_bool(summary_343o.get("formal_client_export_allowed"))
            and not normalize_bool(summary_343o.get("client_ready"))
            and not normalize_bool(summary_343o.get("production_ready"))
            else "FAIL",
            "detail": "formal_client_export_allowed/client_ready/production_ready must remain false",
        },
        {
            "check_name": "safety::343o_demo_arc_not_modified",
            "status": "PASS" if normalize_bool(summary_343o.get("demo_arc_closed")) else "FAIL",
            "detail": "344A must leave 343O demo arc closed and unchanged",
        },
        {
            "check_name": "safety::no_formal_client_export_workbook_generated",
            "status": "PASS",
            "detail": "344A generates only a backlog review package and template workbook.",
        },
        {
            "check_name": "safety::no_argilla_call_made",
            "status": "PASS",
            "detail": "344A is review packaging only and does not import or call Argilla.",
        },
        {
            "check_name": "safety::no_real_production_apply_performed",
            "status": "PASS",
            "detail": "344A does not write back or perform production apply.",
        },
        {
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if upstream_unchanged else "FAIL",
            "detail": "input hashes before/after compared",
        },
        {
            "check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified",
            "status": "PASS",
            "detail": "344A adds review-queue backlog package files only.",
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
            "check_name": "safety::forbidden_output_or_input_artifacts_not_staged",
            "status": "PASS" if not forbidden_staged else "FAIL",
            "detail": json.dumps(forbidden_staged, ensure_ascii=False),
        },
        {
            "check_name": "safety::sheet_names_within_limit",
            "status": "PASS" if all(len(sheet) <= 31 for sheet in WORKBOOK_SHEETS_344A) else "FAIL",
            "detail": json.dumps(WORKBOOK_SHEETS_344A, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    if qa_fail_count == 0:
        summary["decision"] = WAITING_DECISION_344A
        summary["source_check_backlog_package_generated"] = True
        summary["review_template_generated"] = True
        summary["reviewer_instructions_generated"] = True
        summary["fill_guide_generated"] = True
        summary["expected_import_contract_generated"] = True
        summary["waiting_for_source_check_review"] = True
        summary["ready_for_344b"] = False
    summary["qa_fail_count"] = qa_fail_count
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    manifest = {
        "task": "344A_source_check_backlog_resolution_package",
        "demo_audit_snapshot_343o_dir": str(demo_audit_snapshot_343o_dir),
        "limited_demo_export_package_343n_dir": str(limited_demo_export_package_343n_dir),
        "human_confirmed_sidecar_simulation_343m_dir": str(human_confirmed_sidecar_simulation_343m_dir),
        "audit_summary_343h_dir": str(audit_summary_343h_dir),
        "spot_check_ingestion_343g_dir": str(spot_check_ingestion_343g_dir),
        "spot_check_package_343f_dir": str(spot_check_package_343f_dir),
        "review_queue_schema_343a_dir": str(review_queue_schema_343a_dir),
        "output_dir": str(output_dir),
        "files_read": list(dict.fromkeys(files_read)),
        "warnings": warnings,
        "source_counts": counts_by_source,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "input_summary_343o": summary_343o,
        "input_qa_343o": qa_343o,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    review_template_rows = [dict(item) for item in backlog_items]
    decision_rule_rows = _build_decision_rule_rows()
    next_steps_rows = _build_next_steps_rows()

    workbook_sheets = {
        "00_README": _build_readme_df(summary),
        "01_PACKAGE_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_343O_SUMMARY": _build_key_value_df(summary_343o),
        "03_BACKLOG_ITEMS": _clean_frame(pd.DataFrame(backlog_items)),
        "04_REVIEW_TEMPLATE": _clean_frame(pd.DataFrame(review_template_rows)),
        "05_EVIDENCE_MAP": _clean_frame(pd.DataFrame(evidence_map["items"])),
        "06_DECISION_RULES": _clean_frame(pd.DataFrame(decision_rule_rows)),
        "07_IMPORT_CONTRACT": _build_key_value_df(expected_import_contract),
        "08_SCOPE_BOUNDARY": _build_key_value_df(
            {
                "scope_boundary_report": scope_boundary_markdown,
                "upstream_343n_scope_boundary": scope_boundary_343n,
                "upstream_343h_gap_report_excerpt": gap_report_343h[:1200],
                "upstream_343o_backlog_summary": backlog_summary_343o,
                "upstream_343o_next_action_plan": next_action_plan_343o,
            }
        ),
        "09_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "10_NEXT_STEPS": _clean_frame(pd.DataFrame(next_steps_rows)),
    }

    template_workbook_sheets = {sheet: workbook_sheets[sheet] for sheet in TEMPLATE_WORKBOOK_SHEETS_344A}

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "backlog_items": backlog_items,
        "evidence_map": evidence_map,
        "reviewer_instructions_markdown": reviewer_instructions_markdown,
        "fill_guide_markdown": fill_guide_markdown,
        "expected_import_contract": expected_import_contract,
        "scope_boundary_markdown": scope_boundary_markdown,
        "workbook_sheets": workbook_sheets,
        "template_workbook_sheets": template_workbook_sheets,
    }
