from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.demo_export_review_qa_checklist_345e import (  # noqa: E402
    BLOCKED_DECISION_345E,
    READY_DECISION_345E,
    build_demo_export_review_qa_checklist_345e,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_demo_export_review_qa_checklist_345e"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345d_outputs(root: Path) -> Path:
    dir_345d = root / "output" / "full_structured_demo_export_package_345d"
    dir_345d.mkdir(parents=True, exist_ok=True)

    demo_rows = [
        {
            "demo_export_row_id": "345d::demo::00001",
            "source_row_id": "src::001",
            "source_pdf_name": "demo_a.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "1",
            "source_table_id": "table_001",
            "stage": "TRUSTED_CELL",
            "raw_metric_name": "Revenue",
            "demo_normalized_metric_name": "revenue",
            "normalization_source": "BASELINE_RULE",
            "alias_simulation_batch": "",
            "value": "100",
            "unit": "百万元",
            "period": "2024A",
            "currency": "CNY",
            "company_name": "Demo Co",
            "report_type": "Initiation",
            "quality_severity": "NONE",
            "quality_issue_codes": "",
            "source_trace_available": True,
            "demo_export_eligible": True,
            "demo_export_caveat_level": "LOW",
            "demo_export_caveats": "demo only",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
    ]
    quality_limited_rows = [
        {
            "demo_export_row_id": "345d::demo::00002",
            "source_row_id": "src::002",
            "source_pdf_name": "demo_a.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "2",
            "source_table_id": "table_001",
            "stage": "LONG_FORM_CELL",
            "raw_metric_name": "Alias First",
            "demo_normalized_metric_name": "profit_margin",
            "normalization_source": "SECOND_BATCH_SIMULATION",
            "alias_simulation_batch": "SECOND_BATCH",
            "value": "30",
            "unit": "",
            "period": "2024A",
            "currency": "CNY",
            "company_name": "Demo Co",
            "report_type": "Initiation",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "MISSING_UNIT|HUMAN_REVIEW_PENDING",
            "source_trace_available": True,
            "demo_export_eligible": False,
            "demo_export_caveat_level": "MEDIUM",
            "demo_export_caveats": "requires caveat",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
    ]
    excluded_rows = [
        {
            "demo_export_row_id": "345d::demo::00003",
            "source_row_id": "src::003",
            "source_pdf_name": "demo_b.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "3",
            "source_table_id": "table_002",
            "stage": "REJECTED_OR_EXCLUDED",
            "raw_metric_name": "Blind Spot",
            "demo_normalized_metric_name": "",
            "normalization_source": "",
            "alias_simulation_batch": "",
            "value": "50",
            "unit": "百万元",
            "period": "2025A",
            "currency": "CNY",
            "company_name": "Demo Co",
            "report_type": "Update",
            "quality_severity": "HIGH",
            "quality_issue_codes": "UNNORMALIZED_METRIC",
            "source_trace_available": True,
            "demo_export_eligible": False,
            "demo_export_caveat_level": "HIGH",
            "demo_export_caveats": "excluded",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "exclusion_reasons": "UNNORMALIZED_REMAINING_BLIND_SPOT",
        }
    ]
    remaining_blind_spots = [
        {"raw_metric_name": "Blind Spot", "remaining_row_count": 1, "remaining_ready_candidate_count": 0}
    ]
    alias_sidecar = [
        {
            "demo_export_row_id": "345d::demo::00002",
            "source_row_id": "src::002",
            "inventory_row_id": "inv::002",
            "quality_row_id": "q::002",
            "normalization_source": "SECOND_BATCH_SIMULATION",
            "alias_simulation_batch": "SECOND_BATCH",
            "baseline_normalized_metric_name": "",
            "first_batch_simulated_normalized_metric_name": "",
            "second_batch_simulated_normalized_metric_name": "profit_margin",
            "cumulative_simulated_normalized_metric_name": "profit_margin",
            "simulation_action": "SIMULATED_NORMALIZE",
            "simulation_rule_update_required": True,
            "simulation_only_no_write_back": True,
        }
    ]
    quality_caveats = {
        "remaining_unnormalized_raw_metric_name_count": 1,
        "remaining_unnormalized_metric_row_count": 1,
        "remaining_ready_candidate_count": 0,
        "missing_unit_count": 1,
        "missing_period_count": 0,
        "missing_source_trace_count": 0,
        "high_severity_issue_count": 1,
        "medium_severity_issue_count": 1,
        "rejected_or_excluded_count": 1,
        "rows_normalized_only_through_simulation_count": 1,
        "simulation_exact_match_limitation": "Exact-match alias-key simulation may miss unresolved alias-family variants.",
        "formal_export_and_production_gates_false": True,
        "quality_issue_counts": {
            "HUMAN_REVIEW_PENDING": 1,
            "MISSING_UNIT": 1,
            "UNNORMALIZED_METRIC": 1,
            "REVIEW_REQUIRED": 1,
            "STRICT_HUMAN_REVIEW_PENDING": 0,
        },
        "excluded_reason_counts": {"UNNORMALIZED_REMAINING_BLIND_SPOT": 1},
        "quality_limited_scope_policy": "Default 345D keeps MEDIUM quality severity rows in quality_limited_rows and leaves HIGH severity rows excluded unless --include-quality-limited-rows is passed.",
    }
    manifest = {
        "decision": "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY",
        "qa_fail_count": 0,
        "inventory_row_count": 3,
        "demo_export_row_count": 1,
        "quality_limited_row_count": 1,
        "excluded_row_count": 1,
        "coverage_ratio_before_alias_simulation": 0.4,
        "coverage_ratio_after_alias_simulation": 0.8,
        "remaining_unnormalized_raw_metric_name_count": 1,
        "remaining_unnormalized_metric_row_count": 1,
        "remaining_ready_candidate_count": 0,
        "high_severity_issue_count": 1,
        "medium_severity_issue_count": 1,
        "missing_unit_count": 1,
        "missing_period_count": 0,
        "missing_source_trace_count": 0,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_export_generated": False,
        "demo_export_only": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "next_recommended_step": "345E Demo Export Review / QA Checklist",
    }
    demo_export_summary = {
        "decision": "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY",
        "demo_export_row_count": 1,
        "quality_limited_row_count": 1,
        "excluded_row_count": 1,
        "coverage_ratio_before_alias_simulation": 0.4,
        "coverage_ratio_after_alias_simulation": 0.8,
        "alias_simulation_sidecar_row_count": 1,
        "remaining_blind_spot_count": 1,
    }

    _write_json(dir_345d / "full_structured_demo_export_package_345d_manifest.json", manifest)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_demo_rows.json", demo_rows)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_limited_rows.json", quality_limited_rows)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_excluded_rows.json", excluded_rows)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_remaining_blind_spots.json", remaining_blind_spots)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_alias_simulation_sidecar.json", alias_sidecar)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_caveats.json", quality_caveats)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_demo_export_summary.json", demo_export_summary)

    (dir_345d / "full_structured_demo_export_package_345d_demo_rows.csv").write_text(
        "demo_export_row_id,source_row_id,source_pdf_name,formal_client_export_allowed,client_ready,production_ready\r\n345d::demo::00001,src::001,demo_a.pdf,False,False,False\r\n",
        encoding="utf-8-sig",
    )
    (dir_345d / "full_structured_demo_export_package_345d_quality_limited_rows.csv").write_text(
        "demo_export_row_id,source_row_id,source_pdf_name,formal_client_export_allowed,client_ready,production_ready\r\n345d::demo::00002,src::002,demo_a.pdf,False,False,False\r\n",
        encoding="utf-8-sig",
    )
    (dir_345d / "full_structured_demo_export_package_345d_excluded_rows.csv").write_text(
        "demo_export_row_id,source_row_id,source_pdf_name,formal_client_export_allowed,client_ready,production_ready\r\n345d::demo::00003,src::003,demo_b.pdf,False,False,False\r\n",
        encoding="utf-8-sig",
    )
    (dir_345d / "full_structured_demo_export_package_345d_remaining_blind_spots.csv").write_text(
        "raw_metric_name,remaining_row_count,remaining_ready_candidate_count\r\nBlind Spot,1,0\r\n",
        encoding="utf-8-sig",
    )
    (dir_345d / "full_structured_demo_export_package_345d_alias_simulation_sidecar.csv").write_text(
        "demo_export_row_id,source_row_id,alias_simulation_batch,simulation_only_no_write_back\r\n345d::demo::00002,src::002,SECOND_BATCH,True\r\n",
        encoding="utf-8-sig",
    )
    (dir_345d / "full_structured_demo_export_package_345d_quality_caveats.md").write_text(
        "\n".join(
            [
                "# 345D Quality Caveats",
                "",
                "- remaining_unnormalized_raw_metric_name_count: 1",
                "- remaining_unnormalized_metric_row_count: 1",
                "- missing_unit_count: 1",
                "- missing_period_count: 0",
                "- missing_source_trace_count: 0",
                "- high_severity_issue_count: 1",
                "- medium_severity_issue_count: 1",
                "- high severity quality issues remain documented",
                "- medium severity quality issues remain documented",
                "- missing unit count remains documented",
                "- missing period count remains documented",
                "- missing source trace count remains documented",
                "- official rules were not modified",
                "- official alias assets were not modified",
                "- formal_client_export_allowed remains false.",
                "- client_ready remains false.",
                "- production_ready remains false.",
                "- simulation_exact_match_limitation: Exact-match alias-key simulation may miss unresolved alias-family variants.",
            ]
        ),
        encoding="utf-8",
    )
    (dir_345d / "full_structured_demo_export_package_345d_executive_summary.md").write_text("# summary\n", encoding="utf-8")
    (dir_345d / "full_structured_demo_export_package_345d_artifact_index.md").write_text("# index\n", encoding="utf-8")
    (dir_345d / "full_structured_demo_export_package_345d_next_plan.md").write_text("# next\n", encoding="utf-8")

    try:
        from openpyxl import Workbook

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "demo_rows"
        worksheet.append(list(demo_rows[0].keys()))
        worksheet.append(list(demo_rows[0].values()))
        workbook.save(dir_345d / "full_structured_demo_export_package_345d_demo_rows.xlsx")
    except Exception:
        pass

    return dir_345d


def test_345e_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d_outputs(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_demo_export_review_qa_checklist_345e(
            full_structured_demo_export_package_345d_dir=dir_345d,
            output_dir=case_root / "output" / "demo_export_review_qa_checklist_345e",
            repo_root=case_root,
            ledger_path=ledger_path,
            max_display_sample_rows=5,
            strict_artifact_check=False,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345E
        assert manifest["qa_fail_count"] == 0
        assert manifest["artifact_completeness_passed"] is True
        assert manifest["row_count_closure_passed"] is True
        assert manifest["gate_safety_check_passed"] is True
        assert manifest["caveat_completeness_passed"] is True
        assert manifest["presentation_ready_for_demo_only"] is True
        assert manifest["demo_export_row_count"] == 1
        assert manifest["quality_limited_row_count"] == 1
        assert manifest["excluded_row_count"] == 1
        assert manifest["sample_demo_row_count"] == 1
        assert manifest["sample_quality_limited_row_count"] == 1
        assert manifest["sample_excluded_row_count"] == 1
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        assert manifest["official_rules_modified"] is False
        assert manifest["official_alias_assets_modified"] is False
        assert manifest["no_write_back_proof_passed"] is True
        assert manifest["milestone_ledger_updated"] is True
        assert "## 345E Demo Export Review / QA Checklist" in ledger_path.read_text(encoding="utf-8")
        assert artifacts["sample_demo_rows_package"]["rows"][0]["demo_export_row_id"] == "345d::demo::00001"
        assert artifacts["demo_presentation_readiness"]["safe_for_demo_only"] is True
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345e_missing_required_inputs_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing"
        missing_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_demo_export_review_qa_checklist_345e(
                full_structured_demo_export_package_345d_dir=missing_dir,
                output_dir=case_root / "output" / "demo_export_review_qa_checklist_345e",
                repo_root=case_root,
                ledger_path=case_root / "ledger.md",
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345D inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
