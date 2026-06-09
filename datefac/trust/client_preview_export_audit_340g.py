from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.client_preview_export_after_human_review_340f import (
    READY_DECISION as READY_340F_DECISION,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION = "CLIENT_PREVIEW_EXPORT_AUDIT_340G_READY"
NOT_READY_DECISION = "CLIENT_PREVIEW_EXPORT_AUDIT_340G_NOT_READY"

DEFAULT_CLIENT_PREVIEW_340F_DIR = Path(r"D:\_datefac\output\client_preview_after_human_review_340f")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\client_preview_export_audit_340g")

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

PERCENT_METRICS = {"revenue_yoy", "net_profit_yoy", "net_margin", "roe"}
MONEY_METRICS = {"revenue", "net_profit"}
REQUIRED_CORE_COLUMNS = ["document", "metric", "year", "value", "unit", "source_page", "evidence"]
WORKBOOK_SHEETS = [
    "00_README",
    "01_AUDIT_SUMMARY",
    "02_CORE_METRIC_AUDIT",
    "03_UNIT_AUDIT",
    "04_DUPLICATE_AUDIT",
    "05_SOURCE_TRACE_AUDIT",
    "06_NEEDS_REVIEW_AUDIT",
    "07_REJECTED_AUDIT",
    "08_CLAIMS_AUDIT",
    "09_NO_WRITE_BACK_PROOF",
    "10_NEXT_STEP_RECOMMENDATION",
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
        token_lower = token.casefold()
        start = 0
        while True:
            idx = lowered.find(token_lower, start)
            if idx == -1:
                break
            window = lowered[max(0, idx - 50) : idx]
            if "not " not in window and "no " not in window and "false" not in window:
                return True
            start = idx + len(token_lower)
    return False


def _metric_key(metric: Any) -> str:
    return _norm_text(metric).casefold()


def _true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].astype(bool).sum())


def _any_true(frame: pd.DataFrame, column: str) -> bool:
    if frame.empty or column not in frame.columns:
        return False
    return bool(frame[column].astype(bool).any())


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "340G audits the 340F client preview workbook for demo or preview safety and traceability.",
        },
        {
            "topic": "Boundary",
            "message": "This audit does not write back to upstream workbooks and it does not change production behavior.",
        },
        {
            "topic": "Readiness",
            "message": "A passed audit means the workbook is suitable for preview or demo discussion, not for production delivery.",
        },
        {
            "topic": "Claims",
            "message": "The audited preview must remain not production-ready, not client-ready for formal delivery, and not investment advice.",
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


def _build_core_metric_audit_df(core_df: pd.DataFrame, source_trace_df: pd.DataFrame) -> pd.DataFrame:
    if core_df.empty:
        return pd.DataFrame()

    source_trace_ids = {
        (_norm_text(row.get("preview_row_id")), _norm_text(row.get("final_apply_id")), _norm_text(row.get("review_id")))
        for row in source_trace_df.to_dict(orient="records")
    }

    rows: List[Dict[str, Any]] = []
    for row in core_df.to_dict(orient="records"):
        missing_fields = [column for column in REQUIRED_CORE_COLUMNS if not _norm_text(row.get(column))]
        source_trace_found = (
            _norm_text(row.get("preview_row_id")),
            _norm_text(row.get("final_apply_id")),
            _norm_text(row.get("review_id")),
        ) in source_trace_ids
        rows.append(
            {
                "preview_row_id": _norm_text(row.get("preview_row_id")),
                "final_apply_id": _norm_text(row.get("final_apply_id")),
                "review_id": _norm_text(row.get("review_id")),
                "document": _norm_text(row.get("document")),
                "metric": _norm_text(row.get("metric")),
                "year": _norm_text(row.get("year")),
                "value": _norm_text(row.get("value")),
                "unit": _norm_text(row.get("unit")),
                "human_review_status": _norm_text(row.get("human_review_status")),
                "source_page": _norm_text(row.get("source_page")),
                "evidence": _norm_text(row.get("evidence")),
                "reviewer_notes": _norm_text(row.get("reviewer_notes")),
                "source_route": _norm_text(row.get("source_route")),
                "risk_flags": _norm_text(row.get("risk_flags")),
                "required_fields_present": not missing_fields,
                "missing_fields": ", ".join(missing_fields),
                "source_trace_found": source_trace_found,
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_unit_audit_df(core_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for row in core_df.to_dict(orient="records"):
        metric_key = _metric_key(row.get("metric"))
        unit = _norm_text(row.get("unit"))
        money_metric_uses_percent = metric_key in MONEY_METRICS and "%" in unit
        percent_metric_missing_percent = metric_key in PERCENT_METRICS and unit != "%"
        eps_unit_not_yuan = metric_key == "eps" and unit != "元"
        pe_unit_not_bei = metric_key == "pe" and unit != "倍"
        rows.append(
            {
                "preview_row_id": _norm_text(row.get("preview_row_id")),
                "document": _norm_text(row.get("document")),
                "metric": _norm_text(row.get("metric")),
                "year": _norm_text(row.get("year")),
                "unit": unit,
                "money_metric_uses_percent": money_metric_uses_percent,
                "percent_metric_missing_percent": percent_metric_missing_percent,
                "eps_unit_not_yuan": eps_unit_not_yuan,
                "pe_unit_not_bei": pe_unit_not_bei,
                "unit_issue": any(
                    [
                        money_metric_uses_percent,
                        percent_metric_missing_percent,
                        eps_unit_not_yuan,
                        pe_unit_not_bei,
                    ]
                ),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_duplicate_audit_df(core_df: pd.DataFrame) -> pd.DataFrame:
    if core_df.empty:
        return pd.DataFrame()

    records: List[Dict[str, Any]] = []
    grouped = core_df.groupby(["document", "metric", "year"], dropna=False)
    for (document, metric, year), group in grouped:
        preview_row_ids = ", ".join(_norm_text(value) for value in group["preview_row_id"].tolist())
        risk_text = " ".join(_norm_text(value) for value in group.get("risk_flags", pd.Series(dtype=object)).tolist()).casefold()
        justified = "duplicate_justified" in risk_text
        issue = len(group) > 1 and not justified
        records.append(
            {
                "document": _norm_text(document),
                "metric": _norm_text(metric),
                "year": _norm_text(year),
                "row_count": int(len(group)),
                "preview_row_ids": preview_row_ids,
                "justified_duplicate": justified,
                "duplicate_issue": issue,
            }
        )
    return _clean_frame(pd.DataFrame(records))


def _build_source_trace_audit_df(core_df: pd.DataFrame, source_trace_df: pd.DataFrame) -> pd.DataFrame:
    source_lookup = {
        (
            _norm_text(row.get("preview_row_id")),
            _norm_text(row.get("final_apply_id")),
            _norm_text(row.get("review_id")),
        ): row
        for row in source_trace_df.to_dict(orient="records")
    }
    rows: List[Dict[str, Any]] = []
    for row in core_df.to_dict(orient="records"):
        key = (
            _norm_text(row.get("preview_row_id")),
            _norm_text(row.get("final_apply_id")),
            _norm_text(row.get("review_id")),
        )
        source_row = source_lookup.get(key, {})
        missing_required = [
            field
            for field in ["document", "metric", "year", "value", "unit", "source_page", "evidence"]
            if not _norm_text(source_row.get(field if field != "metric" else "metric"))
        ]
        rows.append(
            {
                "preview_row_id": key[0],
                "final_apply_id": key[1],
                "review_id": key[2],
                "source_trace_found": bool(source_row),
                "missing_required_trace_fields": ", ".join(missing_required),
                "trace_issue": (not bool(source_row)) or bool(missing_required),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_filtered_audit_df(filtered_df: pd.DataFrame, core_df: pd.DataFrame, *, status_name: str) -> pd.DataFrame:
    core_keys = {
        (_norm_text(row.get("final_apply_id")), _norm_text(row.get("review_id")))
        for row in core_df.to_dict(orient="records")
    }
    rows: List[Dict[str, Any]] = []
    for row in filtered_df.to_dict(orient="records"):
        key = (_norm_text(row.get("final_apply_id")), _norm_text(row.get("review_id")))
        rows.append(
            {
                "final_apply_id": key[0],
                "review_id": key[1],
                "document": _norm_text(row.get("document")),
                "metric": _norm_text(row.get("metric")),
                "year": _norm_text(row.get("year")),
                "human_review_status": status_name,
                "appears_in_core_preview": key in core_keys,
                "source_page": _norm_text(row.get("source_page")),
                "evidence": _norm_text(row.get("evidence")),
                "reviewer_notes": _norm_text(row.get("reviewer_notes")),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_claims_audit_df(
    readme_df: pd.DataFrame,
    summary_340f: Mapping[str, Any],
) -> pd.DataFrame:
    readme_text = "\n".join(readme_df.get("message", pd.Series(dtype=object)).astype(str).tolist())
    rows = [
        {
            "claim_check": "client_ready_false",
            "status": "PASS" if not summary_340f.get("client_ready", False) else "FAIL",
            "detail": str(summary_340f.get("client_ready", "")),
            "unsafe_claim": bool(summary_340f.get("client_ready", False)),
        },
        {
            "claim_check": "production_ready_false",
            "status": "PASS" if not summary_340f.get("production_ready", False) else "FAIL",
            "detail": str(summary_340f.get("production_ready", "")),
            "unsafe_claim": bool(summary_340f.get("production_ready", False)),
        },
        {
            "claim_check": "no_investment_advice_claim",
            "status": "PASS" if not _contains_forbidden_claim(readme_text, ["investment advice"]) else "FAIL",
            "detail": "README text checked",
            "unsafe_claim": _contains_forbidden_claim(readme_text, ["investment advice"]),
        },
        {
            "claim_check": "no_client_ready_claim",
            "status": "PASS" if not _contains_forbidden_claim(readme_text, ["client-ready", "client ready"]) else "FAIL",
            "detail": "README text checked",
            "unsafe_claim": _contains_forbidden_claim(readme_text, ["client-ready", "client ready"]),
        },
        {
            "claim_check": "no_production_ready_claim",
            "status": "PASS" if not _contains_forbidden_claim(readme_text, ["production-ready", "production ready"]) else "FAIL",
            "detail": "README text checked",
            "unsafe_claim": _contains_forbidden_claim(readme_text, ["production-ready", "production ready"]),
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_client_preview_export_audit_340g(
    *,
    client_preview_340f_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    workbook_340f = client_preview_340f_dir / "client_preview_after_human_review_340f.xlsx"
    summary_340f_path = client_preview_340f_dir / "client_preview_after_human_review_340f_summary.json"

    files_read = [str(summary_340f_path), str(workbook_340f)]
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    input_hashes_before = {str(workbook_340f): sha256_file(workbook_340f)}

    summary_340f = _read_json(summary_340f_path) if summary_340f_path.exists() else {}
    readme_df = _read_excel(workbook_340f, "00_README")
    core_df = _read_excel(workbook_340f, "01_CLIENT_PREVIEW_CORE_METRICS")
    corrected_df = _read_excel(workbook_340f, "02_CLIENT_PREVIEW_CORRECTED")
    needs_review_df = _read_excel(workbook_340f, "03_CLIENT_PREVIEW_NEEDS_REVIEW")
    rejected_df = _read_excel(workbook_340f, "04_CLIENT_PREVIEW_REJECTED")
    source_trace_df = _read_excel(workbook_340f, "05_SOURCE_TRACE")

    core_metric_audit_df = _build_core_metric_audit_df(core_df, source_trace_df)
    unit_audit_df = _build_unit_audit_df(core_df)
    duplicate_audit_df = _build_duplicate_audit_df(core_df)
    source_trace_audit_df = _build_source_trace_audit_df(core_df, source_trace_df)
    needs_review_audit_df = _build_filtered_audit_df(
        needs_review_df,
        core_df,
        status_name="needs_review_after_human",
    )
    rejected_audit_df = _build_filtered_audit_df(
        rejected_df,
        core_df,
        status_name="rejected_after_human",
    )
    claims_audit_df = _build_claims_audit_df(readme_df, summary_340f)

    output_dir.mkdir(parents=True, exist_ok=True)

    input_hashes_after = {str(workbook_340f): sha256_file(workbook_340f)}
    upstream_unchanged = input_hashes_before == input_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_apply_proof_json = build_no_apply_proof(
        stage="340G",
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
        bool(no_apply_proof_json.get("no_official_asset_modification_during_340g"))
        and upstream_unchanged
    )

    audited_core_metric_count = int(len(core_df))
    confirmed_count = int((core_df.get("human_review_status", pd.Series(dtype=object)).astype(str) == "reviewed_after_human").sum()) if not core_df.empty else 0
    corrected_count = int((core_df.get("human_review_status", pd.Series(dtype=object)).astype(str) == "reviewed_after_human_corrected").sum()) if not core_df.empty else 0
    needs_review_count = int(len(needs_review_df))
    rejected_count = int(len(rejected_df))
    duplicate_issue_count = _true_count(duplicate_audit_df, "duplicate_issue")
    unit_issue_count = _true_count(unit_audit_df, "unit_issue")
    missing_source_trace_count = _true_count(source_trace_audit_df, "trace_issue")
    unsafe_claim_count = _true_count(claims_audit_df, "unsafe_claim")

    corrected_keys = {
        (_norm_text(row.get("preview_row_id")), _norm_text(row.get("final_apply_id")), _norm_text(row.get("review_id")))
        for row in corrected_df.to_dict(orient="records")
    }
    corrected_core_keys = {
        (_norm_text(row.get("preview_row_id")), _norm_text(row.get("final_apply_id")), _norm_text(row.get("review_id")))
        for row in core_df.to_dict(orient="records")
        if _norm_text(row.get("human_review_status")) == "reviewed_after_human_corrected"
    }
    corrected_rows_match = corrected_keys == corrected_core_keys

    all_core_fields_present = bool(core_metric_audit_df["required_fields_present"].all()) if not core_metric_audit_df.empty else False
    rejected_not_in_core = not _any_true(rejected_audit_df, "appears_in_core_preview")
    needs_review_not_in_core = not _any_true(needs_review_audit_df, "appears_in_core_preview")
    no_long_sheet_names = all(len(name) <= 31 for name in WORKBOOK_SHEETS)

    checks = [
        {"check_name": "inputs::340f_workbook_exists", "status": "PASS" if workbook_340f.exists() else "FAIL", "detail": str(workbook_340f)},
        {
            "check_name": "readiness::340f_ready",
            "status": "PASS" if summary_340f.get("decision") == READY_340F_DECISION and summary_340f.get("qa_fail_count") == 0 and bool(summary_340f.get("client_preview_ready")) else "FAIL",
            "detail": json.dumps(summary_340f, ensure_ascii=False),
        },
        {"check_name": "quality::audited_core_metric_count", "status": "PASS" if audited_core_metric_count == 34 else "FAIL", "detail": str(audited_core_metric_count)},
        {"check_name": "quality::confirmed_count", "status": "PASS" if confirmed_count == 22 else "FAIL", "detail": str(confirmed_count)},
        {"check_name": "quality::corrected_count", "status": "PASS" if corrected_count == 12 else "FAIL", "detail": str(corrected_count)},
        {"check_name": "quality::needs_review_count", "status": "PASS" if needs_review_count == 12 else "FAIL", "detail": str(needs_review_count)},
        {"check_name": "quality::rejected_count", "status": "PASS" if rejected_count == 31 else "FAIL", "detail": str(rejected_count)},
        {"check_name": "quality::all_core_rows_have_required_fields", "status": "PASS" if all_core_fields_present else "FAIL", "detail": "document/metric/year/value/unit/source_page/evidence checked"},
        {"check_name": "quality::corrected_rows_use_corrected_values", "status": "PASS" if corrected_rows_match and corrected_count == len(corrected_df) else "FAIL", "detail": f"core_corrected={corrected_count}, corrected_sheet={len(corrected_df)}"},
        {"check_name": "quality::money_metrics_not_percent", "status": "PASS" if unit_audit_df_money_ok(unit_audit_df) else "FAIL", "detail": "money metrics unit rules checked"},
        {"check_name": "quality::percent_metrics_use_percent", "status": "PASS" if unit_audit_df_percent_ok(unit_audit_df) else "FAIL", "detail": "percent metrics unit rules checked"},
        {"check_name": "quality::eps_unit_is_yuan", "status": "PASS" if unit_audit_df_eps_ok(unit_audit_df) else "FAIL", "detail": "EPS rows checked"},
        {"check_name": "quality::pe_unit_is_bei", "status": "PASS" if unit_audit_df_pe_ok(unit_audit_df) else "FAIL", "detail": "PE rows checked"},
        {"check_name": "quality::no_duplicate_document_metric_year", "status": "PASS" if duplicate_issue_count == 0 else "FAIL", "detail": str(duplicate_issue_count)},
        {"check_name": "quality::rejected_rows_not_in_core", "status": "PASS" if rejected_not_in_core else "FAIL", "detail": str(_true_count(rejected_audit_df, "appears_in_core_preview"))},
        {"check_name": "quality::needs_review_rows_not_in_core", "status": "PASS" if needs_review_not_in_core else "FAIL", "detail": str(_true_count(needs_review_audit_df, "appears_in_core_preview"))},
        {"check_name": "quality::no_sheet_name_exceeds_limit", "status": "PASS" if no_long_sheet_names else "FAIL", "detail": json.dumps({name: len(name) for name in WORKBOOK_SHEETS}, ensure_ascii=False)},
        {"check_name": "claims::client_ready_false", "status": "PASS" if not summary_340f.get("client_ready", False) else "FAIL", "detail": str(summary_340f.get("client_ready", ""))},
        {"check_name": "claims::production_ready_false", "status": "PASS" if not summary_340f.get("production_ready", False) else "FAIL", "detail": str(summary_340f.get("production_ready", ""))},
        {"check_name": "claims::no_investment_advice_claim", "status": "PASS" if unsafe_claim_count == 0 else "FAIL", "detail": str(unsafe_claim_count)},
        {"check_name": "safety::no_write_back_to_upstream_workbook", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"upstream_unchanged": upstream_unchanged, "official_assets_unchanged": bool(no_apply_proof_json.get("no_official_asset_modification_during_340g"))}, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    client_preview_audit_passed = qa_fail_count == 0
    decision = READY_DECISION if client_preview_audit_passed else NOT_READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "audited_core_metric_count": audited_core_metric_count,
        "confirmed_count": confirmed_count,
        "corrected_count": corrected_count,
        "needs_review_count": needs_review_count,
        "rejected_count": rejected_count,
        "duplicate_issue_count": duplicate_issue_count,
        "unit_issue_count": unit_issue_count,
        "missing_source_trace_count": missing_source_trace_count,
        "unsafe_claim_count": unsafe_claim_count,
        "client_preview_audit_passed": client_preview_audit_passed,
        "client_ready": False,
        "production_ready": False,
        "no_write_back": True,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "output_workbook_path": str(output_dir / "client_preview_export_audit_340g.xlsx"),
    }

    manifest = {
        "task": "340G_client_preview_export_audit",
        "client_preview_340f_dir": str(client_preview_340f_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "client_preview_export_audit_340g_summary.json"),
            "manifest_json": str(output_dir / "client_preview_export_audit_340g_manifest.json"),
            "qa_json": str(output_dir / "client_preview_export_audit_340g_qa.json"),
            "report_md": str(output_dir / "client_preview_export_audit_340g_report.md"),
            "no_write_back_proof_json": str(output_dir / "client_preview_export_audit_340g_no_write_back_proof.json"),
            "workbook_xlsx": str(output_dir / "client_preview_export_audit_340g.xlsx"),
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
                    "next_step": "WAIT_FOR_EXPLICIT_PREVIEW_HANDOFF_TASK",
                    "recommendation": "340G confirms preview suitability only. Wait for an explicit next task before any formal delivery or production-facing packaging.",
                }
            ]
        )
    )

    workbook_sheets = {
        "00_README": _build_readme_df(),
        "01_AUDIT_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_CORE_METRIC_AUDIT": core_metric_audit_df,
        "03_UNIT_AUDIT": unit_audit_df,
        "04_DUPLICATE_AUDIT": duplicate_audit_df,
        "05_SOURCE_TRACE_AUDIT": source_trace_audit_df,
        "06_NEEDS_REVIEW_AUDIT": needs_review_audit_df,
        "07_REJECTED_AUDIT": rejected_audit_df,
        "08_CLAIMS_AUDIT": claims_audit_df,
        "09_NO_WRITE_BACK_PROOF": _build_no_apply_proof_df(no_apply_proof_json),
        "10_NEXT_STEP_RECOMMENDATION": next_step_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_apply_proof_json,
        "workbook_sheets": workbook_sheets,
    }


def unit_audit_df_money_ok(unit_audit_df: pd.DataFrame) -> bool:
    return not _any_true(unit_audit_df, "money_metric_uses_percent")


def unit_audit_df_percent_ok(unit_audit_df: pd.DataFrame) -> bool:
    return not _any_true(unit_audit_df, "percent_metric_missing_percent")


def unit_audit_df_eps_ok(unit_audit_df: pd.DataFrame) -> bool:
    return not _any_true(unit_audit_df, "eps_unit_not_yuan")


def unit_audit_df_pe_ok(unit_audit_df: pd.DataFrame) -> bool:
    return not _any_true(unit_audit_df, "pe_unit_not_bei")
