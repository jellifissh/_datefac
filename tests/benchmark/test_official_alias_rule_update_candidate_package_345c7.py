from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.official_alias_rule_update_candidate_package_345c7 import (  # noqa: E402
    READY_DECISION_345C7,
    build_official_alias_rule_update_candidate_package_345c7,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_official_alias_rule_update_candidate_package_345c7"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345c5_outputs(root: Path) -> Path:
    dir_345c5 = root / "output" / "reviewed_alias_decision_ingestion_345c5"
    dir_345c5.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "REVIEWED_ALIAS_DECISION_INGESTION_345C5_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
    }
    validated_approved_aliases = [
        {
            "alias_review_row_id": "345c4::review::001",
            "alias_adjudication_id": "345c2::alias::001",
            "raw_metric_name": "利润总额",
            "canonical_alias_target": "total_profit",
            "human_alias_review_decision": "APPROVE_NEW_STANDARD",
            "alias_reviewer": "Reviewer A",
            "alias_reviewed_at": "2026-06-14",
            "alias_review_notes": "Distinct metric from net profit.",
            "source_stages": "LONG_FORM_CELL|REVIEW_REQUIRED",
            "pdf_names": "demo_a.pdf|demo_b.pdf",
            "sample_row_ids": "345c::metric::00001|345c::metric::00002",
            "llm_risk_flags": ["profit_term_may_not_equal_net_profit"],
        },
        {
            "alias_review_row_id": "345c4::review::002",
            "alias_adjudication_id": "345c2::alias::002",
            "raw_metric_name": "EBITDA Margin",
            "canonical_alias_target": "ebitda_margin",
            "human_alias_review_decision": "APPROVE_NEW_STANDARD",
            "alias_reviewer": "Reviewer B",
            "alias_reviewed_at": "2026-06-14",
            "alias_review_notes": "Stable ratio style alias.",
            "source_stages": "LONG_FORM_CELL",
            "pdf_names": "demo_c.pdf",
            "sample_row_ids": "345c::metric::00003|345c::metric::00004",
            "llm_risk_flags": [],
        },
    ]
    rejected_or_deferred = [{"raw_metric_name": "Alias Z"}]
    decision_summary = {
        "reviewed_row_count": 4,
        "apply_simulation_eligible_count": 2,
    }
    _write_json(dir_345c5 / "reviewed_alias_decision_ingestion_345c5_manifest.json", manifest)
    _write_json(
        dir_345c5 / "reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.json",
        validated_approved_aliases,
    )
    _write_json(
        dir_345c5 / "reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.json",
        rejected_or_deferred,
    )
    _write_json(
        dir_345c5 / "reviewed_alias_decision_ingestion_345c5_decision_summary.json",
        decision_summary,
    )
    (dir_345c5 / "reviewed_alias_decision_ingestion_345c5_validated_approved_aliases.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c5 / "reviewed_alias_decision_ingestion_345c5_rejected_or_deferred_aliases.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    return dir_345c5


def _seed_345c6_outputs(root: Path) -> Path:
    dir_345c6 = root / "output" / "reviewed_alias_apply_simulation_345c6"
    dir_345c6.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "REVIEWED_ALIAS_APPLY_SIMULATION_345C6_READY",
        "qa_fail_count": 0,
        "validated_approved_alias_count": 2,
        "simulated_alias_applied_row_count": 9,
        "simulated_newly_normalized_row_count": 9,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
    }
    applied_alias_map = [
        {
            "approved_alias_key": "利润总额",
            "raw_metric_name": "利润总额",
            "canonical_alias_target": "total_profit",
            "source_decision": "APPROVE_NEW_STANDARD",
            "applied_row_count": 5,
            "newly_normalized_row_count": 5,
        },
        {
            "approved_alias_key": "EBITDA Margin",
            "raw_metric_name": "EBITDA Margin",
            "canonical_alias_target": "ebitda_margin",
            "source_decision": "APPROVE_NEW_STANDARD",
            "applied_row_count": 4,
            "newly_normalized_row_count": 4,
        },
    ]
    coverage_before_after = {
        "metric_candidate_row_count_before": 20,
        "simulated_alias_applied_row_count": 9,
        "simulated_newly_normalized_row_count": 9,
        "normalization_coverage_ratio_before": 0.1,
        "normalization_coverage_ratio_after_simulation": 0.55,
        "normalization_coverage_ratio_delta": 0.45,
        "ready_candidate_count_before_simulation": 1,
        "ready_candidate_count_after_alias_simulation": 7,
        "ready_candidate_count_delta": 6,
        "remaining_unnormalized_raw_metric_name_count": 2,
        "remaining_unnormalized_metric_row_count": 3,
    }
    remaining_blind_spots = [
        {
            "raw_metric_name": "利润总额同比",
            "remaining_row_count": 2,
            "remaining_ready_candidate_count": 0,
            "source_stages": "REVIEW_REQUIRED",
            "pdf_names": "demo_x.pdf",
            "quality_severity_distribution": "HIGH:2",
            "sample_row_ids": "345c::metric::00009",
        },
        {
            "raw_metric_name": "其它融资现金流",
            "remaining_row_count": 1,
            "remaining_ready_candidate_count": 0,
            "source_stages": "LONG_FORM_CELL",
            "pdf_names": "demo_y.pdf",
            "quality_severity_distribution": "MEDIUM:1",
            "sample_row_ids": "345c::metric::00010",
        },
    ]
    simulated_metric_rows = [
        {
            "raw_metric_name": "利润总额",
            "simulation_applied": True,
            "downstream_ready_before_normalization": False,
            "downstream_ready_after_alias_simulation": True,
        },
        {
            "raw_metric_name": "利润总额",
            "simulation_applied": True,
            "downstream_ready_before_normalization": True,
            "downstream_ready_after_alias_simulation": True,
        },
        {
            "raw_metric_name": "EBITDA Margin",
            "simulation_applied": True,
            "downstream_ready_before_normalization": False,
            "downstream_ready_after_alias_simulation": True,
        },
    ]
    _write_json(dir_345c6 / "reviewed_alias_apply_simulation_345c6_manifest.json", manifest)
    _write_json(
        dir_345c6 / "reviewed_alias_apply_simulation_345c6_applied_alias_map.json",
        applied_alias_map,
    )
    _write_json(
        dir_345c6 / "reviewed_alias_apply_simulation_345c6_coverage_before_after.json",
        coverage_before_after,
    )
    _write_json(
        dir_345c6 / "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.json",
        remaining_blind_spots,
    )
    _write_json(
        dir_345c6 / "reviewed_alias_apply_simulation_345c6_non_applied_aliases.json",
        [],
    )
    _write_json(
        dir_345c6 / "reviewed_alias_apply_simulation_345c6_simulated_metric_rows.json",
        simulated_metric_rows,
    )
    (dir_345c6 / "reviewed_alias_apply_simulation_345c6_applied_alias_map.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c6 / "reviewed_alias_apply_simulation_345c6_coverage_before_after.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c6 / "reviewed_alias_apply_simulation_345c6_remaining_blind_spots.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    (dir_345c6 / "reviewed_alias_apply_simulation_345c6_non_applied_aliases.csv").write_text(
        "stub\n", encoding="utf-8"
    )
    return dir_345c6


def test_345c7_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_345c5 = _seed_345c5_outputs(case_root)
        dir_345c6 = _seed_345c6_outputs(case_root)
        artifacts = build_official_alias_rule_update_candidate_package_345c7(
            reviewed_alias_decision_ingestion_345c5_dir=dir_345c5,
            reviewed_alias_apply_simulation_345c6_dir=dir_345c6,
            output_dir=case_root / "output" / "official_alias_rule_update_candidate_package_345c7",
            repo_root=case_root,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345C7
        assert manifest["qa_fail_count"] == 0
        assert manifest["candidate_row_count"] == 2
        assert manifest["validated_approved_alias_count"] == 2
        assert manifest["simulated_alias_applied_row_count"] == 9
        assert manifest["simulated_newly_normalized_row_count"] == 9
        assert manifest["normalization_coverage_ratio_delta"] == 0.45
        assert manifest["ready_candidate_count_delta"] == 6
        assert manifest["official_rules_modified"] is False
        assert manifest["official_alias_assets_modified"] is False
        assert manifest["candidate_package_only"] is True
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        candidates = artifacts["alias_rule_candidates"]
        assert len(candidates) == 2
        assert all(row["candidate_package_only"] is True for row in candidates)
        assert all(row["official_rules_modified"] is False for row in candidates)
        assert all(row["rule_update_risk_level"] in {"LOW", "MEDIUM", "HIGH"} for row in candidates)
        assert all(
            row["rule_update_recommendation"]
            in {
                "READY_FOR_CONTROLLED_RULE_UPDATE",
                "READY_FOR_DEMO_ONLY_SIDECAR_USE",
                "NEEDS_ADDITIONAL_REVIEW",
                "DO_NOT_UPDATE_RULE",
            }
            for row in candidates
        )
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c7_missing_required_inputs_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing"
        missing_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_official_alias_rule_update_candidate_package_345c7(
                reviewed_alias_decision_ingestion_345c5_dir=missing_dir,
                reviewed_alias_apply_simulation_345c6_dir=missing_dir,
                output_dir=case_root / "output" / "official_alias_rule_update_candidate_package_345c7",
                repo_root=case_root,
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345C5/345C6 inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
