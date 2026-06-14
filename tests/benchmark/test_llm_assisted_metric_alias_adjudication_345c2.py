from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.llm_assisted_metric_alias_adjudication_345c2 import (  # noqa: E402
    FIXTURE_DECISION,
    REQUEST_ONLY_DECISION,
    READY_DECISION,
    build_llm_assisted_metric_alias_adjudication_345c2,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_llm_assisted_metric_alias_adjudication_345c2"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345c_outputs(root: Path) -> Path:
    dir_345c = root / "output" / "metric_candidate_normalization_coverage_345c"
    dir_345c.mkdir(parents=True, exist_ok=True)

    manifest = {
        "decision": "METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "alias_candidate_count": 4,
        "high_priority_alias_candidate_count": 3,
    }
    alias_queue = [
        {
            "raw_metric_name": "鍒╂鼎鎬婚",
            "frequency": 10,
            "source_stages": "LONG_FORM_CELL|REVIEW_REQUIRED",
            "pdf_names": "alpha.pdf|beta.pdf",
            "sample_row_ids": "345c::metric::00001|345c::metric::00002",
            "quality_severity_distribution": "MEDIUM:7, HIGH:3",
            "suggested_priority": "HIGH",
        },
        {
            "raw_metric_name": "璧勬湰寮€鏀?",
            "frequency": 8,
            "source_stages": "LONG_FORM_CELL|REVIEW_REQUIRED",
            "pdf_names": "alpha.pdf",
            "sample_row_ids": "345c::metric::00003",
            "quality_severity_distribution": "MEDIUM:8",
            "suggested_priority": "HIGH",
        },
        {
            "raw_metric_name": "BROKEN_JSON_METRIC",
            "frequency": 6,
            "source_stages": "LONG_FORM_CELL",
            "pdf_names": "gamma.pdf",
            "sample_row_ids": "345c::metric::00004",
            "quality_severity_distribution": "LOW:6",
            "suggested_priority": "HIGH",
        },
        {
            "raw_metric_name": "EV/EBITDA",
            "frequency": 12,
            "source_stages": "REJECTED_OR_EXCLUDED",
            "pdf_names": "delta.pdf",
            "sample_row_ids": "345c::metric::00005",
            "quality_severity_distribution": "HIGH:12",
            "suggested_priority": "LOW",
        },
    ]
    raw_metric_summary = [
        {
            "raw_metric_name": row["raw_metric_name"],
            "row_count": row["frequency"],
            "normalized_metric_row_count": 0,
            "unnormalized_metric_row_count": row["frequency"],
            "normalization_coverage_ratio": 0.0,
            "source_stages": row["source_stages"],
            "pdf_names": row["pdf_names"],
            "top_normalization_statuses": "UNNORMALIZED_WITH_RAW_NAME",
            "suggested_alias_priority": row["suggested_priority"],
        }
        for row in alias_queue
    ]
    metric_rows = [
        {
            "metric_coverage_row_id": "345c::metric::00001",
            "pdf_name": "alpha.pdf",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "quality_severity": "MEDIUM",
            "quality_issues": "UNNORMALIZED_METRIC",
            "review_status": "REVIEW_REQUIRED",
            "trust_status": "REVIEW_REQUIRED",
        },
        {
            "metric_coverage_row_id": "345c::metric::00002",
            "pdf_name": "beta.pdf",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "quality_severity": "HIGH",
            "quality_issues": "UNNORMALIZED_METRIC",
            "review_status": "REVIEW_REQUIRED",
            "trust_status": "REVIEW_REQUIRED",
        },
        {
            "metric_coverage_row_id": "345c::metric::00003",
            "pdf_name": "alpha.pdf",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "quality_severity": "MEDIUM",
            "quality_issues": "UNNORMALIZED_METRIC",
            "review_status": "REVIEW_REQUIRED",
            "trust_status": "REVIEW_REQUIRED",
        },
        {
            "metric_coverage_row_id": "345c::metric::00004",
            "pdf_name": "gamma.pdf",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "quality_severity": "LOW",
            "quality_issues": "UNNORMALIZED_METRIC",
            "review_status": "REVIEW_REQUIRED",
            "trust_status": "REVIEW_REQUIRED",
        },
        {
            "metric_coverage_row_id": "345c::metric::00005",
            "pdf_name": "delta.pdf",
            "source_stage": "REJECTED_OR_EXCLUDED",
            "source_artifact": "342F::06_REJECTED",
            "quality_severity": "HIGH",
            "quality_issues": "REJECTED",
            "review_status": "REJECTED_OR_EXCLUDED",
            "trust_status": "REJECTED",
        },
    ]

    _write_json(dir_345c / "metric_candidate_normalization_coverage_345c_manifest.json", manifest)
    _write_json(dir_345c / "metric_candidate_normalization_coverage_345c_alias_candidate_queue.json", alias_queue)
    _write_json(dir_345c / "metric_candidate_normalization_coverage_345c_raw_metric_summary.json", raw_metric_summary)
    _write_json(dir_345c / "metric_candidate_normalization_coverage_345c_metric_rows.json", metric_rows)
    return dir_345c


def test_request_only_mode_works_without_api_keys() -> None:
    case_root = _make_case_root()
    try:
        dir_345c = _seed_345c_outputs(case_root)
        artifacts = build_llm_assisted_metric_alias_adjudication_345c2(
            metric_candidate_normalization_coverage_345c_dir=dir_345c,
            output_dir=case_root / "output" / "llm_assisted_metric_alias_adjudication_345c2",
            llm_mode="request_only",
            max_alias_candidates=2,
            include_medium_priority=False,
            timeout_seconds=5,
            repo_root=case_root,
            env={},
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == REQUEST_ONLY_DECISION
        assert manifest["qa_fail_count"] == 0
        assert manifest["runtime_config_available"] is False
        assert manifest["request_package_generated"] is True
        assert manifest["suggestion_row_count"] == 0
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        assert len(artifacts["alias_request_package_rows"]) == 2
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_fixture_mode_produces_deterministic_suggestions_and_review_rows() -> None:
    case_root = _make_case_root()
    try:
        dir_345c = _seed_345c_outputs(case_root)
        artifacts = build_llm_assisted_metric_alias_adjudication_345c2(
            metric_candidate_normalization_coverage_345c_dir=dir_345c,
            output_dir=case_root / "output" / "llm_assisted_metric_alias_adjudication_345c2",
            llm_mode="fixture",
            max_alias_candidates=3,
            include_medium_priority=False,
            timeout_seconds=5,
            repo_root=case_root,
            env={},
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == FIXTURE_DECISION
        assert manifest["qa_fail_count"] == 0
        assert manifest["selected_alias_candidate_count"] == 3
        assert manifest["suggestion_row_count"] == 3
        assert manifest["propose_new_standard_count"] == 1
        assert manifest["parse_failed_count"] == 1
        assert manifest["validation_failed_count"] == 1
        assert manifest["high_confidence_suggestion_count"] == 0
        assert manifest["needs_human_review_count"] == 3
        assert len(artifacts["review_required_rows"]) == 3
        broken = [
            row
            for row in artifacts["alias_suggestion_rows"]
            if row["raw_metric_name"] == "BROKEN_JSON_METRIC"
        ][0]
        assert broken["response_parse_status"] == "PARSE_FAILED"
        assert broken["needs_human_review"] is True
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_live_mode_fails_clearly_when_config_missing() -> None:
    case_root = _make_case_root()
    try:
        dir_345c = _seed_345c_outputs(case_root)
        try:
            build_llm_assisted_metric_alias_adjudication_345c2(
                metric_candidate_normalization_coverage_345c_dir=dir_345c,
                output_dir=case_root / "output" / "llm_assisted_metric_alias_adjudication_345c2",
                llm_mode="live",
                max_alias_candidates=2,
                include_medium_priority=False,
                timeout_seconds=5,
                repo_root=case_root,
                env={},
            )
        except RuntimeError as exc:
            assert "requires runtime config" in str(exc)
        else:
            raise AssertionError("Expected live mode to fail clearly without config.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_missing_required_345c_inputs_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing_345c"
        missing_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_llm_assisted_metric_alias_adjudication_345c2(
                metric_candidate_normalization_coverage_345c_dir=missing_dir,
                output_dir=case_root / "output" / "llm_assisted_metric_alias_adjudication_345c2",
                llm_mode="request_only",
                max_alias_candidates=2,
                include_medium_priority=False,
                timeout_seconds=5,
                repo_root=case_root,
                env={},
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345C inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
