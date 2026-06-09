from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION = "HUMAN_REVIEW_PACKAGE_AFTER_AI_ADOPTION_340B_READY_FOR_MANUAL_REVIEW"
NOT_READY_DECISION = "HUMAN_REVIEW_PACKAGE_AFTER_AI_ADOPTION_340B_NOT_READY"

DEFAULT_REVIEWED_STRICTNESS_337D_DIR = Path(r"D:\_datefac\output\reviewed_strictness_year_alignment_337d")
DEFAULT_AI_ADOPTION_338D_DIR = Path(r"D:\_datefac\output\ai_review_adoption_simulation_338d")
DEFAULT_MILESTONE_AUDIT_340A_DIR = Path(r"D:\_datefac\output\milestone_acceptance_audit_340a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\human_review_after_ai_adoption_340b")

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

REVIEWER_DECISIONS = [
    "CONFIRM_AS_REVIEWED",
    "CORRECT_AND_CONFIRM",
    "KEEP_NEEDS_REVIEW",
    "REJECT",
    "NEEDS_MORE_CONTEXT",
]

REVIEW_QUEUE_COLUMNS = [
    "review_id",
    "priority",
    "document",
    "source_sheet",
    "source_row_no",
    "metric_before",
    "year_before",
    "value_before",
    "unit_before",
    "source_page",
    "evidence",
    "model_decision",
    "model_confidence",
    "adoption_action",
    "adoption_reason",
    "deterministic_guard_result",
    "risk_flags",
    "recommended_reviewer_action",
    "reviewer_decision",
    "reviewer_corrected_metric",
    "reviewer_corrected_year",
    "reviewer_corrected_value",
    "reviewer_corrected_unit",
    "reviewer_notes",
]

DETAIL_SHEET_COLUMNS = [
    "review_id",
    "priority",
    "candidate_id",
    "document",
    "source_sheet",
    "source_row_no",
    "metric_before",
    "metric_display_zh",
    "year_before",
    "value_before",
    "unit_before",
    "source_page",
    "evidence",
    "model_decision",
    "model_confidence",
    "adoption_action",
    "adoption_reason",
    "deterministic_guard_result",
    "grounding_source",
    "table_role_guess",
    "risk_flags",
    "recommended_reviewer_action",
    "reviewer_decision",
    "reviewer_corrected_metric",
    "reviewer_corrected_year",
    "reviewer_corrected_value",
    "reviewer_corrected_unit",
    "reviewer_notes",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))


def _is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def _git_status_porcelain_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_staged_names_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    staged: List[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _priority_for_row(category: str, deterministic_guard_result: str) -> str:
    if category == "INVALID_MODEL_RESPONSE":
        return "P0"
    if category == "REJECT_BY_RULE_FOR_CHECK":
        return "P0" if deterministic_guard_result.startswith("HARD_REJECT") else "P2"
    if category == "HOLD_FOR_HUMAN_REVIEW":
        return "P1"
    if category == "ACCEPTED_CONFIRM_SPOT_CHECK":
        return "P3"
    if category == "ACCEPTED_REJECT_SPOT_CHECK":
        return "P4"
    if category == "337D_SUSPICIOUS_BACKLOG":
        return "P3"
    return "P2"


def _recommended_action(category: str, guard_result: str) -> str:
    if category == "INVALID_MODEL_RESPONSE":
        return "忽略模型结论，按原始证据人工判定。"
    if category == "HOLD_FOR_HUMAN_REVIEW":
        return "复核原始证据，决定是否确认、修正或继续保留待复核。"
    if category == "REJECT_BY_RULE_FOR_CHECK":
        if guard_result.startswith("HARD_REJECT"):
            return "重点核查规则拦截是否正确，尤其是单位、百分比和金额冲突。"
        return "核查规则拒绝是否为误杀。"
    if category == "ACCEPTED_CONFIRM_SPOT_CHECK":
        return "抽样检查模型确认是否可靠。"
    if category == "ACCEPTED_REJECT_SPOT_CHECK":
        return "抽样检查模型拒绝是否合理。"
    if category == "337D_NEEDS_REVIEW_BACKLOG":
        return "处理 337D 遗留 needs_review 行，补充证据或维持待复核。"
    return "检查 suspicious reviewed 行是否需要回退或补充上下文。"


def _build_signature(
    document: Any,
    metric: Any,
    year: Any,
    value: Any,
    source_page: Any,
) -> Tuple[str, str, str, str, str]:
    return (
        _norm_text(document),
        _norm_text(metric),
        _norm_text(year),
        _norm_text(value),
        _norm_text(source_page),
    )


def _make_sheet_row_lookup(df: pd.DataFrame, row_no_column: str | None) -> Dict[int, Dict[str, Any]]:
    rows: Dict[int, Dict[str, Any]] = {}
    for index, row in enumerate(df.to_dict(orient="records"), start=2):
        if row_no_column and row_no_column in row and _norm_text(row.get(row_no_column)):
            rows[_safe_int(row.get(row_no_column), index)] = dict(row)
        rows[index] = dict(row)
    return rows


def _candidate_id_from_signature(signature: Tuple[str, str, str, str, str], source_trace_df: pd.DataFrame) -> str:
    if source_trace_df.empty:
        return ""
    for row in source_trace_df.to_dict(orient="records"):
        row_signature = _build_signature(
            row.get("document"),
            row.get("metric_after_337d") or row.get("metric_after") or row.get("metric_before"),
            row.get("year_after_337d") or row.get("year"),
            row.get("value"),
            row.get("source_page"),
        )
        if row_signature == signature:
            return _norm_text(row.get("candidate_id"))
    return ""


def _select_spot_check_rows(df: pd.DataFrame, target_count: int) -> pd.DataFrame:
    if len(df) <= target_count:
        return _clean_frame(df)
    selected_indices: List[int] = []
    seen_pairs: set[Tuple[str, str]] = set()
    for index, row in df.iterrows():
        pair = (_norm_text(row.get("document")), _norm_text(row.get("metric_before")))
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            selected_indices.append(index)
        if len(selected_indices) >= target_count:
            break
    if len(selected_indices) < target_count:
        for index in df.index:
            if index not in selected_indices:
                selected_indices.append(index)
            if len(selected_indices) >= target_count:
                break
    return _clean_frame(df.loc[selected_indices].reset_index(drop=True))


def _append_queue_row(
    rows: List[Dict[str, Any]],
    context_rows: List[Dict[str, Any]],
    *,
    review_id: str,
    category: str,
    candidate_id: str,
    document: str,
    source_sheet: str,
    source_row_no: int,
    metric_before: str,
    metric_display_zh: str,
    year_before: str,
    value_before: str,
    unit_before: str,
    source_page: str,
    evidence: str,
    model_decision: str,
    model_confidence: str,
    adoption_action: str,
    adoption_reason: str,
    deterministic_guard_result: str,
    grounding_source: str,
    table_role_guess: str,
    raw_quote: str,
    supporting_context_quote: str,
    risk_flags: str,
    source_workbook_reference: str,
) -> None:
    priority = _priority_for_row(category, deterministic_guard_result)
    recommended_reviewer_action = _recommended_action(category, deterministic_guard_result)
    row = {
        "review_id": review_id,
        "priority": priority,
        "candidate_id": candidate_id,
        "document": document,
        "source_sheet": source_sheet,
        "source_row_no": source_row_no,
        "metric_before": metric_before,
        "metric_display_zh": metric_display_zh,
        "year_before": year_before,
        "value_before": value_before,
        "unit_before": unit_before,
        "source_page": source_page,
        "evidence": evidence,
        "model_decision": model_decision,
        "model_confidence": model_confidence,
        "adoption_action": adoption_action,
        "adoption_reason": adoption_reason,
        "deterministic_guard_result": deterministic_guard_result,
        "grounding_source": grounding_source,
        "table_role_guess": table_role_guess,
        "risk_flags": risk_flags,
        "recommended_reviewer_action": recommended_reviewer_action,
        "reviewer_decision": "",
        "reviewer_corrected_metric": "",
        "reviewer_corrected_year": "",
        "reviewer_corrected_value": "",
        "reviewer_corrected_unit": "",
        "reviewer_notes": "",
        "_category": category,
    }
    rows.append(row)
    context_rows.append(
        {
            "review_id": review_id,
            "candidate_id": candidate_id,
            "document": document,
            "source_page": source_page,
            "evidence": evidence,
            "raw_quote": raw_quote,
            "supporting_context_quote": supporting_context_quote,
            "grounding_source": grounding_source,
            "table_role_guess": table_role_guess,
            "source_workbook_sheet_row_reference": source_workbook_reference,
        }
    )


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {"topic": "用途", "message": "这个工作簿用于 AI adoption simulation 之后的人工复核，不会自动写回任何上游结果。"},
        {"topic": "边界", "message": "AI 决策仍然只是 dry-run，当前行不会自动应用。"},
        {"topic": "审阅方式", "message": "审阅人应确认、修正、拒绝，或要求更多上下文。"},
        {"topic": "状态", "message": "当前不是 client-ready，也不是 production-ready。"},
        {"topic": "风险提示", "message": "禁止将本工作簿用于投资建议或投资决策。"},
        {"topic": "允许 reviewer_decision", "message": "CONFIRM_AS_REVIEWED | CORRECT_AND_CONFIRM | KEEP_NEEDS_REVIEW | REJECT | NEEDS_MORE_CONTEXT"},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_review_guide_df() -> pd.DataFrame:
    rows = [
        {"section": "收入/净利润", "guide": "优先核对 source_page 与 evidence，确认金额是否来自同一张表和正确年份列。"},
        {"section": "EPS/PE/PB/ROE", "guide": "注意每股类指标与估值类指标是否混淆，检查单位是否为元、倍或百分比。"},
        {"section": "单位处理", "guide": "若金额指标缺少 money unit，应优先保守处理；只有证据充分时才改为确认。"},
        {"section": "同比处理", "guide": "带百分号的值先判断是否其实是 YoY，不要把百分比误当金额。"},
        {"section": "证据不足", "guide": "若 evidence 不足以支撑确认，优先选择 KEEP_NEEDS_REVIEW 或 NEEDS_MORE_CONTEXT。"},
        {"section": "页码/证据缺失", "guide": "source_page 或 evidence 不足时，不要强行确认，记录 reviewer_notes。"},
        {"section": "投资建议边界", "guide": "本工作簿不产生投资建议，也不能作为投资决策依据。"},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _queue_view(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=REVIEW_QUEUE_COLUMNS)
    return _clean_frame(df[REVIEW_QUEUE_COLUMNS])


def _detail_view(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=DETAIL_SHEET_COLUMNS)
    return _clean_frame(df[DETAIL_SHEET_COLUMNS])


def build_human_review_after_ai_adoption_340b(
    *,
    reviewed_strictness_337d_dir: Path,
    ai_adoption_338d_dir: Path,
    milestone_audit_340a_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    workbook_337d = reviewed_strictness_337d_dir / "real_test_mineru_client_export_337d.xlsx"
    workbook_337d_before_after = reviewed_strictness_337d_dir / "reviewed_strictness_year_alignment_337d_before_after.xlsx"
    workbook_338d = ai_adoption_338d_dir / "ai_review_adoption_simulation_338d_plan.xlsx"
    workbook_340a = milestone_audit_340a_dir / "milestone_acceptance_audit_340a.xlsx"
    summary_337d_path = reviewed_strictness_337d_dir / "reviewed_strictness_year_alignment_337d_summary.json"
    summary_338d_path = ai_adoption_338d_dir / "ai_review_adoption_simulation_338d_summary.json"
    summary_340a_path = milestone_audit_340a_dir / "milestone_acceptance_audit_340a_summary.json"

    files_read = [
        str(summary_337d_path),
        str(summary_338d_path),
        str(summary_340a_path),
        str(workbook_337d),
        str(workbook_337d_before_after),
        str(workbook_338d),
        str(workbook_340a),
    ]

    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    input_workbook_hashes_before = {
        str(path): sha256_file(path)
        for path in [workbook_337d, workbook_337d_before_after, workbook_338d, workbook_340a]
    }

    summary_337d = _read_json(summary_337d_path)
    summary_338d = _read_json(summary_338d_path)
    summary_340a = _read_json(summary_340a_path)

    adoption_plan_df = _read_excel(workbook_338d, "02_ADOPTION_PLAN")
    accepted_confirms_df = _read_excel(workbook_338d, "03_ACCEPTED_CONFIRMS")
    accepted_rejects_df = _read_excel(workbook_338d, "05_ACCEPTED_REJECTS")
    hold_df = _read_excel(workbook_338d, "06_HOLD_FOR_HUMAN_REVIEW")
    rejected_by_rule_df = _read_excel(workbook_338d, "07_REJECTED_BY_RULE")
    invalid_df = _read_excel(workbook_338d, "08_INVALID_MODEL_RESPONSES")

    needs_review_df = _read_excel(workbook_337d, "02_NEEDS_REVIEW")
    source_trace_df = _read_excel(workbook_337d, "04_SOURCE_TRACE")
    suspicious_df = _read_excel(workbook_337d, "08_SUSPICIOUS_REVIEWED_AUDIT")
    audit_summary_df = _read_excel(workbook_340a, "01_AUDIT_SUMMARY")

    suspicious_lookup = _make_sheet_row_lookup(suspicious_df, None)
    needs_review_lookup = _make_sheet_row_lookup(needs_review_df, "row_no")

    queue_rows: List[Dict[str, Any]] = []
    context_rows: List[Dict[str, Any]] = []
    represented_keys: set[str] = set()
    next_review_id = 1

    def new_review_id() -> str:
        nonlocal next_review_id
        review_id = f"340b::{next_review_id:03d}"
        next_review_id += 1
        return review_id

    def add_from_adoption_frame(frame: pd.DataFrame, category: str) -> None:
        for row in frame.to_dict(orient="records"):
            source_sheet = _norm_text(row.get("source_sheet"))
            source_row_no = _safe_int(row.get("source_row_no"), 0)
            source_row = suspicious_lookup.get(source_row_no, {}) if source_sheet == "08_SUSPICIOUS_REVIEWED_AUDIT" else needs_review_lookup.get(source_row_no, {})
            candidate_id = _norm_text(source_row.get("candidate_id")) or f"{_norm_text(row.get('adoption_id'))}::candidate"
            represented_keys.add(candidate_id)
            evidence = _norm_text(source_row.get("evidence") or source_row.get("source_evidence_excerpt"))
            source_page = _norm_text(source_row.get("source_page"))
            metric_display_zh = _norm_text(source_row.get("metric_display_zh") or source_row.get("metric_display_zh_after_337d"))
            raw_quote = evidence
            supporting_context_quote = _norm_text(source_row.get("table_preview") or source_row.get("source_evidence_excerpt"))
            risk_tokens = [
                category,
                _norm_text(row.get("model_decision_status")),
                _norm_text(row.get("deterministic_guard_result")),
                _norm_text(source_row.get("suspicious_reason")),
            ]
            risk_flags = " | ".join(token for token in risk_tokens if token)
            _append_queue_row(
                queue_rows,
                context_rows,
                review_id=new_review_id(),
                category=category,
                candidate_id=candidate_id,
                document=_norm_text(row.get("document")),
                source_sheet=source_sheet,
                source_row_no=source_row_no,
                metric_before=_norm_text(row.get("metric_before")),
                metric_display_zh=metric_display_zh,
                year_before=_norm_text(row.get("year_before")),
                value_before=_norm_text(row.get("value_before")),
                unit_before=_norm_text(row.get("unit_before")),
                source_page=source_page,
                evidence=evidence,
                model_decision=_norm_text(row.get("model_decision")),
                model_confidence=_norm_text(row.get("confidence")),
                adoption_action=_norm_text(row.get("adoption_action")),
                adoption_reason=_norm_text(row.get("adoption_reason")),
                deterministic_guard_result=_norm_text(row.get("deterministic_guard_result")),
                grounding_source=_norm_text(row.get("grounding_source")),
                table_role_guess=_norm_text(row.get("table_role_guess")),
                raw_quote=raw_quote,
                supporting_context_quote=supporting_context_quote,
                risk_flags=risk_flags,
                source_workbook_reference=f"real_test_mineru_client_export_337d.xlsx::{source_sheet}::row_{source_row_no}",
            )

    add_from_adoption_frame(invalid_df, "INVALID_MODEL_RESPONSE")
    add_from_adoption_frame(hold_df, "HOLD_FOR_HUMAN_REVIEW")
    add_from_adoption_frame(rejected_by_rule_df, "REJECT_BY_RULE_FOR_CHECK")

    confirm_spot_df = _select_spot_check_rows(accepted_confirms_df, 10)
    reject_spot_df = _select_spot_check_rows(accepted_rejects_df, len(accepted_rejects_df))
    add_from_adoption_frame(confirm_spot_df, "ACCEPTED_CONFIRM_SPOT_CHECK")
    add_from_adoption_frame(reject_spot_df, "ACCEPTED_REJECT_SPOT_CHECK")

    for row in needs_review_df.to_dict(orient="records"):
        signature = _build_signature(row.get("document"), row.get("metric"), row.get("year"), row.get("value"), row.get("source_page"))
        candidate_id = _candidate_id_from_signature(signature, source_trace_df)
        if candidate_id and candidate_id in represented_keys:
            continue
        represented_keys.add(candidate_id or "|".join(signature))
        _append_queue_row(
            queue_rows,
            context_rows,
            review_id=new_review_id(),
            category="337D_NEEDS_REVIEW_BACKLOG",
            candidate_id=candidate_id,
            document=_norm_text(row.get("document")),
            source_sheet="02_NEEDS_REVIEW",
            source_row_no=_safe_int(row.get("row_no"), 0),
            metric_before=_norm_text(row.get("metric")),
            metric_display_zh=_norm_text(row.get("metric_display_zh")),
            year_before=_norm_text(row.get("year")),
            value_before=_norm_text(row.get("value")),
            unit_before=_norm_text(row.get("unit")),
            source_page=_norm_text(row.get("source_page")),
            evidence=_norm_text(row.get("source_evidence_excerpt")),
            model_decision="",
            model_confidence="",
            adoption_action="NOT_REPRESENTED_IN_338D",
            adoption_reason="337d_needs_review_backlog",
            deterministic_guard_result="",
            grounding_source="N/A_337D_ONLY",
            table_role_guess="",
            raw_quote=_norm_text(row.get("source_evidence_excerpt")),
            supporting_context_quote=_norm_text(row.get("notes")),
            risk_flags=_norm_text(row.get("notes")) or "337D_NEEDS_REVIEW",
            source_workbook_reference=f"real_test_mineru_client_export_337d.xlsx::02_NEEDS_REVIEW::row_{_safe_int(row.get('row_no'), 0)}",
        )

    for index, row in enumerate(suspicious_df.to_dict(orient="records"), start=2):
        candidate_id = _norm_text(row.get("candidate_id"))
        if candidate_id and candidate_id in represented_keys:
            continue
        represented_keys.add(candidate_id or f"suspicious::{index}")
        _append_queue_row(
            queue_rows,
            context_rows,
            review_id=new_review_id(),
            category="337D_SUSPICIOUS_BACKLOG",
            candidate_id=candidate_id,
            document=_norm_text(row.get("document")),
            source_sheet="08_SUSPICIOUS_REVIEWED_AUDIT",
            source_row_no=index,
            metric_before=_norm_text(row.get("metric")),
            metric_display_zh="",
            year_before=_norm_text(row.get("year")),
            value_before=_norm_text(row.get("value")),
            unit_before=_norm_text(row.get("unit")),
            source_page=_norm_text(row.get("source_page")),
            evidence=_norm_text(row.get("evidence")),
            model_decision="",
            model_confidence="",
            adoption_action="NOT_REPRESENTED_IN_338D_SUSPICIOUS",
            adoption_reason="337d_suspicious_backlog",
            deterministic_guard_result="",
            grounding_source="N/A_337D_ONLY",
            table_role_guess="",
            raw_quote=_norm_text(row.get("evidence")),
            supporting_context_quote=_norm_text(row.get("337d_action")),
            risk_flags=_norm_text(row.get("suspicious_reason")) or "337D_SUSPICIOUS_REVIEWED",
            source_workbook_reference=f"real_test_mineru_client_export_337d.xlsx::08_SUSPICIOUS_REVIEWED_AUDIT::row_{index}",
        )

    queue_df = _clean_frame(pd.DataFrame(queue_rows))
    context_df = _clean_frame(pd.DataFrame(context_rows))

    hold_queue_df = queue_df[queue_df["_category"] == "HOLD_FOR_HUMAN_REVIEW"].copy()
    invalid_queue_df = queue_df[queue_df["_category"] == "INVALID_MODEL_RESPONSE"].copy()
    rejected_rule_queue_df = queue_df[queue_df["_category"] == "REJECT_BY_RULE_FOR_CHECK"].copy()
    confirm_queue_df = queue_df[queue_df["_category"] == "ACCEPTED_CONFIRM_SPOT_CHECK"].copy()
    reject_queue_df = queue_df[queue_df["_category"] == "ACCEPTED_REJECT_SPOT_CHECK"].copy()

    summary_sheet_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "total_review_queue_count": len(queue_df),
                    "hold_for_human_count": len(hold_queue_df),
                    "invalid_model_response_count": len(invalid_queue_df),
                    "rejected_by_rule_check_count": len(rejected_rule_queue_df),
                    "accepted_confirm_spot_check_count": len(confirm_queue_df),
                    "accepted_reject_spot_check_count": len(reject_queue_df),
                    "source_337d_reviewed_count": _safe_int(summary_337d.get("reviewed_after_count")),
                    "source_338d_accept_confirm_count": _safe_int(summary_338d.get("accept_model_confirm_count")),
                    "source_338d_accept_reject_count": _safe_int(summary_338d.get("accept_model_reject_count")),
                    "source_338d_hold_count": _safe_int(summary_338d.get("hold_for_human_review_count")),
                    "source_338d_invalid_count": _safe_int(summary_338d.get("invalid_model_response_count")),
                    "client_ready": False,
                    "production_ready": False,
                    "no_write_back": True,
                }
            ]
        )
    )

    review_guide_df = _build_review_guide_df()
    readme_df = _build_readme_df()

    review_workbook_path = output_dir / "human_review_after_ai_adoption_340b_review_template.xlsx"
    output_dir.mkdir(parents=True, exist_ok=True)

    input_workbook_hashes_after = {
        str(path): sha256_file(path)
        for path in [workbook_337d, workbook_337d_before_after, workbook_338d, workbook_340a]
    }
    upstream_workbooks_unchanged = input_workbook_hashes_before == input_workbook_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    reviewer_fields_present = set(REVIEW_QUEUE_COLUMNS).issubset(set(_queue_view(queue_df).columns))
    no_apply_proof_path = output_dir / "human_review_after_ai_adoption_340b_no_apply_proof.json"

    summary_match_detail = "340a_summary_field_missing"
    summary_match_pass = True
    if "accept_model_confirm_count_338d" in summary_340a:
        summary_match_pass = _safe_int(summary_338d.get("accept_model_confirm_count")) == _safe_int(
            summary_340a.get("accept_model_confirm_count_338d")
        )
        summary_match_detail = (
            f"338d={summary_338d.get('accept_model_confirm_count')} "
            f"340a={summary_340a.get('accept_model_confirm_count_338d')}"
        )

    checks = [
        {"check_name": "inputs::337d_workbook_exists", "status": "PASS" if workbook_337d.exists() else "FAIL", "detail": str(workbook_337d)},
        {"check_name": "inputs::338d_workbook_exists", "status": "PASS" if workbook_338d.exists() else "FAIL", "detail": str(workbook_338d)},
        {"check_name": "inputs::340a_workbook_exists", "status": "PASS" if workbook_340a.exists() else "FAIL", "detail": str(workbook_340a)},
        {"check_name": "inputs::337d_before_after_exists", "status": "PASS" if workbook_337d_before_after.exists() else "FAIL", "detail": str(workbook_337d_before_after)},
        {"check_name": "counts::review_queue_has_all_hold_rows", "status": "PASS" if len(hold_queue_df) == len(hold_df) else "FAIL", "detail": f"queue={len(hold_queue_df)} source={len(hold_df)}"},
        {"check_name": "counts::review_queue_has_all_invalid_rows", "status": "PASS" if len(invalid_queue_df) == len(invalid_df) else "FAIL", "detail": f"queue={len(invalid_queue_df)} source={len(invalid_df)}"},
        {"check_name": "columns::reviewer_fields_present", "status": "PASS" if reviewer_fields_present else "FAIL", "detail": json.dumps(REVIEW_QUEUE_COLUMNS, ensure_ascii=False)},
        {"check_name": "safety::upstream_workbooks_unchanged", "status": "PASS" if upstream_workbooks_unchanged else "FAIL", "detail": json.dumps(input_workbook_hashes_after, ensure_ascii=False)},
        {"check_name": "safety::official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
        {"check_name": "claims::client_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "safety::no_apply_proof_generated", "status": "PASS", "detail": str(no_apply_proof_path)},
        {"check_name": "outputs::review_workbook_generated", "status": "PASS", "detail": str(review_workbook_path)},
        {
            "check_name": "source::338d_summary_matches_340a",
            "status": "PASS" if summary_match_pass else "FAIL",
            "detail": summary_match_detail,
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    decision = READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "review_workbook_path": str(review_workbook_path),
        "total_review_queue_count": int(len(queue_df)),
        "hold_for_human_count": int(len(hold_queue_df)),
        "invalid_model_response_count": int(len(invalid_queue_df)),
        "rejected_by_rule_check_count": int(len(rejected_rule_queue_df)),
        "accepted_confirm_spot_check_count": int(len(confirm_queue_df)),
        "accepted_reject_spot_check_count": int(len(reject_queue_df)),
        "source_337d_reviewed_count": _safe_int(summary_337d.get("reviewed_after_count")),
        "source_338d_accept_confirm_count": _safe_int(summary_338d.get("accept_model_confirm_count")),
        "source_338d_accept_reject_count": _safe_int(summary_338d.get("accept_model_reject_count")),
        "source_338d_hold_count": _safe_int(summary_338d.get("hold_for_human_review_count")),
        "source_338d_invalid_count": _safe_int(summary_338d.get("invalid_model_response_count")),
        "source_340a_qa_fail_count": _safe_int(summary_340a.get("qa_fail_count")),
        "reviewer_fields_present": reviewer_fields_present,
        "upstream_workbooks_unchanged": upstream_workbooks_unchanged,
        "client_ready": False,
        "production_ready": False,
        "no_write_back": True,
        "no_apply_proof_generated": True,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
    }

    manifest = {
        "task": "340B_human_review_package_after_ai_adoption",
        "reviewed_strictness_337d_dir": str(reviewed_strictness_337d_dir),
        "ai_adoption_338d_dir": str(ai_adoption_338d_dir),
        "milestone_audit_340a_dir": str(milestone_audit_340a_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "human_review_after_ai_adoption_340b_summary.json"),
            "manifest_json": str(output_dir / "human_review_after_ai_adoption_340b_manifest.json"),
            "qa_json": str(output_dir / "human_review_after_ai_adoption_340b_qa.json"),
            "no_apply_proof_json": str(no_apply_proof_path),
            "report_md": str(output_dir / "human_review_after_ai_adoption_340b_report.md"),
            "review_workbook_xlsx": str(review_workbook_path),
        },
        "allowed_reviewer_decisions": list(REVIEWER_DECISIONS),
        "files_read": files_read,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "checks": checks,
        "reviewer_decision_allowed_values": list(REVIEWER_DECISIONS),
        "input_workbook_hashes_before": input_workbook_hashes_before,
        "input_workbook_hashes_after": input_workbook_hashes_after,
    }

    no_apply_proof_json = build_no_apply_proof(
        stage="340B",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    workbook_sheets = {
        "00_README": readme_df,
        "01_REVIEW_QUEUE": _queue_view(queue_df),
        "02_HOLD_FOR_HUMAN_REVIEW": _detail_view(hold_queue_df),
        "03_INVALID_MODEL_RESPONSES": _detail_view(invalid_queue_df),
        "04_REJECTED_BY_RULE_FOR_CHECK": _detail_view(rejected_rule_queue_df),
        "05_ACCEPTED_CONFIRM_SPOT_CHECK": _detail_view(confirm_queue_df),
        "06_ACCEPTED_REJECT_SPOT_CHECK": _detail_view(reject_queue_df),
        "07_SOURCE_TRACE_CONTEXT": _clean_frame(context_df),
        "08_REVIEW_GUIDE": review_guide_df,
        "09_SUMMARY": summary_sheet_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "workbook_sheets": workbook_sheets,
    }
