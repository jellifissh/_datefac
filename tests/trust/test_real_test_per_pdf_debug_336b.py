from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.real_test_per_pdf_debug_336b import (  # noqa: E402
    BLOCKED_DECISION,
    READY_DECISION,
    build_real_test_per_pdf_debug_336b,
)


def _fake_page_texts(pdf_path: Path):
    if pdf_path.name == "zero.pdf":
        return (
            {
                1: "\u8d22\u52a1\u6458\u8981 2026E 2027E",
                2: "\u8425\u4e1a\u6536\u5165 \u6bcf\u80a1\u6536\u76ca \u9884\u6d4b",
            },
            [],
            2,
        )
    return (
        {
            1: "\u8425\u4e1a\u6536\u5165 2024A 120\u4ebf\u5143 2025E 140\u4ebf\u5143",
            2: "\u6295\u8d44\u8bc4\u7ea7 \u4e70\u5165 \u80a1\u7968\u4ee3\u7801 600000",
        },
        [],
        2,
    )


def _fake_extraction(pdf_path: str, pages="all", logger=None, config=None):
    del pages, logger, config
    import pandas as pd

    if pdf_path.endswith("zero.pdf"):
        return [
            {
                "page": 1,
                "table_index": 1,
                "df": pd.DataFrame(
                    [
                        ["\u76ee\u5f55", "A", "B"],
                        ["\u6bb5\u843d", "\u7b80\u4ecb", "\u8bf4\u660e"],
                    ]
                ),
            }
        ]
    return [
        {
            "page": 1,
            "table_index": 1,
            "df": pd.DataFrame(
                [
                    ["\u6307\u6807", "2024A", "2025E"],
                    ["\u8425\u4e1a\u6536\u5165", "120\u4ebf\u5143", "140\u4ebf\u5143"],
                    ["\u51c0\u5229\u7387", "18", "19"],
                ]
            ),
        }
    ]


def test_build_real_test_per_pdf_debug_336b_ready(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    input_dir.mkdir()
    (input_dir / "one.pdf").write_bytes(b"%PDF-1.4 one")
    (input_dir / "zero.pdf").write_bytes(b"%PDF-1.4 zero")
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    artifacts = build_real_test_per_pdf_debug_336b(
        input_pdf_dir=input_dir,
        output_dir=output_dir,
        extraction_fn=_fake_extraction,
        page_text_fn=_fake_page_texts,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    batch_summary = artifacts["batch_summary"]
    assert batch_summary["decision"] == READY_DECISION
    assert batch_summary["pdf_found_count"] == 2
    assert len(artifacts["document_packages"]) == 2
    assert not artifacts["batch_summary_df"].empty

    zero_doc = next(
        package["document_summary"]
        for package in artifacts["document_packages"]
        if package["document_summary"]["pdf_filename"] == "zero.pdf"
    )
    assert zero_doc["candidate_count"] == 0
    assert zero_doc["likely_failure_reason"] == "TABLE_EXTRACTION_OR_ROW_MAPPING_MISSED_FINANCIAL_PAGE"
    assert zero_doc["likely_forecast_pages"]

    one_doc = next(
        package
        for package in artifacts["document_packages"]
        if package["document_summary"]["pdf_filename"] == "one.pdf"
    )
    assert not one_doc["metric_candidates_df"].empty
    assert not one_doc["routing_preview_df"].empty
    assert "metric" in one_doc["metric_candidates_df"].columns


def test_build_real_test_per_pdf_debug_336b_blocked_when_no_pdfs(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    input_dir.mkdir()
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    artifacts = build_real_test_per_pdf_debug_336b(
        input_pdf_dir=input_dir,
        output_dir=output_dir,
        extraction_fn=_fake_extraction,
        page_text_fn=_fake_page_texts,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    assert artifacts["batch_summary"]["decision"] == BLOCKED_DECISION
    assert artifacts["batch_summary"]["pdf_found_count"] == 0
