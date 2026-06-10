from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.llm_assisted_review_adjudication_342k import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_llm_assisted_review_adjudication_342k,
)
from datefac.benchmark.llm_assisted_review_adjudication_342k_report import WORKBOOK_SHEETS  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _seed_342_inputs(root: Path, *, ready_342j: bool = True) -> tuple[Path, Path, Path]:
    preview_342j_dir = root / "output" / "table_first_reviewed_client_preview_pilot_342j"
    sidecar_342i_dir = root / "output" / "table_first_post_human_review_sidecar_result_342i"
    review_342g_dir = root / "output" / "table_first_extraction_review_package_342g"
    preview_342j_dir.mkdir(parents=True, exist_ok=True)
    sidecar_342i_dir.mkdir(parents=True, exist_ok=True)
    review_342g_dir.mkdir(parents=True, exist_ok=True)

    summary_342j = {
        "decision": "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY" if ready_342j else "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_NOT_READY",
        "ready_for_342k": ready_342j,
        "input_review_template_row_count": 6,
        "reviewed_row_count": 2,
        "pending_review_count": 4,
        "reviewed_preview_row_count": 2,
        "confirmed_preview_row_count": 1,
        "corrected_preview_row_count": 1,
        "rejected_in_batch_count": 1,
        "qa_fail_count": 0 if ready_342j else 1,
        "client_ready": False,
        "production_ready": False,
    }
    _write_json(preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j_summary.json", summary_342j)
    _write_json(preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j_qa.json", {"qa_fail_count": 0 if ready_342j else 1, "checks": []})
    _write_json(preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j_no_write_back_proof.json", {"upstream_workbooks_unchanged": True})
    (preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j_report.md").write_text("342J report", encoding="utf-8")
    _write_excel(
        preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j.xlsx",
        {
            "01_PREVIEW_SUMMARY": pd.DataFrame([summary_342j]),
            "03_REVIEWED_PREVIEW": pd.DataFrame(
                [
                    {
                        "review_item_id": "item_done_1",
                        "reviewer_decision": "CONFIRM_CELL",
                        "preview_status": "REVIEWED_PREVIEW",
                    },
                    {
                        "review_item_id": "item_done_2",
                        "reviewer_decision": "CORRECT_AND_CONFIRM",
                        "preview_status": "REVIEWED_PREVIEW",
                    },
                ]
            ),
            "04_CONFIRMED_PREVIEW": pd.DataFrame(
                [
                    {
                        "review_item_id": "item_done_1",
                        "reviewer_decision": "CONFIRM_CELL",
                        "preview_status": "CONFIRMED_PREVIEW",
                    }
                ]
            ),
            "05_CORRECTED_PREVIEW": pd.DataFrame(
                [
                    {
                        "review_item_id": "item_done_2",
                        "reviewer_decision": "CORRECT_AND_CONFIRM",
                        "preview_status": "CORRECTED_PREVIEW",
                    }
                ]
            ),
            "09_REMAINING_REVIEW": pd.DataFrame(
                [
                    {"review_item_id": "item_p1", "review_bucket": "UNIT_YEAR_REVIEW"},
                    {"review_item_id": "item_p2", "review_bucket": "DUPLICATE_REVIEW"},
                    {"review_item_id": "item_p3", "review_bucket": "TRUSTED_AUDIT_SAMPLE"},
                    {"review_item_id": "item_p4", "review_bucket": "UNIT_YEAR_REVIEW"},
                ]
            ),
            "12_342K_READINESS": pd.DataFrame([{"ready_for_342k": ready_342j, "decision": summary_342j["decision"]}]),
        },
    )

    confirmed_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_done_1",
                "review_priority": "MEDIUM",
                "review_bucket": "UNIT_YEAR_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc.pdf",
                "table_id": "t1",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "img1.jpg",
                "metric_raw": "ROE",
                "metric_standardized": "ROE",
                "year_raw": "2024",
                "year_standardized": "2024A",
                "value_raw": "10.5%",
                "value_numeric": 10.5,
                "unit_raw": "",
                "normalized_unit": "%",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_UNIT_MISSING",
                "risk_flags": "UNIT_MISSING",
                "confidence_signal": "MEDIUM",
                "source_html_snippet": "<table>roe</table>",
                "reviewer_decision": "CONFIRM_CELL",
                "final_metric_standardized": "ROE",
                "final_year_standardized": "2024A",
                "final_value_numeric": 10.5,
                "final_normalized_unit": "%",
                "final_status": "POST_HUMAN_CONFIRMED",
            }
        ]
    )
    corrected_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_done_2",
                "review_priority": "MEDIUM",
                "review_bucket": "UNIT_YEAR_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc.pdf",
                "table_id": "t1",
                "table_type": "INCOME_STATEMENT",
                "source_page": 2,
                "bbox": "[2,3,4,5]",
                "image_path": "img2.jpg",
                "metric_raw": "收入增长",
                "metric_standardized": "revenue",
                "year_raw": "2024",
                "year_standardized": "2024A",
                "value_raw": "46%",
                "value_numeric": 46.0,
                "unit_raw": "",
                "normalized_unit": "",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_UNIT_MISSING",
                "risk_flags": "UNIT_MISSING",
                "confidence_signal": "MEDIUM",
                "source_html_snippet": "<table>growth</table>",
                "reviewer_decision": "CORRECT_AND_CONFIRM",
                "final_metric_standardized": "revenue_yoy",
                "final_year_standardized": "2024A",
                "final_value_numeric": 46.0,
                "final_normalized_unit": "%",
                "final_status": "POST_HUMAN_CORRECTED_CONFIRMED",
            }
        ]
    )
    rejected_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_done_3",
                "review_priority": "HIGH",
                "review_bucket": "NOT_CORE_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc.pdf",
                "table_id": "t2",
                "table_type": "UNKNOWN_TABLE",
                "source_page": 3,
                "bbox": "[3,4,5,6]",
                "image_path": "img3.jpg",
                "metric_raw": "评级",
                "reviewer_decision": "NOT_A_CORE_METRIC",
                "final_status": "POST_HUMAN_REJECTED",
            }
        ]
    )
    pending_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_p1",
                "review_priority": "MEDIUM",
                "review_bucket": "UNIT_YEAR_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc.pdf",
                "table_id": "t1",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "img4.jpg",
                "metric_raw": "每股收益",
                "metric_standardized": "EPS",
                "year_raw": "2025",
                "year_standardized": "2025A",
                "value_raw": "1.45",
                "value_numeric": 1.45,
                "unit_raw": "",
                "normalized_unit": "",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_UNIT_MISSING",
                "risk_flags": "UNIT_MISSING",
                "confidence_signal": "MEDIUM",
                "source_html_snippet": "<table>eps</table>",
                "reviewer_decision": "",
            },
            {
                "review_item_id": "item_p2",
                "review_priority": "HIGH",
                "review_bucket": "DUPLICATE_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc.pdf",
                "table_id": "t2",
                "table_type": "INCOME_STATEMENT",
                "source_page": 2,
                "bbox": "[5,6,7,8]",
                "image_path": "img5.jpg",
                "metric_raw": "收入增长",
                "metric_standardized": "revenue",
                "year_raw": "2025",
                "year_standardized": "2025A",
                "value_raw": "12%",
                "value_numeric": 12.0,
                "unit_raw": "",
                "normalized_unit": "",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_DUPLICATE",
                "risk_flags": "UNIT_MISSING|DUPLICATE_DROPPED",
                "confidence_signal": "LOW",
                "source_html_snippet": "<table>growth dup</table>",
                "reviewer_decision": "",
            },
            {
                "review_item_id": "item_p3",
                "review_priority": "LOW",
                "review_bucket": "TRUSTED_AUDIT_SAMPLE",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc.pdf",
                "table_id": "t3",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 3,
                "bbox": "[9,9,9,9]",
                "image_path": "img6.jpg",
                "metric_raw": "ROE",
                "metric_standardized": "ROE",
                "year_raw": "2026E",
                "year_standardized": "2026E",
                "value_raw": "12.8%",
                "value_numeric": 12.8,
                "unit_raw": "%",
                "normalized_unit": "%",
                "extraction_status": "TRUSTED_CELL",
                "review_reason": "TRUSTED_AUDIT_SPOT_CHECK",
                "risk_flags": "",
                "confidence_signal": "HIGH",
                "source_html_snippet": "<table>trusted</table>",
                "reviewer_decision": "",
            },
            {
                "review_item_id": "item_p4",
                "review_priority": "MEDIUM",
                "review_bucket": "UNIT_YEAR_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc.pdf",
                "table_id": "t4",
                "table_type": "INCOME_STATEMENT",
                "source_page": 4,
                "bbox": "[0,0,0,0]",
                "image_path": "",
                "metric_raw": "未知指标",
                "metric_standardized": "",
                "year_raw": "2026E",
                "year_standardized": "",
                "value_raw": "0",
                "value_numeric": 0.0,
                "unit_raw": "",
                "normalized_unit": "",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_UNIT_AMBIGUITY",
                "risk_flags": "",
                "confidence_signal": "MEDIUM",
                "source_html_snippet": "",
                "reviewer_decision": "",
            },
        ]
    )
    _write_json(
        sidecar_342i_dir / "table_first_post_human_review_sidecar_result_342i_summary.json",
        {
            "decision": "TABLE_FIRST_POST_HUMAN_REVIEW_SIDECAR_RESULT_342I_READY",
            "ready_for_342j": True,
            "reviewed_row_count": 3,
            "pending_review_count": 4,
            "post_human_confirmed_count": 2,
            "qa_fail_count": 0,
        },
    )
    _write_json(sidecar_342i_dir / "table_first_post_human_review_sidecar_result_342i_qa.json", {"qa_fail_count": 0, "checks": []})
    _write_json(sidecar_342i_dir / "table_first_post_human_review_sidecar_result_342i_no_write_back_proof.json", {"upstream_workbooks_unchanged": True})
    (sidecar_342i_dir / "table_first_post_human_review_sidecar_result_342i_report.md").write_text("342I report", encoding="utf-8")
    _write_excel(
        sidecar_342i_dir / "table_first_post_human_review_sidecar_result_342i.xlsx",
        {
            "04_FINAL_CONFIRMED": confirmed_df,
            "05_FINAL_CORRECTED": corrected_df,
            "06_FINAL_REJECTED": rejected_df,
            "07_PENDING_REVIEW": pending_df,
        },
    )

    review_template_df = pd.concat([confirmed_df, corrected_df, rejected_df, pending_df], ignore_index=True, sort=False)
    _write_excel(
        review_342g_dir / "table_first_extraction_review_package_342g.xlsx",
        {
            "03_REVIEW_QUEUE": pending_df,
            "04_TRUSTED_AUDIT": pending_df[pending_df["review_bucket"].eq("TRUSTED_AUDIT_SAMPLE")].copy(),
            "05_UNIT_YEAR_ISSUES": pending_df[pending_df["review_bucket"].eq("UNIT_YEAR_REVIEW")].copy(),
            "06_DUPLICATE_ISSUES": pd.DataFrame([{"review_item_id": "item_p2", "duplicate_group_key": "g1", "review_priority": "HIGH"}]),
            "07_GROWTH_ROW_ISSUES": pd.DataFrame([{"review_item_id": "item_p2", "growth_binding_status": "AMBIGUOUS"}]),
            "08_TABLE_TRACE": pd.DataFrame([{"table_id": "t1", "corpus_pdf_id": "pdf_1", "parse_status": "PARSED"}]),
            "10_REVIEW_TEMPLATE": review_template_df,
        },
    )
    return preview_342j_dir, sidecar_342i_dir, review_342g_dir


def test_build_342k_ready_and_excludes_already_reviewed_rows(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    preview_342j_dir, sidecar_342i_dir, review_342g_dir = _seed_342_inputs(repo_root)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_llm_assisted_review_adjudication_342k(
        reviewed_preview_342j_dir=preview_342j_dir,
        post_human_review_342i_dir=sidecar_342i_dir,
        review_package_342g_dir=review_342g_dir,
        output_dir=repo_root / "output" / "llm_assisted_review_adjudication_342k",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["llm_candidate_pool_count"] == 4
    assert summary["prompt_package_count"] == 2
    assert summary["request_pack_count"] == 2
    assert summary["rule_baseline_count"] == 4
    assert summary["dry_run_suggestion_count"] == 4
    assert summary["human_required_count"] >= 2
    assert summary["auto_confirm_candidate_count"] >= 1
    assert summary["unit_year_risk_count"] == 2
    assert summary["duplicate_risk_count"] == 1
    assert summary["growth_row_risk_count"] == 1
    assert summary["source_trace_risk_count"] == 1
    assert summary["metric_mapping_risk_count"] == 1
    assert summary["ready_for_342l"] is True

    candidate_ids = set(artifacts["workbook_sheets"]["03_LLM_CANDIDATE_POOL"]["review_item_id"].astype(str))
    assert "item_done_1" not in candidate_ids
    assert "item_done_2" not in candidate_ids
    assert "item_done_3" not in candidate_ids

    prompt_ids = {row["review_item_id"] for row in artifacts["prompt_pack_rows"]}
    assert "item_p1" in prompt_ids
    assert "item_p3" in prompt_ids
    assert "item_p2" not in prompt_ids
    assert "item_p4" not in prompt_ids

    draft_df = artifacts["workbook_sheets"]["12_REVIEW_TEMPLATE_DRAFT"]
    assert draft_df["reviewer_decision"].astype(str).eq("").all()
    assert draft_df["reviewed_at"].astype(str).eq("").all()
    assert all(name in WORKBOOK_SHEETS for name in artifacts["workbook_sheets"])


def test_build_342k_not_ready_when_342j_not_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    preview_342j_dir, sidecar_342i_dir, review_342g_dir = _seed_342_inputs(repo_root, ready_342j=False)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_llm_assisted_review_adjudication_342k(
        reviewed_preview_342j_dir=preview_342j_dir,
        post_human_review_342i_dir=sidecar_342i_dir,
        review_package_342g_dir=review_342g_dir,
        output_dir=repo_root / "output" / "llm_assisted_review_adjudication_342k",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    assert artifacts["summary"]["decision"] == NOT_READY_DECISION
    assert artifacts["summary"]["ready_for_342l"] is False
    assert artifacts["summary"]["llm_candidate_pool_count"] == 0
