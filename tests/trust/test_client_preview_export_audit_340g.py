from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.client_preview_export_audit_340g import (  # noqa: E402
    READY_DECISION,
    WORKBOOK_SHEETS,
    build_client_preview_export_audit_340g,
)
from datefac.trust.client_preview_export_after_human_review_340f import READY_DECISION as READY_340F_DECISION  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _build_core_rows(*, duplicate: bool = False, bad_pe_unit: bool = False) -> pd.DataFrame:
    rows = []
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
        ("net_profit", "百万元", "reviewed_after_human_corrected"),
        ("EPS", "元", "reviewed_after_human_corrected"),
        ("net_profit", "百万元", "reviewed_after_human_corrected"),
        ("net_profit", "百万元", "reviewed_after_human_corrected"),
        ("net_profit", "百万元", "reviewed_after_human_corrected"),
        ("net_profit", "百万元", "reviewed_after_human_corrected"),
        ("net_profit", "亿元", "reviewed_after_human_corrected"),
        ("net_profit", "亿元", "reviewed_after_human_corrected"),
        ("net_profit", "亿元", "reviewed_after_human_corrected"),
        ("PE", "倍" if not bad_pe_unit else "%", "reviewed_after_human_corrected"),
        ("PE", "倍" if not bad_pe_unit else "%", "reviewed_after_human_corrected"),
        ("PE", "倍" if not bad_pe_unit else "%", "reviewed_after_human_corrected"),
    ]
    for idx, (metric, unit, status) in enumerate(metric_plan, start=1):
        document = f"doc_{idx}.pdf"
        year = "2027E"
        if duplicate and idx == 34:
            document = "doc_2.pdf"
            metric = "net_profit_yoy"
            year = "2027E"
            unit = "%"
            status = "reviewed_after_human"
        rows.append(
            {
                "preview_row_id": f"340f::{idx:03d}",
                "final_apply_id": f"340d::{idx:03d}",
                "review_id": f"340b::{idx:03d}",
                "document": document,
                "company_or_document_hint": Path(document).stem,
                "metric": metric,
                "metric_display_name": metric,
                "year": year,
                "value": str(100 + idx),
                "unit": unit,
                "human_review_status": status,
                "human_review_status_display": status,
                "source_page": idx,
                "evidence": f"evidence {idx}",
                "reviewer_notes": f"note {idx}",
                "source_route": status,
                "risk_flags": "",
                "source_sheet": "02_FINAL_APPLY_PLAN",
                "source_row_no": idx + 10,
            }
        )
    return pd.DataFrame(rows)


def _build_runtime_artifacts(tmp_path: Path, *, duplicate: bool = False, bad_pe_unit: bool = False, unsafe_claim: bool = False, ready: bool = True) -> dict:
    repo_root = tmp_path / "repo"
    input_dir = repo_root / "output" / "client_preview_after_human_review_340f"
    output_dir = repo_root / "output" / "client_preview_export_audit_340g"
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    core_df = _build_core_rows(duplicate=duplicate, bad_pe_unit=bad_pe_unit)
    corrected_df = core_df[core_df["human_review_status"] == "reviewed_after_human_corrected"].copy()
    needs_review_df = pd.DataFrame(
        [
            {
                "final_apply_id": f"340d::{idx:03d}",
                "review_id": f"340b::{idx:03d}",
                "document": f"needs_{idx}.pdf",
                "company_or_document_hint": f"needs_{idx}",
                "metric": "rating",
                "metric_display_name": "rating",
                "year": "",
                "value": "",
                "unit": "",
                "human_review_status": "needs_review_after_human",
                "source_page": idx,
                "evidence": f"needs evidence {idx}",
                "reviewer_notes": f"needs note {idx}",
                "source_route": "needs_review_after_human",
                "risk_flags": "",
                "source_sheet": "02_FINAL_APPLY_PLAN",
                "source_row_no": idx + 10,
            }
            for idx in range(35, 47)
        ]
    )
    rejected_df = pd.DataFrame(
        [
            {
                "final_apply_id": f"340d::{idx:03d}",
                "review_id": f"340b::{idx:03d}",
                "document": f"reject_{idx}.pdf",
                "company_or_document_hint": f"reject_{idx}",
                "metric": "revenue",
                "metric_display_name": "revenue",
                "year": "2027E",
                "value": "reject",
                "unit": "百万元",
                "human_review_status": "rejected_after_human",
                "source_page": idx,
                "evidence": f"reject evidence {idx}",
                "reviewer_notes": f"reject note {idx}",
                "source_route": "rejected_after_human",
                "risk_flags": "",
                "source_sheet": "02_FINAL_APPLY_PLAN",
                "source_row_no": idx + 10,
            }
            for idx in range(47, 78)
        ]
    )
    source_trace_df = core_df[
        [
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
    ].copy()
    readme_messages = [
        "This is a human-reviewed client preview built from the 340E post-human-review sidecar result.",
        "This preview is not production-ready and not client-ready for formal delivery.",
        "This preview is not investment advice." if not unsafe_claim else "This preview is investment advice.",
        "Source evidence, source page, reviewer notes, and provenance are included for traceability.",
        "Rows marked needs_review or rejected are not included in the core preview table.",
        "AI decisions were not directly written back; human review and deterministic validation were used.",
    ]
    readme_df = pd.DataFrame([{"topic": f"topic_{idx}", "message": message} for idx, message in enumerate(readme_messages, start=1)])
    summary_payload = {
        "total_340e_input_rows": 77,
        "client_preview_core_metric_count": 34,
        "client_preview_confirmed_count": 22,
        "client_preview_corrected_count": 12,
        "needs_review_after_human_count": 12,
        "rejected_after_human_count": 31,
        "source_trace_count": 34,
        "client_preview_ready": ready,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0 if ready else 1,
        "decision": READY_340F_DECISION if ready else "BAD",
    }

    _write_json(alias_asset, {})
    _write_json(scope_asset, {})
    _write_json(input_dir / "client_preview_after_human_review_340f_summary.json", summary_payload)
    _write_excel(
        input_dir / "client_preview_after_human_review_340f.xlsx",
        {
            "00_README": readme_df,
            "01_CLIENT_PREVIEW_CORE_METRICS": core_df,
            "02_CLIENT_PREVIEW_CORRECTED": corrected_df,
            "03_CLIENT_PREVIEW_NEEDS_REVIEW": needs_review_df,
            "04_CLIENT_PREVIEW_REJECTED": rejected_df,
            "05_SOURCE_TRACE": source_trace_df,
            "06_QUALITY_AND_LIMITATIONS": pd.DataFrame([{"category": "Scope", "message": "Preview only"}]),
            "07_SUMMARY": pd.DataFrame([summary_payload]),
            "08_NO_WRITE_BACK_PROOF": pd.DataFrame([{"path": "x", "unchanged": True}]),
            "09_NEXT_STEP_RECOMMENDATION": pd.DataFrame([{"next_step": "wait"}]),
        },
    )

    artifacts = build_client_preview_export_audit_340g(
        client_preview_340f_dir=input_dir,
        output_dir=output_dir,
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )
    return {"artifacts": artifacts}


def test_build_client_preview_export_audit_340g(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path)["artifacts"]
    summary = artifacts["summary"]
    assert summary["audited_core_metric_count"] == 34
    assert summary["confirmed_count"] == 22
    assert summary["corrected_count"] == 12
    assert summary["needs_review_count"] == 12
    assert summary["rejected_count"] == 31
    assert summary["duplicate_issue_count"] == 0
    assert summary["unit_issue_count"] == 0
    assert summary["missing_source_trace_count"] == 0
    assert summary["unsafe_claim_count"] == 0
    assert summary["qa_fail_count"] == 0
    assert summary["client_preview_audit_passed"] is True
    assert summary["decision"] == READY_DECISION
    assert set(artifacts["workbook_sheets"].keys()) == set(WORKBOOK_SHEETS)


def test_duplicate_issue_fails(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path, duplicate=True)["artifacts"]
    assert artifacts["summary"]["qa_fail_count"] > 0
    assert artifacts["summary"]["duplicate_issue_count"] > 0


def test_claim_or_unit_issue_fails(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path, bad_pe_unit=True, unsafe_claim=True)["artifacts"]
    assert artifacts["summary"]["qa_fail_count"] > 0
    assert artifacts["summary"]["unit_issue_count"] > 0
    assert artifacts["summary"]["unsafe_claim_count"] > 0
