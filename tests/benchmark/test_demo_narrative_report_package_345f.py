from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.demo_narrative_report_package_345f import (  # noqa: E402
    READY_DECISION_345F,
    build_demo_narrative_report_package_345f,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_demo_narrative_report_package_345f"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345d_outputs(root: Path) -> Path:
    dir_345d = root / "output" / "full_structured_demo_export_package_345d"
    dir_345d.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY",
        "qa_fail_count": 0,
        "demo_export_row_count": 109,
        "quality_limited_row_count": 5558,
        "excluded_row_count": 9121,
        "inventory_row_count": 14788,
        "coverage_ratio_before_alias_simulation": 0.452461,
        "coverage_ratio_after_alias_simulation": 0.684136,
        "baseline_normalized_demo_row_count": 109,
        "alias_simulated_demo_row_count": 1532,
        "remaining_unnormalized_raw_metric_name_count": 96,
        "remaining_unnormalized_metric_row_count": 4671,
        "high_severity_issue_count": 7595,
        "medium_severity_issue_count": 7084,
        "missing_unit_count": 838,
        "missing_period_count": 0,
        "missing_source_trace_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_export_generated": False,
        "demo_export_only": True,
    }
    summary = {
        "decision": "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY",
        "demo_export_row_count": 109,
        "quality_limited_row_count": 5558,
        "excluded_row_count": 9121,
        "coverage_ratio_before_alias_simulation": 0.452461,
        "coverage_ratio_after_alias_simulation": 0.684136,
    }
    quality_caveats = {
        "remaining_unnormalized_raw_metric_name_count": 96,
        "remaining_unnormalized_metric_row_count": 4671,
        "missing_unit_count": 838,
        "missing_period_count": 0,
        "missing_source_trace_count": 0,
        "high_severity_issue_count": 7595,
        "medium_severity_issue_count": 7084,
        "simulation_exact_match_limitation": "Exact-match alias-key simulation may miss unresolved alias-family variants.",
    }
    _write_json(dir_345d / "full_structured_demo_export_package_345d_manifest.json", manifest)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_demo_export_summary.json", summary)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_caveats.json", quality_caveats)
    (dir_345d / "full_structured_demo_export_package_345d_quality_caveats.md").write_text("# caveats\n", encoding="utf-8")
    (dir_345d / "full_structured_demo_export_package_345d_executive_summary.md").write_text("# summary\n", encoding="utf-8")
    (dir_345d / "full_structured_demo_export_package_345d_artifact_index.md").write_text("# index\n", encoding="utf-8")
    (dir_345d / "full_structured_demo_export_package_345d_next_plan.md").write_text("# next\n", encoding="utf-8")
    return dir_345d


def _seed_345e_outputs(root: Path) -> Path:
    dir_345e = root / "output" / "demo_export_review_qa_checklist_345e"
    dir_345e.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY",
        "qa_fail_count": 0,
        "row_count_closure_passed": True,
        "gate_safety_check_passed": True,
        "caveat_completeness_passed": True,
        "presentation_ready_for_demo_only": True,
        "checked_artifact_count": 18,
        "sample_demo_row_count": 3,
        "sample_quality_limited_row_count": 3,
        "sample_excluded_row_count": 3,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
    }
    row_reconciliation = [
        {"item": "inventory_total", "status": "PASS", "actual_count": 14788, "manifest_count": 14788}
    ]
    gate_safety = {"passed": True, "checks": [{"name": "manifest::client_ready", "status": "PASS"}]}
    caveat_completeness = {"passed": True, "missing_topics": [], "present_topics": ["remaining unnormalized metric rows"]}
    presentation = {
        "safe_for_demo_only": True,
        "recommended_first_files": ["demo_export_review_qa_checklist_345e_review_checklist.md"],
        "safe_sample_files": ["demo_export_review_qa_checklist_345e_sample_demo_rows.json"],
        "spoken_caveats": ["demo only"],
        "prohibited_claims": ["do not claim production-ready"],
    }
    demo_sample = {
        "source_artifact": "demo_rows",
        "source_path": "demo_rows.json",
        "sample_limit": 3,
        "selected_count": 3,
        "source_row_count": 3,
        "rows": [
            {"demo_export_row_id": "d1", "raw_metric_name": "Revenue", "period": "2024A", "value": "100", "formal_client_export_allowed": False, "client_ready": False, "production_ready": False},
            {"demo_export_row_id": "d2", "raw_metric_name": "Net Profit", "period": "2025A", "value": "90", "formal_client_export_allowed": False, "client_ready": False, "production_ready": False},
            {"demo_export_row_id": "d3", "raw_metric_name": "ROE", "period": "2026E", "value": "11", "formal_client_export_allowed": False, "client_ready": False, "production_ready": False},
        ],
    }
    quality_sample = {
        "source_artifact": "quality_rows",
        "source_path": "quality_rows.json",
        "sample_limit": 3,
        "selected_count": 3,
        "source_row_count": 3,
        "rows": [
            {"demo_export_row_id": "q1", "raw_metric_name": "Alias First", "period": "2024A", "value": "30", "formal_client_export_allowed": False, "client_ready": False, "production_ready": False},
            {"demo_export_row_id": "q2", "raw_metric_name": "Alias Second", "period": "2025A", "value": "40", "formal_client_export_allowed": False, "client_ready": False, "production_ready": False},
            {"demo_export_row_id": "q3", "raw_metric_name": "Alias Third", "period": "2026E", "value": "50", "formal_client_export_allowed": False, "client_ready": False, "production_ready": False},
        ],
    }
    excluded_sample = {
        "source_artifact": "excluded_rows",
        "source_path": "excluded_rows.json",
        "sample_limit": 3,
        "selected_count": 3,
        "source_row_count": 3,
        "rows": [
            {"demo_export_row_id": "x1", "raw_metric_name": "Blind Spot A", "period": "2024A", "value": "10", "formal_client_export_allowed": False, "client_ready": False, "production_ready": False},
            {"demo_export_row_id": "x2", "raw_metric_name": "Blind Spot B", "period": "2025A", "value": "20", "formal_client_export_allowed": False, "client_ready": False, "production_ready": False},
            {"demo_export_row_id": "x3", "raw_metric_name": "Blind Spot C", "period": "2026E", "value": "30", "formal_client_export_allowed": False, "client_ready": False, "production_ready": False},
        ],
    }

    _write_json(dir_345e / "demo_export_review_qa_checklist_345e_manifest.json", manifest)
    (dir_345e / "demo_export_review_qa_checklist_345e_review_checklist.md").write_text("# checklist\n", encoding="utf-8")
    _write_json(dir_345e / "demo_export_review_qa_checklist_345e_demo_presentation_readiness.json", presentation)
    _write_json(dir_345e / "demo_export_review_qa_checklist_345e_row_count_reconciliation.json", row_reconciliation)
    (dir_345e / "demo_export_review_qa_checklist_345e_row_count_reconciliation.csv").write_text("item,status\ninventory_total,PASS\n", encoding="utf-8-sig")
    _write_json(dir_345e / "demo_export_review_qa_checklist_345e_gate_safety_check.json", gate_safety)
    _write_json(dir_345e / "demo_export_review_qa_checklist_345e_caveat_completeness_check.json", caveat_completeness)
    _write_json(dir_345e / "demo_export_review_qa_checklist_345e_sample_demo_rows.json", demo_sample)
    _write_json(dir_345e / "demo_export_review_qa_checklist_345e_quality_limited_sample_rows.json", quality_sample)
    _write_json(dir_345e / "demo_export_review_qa_checklist_345e_excluded_sample_rows.json", excluded_sample)
    (dir_345e / "demo_export_review_qa_checklist_345e_sample_demo_rows.csv").write_text("demo_export_row_id\n", encoding="utf-8-sig")
    (dir_345e / "demo_export_review_qa_checklist_345e_quality_limited_sample_rows.csv").write_text("demo_export_row_id\n", encoding="utf-8-sig")
    (dir_345e / "demo_export_review_qa_checklist_345e_excluded_sample_rows.csv").write_text("demo_export_row_id\n", encoding="utf-8-sig")
    (dir_345e / "demo_export_review_qa_checklist_345e_executive_summary.md").write_text("# summary\n", encoding="utf-8")
    (dir_345e / "demo_export_review_qa_checklist_345e_artifact_index.md").write_text("# index\n", encoding="utf-8")
    (dir_345e / "demo_export_review_qa_checklist_345e_next_plan.md").write_text("# next\n", encoding="utf-8")
    return dir_345e


def test_345f_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d_outputs(case_root)
        dir_345e = _seed_345e_outputs(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_demo_narrative_report_package_345f(
            full_structured_demo_export_package_345d_dir=dir_345d,
            demo_export_review_qa_checklist_345e_dir=dir_345e,
            output_dir=case_root / "output" / "demo_narrative_report_package_345f",
            repo_root=case_root,
            ledger_path=ledger_path,
            max_sample_rows_in_report=7,
            audiences=["teacher", "team"],
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345F
        assert manifest["qa_fail_count"] == 0
        assert manifest["generated_report_count"] == 10
        assert manifest["sample_rows_for_story_count"] == 7
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        assert manifest["official_rules_modified"] is False
        assert manifest["official_alias_assets_modified"] is False
        assert manifest["formal_export_generated"] is False
        assert manifest["demo_export_only"] is True
        assert manifest["milestone_ledger_updated"] is True
        assert "345F Stakeholder Report" in artifacts["stakeholder_report_md"]
        assert "Allowed Vs Forbidden" in artifacts["claims_allowed_vs_forbidden_md"]
        assert artifacts["sample_rows_for_story_json"]["rows"][0]["demo_export_row_id"] == "d1"
        assert len(artifacts["metrics_summary_rows"]) >= 10
        assert "## 345F Demo Narrative Report Package" in ledger_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345f_missing_required_inputs_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing"
        missing_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_demo_narrative_report_package_345f(
                full_structured_demo_export_package_345d_dir=missing_dir,
                demo_export_review_qa_checklist_345e_dir=missing_dir,
                output_dir=case_root / "output" / "demo_narrative_report_package_345f",
                repo_root=case_root,
                ledger_path=case_root / "ledger.md",
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345D/345E inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
