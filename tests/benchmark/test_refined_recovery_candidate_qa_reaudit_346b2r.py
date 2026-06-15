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

from datefac.benchmark.refined_recovery_candidate_qa_reaudit_346b2r import (  # noqa: E402
    READY_DECISION_346B2R,
    build_refined_recovery_candidate_qa_reaudit_346b2r,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_refined_recovery_candidate_qa_reaudit_346b2r"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_common_inputs(root: Path) -> tuple[Path, Path, Path]:
    dir_345d = root / "output" / "full_structured_demo_export_package_345d"
    dir_346a = root / "output" / "vision_assisted_table_evidence_pilot_346a"
    dir_346a2 = root / "output" / "mineru_image_path_binding_fix_346a2"
    for path in (dir_345d, dir_346a, dir_346a2):
        path.mkdir(parents=True, exist_ok=True)
    _write_json(
        dir_345d / "full_structured_demo_export_package_345d_manifest.json",
        {
            "decision": "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY",
            "qa_fail_count": 0,
            "quality_limited_row_count": 5558,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(
        dir_346a / "vision_assisted_table_evidence_pilot_346a_manifest.json",
        {
            "decision": "VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY",
            "qa_fail_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(
        dir_346a2 / "mineru_image_path_binding_fix_346a2_manifest.json",
        {
            "decision": "MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY",
            "qa_fail_count": 0,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(
        dir_346a2 / "mineru_image_path_binding_fix_346a2_bound_rows.json",
        [
            {"source_row_id": "row-ratio", "image_bound": True, "image_evidence_type": "TABLE_CROP_IMAGE"},
            {"source_row_id": "row-pct", "image_bound": False},
            {"source_row_id": "row-per-share", "image_bound": True, "image_evidence_type": "TABLE_CROP_IMAGE"},
            {"source_row_id": "row-money", "image_bound": True, "image_evidence_type": "TABLE_CROP_IMAGE"},
        ],
    )
    return dir_345d, dir_346a, dir_346a2


def _seed_346b(root: Path) -> Path:
    dir_346b = root / "output" / "quality_limited_row_recovery_pilot_346b"
    dir_346b.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "source_row_id": "row-ratio",
            "pilot_row_id": "pilot-1",
            "demo_export_row_id": "demo-1",
            "raw_metric_name": "EV/EBITDA",
            "demo_normalized_metric_name": "ev_to_ebitda",
            "raw_value": "15.3",
            "sanitized_value": "15.3",
            "period": "2026E",
            "context_available": True,
            "context_snippet": "<table><tr><td>EV/EBITDA</td><td>15.3</td></tr></table>",
        },
        {
            "source_row_id": "row-pct",
            "pilot_row_id": "pilot-2",
            "demo_export_row_id": "demo-2",
            "raw_metric_name": "EBITDA Margin",
            "demo_normalized_metric_name": "ebitda_margin",
            "raw_value": "18.2%",
            "sanitized_value": "18.2",
            "period": "2026E",
            "context_available": True,
            "context_snippet": "<table><tr><td>EBITDA Margin</td><td>18.2%</td></tr></table>",
        },
        {
            "source_row_id": "row-per-share",
            "pilot_row_id": "pilot-3",
            "demo_export_row_id": "demo-3",
            "raw_metric_name": "Book value per share",
            "demo_normalized_metric_name": "book_value_per_share",
            "raw_value": "8.59",
            "sanitized_value": "8.59",
            "period": "2026E",
            "context_available": True,
            "context_snippet": "<table><tr><td>Book value per share (RMB/share)</td><td>8.59</td></tr></table>",
        },
        {
            "source_row_id": "row-money",
            "pilot_row_id": "pilot-4",
            "demo_export_row_id": "demo-4",
            "raw_metric_name": "Gross profit",
            "demo_normalized_metric_name": "gross_profit",
            "raw_value": "7.39",
            "sanitized_value": "7.39",
            "period": "2026E",
            "context_available": True,
            "context_snippet": "<table><tr><td>Gross profit (RMB mn)</td><td>7.39</td></tr></table>",
        },
    ]
    _write_json(
        dir_346b / "quality_limited_row_recovery_pilot_346b_manifest.json",
        {
            "decision": "QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY",
            "qa_fail_count": 0,
            "recovered_demo_candidate_count": 4,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.json", rows)
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_context_injection_results.json", rows)
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.json", rows)
    return dir_346b


def _seed_346b2(root: Path) -> Path:
    dir_346b2 = root / "output" / "recovery_candidate_qa_audit_346b2"
    dir_346b2.mkdir(parents=True, exist_ok=True)
    audited_rows = [
        {
            "source_row_id": "row-ratio",
            "raw_metric_name": "EV/EBITDA",
            "demo_normalized_metric_name": "ev_to_ebitda",
            "mismatch_type": "RATIO_MULTIPLE_UNIT_MISMATCH",
            "safety_decision": "FALSE_POSITIVE_SUSPECT",
        },
        {
            "source_row_id": "row-pct",
            "raw_metric_name": "EBITDA Margin",
            "demo_normalized_metric_name": "ebitda_margin",
            "safety_decision": "SAFE_RECOVERED_DEMO_CANDIDATE",
        },
        {
            "source_row_id": "row-per-share",
            "raw_metric_name": "Book value per share",
            "demo_normalized_metric_name": "book_value_per_share",
            "mismatch_type": "PER_SHARE_UNIT_MISMATCH",
            "safety_decision": "FALSE_POSITIVE_SUSPECT",
        },
        {
            "source_row_id": "row-money",
            "raw_metric_name": "Gross profit",
            "demo_normalized_metric_name": "gross_profit",
            "safety_decision": "SAFE_RECOVERED_DEMO_CANDIDATE",
        },
    ]
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_manifest.json",
        {
            "decision": "RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY",
            "qa_fail_count": 0,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b2 / "recovery_candidate_qa_audit_346b2_recovered_candidate_audit.json", audited_rows)
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_false_positive_suspects.json",
        [row for row in audited_rows if row["safety_decision"] == "FALSE_POSITIVE_SUSPECT"],
    )
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_unit_repair_audit.json",
        [
            {"source_row_id": "row-ratio", "metric_semantic_unit_class": "RATIO_MULTIPLE"},
            {"source_row_id": "row-pct", "metric_semantic_unit_class": "PERCENTAGE_OR_MARGIN"},
            {"source_row_id": "row-per-share", "metric_semantic_unit_class": "PER_SHARE"},
            {"source_row_id": "row-money", "metric_semantic_unit_class": "MONETARY_AMOUNT"},
        ],
    )
    return dir_346b2


def _seed_346b3(root: Path) -> Path:
    dir_346b3 = root / "output" / "recovery_rule_refinement_346b3"
    dir_346b3.mkdir(parents=True, exist_ok=True)
    refined_rows = [
        {
            "source_row_id": "row-ratio",
            "pilot_row_id": "pilot-1",
            "demo_export_row_id": "demo-1",
            "raw_metric_name": "EV/EBITDA",
            "demo_normalized_metric_name": "ev_to_ebitda",
            "raw_value": "15.3",
            "sanitized_value": "15.3",
            "period": "2026E",
            "context_available": True,
            "context_snippet": "<table><tr><td>EV/EBITDA</td><td>15.3</td></tr></table>",
            "semantic_metric_class": "RATIO_MULTIPLE",
            "refined_unit": "x",
            "refined_unit_repair_action": "UNIT_RATIO_MULTIPLE_X",
            "refined_recovery_decision": "REFINED_SAFE_RECOVERED_DEMO_CANDIDATE",
            "image_bound": True,
            "image_evidence_type": "TABLE_CROP_IMAGE",
        },
        {
            "source_row_id": "row-pct",
            "pilot_row_id": "pilot-2",
            "demo_export_row_id": "demo-2",
            "raw_metric_name": "EBITDA Margin",
            "demo_normalized_metric_name": "ebitda_margin",
            "raw_value": "18.2%",
            "sanitized_value": "18.2",
            "period": "2026E",
            "context_available": True,
            "context_snippet": "<table><tr><td>EBITDA Margin</td><td>18.2%</td></tr></table>",
            "semantic_metric_class": "PERCENTAGE_OR_MARGIN",
            "refined_unit": "%",
            "refined_unit_repair_action": "UNIT_PERCENT_FROM_MARGIN_CONTEXT",
            "refined_recovery_decision": "REFINED_SAFE_RECOVERED_DEMO_CANDIDATE",
            "image_bound": False,
            "image_evidence_type": "",
        },
        {
            "source_row_id": "row-per-share",
            "pilot_row_id": "pilot-3",
            "demo_export_row_id": "demo-3",
            "raw_metric_name": "Book value per share",
            "demo_normalized_metric_name": "book_value_per_share",
            "raw_value": "8.59",
            "sanitized_value": "8.59",
            "period": "2026E",
            "context_available": True,
            "context_snippet": "<table><tr><td>Book value per share (RMB/share)</td><td>8.59</td></tr></table>",
            "semantic_metric_class": "PER_SHARE",
            "refined_unit": "RMB/share",
            "refined_unit_repair_action": "UNIT_PER_SHARE_CONTEXT",
            "refined_recovery_decision": "REFINED_SAFE_RECOVERED_DEMO_CANDIDATE",
            "image_bound": True,
            "image_evidence_type": "TABLE_CROP_IMAGE",
        },
        {
            "source_row_id": "row-money",
            "pilot_row_id": "pilot-4",
            "demo_export_row_id": "demo-4",
            "raw_metric_name": "Gross profit",
            "demo_normalized_metric_name": "gross_profit",
            "raw_value": "7.39",
            "sanitized_value": "7.39",
            "period": "2026E",
            "context_available": True,
            "context_snippet": "<table><tr><td>Gross profit (RMB mn)</td><td>7.39</td></tr></table>",
            "semantic_metric_class": "MONETARY_AMOUNT",
            "refined_unit": "RMB",
            "refined_unit_repair_action": "NO_CHANGE",
            "refined_recovery_decision": "REFINED_SAFE_RECOVERED_DEMO_CANDIDATE",
            "image_bound": True,
            "image_evidence_type": "TABLE_CROP_IMAGE",
        },
    ]
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_manifest.json",
        {
            "decision": "RECOVERY_RULE_REFINEMENT_346B3_READY",
            "qa_fail_count": 0,
            "corrected_ratio_multiple_unit_count": 1,
            "corrected_per_share_unit_count": 1,
            "preserved_percentage_margin_unit_count": 1,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b3 / "recovery_rule_refinement_346b3_refined_candidates.json", refined_rows)
    _write_json(dir_346b3 / "recovery_rule_refinement_346b3_refined_safe_candidates.json", refined_rows)
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_corrected_ratio_multiple_rows.json",
        [refined_rows[0]],
    )
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_corrected_per_share_rows.json",
        [refined_rows[2]],
    )
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_preserved_percentage_margin_rows.json",
        [refined_rows[1]],
    )
    _write_json(dir_346b3 / "recovery_rule_refinement_346b3_demoted_rows.json", [])
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_refined_unit_policy.json",
        {"semantic_unit_policy_applied": True},
    )
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_rule_change_log.json",
        [{"change_id": "rule-1"}],
    )
    _write_json(dir_346b3 / "recovery_rule_refinement_346b3_reaudit_preview.json", refined_rows)
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_expansion_readiness_report.json",
        {"safe_to_expand_recovery": False},
    )
    return dir_346b3


def test_346b2r_runner_ready_and_safe_to_expand() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, dir_346a, dir_346a2 = _seed_common_inputs(case_root)
        dir_346b = _seed_346b(case_root)
        dir_346b2 = _seed_346b2(case_root)
        dir_346b3 = _seed_346b3(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        output_dir = case_root / "output" / "refined_recovery_candidate_qa_reaudit_346b2r"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_refined_recovery_candidate_qa_reaudit_346b2r.py"),
            "--full-structured-demo-export-package-345d-dir",
            str(dir_345d),
            "--vision-assisted-table-evidence-pilot-346a-dir",
            str(dir_346a),
            "--mineru-image-path-binding-fix-346a2-dir",
            str(dir_346a2),
            "--quality-limited-row-recovery-pilot-346b-dir",
            str(dir_346b),
            "--recovery-candidate-qa-audit-346b2-dir",
            str(dir_346b2),
            "--recovery-rule-refinement-346b3-dir",
            str(dir_346b3),
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        manifest = json.loads((output_dir / "refined_recovery_candidate_qa_reaudit_346b2r_manifest.json").read_text(encoding="utf-8"))
        assert manifest["decision"] == READY_DECISION_346B2R
        assert manifest["qa_fail_count"] == 0
        assert manifest["reaudit_candidate_count"] == 4
        assert manifest["reaudit_safe_candidate_count"] == 4
        assert manifest["reaudit_false_positive_suspect_count"] == 0
        assert manifest["false_positive_regression_fixed_count"] == 2
        assert manifest["safe_to_expand_recovery"] is True
        assert manifest["recommended_expansion_scope"] == "346B4 Controlled Quality-Limited Recovery Expansion"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b2r_build_function_detects_percent_ratio_regression() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, dir_346a, dir_346a2 = _seed_common_inputs(case_root)
        dir_346b = _seed_346b(case_root)
        dir_346b2 = _seed_346b2(case_root)
        dir_346b3 = _seed_346b3(case_root)
        bad_rows = json.loads((dir_346b3 / "recovery_rule_refinement_346b3_refined_candidates.json").read_text(encoding="utf-8"))
        bad_rows[0]["refined_unit"] = "%"
        bad_rows[0]["refined_unit_repair_action"] = "UNIT_PERCENT_FROM_MARGIN_CONTEXT"
        _write_json(dir_346b3 / "recovery_rule_refinement_346b3_refined_candidates.json", bad_rows)
        _write_json(dir_346b3 / "recovery_rule_refinement_346b3_refined_safe_candidates.json", bad_rows)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_refined_recovery_candidate_qa_reaudit_346b2r(
            full_structured_demo_export_package_345d_dir=dir_345d,
            vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
            mineru_image_path_binding_fix_346a2_dir=dir_346a2,
            quality_limited_row_recovery_pilot_346b_dir=dir_346b,
            recovery_candidate_qa_audit_346b2_dir=dir_346b2,
            recovery_rule_refinement_346b3_dir=dir_346b3,
            output_dir=case_root / "output" / "refined_recovery_candidate_qa_reaudit_346b2r",
            repo_root=case_root,
            ledger_path=ledger_path,
        )
        manifest = artifacts["manifest"]
        assert manifest["ratio_multiple_unit_mismatch_count"] == 1
        assert manifest["reaudit_false_positive_suspect_count"] == 1
        assert manifest["false_positive_regression_still_risky_count"] == 1
        assert manifest["safe_to_expand_recovery"] is False
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b2r_missing_346b3_input_fails_clearly() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, dir_346a, dir_346a2 = _seed_common_inputs(case_root)
        dir_346b = _seed_346b(case_root)
        dir_346b2 = _seed_346b2(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        try:
            build_refined_recovery_candidate_qa_reaudit_346b2r(
                full_structured_demo_export_package_345d_dir=dir_345d,
                vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
                mineru_image_path_binding_fix_346a2_dir=dir_346a2,
                quality_limited_row_recovery_pilot_346b_dir=dir_346b,
                recovery_candidate_qa_audit_346b2_dir=dir_346b2,
                recovery_rule_refinement_346b3_dir=case_root / "missing_346b3",
                output_dir=case_root / "output" / "refined_recovery_candidate_qa_reaudit_346b2r",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError as exc:
            assert "346B3 input directory missing" in str(exc)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b2r_runner_refreshes_existing_ledger_entry() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, dir_346a, dir_346a2 = _seed_common_inputs(case_root)
        dir_346b = _seed_346b(case_root)
        dir_346b2 = _seed_346b2(case_root)
        dir_346b3 = _seed_346b3(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_椤圭洰杩涚▼.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(
            "# Ledger\n\n"
            "## 346B2R Refined Recovery Candidate QA Reaudit\n\n"
            "Status: completed\n\n"
            "- decision: REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_READY\n"
            "- reaudit_safe_candidate_count: 38\n"
            "- reaudit_false_positive_suspect_count: 32\n"
            "- ratio_multiple_unit_mismatch_count: 32\n"
            "- safe_to_expand_recovery: False\n"
            "- next_recommended_step: 346B3R Recovery Rule Refinement Patch\n",
            encoding="utf-8",
        )
        output_dir = case_root / "output" / "refined_recovery_candidate_qa_reaudit_346b2r"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_refined_recovery_candidate_qa_reaudit_346b2r.py"),
            "--full-structured-demo-export-package-345d-dir",
            str(dir_345d),
            "--vision-assisted-table-evidence-pilot-346a-dir",
            str(dir_346a),
            "--mineru-image-path-binding-fix-346a2-dir",
            str(dir_346a2),
            "--quality-limited-row-recovery-pilot-346b-dir",
            str(dir_346b),
            "--recovery-candidate-qa-audit-346b2-dir",
            str(dir_346b2),
            "--recovery-rule-refinement-346b3-dir",
            str(dir_346b3),
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        ledger_text = ledger_path.read_text(encoding="utf-8")
        assert ledger_text.count("## 346B2R Refined Recovery Candidate QA Reaudit") == 1
        assert "- reaudit_safe_candidate_count: 4" in ledger_text
        assert "- reaudit_false_positive_suspect_count: 0" in ledger_text
        assert "- ratio_multiple_unit_mismatch_count: 0" in ledger_text
        assert "- safe_to_expand_recovery: True" in ledger_text
        assert "346B3R Recovery Rule Refinement Patch" not in ledger_text
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
