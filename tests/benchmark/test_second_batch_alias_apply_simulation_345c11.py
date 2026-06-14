from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.second_batch_alias_apply_simulation_345c11 import (  # noqa: E402
    READY_DECISION_345C11,
    build_second_batch_alias_apply_simulation_345c11,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_second_batch_alias_apply_simulation_345c11"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345c_outputs(root: Path) -> Path:
    dir_345c = root / "output" / "metric_candidate_normalization_coverage_345c"
    dir_345c.mkdir(parents=True, exist_ok=True)
    metric_rows = [
        {
            "metric_coverage_row_id": "345c::metric::00001",
            "inventory_row_id": "inv::001",
            "quality_row_id": "qual::001",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "raw_metric_name": "Alias A",
            "normalized_metric_name": "",
            "quality_severity": "LOW",
            "quality_issues": "",
            "downstream_ready_before_normalization": True,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
        },
        {
            "metric_coverage_row_id": "345c::metric::00002",
            "inventory_row_id": "inv::002",
            "quality_row_id": "qual::002",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "raw_metric_name": "Alias A",
            "normalized_metric_name": "",
            "quality_severity": "MEDIUM",
            "quality_issues": "",
            "downstream_ready_before_normalization": False,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
        },
        {
            "metric_coverage_row_id": "345c::metric::00003",
            "inventory_row_id": "inv::003",
            "quality_row_id": "qual::003",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_002",
            "pdf_name": "demo_b.pdf",
            "raw_metric_name": "Alias B",
            "normalized_metric_name": "",
            "quality_severity": "LOW",
            "quality_issues": "",
            "downstream_ready_before_normalization": True,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
        },
        {
            "metric_coverage_row_id": "345c::metric::00004",
            "inventory_row_id": "inv::004",
            "quality_row_id": "qual::004",
            "source_stage": "TRUSTED_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_003",
            "pdf_name": "demo_c.pdf",
            "raw_metric_name": "Alias C",
            "normalized_metric_name": "",
            "quality_severity": "LOW",
            "quality_issues": "",
            "downstream_ready_before_normalization": True,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
        },
        {
            "metric_coverage_row_id": "345c::metric::00005",
            "inventory_row_id": "inv::005",
            "quality_row_id": "qual::005",
            "source_stage": "TRUSTED_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_004",
            "pdf_name": "demo_d.pdf",
            "raw_metric_name": "Existing Metric",
            "normalized_metric_name": "revenue",
            "quality_severity": "LOW",
            "quality_issues": "",
            "downstream_ready_before_normalization": True,
            "normalization_status": "NORMALIZED",
        },
        {
            "metric_coverage_row_id": "345c::metric::00006",
            "inventory_row_id": "inv::006",
            "quality_row_id": "qual::006",
            "source_stage": "REVIEW_REQUIRED",
            "source_artifact": "345a",
            "pdf_id": "pdf_005",
            "pdf_name": "demo_e.pdf",
            "raw_metric_name": "Alias D",
            "normalized_metric_name": "",
            "quality_severity": "HIGH",
            "quality_issues": "needs review",
            "downstream_ready_before_normalization": False,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
        },
    ]
    manifest = {
        "decision": "METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "metric_candidate_row_count": 6,
    }
    _write_json(dir_345c / "metric_candidate_normalization_coverage_345c_manifest.json", manifest)
    _write_json(dir_345c / "metric_candidate_normalization_coverage_345c_metric_rows.json", metric_rows)
    _write_json(
        dir_345c / "metric_candidate_normalization_coverage_345c_alias_candidate_queue.json",
        [{"raw_metric_name": "Alias A", "frequency": 2}],
    )
    (dir_345c / "metric_candidate_normalization_coverage_345c_metric_rows.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c / "metric_candidate_normalization_coverage_345c_alias_candidate_queue.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    return dir_345c


def _seed_345c6_outputs(root: Path) -> Path:
    dir_345c6 = root / "output" / "reviewed_alias_apply_simulation_345c6"
    dir_345c6.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY",
        "qa_fail_count": 0,
        "applied_alias_key_count": 1,
        "simulated_newly_normalized_row_count": 2,
        "ready_candidate_count_after_alias_simulation": 2,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
    }
    applied_alias_map = [
        {
            "approved_alias_key": "Alias A",
            "raw_metric_name": "Alias A",
            "canonical_alias_target": "metric_a",
            "source_decision": "APPROVE_NEW_STANDARD",
            "review_priority": "HIGH",
            "source_stages": "LONG_FORM_CELL",
            "applied_row_count": 2,
            "newly_normalized_row_count": 2,
            "already_normalized_match_count": 0,
            "matching_row_count": 2,
            "simulation_rule_update_required": True,
        }
    ]
    simulated_metric_rows = [
        {
            "metric_coverage_row_id": "345c::metric::00001",
            "inventory_row_id": "inv::001",
            "quality_row_id": "qual::001",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "raw_metric_name": "Alias A",
            "normalized_metric_name": "",
            "quality_severity": "LOW",
            "quality_issues": "",
            "downstream_ready_before_normalization": True,
            "normalization_status_before": "UNNORMALIZED_WITH_RAW_NAME",
            "simulated_normalized_metric_name": "metric_a",
            "normalization_status_after_simulation": "NORMALIZED",
            "simulation_applied": True,
            "simulation_action": "SIMULATED_ALIAS_NORMALIZATION",
            "simulation_source": "REVIEWED_ALIAS_345C5",
            "simulation_rule_update_required": True,
            "simulation_only_no_write_back": True,
            "downstream_ready_after_alias_simulation": True,
        },
        {
            "metric_coverage_row_id": "345c::metric::00002",
            "inventory_row_id": "inv::002",
            "quality_row_id": "qual::002",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "raw_metric_name": "Alias A",
            "normalized_metric_name": "",
            "quality_severity": "MEDIUM",
            "quality_issues": "",
            "downstream_ready_before_normalization": False,
            "normalization_status_before": "UNNORMALIZED_WITH_RAW_NAME",
            "simulated_normalized_metric_name": "metric_a",
            "normalization_status_after_simulation": "NORMALIZED",
            "simulation_applied": True,
            "simulation_action": "SIMULATED_ALIAS_NORMALIZATION",
            "simulation_source": "REVIEWED_ALIAS_345C5",
            "simulation_rule_update_required": True,
            "simulation_only_no_write_back": True,
            "downstream_ready_after_alias_simulation": False,
        },
        {
            "metric_coverage_row_id": "345c::metric::00003",
            "inventory_row_id": "inv::003",
            "quality_row_id": "qual::003",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_002",
            "pdf_name": "demo_b.pdf",
            "raw_metric_name": "Alias B",
            "normalized_metric_name": "",
            "quality_severity": "LOW",
            "quality_issues": "",
            "downstream_ready_before_normalization": True,
            "normalization_status_before": "UNNORMALIZED_WITH_RAW_NAME",
            "simulated_normalized_metric_name": "",
            "normalization_status_after_simulation": "UNNORMALIZED_WITH_RAW_NAME",
            "simulation_applied": False,
            "simulation_action": "NO_SIMULATION_APPLIED",
            "simulation_source": "",
            "simulation_rule_update_required": False,
            "simulation_only_no_write_back": True,
            "downstream_ready_after_alias_simulation": False,
        },
        {
            "metric_coverage_row_id": "345c::metric::00004",
            "inventory_row_id": "inv::004",
            "quality_row_id": "qual::004",
            "source_stage": "TRUSTED_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_003",
            "pdf_name": "demo_c.pdf",
            "raw_metric_name": "Alias C",
            "normalized_metric_name": "",
            "quality_severity": "LOW",
            "quality_issues": "",
            "downstream_ready_before_normalization": True,
            "normalization_status_before": "UNNORMALIZED_WITH_RAW_NAME",
            "simulated_normalized_metric_name": "",
            "normalization_status_after_simulation": "UNNORMALIZED_WITH_RAW_NAME",
            "simulation_applied": False,
            "simulation_action": "NO_SIMULATION_APPLIED",
            "simulation_source": "",
            "simulation_rule_update_required": False,
            "simulation_only_no_write_back": True,
            "downstream_ready_after_alias_simulation": False,
        },
        {
            "metric_coverage_row_id": "345c::metric::00005",
            "inventory_row_id": "inv::005",
            "quality_row_id": "qual::005",
            "source_stage": "TRUSTED_CELL",
            "source_artifact": "345a",
            "pdf_id": "pdf_004",
            "pdf_name": "demo_d.pdf",
            "raw_metric_name": "Existing Metric",
            "normalized_metric_name": "revenue",
            "quality_severity": "LOW",
            "quality_issues": "",
            "downstream_ready_before_normalization": True,
            "normalization_status_before": "NORMALIZED",
            "simulated_normalized_metric_name": "revenue",
            "normalization_status_after_simulation": "NORMALIZED",
            "simulation_applied": False,
            "simulation_action": "NO_SIMULATION_APPLIED",
            "simulation_source": "",
            "simulation_rule_update_required": False,
            "simulation_only_no_write_back": True,
            "downstream_ready_after_alias_simulation": True,
        },
        {
            "metric_coverage_row_id": "345c::metric::00006",
            "inventory_row_id": "inv::006",
            "quality_row_id": "qual::006",
            "source_stage": "REVIEW_REQUIRED",
            "source_artifact": "345a",
            "pdf_id": "pdf_005",
            "pdf_name": "demo_e.pdf",
            "raw_metric_name": "Alias D",
            "normalized_metric_name": "",
            "quality_severity": "HIGH",
            "quality_issues": "needs review",
            "downstream_ready_before_normalization": False,
            "normalization_status_before": "UNNORMALIZED_WITH_RAW_NAME",
            "simulated_normalized_metric_name": "",
            "normalization_status_after_simulation": "UNNORMALIZED_WITH_RAW_NAME",
            "simulation_applied": False,
            "simulation_action": "NO_SIMULATION_APPLIED",
            "simulation_source": "",
            "simulation_rule_update_required": False,
            "simulation_only_no_write_back": True,
            "downstream_ready_after_alias_simulation": False,
        },
    ]
    coverage = {
        "normalization_coverage_ratio_before": 0.166667,
        "normalization_coverage_ratio_after_simulation": 0.5,
        "ready_candidate_count_before_simulation": 1,
        "ready_candidate_count_after_alias_simulation": 2,
    }
    remaining_blind_spots = [
        {"raw_metric_name": "Alias B", "remaining_row_count": 1, "remaining_ready_candidate_count": 0},
        {"raw_metric_name": "Alias C", "remaining_row_count": 1, "remaining_ready_candidate_count": 0},
        {"raw_metric_name": "Alias D", "remaining_row_count": 1, "remaining_ready_candidate_count": 0},
    ]
    _write_json(dir_345c6 / "reviewed_alias_apply_simulation_345c6_manifest.json", manifest)
    _write_json(dir_345c6 / "reviewed_alias_apply_simulation_345c6_applied_alias_map.json", applied_alias_map)
    _write_json(dir_345c6 / "reviewed_alias_apply_simulation_345c6_simulated_metric_rows.json", simulated_metric_rows)
    _write_json(dir_345c6 / "reviewed_alias_apply_simulation_345c6_coverage_before_after.json", coverage)
    _write_json(dir_345c6 / "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.json", remaining_blind_spots)
    (dir_345c6 / "reviewed_alias_apply_simulation_345c6_applied_alias_map.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c6 / "reviewed_alias_apply_simulation_345c6_simulated_metric_rows.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c6 / "reviewed_alias_apply_simulation_345c6_coverage_before_after.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c6 / "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    return dir_345c6


def _seed_345c10_outputs(root: Path) -> Path:
    dir_345c10 = root / "output" / "second_batch_reviewed_alias_decision_ingestion_345c10"
    dir_345c10.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_READY",
        "qa_fail_count": 0,
        "apply_simulation_eligible_count": 3,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
    }
    validated_approved = [
        {
            "raw_metric_name": "Alias B",
            "canonical_alias_target": "metric_b",
            "human_blind_spot_review_decision": "APPROVE_NEW_STANDARD",
            "decision_validation_status": "VALID",
            "apply_simulation_eligible": True,
            "candidate_priority": "HIGH",
            "source_stages": "LONG_FORM_CELL",
            "needs_alias_family_expansion": True,
        },
        {
            "raw_metric_name": "Alias C",
            "canonical_alias_target": "metric_c",
            "human_blind_spot_review_decision": "APPROVE_NEW_STANDARD",
            "decision_validation_status": "VALID",
            "apply_simulation_eligible": True,
            "candidate_priority": "HIGH",
            "source_stages": "TRUSTED_CELL",
            "needs_alias_family_expansion": True,
        },
        {
            "raw_metric_name": "Alias A",
            "canonical_alias_target": "metric_a_second_batch",
            "human_blind_spot_review_decision": "APPROVE_NEW_STANDARD",
            "decision_validation_status": "VALID",
            "apply_simulation_eligible": True,
            "candidate_priority": "MEDIUM",
            "source_stages": "LONG_FORM_CELL",
            "needs_alias_family_expansion": False,
        },
    ]
    reviewed_decisions = list(validated_approved)
    rejected_or_blocked = [
        {
            "raw_metric_name": "Alias Z",
            "human_blind_spot_review_decision": "NEEDS_SOURCE_CONTEXT",
        }
    ]
    _write_json(dir_345c10 / "second_batch_reviewed_alias_decision_ingestion_345c10_manifest.json", manifest)
    _write_json(
        dir_345c10 / "second_batch_reviewed_alias_decision_ingestion_345c10_validated_approved_aliases.json",
        validated_approved,
    )
    _write_json(
        dir_345c10 / "second_batch_reviewed_alias_decision_ingestion_345c10_reviewed_decisions.json",
        reviewed_decisions,
    )
    _write_json(
        dir_345c10 / "second_batch_reviewed_alias_decision_ingestion_345c10_rejected_or_blocked_aliases.json",
        rejected_or_blocked,
    )
    (dir_345c10 / "second_batch_reviewed_alias_decision_ingestion_345c10_validated_approved_aliases.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c10 / "second_batch_reviewed_alias_decision_ingestion_345c10_reviewed_decisions.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c10 / "second_batch_reviewed_alias_decision_ingestion_345c10_rejected_or_blocked_aliases.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    return dir_345c10


def test_345c11_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_345c = _seed_345c_outputs(case_root)
        dir_345c6 = _seed_345c6_outputs(case_root)
        dir_345c10 = _seed_345c10_outputs(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_second_batch_alias_apply_simulation_345c11(
            metric_candidate_normalization_coverage_345c_dir=dir_345c,
            reviewed_alias_apply_simulation_345c6_dir=dir_345c6,
            second_batch_reviewed_alias_decision_ingestion_345c10_dir=dir_345c10,
            output_dir=case_root / "output" / "second_batch_alias_apply_simulation_345c11",
            repo_root=case_root,
            ledger_path=ledger_path,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345C11
        assert manifest["qa_fail_count"] == 0
        assert manifest["first_batch_alias_count"] == 1
        assert manifest["first_batch_simulated_newly_normalized_row_count"] == 2
        assert manifest["second_batch_eligible_alias_count"] == 3
        assert manifest["second_batch_applied_alias_key_count"] == 2
        assert manifest["second_batch_simulated_alias_applied_row_count"] == 2
        assert manifest["second_batch_simulated_newly_normalized_row_count"] == 2
        assert manifest["cumulative_applied_alias_key_count"] == 3
        assert manifest["cumulative_simulated_newly_normalized_row_count"] == 4
        assert manifest["coverage_ratio_before"] == 0.166667
        assert manifest["coverage_ratio_after_first_batch"] == 0.5
        assert manifest["coverage_ratio_after_second_batch"] == 0.833333
        assert manifest["coverage_delta_first_batch"] == 0.333333
        assert manifest["coverage_delta_second_batch_incremental"] == 0.333333
        assert manifest["coverage_delta_cumulative"] == 0.666666
        assert manifest["ready_candidate_count_before"] == 1
        assert manifest["ready_candidate_count_after_first_batch"] == 2
        assert manifest["ready_candidate_count_after_second_batch"] == 4
        assert manifest["ready_candidate_delta_first_batch"] == 1
        assert manifest["ready_candidate_delta_second_batch_incremental"] == 2
        assert manifest["ready_candidate_delta_cumulative"] == 3
        assert manifest["remaining_unnormalized_raw_metric_name_count"] == 1
        assert manifest["remaining_unnormalized_metric_row_count"] == 1
        assert manifest["non_applied_second_batch_alias_count"] == 1
        assert manifest["alias_branch_final_recommendation"] == "STOP_ALIAS_BRANCH_AND_RETURN_TO_345D"
        assert manifest["full_structured_demo_export_reasonable_after_345c11"] is True
        assert manifest["official_rules_modified"] is False
        assert manifest["official_alias_assets_modified"] is False
        assert manifest["alias_apply_simulation_only"] is True
        assert manifest["candidate_package_only"] is True
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        assert manifest["milestone_ledger_updated"] is True
        assert "## 345C11 Second Batch Alias Apply Simulation" in ledger_path.read_text(
            encoding="utf-8"
        )

        simulated_rows = artifacts["simulated_metric_rows"]
        row_a = next(row for row in simulated_rows if row["metric_coverage_row_id"] == "345c::metric::00001")
        row_b = next(row for row in simulated_rows if row["metric_coverage_row_id"] == "345c::metric::00003")
        row_c = next(row for row in simulated_rows if row["metric_coverage_row_id"] == "345c::metric::00004")
        assert row_a["first_batch_simulation_applied"] is True
        assert row_a["second_batch_simulation_applied"] is False
        assert row_b["second_batch_simulation_applied"] is True
        assert row_b["cumulative_simulated_normalized_metric_name"] == "metric_b"
        assert row_c["second_batch_simulation_applied"] is True
        assert len(artifacts["non_applied_aliases"]) == 1
        assert artifacts["non_applied_aliases"][0]["raw_metric_name"] == "Alias A"
        assert artifacts["remaining_blind_spots"][0]["raw_metric_name"] == "Alias D"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c11_missing_required_inputs_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing"
        missing_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_second_batch_alias_apply_simulation_345c11(
                metric_candidate_normalization_coverage_345c_dir=missing_dir,
                reviewed_alias_apply_simulation_345c6_dir=missing_dir,
                second_batch_reviewed_alias_decision_ingestion_345c10_dir=missing_dir,
                output_dir=case_root / "output" / "second_batch_alias_apply_simulation_345c11",
                repo_root=case_root,
                ledger_path=case_root / "ledger.md",
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345C/345C6/345C10 inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
