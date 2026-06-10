from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.table_first_human_review_apply_simulation_342h import (  # noqa: E402
    READY_DECISION,
    WAITING_DECISION,
    build_table_first_human_review_apply_simulation_342h,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _as_reviewable_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in [
        "reviewer_decision",
        "reviewer_metric_standardized",
        "reviewer_year_standardized",
        "reviewer_value_numeric",
        "reviewer_normalized_unit",
        "reviewer_note",
        "reviewer_id",
        "reviewed_at",
    ]:
        if column in out.columns:
            out[column] = out[column].astype(object)
    return out


def _seed_342g(root: Path) -> Path:
    output_dir = root / "output" / "table_first_extraction_review_package_342g"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "audited_pdf_count": 2,
        "input_long_form_cell_count": 10,
        "input_trusted_cell_count": 2,
        "input_review_required_cell_count": 3,
        "input_rejected_cell_count": 5,
        "review_queue_count": 3,
        "trusted_audit_sample_count": 2,
        "unit_year_issue_count": 3,
        "duplicate_issue_count": 1,
        "growth_row_issue_count": 1,
        "high_priority_review_count": 1,
        "medium_priority_review_count": 2,
        "low_priority_review_count": 2,
        "review_template_row_count": 5,
        "ready_for_342h": True,
        "recommended_342h_scope": "table_first_human_review_apply_simulation",
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0,
        "decision": "TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_READY",
        "no_write_back_proof_passed": True,
        "output_workbook_path": str(output_dir / "table_first_extraction_review_package_342g.xlsx"),
    }
    _write_json(output_dir / "table_first_extraction_review_package_342g_summary.json", summary)
    _write_json(output_dir / "table_first_extraction_review_package_342g_qa.json", {"qa_fail_count": 0, "checks": []})
    _write_json(
        output_dir / "table_first_extraction_review_package_342g_no_write_back_proof.json",
        {"upstream_workbooks_unchanged": True, "no_official_asset_modification_during_342g": True},
    )
    (output_dir / "table_first_extraction_review_package_342g_report.md").write_text("342G report", encoding="utf-8")

    template_df = pd.DataFrame(
        [
            {
                "review_item_id": "342g::queue::0001",
                "review_priority": "HIGH",
                "review_bucket": "UNIT_YEAR_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc_1.pdf",
                "table_id": "t1",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "img1.jpg",
                "metric_raw": "Revenue",
                "metric_standardized": "revenue",
                "year_raw": "2024",
                "year_standardized": "2024A",
                "value_raw": "100",
                "value_numeric": 100.0,
                "unit_raw": "百万元",
                "normalized_unit": "百万元",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_UNIT_MISSING",
                "risk_flags": "UNIT_MISSING",
                "confidence_signal": "MEDIUM",
                "source_html_snippet": "<table>rev</table>",
                "reviewer_decision": "",
                "reviewer_metric_standardized": "",
                "reviewer_year_standardized": "",
                "reviewer_value_numeric": "",
                "reviewer_normalized_unit": "",
                "reviewer_note": "",
                "reviewer_id": "",
                "reviewed_at": "",
            },
            {
                "review_item_id": "342g::queue::0002",
                "review_priority": "MEDIUM",
                "review_bucket": "GROWTH_ROW_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc_1.pdf",
                "table_id": "t1",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "img1.jpg",
                "metric_raw": "ROE",
                "metric_standardized": "ROE",
                "year_raw": "2024",
                "year_standardized": "2024A",
                "value_raw": "9.9%",
                "value_numeric": 9.9,
                "unit_raw": "%",
                "normalized_unit": "%",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_UNIT_MISSING",
                "risk_flags": "UNIT_MISSING",
                "confidence_signal": "MEDIUM",
                "source_html_snippet": "<table>roe</table>",
                "reviewer_decision": "",
                "reviewer_metric_standardized": "",
                "reviewer_year_standardized": "",
                "reviewer_value_numeric": "",
                "reviewer_normalized_unit": "",
                "reviewer_note": "",
                "reviewer_id": "",
                "reviewed_at": "",
            },
            {
                "review_item_id": "342g::trusted::0001",
                "review_priority": "LOW",
                "review_bucket": "TRUSTED_AUDIT_SAMPLE",
                "corpus_pdf_id": "pdf_2",
                "file_name": "doc_2.pdf",
                "table_id": "t2",
                "table_type": "BALANCE_SHEET",
                "source_page": 2,
                "bbox": "[2,3,4,5]",
                "image_path": "img2.jpg",
                "metric_raw": "Assets",
                "metric_standardized": "total_assets",
                "year_raw": "2025",
                "year_standardized": "2025A",
                "value_raw": "200",
                "value_numeric": 200.0,
                "unit_raw": "亿元",
                "normalized_unit": "亿元",
                "extraction_status": "TRUSTED_CELL",
                "review_reason": "TRUSTED_AUDIT_SPOT_CHECK",
                "risk_flags": "",
                "confidence_signal": "HIGH",
                "source_html_snippet": "<table>assets</table>",
                "reviewer_decision": "",
                "reviewer_metric_standardized": "",
                "reviewer_year_standardized": "",
                "reviewer_value_numeric": "",
                "reviewer_normalized_unit": "",
                "reviewer_note": "",
                "reviewer_id": "",
                "reviewed_at": "",
            },
            {
                "review_item_id": "342g::queue::0003",
                "review_priority": "LOW",
                "review_bucket": "REVIEW_REQUIRED_QUEUE",
                "corpus_pdf_id": "pdf_3",
                "file_name": "doc_3.pdf",
                "table_id": "t3",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 3,
                "bbox": "[3,4,5,6]",
                "image_path": "img3.jpg",
                "metric_raw": "PE",
                "metric_standardized": "PE",
                "year_raw": "2025",
                "year_standardized": "2025A",
                "value_raw": "20",
                "value_numeric": 20.0,
                "unit_raw": "倍",
                "normalized_unit": "倍",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_DUPLICATE",
                "risk_flags": "DUPLICATE_DROPPED",
                "confidence_signal": "LOW",
                "source_html_snippet": "<table>pe</table>",
                "reviewer_decision": "",
                "reviewer_metric_standardized": "",
                "reviewer_year_standardized": "",
                "reviewer_value_numeric": "",
                "reviewer_normalized_unit": "",
                "reviewer_note": "",
                "reviewer_id": "",
                "reviewed_at": "",
            },
            {
                "review_item_id": "342g::queue::0004",
                "review_priority": "LOW",
                "review_bucket": "REVIEW_REQUIRED_QUEUE",
                "corpus_pdf_id": "pdf_4",
                "file_name": "doc_4.pdf",
                "table_id": "t4",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 4,
                "bbox": "[4,5,6,7]",
                "image_path": "img4.jpg",
                "metric_raw": "Net profit",
                "metric_standardized": "net_profit",
                "year_raw": "2026E",
                "year_standardized": "2026E",
                "value_raw": "50",
                "value_numeric": 50.0,
                "unit_raw": "百万元",
                "normalized_unit": "百万元",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_UNIT_MISSING",
                "risk_flags": "",
                "confidence_signal": "MEDIUM",
                "source_html_snippet": "<table>np</table>",
                "reviewer_decision": "",
                "reviewer_metric_standardized": "",
                "reviewer_year_standardized": "",
                "reviewer_value_numeric": "",
                "reviewer_normalized_unit": "",
                "reviewer_note": "",
                "reviewer_id": "",
                "reviewed_at": "",
            },
        ]
    )

    _write_excel(
        output_dir / "table_first_extraction_review_package_342g.xlsx",
        {
            "00_README": pd.DataFrame([{"topic": "Purpose", "message": "test"}]),
            "01_REVIEW_SUMMARY": pd.DataFrame([summary]),
            "10_REVIEW_TEMPLATE": template_df,
            "11_DECISION_OPTIONS": pd.DataFrame(
                [
                    {"reviewer_decision": "CONFIRM_CELL", "meaning_zh": "确认", "meaning_en": "confirm"},
                    {"reviewer_decision": "CORRECT_AND_CONFIRM", "meaning_zh": "修正后确认", "meaning_en": "correct"},
                ]
            ),
            "12_342H_READINESS": pd.DataFrame([{"ready_for_342h": True}]),
            "13_NO_WRITE_BACK": pd.DataFrame([{"path": "x", "before_hash": "a", "after_hash": "a", "unchanged": True}]),
        },
    )
    return output_dir


def test_build_342h_waiting_when_reviewed_workbook_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    review_package_dir = _seed_342g(repo_root)
    reviewed_input_dir = repo_root / "input" / "table_first_review_342g_reviewed"
    reviewed_input_dir.mkdir(parents=True, exist_ok=True)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_table_first_human_review_apply_simulation_342h(
        review_package_342g_dir=review_package_dir,
        reviewed_input_dir=reviewed_input_dir,
        output_dir=repo_root / "output" / "table_first_human_review_apply_simulation_342h",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["reviewed_workbook_exists"] is False
    assert summary["decision"] == WAITING_DECISION
    assert summary["pending_review_count"] == 5
    assert summary["reviewed_row_count"] == 0
    assert summary["qa_fail_count"] == 0
    assert summary["recommended_next_action"] == "fill_342g_review_template_first"


def test_build_342h_ready_with_valid_reviewed_workbook(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    review_package_dir = _seed_342g(repo_root)
    reviewed_input_dir = repo_root / "input" / "table_first_review_342g_reviewed"
    reviewed_input_dir.mkdir(parents=True, exist_ok=True)

    reviewed_df = pd.read_excel(review_package_dir / "table_first_extraction_review_package_342g.xlsx", sheet_name="10_REVIEW_TEMPLATE")
    reviewed_df = _as_reviewable_frame(reviewed_df)
    reviewed_df.loc[0, "reviewer_decision"] = "CONFIRM_CELL"
    reviewed_df.loc[1, "reviewer_decision"] = "CORRECT_AND_CONFIRM"
    reviewed_df.loc[1, "reviewer_normalized_unit"] = "%"
    reviewed_df.loc[2, "reviewer_decision"] = "REJECT_CELL"
    reviewed_df.loc[2, "reviewer_note"] = "reject"
    reviewed_df.loc[3, "reviewer_decision"] = "KEEP_REVIEW_REQUIRED"
    reviewed_df.loc[4, "reviewer_decision"] = "NEEDS_SOURCE_CHECK"
    _write_excel(reviewed_input_dir / "table_first_extraction_review_package_342g_reviewed.xlsx", {"10_REVIEW_TEMPLATE": reviewed_df})

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_table_first_human_review_apply_simulation_342h(
        review_package_342g_dir=review_package_dir,
        reviewed_input_dir=reviewed_input_dir,
        output_dir=repo_root / "output" / "table_first_human_review_apply_simulation_342h",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["reviewed_workbook_exists"] is True
    assert summary["decision"] == READY_DECISION
    assert summary["reviewed_row_count"] == 5
    assert summary["pending_review_count"] == 0
    assert summary["confirmed_cell_count"] == 1
    assert summary["corrected_cell_count"] == 1
    assert summary["rejected_cell_count"] == 1
    assert summary["still_review_required_count"] == 1
    assert summary["needs_source_check_count"] == 1
    assert summary["validation_error_count"] == 0
    assert summary["ready_for_342i"] is True


def test_build_342h_not_ready_with_invalid_reviewed_workbook(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    review_package_dir = _seed_342g(repo_root)
    reviewed_input_dir = repo_root / "input" / "table_first_review_342g_reviewed"
    reviewed_input_dir.mkdir(parents=True, exist_ok=True)

    reviewed_df = pd.read_excel(review_package_dir / "table_first_extraction_review_package_342g.xlsx", sheet_name="10_REVIEW_TEMPLATE")
    reviewed_df = _as_reviewable_frame(reviewed_df)
    reviewed_df.loc[0, "reviewer_decision"] = "BAD_DECISION"
    reviewed_df.loc[1, "reviewer_decision"] = "CORRECT_AND_CONFIRM"
    _write_excel(reviewed_input_dir / "table_first_extraction_review_package_342g_reviewed.xlsx", {"10_REVIEW_TEMPLATE": reviewed_df})

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_table_first_human_review_apply_simulation_342h(
        review_package_342g_dir=review_package_dir,
        reviewed_input_dir=reviewed_input_dir,
        output_dir=repo_root / "output" / "table_first_human_review_apply_simulation_342h",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["reviewed_workbook_exists"] is True
    assert summary["decision"].endswith("NOT_READY")
    assert summary["validation_error_count"] >= 2
    assert summary["unknown_decision_count"] == 1
    assert summary["correction_without_change_count"] == 1
