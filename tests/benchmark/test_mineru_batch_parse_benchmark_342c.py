from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.mineru_batch_parse_benchmark_342c import (  # noqa: E402
    DEFAULT_MINERU_EXE,
    PILOT_SPLIT,
    READY_DECISION,
    READY_WITH_FAILURES_DECISION,
    WORKBOOK_SHEETS,
    build_mineru_batch_parse_benchmark_342c,
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
                "split": PILOT_SPLIT,
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
    _write_json(
        output_dir / "real_pdf_corpus_intake_342b_manifest.json",
        {
            "task": "342B_real_pdf_corpus_intake_metadata_audit",
        },
    )
    return output_dir


def test_build_mineru_batch_parse_benchmark_342c_dry_run(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b_workbook(repo_root)

    artifacts = build_mineru_batch_parse_benchmark_342c(
        corpus_342b_dir=corpus_dir,
        output_dir=repo_root / "output" / "mineru_batch_parse_benchmark_342c",
        repo_root=repo_root,
        dry_run=True,
        limit=5,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    parse_results_df = artifacts["workbook_sheets"]["02_PDF_PARSE_RESULTS"]
    assert summary["pilot_total_count"] == 5
    assert summary["mineru_success_count"] == 0
    assert summary["mineru_failed_count"] == 0
    assert summary["ready_for_342d"] == "conditional"
    assert summary["decision"] == READY_WITH_FAILURES_DECISION
    assert set(parse_results_df["parse_status"].tolist()) == {"SKIPPED_DRY_RUN"}
    assert set(artifacts["workbook_sheets"].keys()) == set(WORKBOOK_SHEETS)


def test_build_mineru_batch_parse_benchmark_342c_real_run_with_custom_template(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = _seed_342b_workbook(repo_root)
    output_dir = repo_root / "output" / "mineru_batch_parse_benchmark_342c"
    script_path = repo_root / "fake_mineru.py"
    script_path.write_text(
        "from pathlib import Path\n"
        "import json\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        "pdf = Path(args[args.index('-p') + 1])\n"
        "out = Path(args[args.index('-o') + 1]) / pdf.stem / 'auto'\n"
        "out.mkdir(parents=True, exist_ok=True)\n"
        "payload = {'pages': [{'page_idx': 0, 'blocks': [{'type': 'text', 'text': 'x' * 300}]}]}\n"
        "(out / f'{pdf.stem}_content_list.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')\n"
        "(out / f'{pdf.stem}.md').write_text('# test\\n' + ('markdown content\\n' * 200), encoding='utf-8')\n"
        "print('ok')\n",
        encoding="utf-8",
    )
    command_template = f'python "{script_path}" -p "{{pdf_path}}" -o "{{mineru_output_root}}"'

    artifacts = build_mineru_batch_parse_benchmark_342c(
        corpus_342b_dir=corpus_dir,
        output_dir=output_dir,
        repo_root=repo_root,
        mineru_command=command_template,
        dry_run=False,
        limit=5,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    parse_results_df = artifacts["workbook_sheets"]["02_PDF_PARSE_RESULTS"]
    assert summary["pilot_total_count"] == 5
    assert summary["mineru_success_count"] == 5
    assert summary["mineru_failed_count"] == 0
    assert summary["empty_output_count"] == 0
    assert summary["ready_for_342d"] == "true"
    assert summary["decision"] == READY_DECISION
    assert set(parse_results_df["parse_status"].tolist()) == {"SUCCESS"}
    assert parse_results_df["json_file_count"].sum() >= 5
    assert parse_results_df["markdown_file_count"].sum() >= 5


def test_build_mineru_batch_parse_benchmark_342c_missing_pilot_fails_qa(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    corpus_dir = repo_root / "output" / "real_pdf_corpus_intake_342b"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(corpus_dir / "real_pdf_corpus_intake_342b.xlsx", engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "Purpose", "message": "test"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"decision": "REAL_PDF_CORPUS_INTAKE_342B_READY"}]).to_excel(writer, sheet_name="01_CORPUS_SUMMARY", index=False)
        pd.DataFrame(columns=["corpus_pdf_id", "file_name", "file_path", "sha256", "page_count"]).to_excel(writer, sheet_name="02_PDF_CORPUS", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="03_DEDUP_AUDIT", index=False)
        pd.DataFrame(columns=["corpus_pdf_id", "assigned_tier"]).to_excel(writer, sheet_name="04_TIER_ASSIGNMENT", index=False)
        pd.DataFrame(columns=["corpus_pdf_id", "split"]).to_excel(writer, sheet_name="05_SPLIT_PLAN", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="06_METADATA_AUDIT", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="07_RUN_READINESS", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="08_RISK_FLAGS", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="09_NO_WRITE_BACK_PROOF", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="10_NEXT_STEPS", index=False)
    _write_json(corpus_dir / "real_pdf_corpus_intake_342b_summary.json", {"decision": "REAL_PDF_CORPUS_INTAKE_342B_READY"})
    _write_json(corpus_dir / "real_pdf_corpus_intake_342b_manifest.json", {"task": "342B"})

    artifacts = build_mineru_batch_parse_benchmark_342c(
        corpus_342b_dir=corpus_dir,
        output_dir=repo_root / "output" / "mineru_batch_parse_benchmark_342c",
        repo_root=repo_root,
        dry_run=True,
        limit=5,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    assert summary["pilot_total_count"] == 0
    assert summary["qa_fail_count"] >= 1
    assert summary["decision"].endswith("NOT_READY")
