from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.remaining_blind_spot_alias_candidate_package_345c8 import (  # noqa: E402
    READY_DECISION_345C8,
    build_remaining_blind_spot_alias_candidate_package_345c8,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_remaining_blind_spot_alias_candidate_package_345c8"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345c6_outputs(root: Path) -> Path:
    dir_345c6 = root / "output" / "reviewed_alias_apply_simulation_345c6"
    dir_345c6.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "remaining_unnormalized_raw_metric_name_count": 5,
        "remaining_unnormalized_metric_row_count": 64,
    }
    remaining_blind_spots = [
        {
            "raw_metric_name": "财务费用",
            "remaining_row_count": 25,
            "remaining_ready_candidate_count": 2,
            "source_stages": "LONG_FORM_CELL|REVIEW_REQUIRED",
            "pdf_names": "a.pdf|b.pdf",
            "quality_severity_distribution": "HIGH:10, MEDIUM:15",
            "sample_row_ids": "id1|id2",
        },
        {
            "raw_metric_name": "EBITDA",
            "remaining_row_count": 18,
            "remaining_ready_candidate_count": 1,
            "source_stages": "LONG_FORM_CELL",
            "pdf_names": "c.pdf",
            "quality_severity_distribution": "MEDIUM:18",
            "sample_row_ids": "id3|id4",
        },
        {
            "raw_metric_name": "变化",
            "remaining_row_count": 12,
            "remaining_ready_candidate_count": 0,
            "source_stages": "REVIEW_REQUIRED",
            "pdf_names": "d.pdf",
            "quality_severity_distribution": "HIGH:12",
            "sample_row_ids": "id5",
        },
        {
            "raw_metric_name": "YoY(%)",
            "remaining_row_count": 6,
            "remaining_ready_candidate_count": 0,
            "source_stages": "LONG_FORM_CELL",
            "pdf_names": "e.pdf",
            "quality_severity_distribution": "MEDIUM:6",
            "sample_row_ids": "id6",
        },
        {
            "raw_metric_name": "现金流",
            "remaining_row_count": 3,
            "remaining_ready_candidate_count": 0,
            "source_stages": "LONG_FORM_CELL",
            "pdf_names": "f.pdf",
            "quality_severity_distribution": "LOW:3",
            "sample_row_ids": "id7",
        },
    ]
    simulated_metric_rows = [
        {
            "raw_metric_name": "财务费用",
            "normalization_status_after_simulation": "UNNORMALIZED_WITH_RAW_NAME",
            "source_artifact": "artifact_a",
            "pdf_name": "a.pdf",
            "source_stage": "REVIEW_REQUIRED",
            "quality_severity": "HIGH",
            "quality_issues": "context missing",
            "downstream_ready_after_alias_simulation": True,
        },
        {
            "raw_metric_name": "EBITDA",
            "normalization_status_after_simulation": "UNNORMALIZED_WITH_RAW_NAME",
            "source_artifact": "artifact_b",
            "pdf_name": "c.pdf",
            "source_stage": "LONG_FORM_CELL",
            "quality_severity": "MEDIUM",
            "quality_issues": "",
            "downstream_ready_after_alias_simulation": False,
        },
    ]
    coverage_before_after = {
        "metric_candidate_row_count_before": 100,
        "remaining_unnormalized_raw_metric_name_count": 5,
        "remaining_unnormalized_metric_row_count": 64,
    }
    _write_json(dir_345c6 / "reviewed_alias_apply_simulation_345c6_manifest.json", manifest)
    _write_json(
        dir_345c6 / "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.json",
        remaining_blind_spots,
    )
    _write_json(
        dir_345c6 / "reviewed_alias_apply_simulation_345c6_non_applied_aliases.json",
        [],
    )
    _write_json(
        dir_345c6 / "reviewed_alias_apply_simulation_345c6_coverage_before_after.json",
        coverage_before_after,
    )
    _write_json(
        dir_345c6 / "reviewed_alias_apply_simulation_345c6_simulated_metric_rows.json",
        simulated_metric_rows,
    )
    (dir_345c6 / "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c6 / "reviewed_alias_apply_simulation_345c6_non_applied_aliases.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c6 / "reviewed_alias_apply_simulation_345c6_coverage_before_after.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    return dir_345c6


def _seed_345c7_outputs(root: Path) -> Path:
    dir_345c7 = root / "output" / "official_alias_rule_update_candidate_package_345c7"
    dir_345c7.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "OFFICIAL_ALIAS_RULE_UPDATE_CANDIDATE_PACKAGE_345C7_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
    }
    _write_json(dir_345c7 / "official_alias_rule_update_candidate_package_345c7_manifest.json", manifest)
    _write_json(
        dir_345c7
        / "official_alias_rule_update_candidate_package_345c7_remaining_blind_spot_summary.json",
        [
            {
                "raw_metric_name": "财务费用",
                "remaining_row_count": 25,
                "remaining_ready_candidate_count": 2,
                "source_stages": "LONG_FORM_CELL|REVIEW_REQUIRED",
                "pdf_names": "a.pdf|b.pdf",
                "quality_severity_distribution": "HIGH:10, MEDIUM:15",
                "sample_row_ids": "id1|id2",
            },
            {
                "raw_metric_name": "EBITDA",
                "remaining_row_count": 18,
                "remaining_ready_candidate_count": 1,
                "source_stages": "LONG_FORM_CELL",
                "pdf_names": "c.pdf",
                "quality_severity_distribution": "MEDIUM:18",
                "sample_row_ids": "id3|id4",
            },
        ],
    )
    _write_json(
        dir_345c7 / "official_alias_rule_update_candidate_package_345c7_risk_review.json",
        [
            {
                "raw_metric_name": "利润总额",
                "rule_update_risk_level": "MEDIUM",
                "rule_update_recommendation": "READY_FOR_DEMO_ONLY_SIDECAR_USE",
            }
        ],
    )
    (dir_345c7 / "official_alias_rule_update_candidate_package_345c7_executive_summary.md").write_text(
        "existing summary", encoding="utf-8"
    )
    (dir_345c7 / "official_alias_rule_update_candidate_package_345c7_remaining_blind_spot_summary.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c7 / "official_alias_rule_update_candidate_package_345c7_risk_review.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    return dir_345c7


def test_345c8_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_345c6 = _seed_345c6_outputs(case_root)
        dir_345c7 = _seed_345c7_outputs(case_root)
        artifacts = build_remaining_blind_spot_alias_candidate_package_345c8(
            reviewed_alias_apply_simulation_345c6_dir=dir_345c6,
            official_alias_rule_update_candidate_package_345c7_dir=dir_345c7,
            output_dir=case_root / "output" / "remaining_blind_spot_alias_candidate_package_345c8",
            max_blind_spot_candidates=3,
            min_row_impact=10,
            repo_root=case_root,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345C8
        assert manifest["qa_fail_count"] == 0
        assert manifest["selected_candidate_count"] <= 3
        assert manifest["remaining_unnormalized_raw_metric_name_count"] == 5
        assert manifest["remaining_unnormalized_metric_row_count"] == 64
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        assert manifest["candidate_package_only"] is True
        selected = artifacts["selected_candidates"]
        assert len(selected) == 2
        assert {row["raw_metric_name"] for row in selected} == {"财务费用", "EBITDA"}
        assert all(row["candidate_package_only"] is True for row in selected)
        assert all(row["official_rules_modified"] is False for row in selected)
        assert all(row["review_recommendation"] != "EXCLUDE_TOO_GENERIC" for row in selected)
        assert artifacts["stop_or_continue_decision"]["alias_branch_stop_or_continue_decision"] in {
            "CONTINUE_WITH_SECOND_REVIEW_BATCH",
            "CONTINUE_ONLY_IF_HUMAN_REVIEW_CAPACITY_EXISTS",
            "STOP_ALIAS_BRANCH_AND_RETURN_TO_345D",
        }
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c8_missing_required_inputs_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing"
        missing_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_remaining_blind_spot_alias_candidate_package_345c8(
                reviewed_alias_apply_simulation_345c6_dir=missing_dir,
                official_alias_rule_update_candidate_package_345c7_dir=missing_dir,
                output_dir=case_root / "output" / "remaining_blind_spot_alias_candidate_package_345c8",
                max_blind_spot_candidates=30,
                min_row_impact=10,
                repo_root=case_root,
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345C6/345C7 inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
