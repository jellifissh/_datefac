from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.parser_ensemble_compare_342d import (  # noqa: E402
    READY_DECISION,
    build_parser_ensemble_compare_342d,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_342b_workbook(root: Path) -> Path:
    output_dir = root / "output" / "real_pdf_corpus_intake_342b"
    workbook_path = output_dir / "real_pdf_corpus_intake_342b.xlsx"
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {"corpus_pdf_id": "342b_pdf_013", "file_name": "H3_AP202606081823356439_1.pdf", "file_path": str(root / "input" / "H3_AP202606081823356439_1.pdf"), "file_size_mb": 1.0, "sha256": "sha-013", "modified_time": "2026-06-10T00:00:00+00:00", "source_bucket": "real_test", "document_hint": "013", "page_count": 38, "intake_status": "INTAKE_READY"},
        {"corpus_pdf_id": "342b_pdf_017", "file_name": "H3_AP202605141822318031_1.pdf", "file_path": str(root / "input" / "H3_AP202605141822318031_1.pdf"), "file_size_mb": 1.0, "sha256": "sha-017", "modified_time": "2026-06-10T00:00:00+00:00", "source_bucket": "real_test", "document_hint": "017", "page_count": 22, "intake_status": "INTAKE_READY"},
        {"corpus_pdf_id": "342b_pdf_027", "file_name": "H3_AP202606061823323264_1.pdf", "file_path": str(root / "input" / "H3_AP202606061823323264_1.pdf"), "file_size_mb": 1.0, "sha256": "sha-027", "modified_time": "2026-06-10T00:00:00+00:00", "source_bucket": "real_test", "document_hint": "027", "page_count": 68, "intake_status": "INTAKE_READY"},
        {"corpus_pdf_id": "342b_pdf_010", "file_name": "hard_report.pdf", "file_path": str(root / "input" / "hard_report.pdf"), "file_size_mb": 1.0, "sha256": "sha-010", "modified_time": "2026-06-10T00:00:00+00:00", "source_bucket": "real_test", "document_hint": "010", "page_count": 6, "intake_status": "INTAKE_READY"},
        {"corpus_pdf_id": "342b_pdf_002", "file_name": "6a0b9e0769373f552c4348621ad58543.pdf", "file_path": str(root / "input" / "6a0b9e0769373f552c4348621ad58543.pdf"), "file_size_mb": 1.0, "sha256": "sha-002", "modified_time": "2026-06-10T00:00:00+00:00", "source_bucket": "real_test", "document_hint": "002", "page_count": 5, "intake_status": "INTAKE_READY"},
    ]
    corpus_df = pd.DataFrame(rows)
    tier_df = pd.DataFrame(
        [
            {"corpus_pdf_id": "342b_pdf_013", "assigned_tier": "Tier A", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"},
            {"corpus_pdf_id": "342b_pdf_017", "assigned_tier": "Tier B", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"},
            {"corpus_pdf_id": "342b_pdf_027", "assigned_tier": "Tier C", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"},
            {"corpus_pdf_id": "342b_pdf_010", "assigned_tier": "Tier D", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"},
            {"corpus_pdf_id": "342b_pdf_002", "assigned_tier": "Tier F", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"},
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


def _seed_mineru_parse_dir(parse_dir: Path, *, text: str) -> None:
    parse_dir.mkdir(parents=True, exist_ok=True)
    stem = parse_dir.parent.name
    (parse_dir / f"{stem}.md").write_text(f"# title\n{text}\n| 年份 | 营业收入 |\n|---|---|\n|2026E|100亿元|\n", encoding="utf-8")
    payload = [
        {"type": "text", "text": text, "page_idx": 0},
        {"type": "table", "text": "2026E 营业收入 100亿元 EPS 1.2元/股", "page_idx": 0},
        {"type": "image", "text": "", "page_idx": 0},
    ]
    (parse_dir / f"{stem}_content_list.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    (parse_dir / f"{stem}_middle.json").write_text('{"ok":true}', encoding="utf-8")
    (parse_dir / f"{stem}_model.json").write_text('{"ok":true}', encoding="utf-8")
    (parse_dir / f"{stem}_layout.pdf").write_bytes(b"pdf")
    (parse_dir / f"{stem}_span.pdf").write_bytes(b"pdf")
    (parse_dir / f"{stem}_origin.pdf").write_bytes(b"pdf")
    (parse_dir / "img1.jpg").write_bytes(b"jpg")


def _seed_342c6(root: Path) -> Path:
    output_dir = root / "output" / "mineru_pilot_network_recovery_342c6"
    mineru_outputs = output_dir / "mineru_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    stems = {
        "342b_pdf_013": "H3_AP202606081823356439_1",
        "342b_pdf_017": "H3_AP202605141822318031_1",
        "342b_pdf_027": "H3_AP202606061823323264_1",
        "342b_pdf_010": "hard_report",
        "342b_pdf_002": "6a0b9e0769373f552c4348621ad58543",
    }
    for corpus_pdf_id, stem in stems.items():
        _seed_mineru_parse_dir(mineru_outputs / stem / "auto", text=f"{stem} 营业收入 净利润 ROE EPS PE PB 2026E")
    final_df = pd.DataFrame(
        [
            {"corpus_pdf_id": corpus_pdf_id, "file_name": f"{stem}.pdf" if not stem.endswith(".pdf") and stem != "hard_report" else f"{stem}.pdf" if stem == "hard_report" else stem, "source": "reused_342c2_success", "final_parse_status": "SUCCESS", "output_dir": str(mineru_outputs / stem / "auto"), "md_file_count": 1, "content_list_json_count": 1, "middle_json_count": 1, "image_file_count": 1, "output_file_count": 7, "output_size_mb": 0.01, "error_message": ""}
            for corpus_pdf_id, stem in stems.items()
        ]
    )
    final_df.loc[final_df["corpus_pdf_id"] == "342b_pdf_010", "file_name"] = "hard_report.pdf"
    final_df.loc[final_df["corpus_pdf_id"] == "342b_pdf_002", "file_name"] = "6a0b9e0769373f552c4348621ad58543.pdf"
    with pd.ExcelWriter(output_dir / "mineru_pilot_network_recovery_342c6.xlsx", engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "Purpose", "message": "test"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"decision": "MINERU_PILOT_NETWORK_RECOVERY_342C6_READY"}]).to_excel(writer, sheet_name="01_RECOVERY_SUMMARY", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="02_FAILED_ROWS_TO_RERUN", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="03_RERUN_RESULTS", index=False)
        final_df.to_excel(writer, sheet_name="04_FINAL_PILOT_ROLLUP", index=False)
    _write_json(output_dir / "mineru_pilot_network_recovery_342c6_summary.json", {"final_success_count": 5, "final_failed_count": 0, "ready_for_342d": "true", "qa_fail_count": 0, "decision": "MINERU_PILOT_NETWORK_RECOVERY_342C6_READY", "no_write_back_proof_passed": True})
    _write_json(output_dir / "mineru_pilot_network_recovery_342c6_qa.json", {"qa_fail_count": 0, "checks": []})
    return output_dir


def _seed_marker_baseline(root: Path) -> None:
    base = root / "output" / "eval_marker1_no_llm_parser_benchmark" / "marker_outputs" / "6a0b9e0769373f552c4348621ad58543"
    base.mkdir(parents=True, exist_ok=True)
    marker_payload = {
        "block_type": "Document",
        "children": [
            {"block_type": "Page", "children": [{"block_type": "Table", "html": "<table><tr><td>2026E</td><td>营业收入</td></tr></table>"}]},
            {"block_type": "Text", "html": "净利润 EPS PE PB ROE"},
        ],
    }
    (base / "6a0b9e0769373f552c4348621ad58543.json").write_text(json.dumps(marker_payload, ensure_ascii=False), encoding="utf-8")
    (base / "6a0b9e0769373f552c4348621ad58543_meta.json").write_text('{"ok":true}', encoding="utf-8")


def test_build_342d_ready_with_partial_baseline(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b_workbook(repo_root)
    mineru_342c6_dir = _seed_342c6(repo_root)
    _seed_marker_baseline(repo_root)

    artifacts = build_parser_ensemble_compare_342d(
        corpus_342b_dir=corpus_dir,
        mineru_342c6_dir=mineru_342c6_dir,
        output_dir=repo_root / "output" / "parser_ensemble_compare_342d",
        repo_root=repo_root,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    compare_df = artifacts["workbook_sheets"]["02_PDF_LEVEL_COMPARE"]
    assert summary["compared_pdf_count"] == 5
    assert summary["mineru_success_count"] == 5
    assert summary["mineru_artifact_complete_count"] == 5
    assert summary["mineru_markdown_usable_count"] >= 3
    assert summary["mineru_content_list_usable_count"] == 5
    assert summary["baseline_available_count"] >= 1
    assert summary["insufficient_baseline_count"] >= 1
    assert summary["ready_for_342e"] == "true"
    assert summary["recommended_342e_scope"] == "full_pilot_set_5_mineru_outputs"
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_DECISION
    assert "INSUFFICIENT_BASELINE" in set(compare_df["compare_judgment"].tolist())


def test_build_342d_fails_when_342c6_not_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b_workbook(repo_root)
    mineru_342c6_dir = _seed_342c6(repo_root)
    _write_json(
        mineru_342c6_dir / "mineru_pilot_network_recovery_342c6_summary.json",
        {"final_success_count": 4, "final_failed_count": 1, "ready_for_342d": "conditional", "qa_fail_count": 1, "decision": "MINERU_PILOT_NETWORK_RECOVERY_342C6_NOT_READY", "no_write_back_proof_passed": True},
    )

    artifacts = build_parser_ensemble_compare_342d(
        corpus_342b_dir=corpus_dir,
        mineru_342c6_dir=mineru_342c6_dir,
        output_dir=repo_root / "output" / "parser_ensemble_compare_342d",
        repo_root=repo_root,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    assert summary["qa_fail_count"] >= 1
    assert summary["decision"].endswith("NOT_READY")
