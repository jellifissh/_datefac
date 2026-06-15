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

from datefac.benchmark.recovery_candidate_qa_audit_346b2 import (  # noqa: E402
    READY_DECISION_346B2,
    build_recovery_candidate_qa_audit_346b2,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_recovery_candidate_qa_audit_346b2"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_common_inputs(root: Path) -> tuple[Path, Path, Path]:
    dir_345d = root / "output" / "full_structured_demo_export_package_345d"
    dir_346a = root / "output" / "vision_assisted_table_evidence_pilot_346a"
    dir_346a2 = root / "output" / "mineru_image_path_binding_fix_346a2"
    for path in [dir_345d, dir_346a, dir_346a2]:
        path.mkdir(parents=True, exist_ok=True)

    _write_json(
        dir_345d / "full_structured_demo_export_package_345d_manifest.json",
        {
            "decision": "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY",
            "qa_fail_count": 0,
            "quality_limited_row_count": 3,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_limited_rows.json", [])
    _write_json(dir_345d / "full_structured_demo_export_package_345d_demo_rows.json", [])
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_caveats.json", {"note": "demo only"})
    (dir_345d / "full_structured_demo_export_package_345d_quality_caveats.md").write_text("# caveats\n", encoding="utf-8")

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
    _write_json(dir_346a / "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json", [])
    _write_json(dir_346a / "vision_assisted_table_evidence_pilot_346a_field_repair_targets.json", [])
    (dir_346a / "vision_assisted_table_evidence_pilot_346a_conflict_handling_policy.md").write_text("# policy\n", encoding="utf-8")

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
    _write_json(dir_346a2 / "mineru_image_path_binding_fix_346a2_bound_rows.json", [])
    _write_json(dir_346a2 / "mineru_image_path_binding_fix_346a2_image_resolution_status.json", [])
    _write_json(dir_346a2 / "mineru_image_path_binding_fix_346a2_json_md_context_index.json", [])
    _write_jsonl(dir_346a2 / "mineru_image_path_binding_fix_346a2_vlm_request_package.jsonl", [])
    return dir_345d, dir_346a, dir_346a2


def _seed_346b_outputs(root: Path, recovered_rows: list[dict], needs_human_rows: list[dict], still_limited_rows: list[dict]) -> Path:
    dir_346b = root / "output" / "quality_limited_row_recovery_pilot_346b"
    dir_346b.mkdir(parents=True, exist_ok=True)
    _write_json(
        dir_346b / "quality_limited_row_recovery_pilot_346b_manifest.json",
        {
            "decision": "QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY",
            "qa_fail_count": 0,
            "recovered_demo_candidate_count": len(recovered_rows),
            "needs_human_review_count": len(needs_human_rows),
            "still_quality_limited_count": len(still_limited_rows),
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.json", recovered_rows)
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_still_limited_rows.json", still_limited_rows)
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_needs_human_review_rows.json", needs_human_rows)
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_needs_vlm_rows.json", [])
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_downgraded_excluded_rows.json", [])
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_value_sanitizer_results.json", recovered_rows)
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_context_injection_results.json", recovered_rows)
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.json", recovered_rows)
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_recovery_fail_reasons.json", [])
    _write_json(
        dir_346b / "quality_limited_row_recovery_pilot_346b_reaudit_summary.json",
        {"status_distribution": {"RECOVERED_DEMO_CANDIDATE": len(recovered_rows)}},
    )
    return dir_346b


def test_346b2_runner_ready_and_flags_false_positive_ratio_percent() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, dir_346a, dir_346a2 = _seed_common_inputs(case_root)
        recovered_rows = [
            {
                "demo_export_row_id": "345d::demo::00001",
                "pilot_row_id": "346a::pilot::00001",
                "source_row_id": "row-001",
                "source_pdf_name": "demo.pdf",
                "raw_metric_name": "EV/EBITDA",
                "demo_normalized_metric_name": "ev_to_ebitda",
                "value": "15.3",
                "sanitized_value": "15.3",
                "value_parse_status": "PARSED",
                "period": "2024A",
                "unit": "",
                "inherited_unit": "%",
                "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
                "image_bound": True,
                "image_evidence_type": "TABLE_CROP_IMAGE",
                "context_available": True,
                "context_snippet": "<table><tr><td>EV/EBITDA</td><td>15.3</td></tr></table>",
                "quality_severity": "MEDIUM",
            },
            {
                "demo_export_row_id": "345d::demo::00002",
                "pilot_row_id": "346a::pilot::00002",
                "source_row_id": "row-002",
                "source_pdf_name": "demo.pdf",
                "raw_metric_name": "EBITDA Margin",
                "demo_normalized_metric_name": "ebitda_margin",
                "value": "19.0",
                "sanitized_value": "19.0",
                "value_parse_status": "PARSED",
                "period": "2024A",
                "unit": "",
                "inherited_unit": "%",
                "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
                "image_bound": True,
                "image_evidence_type": "TABLE_CROP_IMAGE",
                "context_available": True,
                "context_snippet": "<table><tr><td>EBITDA Margin</td><td>19.0%</td></tr></table>",
                "quality_severity": "MEDIUM",
            },
            {
                "demo_export_row_id": "345d::demo::00003",
                "pilot_row_id": "346a::pilot::00003",
                "source_row_id": "row-003",
                "source_pdf_name": "demo.pdf",
                "raw_metric_name": "毛利润(亿元）",
                "demo_normalized_metric_name": "gross_profit",
                "value": "7.39",
                "sanitized_value": "7.39",
                "value_parse_status": "PARSED",
                "period": "2022A",
                "unit": "亿元",
                "inherited_unit": "亿元",
                "unit_repair_action": "NO_CHANGE",
                "image_bound": True,
                "image_evidence_type": "TABLE_CROP_IMAGE",
                "context_available": True,
                "context_snippet": "<table><tr><td>毛利润(亿元）</td><td>7.39</td></tr></table>",
                "quality_severity": "MEDIUM",
            },
        ]
        needs_human_rows = [
            {
                "source_row_id": "row-004",
                "raw_metric_name": "速动比率",
                "demo_normalized_metric_name": "quick_ratio",
                "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
                "top_fail_reasons": ["NO_BOUND_EVIDENCE"],
                "image_bound": False,
                "context_available": False,
            }
        ]
        still_limited_rows = [
            {
                "source_row_id": "row-005",
                "raw_metric_name": "营业利润",
                "demo_normalized_metric_name": "operating_profit",
                "unit_repair_action": "UNIT_UNRESOLVED",
                "top_fail_reasons": ["UNRESOLVED_UNIT", "NO_BOUND_EVIDENCE"],
                "image_bound": False,
                "context_available": False,
            }
        ]
        dir_346b = _seed_346b_outputs(case_root, recovered_rows, needs_human_rows, still_limited_rows)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        output_dir = case_root / "output" / "recovery_candidate_qa_audit_346b2"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_recovery_candidate_qa_audit_346b2.py"),
            "--full-structured-demo-export-package-345d-dir",
            str(dir_345d),
            "--vision-assisted-table-evidence-pilot-346a-dir",
            str(dir_346a),
            "--mineru-image-path-binding-fix-346a2-dir",
            str(dir_346a2),
            "--quality-limited-row-recovery-pilot-346b-dir",
            str(dir_346b),
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        manifest = json.loads((output_dir / "recovery_candidate_qa_audit_346b2_manifest.json").read_text(encoding="utf-8"))
        assert manifest["decision"] == READY_DECISION_346B2
        assert manifest["qa_fail_count"] == 0
        assert manifest["audited_recovered_candidate_count"] == 3
        assert manifest["safe_recovered_candidate_count"] == 2
        assert manifest["false_positive_suspect_count"] == 1
        assert manifest["ratio_multiple_unit_mismatch_count"] == 1
        assert manifest["safe_to_expand_recovery"] is False
        assert manifest["recommended_next_step"] == "346B3 Recovery Rule Refinement"
        assert manifest["milestone_ledger_updated"] is True
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b2_semantic_classes_and_triage_outputs() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, dir_346a, dir_346a2 = _seed_common_inputs(case_root)
        recovered_rows = [
            {
                "source_row_id": "row-001",
                "pilot_row_id": "346a::pilot::00001",
                "demo_export_row_id": "345d::demo::00001",
                "raw_metric_name": "每股净资产",
                "demo_normalized_metric_name": "book_value_per_share",
                "value": "8.59",
                "sanitized_value": "8.59",
                "value_parse_status": "PARSED",
                "period": "2024A",
                "unit": "",
                "inherited_unit": "%",
                "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
                "image_bound": True,
                "image_evidence_type": "TABLE_CROP_IMAGE",
                "context_available": True,
                "context_snippet": "<table><tr><td>每股净资产</td><td>8.59</td></tr></table>",
                "quality_severity": "MEDIUM",
            }
        ]
        needs_human_rows = [
            {
                "source_row_id": "row-002",
                "raw_metric_name": "速动比率",
                "demo_normalized_metric_name": "quick_ratio",
                "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
                "top_fail_reasons": ["NO_BOUND_EVIDENCE"],
                "image_bound": False,
                "context_available": False,
            }
        ]
        still_limited_rows = [
            {
                "source_row_id": "row-003",
                "raw_metric_name": "营业利润",
                "demo_normalized_metric_name": "operating_profit",
                "unit_repair_action": "UNIT_UNRESOLVED",
                "top_fail_reasons": ["UNRESOLVED_UNIT"],
                "image_bound": False,
                "context_available": False,
            }
        ]
        dir_346b = _seed_346b_outputs(case_root, recovered_rows, needs_human_rows, still_limited_rows)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_recovery_candidate_qa_audit_346b2(
            full_structured_demo_export_package_345d_dir=dir_345d,
            vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
            mineru_image_path_binding_fix_346a2_dir=dir_346a2,
            quality_limited_row_recovery_pilot_346b_dir=dir_346b,
            output_dir=case_root / "output" / "recovery_candidate_qa_audit_346b2",
            repo_root=case_root,
            ledger_path=ledger_path,
        )
        audited = artifacts["recovered_candidate_audit_rows"][0]
        assert audited["metric_semantic_unit_class"] == "PER_SHARE"
        assert audited["safety_decision"] == "FALSE_POSITIVE_SUSPECT"
        assert audited["mismatch_type"] == "PER_SHARE_UNIT_MISMATCH"
        assert artifacts["needs_human_review_triage_rows"][0]["triage_action"] == "HUMAN_REVIEW_REQUIRED"
        assert artifacts["still_limited_triage_rows"][0]["triage_action"] == "RULE_REFINEMENT_UNIT_CLASSIFICATION"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b2_missing_346b_input_fails_clearly() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, dir_346a, dir_346a2 = _seed_common_inputs(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        try:
            build_recovery_candidate_qa_audit_346b2(
                full_structured_demo_export_package_345d_dir=dir_345d,
                vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
                mineru_image_path_binding_fix_346a2_dir=dir_346a2,
                quality_limited_row_recovery_pilot_346b_dir=case_root / "missing_346b",
                output_dir=case_root / "output" / "recovery_candidate_qa_audit_346b2",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError as exc:
            assert "346B input directory missing" in str(exc)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
