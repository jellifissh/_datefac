from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.mineru_pilot_network_recovery_342c6 import (  # noqa: E402
    READY_DECISION,
    build_mineru_pilot_network_recovery_342c6,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_342b_workbook(root: Path) -> Path:
    output_dir = root / "output" / "real_pdf_corpus_intake_342b"
    workbook_path = output_dir / "real_pdf_corpus_intake_342b.xlsx"
    output_dir.mkdir(parents=True, exist_ok=True)
    corpus_rows = [
        {
            "corpus_pdf_id": "342b_pdf_013",
            "file_name": "H3_AP202606081823356439_1.pdf",
            "file_path": str(root / "input" / "H3_AP202606081823356439_1.pdf"),
            "file_size_mb": 0.5,
            "sha256": "sha-013",
            "modified_time": "2026-06-10T00:00:00+00:00",
            "source_bucket": "real_test",
            "document_hint": "pdf 013",
            "page_count": 38,
            "intake_status": "INTAKE_READY",
        },
        {
            "corpus_pdf_id": "342b_pdf_017",
            "file_name": "H3_AP202605141822318031_1.pdf",
            "file_path": str(root / "input" / "H3_AP202605141822318031_1.pdf"),
            "file_size_mb": 0.5,
            "sha256": "sha-017",
            "modified_time": "2026-06-10T00:00:00+00:00",
            "source_bucket": "real_test",
            "document_hint": "pdf 017",
            "page_count": 22,
            "intake_status": "INTAKE_READY",
        },
        {
            "corpus_pdf_id": "342b_pdf_027",
            "file_name": "H3_AP202606061823323264_1.pdf",
            "file_path": str(root / "input" / "H3_AP202606061823323264_1.pdf"),
            "file_size_mb": 0.5,
            "sha256": "sha-027",
            "modified_time": "2026-06-10T00:00:00+00:00",
            "source_bucket": "real_test",
            "document_hint": "pdf 027",
            "page_count": 68,
            "intake_status": "INTAKE_READY",
        },
        {
            "corpus_pdf_id": "342b_pdf_010",
            "file_name": "hard_report.pdf",
            "file_path": str(root / "input" / "hard_report.pdf"),
            "file_size_mb": 0.5,
            "sha256": "sha-010",
            "modified_time": "2026-06-10T00:00:00+00:00",
            "source_bucket": "real_test",
            "document_hint": "pdf 010",
            "page_count": 6,
            "intake_status": "INTAKE_READY",
        },
        {
            "corpus_pdf_id": "342b_pdf_002",
            "file_name": "6a0b9e0769373f552c4348621ad58543.pdf",
            "file_path": str(root / "input" / "6a0b9e0769373f552c4348621ad58543.pdf"),
            "file_size_mb": 0.5,
            "sha256": "sha-002",
            "modified_time": "2026-06-10T00:00:00+00:00",
            "source_bucket": "real_test",
            "document_hint": "pdf 002",
            "page_count": 5,
            "intake_status": "INTAKE_READY",
        },
    ]
    corpus_df = pd.DataFrame(corpus_rows)
    tier_df = pd.DataFrame(
        [
            {"corpus_pdf_id": "342b_pdf_013", "assigned_tier": "Tier A", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"},
            {"corpus_pdf_id": "342b_pdf_017", "assigned_tier": "Tier B", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"},
            {"corpus_pdf_id": "342b_pdf_027", "assigned_tier": "Tier C", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"},
            {"corpus_pdf_id": "342b_pdf_010", "assigned_tier": "Tier D", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"},
            {"corpus_pdf_id": "342b_pdf_002", "assigned_tier": "Tier F", "tier_confidence": "high", "tier_reason": "test", "expected_parser_risk": "medium", "expected_review_burden": "medium"},
        ]
    )
    split_df = pd.DataFrame(
        [{"corpus_pdf_id": row["corpus_pdf_id"], "split": "pilot_set", "split_reason": "test"} for row in corpus_rows]
    )
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "Purpose", "message": "test"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"decision": "REAL_PDF_CORPUS_INTAKE_342B_READY"}]).to_excel(writer, sheet_name="01_CORPUS_SUMMARY", index=False)
        corpus_df.to_excel(writer, sheet_name="02_PDF_CORPUS", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="03_DEDUP_AUDIT", index=False)
        tier_df.to_excel(writer, sheet_name="04_TIER_ASSIGNMENT", index=False)
        split_df.to_excel(writer, sheet_name="05_SPLIT_PLAN", index=False)
    _write_json(
        output_dir / "real_pdf_corpus_intake_342b_summary.json",
        {
            "pilot_set_count": 5,
            "qa_fail_count": 0,
            "decision": "REAL_PDF_CORPUS_INTAKE_342B_READY",
        },
    )
    _write_json(output_dir / "real_pdf_corpus_intake_342b_manifest.json", {"task": "342B"})
    for row in corpus_rows:
        pdf_path = Path(row["file_path"])
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4 test")
    return output_dir


def _write_fake_success_artifacts(parse_dir: Path) -> None:
    parse_dir.mkdir(parents=True, exist_ok=True)
    (parse_dir / "artifact.md").write_text("# ok\n", encoding="utf-8")
    (parse_dir / "artifact_content_list.json").write_text('{"pages":[{"page_idx":0}]}', encoding="utf-8")
    (parse_dir / "artifact_middle.json").write_text('{"middle":true}', encoding="utf-8")
    (parse_dir / "page_1.png").write_bytes(b"png")


def _seed_342c2_after_env_fix(root: Path) -> Path:
    output_dir = root / "output" / "mineru_pilot_retry_verified_env_342c2_after_env_fix"
    mineru_outputs = output_dir / "mineru_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    for stem in [
        "H3_AP202606081823356439_1",
        "H3_AP202605141822318031_1",
        "H3_AP202606061823323264_1",
    ]:
        _write_fake_success_artifacts(mineru_outputs / stem / "auto")
    parse_df = pd.DataFrame(
        [
            {
                "corpus_pdf_id": "342b_pdf_013",
                "file_name": "H3_AP202606081823356439_1.pdf",
                "parse_status": "SUCCESS",
                "output_dir": str(mineru_outputs / "H3_AP202606081823356439_1" / "auto"),
                "output_file_count": 4,
                "markdown_file_count": 1,
                "json_file_count": 2,
                "empty_output_flag": False,
                "error_message": "",
            },
            {
                "corpus_pdf_id": "342b_pdf_017",
                "file_name": "H3_AP202605141822318031_1.pdf",
                "parse_status": "SUCCESS",
                "output_dir": str(mineru_outputs / "H3_AP202605141822318031_1" / "auto"),
                "output_file_count": 4,
                "markdown_file_count": 1,
                "json_file_count": 2,
                "empty_output_flag": False,
                "error_message": "",
            },
            {
                "corpus_pdf_id": "342b_pdf_027",
                "file_name": "H3_AP202606061823323264_1.pdf",
                "parse_status": "SUCCESS",
                "output_dir": str(mineru_outputs / "H3_AP202606061823323264_1" / "auto"),
                "output_file_count": 4,
                "markdown_file_count": 1,
                "json_file_count": 2,
                "empty_output_flag": False,
                "error_message": "",
            },
            {
                "corpus_pdf_id": "342b_pdf_010",
                "file_name": "hard_report.pdf",
                "parse_status": "FAILED",
                "output_dir": "",
                "output_file_count": 0,
                "markdown_file_count": 0,
                "json_file_count": 0,
                "empty_output_flag": True,
                "error_message": "",
            },
            {
                "corpus_pdf_id": "342b_pdf_002",
                "file_name": "6a0b9e0769373f552c4348621ad58543.pdf",
                "parse_status": "FAILED",
                "output_dir": "",
                "output_file_count": 0,
                "markdown_file_count": 0,
                "json_file_count": 0,
                "empty_output_flag": True,
                "error_message": "",
            },
        ]
    )
    with pd.ExcelWriter(output_dir / "mineru_pilot_retry_verified_env_342c2.xlsx", engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "Purpose", "message": "test"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"decision": "MINERU_PILOT_RETRY_VERIFIED_ENV_342C2_READY"}]).to_excel(writer, sheet_name="01_RETRY_SUMMARY", index=False)
        parse_df.to_excel(writer, sheet_name="02_RETRY_PARSE_RESULTS", index=False)
    _write_json(
        output_dir / "mineru_pilot_retry_verified_env_342c2_summary.json",
        {
            "retry_pilot_total_count": 5,
            "retry_mineru_success_count": 3,
            "retry_mineru_failed_count": 2,
            "empty_output_count": 2,
            "ready_for_342d": "conditional",
            "recommended_next_scope": "inspect_failed_retry_rows_then_compare",
            "qa_fail_count": 0,
            "decision": "MINERU_PILOT_RETRY_VERIFIED_ENV_342C2_READY",
            "no_write_back_proof_passed": True,
        },
    )
    _write_json(output_dir / "mineru_pilot_retry_verified_env_342c2_qa.json", {"qa_fail_count": 0, "checks": []})
    return output_dir


def _write_fake_mineru_script(root: Path) -> Path:
    script_path = root / "fake_mineru_342c6.py"
    script_path.write_text(
        "from pathlib import Path\n"
        "import json\n"
        "import os\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        "pdf = Path(args[args.index('-p') + 1])\n"
        "out_root = Path(args[args.index('-o') + 1])\n"
        "fail_token = os.environ.get('FAKE_FAIL_TOKEN', '')\n"
        "if fail_token and fail_token in pdf.name:\n"
        "    print('forced failure for ' + pdf.name, file=sys.stderr)\n"
        "    raise SystemExit(2)\n"
        "out = out_root / pdf.stem / 'auto'\n"
        "out.mkdir(parents=True, exist_ok=True)\n"
        "(out / f'{pdf.stem}.md').write_text('# ok\\n', encoding='utf-8')\n"
        "(out / f'{pdf.stem}_content_list.json').write_text(json.dumps({'pages':[{'page_idx':0}]}, ensure_ascii=False), encoding='utf-8')\n"
        "(out / f'{pdf.stem}_middle.json').write_text(json.dumps({'middle':True}, ensure_ascii=False), encoding='utf-8')\n"
        "(out / 'page_1.png').write_bytes(b'png')\n",
        encoding="utf-8",
    )
    return script_path


def test_build_342c6_recovers_all_failed_rows(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b_workbook(repo_root)
    mineru_342c2_dir = _seed_342c2_after_env_fix(repo_root)
    script_path = _write_fake_mineru_script(repo_root)

    artifacts = build_mineru_pilot_network_recovery_342c6(
        corpus_342b_dir=corpus_dir,
        mineru_342c2_dir=mineru_342c2_dir,
        output_dir=repo_root / "output" / "mineru_pilot_network_recovery_342c6",
        repo_root=repo_root,
        mineru_command=f'python "{script_path}"',
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    final_df = artifacts["workbook_sheets"]["04_FINAL_PILOT_ROLLUP"]
    rerun_df = artifacts["workbook_sheets"]["03_RERUN_RESULTS"]
    assert summary["original_success_count"] == 3
    assert summary["original_failed_count"] == 2
    assert summary["rerun_target_count"] == 2
    assert summary["rerun_success_count"] == 2
    assert summary["rerun_failed_count"] == 0
    assert summary["final_success_count"] == 5
    assert summary["final_failed_count"] == 0
    assert summary["final_empty_output_count"] == 0
    assert summary["ready_for_342d"] == "true"
    assert summary["recommended_342d_scope"] == "full_pilot_set_5"
    assert summary["decision"] == READY_DECISION
    assert summary["qa_fail_count"] == 0
    assert set(final_df["source"].tolist()) == {"reused_342c2_success", "rerun_342c6"}
    assert len(rerun_df) == 2


def test_build_342c6_keeps_conditional_when_one_rerun_still_fails(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b_workbook(repo_root)
    mineru_342c2_dir = _seed_342c2_after_env_fix(repo_root)
    script_path = _write_fake_mineru_script(repo_root)
    monkeypatch.setenv("FAKE_FAIL_TOKEN", "hard_report")

    artifacts = build_mineru_pilot_network_recovery_342c6(
        corpus_342b_dir=corpus_dir,
        mineru_342c2_dir=mineru_342c2_dir,
        output_dir=repo_root / "output" / "mineru_pilot_network_recovery_342c6",
        repo_root=repo_root,
        mineru_command=f'python "{script_path}"',
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    assert summary["rerun_success_count"] == 1
    assert summary["rerun_failed_count"] == 1
    assert summary["final_success_count"] == 4
    assert summary["final_failed_count"] == 1
    assert summary["ready_for_342d"] == "conditional"
    assert summary["recommended_342d_scope"] == "successful_pilot_outputs_only"
    assert summary["qa_fail_count"] == 0
