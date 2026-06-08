from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.client_facing_clean_export_335a import (  # noqa: E402
    CUSTOMER_SHEETS,
    READY_330K4_DECISION,
    READY_331B_DECISION,
    READY_332A_DECISION,
    build_client_facing_clean_export_335a,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _reviewed_row(candidate_id: str, *, confirmed: bool, idx: int) -> dict:
    return {
        "candidate_id": candidate_id,
        "pdf_document_id": f"doc_{idx % 7}.pdf",
        "source_page": idx + 1,
        "metric_label_raw": "营业收入",
        "normalized_metric": "revenue",
        "year": 2024 + (idx % 3),
        "value": 100 + idx,
        "final_unit_preview": "RMB_mn",
        "current_unit": "RMB_mn",
        "reviewer_unit": "RMB_mn" if confirmed else "",
        "confidence_level": "HIGH",
        "confidence_score": 100,
        "upstream_routing_decision": "TRUSTED",
        "preview_routing_bucket": "TRUSTED_PREVIEW" if not confirmed else "REVIEWED_UNIT_CONFIRMED",
        "risk_flags": "",
        "source_evidence_refs": f"ref-{candidate_id}",
        "source_evidence_text": f"evidence-{candidate_id}",
        "reviewer_decision": "CONFIRM_UNIT" if confirmed else "",
        "reviewer_notes": "confirmed" if confirmed else "",
        "dry_run_action": "" if not confirmed else "WOULD_CONFIRM_OR_SET_UNIT",
        "preview_row_origin": "330K3_CONFIRMED_FROM_UNIT_REVIEW" if confirmed else "330L_TRUSTED_BASELINE",
    }


def _rejected_row(candidate_id: str, idx: int) -> dict:
    return {
        "candidate_id": candidate_id,
        "pdf_document_id": f"reject_{idx % 5}.pdf",
        "source_page": idx + 10,
        "metric_label_raw": "eps",
        "normalized_metric": "eps",
        "year": "2025",
        "value": idx,
        "final_unit_preview": "",
        "current_unit": "",
        "reviewer_unit": "",
        "confidence_level": "LOW",
        "confidence_score": 44,
        "upstream_routing_decision": "REVIEW_REQUIRED",
        "preview_routing_bucket": "HUMAN_REJECTED_BY_UNIT_REVIEW",
        "risk_flags": "LABEL_AMBIGUOUS | UNIT_CONFLICT | UNIT_UNKNOWN",
        "source_evidence_refs": f"reject-ref-{candidate_id}",
        "source_evidence_text": f"reject-evidence-{candidate_id}",
        "reviewer_decision": "REJECT_UNIT",
        "reviewer_notes": "false positive",
        "dry_run_action": "WOULD_REJECT_FROM_TRUSTED_EXPORT",
        "preview_row_origin": "330K3_REJECTED_FROM_UNIT_REVIEW",
    }


def _needs_review_row(candidate_id: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "pdf_document_id": "needs_review.pdf",
        "source_page": 26,
        "metric_label_raw": "毛利率",
        "normalized_metric": "gross_margin",
        "year": 2024,
        "value": 2025,
        "final_unit_preview": "percent",
        "current_unit": "percent",
        "reviewer_unit": "percent",
        "confidence_level": "MEDIUM",
        "confidence_score": 70,
        "upstream_routing_decision": "REVIEW_REQUIRED",
        "preview_routing_bucket": "REMAINING_REVIEW_REQUIRED",
        "risk_flags": "UNIT_CONFLICT",
        "source_evidence_refs": "needs-ref",
        "source_evidence_text": "needs-evidence",
        "reviewer_decision": "NEEDS_MORE_CONTEXT",
        "reviewer_notes": "Needs original source check.",
        "dry_run_action": "WOULD_KEEP_REVIEW_REQUIRED_FOR_SOURCE_CHECK",
        "preview_row_origin": "330K3_STILL_REVIEW_REQUIRED",
    }


def test_build_client_facing_clean_export_335a(tmp_path: Path) -> None:
    reviewed_dir = tmp_path / "reviewed_export_refresh_330k4"
    demo_331b_dir = tmp_path / "demo_packaging_331b"
    audit_332a_dir = tmp_path / "demo_release_audit_332a"
    client_330l_dir = tmp_path / "client_style_export_preview_330l"
    output_dir = tmp_path / "client_facing_clean_export_335a"
    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"

    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    _write_json(
        reviewed_dir / "reviewed_export_refresh_330k4_summary.json",
        {
            "decision": READY_330K4_DECISION,
            "qa_fail_count": 0,
            "original_trusted_sheet_row_count": 96,
            "reviewed_unit_confirmed_count": 2,
            "reviewed_trusted_preview_row_count": 98,
            "human_rejected_row_count": 18,
            "remaining_review_required_after_unit_review_count": 1,
            "apply_plan_row_count": 21,
        },
    )
    _write_json(
        reviewed_dir / "reviewed_export_refresh_330k4_qa.json",
        {"qa_fail_count": 0},
    )
    _write_json(
        demo_331b_dir / "demo_packaging_331b_summary.json",
        {"decision": READY_331B_DECISION, "qa_fail_count": 0},
    )
    _write_json(
        audit_332a_dir / "demo_release_audit_332a_summary.json",
        {"decision": READY_332A_DECISION, "qa_fail_count": 0},
    )
    _write_json(
        client_330l_dir / "client_style_export_preview_330l_summary.json",
        {"trusted_sheet_row_count": 96},
    )

    reviewed_rows = [_reviewed_row(f"base-{i}", confirmed=False, idx=i) for i in range(96)]
    reviewed_rows.extend(
        [_reviewed_row(f"confirm-{i}", confirmed=True, idx=96 + i) for i in range(2)]
    )
    rejected_rows = [_rejected_row(f"reject-{i}", i) for i in range(18)]
    needs_row = [_needs_review_row("needs-1")]
    trace_rows = [
        {
            "candidate_id": row["candidate_id"],
            "pdf_document_id": row["pdf_document_id"],
            "metric_label_raw": row["metric_label_raw"],
            "normalized_metric": row["normalized_metric"],
            "year": row["year"],
            "value": row["value"],
            "current_unit": row["current_unit"],
            "reviewer_unit": row["reviewer_unit"],
            "final_unit_preview": row["final_unit_preview"],
            "source_page": row["source_page"],
            "source_evidence_refs": row["source_evidence_refs"],
            "source_evidence_text": row["source_evidence_text"],
            "parser_sources": "pdfplumber",
            "provenance_summary": "trace",
            "confidence_level": row["confidence_level"],
            "confidence_score": row["confidence_score"],
            "upstream_routing_decision": row["upstream_routing_decision"],
            "risk_flags": row["risk_flags"],
            "reviewer_decision": row["reviewer_decision"],
            "reviewer_notes": row["reviewer_notes"],
            "dry_run_action": row["dry_run_action"],
            "preview_routing_bucket": row["preview_routing_bucket"],
            "preview_row_origin": row["preview_row_origin"],
        }
        for row in [*reviewed_rows[-2:], *rejected_rows, *needs_row]
    ]

    reviewed_dir.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(
        reviewed_dir / "reviewed_export_refresh_330k4_preview.xlsx",
        engine="openpyxl",
    ) as writer:
        pd.DataFrame([{"section": "title", "content": "demo"}]).to_excel(
            writer, sheet_name="00_README", index=False
        )
        pd.DataFrame(reviewed_rows).to_excel(
            writer, sheet_name="01_REVIEWED_TRUSTED_PREVIEW", index=False
        )
        pd.DataFrame(needs_row).to_excel(
            writer, sheet_name="02_REMAINING_REVIEW_REQUIRED", index=False
        )
        pd.DataFrame(rejected_rows).to_excel(
            writer, sheet_name="03_HUMAN_REJECTED_BY_UNIT_REV", index=False
        )
        pd.DataFrame(trace_rows).to_excel(
            writer, sheet_name="04_APPLY_PLAN_TRACE", index=False
        )
        pd.DataFrame([{"metric": "source_page_missing_count", "value": 0}]).to_excel(
            writer, sheet_name="05_QA_CONTEXT", index=False
        )

    artifacts = build_client_facing_clean_export_335a(
        reviewed_export_refresh_dir=reviewed_dir,
        demo_packaging_331b_dir=demo_331b_dir,
        demo_release_audit_dir=audit_332a_dir,
        client_style_export_preview_dir=client_330l_dir,
        output_dir=output_dir,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
        files_read=[],
    )

    summary = artifacts["summary"]
    assert summary["decision"] == "CLIENT_FACING_CLEAN_EXPORT_PREVIEW_READY"
    assert summary["core_metrics_reviewed_row_count"] == 98
    assert summary["needs_review_row_count"] == 1
    assert summary["excluded_or_rejected_row_count"] == 18

    reviewed_df = artifacts["core_metrics_reviewed_df"]
    needs_df = artifacts["needs_review_df"]
    rejected_df = artifacts["excluded_or_rejected_df"]
    trace_df = artifacts["source_trace_df"]

    assert list(reviewed_df.columns) == [
        "row_no",
        "document",
        "metric",
        "year",
        "value",
        "unit",
        "source_page",
        "confidence_status",
        "review_status",
        "source_evidence",
        "notes",
    ]
    assert "dry_run_action" not in reviewed_df.columns
    assert "preview_routing_bucket" not in reviewed_df.columns
    assert len(needs_df) == 1
    assert len(rejected_df) == 18
    assert len(trace_df) == 117
    assert "internal_candidate_id" in trace_df.columns
    assert set(trace_df["customer_sheet"].unique()) == {
        CUSTOMER_SHEETS["reviewed"],
        CUSTOMER_SHEETS["needs_review"],
        CUSTOMER_SHEETS["rejected"],
    }
    assert reviewed_df.loc[96, "review_status"] == "human_unit_confirmed"
    assert needs_df.loc[0, "recommended_action"] == "Verify the value and unit against the source PDF before use."
