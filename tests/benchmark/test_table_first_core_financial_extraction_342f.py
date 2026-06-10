from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.table_first_core_financial_extraction_342f import (  # noqa: E402
    READY_DECISION,
    build_table_first_core_financial_extraction_342f,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_342b(root: Path) -> Path:
    output_dir = root / "output" / "real_pdf_corpus_intake_342b"
    workbook_path = output_dir / "real_pdf_corpus_intake_342b.xlsx"
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {"corpus_pdf_id": f"342b_pdf_00{i}", "file_name": f"pdf_{i}.pdf", "file_path": str(root / "input" / f"pdf_{i}.pdf"), "file_size_mb": 1.0, "sha256": f"sha-{i}", "modified_time": "2026-06-10T00:00:00+00:00", "source_bucket": "real_test", "document_hint": f"{i}", "page_count": 20 + i, "intake_status": "INTAKE_READY"}
        for i in range(1, 6)
    ]
    corpus_df = pd.DataFrame(rows)
    tier_df = pd.DataFrame([{"corpus_pdf_id": row["corpus_pdf_id"], "assigned_tier": "Tier A", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"} for row in rows])
    split_df = pd.DataFrame([{"corpus_pdf_id": row["corpus_pdf_id"], "split": "pilot_set", "split_reason": "test"} for row in rows])
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "Purpose", "message": "test"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"decision": "REAL_PDF_CORPUS_INTAKE_342B_READY"}]).to_excel(writer, sheet_name="01_CORPUS_SUMMARY", index=False)
        corpus_df.to_excel(writer, sheet_name="02_PDF_CORPUS", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="03_DEDUP_AUDIT", index=False)
        tier_df.to_excel(writer, sheet_name="04_TIER_ASSIGNMENT", index=False)
        split_df.to_excel(writer, sheet_name="05_SPLIT_PLAN", index=False)
    _write_json(output_dir / "real_pdf_corpus_intake_342b_summary.json", {"pilot_set_count": 5, "qa_fail_count": 0, "decision": "REAL_PDF_CORPUS_INTAKE_342B_READY"})
    _write_json(output_dir / "real_pdf_corpus_intake_342b_manifest.json", {"task": "342B"})
    return output_dir


def _seed_342e(root: Path, ready: bool = True) -> Path:
    output_dir = root / "output" / "core_metric_candidate_quality_342e"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "audited_pdf_count": 5,
        "core_extractable_table_count": 3,
        "pdf_with_core_extractable_table_count": 5 if ready else 4,
        "ready_for_342f": True if ready else False,
        "recommended_342f_scope": "table_first_core_extractable_only",
        "qa_fail_count": 0 if ready else 1,
        "decision": "CORE_METRIC_CANDIDATE_QUALITY_342E_READY" if ready else "CORE_METRIC_CANDIDATE_QUALITY_342E_NOT_READY",
    }
    _write_json(output_dir / "core_metric_candidate_quality_342e_summary.json", summary)
    _write_json(output_dir / "core_metric_candidate_quality_342e_qa.json", {"qa_fail_count": summary["qa_fail_count"], "checks": []})

    forecast_html = "<table><tr><td>盈利预测和财务指标</td><td>2026E</td><td>2027E</td></tr><tr><td>营业收入（百万元）</td><td>100</td><td>120</td></tr><tr><td>营业收入（百万元）</td><td>100</td><td>120</td></tr><tr><td>(+/-%)</td><td>10%</td><td>20%</td></tr><tr><td>经调整净利润(百万元)</td><td>20</td><td>24</td></tr><tr><td>(+/-%)</td><td>5%</td><td>6%</td></tr><tr><td>每股收益（元）</td><td>1.2</td><td>1.4</td></tr><tr><td>市盈率 (PE)</td><td>10</td><td>8</td></tr></table>"
    cash_html = "<table><tr><td>现金流量表（百万元）</td><td>2026E</td><td>2027E</td></tr><tr><td>经营活动现金流</td><td>(10)</td><td>20</td></tr><tr><td>投资活动现金流</td><td>(5)</td><td>(6)</td></tr></table>"
    broken_html = ""
    core_df = pd.DataFrame(
        [
            {"table_id": "t1", "pdf_id": "342b_pdf_001", "file_name": "pdf_1.pdf", "page_idx": 1, "bbox": "[1,2,3,4]", "html": forecast_html, "img_path": "img1.jpg", "caption": "财务预测与估值", "footnote": "资料来源", "source_file": "c1_content_list.json", "source_kind": "content_list", "row_count": 8, "column_count": 3, "header_year_tokens": "2026E|2027E", "financial_keyword_hits": "营业收入|经调整净利润|PE", "table_type": "CORE_FORECAST_SUMMARY", "table_value_class": "MIXED", "extraction_recommendation": "core_extractable", "source_trace_quality": "STRONG", "parse_output_dir": "parse1"},
            {"table_id": "t2", "pdf_id": "342b_pdf_002", "file_name": "pdf_2.pdf", "page_idx": 2, "bbox": "[1,2,3,4]", "html": forecast_html, "img_path": "img2.jpg", "caption": "财务预测与估值", "footnote": "资料来源", "source_file": "c1_content_list_v2.json", "source_kind": "content_list_v2", "row_count": 8, "column_count": 3, "header_year_tokens": "2026E|2027E", "financial_keyword_hits": "营业收入|经调整净利润|PE", "table_type": "CORE_FORECAST_SUMMARY", "table_value_class": "MIXED", "extraction_recommendation": "core_extractable", "source_trace_quality": "STRONG", "parse_output_dir": "parse2"},
            {"table_id": "t3", "pdf_id": "342b_pdf_003", "file_name": "pdf_3.pdf", "page_idx": 3, "bbox": "[1,2,3,4]", "html": cash_html, "img_path": "img3.jpg", "caption": "现金流量表", "footnote": "", "source_file": "c3_content_list.json", "source_kind": "content_list", "row_count": 3, "column_count": 3, "header_year_tokens": "2026E|2027E", "financial_keyword_hits": "经营活动现金流|投资活动现金流", "table_type": "CASH_FLOW_STATEMENT", "table_value_class": "MONEY", "extraction_recommendation": "core_extractable", "source_trace_quality": "STRONG", "parse_output_dir": "parse3"},
            {"table_id": "t4", "pdf_id": "342b_pdf_004", "file_name": "pdf_4.pdf", "page_idx": 4, "bbox": "[1,2,3,4]", "html": broken_html, "img_path": "img4.jpg", "caption": "损坏表", "footnote": "", "source_file": "c4.md", "source_kind": "markdown", "row_count": 0, "column_count": 0, "header_year_tokens": "", "financial_keyword_hits": "", "table_type": "INCOME_STATEMENT", "table_value_class": "MONEY", "extraction_recommendation": "core_extractable", "source_trace_quality": "MEDIUM", "parse_output_dir": "parse4"},
        ]
    )
    metadata_df = pd.DataFrame(
        [{"table_id": "m1", "pdf_id": "342b_pdf_001", "file_name": "pdf_1.pdf", "table_type": "BASIC_DATA", "caption": "基础数据"}]
    )
    excluded_df = pd.DataFrame(
        [{"table_id": "x1", "pdf_id": "342b_pdf_001", "file_name": "pdf_1.pdf", "table_type": "DISCLAIMER", "caption": "免责声明"}]
    )
    with pd.ExcelWriter(output_dir / "core_metric_candidate_quality_342e.xlsx", engine="openpyxl") as writer:
        pd.DataFrame([summary]).to_excel(writer, sheet_name="01_TABLE_QUALITY_SUMMARY", index=False)
        pd.concat([core_df, metadata_df.reindex(columns=core_df.columns), excluded_df.reindex(columns=core_df.columns)], ignore_index=True).to_excel(writer, sheet_name="03_ALL_TABLE_BLOCKS", index=False)
        core_df.to_excel(writer, sheet_name="05_CORE_EXTRACTABLE", index=False)
        metadata_df.to_excel(writer, sheet_name="06_METADATA_EXTRACTABLE", index=False)
        excluded_df.to_excel(writer, sheet_name="07_EXCLUDED_TABLES", index=False)
    return output_dir


def _seed_342c6(root: Path) -> Path:
    output_dir = root / "output" / "mineru_pilot_network_recovery_342c6"
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "mineru_pilot_network_recovery_342c6_summary.json", {"final_success_count": 5, "final_failed_count": 0, "qa_fail_count": 0, "decision": "MINERU_PILOT_NETWORK_RECOVERY_342C6_READY"})
    return output_dir


def _seed_342d(root: Path) -> Path:
    output_dir = root / "output" / "parser_ensemble_compare_342d"
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "parser_ensemble_compare_342d_summary.json", {"compared_pdf_count": 5, "mineru_success_count": 5, "mineru_artifact_complete_count": 5, "ready_for_342e": "true", "qa_fail_count": 0, "decision": "PARSER_ENSEMBLE_COMPARE_342D_READY"})
    return output_dir


def test_build_342f_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b(repo_root)
    mineru_342c6_dir = _seed_342c6(repo_root)
    parser_compare_342d_dir = _seed_342d(repo_root)
    candidate_quality_342e_dir = _seed_342e(repo_root, ready=True)

    artifacts = build_table_first_core_financial_extraction_342f(
        corpus_342b_dir=corpus_dir,
        mineru_342c6_dir=mineru_342c6_dir,
        parser_compare_342d_dir=parser_compare_342d_dir,
        candidate_quality_342e_dir=candidate_quality_342e_dir,
        output_dir=repo_root / "output" / "table_first_core_financial_extraction_342f",
        repo_root=repo_root,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    long_df = artifacts["workbook_sheets"]["03_LONG_FORM_CELLS"]
    trusted_df = artifacts["workbook_sheets"]["04_TRUSTED_CELLS"]
    review_df = artifacts["workbook_sheets"]["05_REVIEW_REQUIRED"]
    coverage_df = artifacts["workbook_sheets"]["07_METRIC_COVERAGE"]
    assert summary["audited_pdf_count"] == 5
    assert summary["input_core_extractable_table_count"] == 4
    assert summary["parsed_core_table_count"] >= 3
    assert summary["html_parse_failed_table_count"] == 1
    assert summary["long_form_cell_count"] > 0
    assert summary["trusted_cell_count"] > 0
    assert summary["review_required_cell_count"] > 0
    assert summary["duplicate_cell_count"] > 0
    assert summary["ready_for_342g"] == "true"
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_DECISION
    assert "revenue_yoy" in set(long_df["metric_standardized"].tolist())
    assert "PAREN_NEGATIVE_VALUE" in "|".join(long_df["risk_flags"].astype(str).tolist())
    assert "REVIEW_REQUIRED_TABLE_PARSE_FAILED" in set(review_df["review_reason"].tolist())
    assert "revenue" in set(coverage_df["metric_standardized"].tolist())
    assert all(table_id not in set(long_df["table_id"].tolist()) for table_id in ["m1", "x1"])


def test_build_342f_fails_when_342e_not_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b(repo_root)
    mineru_342c6_dir = _seed_342c6(repo_root)
    parser_compare_342d_dir = _seed_342d(repo_root)
    candidate_quality_342e_dir = _seed_342e(repo_root, ready=False)

    artifacts = build_table_first_core_financial_extraction_342f(
        corpus_342b_dir=corpus_dir,
        mineru_342c6_dir=mineru_342c6_dir,
        parser_compare_342d_dir=parser_compare_342d_dir,
        candidate_quality_342e_dir=candidate_quality_342e_dir,
        output_dir=repo_root / "output" / "table_first_core_financial_extraction_342f",
        repo_root=repo_root,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    assert artifacts["summary"]["qa_fail_count"] >= 1
    assert artifacts["summary"]["decision"].endswith("NOT_READY")
