from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.client_preview_export_after_human_review_340f import (  # noqa: E402
    READY_DECISION,
    build_client_preview_export_after_human_review_340f,
)
from datefac.trust.client_preview_export_after_human_review_340f_report import WORKBOOK_SHEETS  # noqa: E402
from datefac.trust.post_human_review_sidecar_result_340e import READY_DECISION as READY_340E_DECISION  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _build_reviewed_rows() -> pd.DataFrame:
    metric_plan = [
        ("net_profit", "百万元", "reviewed_after_human"),
        ("net_profit_yoy", "%", "reviewed_after_human"),
        ("revenue", "百万元", "reviewed_after_human"),
        ("net_profit", "百万元", "reviewed_after_human"),
        ("EPS", "元", "reviewed_after_human"),
        ("revenue", "亿元", "reviewed_after_human"),
        ("net_profit", "亿元", "reviewed_after_human"),
        ("EPS", "元", "reviewed_after_human"),
        ("revenue_yoy", "%", "reviewed_after_human"),
        ("net_profit_yoy", "%", "reviewed_after_human"),
        ("net_margin", "%", "reviewed_after_human"),
        ("ROE", "%", "reviewed_after_human"),
        ("EPS", "元", "reviewed_after_human"),
        ("revenue_yoy", "%", "reviewed_after_human"),
        ("revenue_yoy", "%", "reviewed_after_human"),
        ("revenue_yoy", "%", "reviewed_after_human"),
        ("net_profit_yoy", "%", "reviewed_after_human"),
        ("net_profit_yoy", "%", "reviewed_after_human"),
        ("net_margin", "%", "reviewed_after_human"),
        ("net_margin", "%", "reviewed_after_human"),
        ("ROE", "%", "reviewed_after_human"),
        ("ROE", "%", "reviewed_after_human"),
    ]
    rows = []
    for idx, (metric, unit, route) in enumerate(metric_plan, start=1):
        rows.append(
            {
                "final_apply_id": f"340d::{idx:03d}",
                "review_id": f"340b::{idx:03d}",
                "document": f"doc_{(idx % 3) + 1}.pdf",
                "source_sheet": "02_FINAL_APPLY_PLAN",
                "source_row_no": idx + 10,
                "metric_before": metric,
                "year_before": "2027E",
                "value_before": str(100 + idx),
                "unit_before": unit,
                "reviewer_decision": "CONFIRM_AS_REVIEWED",
                "corrected_metric": "",
                "corrected_year": "",
                "corrected_value": "",
                "corrected_unit": "",
                "final_dry_run_action": "FINAL_WOULD_CONFIRM_REVIEWED",
                "final_route_after_apply": route,
                "source_page": idx,
                "evidence": f"evidence {idx}",
                "reviewer_notes": f"note {idx}",
                "risk_flags": "duplicate" if idx % 7 == 0 else "",
                "adoption_action_338d": "HOLD_FOR_HUMAN_REVIEW",
                "dry_run_action_340c": "FINAL_WOULD_CONFIRM_REVIEWED",
                "final_metric": metric,
                "final_year": "2027E",
                "final_value": str(100 + idx),
                "final_unit": unit,
            }
        )
    return pd.DataFrame(rows)


def _build_corrected_rows(pe_unit: str = "倍") -> pd.DataFrame:
    plan = [
        ("net_profit", "net_profit", "2027E", "2001", "百万元"),
        ("EPS", "EPS", "2027E", "2.01", "元"),
        ("net_profit", "net_profit", "2027E", "2003", "百万元"),
        ("net_profit", "net_profit", "2027E", "2004", "百万元"),
        ("net_profit", "net_profit", "2027E", "2005", "百万元"),
        ("net_profit", "net_profit", "2027E", "2006", "百万元"),
        ("net_profit", "net_profit", "2027E", "20.07", "亿元"),
        ("net_profit", "net_profit", "2027E", "20.08", "亿元"),
        ("net_profit", "net_profit", "2027E", "20.09", "亿元"),
        ("PE", "PE", "2027E", "18.0", pe_unit),
        ("PE", "PE", "2028E", "16.5", pe_unit),
        ("PE", "PE", "2029E", "15.0", pe_unit),
    ]
    rows = []
    for local_idx, (metric_before, final_metric, final_year, final_value, final_unit) in enumerate(plan, start=23):
        rows.append(
            {
                "final_apply_id": f"340d::{local_idx:03d}",
                "review_id": f"340b::{local_idx:03d}",
                "document": f"doc_{(local_idx % 4) + 1}.pdf",
                "source_sheet": "02_FINAL_APPLY_PLAN",
                "source_row_no": local_idx + 10,
                "metric_before": metric_before,
                "year_before": "2027E",
                "value_before": "old",
                "unit_before": "%" if metric_before in {"PE", "EPS", "net_profit"} else "",
                "reviewer_decision": "CORRECT_AND_CONFIRM",
                "corrected_metric": final_metric,
                "corrected_year": final_year,
                "corrected_value": final_value,
                "corrected_unit": final_unit,
                "final_dry_run_action": "FINAL_WOULD_APPLY_CORRECTION_AND_CONFIRM",
                "final_route_after_apply": "reviewed_after_human_corrected",
                "source_page": local_idx,
                "evidence": f"evidence {local_idx}",
                "reviewer_notes": f"note {local_idx}",
                "risk_flags": "",
                "adoption_action_338d": "HOLD_FOR_HUMAN_REVIEW",
                "dry_run_action_340c": "FINAL_WOULD_APPLY_CORRECTION_AND_CONFIRM",
                "final_metric": final_metric,
                "final_year": final_year,
                "final_value": final_value,
                "final_unit": final_unit,
            }
        )
    return pd.DataFrame(rows)


def _build_needs_review_rows() -> pd.DataFrame:
    metrics = ["stock_code", "rating", "broker", "broker", "stock_code", "rating", "EPS", "ROE", "stock_code", "report_date", "rating", "broker"]
    units = ["", "", "", "亿元", "亿元", "亿元", "元/股", "%", "", "", "", ""]
    rows = []
    for idx, (metric, unit) in enumerate(zip(metrics, units), start=35):
        rows.append(
            {
                "final_apply_id": f"340d::{idx:03d}",
                "review_id": f"340b::{idx:03d}",
                "document": f"doc_{(idx % 2) + 1}.pdf",
                "source_sheet": "02_FINAL_APPLY_PLAN",
                "source_row_no": idx + 10,
                "metric_before": metric,
                "year_before": "",
                "value_before": "",
                "unit_before": unit,
                "reviewer_decision": "KEEP_NEEDS_REVIEW",
                "corrected_metric": "",
                "corrected_year": "",
                "corrected_value": "",
                "corrected_unit": "",
                "final_dry_run_action": "FINAL_WOULD_KEEP_NEEDS_REVIEW",
                "final_route_after_apply": "needs_review_after_human",
                "source_page": idx,
                "evidence": f"needs evidence {idx}",
                "reviewer_notes": f"needs note {idx}",
                "risk_flags": "",
                "adoption_action_338d": "HOLD_FOR_HUMAN_REVIEW",
                "dry_run_action_340c": "FINAL_WOULD_KEEP_NEEDS_REVIEW",
            }
        )
    return pd.DataFrame(rows)


def _build_rejected_rows() -> pd.DataFrame:
    metrics = ["revenue"] * 8 + ["net_profit"] * 12 + ["EPS"] * 7 + ["PE"] * 3 + ["stock_name"]
    units = ["百万元", "元", "亿元", "", "", "", "亿元", "亿元"] + [""] * 12 + ["元"] * 7 + ["亿元"] * 3 + [""]
    rows = []
    for idx, (metric, unit) in enumerate(zip(metrics, units), start=47):
        rows.append(
            {
                "final_apply_id": f"340d::{idx:03d}",
                "review_id": f"340b::{idx:03d}",
                "document": f"doc_{(idx % 5) + 1}.pdf",
                "source_sheet": "02_FINAL_APPLY_PLAN",
                "source_row_no": idx + 10,
                "metric_before": metric,
                "year_before": "2027E" if metric not in {"stock_name"} else "",
                "value_before": "reject",
                "unit_before": unit,
                "reviewer_decision": "REJECT",
                "corrected_metric": "",
                "corrected_year": "",
                "corrected_value": "",
                "corrected_unit": "",
                "final_dry_run_action": "FINAL_WOULD_REJECT",
                "final_route_after_apply": "rejected_after_human",
                "source_page": idx,
                "evidence": f"reject evidence {idx}",
                "reviewer_notes": f"reject note {idx}",
                "risk_flags": "",
                "adoption_action_338d": "HOLD_FOR_HUMAN_REVIEW",
                "dry_run_action_340c": "FINAL_WOULD_REJECT",
            }
        )
    return pd.DataFrame(rows)


def _build_runtime_artifacts(tmp_path: Path, *, pe_unit: str = "倍", ready: bool = True) -> dict:
    repo_root = tmp_path / "repo"
    input_dir = repo_root / "output" / "post_human_review_sidecar_result_340e"
    output_dir = repo_root / "output" / "client_preview_after_human_review_340f"
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    reviewed_df = _build_reviewed_rows()
    corrected_df = _build_corrected_rows(pe_unit=pe_unit)
    needs_review_df = _build_needs_review_rows()
    rejected_df = _build_rejected_rows()
    source_trace_df = pd.concat([reviewed_df, corrected_df], ignore_index=True)[
        [
            "final_apply_id",
            "review_id",
            "document",
            "source_sheet",
            "source_row_no",
            "source_page",
            "evidence",
            "metric_before",
            "year_before",
            "value_before",
            "unit_before",
            "final_dry_run_action",
            "final_route_after_apply",
        ]
    ]
    summary_payload = {
        "total_input_rows": 77,
        "reviewed_after_human_count": 22,
        "reviewed_after_human_corrected_count": 12,
        "reviewed_after_human_total_count": 34,
        "rejected_after_human_count": 31,
        "needs_review_after_human_count": 12,
        "qa_fail_count": 0 if ready else 1,
        "decision": READY_340E_DECISION if ready else "BAD",
        "client_ready": False,
        "production_ready": False,
    }

    _write_json(alias_asset, {})
    _write_json(scope_asset, {})
    _write_json(input_dir / "post_human_review_sidecar_result_340e_summary.json", summary_payload)
    _write_excel(
        input_dir / "post_human_review_sidecar_result_340e.xlsx",
        {
            "01_REVIEWED_AFTER_HUMAN": reviewed_df,
            "02_REVIEWED_HUMAN_CORRECTED": corrected_df,
            "03_NEEDS_REVIEW_AFTER_HUMAN": needs_review_df,
            "04_REJECTED_AFTER_HUMAN": rejected_df,
            "05_CORRECTION_LOG": corrected_df,
            "06_SOURCE_TRACE": source_trace_df,
            "07_RISK_AUDIT": pd.DataFrame([{"review_id": "340b::001"}]),
            "08_SUMMARY": pd.DataFrame([summary_payload]),
            "09_NO_WRITE_BACK_PROOF": pd.DataFrame([{"path": "x", "unchanged": True}]),
            "10_NEXT_STEP_RECOMMENDATION": pd.DataFrame([{"next_step": "wait"}]),
        },
    )

    artifacts = build_client_preview_export_after_human_review_340f(
        post_human_review_340e_dir=input_dir,
        output_dir=output_dir,
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )
    return {"artifacts": artifacts}


def test_build_client_preview_export_after_human_review_340f(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path)["artifacts"]
    summary = artifacts["summary"]
    assert summary["total_340e_input_rows"] == 77
    assert summary["client_preview_core_metric_count"] == 34
    assert summary["client_preview_confirmed_count"] == 22
    assert summary["client_preview_corrected_count"] == 12
    assert summary["needs_review_after_human_count"] == 12
    assert summary["rejected_after_human_count"] == 31
    assert summary["source_trace_count"] == 34
    assert summary["qa_fail_count"] == 0
    assert summary["client_preview_ready"] is True
    assert summary["decision"] == READY_DECISION
    workbook_sheets = artifacts["workbook_sheets"]
    assert set(WORKBOOK_SHEETS) == set(workbook_sheets.keys())
    corrected_df = workbook_sheets["02_CLIENT_PREVIEW_CORRECTED"]
    assert len(corrected_df) == 12
    assert set(corrected_df["unit"].tolist()) >= {"倍", "元", "百万元", "亿元"}


def test_invalid_340e_state_fails(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path, ready=False)["artifacts"]
    assert artifacts["summary"]["qa_fail_count"] > 0


def test_invalid_pe_unit_fails(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path, pe_unit="%")["artifacts"]
    assert artifacts["summary"]["qa_fail_count"] > 0
    failing_checks = {check["check_name"]: check["status"] for check in artifacts["qa_json"]["checks"]}
    assert failing_checks["quality::pe_unit_is_bei"] == "FAIL"
