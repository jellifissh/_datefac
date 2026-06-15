from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.recovery_rule_refinement_patch_346b3r import (  # noqa: E402
    PATCH_REQUIRES_REAUDIT,
    READY_DECISION_346B3R,
    build_recovery_rule_refinement_patch_346b3r,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_recovery_rule_refinement_patch_346b3r"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345d(root: Path) -> Path:
    dir_345d = root / "output" / "full_structured_demo_export_package_345d"
    dir_345d.mkdir(parents=True, exist_ok=True)
    _write_json(
        dir_345d / "full_structured_demo_export_package_345d_manifest.json",
        {
            "decision": "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY",
            "qa_fail_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    return dir_345d


def _seed_346b3(root: Path) -> Path:
    dir_346b3 = root / "output" / "recovery_rule_refinement_346b3"
    dir_346b3.mkdir(parents=True, exist_ok=True)
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_manifest.json",
        {
            "decision": "RECOVERY_RULE_REFINEMENT_346B3_READY",
            "qa_fail_count": 0,
            "input_346a_dir": r"D:\_datefac\output\vision_assisted_table_evidence_pilot_346a",
            "input_346a2_dir": r"D:\_datefac\output\mineru_image_path_binding_fix_346a2",
            "input_346b_dir": r"D:\_datefac\output\quality_limited_row_recovery_pilot_346b",
            "input_346b2_dir": r"D:\_datefac\output\recovery_candidate_qa_audit_346b2",
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_refined_unit_policy.json",
        {"semantic_unit_policy_applied": True, "ratio_multiple_policy": "no percent on ratio/multiple"},
    )
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_rule_change_log.json",
        [{"change_id": "346B3_RULE_001"}],
    )
    return dir_346b3


def _seed_346b2r(root: Path) -> Path:
    dir_346b2r = root / "output" / "refined_recovery_candidate_qa_reaudit_346b2r"
    dir_346b2r.mkdir(parents=True, exist_ok=True)
    _write_json(
        dir_346b2r / "refined_recovery_candidate_qa_reaudit_346b2r_manifest.json",
        {
            "decision": "REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_READY",
            "qa_fail_count": 0,
            "safe_to_expand_recovery": True,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(
        dir_346b2r / "refined_recovery_candidate_qa_reaudit_346b2r_expansion_readiness_report.json",
        {
            "safe_to_expand_recovery": True,
            "controlled_max_row_limit_suggestion": 500,
        },
    )
    return dir_346b2r


def _seed_346b4(root: Path) -> Path:
    dir_346b4 = root / "output" / "controlled_quality_limited_recovery_expansion_346b4"
    dir_346b4.mkdir(parents=True, exist_ok=True)
    unknown_rows = []
    recovery_rows = []
    lineage_rows = []
    for idx in range(12):
        source_row_id = f"capex::{idx:02d}"
        row = {
            "source_row_id": source_row_id,
            "raw_metric_name": "资本开支",
            "demo_normalized_metric_name": "capital_expenditure",
            "semantic_metric_class": "UNKNOWN",
            "controlled_recovery_decision": "CONTROLLED_NEEDS_RULE_REFINEMENT",
            "controlled_unit_repair_action": "NO_CHANGE",
            "source_pdf_name": "demo.pdf",
            "source_page": "32.0",
            "source_table_id": "tbl-32",
            "period": "2025A",
            "raw_value": "-8.95",
            "value": "-8.95",
            "sanitized_value": "-8.95",
            "value_parse_status": "PARSED",
            "minimum_lineage_present": True,
            "source_trace_available": True,
            "evidence_strength": "SOURCE_TRACE_DETERMINISTIC_POLICY",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
        unknown_rows.append(dict(row))
        recovery_rows.append(dict(row))
        lineage_rows.append(
            {
                "source_row_id": source_row_id,
                "minimum_lineage_present": True,
                "source_trace_available": True,
                "evidence_strength": "SOURCE_TRACE_DETERMINISTIC_POLICY",
            }
        )
    for idx in range(10):
        source_row_id = f"debt::{idx:02d}"
        row = {
            "source_row_id": source_row_id,
            "raw_metric_name": "债务融资",
            "demo_normalized_metric_name": "debt_financing",
            "semantic_metric_class": "UNKNOWN",
            "controlled_recovery_decision": "CONTROLLED_NEEDS_RULE_REFINEMENT",
            "controlled_unit_repair_action": "NO_CHANGE",
            "source_pdf_name": "demo.pdf",
            "source_page": "32.0",
            "source_table_id": "tbl-32",
            "period": "2025A",
            "raw_value": "1.0",
            "value": "1.0",
            "sanitized_value": "1.0",
            "value_parse_status": "PARSED",
            "minimum_lineage_present": True,
            "source_trace_available": True,
            "evidence_strength": "SOURCE_TRACE_DETERMINISTIC_POLICY",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
        unknown_rows.append(dict(row))
        recovery_rows.append(dict(row))
        lineage_rows.append(
            {
                "source_row_id": source_row_id,
                "minimum_lineage_present": True,
                "source_trace_available": True,
                "evidence_strength": "SOURCE_TRACE_DETERMINISTIC_POLICY",
            }
        )

    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_manifest.json",
        {
            "decision": "CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY",
            "qa_fail_count": 0,
            "controlled_expansion_input_row_count": 500,
            "safe_recovered_candidate_count": 212,
            "semantic_class_unknown_count": 22,
            "needs_rule_refinement_count": 22,
            "safe_to_continue_expansion": False,
            "recommended_next_step": "346B3R Recovery Rule Refinement Patch",
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.json",
        unknown_rows,
    )
    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_recovery_results.json",
        recovery_rows,
    )
    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.json",
        [
            {"semantic_metric_class": "MONETARY_AMOUNT", "row_count": 406},
            {"semantic_metric_class": "UNKNOWN", "row_count": 22},
        ],
    )
    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_unit_action_distribution.json",
        [
            {"controlled_unit_repair_action": "NO_CHANGE", "row_count": 22},
        ],
    )
    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_lineage_evidence_audit.json",
        lineage_rows,
    )
    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_guardrail_summary.json",
        {
            "false_positive_guardrail_hit_count": 0,
            "guardrail_reason_distribution": {
                "missing_monetary_unit_context": 252,
                "per_share_requires_explicit_currency_share_context": 14,
                "semantic_class_unknown": 22,
            },
        },
    )
    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_expansion_readiness_report.json",
        {
            "safe_to_continue_expansion": False,
            "recommended_next_step": "346B3R Recovery Rule Refinement Patch",
        },
    )
    return dir_346b4


def test_346b3r_runner_ready_and_outputs_patch_preview() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        dir_346b3 = _seed_346b3(case_root)
        dir_346b2r = _seed_346b2r(case_root)
        dir_346b4 = _seed_346b4(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        output_dir = case_root / "output" / "recovery_rule_refinement_patch_346b3r"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_recovery_rule_refinement_patch_346b3r.py"),
            "--full-structured-demo-export-package-345d-dir",
            str(dir_345d),
            "--recovery-rule-refinement-346b3-dir",
            str(dir_346b3),
            "--refined-recovery-candidate-qa-reaudit-346b2r-dir",
            str(dir_346b2r),
            "--controlled-quality-limited-recovery-expansion-346b4-dir",
            str(dir_346b4),
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        manifest = json.loads((output_dir / "recovery_rule_refinement_patch_346b3r_manifest.json").read_text(encoding="utf-8"))
        assert manifest["decision"] == READY_DECISION_346B3R
        assert manifest["qa_fail_count"] == 0
        assert manifest["audited_unknown_row_count"] == 22
        assert manifest["patchable_rule_gap_count"] == 22
        assert manifest["non_patchable_row_count"] == 0
        assert manifest["proposed_semantic_classifier_patch_count"] == 2
        assert manifest["proposed_unit_policy_patch_count"] == 2
        assert manifest["rows_converted_from_unknown_to_known_semantic_class_count"] == 22
        assert manifest["rows_kept_quality_limited_count"] == 22
        assert manifest["patch_requires_reaudit_count"] == 22
        assert manifest["safe_to_replay_346b4"] is True
        assert manifest["safe_to_continue_expansion"] is False
        assert manifest["milestone_ledger_updated"] is True
        assert "## 346B3R Recovery Rule Refinement Patch" in ledger_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b3r_build_marks_all_known_families_for_reaudit_only() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        dir_346b3 = _seed_346b3(case_root)
        dir_346b2r = _seed_346b2r(case_root)
        dir_346b4 = _seed_346b4(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_recovery_rule_refinement_patch_346b3r(
            full_structured_demo_export_package_345d_dir=dir_345d,
            recovery_rule_refinement_346b3_dir=dir_346b3,
            refined_recovery_candidate_qa_reaudit_346b2r_dir=dir_346b2r,
            controlled_quality_limited_recovery_expansion_346b4_dir=dir_346b4,
            output_dir=case_root / "output" / "recovery_rule_refinement_patch_346b3r",
            repo_root=case_root,
            ledger_path=ledger_path,
        )

        rows = artifacts["unknown_row_audit_rows"]
        assert len(rows) == 22
        assert all(row["proposed_semantic_class"] == "MONETARY_AMOUNT" for row in rows)
        assert all(row["patch_safety_decision"] == PATCH_REQUIRES_REAUDIT for row in rows)
        assert all("%" not in row["unit_policy_preview"] for row in rows)
        assert artifacts["manifest"]["safe_to_continue_expansion"] is False
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b3r_missing_346b4_input_fails_clearly() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        dir_346b3 = _seed_346b3(case_root)
        dir_346b2r = _seed_346b2r(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        try:
            build_recovery_rule_refinement_patch_346b3r(
                full_structured_demo_export_package_345d_dir=dir_345d,
                recovery_rule_refinement_346b3_dir=dir_346b3,
                refined_recovery_candidate_qa_reaudit_346b2r_dir=dir_346b2r,
                controlled_quality_limited_recovery_expansion_346b4_dir=case_root / "missing_346b4",
                output_dir=case_root / "output" / "recovery_rule_refinement_patch_346b3r",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError as exc:
            assert "346B4 input directory missing" in str(exc)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
