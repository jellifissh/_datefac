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

from datefac.benchmark.recovery_rule_refinement_346b3 import (  # noqa: E402
    READY_DECISION_346B3,
    build_recovery_rule_refinement_346b3,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_recovery_rule_refinement_346b3"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345d_346a_346a2(root: Path) -> tuple[Path, Path, Path]:
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
            {"source_row_id": "row-ratio", "image_bound": True},
            {"source_row_id": "row-pct", "image_bound": True},
            {"source_row_id": "row-per-share", "image_bound": True},
            {"source_row_id": "row-money", "image_bound": True},
        ],
    )
    return dir_345d, dir_346a, dir_346a2


def _seed_346b(root: Path) -> Path:
    dir_346b = root / "output" / "quality_limited_row_recovery_pilot_346b"
    dir_346b.mkdir(parents=True, exist_ok=True)
    recovered_rows = [
        {
            "source_row_id": "row-ratio",
            "raw_metric_name": "EV/EBITDA",
            "demo_normalized_metric_name": "ev_to_ebitda",
            "unit": "",
            "inherited_unit": "%",
            "recovered_unit": "%",
            "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
            "value": "15.3",
            "sanitized_value": "15.3",
            "value_parse_status": "PARSED",
            "period": "2026E",
            "context_snippet": "<table><tr><td>EV/EBITDA</td><td>15.3</td></tr></table>",
        },
        {
            "source_row_id": "row-pct",
            "raw_metric_name": "EBITDA Margin",
            "demo_normalized_metric_name": "ebitda_margin",
            "unit": "",
            "inherited_unit": "%",
            "recovered_unit": "%",
            "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
            "value": "18.2",
            "sanitized_value": "18.2",
            "value_parse_status": "PARSED",
            "period": "2026E",
            "context_snippet": "<table><tr><td>EBITDA Margin</td><td>18.2%</td></tr></table>",
        },
        {
            "source_row_id": "row-per-share",
            "raw_metric_name": "每股净资产",
            "demo_normalized_metric_name": "book_value_per_share",
            "unit": "",
            "inherited_unit": "%",
            "recovered_unit": "%",
            "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
            "value": "8.59",
            "sanitized_value": "8.59",
            "value_parse_status": "PARSED",
            "period": "2026E",
            "context_snippet": "<table><tr><td>每股净资产</td><td>8.59</td></tr></table>",
        },
        {
            "source_row_id": "row-money",
            "raw_metric_name": "毛利润(亿元）",
            "demo_normalized_metric_name": "gross_profit",
            "unit": "亿元",
            "inherited_unit": "亿元",
            "recovered_unit": "亿元",
            "unit_repair_action": "NO_CHANGE",
            "value": "7.39",
            "sanitized_value": "7.39",
            "value_parse_status": "PARSED",
            "period": "2026E",
            "context_snippet": "<table><tr><td>毛利润(亿元）</td><td>7.39</td></tr></table>",
        },
    ]
    _write_json(
        dir_346b / "quality_limited_row_recovery_pilot_346b_manifest.json",
        {
            "decision": "QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY",
            "qa_fail_count": 0,
            "recovered_demo_candidate_count": 4,
            "needs_human_review_count": 0,
            "still_quality_limited_count": 0,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.json", recovered_rows)
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_context_injection_results.json", recovered_rows)
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_evidence_assisted_recovery_results.json", recovered_rows)
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_value_sanitizer_results.json", recovered_rows)
    _write_json(
        dir_346b / "quality_limited_row_recovery_pilot_346b_reaudit_summary.json",
        {"status_distribution": {"RECOVERED_DEMO_CANDIDATE": 4}},
    )
    return dir_346b


def _seed_346b2(root: Path) -> Path:
    dir_346b2 = root / "output" / "recovery_candidate_qa_audit_346b2"
    dir_346b2.mkdir(parents=True, exist_ok=True)
    audited_rows = [
        {
            "source_row_id": "row-ratio",
            "raw_metric_name": "EV/EBITDA",
            "demo_normalized_metric_name": "ev_to_ebitda",
            "metric_semantic_unit_class": "RATIO_MULTIPLE",
            "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
            "recovered_unit": "%",
            "safety_decision": "FALSE_POSITIVE_SUSPECT",
            "mismatch_type": "RATIO_MULTIPLE_UNIT_MISMATCH",
            "context_snippet": "<table><tr><td>EV/EBITDA</td><td>15.3</td></tr></table>",
        },
        {
            "source_row_id": "row-pct",
            "raw_metric_name": "EBITDA Margin",
            "demo_normalized_metric_name": "ebitda_margin",
            "metric_semantic_unit_class": "PERCENTAGE_OR_MARGIN",
            "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
            "recovered_unit": "%",
            "safety_decision": "SAFE_RECOVERED_DEMO_CANDIDATE",
            "context_snippet": "<table><tr><td>EBITDA Margin</td><td>18.2%</td></tr></table>",
        },
        {
            "source_row_id": "row-per-share",
            "raw_metric_name": "每股净资产",
            "demo_normalized_metric_name": "book_value_per_share",
            "metric_semantic_unit_class": "PER_SHARE",
            "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
            "recovered_unit": "%",
            "safety_decision": "FALSE_POSITIVE_SUSPECT",
            "mismatch_type": "PER_SHARE_UNIT_MISMATCH",
            "context_snippet": "<table><tr><td>每股净资产</td><td>8.59</td></tr></table>",
        },
        {
            "source_row_id": "row-money",
            "raw_metric_name": "毛利润(亿元）",
            "demo_normalized_metric_name": "gross_profit",
            "metric_semantic_unit_class": "MONETARY_AMOUNT",
            "unit_repair_action": "NO_CHANGE",
            "recovered_unit": "亿元",
            "safety_decision": "SAFE_RECOVERED_DEMO_CANDIDATE",
            "context_snippet": "<table><tr><td>毛利润(亿元）</td><td>7.39</td></tr></table>",
        },
    ]
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_manifest.json",
        {
            "decision": "RECOVERY_CANDIDATE_QA_AUDIT_346B2_READY",
            "qa_fail_count": 0,
            "safe_recovered_candidate_count": 2,
            "false_positive_suspect_count": 2,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b2 / "recovery_candidate_qa_audit_346b2_recovered_candidate_audit.json", audited_rows)
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_safe_recovered_candidates.json",
        [row for row in audited_rows if row["safety_decision"] == "SAFE_RECOVERED_DEMO_CANDIDATE"],
    )
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_false_positive_suspects.json",
        [row for row in audited_rows if row["safety_decision"] == "FALSE_POSITIVE_SUSPECT"],
    )
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_unit_repair_audit.json",
        [
            {
                "source_row_id": "row-ratio",
                "metric_semantic_unit_class": "RATIO_MULTIPLE",
                "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
            },
            {
                "source_row_id": "row-pct",
                "metric_semantic_unit_class": "PERCENTAGE_OR_MARGIN",
                "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
            },
            {
                "source_row_id": "row-per-share",
                "metric_semantic_unit_class": "PER_SHARE",
                "unit_repair_action": "UNIT_PERCENT_FROM_RATIO_CONTEXT",
            },
            {
                "source_row_id": "row-money",
                "metric_semantic_unit_class": "MONETARY_AMOUNT",
                "unit_repair_action": "NO_CHANGE",
            },
        ],
    )
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_metric_semantic_class_distribution.json",
        [
            {"metric_semantic_unit_class": "RATIO_MULTIPLE", "row_count": 1},
            {"metric_semantic_unit_class": "PERCENTAGE_OR_MARGIN", "row_count": 1},
            {"metric_semantic_unit_class": "PER_SHARE", "row_count": 1},
            {"metric_semantic_unit_class": "MONETARY_AMOUNT", "row_count": 1},
        ],
    )
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_expansion_readiness_report.json",
        {"safe_to_expand_recovery": False},
    )
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_reaudit_summary.json",
        {"safety_decision_distribution": {"SAFE_RECOVERED_DEMO_CANDIDATE": 2, "FALSE_POSITIVE_SUSPECT": 2}},
    )
    return dir_346b2


def test_346b3_runner_ready_and_refines_units() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, dir_346a, dir_346a2 = _seed_345d_346a_346a2(case_root)
        dir_346b = _seed_346b(case_root)
        dir_346b2 = _seed_346b2(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        output_dir = case_root / "output" / "recovery_rule_refinement_346b3"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_recovery_rule_refinement_346b3.py"),
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
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        manifest = json.loads((output_dir / "recovery_rule_refinement_346b3_manifest.json").read_text(encoding="utf-8"))
        rows = json.loads((output_dir / "recovery_rule_refinement_346b3_refined_candidates.json").read_text(encoding="utf-8"))
        by_id = {row["source_row_id"]: row for row in rows}
        assert manifest["decision"] == READY_DECISION_346B3
        assert manifest["qa_fail_count"] == 0
        assert manifest["refined_candidate_count"] == 4
        assert manifest["refined_safe_candidate_count"] == 3
        assert manifest["demoted_candidate_count"] == 1
        assert manifest["remaining_false_positive_suspect_count"] == 1
        assert manifest["safe_to_expand_recovery"] is False
        assert manifest["milestone_ledger_updated"] is True
        assert by_id["row-ratio"]["refined_unit"] == "x"
        assert by_id["row-ratio"]["refined_unit_repair_action"] == "UNIT_RATIO_MULTIPLE_X"
        assert by_id["row-pct"]["refined_unit"] == "%"
        assert by_id["row-per-share"]["refined_unit"] == ""
        assert by_id["row-per-share"]["refined_recovery_decision"] == "REFINED_DEMOTED_TO_HUMAN_REVIEW"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b3_build_function_flags_demoted_per_share_and_preserved_percentage() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, dir_346a, dir_346a2 = _seed_345d_346a_346a2(case_root)
        dir_346b = _seed_346b(case_root)
        dir_346b2 = _seed_346b2(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_recovery_rule_refinement_346b3(
            full_structured_demo_export_package_345d_dir=dir_345d,
            vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
            mineru_image_path_binding_fix_346a2_dir=dir_346a2,
            quality_limited_row_recovery_pilot_346b_dir=dir_346b,
            recovery_candidate_qa_audit_346b2_dir=dir_346b2,
            output_dir=case_root / "output" / "recovery_rule_refinement_346b3",
            repo_root=case_root,
            ledger_path=ledger_path,
        )
        rows = {row["source_row_id"]: row for row in artifacts["refined_candidate_rows"]}
        assert rows["row-ratio"]["semantic_metric_class"] == "RATIO_MULTIPLE"
        assert rows["row-ratio"]["refined_unit_repair_action"] == "UNIT_RATIO_MULTIPLE_X"
        assert rows["row-pct"]["semantic_metric_class"] == "PERCENTAGE_OR_MARGIN"
        assert rows["row-pct"]["refined_unit"] == "%"
        assert rows["row-per-share"]["semantic_metric_class"] == "PER_SHARE"
        assert rows["row-per-share"]["remaining_false_positive_suspect"] is True
        assert artifacts["manifest"]["safe_to_expand_recovery"] is False
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b3_missing_346b2_input_fails_clearly() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, dir_346a, dir_346a2 = _seed_345d_346a_346a2(case_root)
        dir_346b = _seed_346b(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        try:
            build_recovery_rule_refinement_346b3(
                full_structured_demo_export_package_345d_dir=dir_345d,
                vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
                mineru_image_path_binding_fix_346a2_dir=dir_346a2,
                quality_limited_row_recovery_pilot_346b_dir=dir_346b,
                recovery_candidate_qa_audit_346b2_dir=case_root / "missing_346b2",
                output_dir=case_root / "output" / "recovery_rule_refinement_346b3",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError as exc:
            assert "346B2 input directory missing" in str(exc)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
