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

from datefac.benchmark.controlled_expansion_qa_audit_346b4q import (  # noqa: E402
    READY_DECISION_346B4Q,
    build_controlled_expansion_qa_audit_346b4q,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_t346b4q"
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
    for idx in range(500):
        row = {
            "source_row_id": f"row::{idx:03d}",
            "raw_metric_name": "Revenue",
            "demo_normalized_metric_name": "revenue",
            "raw_value": f"{100 + idx / 10:.1f}",
            "sanitized_value": f"{100 + idx / 10:.1f}",
            "period": "2025A",
            "minimum_lineage_present": True,
            "source_trace_available": True,
            "source_pdf_name": "demo.pdf",
            "source_page": "12",
            "source_table_id": "tbl-1",
            "controlled_recovery_decision": "CONTROLLED_RECOVERED_DEMO_CANDIDATE" if idx < 212 else "CONTROLLED_STILL_QUALITY_LIMITED",
        }
        if 212 <= idx < 234:
            row["controlled_recovery_decision"] = "CONTROLLED_NEEDS_RULE_REFINEMENT"
            row["demo_normalized_metric_name"] = "capital_expenditure" if idx < 224 else "debt_financing"
            row["raw_metric_name"] = "Capex" if idx < 224 else "Debt financing"
        selected_rows.append(dict(row))
        recovery_rows.append(dict(row))
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
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_selected_rows.json", selected_rows)
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_recovery_results.json", recovery_rows)
    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_guardrail_summary.json",
        {
            "false_positive_guardrail_hit_count": 0,
            "guardrail_reason_distribution": {"semantic_class_unknown": 22},
        },
    )
    return dir_346b4


def _seed_346b3r(root: Path) -> Path:
    dir_346b3r = root / "output" / "recovery_rule_refinement_patch_346b3r"
    dir_346b3r.mkdir(parents=True, exist_ok=True)
    patchable_rows = []
    patch_safety_rows = []
    for idx in range(22):
        source_row_id = f"row::{212 + idx:03d}"
        metric_family = "capital_expenditure" if idx < 12 else "debt_financing"
        patchable_rows.append(
            {
                "source_row_id": source_row_id,
                "demo_normalized_metric_name": metric_family,
                "metric_family": metric_family,
                "patch_confidence": "HIGH",
            }
        )
        patch_safety_rows.append(
            {
                "source_row_id": source_row_id,
                "metric_family": metric_family,
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
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b3r / "recovery_rule_refinement_patch_346b3r_patchable_rows.json", patchable_rows)
    _write_json(dir_346b3r / "recovery_rule_refinement_patch_346b3r_patch_safety_review.json", patch_safety_rows)
    _write_json(
        dir_346b3r / "recovery_rule_refinement_patch_346b3r_replay_readiness_report.json",
        {
            "safe_to_replay_346b4": True,
            "patch_requires_reaudit_count": 22,
            "live_vlm_call_count": 0,
        },
    )
    return dir_346b3r


def _seed_346b4r(root: Path) -> Path:
    dir_346b4r = root / "output" / "controlled_expansion_replay_with_patched_rules_346b4r"
    dir_346b4r.mkdir(parents=True, exist_ok=True)
    replay_rows = []
    safe_rows = []
    patched_rows = []
    lineage_rows = []
    for idx in range(234):
        is_patch = idx >= 212
        metric = "revenue"
        raw_metric_name = "Revenue"
        semantic_class = "MONETARY_AMOUNT"
        unit_action = "NO_CHANGE"
        recovered_unit = "RMB"
        previous_decision = "CONTROLLED_RECOVERED_DEMO_CANDIDATE"
        if idx == 0:
            metric = "ev_to_ebitda"
            raw_metric_name = "EV/EBITDA"
            semantic_class = "RATIO_MULTIPLE"
            unit_action = "UNIT_RATIO_MULTIPLE_X"
            recovered_unit = "x"
        elif idx == 1:
            metric = "ebitda_margin"
            raw_metric_name = "EBITDA Margin"
            semantic_class = "PERCENTAGE_OR_MARGIN"
            unit_action = "UNIT_PERCENT_FROM_MARGIN_CONTEXT"
            recovered_unit = "%"
        elif idx == 2:
            metric = "book_value_per_share"
            raw_metric_name = "BVPS"
            semantic_class = "PER_SHARE"
            unit_action = "UNIT_PER_SHARE_CONTEXT"
            recovered_unit = "RMB/share"
        if is_patch:
            metric = "capital_expenditure" if idx < 224 else "debt_financing"
            raw_metric_name = "Capex" if idx < 224 else "Debt financing"
            semantic_class = "MONETARY_AMOUNT"
            unit_action = "REPLAY_UNIT_POLICY_RETAIN_BLANK_MONETARY_CONTEXT"
            recovered_unit = ""
            previous_decision = "CONTROLLED_NEEDS_RULE_REFINEMENT"
        row = {
            "source_row_id": f"row::{idx:03d}",
            "raw_metric_name": raw_metric_name,
            "demo_normalized_metric_name": metric,
            "raw_value": f"{100 + idx / 10:.1f}",
            "sanitized_value": f"{100 + idx / 10:.1f}",
            "period": "2025A",
            "source_pdf_name": "demo.pdf",
            "source_page": "12",
            "source_table_id": "tbl-1",
            "minimum_lineage_present": True,
            "source_trace_available": True,
            "evidence_strength": "SOURCE_TRACE_DETERMINISTIC_POLICY",
            "evidence_weakness": False,
            "lineage_preserved": True,
            "previous_346b4_decision": previous_decision,
            "patched_semantic_class": semantic_class,
            "semantic_metric_class": semantic_class,
            "patched_unit_action": unit_action,
            "controlled_unit_repair_action": unit_action,
            "patched_controlled_recovered_unit": recovered_unit,
            "controlled_recovered_unit": recovered_unit,
            "replay_recovery_decision": "REPLAY_SAFE_RECOVERED_DEMO_CANDIDATE",
            "patch_applied": is_patch,
            "patch_source": "346B3R_SIDE_CAR" if is_patch else "",
            "patch_reason": "deterministic semantic patch" if is_patch else "",
            "patch_confidence": "HIGH" if is_patch else "",
            "patch_safety_decision": "PATCH_REQUIRES_REAUDIT" if is_patch else "",
            "unit_semantic_mismatch": False,
            "same_row_set_replay": True,
            "new_row_selected": False,
            "demo_export_only": True,
        }
        replay_rows.append(dict(row))
        safe_rows.append(dict(row))
        lineage_rows.append(
            {
                "source_row_id": row["source_row_id"],
                "lineage_preserved": True,
                "minimum_lineage_present": True,
                "source_trace_available": True,
                "evidence_strength": "SOURCE_TRACE_DETERMINISTIC_POLICY",
                "evidence_weakness": False,
            }
        )
        if is_patch:
            patched_rows.append(dict(row))
    _write_json(
        dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_manifest.json",
        {
            "decision": "CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_READY",
            "qa_fail_count": 0,
            "same_row_set_replay": True,
            "new_row_selected_count": 0,
            "previous_controlled_expansion_input_row_count": 500,
            "replay_input_row_count": 500,
            "replay_safe_recovered_candidate_count": 234,
            "patch_applied_row_count": 22,
            "false_positive_guardrail_hit_count": 0,
            "unit_semantic_mismatch_count": 0,
            "lineage_audit_passed": True,
            "safe_to_continue_expansion": True,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_replay_results.json", replay_rows)
    _write_json(dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.json", safe_rows)
    _write_json(dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.json", patched_rows)
    _write_json(dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_remaining_unknown_rows.json", [])
    _write_json(dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_guardrail_hits.json", [])
    _write_json(
        dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_delta_report.json",
        [
            {"metric_name": "safe_recovered_candidate_count", "previous_value": 212, "replay_value": 234, "delta_value": 22},
            {"metric_name": "semantic_class_unknown_count", "previous_value": 22, "replay_value": 0, "delta_value": -22},
        ],
    )
    _write_json(
        dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_semantic_class_distribution.json",
        [
            {"semantic_metric_class": "MONETARY_AMOUNT", "row_count": 231},
            {"semantic_metric_class": "RATIO_MULTIPLE", "row_count": 1},
            {"semantic_metric_class": "PERCENTAGE_OR_MARGIN", "row_count": 1},
            {"semantic_metric_class": "PER_SHARE", "row_count": 1},
        ],
    )
    _write_json(
        dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_unit_action_distribution.json",
        [
            {"patched_unit_action": "NO_CHANGE", "row_count": 209},
            {"patched_unit_action": "REPLAY_UNIT_POLICY_RETAIN_BLANK_MONETARY_CONTEXT", "row_count": 22},
            {"patched_unit_action": "UNIT_PERCENT_FROM_MARGIN_CONTEXT", "row_count": 1},
            {"patched_unit_action": "UNIT_PER_SHARE_CONTEXT", "row_count": 1},
            {"patched_unit_action": "UNIT_RATIO_MULTIPLE_X", "row_count": 1},
        ],
    )
    _write_json(dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_lineage_evidence_audit.json", lineage_rows)
    _write_json(
        dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_expansion_readiness_report.json",
        {
            "same_row_set_replay": True,
            "new_row_selected_count": 0,
            "unknown_resolved_count": 22,
            "patch_applied_row_count": 22,
            "patch_regression_count": 0,
            "false_positive_guardrail_hit_count": 0,
            "unit_semantic_mismatch_count": 0,
            "lineage_audit_passed": True,
            "safe_to_continue_expansion": True,
            "recommended_next_step": "346B4Q Controlled Expansion QA Audit",
        },
    )
    return dir_346b4r


def test_346b4q_runner_ready_and_safe_to_larger_expansion() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        dir_346b4 = _seed_346b4(case_root)
        dir_346b3r = _seed_346b3r(case_root)
        dir_346b4r = _seed_346b4r(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        output_dir = case_root / "output" / "controlled_expansion_qa_audit_346b4q"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_controlled_expansion_qa_audit_346b4q.py"),
            "--full-structured-demo-export-package-345d-dir",
            str(dir_345d),
            "--controlled-quality-limited-recovery-expansion-346b4-dir",
            str(dir_346b4),
            "--recovery-rule-refinement-patch-346b3r-dir",
            str(dir_346b3r),
            "--controlled-expansion-replay-with-patched-rules-346b4r-dir",
            str(dir_346b4r),
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        manifest = json.loads((output_dir / "controlled_expansion_qa_audit_346b4q_manifest.json").read_text(encoding="utf-8"))
        assert manifest["decision"] == READY_DECISION_346B4Q
        assert manifest["qa_fail_count"] == 0
        assert manifest["qa_audited_candidate_count"] == 234
        assert manifest["qa_safe_candidate_count"] == 234
        assert manifest["qa_false_positive_suspect_count"] == 0
        assert manifest["patch_applied_audited_row_count"] == 22
        assert manifest["patch_applied_qa_pass_count"] == 22
        assert manifest["qa_safe_to_larger_expansion"] is True
        assert manifest["recommended_next_step"] == "346B5 Larger Quality-Limited Recovery Expansion"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b4q_build_detects_ratio_percent_regression() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        dir_346b4 = _seed_346b4(case_root)
        dir_346b3r = _seed_346b3r(case_root)
        dir_346b4r = _seed_346b4r(case_root)
        bad_rows = json.loads((dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.json").read_text(encoding="utf-8"))
        bad_rows[0]["patched_controlled_recovered_unit"] = "%"
        bad_rows[0]["controlled_recovered_unit"] = "%"
        _write_json(dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.json", bad_rows)
        replay_rows = json.loads((dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_replay_results.json").read_text(encoding="utf-8"))
        replay_rows[0]["patched_controlled_recovered_unit"] = "%"
        replay_rows[0]["controlled_recovered_unit"] = "%"
        _write_json(dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_replay_results.json", replay_rows)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_controlled_expansion_qa_audit_346b4q(
            full_structured_demo_export_package_345d_dir=dir_345d,
            controlled_quality_limited_recovery_expansion_346b4_dir=dir_346b4,
            recovery_rule_refinement_patch_346b3r_dir=dir_346b3r,
            controlled_expansion_replay_with_patched_rules_346b4r_dir=dir_346b4r,
            output_dir=case_root / "output" / "controlled_expansion_qa_audit_346b4q",
            repo_root=case_root,
            ledger_path=ledger_path,
        )
        manifest = artifacts["manifest"]
        assert manifest["unit_semantic_mismatch_count"] == 1
        assert manifest["qa_false_positive_suspect_count"] == 1
        assert manifest["qa_safe_to_larger_expansion"] is False
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b4q_missing_346b4r_input_fails_clearly() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        dir_346b4 = _seed_346b4(case_root)
        dir_346b3r = _seed_346b3r(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        try:
            build_controlled_expansion_qa_audit_346b4q(
                full_structured_demo_export_package_345d_dir=dir_345d,
                controlled_quality_limited_recovery_expansion_346b4_dir=dir_346b4,
                recovery_rule_refinement_patch_346b3r_dir=dir_346b3r,
                controlled_expansion_replay_with_patched_rules_346b4r_dir=case_root / "missing_346b4r",
                output_dir=case_root / "output" / "controlled_expansion_qa_audit_346b4q",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError as exc:
            assert "346B4R input directory missing" in str(exc)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
