from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.mineru_real_pdf_intake_337a import (  # noqa: E402
    BLOCKED_DECISION,
    READY_DECISION,
    build_mineru_real_pdf_intake_337a,
)


def _write_fake_mineru_output(parse_dir: Path) -> None:
    parse_dir.mkdir(parents=True, exist_ok=True)
    content = [
        {"type": "text", "text": "示例公司 600000.SH 买入 2026年6月8日 某某证券", "page_idx": 0},
        {"type": "text", "text": "财务数据与估值", "page_idx": 1},
        {
            "type": "table",
            "img_path": "images/sample.jpg",
            "table_caption": ["财务数据与估值"],
            "table_footnote": [],
            "table_body": "<table><tr><td>指标</td><td>2024A</td><td>2025A</td><td>2026E</td></tr><tr><td>营业收入(百万元)</td><td>100</td><td>120</td><td>140</td></tr><tr><td>归母净利润(百万元)</td><td>20</td><td>24</td><td>30</td></tr><tr><td>EPS(元/股)</td><td>1.0</td><td>1.2</td><td>1.5</td></tr><tr><td>ROE(%)</td><td>10</td><td>11</td><td>12</td></tr><tr><td>P/E(倍)</td><td>12</td><td>11</td><td>10</td></tr></table>",
            "bbox": [0, 0, 100, 100],
            "page_idx": 1,
        },
    ]
    (parse_dir / "sample_content_list.json").write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    (parse_dir / "sample.md").write_text("# 示例\n\n财务数据与估值\n", encoding="utf-8")
    images_dir = parse_dir / "images"
    images_dir.mkdir(exist_ok=True)
    (images_dir / "sample.jpg").write_bytes(b"fake")


def _fake_ready_runner(pdf_path: Path, mineru_outputs_root: Path, mineru_exe: Path):
    del mineru_exe
    parse_dir = mineru_outputs_root / pdf_path.stem / "auto"
    _write_fake_mineru_output(parse_dir)
    return {
        "success": True,
        "parse_dir": parse_dir,
        "status": "fake_success",
        "stdout": "",
        "stderr": "",
        "manual_command": f"manual {pdf_path.name}",
        "returncode": 0,
    }


def _fake_blocked_runner(pdf_path: Path, mineru_outputs_root: Path, mineru_exe: Path):
    del mineru_outputs_root, mineru_exe
    return {
        "success": False,
        "parse_dir": None,
        "status": "mineru_missing",
        "stdout": "",
        "stderr": f"missing mineru for {pdf_path.name}",
        "manual_command": f"manual {pdf_path.name}",
        "returncode": None,
    }


def test_build_mineru_real_pdf_intake_337a_ready(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    input_dir.mkdir()
    (input_dir / "one.pdf").write_bytes(b"%PDF-1.4 one")
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    artifacts = build_mineru_real_pdf_intake_337a(
        input_pdf_dir=input_dir,
        output_dir=output_dir,
        mineru_runner=_fake_ready_runner,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["pdf_found_count"] == 1
    assert summary["pdf_processed_count"] == 1
    assert summary["mineru_success_count"] == 1
    assert summary["reviewed_count"] >= 5
    assert summary["qa_fail_count"] == 0

    document_summary = artifacts["document_rows"][0]
    assert document_summary["mineru_table_count"] == 1
    assert document_summary["financial_table_candidate_count"] == 1
    assert document_summary["page_count"] == 2

    workbook_sheets = artifacts["combined_workbook_sheets"]
    assert "01_REVIEWED_CORE_METRICS" in workbook_sheets
    assert "06_FINANCIAL_TABLE_CANDIDATES" in workbook_sheets
    reviewed_df = workbook_sheets["01_REVIEWED_CORE_METRICS"]
    assert not reviewed_df.empty
    assert "metric" in reviewed_df.columns


def test_build_mineru_real_pdf_intake_337a_blocked_when_mineru_unavailable(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    input_dir.mkdir()
    (input_dir / "one.pdf").write_bytes(b"%PDF-1.4 one")
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    artifacts = build_mineru_real_pdf_intake_337a(
        input_pdf_dir=input_dir,
        output_dir=output_dir,
        mineru_runner=_fake_blocked_runner,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    assert artifacts["summary"]["decision"] == BLOCKED_DECISION
    assert artifacts["summary"]["pdf_found_count"] == 1
    assert artifacts["summary"]["pdf_processed_count"] == 0
    assert artifacts["qa_json"]["blocked_reasons"]
    assert artifacts["summary"]["manual_mineru_commands"] == ["manual one.pdf"]
