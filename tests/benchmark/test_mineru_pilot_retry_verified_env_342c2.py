from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.mineru_pilot_retry_verified_env_342c2 import (  # noqa: E402
    READY_DECISION,
    build_mineru_pilot_retry_verified_env_342c2,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_342b_workbook(root: Path) -> Path:
    output_dir = root / "output" / "real_pdf_corpus_intake_342b"
    workbook_path = output_dir / "real_pdf_corpus_intake_342b.xlsx"
    output_dir.mkdir(parents=True, exist_ok=True)
    corpus_df = pd.DataFrame(
        [
            {
                "corpus_pdf_id": f"342b_pdf_{idx:03d}",
                "file_name": f"sample_{idx:02d}.pdf",
                "file_path": str(root / "input" / f"sample_{idx:02d}.pdf"),
                "file_size_mb": 0.5,
                "sha256": f"sha-{idx:02d}",
                "modified_time": "2026-06-09T00:00:00+00:00",
                "source_bucket": "real_test",
                "document_hint": f"sample {idx}",
                "page_count": idx + 2,
                "intake_status": "INTAKE_READY",
            }
            for idx in range(1, 6)
        ]
    )
    tier_df = pd.DataFrame(
        [
            {
                "corpus_pdf_id": f"342b_pdf_{idx:03d}",
                "assigned_tier": tier,
                "tier_confidence": "medium",
                "tier_reason": "test tier",
                "expected_parser_risk": "medium",
                "expected_review_burden": "medium",
            }
            for idx, tier in enumerate(["Tier A", "Tier B", "Tier C", "Tier D", "Tier F"], start=1)
        ]
    )
    split_df = pd.DataFrame(
        [
            {
                "corpus_pdf_id": f"342b_pdf_{idx:03d}",
                "split": "pilot_set",
                "split_reason": "test pilot assignment",
            }
            for idx in range(1, 6)
        ]
    )
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "Purpose", "message": "test"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"decision": "REAL_PDF_CORPUS_INTAKE_342B_READY"}]).to_excel(writer, sheet_name="01_CORPUS_SUMMARY", index=False)
        corpus_df.to_excel(writer, sheet_name="02_PDF_CORPUS", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="03_DEDUP_AUDIT", index=False)
        tier_df.to_excel(writer, sheet_name="04_TIER_ASSIGNMENT", index=False)
        split_df.to_excel(writer, sheet_name="05_SPLIT_PLAN", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="06_METADATA_AUDIT", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="07_RUN_READINESS", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="08_RISK_FLAGS", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="09_NO_WRITE_BACK_PROOF", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="10_NEXT_STEPS", index=False)
    _write_json(
        output_dir / "real_pdf_corpus_intake_342b_summary.json",
        {
            "current_pdf_count": 31,
            "unique_pdf_count": 31,
            "pilot_set_count": 5,
            "qa_fail_count": 0,
            "decision": "REAL_PDF_CORPUS_INTAKE_342B_READY",
        },
    )
    _write_json(output_dir / "real_pdf_corpus_intake_342b_manifest.json", {"task": "342B"})
    for idx in range(1, 6):
        pdf_path = root / "input" / f"sample_{idx:02d}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4 test pdf")
    return output_dir


def _seed_342c_failure(root: Path, *, include_ssl: bool = True) -> Path:
    output_dir = root / "output" / "mineru_batch_parse_benchmark_342c"
    output_dir.mkdir(parents=True, exist_ok=True)
    error_text = (
        "requests.exceptions.SSLError: HTTPSConnectionPool(host='huggingface.co', port=443) "
        "certificate verify failed"
        if include_ssl
        else "generic MinerU failure"
    )
    parse_df = pd.DataFrame(
        [
            {
                "corpus_pdf_id": f"342b_pdf_{idx:03d}",
                "file_name": f"sample_{idx:02d}.pdf",
                "file_path": str(root / "input" / f"sample_{idx:02d}.pdf"),
                "sha256": f"sha-{idx:02d}",
                "split": "pilot_set",
                "assigned_tier": "Tier A",
                "page_count": idx + 2,
                "parse_status": "FAILED",
                "runtime_seconds": 1.0 + idx,
                "output_dir": "",
                "markdown_file_count": 0,
                "json_file_count": 0,
                "html_file_count": 0,
                "image_file_count": 0,
                "table_like_file_count": 0,
                "output_file_count": 0,
                "output_size_mb": 0,
                "empty_output_flag": True,
                "error_message": error_text,
                "command_used": "mineru ...",
            }
            for idx in range(1, 6)
        ]
    )
    with pd.ExcelWriter(output_dir / "mineru_batch_parse_benchmark_342c.xlsx", engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "Purpose", "message": "test"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"decision": "MINERU_BATCH_PARSE_BENCHMARK_342C_READY_WITH_FAILURES"}]).to_excel(writer, sheet_name="01_PARSE_SUMMARY", index=False)
        parse_df.to_excel(writer, sheet_name="02_PDF_PARSE_RESULTS", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="03_OUTPUT_ARTIFACT_AUDIT", index=False)
        pd.DataFrame([{"corpus_pdf_id": "342b_pdf_001", "error_message": error_text}]).to_excel(writer, sheet_name="04_FAILURE_AUDIT", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="05_EMPTY_OUTPUT_AUDIT", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="06_RUNTIME_AUDIT", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="07_NEXT_342D_READINESS", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="08_NO_WRITE_BACK_PROOF", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="09_NEXT_STEPS", index=False)
    _write_json(
        output_dir / "mineru_batch_parse_benchmark_342c_summary.json",
        {
            "pilot_total_count": 5,
            "mineru_success_count": 0,
            "mineru_failed_count": 5,
            "empty_output_count": 5,
            "qa_fail_count": 0,
            "ready_for_342d": "false",
            "decision": "MINERU_BATCH_PARSE_BENCHMARK_342C_READY_WITH_FAILURES",
        },
    )
    _write_json(output_dir / "mineru_batch_parse_benchmark_342c_qa.json", {"qa_fail_count": 0, "checks": []})
    return output_dir


def _write_fake_mineru_script(root: Path) -> Path:
    script_path = root / "fake_mineru_342c2.py"
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
        "payload = {'pages': [{'page_idx': 0, 'blocks': [{'type': 'text', 'text': 'x' * 300}]}]}\n"
        "(out / f'{pdf.stem}_content_list.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')\n"
        "(out / f'{pdf.stem}.md').write_text('# test\\n' + ('markdown content\\n' * 30), encoding='utf-8')\n"
        "(out / 'tables.html').write_text('<table><tr><td>x</td></tr></table>', encoding='utf-8')\n"
        "print('ok')\n",
        encoding="utf-8",
    )
    return script_path


def test_build_342c2_detects_ssl_failure_and_successful_retry(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b_workbook(repo_root)
    mineru_342c_dir = _seed_342c_failure(repo_root, include_ssl=True)
    script_path = _write_fake_mineru_script(repo_root)

    artifacts = build_mineru_pilot_retry_verified_env_342c2(
        corpus_342b_dir=corpus_dir,
        mineru_342c_dir=mineru_342c_dir,
        output_dir=repo_root / "output" / "mineru_pilot_retry_verified_env_342c2",
        repo_root=repo_root,
        mineru_command=f'python "{script_path}"',
        limit=5,
        working_lab_dir=repo_root,
        model_cache_dir=repo_root / "models",
        mineru_config_path=None,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    parse_results_df = artifacts["workbook_sheets"]["02_RETRY_PARSE_RESULTS"]
    assert summary["original_342c_ssl_failure_detected"] is True
    assert summary["original_342c_huggingface_detected"] is True
    assert summary["retry_pilot_total_count"] == 5
    assert summary["retry_mineru_success_count"] == 5
    assert summary["retry_mineru_failed_count"] == 0
    assert summary["empty_output_count"] == 0
    assert summary["ready_for_342d"] == "true"
    assert summary["decision"] == READY_DECISION
    assert summary["qa_fail_count"] == 0
    assert set(parse_results_df["parse_status"].tolist()) == {"SUCCESS"}


def test_build_342c2_partial_success_is_conditional(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b_workbook(repo_root)
    mineru_342c_dir = _seed_342c_failure(repo_root, include_ssl=True)
    script_path = _write_fake_mineru_script(repo_root)

    old_fail_token = os.environ.get("FAKE_FAIL_TOKEN")
    os.environ["FAKE_FAIL_TOKEN"] = "sample_04"
    try:
        artifacts = build_mineru_pilot_retry_verified_env_342c2(
            corpus_342b_dir=corpus_dir,
            mineru_342c_dir=mineru_342c_dir,
            output_dir=repo_root / "output" / "mineru_pilot_retry_verified_env_342c2",
            repo_root=repo_root,
            mineru_command=f'python "{script_path}"',
            limit=5,
            working_lab_dir=repo_root,
            model_cache_dir=repo_root / "models",
            mineru_config_path=None,
            alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
            scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
        )
    finally:
        if old_fail_token is None:
            os.environ.pop("FAKE_FAIL_TOKEN", None)
        else:
            os.environ["FAKE_FAIL_TOKEN"] = old_fail_token

    summary = artifacts["summary"]
    failure_df = artifacts["workbook_sheets"]["05_RETRY_FAILURE_AUDIT"]
    assert summary["retry_mineru_success_count"] == 4
    assert summary["retry_mineru_failed_count"] == 1
    assert summary["ready_for_342d"] == "conditional"
    assert summary["qa_fail_count"] == 0
    assert len(failure_df) == 1


def test_build_342c2_missing_ssl_recap_fails_qa(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b_workbook(repo_root)
    mineru_342c_dir = _seed_342c_failure(repo_root, include_ssl=False)
    script_path = _write_fake_mineru_script(repo_root)

    artifacts = build_mineru_pilot_retry_verified_env_342c2(
        corpus_342b_dir=corpus_dir,
        mineru_342c_dir=mineru_342c_dir,
        output_dir=repo_root / "output" / "mineru_pilot_retry_verified_env_342c2",
        repo_root=repo_root,
        mineru_command=f'python "{script_path}"',
        limit=5,
        working_lab_dir=repo_root,
        model_cache_dir=repo_root / "models",
        mineru_config_path=None,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    assert summary["original_342c_ssl_failure_detected"] is False
    assert summary["qa_fail_count"] >= 1
    assert summary["decision"].endswith("NOT_READY")
