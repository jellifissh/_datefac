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

from datefac.benchmark.larger_quality_limited_recovery_expansion_346b5 import (  # noqa: E402
    READY_DECISION_346B5,
    build_larger_quality_limited_recovery_expansion_346b5,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_t346b5"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"c_{uuid4().hex[:8]}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345d(root: Path) -> Path:
    dir_345d = root / "output" / "full_structured_demo_export_package_345d"
    dir_345d.mkdir(parents=True, exist_ok=True)
    quality_rows = []
    for idx in range(40):
        metric = "revenue"
        raw_metric_name = "Revenue"
        unit = "RMB"
        value = f"{100 + idx}.0"
        if idx == 0:
            metric = "ev_to_ebitda"
            raw_metric_name = "EV/EBITDA"
            unit = ""
        elif idx == 1:
            metric = "ebitda_margin"
            raw_metric_name = "EBITDA Margin"
            unit = ""
        elif idx == 2:
            metric = "book_value_per_share"
            raw_metric_name = "BVPS"
            unit = "RMB/share"
        elif idx == 3:
            metric = "capital_expenditure"
            raw_metric_name = "Capex"
            unit = "RMB"
        elif idx == 4:
            metric = "debt_financing"
            raw_metric_name = "Debt financing"
            unit = "RMB"
        quality_rows.append(
            {
                "demo_export_row_id": f"345d::demo::{idx:05d}",
                "source_row_id": f"row::{idx:03d}",
                "source_pdf_name": "demo.pdf",
                "source_artifact": "342F::03_LONG_FORM_CELLS",
                "source_page": "12",
                "source_table_id": "tbl-1",
                "stage": "LONG_FORM_CELL",
                "raw_metric_name": raw_metric_name,
                "demo_normalized_metric_name": metric,
                "normalization_source": "BASELINE_345C",
                "alias_simulation_batch": "NONE",
                "value": value,
                "unit": unit,
                "period": "2025A",
                "currency": "",
                "company_name": "",
                "report_type": "",
                "quality_severity": "MEDIUM",
                "quality_issue_codes": "HUMAN_REVIEW_PENDING",
                "source_trace_available": True,
                "demo_export_eligible": True,
                "demo_export_caveat_level": "MEDIUM",
                "demo_export_caveats": "HUMAN_REVIEW_PENDING",
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
            }
        )
    _write_json(
        dir_345d / "full_structured_demo_export_package_345d_manifest.json",
        {
            "decision": "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY",
            "qa_fail_count": 0,
            "quality_limited_row_count": 40,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_limited_rows.json", quality_rows)
    _write_json(
        dir_345d / "full_structured_demo_export_package_345d_demo_rows.json",
        [{"source_row_id": "demo::001"}],
    )
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_caveats.json", [])
    return dir_345d


def _seed_346b4(root: Path) -> Path:
    dir_346b4 = root / "output" / "controlled_quality_limited_recovery_expansion_346b4"
    dir_346b4.mkdir(parents=True, exist_ok=True)
    selected_rows = []
    recovery_rows = []
    safe_rows = []
    for idx in range(10):
        row = {
            "source_row_id": f"row::{idx:03d}",
            "raw_metric_name": "Revenue",
            "demo_normalized_metric_name": "revenue",
            "value": f"{100 + idx}.0",
            "unit": "RMB",
            "period": "2025A",
            "source_pdf_name": "demo.pdf",
            "source_page": "12",
            "source_table_id": "tbl-1",
            "source_trace_available": True,
            "semantic_metric_class": "MONETARY_AMOUNT",
            "controlled_recovered_unit": "RMB",
            "controlled_unit_repair_action": "NO_CHANGE",
            "controlled_recovery_decision": "CONTROLLED_RECOVERED_DEMO_CANDIDATE",
        }
        selected_rows.append(dict(row))
        recovery_rows.append(dict(row))
        safe_rows.append(dict(row))
    _write_json(
        dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_manifest.json",
        {
            "decision": "CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_READY",
            "qa_fail_count": 0,
            "controlled_expansion_input_row_count": 10,
            "safe_recovered_candidate_count": 10,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_selected_rows.json", selected_rows)
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_recovery_results.json", recovery_rows)
    _write_json(dir_346b4 / "controlled_quality_limited_recovery_expansion_346b4_safe_recovered_candidates.json", safe_rows)
    return dir_346b4


def _seed_346b3r(root: Path) -> Path:
    dir_346b3r = root / "output" / "recovery_rule_refinement_patch_346b3r"
    dir_346b3r.mkdir(parents=True, exist_ok=True)
    _write_json(
        dir_346b3r / "recovery_rule_refinement_patch_346b3r_manifest.json",
        {
            "decision": "RECOVERY_RULE_REFINEMENT_PATCH_346B3R_READY",
            "qa_fail_count": 0,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(
        dir_346b3r / "recovery_rule_refinement_patch_346b3r_proposed_semantic_classifier_patches.json",
        [
            {"metric_family": "capital_expenditure", "proposed_semantic_class": "MONETARY_AMOUNT"},
            {"metric_family": "debt_financing", "proposed_semantic_class": "MONETARY_AMOUNT"},
        ],
    )
    _write_json(
        dir_346b3r / "recovery_rule_refinement_patch_346b3r_proposed_unit_policy_patches.json",
        [
            {"metric_family": "capital_expenditure", "unit_policy_decision": "KEEP_LIMITED_UNTIL_MONETARY_UNIT_CONTEXT_CONFIRMED"},
            {"metric_family": "debt_financing", "unit_policy_decision": "KEEP_LIMITED_UNTIL_MONETARY_UNIT_CONTEXT_CONFIRMED"},
        ],
    )
    _write_json(dir_346b3r / "recovery_rule_refinement_patch_346b3r_patched_unit_policy_preview.json", {"preview": True})
    _write_json(
        dir_346b3r / "recovery_rule_refinement_patch_346b3r_patch_safety_review.json",
        [
            {"source_row_id": "row::003", "patch_safety_decision": "PATCH_REQUIRES_REAUDIT"},
            {"source_row_id": "row::004", "patch_safety_decision": "PATCH_REQUIRES_REAUDIT"},
        ],
    )
    return dir_346b3r


def _seed_346b4r(root: Path) -> Path:
    dir_346b4r = root / "output" / "controlled_expansion_replay_with_patched_rules_346b4r"
    dir_346b4r.mkdir(parents=True, exist_ok=True)
    safe_rows = []
    patched_rows = []
    for idx in range(12):
        is_patch = idx >= 10
        row = {
            "source_row_id": f"row::{idx:03d}",
            "raw_metric_name": "Revenue",
            "demo_normalized_metric_name": "revenue",
            "patched_semantic_class": "MONETARY_AMOUNT",
            "patched_unit_action": "NO_CHANGE",
            "patched_controlled_recovered_unit": "RMB",
            "replay_recovery_decision": "REPLAY_SAFE_RECOVERED_DEMO_CANDIDATE",
            "patch_applied": is_patch,
            "lineage_preserved": True,
            "evidence_weakness": False,
        }
        if is_patch:
            row["demo_normalized_metric_name"] = "capital_expenditure"
            row["raw_metric_name"] = "Capex"
            row["patch_source"] = "346B3R_SIDE_CAR"
        safe_rows.append(dict(row))
        if is_patch:
            patched_rows.append(dict(row))
    _write_json(
        dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_manifest.json",
        {
            "decision": "CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_READY",
            "qa_fail_count": 0,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_safe_recovered_candidates.json", safe_rows)
    _write_json(dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_patched_rows.json", patched_rows)
    _write_json(
        dir_346b4r / "controlled_expansion_replay_with_patched_rules_346b4r_expansion_readiness_report.json",
        {"safe_to_continue_expansion": True},
    )
    return dir_346b4r


def _seed_346b4q(root: Path) -> Path:
    dir_346b4q = root / "output" / "controlled_expansion_qa_audit_346b4q"
    dir_346b4q.mkdir(parents=True, exist_ok=True)
    safe_rows = [{"source_row_id": f"row::{idx:03d}"} for idx in range(12)]
    patch_rows = [
        {"source_row_id": "row::010", "patch_qa_decision": "PATCH_QA_PASS"},
        {"source_row_id": "row::011", "patch_qa_decision": "PATCH_QA_PASS"},
    ]
    _write_json(
        dir_346b4q / "controlled_expansion_qa_audit_346b4q_manifest.json",
        {
            "decision": "CONTROLLED_EXPANSION_QA_AUDIT_346B4Q_READY",
            "qa_fail_count": 0,
            "qa_safe_to_larger_expansion": True,
            "recommended_larger_expansion_row_limit": 1500,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b4q / "controlled_expansion_qa_audit_346b4q_qa_safe_candidates.json", safe_rows)
    _write_json(dir_346b4q / "controlled_expansion_qa_audit_346b4q_patch_applied_row_qa.json", patch_rows)
    _write_json(
        dir_346b4q / "controlled_expansion_qa_audit_346b4q_larger_expansion_readiness_report.json",
        {
            "qa_safe_to_larger_expansion": True,
            "recommended_larger_expansion_row_limit": 1500,
            "recommended_next_step": "346B5 Larger Quality-Limited Recovery Expansion",
        },
    )
    return dir_346b4q


def test_346b5_runner_ready_and_excludes_previous_controlled_batch() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        dir_346b4 = _seed_346b4(case_root)
        dir_346b3r = _seed_346b3r(case_root)
        dir_346b4r = _seed_346b4r(case_root)
        dir_346b4q = _seed_346b4q(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        output_dir = case_root / "output" / "larger_quality_limited_recovery_expansion_346b5"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_larger_quality_limited_recovery_expansion_346b5.py"),
            "--full-structured-demo-export-package-345d-dir",
            str(dir_345d),
            "--controlled-quality-limited-recovery-expansion-346b4-dir",
            str(dir_346b4),
            "--recovery-rule-refinement-patch-346b3r-dir",
            str(dir_346b3r),
            "--controlled-expansion-replay-with-patched-rules-346b4r-dir",
            str(dir_346b4r),
            "--controlled-expansion-qa-audit-346b4q-dir",
            str(dir_346b4q),
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
            "--max-expansion-rows",
            "20",
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        manifest = json.loads((output_dir / "larger_quality_limited_recovery_expansion_346b5_manifest.json").read_text(encoding="utf-8"))
        assert manifest["decision"] == READY_DECISION_346B5
        assert manifest["qa_fail_count"] == 0
        assert manifest["already_346b4_controlled_batch_row_count"] == 10
        assert manifest["larger_expansion_input_row_count"] == 20
        assert manifest["safe_recovered_candidate_count"] > 0
        assert manifest["formal_client_export_allowed"] is False
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b5_build_blocks_when_346b4q_not_ready_for_larger_expansion() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        dir_346b4 = _seed_346b4(case_root)
        dir_346b3r = _seed_346b3r(case_root)
        dir_346b4r = _seed_346b4r(case_root)
        dir_346b4q = _seed_346b4q(case_root)
        manifest_path = dir_346b4q / "controlled_expansion_qa_audit_346b4q_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["qa_safe_to_larger_expansion"] = False
        _write_json(manifest_path, manifest)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        try:
            build_larger_quality_limited_recovery_expansion_346b5(
                full_structured_demo_export_package_345d_dir=dir_345d,
                controlled_quality_limited_recovery_expansion_346b4_dir=dir_346b4,
                recovery_rule_refinement_patch_346b3r_dir=dir_346b3r,
                controlled_expansion_replay_with_patched_rules_346b4r_dir=dir_346b4r,
                controlled_expansion_qa_audit_346b4q_dir=dir_346b4q,
                output_dir=case_root / "output" / "larger_quality_limited_recovery_expansion_346b5",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert "346B4Q qa_safe_to_larger_expansion must be true" in str(exc)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b5_ratio_percent_guardrail_prevents_safe_promotion() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d(case_root)
        rows = json.loads((dir_345d / "full_structured_demo_export_package_345d_quality_limited_rows.json").read_text(encoding="utf-8"))
        for row in rows:
            if row["source_row_id"] == "row::010":
                row["demo_normalized_metric_name"] = "ev_to_ebitda"
                row["raw_metric_name"] = "EV/EBITDA"
                row["unit"] = "%"
        _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_limited_rows.json", rows)
        dir_346b4 = _seed_346b4(case_root)
        dir_346b3r = _seed_346b3r(case_root)
        dir_346b4r = _seed_346b4r(case_root)
        dir_346b4q = _seed_346b4q(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_larger_quality_limited_recovery_expansion_346b5(
            full_structured_demo_export_package_345d_dir=dir_345d,
            controlled_quality_limited_recovery_expansion_346b4_dir=dir_346b4,
            recovery_rule_refinement_patch_346b3r_dir=dir_346b3r,
            controlled_expansion_replay_with_patched_rules_346b4r_dir=dir_346b4r,
            controlled_expansion_qa_audit_346b4q_dir=dir_346b4q,
            output_dir=case_root / "output" / "larger_quality_limited_recovery_expansion_346b5",
            repo_root=case_root,
            ledger_path=ledger_path,
            max_expansion_rows=20,
        )
        manifest = artifacts["manifest"]
        assert manifest["false_positive_guardrail_hit_count"] >= 1
        assert manifest["safe_to_qa_larger_expansion"] is False
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
