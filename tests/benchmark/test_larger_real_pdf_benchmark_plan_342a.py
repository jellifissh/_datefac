from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.larger_real_pdf_benchmark_plan_342a import (  # noqa: E402
    BENCHMARK_STATUS_NEEDS_MORE,
    BENCHMARK_STATUS_READY_SMALL_SCALE,
    READY_DECISION,
    WORKBOOK_SHEETS,
    build_larger_real_pdf_benchmark_plan_342a,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _seed_pdfs(root: Path, count: int, subdir: str = "real_test") -> None:
    target_dir = root / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(1, count + 1):
        (target_dir / f"sample_{idx:03d}.pdf").write_bytes(b"%PDF-1.4\n342A\n")


def _seed_upstream(repo_root: Path, *, include_summaries: bool = True) -> tuple[Path, Path, Path]:
    dir_341a = repo_root / "output" / "human_reviewed_client_preview_milestone_341a"
    dir_340g = repo_root / "output" / "client_preview_export_audit_340g"
    dir_340f = repo_root / "output" / "client_preview_after_human_review_340f"
    if include_summaries:
        _write_json(
            dir_341a / "human_reviewed_client_preview_milestone_341a_summary.json",
            {
                "demo_ready": True,
                "client_preview_ready": True,
                "client_ready": False,
                "production_ready": False,
                "qa_fail_count": 0,
                "decision": "HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_READY",
            },
        )
        _write_json(
            dir_340g / "client_preview_export_audit_340g_summary.json",
            {
                "audited_core_metric_count": 34,
                "duplicate_issue_count": 0,
                "unit_issue_count": 0,
                "missing_source_trace_count": 0,
                "unsafe_claim_count": 0,
                "client_preview_audit_passed": True,
                "qa_fail_count": 0,
                "decision": "CLIENT_PREVIEW_EXPORT_AUDIT_340G_READY",
            },
        )
        _write_json(
            dir_340f / "client_preview_after_human_review_340f_summary.json",
            {
                "client_preview_core_metric_count": 34,
                "client_preview_ready": True,
                "client_ready": False,
                "production_ready": False,
                "qa_fail_count": 0,
                "decision": "CLIENT_PREVIEW_AFTER_HUMAN_REVIEW_340F_READY",
            },
        )
    else:
        dir_341a.mkdir(parents=True, exist_ok=True)
        dir_340g.mkdir(parents=True, exist_ok=True)
        dir_340f.mkdir(parents=True, exist_ok=True)
    return dir_341a, dir_340g, dir_340f


def test_build_larger_real_pdf_benchmark_plan_ready_small_scale(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    input_dir = repo_root / "input"
    future_dir = input_dir / "real_pdf_benchmark_342a"
    _seed_pdfs(input_dir, 8, subdir="real_test")
    _seed_pdfs(input_dir, 4, subdir="unfamiliar")
    _seed_pdfs(future_dir, 2, subdir="tier_d")
    dir_341a, dir_340g, dir_340f = _seed_upstream(repo_root, include_summaries=True)

    artifacts = build_larger_real_pdf_benchmark_plan_342a(
        input_dir=input_dir,
        milestone_341a_dir=dir_341a,
        client_preview_audit_340g_dir=dir_340g,
        client_preview_340f_dir=dir_340f,
        output_dir=repo_root / "output" / "larger_real_pdf_benchmark_plan_342a",
        future_benchmark_dir=future_dir,
        repo_root=repo_root,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    assert summary["current_pdf_count"] == 14
    assert summary["benchmark_status"] == BENCHMARK_STATUS_READY_SMALL_SCALE
    assert summary["target_pdf_count_min"] == 10
    assert summary["target_pdf_count_recommended"] == 30
    assert summary["target_pdf_count_stretch"] == 50
    assert summary["detected_341a_decision"] == "HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_READY"
    assert summary["detected_340g_audit_passed"] is True
    assert summary["detected_340f_client_preview_core_metric_count"] == 34
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_DECISION
    assert set(artifacts["workbook_sheets"].keys()) == set(WORKBOOK_SHEETS)
    assert len(artifacts["workbook_sheets"]["03_SAMPLE_TIERS"]) == 6
    assert len(artifacts["workbook_sheets"]["04_TARGET_METRICS"]) == 10
    assert len(artifacts["workbook_sheets"]["05_RUN_PLAN"]) == 7


def test_build_larger_real_pdf_benchmark_plan_needs_more_pdfs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    input_dir = repo_root / "input"
    future_dir = input_dir / "real_pdf_benchmark_342a"
    _seed_pdfs(input_dir, 3, subdir="real_test")
    dir_341a, dir_340g, dir_340f = _seed_upstream(repo_root, include_summaries=True)

    artifacts = build_larger_real_pdf_benchmark_plan_342a(
        input_dir=input_dir,
        milestone_341a_dir=dir_341a,
        client_preview_audit_340g_dir=dir_340g,
        client_preview_340f_dir=dir_340f,
        output_dir=repo_root / "output" / "larger_real_pdf_benchmark_plan_342a",
        future_benchmark_dir=future_dir,
        repo_root=repo_root,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    assert summary["current_pdf_count"] == 3
    assert summary["benchmark_status"] == BENCHMARK_STATUS_NEEDS_MORE
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_DECISION


def test_missing_optional_summaries_warn_without_fail(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    input_dir = repo_root / "input"
    future_dir = input_dir / "real_pdf_benchmark_342a"
    _seed_pdfs(input_dir, 12, subdir="real_test")
    dir_341a, dir_340g, dir_340f = _seed_upstream(repo_root, include_summaries=False)

    artifacts = build_larger_real_pdf_benchmark_plan_342a(
        input_dir=input_dir,
        milestone_341a_dir=dir_341a,
        client_preview_audit_340g_dir=dir_340g,
        client_preview_340f_dir=dir_340f,
        output_dir=repo_root / "output" / "larger_real_pdf_benchmark_plan_342a",
        future_benchmark_dir=future_dir,
        repo_root=repo_root,
        alias_asset_path=repo_root / "data" / "overrides" / "semantic_alias_candidates.json",
        scope_asset_path=repo_root / "data" / "mapping" / "formal_scope_rules.json",
    )

    summary = artifacts["summary"]
    qa_json = artifacts["qa_json"]
    assert summary["benchmark_status"] == BENCHMARK_STATUS_READY_SMALL_SCALE
    assert summary["warning_count"] == 3
    assert summary["qa_fail_count"] == 0
    assert qa_json["warning_count"] == 3
    assert len(qa_json["warnings"]) == 3
