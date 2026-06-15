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

from datefac.benchmark.controlled_quality_limited_recovery_expansion_346b4 import (  # noqa: E402
    READY_DECISION_346B4,
    SAFE_DECISION,
    build_controlled_quality_limited_recovery_expansion_346b4,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_t_346b4"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345d(root: Path) -> tuple[Path, list[dict], list[dict]]:
    dir_345d = root / "output" / "full_structured_demo_export_package_345d"
    dir_345d.mkdir(parents=True, exist_ok=True)
    quality_rows = [
        {
            "demo_export_row_id": "345d::ql::0001",
            "source_row_id": "row-ratio",
            "source_pdf_name": "demo.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "1",
            "source_table_id": "tbl-1",
            "stage": "LONG_FORM_CELL",
            "raw_metric_name": "EV/EBITDA",
            "demo_normalized_metric_name": "ev_to_ebitda",
            "normalization_source": "SECOND_BATCH_ALIAS_SIMULATION_345C11",
            "alias_simulation_batch": "SECOND_BATCH",
            "value": "15.3",
            "unit": "",
            "period": "2024A",
            "currency": "",
            "company_name": "",
            "report_type": "",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "MISSING_UNIT|UNNORMALIZED_METRIC|HUMAN_REVIEW_PENDING",
            "source_trace_available": True,
            "demo_export_eligible": True,
            "demo_export_caveat_level": "MEDIUM",
            "demo_export_caveats": "HUMAN_REVIEW_PENDING|MISSING_UNIT",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
        {
            "demo_export_row_id": "345d::ql::0002",
            "source_row_id": "row-pct",
            "source_pdf_name": "demo.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "1",
            "source_table_id": "tbl-1",
            "stage": "LONG_FORM_CELL",
            "raw_metric_name": "EBITDA Margin",
            "demo_normalized_metric_name": "ebitda_margin",
            "normalization_source": "FIRST_BATCH_ALIAS_SIMULATION_345C6",
            "alias_simulation_batch": "FIRST_BATCH",
            "value": "18.2",
            "unit": "",
            "period": "2024A",
            "currency": "",
            "company_name": "",
            "report_type": "",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "MISSING_UNIT|UNNORMALIZED_METRIC|HUMAN_REVIEW_PENDING",
            "source_trace_available": True,
            "demo_export_eligible": True,
            "demo_export_caveat_level": "MEDIUM",
            "demo_export_caveats": "HUMAN_REVIEW_PENDING|MISSING_UNIT",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
        {
            "demo_export_row_id": "345d::ql::0003",
            "source_row_id": "row-money",
            "source_pdf_name": "demo.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "2",
            "source_table_id": "tbl-2",
            "stage": "LONG_FORM_CELL",
            "raw_metric_name": "营业收入（百万元）",
            "demo_normalized_metric_name": "revenue",
            "normalization_source": "BASELINE_345C",
            "alias_simulation_batch": "NONE",
            "value": "17341.0",
            "unit": "",
            "period": "2024A",
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
        },
        {
            "demo_export_row_id": "345d::ql::0004",
            "source_row_id": "row-per-share",
            "source_pdf_name": "demo.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "3",
            "source_table_id": "tbl-3",
            "stage": "LONG_FORM_CELL",
            "raw_metric_name": "每股净资产",
            "demo_normalized_metric_name": "book_value_per_share",
            "normalization_source": "SECOND_BATCH_ALIAS_SIMULATION_345C11",
            "alias_simulation_batch": "SECOND_BATCH",
            "value": "8.59",
            "unit": "",
            "period": "2024A",
            "currency": "",
            "company_name": "",
            "report_type": "",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "MISSING_UNIT|UNNORMALIZED_METRIC|HUMAN_REVIEW_PENDING",
            "source_trace_available": True,
            "demo_export_eligible": True,
            "demo_export_caveat_level": "MEDIUM",
            "demo_export_caveats": "HUMAN_REVIEW_PENDING|MISSING_UNIT",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
        {
            "demo_export_row_id": "345d::ql::0005",
            "source_row_id": "row-unknown",
            "source_pdf_name": "demo.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "3",
            "source_table_id": "tbl-3",
            "stage": "LONG_FORM_CELL",
            "raw_metric_name": "Mystery Metric",
            "demo_normalized_metric_name": "",
            "normalization_source": "NONE",
            "alias_simulation_batch": "NONE",
            "value": "3.14",
            "unit": "",
            "period": "2024A",
            "currency": "",
            "company_name": "",
            "report_type": "",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "UNNORMALIZED_METRIC|HUMAN_REVIEW_PENDING",
            "source_trace_available": True,
            "demo_export_eligible": True,
            "demo_export_caveat_level": "MEDIUM",
            "demo_export_caveats": "HUMAN_REVIEW_PENDING|UNNORMALIZED_METRIC",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
        {
            "demo_export_row_id": "345d::ql::0006",
            "source_row_id": "row-pilot",
            "source_pdf_name": "demo.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "4",
            "source_table_id": "tbl-4",
            "stage": "LONG_FORM_CELL",
            "raw_metric_name": "EV/EBITDA",
            "demo_normalized_metric_name": "ev_to_ebitda",
            "normalization_source": "SECOND_BATCH_ALIAS_SIMULATION_345C11",
            "alias_simulation_batch": "SECOND_BATCH",
            "value": "10.2",
            "unit": "",
            "period": "2024A",
            "currency": "",
            "company_name": "",
            "report_type": "",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "MISSING_UNIT|UNNORMALIZED_METRIC|HUMAN_REVIEW_PENDING",
            "source_trace_available": True,
            "demo_export_eligible": True,
            "demo_export_caveat_level": "MEDIUM",
            "demo_export_caveats": "HUMAN_REVIEW_PENDING|MISSING_UNIT",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    ]
    demo_rows = [
        {
            "demo_export_row_id": "345d::demo::0001",
            "source_row_id": "row-demo",
            "stage": "TRUSTED_CELL",
            "raw_metric_name": "Revenue",
            "demo_normalized_metric_name": "revenue",
            "value": "100",
            "unit": "百万元",
            "period": "2024A",
        }
    ]
    _write_json(
        dir_345d / "full_structured_demo_export_package_345d_manifest.json",
        {
            "decision": "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY",
            "qa_fail_count": 0,
            "quality_limited_row_count": len(quality_rows),
            "demo_export_row_count": len(demo_rows),
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_limited_rows.json", quality_rows)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_demo_rows.json", demo_rows)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_caveats.json", [{"issue": "demo"}])
    return dir_345d, quality_rows, demo_rows


def _seed_346a(root: Path, quality_rows: list[dict]) -> Path:
    dir_346a = root / "output" / "vision_assisted_table_evidence_pilot_346a"
    dir_346a.mkdir(parents=True, exist_ok=True)
    pool_rows = []
    for idx, row in enumerate(quality_rows, start=1):
        pool_rows.append(
            {
                **row,
                "candidate_row_id": f"346a::candidate::{idx:04d}",
                "priority_score": 175 if row["source_row_id"] in {"row-ratio", "row-pct", "row-per-share"} else 115,
                "raw_metric_repeat_count": 20 - idx,
                "requires_image_evidence": True,
                "selection_reason": "MEDIUM_SEVERITY;UNIT_REPAIR_TARGET;VALUE_ALIGNMENT_CHECK_TARGET",
                "target_field_types": ["unit", "value"],
                "source_page_number": idx,
                "vision_task_type": "HEADER_AND_VALUE_ALIGNMENT_CHECK",
            }
        )
    _write_json(
        dir_346a / "vision_assisted_table_evidence_pilot_346a_manifest.json",
        {
            "decision": "VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY",
            "qa_fail_count": 0,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346a / "vision_assisted_table_evidence_pilot_346a_candidate_pool.json", pool_rows)
    _write_json(dir_346a / "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json", [pool_rows[-1]])
    return dir_346a


def _seed_346a2(root: Path) -> Path:
    dir_346a2 = root / "output" / "mineru_image_path_binding_fix_346a2"
    dir_346a2.mkdir(parents=True, exist_ok=True)
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
            {
                "source_row_id": "row-pilot",
                "image_bound": True,
                "image_evidence_type": "TABLE_CROP_IMAGE",
            }
        ],
    )
    return dir_346a2


def _seed_346b(root: Path, quality_rows: list[dict]) -> Path:
    dir_346b = root / "output" / "quality_limited_row_recovery_pilot_346b"
    dir_346b.mkdir(parents=True, exist_ok=True)
    pilot_row = next(row for row in quality_rows if row["source_row_id"] == "row-pilot")
    _write_json(
        dir_346b / "quality_limited_row_recovery_pilot_346b_manifest.json",
        {
            "decision": "QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_READY",
            "qa_fail_count": 0,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_input_rows.json", [pilot_row])
    _write_json(dir_346b / "quality_limited_row_recovery_pilot_346b_recovered_demo_candidates.json", [pilot_row])
    return dir_346b


def _seed_346b2(root: Path) -> Path:
    dir_346b2 = root / "output" / "recovery_candidate_qa_audit_346b2"
    dir_346b2.mkdir(parents=True, exist_ok=True)
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
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_false_positive_suspects.json",
        [
            {
                "source_row_id": "row-ratio",
                "mismatch_type": "RATIO_MULTIPLE_UNIT_MISMATCH",
            }
        ],
    )
    _write_json(
        dir_346b2 / "recovery_candidate_qa_audit_346b2_unit_repair_audit.json",
        [{"source_row_id": "row-ratio", "metric_semantic_unit_class": "RATIO_MULTIPLE"}],
    )
    return dir_346b2


def _seed_346b3(root: Path) -> Path:
    dir_346b3 = root / "output" / "recovery_rule_refinement_346b3"
    dir_346b3.mkdir(parents=True, exist_ok=True)
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_manifest.json",
        {
            "decision": "RECOVERY_RULE_REFINEMENT_346B3_READY",
            "qa_fail_count": 0,
            "live_vlm_call_count": 0,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    )
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_refined_unit_policy.json",
        {"semantic_unit_policy_applied": True},
    )
    _write_json(dir_346b3 / "recovery_rule_refinement_346b3_rule_change_log.json", [{"change_id": "rule-1"}])
    _write_json(
        dir_346b3 / "recovery_rule_refinement_346b3_refined_safe_candidates.json",
        [{"source_row_id": "row-ratio"}],
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
    _write_json(dir_346b2r / "refined_recovery_candidate_qa_reaudit_346b2r_safe_candidates.json", [{"source_row_id": "row-ratio"}])
    _write_json(dir_346b2r / "refined_recovery_candidate_qa_reaudit_346b2r_candidate_reaudit.json", [{"source_row_id": "row-ratio"}])
    _write_json(
        dir_346b2r / "refined_recovery_candidate_qa_reaudit_346b2r_expansion_readiness_report.json",
        {
            "safe_to_expand_recovery": True,
            "controlled_max_row_limit_suggestion": 500,
        },
    )
    return dir_346b2r


def test_346b4_runner_ready_and_excludes_demo_and_pilot() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, quality_rows, _ = _seed_345d(case_root)
        dir_346a = _seed_346a(case_root, quality_rows)
        dir_346a2 = _seed_346a2(case_root)
        dir_346b = _seed_346b(case_root, quality_rows)
        dir_346b2 = _seed_346b2(case_root)
        dir_346b3 = _seed_346b3(case_root)
        dir_346b2r = _seed_346b2r(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_椤圭洰杩涚▼.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        output_dir = case_root / "output" / "controlled_quality_limited_recovery_expansion_346b4"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_controlled_quality_limited_recovery_expansion_346b4.py"),
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
            "--refined-recovery-candidate-qa-reaudit-346b2r-dir",
            str(dir_346b2r),
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
            "--max-expansion-rows",
            "5",
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        manifest = json.loads((output_dir / "controlled_quality_limited_recovery_expansion_346b4_manifest.json").read_text(encoding="utf-8"))
        assert manifest["decision"] == READY_DECISION_346B4
        assert manifest["qa_fail_count"] == 0
        assert manifest["controlled_expansion_input_row_count"] == 5
        assert manifest["already_demo_ready_row_touched_count"] == 0
        assert manifest["already_346b_pilot_row_count"] == 0
        assert manifest["safe_recovered_candidate_count"] == 3
        assert manifest["needs_human_review_count"] == 1
        assert manifest["needs_rule_refinement_count"] == 1
        assert manifest["false_positive_guardrail_hit_count"] == 0
        assert manifest["recovered_candidate_count"] == 3
        assert manifest["unit_semantic_mismatch_count"] == 0

        selected_rows = json.loads((output_dir / "controlled_quality_limited_recovery_expansion_346b4_selected_rows.json").read_text(encoding="utf-8"))
        assert {row["source_row_id"] for row in selected_rows} == {"row-ratio", "row-pct", "row-money", "row-per-share", "row-unknown"}
        assert "row-pilot" not in {row["source_row_id"] for row in selected_rows}

        recovered_rows = json.loads((output_dir / "controlled_quality_limited_recovery_expansion_346b4_recovery_results.json").read_text(encoding="utf-8"))
        ratio_row = next(row for row in recovered_rows if row["source_row_id"] == "row-ratio")
        pct_row = next(row for row in recovered_rows if row["source_row_id"] == "row-pct")
        per_share_row = next(row for row in recovered_rows if row["source_row_id"] == "row-per-share")
        assert ratio_row["controlled_recovery_decision"] == SAFE_DECISION
        assert ratio_row["controlled_recovered_unit"] == "x"
        assert pct_row["controlled_recovery_decision"] == SAFE_DECISION
        assert pct_row["controlled_recovered_unit"] == "%"
        assert per_share_row["controlled_recovery_decision"] == "CONTROLLED_NEEDS_HUMAN_REVIEW"
        assert "346B4 Controlled Quality-Limited Recovery Expansion" in ledger_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b4_requires_safe_346b2r_gate() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, quality_rows, _ = _seed_345d(case_root)
        dir_346a = _seed_346a(case_root, quality_rows)
        dir_346a2 = _seed_346a2(case_root)
        dir_346b = _seed_346b(case_root, quality_rows)
        dir_346b2 = _seed_346b2(case_root)
        dir_346b3 = _seed_346b3(case_root)
        dir_346b2r = _seed_346b2r(case_root)
        _write_json(
            dir_346b2r / "refined_recovery_candidate_qa_reaudit_346b2r_manifest.json",
            {
                "decision": "REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_READY",
                "qa_fail_count": 0,
                "safe_to_expand_recovery": False,
                "live_vlm_call_count": 0,
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
            },
        )
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_椤圭洰杩涚▼.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        try:
            build_controlled_quality_limited_recovery_expansion_346b4(
                full_structured_demo_export_package_345d_dir=dir_345d,
                vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
                mineru_image_path_binding_fix_346a2_dir=dir_346a2,
                quality_limited_row_recovery_pilot_346b_dir=dir_346b,
                recovery_candidate_qa_audit_346b2_dir=dir_346b2,
                recovery_rule_refinement_346b3_dir=dir_346b3,
                refined_recovery_candidate_qa_reaudit_346b2r_dir=dir_346b2r,
                output_dir=case_root / "output" / "controlled_quality_limited_recovery_expansion_346b4",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert "safe_to_expand_recovery" in str(exc)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b4_missing_346b3_input_fails_clearly() -> None:
    case_root = _make_case_root()
    try:
        dir_345d, quality_rows, _ = _seed_345d(case_root)
        dir_346a = _seed_346a(case_root, quality_rows)
        dir_346a2 = _seed_346a2(case_root)
        dir_346b = _seed_346b(case_root, quality_rows)
        dir_346b2 = _seed_346b2(case_root)
        dir_346b2r = _seed_346b2r(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_椤圭洰杩涚▼.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        try:
            build_controlled_quality_limited_recovery_expansion_346b4(
                full_structured_demo_export_package_345d_dir=dir_345d,
                vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
                mineru_image_path_binding_fix_346a2_dir=dir_346a2,
                quality_limited_row_recovery_pilot_346b_dir=dir_346b,
                recovery_candidate_qa_audit_346b2_dir=dir_346b2,
                recovery_rule_refinement_346b3_dir=case_root / "missing_346b3",
                refined_recovery_candidate_qa_reaudit_346b2r_dir=dir_346b2r,
                output_dir=case_root / "output" / "controlled_quality_limited_recovery_expansion_346b4",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError as exc:
            assert "346B3 input directory missing" in str(exc)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
