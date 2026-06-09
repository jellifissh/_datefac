from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.real_pdf_corpus_intake_342b import (  # noqa: E402
    BENCHMARK_PLAN_READY_DECISION,
    BENCHMARK_SPLIT,
    HOLDOUT_SPLIT,
    PILOT_SPLIT,
    READY_DECISION,
    WORKBOOK_SHEETS,
    build_real_pdf_corpus_intake_342b,
)


MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
    b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
    b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R >>endobj\n"
    b"4 0 obj<< /Length 44 >>stream\nBT /F1 12 Tf 72 72 Td (342B test page) Tj ET\nendstream\nendobj\n"
    b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000202 00000 n \n"
    b"trailer<< /Root 1 0 R /Size 5 >>\nstartxref\n295\n%%EOF\n"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_pdf(path: Path, content: bytes = MINIMAL_PDF) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _seed_342a_summary(repo_root: Path) -> Path:
    benchmark_dir = repo_root / "output" / "larger_real_pdf_benchmark_plan_342a"
    _write_json(
        benchmark_dir / "larger_real_pdf_benchmark_plan_342a_summary.json",
        {
            "current_pdf_count": 31,
            "benchmark_status": "READY_FOR_SMALL_SCALE_BENCHMARK",
            "qa_fail_count": 0,
            "decision": BENCHMARK_PLAN_READY_DECISION,
        },
    )
    return benchmark_dir


def test_build_real_pdf_corpus_intake_342b_ready_and_deduped(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    input_dir = repo_root / "input"
    _write_pdf(input_dir / "real_test" / "sample_a.pdf")
    _write_pdf(input_dir / "real_test" / "sample_b.pdf")
    _write_pdf(input_dir / "real_test" / "sample_c.pdf")
    _write_pdf(input_dir / "real_test" / "sample_d.pdf")
    _write_pdf(input_dir / "real_test" / "sample_e.pdf")
    _write_pdf(input_dir / "stage7a_regression_pdfs" / "sample_f.pdf")
    _write_pdf(input_dir / "stage7a_regression_pdfs" / "sample_g.pdf")
    _write_pdf(input_dir / "stage7a_regression_pdfs" / "sample_h.pdf")
    _write_pdf(input_dir / "unfamiliar" / "peer_industry_sample_i.pdf")
    _write_pdf(input_dir / "unfamiliar" / "sample_j.pdf")
    _write_pdf(input_dir / "unfamiliar" / "sample_k.pdf")
    _write_pdf(input_dir / "input_root_copy.pdf", content=MINIMAL_PDF + b"root\n")
    # duplicate of sample_a
    _write_pdf(input_dir / "duplicates" / "sample_a_dup.pdf")

    benchmark_dir = _seed_342a_summary(repo_root)

    artifacts = build_real_pdf_corpus_intake_342b(
        input_dir=input_dir,
        benchmark_plan_342a_dir=benchmark_dir,
        output_dir=repo_root / "output" / "real_pdf_corpus_intake_342b",
        repo_root=repo_root,
        future_input_dir=input_dir / "real_pdf_benchmark_342a",
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    split_df = artifacts["workbook_sheets"]["05_SPLIT_PLAN"]
    dedup_df = artifacts["workbook_sheets"]["03_DEDUP_AUDIT"]
    assert summary["current_pdf_count"] == 13
    assert summary["unique_pdf_count"] == 2
    assert summary["duplicate_pdf_count"] == 11
    assert summary["assigned_tier_count"] >= 1
    assert summary["ready_for_342c"] is False
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_DECISION
    assert set(artifacts["workbook_sheets"].keys()) == set(WORKBOOK_SHEETS)
    assert not dedup_df.empty
    assert set(split_df["split"].tolist()) <= {PILOT_SPLIT, BENCHMARK_SPLIT, HOLDOUT_SPLIT}


def test_build_real_pdf_corpus_intake_342b_ready_for_342c_with_unique_pdfs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    input_dir = repo_root / "input"
    for idx in range(1, 13):
        _write_pdf(input_dir / "real_test" / f"sample_{idx:02d}.pdf", content=MINIMAL_PDF + f"{idx}".encode("utf-8"))
    benchmark_dir = _seed_342a_summary(repo_root)

    artifacts = build_real_pdf_corpus_intake_342b(
        input_dir=input_dir,
        benchmark_plan_342a_dir=benchmark_dir,
        output_dir=repo_root / "output" / "real_pdf_corpus_intake_342b",
        repo_root=repo_root,
        future_input_dir=input_dir / "real_pdf_benchmark_342a",
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    assert summary["current_pdf_count"] == 12
    assert summary["unique_pdf_count"] == 12
    assert summary["duplicate_pdf_count"] == 0
    assert summary["pilot_set_count"] == 5
    assert summary["benchmark_set_count"] == 7
    assert summary["holdout_set_count"] == 0
    assert summary["ready_for_342c"] is True
    assert summary["recommended_first_run_pdf_count"] == 5
    assert summary["qa_fail_count"] == 0


def test_build_real_pdf_corpus_intake_342b_zero_byte_blocks_readiness(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    input_dir = repo_root / "input"
    for idx in range(1, 11):
        _write_pdf(input_dir / "real_test" / f"sample_{idx:02d}.pdf", content=MINIMAL_PDF + f"{idx}".encode("utf-8"))
    zero_byte_path = input_dir / "unfamiliar" / "broken.pdf"
    zero_byte_path.parent.mkdir(parents=True, exist_ok=True)
    zero_byte_path.write_bytes(b"")
    benchmark_dir = _seed_342a_summary(repo_root)

    artifacts = build_real_pdf_corpus_intake_342b(
        input_dir=input_dir,
        benchmark_plan_342a_dir=benchmark_dir,
        output_dir=repo_root / "output" / "real_pdf_corpus_intake_342b",
        repo_root=repo_root,
        future_input_dir=input_dir / "real_pdf_benchmark_342a",
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    assert summary["current_pdf_count"] == 11
    assert summary["zero_byte_file_count"] == 1
    assert summary["ready_for_342c"] is False
    assert summary["qa_fail_count"] == 0
