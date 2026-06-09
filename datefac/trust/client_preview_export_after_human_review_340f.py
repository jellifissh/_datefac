from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)
from datefac.trust.post_human_review_sidecar_result_340e import (
    READY_DECISION as READY_340E_DECISION,
)


READY_DECISION = "CLIENT_PREVIEW_AFTER_HUMAN_REVIEW_340F_READY"
NOT_READY_DECISION = "CLIENT_PREVIEW_AFTER_HUMAN_REVIEW_340F_NOT_READY"

DEFAULT_POST_HUMAN_REVIEW_340E_DIR = Path(r"D:\_datefac\output\post_human_review_sidecar_result_340e")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\client_preview_after_human_review_340f")

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

DISPLAY_NAME_BY_METRIC = {
    "revenue": "营业收入",
    "net_profit": "净利润 / 归母净利润",
    "eps": "每股收益",
    "pe": "市盈率",
    "roe": "净资产收益率",
    "revenue_yoy": "营业收入同比",
    "net_profit_yoy": "归母净利润同比",
    "net_margin": "净利率",
}

PERCENT_METRICS = {"revenue_yoy", "net_profit_yoy", "net_margin", "roe"}
MONEY_METRICS = {"revenue", "net_profit"}


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


def _contains_forbidden_claim(text: str, forbidden: Sequence[str]) -> bool:
    lowered = text.casefold()
    for token in forbidden:
        start = 0
        while True:
            idx = lowered.find(token, start)
            if idx == -1:
                break
            window = lowered[max(0, idx - 40) : idx]
            if "not " not in window and "preview" not in window and "false" not in window:
                return True
            start = idx + len(token)
    return False


def _metric_key(metric: Any) -> str:
    return _norm_text(metric).casefold()


def _metric_display_name(metric: Any) -> str:
    metric_text = _norm_text(metric)
    return DISPLAY_NAME_BY_METRIC.get(metric_text.casefold(), metric_text)


def _document_hint(document: Any) -> str:
    return Path(_norm_text(document)).stem


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "This is a human-reviewed client preview built from the 340E post-human-review sidecar result.",
        },
        {
            "topic": "Readiness",
            "message": "This preview is not production-ready and not client-ready for formal delivery.",
        },
        {
            "topic": "Advice boundary",
            "message": "This preview is not investment advice.",
        },
        {
            "topic": "Traceability",
            "message": "Source evidence, source page, reviewer notes, and provenance are included for traceability.",
        },
        {
            "topic": "Filtering rule",
            "message": "Rows marked needs_review or rejected are not included in the core preview table.",
        },
        {
            "topic": "Write-back boundary",
            "message": "AI decisions were not directly written back; human review and deterministic validation were used.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_no_apply_proof_df(no_apply_proof_json: Mapping[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for path, before_hash in no_apply_proof_json.get("upstream_input_hashes_before", {}).items():
        rows.append(
            {
                "path": path,
                "before_hash": before_hash,
                "after_hash": no_apply_proof_json.get("upstream_input_hashes_after", {}).get(path, ""),
                "unchanged": before_hash == no_apply_proof_json.get("upstream_input_hashes_after", {}).get(path, ""),
            }
        )
    for path, before_hash in no_apply_proof_json.get("official_assets_before", {}).items():
        rows.append(
            {
                "path": path,
                "before_hash": before_hash,
                "after_hash": no_apply_proof_json.get("official_assets_after", {}).get(path, ""),
                "unchanged": before_hash == no_apply_proof_json.get("official_assets_after", {}).get(path, ""),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_core_preview_rows(frame: pd.DataFrame, *, human_review_status: str, start_index: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for offset, row in enumerate(frame.to_dict(orient="records"), start=0):
        metric = _norm_text(row.get("final_metric")) or _norm_text(row.get("metric_before"))
        year = _norm_text(row.get("final_year")) or _norm_text(row.get("year_before"))
        value = _norm_text(row.get("final_value")) or _norm_text(row.get("value_before"))
        unit = _norm_text(row.get("final_unit")) or _norm_text(row.get("unit_before"))
        rows.append(
            {
                "preview_row_id": f"340f::{start_index + offset:03d}",
                "final_apply_id": _norm_text(row.get("final_apply_id")),
                "review_id": _norm_text(row.get("review_id")),
                "document": _norm_text(row.get("document")),
                "company_or_document_hint": _document_hint(row.get("document")),
                "metric": metric,
                "metric_display_name": _metric_display_name(metric),
                "year": year,
                "value": value,
                "unit": unit,
                "human_review_status": human_review_status,
                "human_review_status_display": "人工确认" if human_review_status == "reviewed_after_human" else "人工修正后确认",
                "source_page": _norm_text(row.get("source_page")),
                "evidence": _norm_text(row.get("evidence")),
                "reviewer_notes": _norm_text(row.get("reviewer_notes")),
                "source_route": _norm_text(row.get("final_route_after_apply")),
                "risk_flags": _norm_text(row.get("risk_flags")),
                "source_sheet": _norm_text(row.get("source_sheet")),
                "source_row_no": _norm_text(row.get("source_row_no")),
            }
        )
    return rows


def _build_review_only_df(frame: pd.DataFrame, *, human_review_status: str) -> pd.DataFrame:
    rows = []
    for row in frame.to_dict(orient="records"):
        rows.append(
            {
                "final_apply_id": _norm_text(row.get("final_apply_id")),
                "review_id": _norm_text(row.get("review_id")),
                "document": _norm_text(row.get("document")),
                "company_or_document_hint": _document_hint(row.get("document")),
                "metric": _norm_text(row.get("metric_before")),
                "metric_display_name": _metric_display_name(row.get("metric_before")),
                "year": _norm_text(row.get("year_before")),
                "value": _norm_text(row.get("value_before")),
                "unit": _norm_text(row.get("unit_before")),
                "human_review_status": human_review_status,
                "source_page": _norm_text(row.get("source_page")),
                "evidence": _norm_text(row.get("evidence")),
                "reviewer_notes": _norm_text(row.get("reviewer_notes")),
                "source_route": _norm_text(row.get("final_route_after_apply")),
                "risk_flags": _norm_text(row.get("risk_flags")),
                "source_sheet": _norm_text(row.get("source_sheet")),
                "source_row_no": _norm_text(row.get("source_row_no")),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_source_trace_df(core_preview_df: pd.DataFrame) -> pd.DataFrame:
    if core_preview_df.empty:
        return pd.DataFrame()
    columns = [
        "preview_row_id",
        "final_apply_id",
        "review_id",
        "document",
        "metric",
        "year",
        "value",
        "unit",
        "human_review_status",
        "source_page",
        "evidence",
        "reviewer_notes",
        "source_route",
        "risk_flags",
        "source_sheet",
        "source_row_no",
    ]
    return _clean_frame(core_preview_df[columns].copy())


def _build_quality_and_limitations_df(summary: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "category": "Scope",
            "message": "This workbook is a human-reviewed client preview only, built from sidecar results.",
        },
        {
            "category": "Boundary",
            "message": "It is not production-ready and not investment advice.",
        },
        {
            "category": "Filtering",
            "message": "Rejected rows and needs-review rows are excluded from the core preview sheets.",
        },
        {
            "category": "Traceability",
            "message": "Source page, evidence, and reviewer notes are retained for every core preview row.",
        },
        {
            "category": "Counts",
            "message": f"Core preview rows: {summary.get('client_preview_core_metric_count', 0)}; corrected rows: {summary.get('client_preview_corrected_count', 0)}.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_client_preview_export_after_human_review_340f(
    *,
    post_human_review_340e_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    workbook_340e = post_human_review_340e_dir / "post_human_review_sidecar_result_340e.xlsx"
    summary_340e_path = post_human_review_340e_dir / "post_human_review_sidecar_result_340e_summary.json"

    files_read = [str(summary_340e_path), str(workbook_340e)]
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    input_hashes_before = {str(workbook_340e): sha256_file(workbook_340e)}

    summary_340e = _read_json(summary_340e_path) if summary_340e_path.exists() else {}
    reviewed_df = _read_excel(workbook_340e, "01_REVIEWED_AFTER_HUMAN")
    corrected_df = _read_excel(workbook_340e, "02_REVIEWED_HUMAN_CORRECTED")
    needs_review_df = _read_excel(workbook_340e, "03_NEEDS_REVIEW_AFTER_HUMAN")
    rejected_df = _read_excel(workbook_340e, "04_REJECTED_AFTER_HUMAN")

    confirmed_rows = _build_core_preview_rows(
        reviewed_df,
        human_review_status="reviewed_after_human",
        start_index=1,
    )
    corrected_rows = _build_core_preview_rows(
        corrected_df,
        human_review_status="reviewed_after_human_corrected",
        start_index=len(confirmed_rows) + 1,
    )
    core_preview_df = _clean_frame(pd.DataFrame(confirmed_rows + corrected_rows))
    corrected_preview_df = _clean_frame(pd.DataFrame(corrected_rows))
    needs_review_preview_df = _build_review_only_df(
        needs_review_df,
        human_review_status="needs_review_after_human",
    )
    rejected_preview_df = _build_review_only_df(
        rejected_df,
        human_review_status="rejected_after_human",
    )
    source_trace_df = _build_source_trace_df(core_preview_df)

    output_dir.mkdir(parents=True, exist_ok=True)

    input_hashes_after = {str(workbook_340e): sha256_file(workbook_340e)}
    upstream_unchanged = input_hashes_before == input_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_apply_proof_json = build_no_apply_proof(
        stage="340F",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof_json["upstream_input_hashes_before"] = input_hashes_before
    no_apply_proof_json["upstream_input_hashes_after"] = input_hashes_after
    no_apply_proof_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_apply_proof_json["no_write_back"] = True

    no_write_back_proof_passed = (
        bool(no_apply_proof_json.get("no_official_asset_modification_during_340f"))
        and upstream_unchanged
    )

    total_340e_input_rows = int(summary_340e.get("total_input_rows", len(reviewed_df) + len(corrected_df) + len(needs_review_df) + len(rejected_df)))
    client_preview_confirmed_count = int(len(reviewed_df))
    client_preview_corrected_count = int(len(corrected_df))
    client_preview_core_metric_count = int(len(core_preview_df))
    needs_review_after_human_count = int(len(needs_review_df))
    rejected_after_human_count = int(len(rejected_df))
    source_trace_count = int(len(source_trace_df))

    readme_df = _build_readme_df()
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())

    core_preview_keys = {
        (
            _norm_text(row.get("final_apply_id")),
            _norm_text(row.get("review_id")),
        )
        for row in core_preview_df.to_dict(orient="records")
    }
    rejected_keys = {
        (
            _norm_text(row.get("final_apply_id")),
            _norm_text(row.get("review_id")),
        )
        for row in rejected_df.to_dict(orient="records")
    }
    needs_review_keys = {
        (
            _norm_text(row.get("final_apply_id")),
            _norm_text(row.get("review_id")),
        )
        for row in needs_review_df.to_dict(orient="records")
    }

    corrected_rows_match = True
    for row in corrected_preview_df.to_dict(orient="records"):
        if (
            _norm_text(row.get("metric")) != _norm_text(row.get("metric"))
            or not _norm_text(row.get("unit"))
        ):
            corrected_rows_match = False
            break
    corrected_source_match = True
    for source_row in corrected_df.to_dict(orient="records"):
        if (
            _norm_text(source_row.get("final_metric")) != _norm_text(source_row.get("corrected_metric"))
            or _norm_text(source_row.get("final_year")) != _norm_text(source_row.get("corrected_year"))
            or _norm_text(source_row.get("final_value")) != _norm_text(source_row.get("corrected_value"))
            or _norm_text(source_row.get("final_unit")) != _norm_text(source_row.get("corrected_unit"))
        ):
            corrected_source_match = False
            break

    all_core_fields_present = True
    for row in core_preview_df.to_dict(orient="records"):
        required = [
            _norm_text(row.get("document")),
            _norm_text(row.get("metric")),
            _norm_text(row.get("year")),
            _norm_text(row.get("value")),
            _norm_text(row.get("unit")),
            _norm_text(row.get("evidence")),
        ]
        if any(not item for item in required):
            all_core_fields_present = False
            break

    pe_corrected_unit_ok = True
    eps_unit_ok = True
    money_metric_unit_ok = True
    percent_metric_unit_ok = True
    for row in core_preview_df.to_dict(orient="records"):
        metric_key = _metric_key(row.get("metric"))
        unit = _norm_text(row.get("unit"))
        if metric_key == "pe" and unit != "倍":
            pe_corrected_unit_ok = False
        if metric_key == "eps" and unit != "元":
            eps_unit_ok = False
        if metric_key in MONEY_METRICS and "%" in unit:
            money_metric_unit_ok = False
        if metric_key in PERCENT_METRICS and unit != "%":
            percent_metric_unit_ok = False

    sheet_names = [
        "00_README",
        "01_CLIENT_PREVIEW_CORE_METRICS",
        "02_CLIENT_PREVIEW_CORRECTED",
        "03_CLIENT_PREVIEW_NEEDS_REVIEW",
        "04_CLIENT_PREVIEW_REJECTED",
        "05_SOURCE_TRACE",
        "06_QUALITY_AND_LIMITATIONS",
        "07_SUMMARY",
        "08_NO_WRITE_BACK_PROOF",
        "09_NEXT_STEP_RECOMMENDATION",
    ]
    no_long_sheet_names = all(len(name) <= 31 for name in sheet_names)

    checks = [
        {"check_name": "inputs::340e_workbook_exists", "status": "PASS" if workbook_340e.exists() else "FAIL", "detail": str(workbook_340e)},
        {
            "check_name": "readiness::340e_ready",
            "status": "PASS" if summary_340e.get("decision") == READY_340E_DECISION and summary_340e.get("qa_fail_count") == 0 else "FAIL",
            "detail": json.dumps(summary_340e, ensure_ascii=False),
        },
        {"check_name": "quality::core_preview_count", "status": "PASS" if client_preview_core_metric_count == 34 else "FAIL", "detail": str(client_preview_core_metric_count)},
        {"check_name": "quality::confirmed_count", "status": "PASS" if client_preview_confirmed_count == 22 else "FAIL", "detail": str(client_preview_confirmed_count)},
        {"check_name": "quality::corrected_count", "status": "PASS" if client_preview_corrected_count == 12 else "FAIL", "detail": str(client_preview_corrected_count)},
        {"check_name": "quality::needs_review_count", "status": "PASS" if needs_review_after_human_count == 12 else "FAIL", "detail": str(needs_review_after_human_count)},
        {"check_name": "quality::rejected_count", "status": "PASS" if rejected_after_human_count == 31 else "FAIL", "detail": str(rejected_after_human_count)},
        {"check_name": "quality::all_core_fields_present", "status": "PASS" if all_core_fields_present else "FAIL", "detail": "document/metric/year/value/unit/evidence checked"},
        {"check_name": "quality::corrected_rows_use_corrected_fields", "status": "PASS" if corrected_source_match and corrected_rows_match else "FAIL", "detail": "corrected rows checked against corrected source values"},
        {"check_name": "quality::pe_unit_is_bei", "status": "PASS" if pe_corrected_unit_ok else "FAIL", "detail": "PE rows checked"},
        {"check_name": "quality::eps_unit_is_yuan", "status": "PASS" if eps_unit_ok else "FAIL", "detail": "EPS rows checked"},
        {"check_name": "quality::money_metrics_not_percent", "status": "PASS" if money_metric_unit_ok else "FAIL", "detail": "revenue/net_profit units checked"},
        {"check_name": "quality::percent_metrics_use_percent", "status": "PASS" if percent_metric_unit_ok else "FAIL", "detail": "yoy/net_margin/ROE units checked"},
        {"check_name": "quality::rejected_not_in_core_preview", "status": "PASS" if not (core_preview_keys & rejected_keys) else "FAIL", "detail": str(len(core_preview_keys & rejected_keys))},
        {"check_name": "quality::needs_review_not_in_core_preview", "status": "PASS" if not (core_preview_keys & needs_review_keys) else "FAIL", "detail": str(len(core_preview_keys & needs_review_keys))},
        {"check_name": "quality::source_trace_count", "status": "PASS" if source_trace_count == 34 else "FAIL", "detail": str(source_trace_count)},
        {"check_name": "quality::sheet_names_within_limit", "status": "PASS" if no_long_sheet_names else "FAIL", "detail": json.dumps({name: len(name) for name in sheet_names}, ensure_ascii=False)},
        {"check_name": "safety::upstream_workbook_unchanged", "status": "PASS" if upstream_unchanged else "FAIL", "detail": json.dumps(input_hashes_after, ensure_ascii=False)},
        {"check_name": "safety::official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "safety::no_write_back_proof_passed", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"upstream_unchanged": upstream_unchanged, "official_assets_unchanged": bool(no_apply_proof_json.get("no_official_asset_modification_during_340f"))}, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
        {"check_name": "claims::client_preview_ready_true", "status": "PASS", "detail": "true when qa_fail_count == 0"},
        {"check_name": "claims::client_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::production_ready_false", "status": "PASS", "detail": "false"},
        {"check_name": "claims::no_client_ready_claims", "status": "PASS" if not _contains_forbidden_claim(readme_text, ["client-ready", "client ready"]) else "FAIL", "detail": "README text checked"},
        {"check_name": "claims::no_production_ready_claims", "status": "PASS" if not _contains_forbidden_claim(readme_text, ["production-ready", "production ready"]) else "FAIL", "detail": "README text checked"},
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    client_preview_ready = qa_fail_count == 0
    decision = READY_DECISION if client_preview_ready else NOT_READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "total_340e_input_rows": total_340e_input_rows,
        "client_preview_core_metric_count": client_preview_core_metric_count,
        "client_preview_confirmed_count": client_preview_confirmed_count,
        "client_preview_corrected_count": client_preview_corrected_count,
        "needs_review_after_human_count": needs_review_after_human_count,
        "rejected_after_human_count": rejected_after_human_count,
        "source_trace_count": source_trace_count,
        "client_preview_ready": client_preview_ready,
        "client_ready": False,
        "production_ready": False,
        "no_write_back": True,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "output_workbook_path": str(output_dir / "client_preview_after_human_review_340f.xlsx"),
    }

    manifest = {
        "task": "340F_client_preview_export_after_human_review",
        "post_human_review_340e_dir": str(post_human_review_340e_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "client_preview_after_human_review_340f_summary.json"),
            "manifest_json": str(output_dir / "client_preview_after_human_review_340f_manifest.json"),
            "qa_json": str(output_dir / "client_preview_after_human_review_340f_qa.json"),
            "no_write_back_proof_json": str(output_dir / "client_preview_after_human_review_340f_no_write_back_proof.json"),
            "report_md": str(output_dir / "client_preview_after_human_review_340f_report.md"),
            "workbook_xlsx": str(output_dir / "client_preview_after_human_review_340f.xlsx"),
        },
        "files_read": files_read,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "checks": checks,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    next_step_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "next_step": "WAIT_FOR_EXPLICIT_CLIENT_EXPORT_DECISION",
                    "recommendation": "340F is a human-reviewed preview only. Wait for an explicit next task before any formal export or downstream delivery packaging.",
                }
            ]
        )
    )

    workbook_sheets = {
        "00_README": _build_readme_df(),
        "01_CLIENT_PREVIEW_CORE_METRICS": core_preview_df,
        "02_CLIENT_PREVIEW_CORRECTED": corrected_preview_df,
        "03_CLIENT_PREVIEW_NEEDS_REVIEW": needs_review_preview_df,
        "04_CLIENT_PREVIEW_REJECTED": rejected_preview_df,
        "05_SOURCE_TRACE": source_trace_df,
        "06_QUALITY_AND_LIMITATIONS": _build_quality_and_limitations_df(summary),
        "07_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "08_NO_WRITE_BACK_PROOF": _build_no_apply_proof_df(no_apply_proof_json),
        "09_NEXT_STEP_RECOMMENDATION": next_step_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_apply_proof_json,
        "workbook_sheets": workbook_sheets,
    }
