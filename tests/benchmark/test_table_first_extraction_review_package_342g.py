from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.table_first_extraction_review_package_342g import (  # noqa: E402
    READY_DECISION,
    build_table_first_extraction_review_package_342g,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _seed_minimal_inputs(root: Path) -> tuple[Path, Path, Path, Path]:
    corpus_dir = root / "output" / "real_pdf_corpus_intake_342b"
    mineru_dir = root / "output" / "mineru_pilot_network_recovery_342c6"
    parser_dir = root / "output" / "parser_ensemble_compare_342d"
    candidate_dir = root / "output" / "core_metric_candidate_quality_342e"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    mineru_dir.mkdir(parents=True, exist_ok=True)
    parser_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir.mkdir(parents=True, exist_ok=True)
    _write_json(corpus_dir / "real_pdf_corpus_intake_342b_summary.json", {"decision": "REAL_PDF_CORPUS_INTAKE_342B_READY"})
    _write_json(corpus_dir / "real_pdf_corpus_intake_342b_manifest.json", {"task": "342B"})
    _write_json(mineru_dir / "mineru_pilot_network_recovery_342c6_summary.json", {"decision": "MINERU_PILOT_NETWORK_RECOVERY_342C6_READY", "qa_fail_count": 0})
    _write_json(parser_dir / "parser_ensemble_compare_342d_summary.json", {"decision": "PARSER_ENSEMBLE_COMPARE_342D_READY", "qa_fail_count": 0})
    _write_json(candidate_dir / "core_metric_candidate_quality_342e_summary.json", {"decision": "CORE_METRIC_CANDIDATE_QUALITY_342E_READY", "qa_fail_count": 0})
    return corpus_dir, mineru_dir, parser_dir, candidate_dir


def _seed_342f(root: Path, ready: bool = True) -> Path:
    output_dir = root / "output" / "table_first_core_financial_extraction_342f"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "audited_pdf_count": 2,
        "input_core_extractable_table_count": 3,
        "parsed_core_table_count": 3,
        "html_parse_failed_table_count": 0,
        "long_form_cell_count": 12,
        "trusted_cell_count": 4,
        "review_required_cell_count": 4,
        "rejected_cell_count": 4,
        "metric_covered_count": 5,
        "metric_year_pair_count": 9,
        "unit_issue_count": 2,
        "year_header_issue_count": 1,
        "duplicate_cell_count": 2,
        "table_trace_count": 3,
        "ready_for_342g": "true" if ready else "false",
        "recommended_342g_scope": "table_first_extraction_review_package",
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0 if ready else 1,
        "decision": "TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_READY" if ready else "TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_NOT_READY",
        "no_write_back_proof_passed": True if ready else False,
        "output_workbook_path": str(output_dir / "table_first_core_financial_extraction_342f.xlsx"),
    }
    qa = {"qa_fail_count": summary["qa_fail_count"], "checks": []}
    _write_json(output_dir / "table_first_core_financial_extraction_342f_summary.json", summary)
    _write_json(output_dir / "table_first_core_financial_extraction_342f_qa.json", qa)
    _write_json(
        output_dir / "table_first_core_financial_extraction_342f_no_write_back_proof.json",
        {"upstream_unchanged": True, "official_assets_unchanged": True, "client_export_generated": False},
    )

    long_rows = [
        {
            "long_cell_id": "c1",
            "corpus_pdf_id": "pdf_1",
            "file_name": "doc_1.pdf",
            "table_id": "t1",
            "table_type": "CORE_FORECAST_SUMMARY",
            "table_value_class": "MIXED",
            "source_file": "doc_1_content_list.json",
            "source_page": 1,
            "bbox": "[1,2,3,4]",
            "image_path": "img1.jpg",
            "metric_raw": "营业收入（百万元）",
            "metric_standardized": "revenue",
            "year_raw": "2024",
            "year_standardized": "2024A",
            "value_raw": "100",
            "value_numeric": 100.0,
            "unit_raw": "百万元",
            "normalized_unit": "百万元",
            "row_index": 1,
            "col_index": 1,
            "source_html_snippet": "<table>revenue</table>",
            "extraction_status": "TRUSTED_CELL",
            "review_reason": "",
            "risk_flags": "",
            "confidence_signal": "HIGH",
            "unit_status": "OK",
        },
        {
            "long_cell_id": "c2",
            "corpus_pdf_id": "pdf_1",
            "file_name": "doc_1.pdf",
            "table_id": "t1",
            "table_type": "CORE_FORECAST_SUMMARY",
            "table_value_class": "MIXED",
            "source_file": "doc_1_content_list.json",
            "source_page": 1,
            "bbox": "[1,2,3,4]",
            "image_path": "img1.jpg",
            "metric_raw": "净利润（百万元）",
            "metric_standardized": "net_profit",
            "year_raw": "2024",
            "year_standardized": "2024A",
            "value_raw": "(10)",
            "value_numeric": -10.0,
            "unit_raw": "百万元",
            "normalized_unit": "百万元",
            "row_index": 2,
            "col_index": 1,
            "source_html_snippet": "<table>profit</table>",
            "extraction_status": "TRUSTED_CELL",
            "review_reason": "",
            "risk_flags": "PAREN_NEGATIVE_VALUE",
            "confidence_signal": "HIGH",
            "unit_status": "OK",
        },
        {
            "long_cell_id": "c3",
            "corpus_pdf_id": "pdf_2",
            "file_name": "doc_2.pdf",
            "table_id": "t2",
            "table_type": "BALANCE_SHEET",
            "table_value_class": "MONEY",
            "source_file": "doc_2_content_list.json",
            "source_page": "",
            "bbox": "[2,3,4,5]",
            "image_path": "img2.jpg",
            "metric_raw": "资产总计",
            "metric_standardized": "total_assets",
            "year_raw": "2025",
            "year_standardized": "",
            "value_raw": "200",
            "value_numeric": 200.0,
            "unit_raw": "亿元",
            "normalized_unit": "亿元",
            "row_index": 3,
            "col_index": 1,
            "source_html_snippet": "<table>assets</table>",
            "extraction_status": "REVIEW_REQUIRED",
            "review_reason": "REVIEW_REQUIRED_YEAR_HEADER_MISSING",
            "risk_flags": "YEAR_HEADER_MISSING",
            "confidence_signal": "LOW",
            "unit_status": "OK",
        },
        {
            "long_cell_id": "c4",
            "corpus_pdf_id": "pdf_2",
            "file_name": "doc_2.pdf",
            "table_id": "t2",
            "table_type": "BALANCE_SHEET",
            "table_value_class": "MONEY",
            "source_file": "doc_2_content_list.json",
            "source_page": "",
            "bbox": "[2,3,4,5]",
            "image_path": "img2.jpg",
            "metric_raw": "资产总计",
            "metric_standardized": "total_assets",
            "year_raw": "2025",
            "year_standardized": "",
            "value_raw": "200",
            "value_numeric": 200.0,
            "unit_raw": "亿元",
            "normalized_unit": "亿元",
            "row_index": 4,
            "col_index": 1,
            "source_html_snippet": "<table>assets dup</table>",
            "extraction_status": "REVIEW_REQUIRED",
            "review_reason": "REVIEW_REQUIRED_DUPLICATE",
            "risk_flags": "DUPLICATE_DROPPED",
            "confidence_signal": "LOW",
            "unit_status": "OK",
        },
        {
            "long_cell_id": "c5",
            "corpus_pdf_id": "pdf_2",
            "file_name": "doc_2.pdf",
            "table_id": "t2",
            "table_type": "INCOME_STATEMENT",
            "table_value_class": "PERCENT",
            "source_file": "doc_2_content_list.json",
            "source_page": 5,
            "bbox": "[2,3,4,5]",
            "image_path": "img2.jpg",
            "metric_raw": "(+/-%)",
            "metric_standardized": "revenue_yoy",
            "year_raw": "2025",
            "year_standardized": "2025A",
            "value_raw": "10%",
            "value_numeric": 10.0,
            "unit_raw": "",
            "normalized_unit": "%",
            "row_index": 5,
            "col_index": 1,
            "source_html_snippet": "<table>growth</table>",
            "extraction_status": "REVIEW_REQUIRED",
            "review_reason": "REVIEW_REQUIRED_UNIT_MISSING",
            "risk_flags": "UNIT_MISSING",
            "confidence_signal": "MEDIUM",
            "unit_status": "MISSING",
        },
        {
            "long_cell_id": "c6",
            "corpus_pdf_id": "pdf_2",
            "file_name": "doc_2.pdf",
            "table_id": "t3",
            "table_type": "CASH_FLOW_STATEMENT",
            "table_value_class": "MONEY",
            "source_file": "doc_2_content_list.json",
            "source_page": 6,
            "bbox": "[2,3,4,5]",
            "image_path": "img3.jpg",
            "metric_raw": "未知指标",
            "metric_standardized": "",
            "year_raw": "2025",
            "year_standardized": "2025A",
            "value_raw": "5",
            "value_numeric": 5.0,
            "unit_raw": "",
            "normalized_unit": "",
            "row_index": 6,
            "col_index": 1,
            "source_html_snippet": "<table>unknown</table>",
            "extraction_status": "REJECTED_CELL",
            "review_reason": "REJECTED_METRIC_UNRECOGNIZED",
            "risk_flags": "UNIT_MISSING",
            "confidence_signal": "LOW",
            "unit_status": "MISSING",
        },
    ]
    long_df = pd.DataFrame(long_rows)
    trusted_df = long_df[long_df["extraction_status"] == "TRUSTED_CELL"].copy()
    review_df = long_df[long_df["extraction_status"] == "REVIEW_REQUIRED"].copy()
    rejected_df = long_df[long_df["extraction_status"] == "REJECTED_CELL"].copy()
    metric_cov_df = pd.DataFrame(
        [
            {"metric_standardized": "revenue", "table_type": "CORE_FORECAST_SUMMARY", "pdf_hit_count": 1, "year_hit_count": 1, "trusted_cell_count": 1, "review_required_count": 0, "rejected_cell_count": 0, "coverage_status": "TRUSTED", "main_risk": ""},
            {"metric_standardized": "total_assets", "table_type": "BALANCE_SHEET", "pdf_hit_count": 1, "year_hit_count": 1, "trusted_cell_count": 0, "review_required_count": 2, "rejected_cell_count": 0, "coverage_status": "REVIEW_REQUIRED", "main_risk": "REVIEW_REQUIRED_YEAR_HEADER_MISSING"},
        ]
    )
    unit_df = pd.DataFrame(
        [
            {"metric_standardized": "revenue_yoy", "raw_unit": "", "normalized_unit": "%", "unit_status": "MISSING", "affected_cell_count": 1},
            {"metric_standardized": "total_assets", "raw_unit": "亿元", "normalized_unit": "亿元", "unit_status": "OK", "affected_cell_count": 2},
        ]
    )
    trace_df = pd.DataFrame(
        [
            {"table_id": "t1", "corpus_pdf_id": "pdf_1", "file_name": "doc_1.pdf", "table_type": "CORE_FORECAST_SUMMARY", "source_page": 1, "bbox": "[1,2,3,4]", "image_path": "img1.jpg", "source_file": "doc_1_content_list.json", "html_available": True, "parse_status": "PARSED", "row_count": 5, "column_count": 3, "header_year_tokens": "2024", "first_col_metric_candidates": "营业收入|净利润", "extracted_cell_count": 2, "trusted_cell_count": 2, "review_required_count": 0, "rejected_cell_count": 0},
            {"table_id": "t2", "corpus_pdf_id": "pdf_2", "file_name": "doc_2.pdf", "table_type": "BALANCE_SHEET", "source_page": "", "bbox": "[2,3,4,5]", "image_path": "img2.jpg", "source_file": "doc_2_content_list.json", "html_available": True, "parse_status": "PARSED", "row_count": 4, "column_count": 3, "header_year_tokens": "", "first_col_metric_candidates": "资产总计", "extracted_cell_count": 3, "trusted_cell_count": 0, "review_required_count": 3, "rejected_cell_count": 0},
        ]
    )
    readiness_df = pd.DataFrame(
        [
            {
                "long_form_cell_count": 12,
                "trusted_cell_count": 4,
                "review_required_cell_count": 4,
                "table_trace_count": 3,
                "ready_for_342g": True,
                "recommended_342g_scope": "table_first_extraction_review_package",
                "reason": "ready",
            }
        ]
    )
    proof_df = pd.DataFrame([{"path": "x", "before_hash": "a", "after_hash": "a", "unchanged": True}])
    next_df = pd.DataFrame([{"step_order": 1, "next_step": "342G", "rationale": "next"}])
    _write_excel(
        output_dir / "table_first_core_financial_extraction_342f.xlsx",
        {
            "00_README": pd.DataFrame([{"topic": "Purpose", "message": "test"}]),
            "01_EXTRACTION_SUMMARY": pd.DataFrame([summary]),
            "02_INPUT_CORE_TABLES": pd.DataFrame([{"table_id": "t1"}]),
            "03_LONG_FORM_CELLS": long_df,
            "04_TRUSTED_CELLS": trusted_df,
            "05_REVIEW_REQUIRED": review_df,
            "06_REJECTED_CELLS": rejected_df,
            "07_METRIC_COVERAGE": metric_cov_df,
            "08_UNIT_NORMALIZATION": unit_df,
            "09_TABLE_TRACE": trace_df,
            "10_342G_READINESS": readiness_df,
            "11_NO_WRITE_BACK_PROOF": proof_df,
            "12_NEXT_STEPS": next_df,
        },
    )
    return output_dir


def test_build_342g_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir, mineru_dir, parser_dir, candidate_dir = _seed_minimal_inputs(repo_root)
    core_extraction_dir = _seed_342f(repo_root, ready=True)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_table_first_extraction_review_package_342g(
        corpus_342b_dir=corpus_dir,
        mineru_342c6_dir=mineru_dir,
        parser_compare_342d_dir=parser_dir,
        candidate_quality_342e_dir=candidate_dir,
        core_extraction_342f_dir=core_extraction_dir,
        output_dir=repo_root / "output" / "table_first_extraction_review_package_342g",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    review_queue_df = artifacts["workbook_sheets"]["03_REVIEW_QUEUE"]
    trusted_audit_df = artifacts["workbook_sheets"]["04_TRUSTED_AUDIT"]
    review_template_df = artifacts["workbook_sheets"]["10_REVIEW_TEMPLATE"]
    duplicate_df = artifacts["workbook_sheets"]["06_DUPLICATE_ISSUES"]
    growth_df = artifacts["workbook_sheets"]["07_GROWTH_ROW_ISSUES"]

    assert summary["review_queue_count"] == 3
    assert summary["trusted_audit_sample_count"] >= 2
    assert summary["duplicate_issue_count"] >= 1
    assert summary["growth_row_issue_count"] >= 1
    assert summary["review_template_row_count"] == len(review_queue_df) + len(trusted_audit_df)
    assert summary["ready_for_342h"] == "true"
    assert summary["decision"] == READY_DECISION
    assert set(review_queue_df["extraction_status"].astype(str)) == {"REVIEW_REQUIRED"}
    assert set(trusted_audit_df["extraction_status"].astype(str)) == {"TRUSTED_CELL"}
    assert review_template_df["reviewer_decision"].fillna("").astype(str).str.strip().eq("").all()
    assert review_template_df["review_bucket"].isin(
        [
            "REVIEW_REQUIRED_QUEUE",
            "DUPLICATE_REVIEW",
            "UNIT_YEAR_REVIEW",
            "GROWTH_ROW_REVIEW",
            "TRUSTED_AUDIT_SAMPLE",
        ]
    ).all()
    assert "duplicate_group_key" in duplicate_df.columns
    assert "growth_binding_status" in growth_df.columns


def test_build_342g_not_ready_when_342f_not_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir, mineru_dir, parser_dir, candidate_dir = _seed_minimal_inputs(repo_root)
    core_extraction_dir = _seed_342f(repo_root, ready=False)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_table_first_extraction_review_package_342g(
        corpus_342b_dir=corpus_dir,
        mineru_342c6_dir=mineru_dir,
        parser_compare_342d_dir=parser_dir,
        candidate_quality_342e_dir=candidate_dir,
        core_extraction_342f_dir=core_extraction_dir,
        output_dir=repo_root / "output" / "table_first_extraction_review_package_342g",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    assert artifacts["summary"]["qa_fail_count"] >= 1
    assert artifacts["summary"]["decision"].endswith("NOT_READY")
