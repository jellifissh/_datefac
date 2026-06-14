from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.second_batch_reviewed_alias_decision_ingestion_345c10 import (  # noqa: E402
    READY_DECISION_345C10,
    append_345c10_ledger_entry,
    build_second_batch_reviewed_alias_decision_ingestion_345c10,
    ledger_has_345c10_entry,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_reviewed_workbook(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="review_required", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="context_only", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="blocked_or_too_generic", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="decision_options", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="reviewer_checklist", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="package_summary", index=False)


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_second_batch_reviewed_alias_decision_ingestion_345c10"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345c9_outputs(root: Path) -> tuple[Path, Path, Path]:
    dir_345c9 = root / "output" / "remaining_blind_spot_human_review_package_345c9"
    dir_345c9.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "REMAINING_BLIND_SPOT_HUMAN_REVIEW_PACKAGE_345C9_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "review_required_row_count": 3,
        "context_only_row_count": 1,
        "blocked_or_too_generic_row_count": 1,
    }
    review_rows = [
        {
            "blind_spot_review_row_id": "345c9::review::001",
            "source_345c8_blind_spot_candidate_id": "345c8::candidate::001",
            "raw_metric_name": "财务费用",
            "remaining_row_count": 100,
            "remaining_raw_metric_rank": 1,
            "candidate_priority": "HIGH",
            "risk_level": "MEDIUM",
            "estimated_max_newly_normalized_rows": 100,
            "estimated_coverage_delta_if_resolved": 0.01,
            "estimated_ready_candidate_delta_if_resolved": 0,
            "human_blind_spot_review_decision": "",
            "approved_standard_metric": "",
            "approved_new_standard_metric": "",
            "needs_alias_family_expansion": False,
            "needs_source_context": False,
            "reviewer": "",
            "reviewed_at": "",
            "review_notes": "",
            "alias_rule_update_allowed": False,
        },
        {
            "blind_spot_review_row_id": "345c9::review::002",
            "source_345c8_blind_spot_candidate_id": "345c8::candidate::002",
            "raw_metric_name": "ROIC",
            "remaining_row_count": 90,
            "remaining_raw_metric_rank": 2,
            "candidate_priority": "HIGH",
            "risk_level": "MEDIUM",
            "estimated_max_newly_normalized_rows": 90,
            "estimated_coverage_delta_if_resolved": 0.009,
            "estimated_ready_candidate_delta_if_resolved": 0,
            "human_blind_spot_review_decision": "",
            "approved_standard_metric": "",
            "approved_new_standard_metric": "",
            "needs_alias_family_expansion": False,
            "needs_source_context": False,
            "reviewer": "",
            "reviewed_at": "",
            "review_notes": "",
            "alias_rule_update_allowed": False,
        },
        {
            "blind_spot_review_row_id": "345c9::review::003",
            "source_345c8_blind_spot_candidate_id": "345c8::candidate::003",
            "raw_metric_name": "负债净变化",
            "remaining_row_count": 50,
            "remaining_raw_metric_rank": 3,
            "candidate_priority": "HIGH",
            "risk_level": "MEDIUM",
            "estimated_max_newly_normalized_rows": 50,
            "estimated_coverage_delta_if_resolved": 0.004,
            "estimated_ready_candidate_delta_if_resolved": 0,
            "human_blind_spot_review_decision": "",
            "approved_standard_metric": "",
            "approved_new_standard_metric": "",
            "needs_alias_family_expansion": False,
            "needs_source_context": False,
            "reviewer": "",
            "reviewed_at": "",
            "review_notes": "",
            "alias_rule_update_allowed": False,
        },
    ]
    reviewed_rows = [
        {
            **review_rows[0],
            "human_blind_spot_review_decision": "APPROVE_NEW_STANDARD",
            "approved_new_standard_metric": "financial_expense",
            "needs_alias_family_expansion": True,
            "needs_source_context": False,
            "reviewer": "小唐",
            "reviewed_at": "2026-06-14",
            "review_notes": "批准为新标准指标。",
            "alias_rule_update_allowed": True,
        },
        {
            **review_rows[1],
            "human_blind_spot_review_decision": "APPROVE_NEW_STANDARD",
            "approved_new_standard_metric": "return_on_invested_capital",
            "needs_alias_family_expansion": True,
            "needs_source_context": False,
            "reviewer": "小唐",
            "reviewed_at": "2026-06-14",
            "review_notes": "批准为新标准指标。",
            "alias_rule_update_allowed": False,
        },
        {
            **review_rows[2],
            "human_blind_spot_review_decision": "NEEDS_SOURCE_CONTEXT",
            "approved_new_standard_metric": "",
            "needs_alias_family_expansion": False,
            "needs_source_context": True,
            "reviewer": "小唐",
            "reviewed_at": "2026-06-14",
            "review_notes": "需要更多上下文。",
            "alias_rule_update_allowed": False,
        },
    ]
    _write_json(dir_345c9 / "remaining_blind_spot_human_review_package_345c9_manifest.json", manifest)
    _write_json(
        dir_345c9 / "remaining_blind_spot_human_review_package_345c9_review_rows.json",
        review_rows,
    )
    _write_json(
        dir_345c9 / "remaining_blind_spot_human_review_package_345c9_context_only_rows.json",
        [{"blind_spot_review_row_id": "ctx::001"}],
    )
    _write_json(
        dir_345c9 / "remaining_blind_spot_human_review_package_345c9_blocked_rows.json",
        [{"blind_spot_review_row_id": "blk::001"}],
    )
    reviewed_workbook = (
        dir_345c9 / "remaining_blind_spot_human_review_package_345c9_reviewed.xlsx"
    )
    _write_reviewed_workbook(reviewed_workbook, reviewed_rows)
    ledger_path = root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text("# Ledger\n\n## 345C9 Existing Entry\n", encoding="utf-8")
    return dir_345c9, reviewed_workbook, ledger_path


def test_345c10_ready_path_and_runner_outputs() -> None:
    case_root = _make_case_root()
    try:
        dir_345c9, reviewed_workbook, ledger_path = _seed_345c9_outputs(case_root)
        seed_artifacts = build_second_batch_reviewed_alias_decision_ingestion_345c10(
            remaining_blind_spot_human_review_package_345c9_dir=dir_345c9,
            reviewed_blind_spot_workbook=reviewed_workbook,
            output_dir=case_root / "output" / "second_batch_reviewed_alias_decision_ingestion_345c10",
            repo_root=case_root,
            ledger_path=ledger_path,
        )
        assert seed_artifacts["manifest"]["milestone_ledger_updated"] is False
        changed = append_345c10_ledger_entry(
            manifest=seed_artifacts["manifest"],
            ledger_path=ledger_path,
        )
        assert changed is True
        assert ledger_has_345c10_entry(ledger_path) is True

        output_dir = case_root / "output" / "runner_output"
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "tools" / "run_second_batch_reviewed_alias_decision_ingestion_345c10.py"),
                "--remaining-blind-spot-human-review-package-345c9-dir",
                str(dir_345c9),
                "--reviewed-blind-spot-workbook",
                str(reviewed_workbook),
                "--output-dir",
                str(output_dir),
                "--ledger-path",
                str(ledger_path),
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        assert "SECOND_BATCH_REVIEWED_ALIAS_DECISION_INGESTION_345C10_READY" in result.stdout
        manifest_path = output_dir / "second_batch_reviewed_alias_decision_ingestion_345c10_manifest.json"
        reviewed_decisions_path = output_dir / "second_batch_reviewed_alias_decision_ingestion_345c10_reviewed_decisions.json"
        validated_approved_path = output_dir / "second_batch_reviewed_alias_decision_ingestion_345c10_validated_approved_aliases.json"
        rejected_path = output_dir / "second_batch_reviewed_alias_decision_ingestion_345c10_rejected_or_blocked_aliases.json"
        validation_issues_path = output_dir / "second_batch_reviewed_alias_decision_ingestion_345c10_validation_issues.json"
        decision_summary_path = output_dir / "second_batch_reviewed_alias_decision_ingestion_345c10_decision_summary.json"
        assert manifest_path.exists()
        assert reviewed_decisions_path.exists()
        assert validated_approved_path.exists()
        assert rejected_path.exists()
        assert validation_issues_path.exists()
        assert decision_summary_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["decision"] == READY_DECISION_345C10
        assert manifest["qa_fail_count"] == 0
        assert manifest["reviewed_row_count"] == 3
        assert manifest["approved_new_standard_count"] == 2
        assert manifest["needs_source_context_count"] == 1
        assert manifest["approved_existing_mapping_count"] == 0
        assert manifest["validation_issue_count"] == 0
        assert manifest["apply_simulation_eligible_count"] == 2
        assert manifest["needs_alias_family_expansion_count"] == 2
        assert manifest["alias_rule_update_allowed_count"] == 0
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        reviewed_decisions = json.loads(reviewed_decisions_path.read_text(encoding="utf-8"))
        assert all(row["alias_rule_update_allowed"] is False for row in reviewed_decisions)
        assert sum(1 for row in reviewed_decisions if row["apply_simulation_eligible"]) == 2
        assert sum(1 for row in reviewed_decisions if row["human_blind_spot_review_decision"] == "NEEDS_SOURCE_CONTEXT") == 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c10_missing_required_inputs_fail() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing_345c9"
        missing_dir.mkdir(parents=True, exist_ok=True)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        try:
            build_second_batch_reviewed_alias_decision_ingestion_345c10(
                remaining_blind_spot_human_review_package_345c9_dir=missing_dir,
                reviewed_blind_spot_workbook=missing_dir / "missing.xlsx",
                output_dir=case_root / "output" / "second_batch_reviewed_alias_decision_ingestion_345c10",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345C9 inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c10_duplicate_ids_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        dir_345c9, reviewed_workbook, ledger_path = _seed_345c9_outputs(case_root)
        reviewed_rows = pd.read_excel(reviewed_workbook, sheet_name="review_required").to_dict(
            orient="records"
        )
        reviewed_rows[1]["blind_spot_review_row_id"] = reviewed_rows[0]["blind_spot_review_row_id"]
        _write_reviewed_workbook(reviewed_workbook, reviewed_rows)
        try:
            build_second_batch_reviewed_alias_decision_ingestion_345c10(
                remaining_blind_spot_human_review_package_345c9_dir=dir_345c9,
                reviewed_blind_spot_workbook=reviewed_workbook,
                output_dir=case_root / "output" / "second_batch_reviewed_alias_decision_ingestion_345c10",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
        except ValueError as exc:
            assert "Duplicate reviewed blind_spot_review_row_id" in str(exc)
        else:
            raise AssertionError("Expected duplicate id failure.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
