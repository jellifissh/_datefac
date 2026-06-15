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

from datefac.benchmark.controlled_expansion_replay_with_patched_rules_346b4r import (  # noqa: E402
    READY_DECISION_346B4R,
    build_controlled_expansion_replay_with_patched_rules_346b4r,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    # Keep fixture paths short enough for Windows path-length limits.
    base_dir = PROJECT_ROOT / "_t346b4r"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"c_{uuid4().hex[:8]}"
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


def _seed_346b4(root: Path) -> Path:
    dir_346b4 = root / "output" / "controlled_quality_limited_recovery_expansion_346b4"
    dir_346b4.mkdir(parents=True, exist_ok=True)
    selected_rows = []
    recovery_rows = []
    safe_rows = []
    still_rows = []
    human_rows = []
    unknown_rows = []
    for idx in range(212):
        row = {
            "source_row_id": f"safe::{idx:03d}",
            "raw_metric_name": "Revenue",
            "demo_normalized_metric_name": "revenue",
            "semantic_metric_class": "MONETARY_AMOUNT",
            "controlled_unit_repair_action": "UNIT_MONETARY_CONTEXT_CONFIRMED",
            "controlled_recovered_unit": "百万元",
            "controlled_recovery_decision": "CONTROLLED_RECOVERED_DEMO_CANDIDATE",
            "minimum_lineage_present": True,
            "source_trace_available": True,
            "source_pdf_name": "demo.pdf",
            "source_page": "12",
            "source_table_id": "tbl-safe",
            "period": "2025A",
            "evidence_strength": "SOURCE_TRACE_DETERMINISTIC_POLICY",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
        selected_rows.append(dict(row))
        recovery_rows.append(dict(row))
        safe_rows.append(dict(row))
    for idx in range(252):
        row = {
            "source_row_id": f"still::{idx:03d}",
            "raw_metric_name": "Revenue",
            "demo_normalized_metric_name": "revenue",
            "semantic_metric_class": "MONETARY_AMOUNT",
            "controlled_unit_repair_action": "NO_CHANGE",
            "controlled_recovered_unit": "",
            "controlled_recovery_decision": "CONTROLLED_STILL_QUALITY_LIMITED",
            "minimum_lineage_present": True,
            "source_trace_available": True,
            "source_pdf_name": "demo.pdf",
            "source_page": "22",
            "source_table_id": "tbl-still",
            "period": "2025A",
            "evidence_strength": "SOURCE_TRACE_DETERMINISTIC_POLICY",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
        selected_rows.append(dict(row))
        recovery_rows.append(dict(row))
        still_rows.append(dict(row))
    for idx in range(14):
        row = {
            "source_row_id": f"human::{idx:03d}",
            "raw_metric_name": "BVPS",
            "demo_normalized_metric_name": "book_value_per_share",
            "semantic_metric_class": "PER_SHARE",
            "controlled_unit_repair_action": "NEEDS_UNIT_CURRENCY_CONTEXT_PER_SHARE",
            "controlled_recovered_unit": "",
            "controlled_recovery_decision": "CONTROLLED_NEEDS_HUMAN_REVIEW",
            "minimum_lineage_present": True,
            "source_trace_available": True,
            "source_pdf_name": "demo.pdf",
            "source_page": "28",
            "source_table_id": "tbl-human",
            "period": "2025A",
            "evidence_strength": "SOURCE_TRACE_DETERMINISTIC_POLICY",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
        selected_rows.append(dict(row))
        recovery_rows.append(dict(row))
        human_rows.append(dict(row))
    for idx in range(12):
        row = {
            "source_row_id": f"capex::{idx:02d}",
            "raw_metric_name": "资本开支",
            "demo_normalized_metric_name": "capital_expenditure",
            "semantic_metric_class": "UNKNOWN",
            "controlled_unit_repair_action": "NO_CHANGE",
            "controlled_recovered_unit": "",
            "controlled_recovery_decision": "CONTROLLED_NEEDS_RULE_REFINEMENT",
            "minimum_lineage_present": True,
            "source_trace_available": True,
            "source_pdf_name": "demo.pdf",
            "source_page": "32",
            "source_table_id": "tbl-capex",
            "period": "2025A",
            "evidence_strength": "SOURCE_TRACE_DETERMINISTIC_POLICY",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
        selected_rows.append(dict(row))
        recovery_rows.append(dict(row))
        unknown_rows.append(dict(row))
    for idx in range(10):
        row = {
            "source_row_id": f"debt::{idx:02d}",
            "raw_metric_name": "债务融资",
            "demo_normalized_metric_name": "debt_financing",
            "semantic_metric_class": "UNKNOWN",
            "controlled_unit_repair_action": "NO_CHANGE",
            "controlled_recovered_unit": "",
            "controlled_recovery_decision": "CONTROLLED_NEEDS_RULE_REFINEMENT",
            "minimum_lineage_present": True,
            "source_trace_available": True,
            "source_pdf_name": "demo.pdf",
            "source_page": "32",
            "source_table_id": "tbl-debt",
            "period": "2025A",
            "evidence_strength": "SOURCE_TRACE_DETERMINISTIC_POLICY",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
        selected_rows.append(dict(row))
        recovery_rows.append(dict(row))
        unknown_rows.append(dict(row))

    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_manifest.json",
        {
            "decision": "CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY",
            "qa_fail_count": 0,
            "controlled_expansion_input_row_count": 500,
            "safe_recovered_candidate_count": 212,
            "semantic_class_unknown_count": 22,
            "needs_rule_refinement_count": 22,
            "still_quality_limited_count": 252,
            "needs_human_review_count": 14,
            "safe_to_continue_expansion": False,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_selected_rows.json", selected_rows)
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_recovery_results.json", recovery_rows)
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_recovered_demo_candidates.json", safe_rows)
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.json", safe_rows)
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_still_limited_rows.json", still_rows)
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_needs_human_review_rows.json", human_rows)
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_needs_rule_refinement_rows.json", unknown_rows)
    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_semantic_class_distribution.json",
        [
            {"semantic_metric_class": "MONETARY_AMOUNT", "row_count": 464},
            {"semantic_metric_class": "PER_SHARE", "row_count": 14},
            {"semantic_metric_class": "UNKNOWN", "row_count": 22},
        ],
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
    return dir_346b4


def _seed_346b3r(root: Path) -> Path:
    dir_346b3r = root / "output" / "recovery_rule_refinement_patch_346b3r"
    dir_346b3r.mkdir(parents=True, exist_ok=True)
    patchable_rows = []
    patch_safety_rows = []
    for idx in range(12):
        source_row_id = f"capex::{idx:02d}"
        patchable_rows.append(
            {
                "source_row_id": source_row_id,
                "raw_metric_name": "资本开支",
                "demo_normalized_metric_name": "capital_expenditure",
                "metric_family": "capital_expenditure",
                "patch_confidence": "HIGH",
                "patchable_rule_gap": True,
            }
        )
        patch_safety_rows.append(
            {
                "source_row_id": source_row_id,
                "metric_family": "capital_expenditure",
                "patch_safety_decision": "PATCH_REQUIRES_REAUDIT",
                "patch_safety_reason": "deterministic semantic patch; replay QA still required",
            }
        )
    for idx in range(10):
        source_row_id = f"debt::{idx:02d}"
        patchable_rows.append(
            {
                "source_row_id": source_row_id,
                "raw_metric_name": "债务融资",
                "demo_normalized_metric_name": "debt_financing",
                "metric_family": "debt_financing",
                "patch_confidence": "HIGH",
                "patchable_rule_gap": True,
            }
        )
        patch_safety_rows.append(
            {
                "source_row_id": source_row_id,
                "metric_family": "debt_financing",
                "patch_safety_decision": "PATCH_REQUIRES_REAUDIT",
                "patch_safety_reason": "deterministic semantic patch; replay QA still required",
            }
        )
    _write_json(
        dir_346b3r / "recovery_rule_refinement_patch_346b3r_manifest.json",
        {
            "decision": "RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY",
            "qa_fail_count": 0,
            "safe_to_replay_346b4": True,
            "patch_requires_reaudit_count": 22,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b3r / "recovery_rule_refinement_patch_346b3r_patchable_rows.json", patchable_rows)
    _write_json(
        dir_346b3r / "recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.json",
        [
            {
                "metric_family": "capital_expenditure",
                "raw_metric_name": "资本开支",
                "patch_candidate_type": "SPECIAL_MONETARY_PATTERN",
                "proposed_semantic_class": "MONETARY_AMOUNT",
                "semantic_classifier_pattern": "capital_expenditure|资本开支",
                "row_count": 12,
            },
            {
                "metric_family": "debt_financing",
                "raw_metric_name": "债务融资",
                "patch_candidate_type": "SPECIAL_MONETARY_PATTERN",
                "proposed_semantic_class": "MONETARY_AMOUNT",
                "semantic_classifier_pattern": "debt_financing|债务融资",
                "row_count": 10,
            },
        ],
    )
    _write_json(
        dir_346b3r / "recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.json",
        [
            {
                "metric_family": "capital_expenditure",
                "unit_policy_patch_type": "DOMAIN_SPECIFIC_UNIT_PATTERN",
                "unit_policy_decision": "KEEP_LIMITED_UNTIL_MONETARY_UNIT_CONTEXT_CONFIRMED",
                "preview_policy": "do not infer percent-style or ratio-style units; keep unit blank unless a later replay step binds deterministic monetary context",
                "row_count": 12,
            },
            {
                "metric_family": "debt_financing",
                "unit_policy_patch_type": "DOMAIN_SPECIFIC_UNIT_PATTERN",
                "unit_policy_decision": "KEEP_LIMITED_UNTIL_MONETARY_UNIT_CONTEXT_CONFIRMED",
                "preview_policy": "do not infer percent-style or ratio-style units; keep unit blank unless a later replay step binds deterministic monetary context",
                "row_count": 10,
            },
        ],
    )
    _write_json(
        dir_346b3r / "recovery_rule_refinement_patch_346b3r_patched_unit_policy_preview.json",
        {"sidecar_only": True, "no_write_back": True},
    )
    _write_json(dir_346b3r / "recovery_rule_refinement_patch_346b3r_patch_safety_review.json", patch_safety_rows)
    _write_json(
        dir_346b3r / "recovery_rule_refinement_patch_346b3r_replay_readiness_report.json",
        {
            "safe_to_replay_346b4": True,
            "safe_to_continue_expansion": False,
        },
    )
    return dir_346b3r


def test_346b4r_runner_ready_and_same_row_set_replay() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        dir_346b4 = _seed_346b4(case_root)
        dir_346b3r = _seed_346b3r(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        output_dir = case_root / "output" / "controlled_expansion_replay_with_patched_rules_346b4r"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_controlled_expansion_replay_with_patched_rules_346b4r.py"),
            "--full-structured-demo-export-package-345d-dir",
            str(dir_345d),
            "--controlled-quality-limited-recovery-expansion-346b4-dir",
            str(dir_346b4),
            "--recovery-rule-refinement-patch-346b3r-dir",
            str(dir_346b3r),
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        manifest = json.loads((output_dir / "controlled_expansion_replay_with_patched_rules_346b4r_manifest.json").read_text(encoding="utf-8"))
        assert manifest["decision"] == READY_DECISION_346B4R
        assert manifest["qa_fail_count"] == 0
        assert manifest["replay_input_row_count"] == 500
        assert manifest["same_row_set_replay"] is True
        assert manifest["new_row_selected_count"] == 0
        assert manifest["patch_applied_row_count"] == 22
        assert manifest["replay_semantic_class_unknown_count"] == 0
        assert manifest["unknown_resolved_count"] == 22
        assert manifest["patch_regression_count"] == 0
        assert manifest["false_positive_guardrail_hit_count"] == 0
        assert manifest["unit_semantic_mismatch_count"] == 0
        assert manifest["lineage_audit_passed"] is True
        assert manifest["safe_to_continue_expansion"] is True
        assert manifest["replay_safe_recovered_candidate_count"] == 234
        assert manifest["safe_recovered_delta"] == 22
        assert manifest["milestone_ledger_updated"] is True
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b4r_build_produces_no_new_rows_and_no_unknowns() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        dir_346b4 = _seed_346b4(case_root)
        dir_346b3r = _seed_346b3r(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_controlled_expansion_replay_with_patched_rules_346b4r(
            full_structured_demo_export_package_345d_dir=dir_345d,
            controlled_quality_limited_recovery_expansion_346b4_dir=dir_346b4,
            recovery_rule_refinement_patch_346b3r_dir=dir_346b3r,
            output_dir=case_root / "output" / "controlled_expansion_replay_with_patched_rules_346b4r",
            repo_root=case_root,
            ledger_path=ledger_path,
        )
        rows = artifacts["replay_results_rows"]
        assert len(rows) == 500
        assert all(not row["new_row_selected"] for row in rows)
        assert sum(1 for row in rows if row["patch_applied"]) == 22
        assert sum(1 for row in rows if row["replay_semantic_class_unknown"]) == 0
        assert all(not row["unit_semantic_mismatch"] for row in rows)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b4r_missing_346b3r_input_fails_clearly() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        dir_346b4 = _seed_346b4(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        try:
            build_controlled_expansion_replay_with_patched_rules_346b4r(
                full_structured_demo_export_package_345d_dir=dir_345d,
                controlled_quality_limited_recovery_expansion_346b4_dir=dir_346b4,
                recovery_rule_refinement_patch_346b3r_dir=case_root / "missing_346b3r",
                output_dir=case_root / "output" / "controlled_expansion_replay_with_patched_rules_346b4r",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError as exc:
            assert "346B3R input directory missing" in str(exc)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
