from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.core_metric_candidate_quality_342e import (  # noqa: E402
    READY_DECISION,
    build_core_metric_candidate_quality_342e,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_342b_workbook(root: Path) -> Path:
    output_dir = root / "output" / "real_pdf_corpus_intake_342b"
    workbook_path = output_dir / "real_pdf_corpus_intake_342b.xlsx"
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {"corpus_pdf_id": "342b_pdf_001", "file_name": "alpha.pdf", "file_path": str(root / "input" / "alpha.pdf"), "file_size_mb": 1.0, "sha256": "sha-001", "modified_time": "2026-06-10T00:00:00+00:00", "source_bucket": "real_test", "document_hint": "001", "page_count": 30, "intake_status": "INTAKE_READY"},
        {"corpus_pdf_id": "342b_pdf_002", "file_name": "beta.pdf", "file_path": str(root / "input" / "beta.pdf"), "file_size_mb": 1.0, "sha256": "sha-002", "modified_time": "2026-06-10T00:00:00+00:00", "source_bucket": "real_test", "document_hint": "002", "page_count": 28, "intake_status": "INTAKE_READY"},
        {"corpus_pdf_id": "342b_pdf_003", "file_name": "gamma.pdf", "file_path": str(root / "input" / "gamma.pdf"), "file_size_mb": 1.0, "sha256": "sha-003", "modified_time": "2026-06-10T00:00:00+00:00", "source_bucket": "real_test", "document_hint": "003", "page_count": 26, "intake_status": "INTAKE_READY"},
        {"corpus_pdf_id": "342b_pdf_004", "file_name": "delta.pdf", "file_path": str(root / "input" / "delta.pdf"), "file_size_mb": 1.0, "sha256": "sha-004", "modified_time": "2026-06-10T00:00:00+00:00", "source_bucket": "real_test", "document_hint": "004", "page_count": 24, "intake_status": "INTAKE_READY"},
        {"corpus_pdf_id": "342b_pdf_005", "file_name": "epsilon.pdf", "file_path": str(root / "input" / "epsilon.pdf"), "file_size_mb": 1.0, "sha256": "sha-005", "modified_time": "2026-06-10T00:00:00+00:00", "source_bucket": "real_test", "document_hint": "005", "page_count": 22, "intake_status": "INTAKE_READY"},
    ]
    corpus_df = pd.DataFrame(rows)
    tier_df = pd.DataFrame(
        [
            {"corpus_pdf_id": row["corpus_pdf_id"], "assigned_tier": "Tier A", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"}
            for row in rows
        ]
    )
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
    for row in rows:
        pdf_path = Path(row["file_path"])
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4 test")
    return output_dir


def _seed_parse_dir(parse_dir: Path, stem: str, variant: str) -> None:
    parse_dir.mkdir(parents=True, exist_ok=True)
    (parse_dir / "images").mkdir(exist_ok=True)
    (parse_dir / "images" / f"{stem}.jpg").write_bytes(b"jpeg")
    if variant == "core":
        html = "<table><tr><td>盈利预测和财务指标</td><td>2026E</td><td>2027E</td></tr><tr><td>营业收入（亿元）</td><td>100</td><td>110</td></tr><tr><td>归母净利润（亿元）</td><td>20</td><td>24</td></tr><tr><td>每股收益（元）</td><td>1.2</td><td>1.4</td></tr><tr><td>市盈率（PE）</td><td>10</td><td>8</td></tr></table>"
        caption = ["财务预测与估值"]
        footnote = ["资料来源：测试研究所"]
    elif variant == "metadata":
        html = "<table><tr><td>投资评级</td><td>买入</td></tr><tr><td>收盘价</td><td>10元</td></tr><tr><td>总市值</td><td>100亿元</td></tr></table>"
        caption = ["基础数据"]
        footnote = []
    elif variant == "disclaimer":
        html = "<table><tr><td>免责声明</td></tr><tr><td>本报告仅供参考</td></tr></table>"
        caption = ["免责声明"]
        footnote = []
    else:
        html = "<table><tr><td>未知表</td><td>2026E</td></tr><tr><td>数据A</td><td>1</td></tr></table>"
        caption = ["待判定表格"]
        footnote = []

    content_list = [
        {"type": "table", "page_idx": 0, "bbox": [10, 20, 100, 120], "img_path": f"images/{stem}.jpg", "table_caption": caption, "table_footnote": footnote, "table_body": html},
    ]
    content_list_v2 = [[{"type": "table", "bbox": [10, 20, 100, 120], "content": {"image_source": {"path": f"images/{stem}.jpg"}, "table_caption": [{"type": "text", "content": caption[0] if caption else ""}], "table_footnote": [{"type": "text", "content": footnote[0]}] if footnote else [], "html": html}}]]
    middle = {"pdf_info": [{"page_idx": 0, "preproc_blocks": [{"type": "table", "bbox": [10, 20, 100, 120], "index": 1, "score": 0.99}], "para_blocks": [], "discarded_blocks": []}]}
    model = [{"page_info": {"page_no": 0, "width": 1000, "height": 1500}, "layout_dets": [{"label": "table", "bbox": [10, 20, 100, 120], "score": 0.98, "index": 1}]}]
    markdown = f"# report\n{html}\n"

    (parse_dir / f"{stem}.md").write_text(markdown, encoding="utf-8")
    (parse_dir / f"{stem}_content_list.json").write_text(json.dumps(content_list, ensure_ascii=False), encoding="utf-8")
    (parse_dir / f"{stem}_content_list_v2.json").write_text(json.dumps(content_list_v2, ensure_ascii=False), encoding="utf-8")
    (parse_dir / f"{stem}_middle.json").write_text(json.dumps(middle, ensure_ascii=False), encoding="utf-8")
    (parse_dir / f"{stem}_model.json").write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")


def _seed_342c6(root: Path) -> Path:
    output_dir = root / "output" / "mineru_pilot_network_recovery_342c6"
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    variants = ["core", "core", "metadata", "disclaimer", "unknown"]
    for index, variant in enumerate(variants, start=1):
        pdf_id = f"342b_pdf_00{index}"
        stem = f"parse_{index}"
        parse_dir = output_dir / "parse_bank" / stem / "auto"
        _seed_parse_dir(parse_dir, stem, variant)
        rows.append(
            {
                "corpus_pdf_id": pdf_id,
                "file_name": f"{stem}.pdf",
                "source": "reused_342c2_success" if index <= 3 else "rerun_342c6",
                "final_parse_status": "SUCCESS",
                "output_dir": str(parse_dir),
                "md_file_count": 1,
                "content_list_json_count": 1,
                "middle_json_count": 1,
                "image_file_count": 1,
                "output_file_count": 5,
                "output_size_mb": 0.01,
                "error_message": "",
            }
        )
    final_df = pd.DataFrame(rows)
    with pd.ExcelWriter(output_dir / "mineru_pilot_network_recovery_342c6.xlsx", engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "Purpose", "message": "test"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"decision": "MINERU_PILOT_NETWORK_RECOVERY_342C6_READY"}]).to_excel(writer, sheet_name="01_RECOVERY_SUMMARY", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="02_FAILED_ROWS_TO_RERUN", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="03_RERUN_RESULTS", index=False)
        final_df.to_excel(writer, sheet_name="04_FINAL_PILOT_ROLLUP", index=False)
    _write_json(output_dir / "mineru_pilot_network_recovery_342c6_summary.json", {"final_success_count": 5, "final_failed_count": 0, "ready_for_342d": "true", "qa_fail_count": 0, "decision": "MINERU_PILOT_NETWORK_RECOVERY_342C6_READY", "no_write_back_proof_passed": True})
    _write_json(output_dir / "mineru_pilot_network_recovery_342c6_qa.json", {"qa_fail_count": 0, "checks": []})
    return output_dir


def _seed_342d(root: Path, ready: bool = True) -> Path:
    output_dir = root / "output" / "parser_ensemble_compare_342d"
    output_dir.mkdir(parents=True, exist_ok=True)
    compare_df = pd.DataFrame(
        [
            {"corpus_pdf_id": f"342b_pdf_00{i}", "file_name": f"parse_{i}.pdf", "mineru_artifact_complete_flag": True, "mineru_table_signal_score": 10, "mineru_financial_signal_score": 10, "mineru_markdown_usable_flag": True, "baseline_available": False, "baseline_table_signal_score": 0, "baseline_financial_signal_score": 0, "baseline_missing_reason": "no_matching_historical_artifacts", "compare_judgment": "INSUFFICIENT_BASELINE"}
            for i in range(1, 6)
        ]
    )
    with pd.ExcelWriter(output_dir / "parser_ensemble_compare_342d.xlsx", engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "Purpose", "message": "test"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"decision": "PARSER_ENSEMBLE_COMPARE_342D_READY" if ready else "PARSER_ENSEMBLE_COMPARE_342D_NOT_READY"}]).to_excel(writer, sheet_name="01_COMPARE_SUMMARY", index=False)
        compare_df.to_excel(writer, sheet_name="02_PDF_LEVEL_COMPARE", index=False)
    _write_json(output_dir / "parser_ensemble_compare_342d_summary.json", {"compared_pdf_count": 5, "mineru_success_count": 5 if ready else 4, "mineru_artifact_complete_count": 5 if ready else 4, "ready_for_342e": "true" if ready else "conditional", "qa_fail_count": 0 if ready else 1, "decision": "PARSER_ENSEMBLE_COMPARE_342D_READY" if ready else "PARSER_ENSEMBLE_COMPARE_342D_NOT_READY", "no_write_back_proof_passed": True})
    _write_json(output_dir / "parser_ensemble_compare_342d_qa.json", {"qa_fail_count": 0 if ready else 1, "checks": []})
    return output_dir


def test_build_342e_table_first_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b_workbook(repo_root)
    mineru_342c6_dir = _seed_342c6(repo_root)
    parser_compare_342d_dir = _seed_342d(repo_root, ready=True)

    artifacts = build_core_metric_candidate_quality_342e(
        corpus_342b_dir=corpus_dir,
        mineru_342c6_dir=mineru_342c6_dir,
        parser_compare_342d_dir=parser_compare_342d_dir,
        output_dir=repo_root / "output" / "core_metric_candidate_quality_342e",
        repo_root=repo_root,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    all_tables = artifacts["workbook_sheets"]["03_ALL_TABLE_BLOCKS"]
    coverage = artifacts["workbook_sheets"]["04_TABLE_TYPE_COVERAGE"]
    assert summary["audited_pdf_count"] == 5
    assert summary["total_table_block_count"] > 0
    assert summary["core_extractable_table_count"] >= 2
    assert summary["metadata_extractable_table_count"] >= 1
    assert summary["excluded_table_count"] >= 1
    assert summary["ready_for_342f"] in {"true", "conditional"}
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_DECISION
    assert "CORE_FORECAST_SUMMARY" in set(all_tables["table_type"].tolist())
    assert "BASIC_DATA" in set(all_tables["table_type"].tolist())
    assert "DISCLAIMER" in set(all_tables["table_type"].tolist())
    assert len(coverage) == 12


def test_build_342e_fails_when_342d_not_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b_workbook(repo_root)
    mineru_342c6_dir = _seed_342c6(repo_root)
    parser_compare_342d_dir = _seed_342d(repo_root, ready=False)

    artifacts = build_core_metric_candidate_quality_342e(
        corpus_342b_dir=corpus_dir,
        mineru_342c6_dir=mineru_342c6_dir,
        parser_compare_342d_dir=parser_compare_342d_dir,
        output_dir=repo_root / "output" / "core_metric_candidate_quality_342e",
        repo_root=repo_root,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    assert summary["qa_fail_count"] >= 1
    assert summary["decision"].endswith("NOT_READY")
