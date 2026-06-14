from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.remaining_blind_spot_human_review_package_345c9 import (  # noqa: E402
    READY_DECISION_345C9,
    append_345c9_ledger_entry,
    build_remaining_blind_spot_human_review_package_345c9,
    ledger_has_345c9_entry,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_remaining_blind_spot_human_review_package_345c9"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345c8_outputs(root: Path) -> tuple[Path, Path]:
    output_dir = root / "output" / "remaining_blind_spot_alias_candidate_package_345c8"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "REMAINING_BLIND_SPOT_ALIAS_CANDIDATE_PACKAGE_345C8_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "candidate_package_only": True,
        "selected_candidate_count": 5,
        "alias_branch_stop_or_continue_decision": "CONTINUE_WITH_SECOND_REVIEW_BATCH",
    }
    selected_candidates = [
        {
            "blind_spot_candidate_id": "345c8::candidate::001",
            "raw_metric_name": "财务费用",
            "remaining_row_count": 120,
            "remaining_raw_metric_rank": 1,
            "source_stages": "LONG_FORM_CELL|REVIEW_REQUIRED",
            "pdf_names": "alpha.pdf",
            "source_artifacts": "342F::03_LONG_FORM_CELLS",
            "sample_row_ids": "345c::metric::00001|345c::metric::00002",
            "sample_evidence_excerpt": "alpha.pdf|LONG_FORM_CELL|MEDIUM|UNNORMALIZED_METRIC",
            "candidate_priority": "HIGH",
            "review_recommendation": "INCLUDE_IN_SECOND_REVIEW_BATCH",
            "candidate_reason": "strong_second_batch_candidate",
            "risk_level": "MEDIUM",
            "risk_reasons": ["high_remaining_row_count_with_concrete_metric_signal"],
            "estimated_max_newly_normalized_rows": 120,
            "estimated_coverage_delta_if_resolved": 0.01,
            "estimated_ready_candidate_delta_if_resolved": 0,
            "needs_llm_adjudication": False,
            "needs_human_review": True,
            "suggested_next_review_action": "bounded_alias_review",
            "candidate_package_only": True,
            "official_rules_modified": False,
            "official_alias_assets_modified": False,
        },
        {
            "blind_spot_candidate_id": "345c8::candidate::002",
            "raw_metric_name": "EV/EBITDA",
            "remaining_row_count": 95,
            "remaining_raw_metric_rank": 2,
            "source_stages": "LONG_FORM_CELL",
            "pdf_names": "beta.pdf",
            "source_artifacts": "342F::03_LONG_FORM_CELLS",
            "sample_row_ids": "345c::metric::00003|345c::metric::00004",
            "sample_evidence_excerpt": "beta.pdf|LONG_FORM_CELL|MEDIUM|UNNORMALIZED_METRIC",
            "candidate_priority": "HIGH",
            "review_recommendation": "INCLUDE_IN_SECOND_REVIEW_BATCH",
            "candidate_reason": "strong_second_batch_candidate",
            "risk_level": "MEDIUM",
            "risk_reasons": ["high_remaining_row_count_with_concrete_metric_signal"],
            "estimated_max_newly_normalized_rows": 95,
            "estimated_coverage_delta_if_resolved": 0.008,
            "estimated_ready_candidate_delta_if_resolved": 0,
            "needs_llm_adjudication": False,
            "needs_human_review": True,
            "suggested_next_review_action": "bounded_alias_review",
            "candidate_package_only": True,
            "official_rules_modified": False,
            "official_alias_assets_modified": False,
        },
        {
            "blind_spot_candidate_id": "345c8::candidate::003",
            "raw_metric_name": "EBIT Margin",
            "remaining_row_count": 70,
            "remaining_raw_metric_rank": 3,
            "source_stages": "LONG_FORM_CELL",
            "pdf_names": "gamma.pdf",
            "source_artifacts": "342F::03_LONG_FORM_CELLS",
            "sample_row_ids": "345c::metric::00005",
            "sample_evidence_excerpt": "gamma.pdf|LONG_FORM_CELL|MEDIUM|UNNORMALIZED_METRIC",
            "candidate_priority": "MEDIUM",
            "review_recommendation": "INCLUDE_AS_CONTEXT_ONLY",
            "candidate_reason": "needs_context_not_direct_alias_update",
            "risk_level": "HIGH",
            "risk_reasons": ["likely_ratio_growth_or_suffix_metric_needing_context"],
            "estimated_max_newly_normalized_rows": 70,
            "estimated_coverage_delta_if_resolved": 0.004,
            "estimated_ready_candidate_delta_if_resolved": 0,
            "needs_llm_adjudication": False,
            "needs_human_review": True,
            "suggested_next_review_action": "context_reference_only",
            "candidate_package_only": True,
            "official_rules_modified": False,
            "official_alias_assets_modified": False,
        },
        {
            "blind_spot_candidate_id": "345c8::candidate::004",
            "raw_metric_name": "成本",
            "remaining_row_count": 60,
            "remaining_raw_metric_rank": 4,
            "source_stages": "LONG_FORM_CELL",
            "pdf_names": "delta.pdf",
            "source_artifacts": "342F::03_LONG_FORM_CELLS",
            "sample_row_ids": "345c::metric::00006",
            "sample_evidence_excerpt": "delta.pdf|LONG_FORM_CELL|MEDIUM|UNNORMALIZED_METRIC",
            "candidate_priority": "HIGH",
            "review_recommendation": "NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW",
            "candidate_reason": "large_impact_but_too_generic_without_context",
            "risk_level": "HIGH",
            "risk_reasons": ["generic_or_ambiguous_metric_name_without_concrete_semantic_anchor"],
            "estimated_max_newly_normalized_rows": 60,
            "estimated_coverage_delta_if_resolved": 0.003,
            "estimated_ready_candidate_delta_if_resolved": 0,
            "needs_llm_adjudication": False,
            "needs_human_review": True,
            "suggested_next_review_action": "collect_more_source_context_before_alias_review",
            "candidate_package_only": True,
            "official_rules_modified": False,
            "official_alias_assets_modified": False,
        },
        {
            "blind_spot_candidate_id": "345c8::candidate::005",
            "raw_metric_name": "其他",
            "remaining_row_count": 55,
            "remaining_raw_metric_rank": 5,
            "source_stages": "LONG_FORM_CELL",
            "pdf_names": "epsilon.pdf",
            "source_artifacts": "342F::03_LONG_FORM_CELLS",
            "sample_row_ids": "345c::metric::00007",
            "sample_evidence_excerpt": "epsilon.pdf|LONG_FORM_CELL|MEDIUM|UNNORMALIZED_METRIC",
            "candidate_priority": "HIGH",
            "review_recommendation": "EXCLUDE_TOO_GENERIC",
            "candidate_reason": "generic_fragment_excluded",
            "risk_level": "HIGH",
            "risk_reasons": ["generic_or_ambiguous_metric_name_without_concrete_semantic_anchor"],
            "estimated_max_newly_normalized_rows": 55,
            "estimated_coverage_delta_if_resolved": 0.002,
            "estimated_ready_candidate_delta_if_resolved": 0,
            "needs_llm_adjudication": False,
            "needs_human_review": True,
            "suggested_next_review_action": "collect_more_source_context_before_alias_review",
            "candidate_package_only": True,
            "official_rules_modified": False,
            "official_alias_assets_modified": False,
        },
    ]
    candidate_impact_summary = [
        {
            "blind_spot_candidate_id": row["blind_spot_candidate_id"],
            "raw_metric_name": row["raw_metric_name"],
            "estimated_max_newly_normalized_rows": row["estimated_max_newly_normalized_rows"],
            "estimated_coverage_delta_if_resolved": row["estimated_coverage_delta_if_resolved"],
            "estimated_ready_candidate_delta_if_resolved": row["estimated_ready_candidate_delta_if_resolved"],
            "candidate_priority": row["candidate_priority"],
            "review_recommendation": row["review_recommendation"],
        }
        for row in selected_candidates
    ]
    review_batch_recommendation = {
        "selected_candidate_count": 5,
        "include_in_second_review_batch_count": 2,
        "include_as_context_only_count": 1,
        "needs_source_context_before_review_count": 1,
    }
    stop_or_continue_decision = {
        "alias_branch_stop_or_continue_decision": "CONTINUE_WITH_SECOND_REVIEW_BATCH",
        "reason": "selected candidates still show meaningful batchable impact",
        "full_structured_demo_export_reasonable_after_345c8": False,
        "next_plan_recommendation": "345C9 Remaining Blind Spot Human Review Package",
    }
    _write_json(output_dir / "remaining_blind_spot_alias_candidate_package_345c8_manifest.json", manifest)
    _write_json(
        output_dir / "remaining_blind_spot_alias_candidate_package_345c8_selected_candidates.json",
        selected_candidates,
    )
    _write_json(
        output_dir / "remaining_blind_spot_alias_candidate_package_345c8_candidate_impact_summary.json",
        candidate_impact_summary,
    )
    _write_json(
        output_dir / "remaining_blind_spot_alias_candidate_package_345c8_review_batch_recommendation.json",
        review_batch_recommendation,
    )
    _write_json(
        output_dir / "remaining_blind_spot_alias_candidate_package_345c8_stop_or_continue_decision.json",
        stop_or_continue_decision,
    )
    (output_dir / "remaining_blind_spot_alias_candidate_package_345c8_executive_summary.md").write_text(
        "# existing summary",
        encoding="utf-8",
    )
    (output_dir / "remaining_blind_spot_alias_candidate_package_345c8_selected_candidates.csv").write_text(
        "stub\n",
        encoding="utf-8",
    )
    (output_dir / "remaining_blind_spot_alias_candidate_package_345c8_candidate_impact_summary.csv").write_text(
        "stub\n",
        encoding="utf-8",
    )
    ledger_path = root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text("# Ledger\n\n## 345C8 Existing Entry\n", encoding="utf-8")
    return output_dir, ledger_path


def test_345c9_ready_path_and_ledger_update() -> None:
    case_root = _make_case_root()
    try:
        input_dir, ledger_path = _seed_345c8_outputs(case_root)
        seed_artifacts = build_remaining_blind_spot_human_review_package_345c9(
            remaining_blind_spot_alias_candidate_package_345c8_dir=input_dir,
            output_dir=case_root / "output" / "remaining_blind_spot_human_review_package_345c9",
            repo_root=case_root,
            include_context_only=False,
            ledger_path=ledger_path,
        )
        assert seed_artifacts["manifest"]["milestone_ledger_updated"] is False
        changed = append_345c9_ledger_entry(
            manifest=seed_artifacts["manifest"],
            ledger_path=ledger_path,
        )
        assert changed is True
        assert ledger_has_345c9_entry(ledger_path) is True

        artifacts = build_remaining_blind_spot_human_review_package_345c9(
            remaining_blind_spot_alias_candidate_package_345c8_dir=input_dir,
            output_dir=case_root / "output" / "remaining_blind_spot_human_review_package_345c9",
            repo_root=case_root,
            include_context_only=False,
            ledger_path=ledger_path,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345C9
        assert manifest["qa_fail_count"] == 0
        assert manifest["review_required_row_count"] == 2
        assert manifest["context_only_row_count"] == 1
        assert manifest["blocked_or_too_generic_row_count"] == 2
        assert manifest["generated_review_pending_count"] == 2
        assert manifest["generated_approved_count"] == 0
        assert manifest["alias_rule_update_allowed_count"] == 0
        assert manifest["milestone_ledger_updated"] is True
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        review_rows = artifacts["review_rows"]
        assert len(review_rows) == 2
        assert all(not row["human_blind_spot_review_decision"] for row in review_rows)
        assert all(row["alias_rule_update_allowed"] is False for row in review_rows)
        assert all(
            row["review_recommendation"] == "INCLUDE_IN_SECOND_REVIEW_BATCH"
            for row in review_rows
        )
        assert len(artifacts["context_only_rows"]) == 1
        assert all(
            row["review_recommendation"] == "INCLUDE_AS_CONTEXT_ONLY"
            for row in artifacts["context_only_rows"]
        )
        assert len(artifacts["blocked_rows"]) == 2
        assert all(
            row["review_recommendation"]
            in {"EXCLUDE_TOO_GENERIC", "NEEDS_SOURCE_CONTEXT_BEFORE_REVIEW"}
            for row in artifacts["blocked_rows"]
        )
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c9_missing_required_inputs_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing"
        missing_dir.mkdir(parents=True, exist_ok=True)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        try:
            build_remaining_blind_spot_human_review_package_345c9(
                remaining_blind_spot_alias_candidate_package_345c8_dir=missing_dir,
                output_dir=case_root / "output" / "remaining_blind_spot_human_review_package_345c9",
                repo_root=case_root,
                include_context_only=False,
                ledger_path=ledger_path,
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345C8 inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
