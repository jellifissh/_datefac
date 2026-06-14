from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.full_structured_demo_export_package_345d import (  # noqa: E402
    READY_DECISION_345D,
    build_full_structured_demo_export_package_345d,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_full_structured_demo_export_package_345d"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345a_outputs(root: Path) -> Path:
    dir_345a = root / "output" / "full_structured_data_inventory_345a"
    dir_345a.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "inventory_row_id": "inv::001",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_stage": "LONG_FORM_CELL",
            "source_row_id": "src::001",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "table_id": "table_001",
            "row_index": "1",
            "column_name": "",
            "metric_name": "Revenue",
            "normalized_metric_name": "revenue",
            "value_raw": "100",
            "value_normalized": "100.0",
            "unit": "百万元",
            "period": "2024A",
            "source_page": "1",
            "confidence": "HIGH",
            "trust_status": "TRUSTED",
            "review_status": "TRUSTED_CELL",
            "human_review_status": "NOT_REVIEWED",
            "is_metric_candidate": True,
            "is_normalized_metric": True,
            "is_downstream_ready_candidate": True,
            "missing_required_field_count": 0,
            "missing_required_fields": "",
        },
        {
            "inventory_row_id": "inv::002",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_stage": "LONG_FORM_CELL",
            "source_row_id": "src::002",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "table_id": "table_001",
            "row_index": "2",
            "column_name": "",
            "metric_name": "Alias First",
            "normalized_metric_name": "",
            "value_raw": "90",
            "value_normalized": "90.0",
            "unit": "",
            "period": "2024A",
            "source_page": "2",
            "confidence": "MEDIUM",
            "trust_status": "LONG_FORM",
            "review_status": "LONG_FORM_CELL",
            "human_review_status": "NOT_REVIEWED",
            "is_metric_candidate": True,
            "is_normalized_metric": False,
            "is_downstream_ready_candidate": True,
            "missing_required_field_count": 1,
            "missing_required_fields": "unit",
        },
        {
            "inventory_row_id": "inv::003",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_stage": "LONG_FORM_CELL",
            "source_row_id": "src::003",
            "pdf_id": "pdf_002",
            "pdf_name": "demo_b.pdf",
            "table_id": "table_002",
            "row_index": "3",
            "column_name": "",
            "metric_name": "Alias Second",
            "normalized_metric_name": "",
            "value_raw": "80",
            "value_normalized": "80.0",
            "unit": "百万元",
            "period": "2025A",
            "source_page": "3",
            "confidence": "MEDIUM",
            "trust_status": "LONG_FORM",
            "review_status": "LONG_FORM_CELL",
            "human_review_status": "NOT_REVIEWED",
            "is_metric_candidate": True,
            "is_normalized_metric": False,
            "is_downstream_ready_candidate": True,
            "missing_required_field_count": 0,
            "missing_required_fields": "",
        },
        {
            "inventory_row_id": "inv::004",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_stage": "REJECTED_OR_EXCLUDED",
            "source_row_id": "src::004",
            "pdf_id": "pdf_003",
            "pdf_name": "demo_c.pdf",
            "table_id": "table_003",
            "row_index": "4",
            "column_name": "",
            "metric_name": "Rejected",
            "normalized_metric_name": "rejected_metric",
            "value_raw": "70",
            "value_normalized": "70.0",
            "unit": "百万元",
            "period": "2024A",
            "source_page": "4",
            "confidence": "LOW",
            "trust_status": "REJECTED",
            "review_status": "REJECTED_OR_EXCLUDED",
            "human_review_status": "NOT_REVIEWED",
            "is_metric_candidate": True,
            "is_normalized_metric": True,
            "is_downstream_ready_candidate": False,
            "missing_required_field_count": 0,
            "missing_required_fields": "",
        },
        {
            "inventory_row_id": "inv::005",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_stage": "LONG_FORM_CELL",
            "source_row_id": "src::005",
            "pdf_id": "pdf_004",
            "pdf_name": "demo_d.pdf",
            "table_id": "table_004",
            "row_index": "5",
            "column_name": "",
            "metric_name": "Still Blind",
            "normalized_metric_name": "",
            "value_raw": "60",
            "value_normalized": "60.0",
            "unit": "百万元",
            "period": "2026A",
            "source_page": "5",
            "confidence": "LOW",
            "trust_status": "LONG_FORM",
            "review_status": "LONG_FORM_CELL",
            "human_review_status": "NOT_REVIEWED",
            "is_metric_candidate": True,
            "is_normalized_metric": False,
            "is_downstream_ready_candidate": False,
            "missing_required_field_count": 0,
            "missing_required_fields": "",
        },
    ]
    manifest = {
        "decision": "FULL_STRUCTURED_DATA_INVENTORY_345A_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "total_inventory_row_count": 5,
        "downstream_ready_candidate_count": 4,
    }
    stage_summary = [
        {"source_stage": "LONG_FORM_CELL", "row_count": 4},
        {"source_stage": "REJECTED_OR_EXCLUDED", "row_count": 1},
    ]
    _write_json(dir_345a / "full_structured_data_inventory_345a_manifest.json", manifest)
    _write_json(dir_345a / "full_structured_data_inventory_345a_row_inventory.json", rows)
    _write_json(dir_345a / "full_structured_data_inventory_345a_stage_status_summary.json", stage_summary)
    (dir_345a / "full_structured_data_inventory_345a_row_inventory.csv").write_text("stub\n", encoding="utf-8")
    return dir_345a


def _seed_345b_outputs(root: Path) -> Path:
    dir_345b = root / "output" / "full_extraction_quality_audit_345b"
    dir_345b.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "quality_row_id": "q::001",
            "inventory_row_id": "inv::001",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_stage": "LONG_FORM_CELL",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "table_id": "table_001",
            "metric_name": "Revenue",
            "normalized_metric_name": "revenue",
            "value_raw": "100",
            "value_normalized": "100.0",
            "unit": "百万元",
            "period": "2024A",
            "source_page": "1",
            "trust_status": "TRUSTED",
            "review_status": "TRUSTED_CELL",
            "human_review_status": "NOT_REVIEWED",
            "missing_required_fields": "",
            "has_metric_name": True,
            "has_value": True,
            "has_unit": True,
            "has_period": True,
            "has_source_trace": True,
            "is_rejected_or_excluded": False,
            "is_downstream_ready_candidate": True,
            "quality_issue_count": 0,
            "quality_issues": "",
            "quality_severity": "NONE",
            "recommended_action": "KEEP",
        },
        {
            "quality_row_id": "q::002",
            "inventory_row_id": "inv::002",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_stage": "LONG_FORM_CELL",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "table_id": "table_001",
            "metric_name": "Alias First",
            "normalized_metric_name": "",
            "value_raw": "90",
            "value_normalized": "90.0",
            "unit": "",
            "period": "2024A",
            "source_page": "2",
            "trust_status": "LONG_FORM",
            "review_status": "LONG_FORM_CELL",
            "human_review_status": "NOT_REVIEWED",
            "missing_required_fields": "unit",
            "has_metric_name": True,
            "has_value": True,
            "has_unit": False,
            "has_period": True,
            "has_source_trace": True,
            "is_rejected_or_excluded": False,
            "is_downstream_ready_candidate": True,
            "quality_issue_count": 2,
            "quality_issues": "MISSING_UNIT|HUMAN_REVIEW_PENDING",
            "quality_severity": "MEDIUM",
            "recommended_action": "WAIT_FOR_HUMAN_REVIEW",
        },
        {
            "quality_row_id": "q::003",
            "inventory_row_id": "inv::003",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_stage": "LONG_FORM_CELL",
            "pdf_id": "pdf_002",
            "pdf_name": "demo_b.pdf",
            "table_id": "table_002",
            "metric_name": "Alias Second",
            "normalized_metric_name": "",
            "value_raw": "80",
            "value_normalized": "80.0",
            "unit": "百万元",
            "period": "2025A",
            "source_page": "",
            "trust_status": "LONG_FORM",
            "review_status": "LONG_FORM_CELL",
            "human_review_status": "NOT_REVIEWED",
            "missing_required_fields": "source_page",
            "has_metric_name": True,
            "has_value": True,
            "has_unit": True,
            "has_period": True,
            "has_source_trace": False,
            "is_rejected_or_excluded": False,
            "is_downstream_ready_candidate": True,
            "quality_issue_count": 2,
            "quality_issues": "MISSING_SOURCE_TRACE|HUMAN_REVIEW_PENDING",
            "quality_severity": "HIGH",
            "recommended_action": "FIX_SOURCE_TRACE",
        },
        {
            "quality_row_id": "q::004",
            "inventory_row_id": "inv::004",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_stage": "REJECTED_OR_EXCLUDED",
            "pdf_id": "pdf_003",
            "pdf_name": "demo_c.pdf",
            "table_id": "table_003",
            "metric_name": "Rejected",
            "normalized_metric_name": "rejected_metric",
            "value_raw": "70",
            "value_normalized": "70.0",
            "unit": "百万元",
            "period": "2024A",
            "source_page": "4",
            "trust_status": "REJECTED",
            "review_status": "REJECTED_OR_EXCLUDED",
            "human_review_status": "NOT_REVIEWED",
            "missing_required_fields": "",
            "has_metric_name": True,
            "has_value": True,
            "has_unit": True,
            "has_period": True,
            "has_source_trace": True,
            "is_rejected_or_excluded": True,
            "is_downstream_ready_candidate": False,
            "quality_issue_count": 1,
            "quality_issues": "REJECTED_OR_EXCLUDED",
            "quality_severity": "HIGH",
            "recommended_action": "EXCLUDE",
        },
        {
            "quality_row_id": "q::005",
            "inventory_row_id": "inv::005",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_stage": "LONG_FORM_CELL",
            "pdf_id": "pdf_004",
            "pdf_name": "demo_d.pdf",
            "table_id": "table_004",
            "metric_name": "Still Blind",
            "normalized_metric_name": "",
            "value_raw": "60",
            "value_normalized": "60.0",
            "unit": "百万元",
            "period": "2026A",
            "source_page": "5",
            "trust_status": "LONG_FORM",
            "review_status": "LONG_FORM_CELL",
            "human_review_status": "NOT_REVIEWED",
            "missing_required_fields": "",
            "has_metric_name": True,
            "has_value": True,
            "has_unit": True,
            "has_period": True,
            "has_source_trace": True,
            "is_rejected_or_excluded": False,
            "is_downstream_ready_candidate": False,
            "quality_issue_count": 1,
            "quality_issues": "UNNORMALIZED_METRIC",
            "quality_severity": "HIGH",
            "recommended_action": "NEEDS_ALIAS_REVIEW",
        },
    ]
    manifest = {
        "decision": "FULL_EXTRACTION_QUALITY_AUDIT_345B_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "input_inventory_row_count": 5,
        "audited_row_count": 5,
        "high_severity_issue_count": 3,
        "medium_severity_issue_count": 1,
        "ready_candidate_count_after_quality_audit": 1,
    }
    _write_json(dir_345b / "full_extraction_quality_audit_345b_manifest.json", manifest)
    _write_json(dir_345b / "full_extraction_quality_audit_345b_quality_rows.json", rows)
    _write_json(dir_345b / "full_extraction_quality_audit_345b_priority_fix_queue.json", rows)
    _write_json(
        dir_345b / "full_extraction_quality_audit_345b_missing_field_hotspots.json",
        [{"source_stage": "LONG_FORM_CELL", "missing_unit_count": 1, "missing_period_count": 0, "missing_source_page_count": 1}],
    )
    (dir_345b / "full_extraction_quality_audit_345b_quality_rows.csv").write_text("stub\n", encoding="utf-8")
    return dir_345b


def _seed_345c_outputs(root: Path) -> Path:
    dir_345c = root / "output" / "metric_candidate_normalization_coverage_345c"
    dir_345c.mkdir(parents=True, exist_ok=True)
    rows = [
        {"inventory_row_id": "inv::001", "metric_coverage_row_id": "mc::001"},
        {"inventory_row_id": "inv::002", "metric_coverage_row_id": "mc::002"},
        {"inventory_row_id": "inv::003", "metric_coverage_row_id": "mc::003"},
        {"inventory_row_id": "inv::004", "metric_coverage_row_id": "mc::004"},
        {"inventory_row_id": "inv::005", "metric_coverage_row_id": "mc::005"},
    ]
    manifest = {
        "decision": "METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "metric_candidate_row_count": 5,
        "normalized_metric_row_count": 2,
        "normalization_coverage_ratio": 0.4,
    }
    _write_json(dir_345c / "metric_candidate_normalization_coverage_345c_manifest.json", manifest)
    _write_json(dir_345c / "metric_candidate_normalization_coverage_345c_metric_rows.json", rows)
    (dir_345c / "metric_candidate_normalization_coverage_345c_metric_rows.csv").write_text("stub\n", encoding="utf-8")
    return dir_345c


def _seed_345c11_outputs(root: Path) -> Path:
    dir_345c11 = root / "output" / "second_batch_alias_apply_simulation_345c11"
    dir_345c11.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "metric_coverage_row_id": "mc::001",
            "inventory_row_id": "inv::001",
            "quality_row_id": "q::001",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "raw_metric_name": "Revenue",
            "normalized_metric_name": "revenue",
            "quality_severity": "NONE",
            "quality_issues": "",
            "review_status": "TRUSTED_CELL",
            "trust_status": "TRUSTED",
            "downstream_ready_before_normalization": True,
            "normalization_status": "NORMALIZED",
            "simulated_normalized_metric_name": "revenue",
            "normalization_status_before": "NORMALIZED",
            "normalization_status_after_simulation": "NORMALIZED",
            "simulation_applied": False,
            "simulation_action": "NO_SIMULATION_APPLIED",
            "simulation_source": "",
            "simulation_rule_update_required": False,
            "simulation_only_no_write_back": True,
            "downstream_ready_after_alias_simulation": True,
            "baseline_normalization_status": "NORMALIZED",
            "first_batch_simulated_normalized_metric_name": "revenue",
            "normalization_status_after_first_batch": "NORMALIZED",
            "first_batch_simulation_applied": False,
            "first_batch_simulation_action": "NO_SIMULATION_APPLIED",
            "first_batch_simulation_source": "",
            "downstream_ready_after_first_batch": True,
            "second_batch_simulated_normalized_metric_name": "",
            "second_batch_simulation_applied": False,
            "second_batch_simulation_action": "NO_SECOND_BATCH_SIMULATION_APPLIED",
            "second_batch_simulation_source": "",
            "normalization_status_after_second_batch": "NORMALIZED",
            "cumulative_simulated_normalized_metric_name": "revenue",
            "cumulative_simulation_action": "NO_SIMULATION_APPLIED",
            "downstream_ready_after_second_batch": True,
        },
        {
            "metric_coverage_row_id": "mc::002",
            "inventory_row_id": "inv::002",
            "quality_row_id": "q::002",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "pdf_id": "pdf_001",
            "pdf_name": "demo_a.pdf",
            "raw_metric_name": "Alias First",
            "normalized_metric_name": "",
            "quality_severity": "MEDIUM",
            "quality_issues": "MISSING_UNIT|HUMAN_REVIEW_PENDING",
            "review_status": "LONG_FORM_CELL",
            "trust_status": "LONG_FORM",
            "downstream_ready_before_normalization": True,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
            "simulated_normalized_metric_name": "metric_first",
            "normalization_status_before": "UNNORMALIZED_WITH_RAW_NAME",
            "normalization_status_after_simulation": "NORMALIZED",
            "simulation_applied": True,
            "simulation_action": "SIMULATED_ALIAS_NORMALIZATION",
            "simulation_source": "REVIEWED_ALIAS_345C5",
            "simulation_rule_update_required": True,
            "simulation_only_no_write_back": True,
            "downstream_ready_after_alias_simulation": True,
            "baseline_normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
            "first_batch_simulated_normalized_metric_name": "metric_first",
            "normalization_status_after_first_batch": "NORMALIZED",
            "first_batch_simulation_applied": True,
            "first_batch_simulation_action": "SIMULATED_ALIAS_NORMALIZATION",
            "first_batch_simulation_source": "REVIEWED_ALIAS_345C5",
            "downstream_ready_after_first_batch": True,
            "second_batch_simulated_normalized_metric_name": "",
            "second_batch_simulation_applied": False,
            "second_batch_simulation_action": "NO_SECOND_BATCH_SIMULATION_APPLIED",
            "second_batch_simulation_source": "",
            "normalization_status_after_second_batch": "NORMALIZED",
            "cumulative_simulated_normalized_metric_name": "metric_first",
            "cumulative_simulation_action": "FIRST_BATCH_ALIAS_SIMULATION_ONLY",
            "downstream_ready_after_second_batch": True,
        },
        {
            "metric_coverage_row_id": "mc::003",
            "inventory_row_id": "inv::003",
            "quality_row_id": "q::003",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "pdf_id": "pdf_002",
            "pdf_name": "demo_b.pdf",
            "raw_metric_name": "Alias Second",
            "normalized_metric_name": "",
            "quality_severity": "HIGH",
            "quality_issues": "MISSING_SOURCE_TRACE|HUMAN_REVIEW_PENDING",
            "review_status": "LONG_FORM_CELL",
            "trust_status": "LONG_FORM",
            "downstream_ready_before_normalization": True,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
            "simulated_normalized_metric_name": "",
            "normalization_status_before": "UNNORMALIZED_WITH_RAW_NAME",
            "normalization_status_after_simulation": "UNNORMALIZED_WITH_RAW_NAME",
            "simulation_applied": False,
            "simulation_action": "NO_SIMULATION_APPLIED",
            "simulation_source": "",
            "simulation_rule_update_required": True,
            "simulation_only_no_write_back": True,
            "downstream_ready_after_alias_simulation": False,
            "baseline_normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
            "first_batch_simulated_normalized_metric_name": "",
            "normalization_status_after_first_batch": "UNNORMALIZED_WITH_RAW_NAME",
            "first_batch_simulation_applied": False,
            "first_batch_simulation_action": "NO_SIMULATION_APPLIED",
            "first_batch_simulation_source": "",
            "downstream_ready_after_first_batch": False,
            "second_batch_simulated_normalized_metric_name": "metric_second",
            "second_batch_simulation_applied": True,
            "second_batch_simulation_action": "SIMULATED_ALIAS_NORMALIZATION_SECOND_BATCH",
            "second_batch_simulation_source": "REVIEWED_ALIAS_345C10",
            "normalization_status_after_second_batch": "NORMALIZED",
            "cumulative_simulated_normalized_metric_name": "metric_second",
            "cumulative_simulation_action": "SECOND_BATCH_ALIAS_SIMULATION_ONLY",
            "downstream_ready_after_second_batch": True,
        },
        {
            "metric_coverage_row_id": "mc::004",
            "inventory_row_id": "inv::004",
            "quality_row_id": "q::004",
            "source_stage": "REJECTED_OR_EXCLUDED",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "pdf_id": "pdf_003",
            "pdf_name": "demo_c.pdf",
            "raw_metric_name": "Rejected",
            "normalized_metric_name": "rejected_metric",
            "quality_severity": "HIGH",
            "quality_issues": "REJECTED_OR_EXCLUDED",
            "review_status": "REJECTED_OR_EXCLUDED",
            "trust_status": "REJECTED",
            "downstream_ready_before_normalization": False,
            "normalization_status": "NORMALIZED",
            "simulated_normalized_metric_name": "rejected_metric",
            "normalization_status_before": "NORMALIZED",
            "normalization_status_after_simulation": "NORMALIZED",
            "simulation_applied": False,
            "simulation_action": "NO_SIMULATION_APPLIED",
            "simulation_source": "",
            "simulation_rule_update_required": False,
            "simulation_only_no_write_back": True,
            "downstream_ready_after_alias_simulation": False,
            "baseline_normalization_status": "NORMALIZED",
            "first_batch_simulated_normalized_metric_name": "rejected_metric",
            "normalization_status_after_first_batch": "NORMALIZED",
            "first_batch_simulation_applied": False,
            "first_batch_simulation_action": "NO_SIMULATION_APPLIED",
            "first_batch_simulation_source": "",
            "downstream_ready_after_first_batch": False,
            "second_batch_simulated_normalized_metric_name": "",
            "second_batch_simulation_applied": False,
            "second_batch_simulation_action": "NO_SECOND_BATCH_SIMULATION_APPLIED",
            "second_batch_simulation_source": "",
            "normalization_status_after_second_batch": "NORMALIZED",
            "cumulative_simulated_normalized_metric_name": "rejected_metric",
            "cumulative_simulation_action": "NO_SIMULATION_APPLIED",
            "downstream_ready_after_second_batch": False,
        },
        {
            "metric_coverage_row_id": "mc::005",
            "inventory_row_id": "inv::005",
            "quality_row_id": "q::005",
            "source_stage": "LONG_FORM_CELL",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "pdf_id": "pdf_004",
            "pdf_name": "demo_d.pdf",
            "raw_metric_name": "Still Blind",
            "normalized_metric_name": "",
            "quality_severity": "HIGH",
            "quality_issues": "UNNORMALIZED_METRIC",
            "review_status": "LONG_FORM_CELL",
            "trust_status": "LONG_FORM",
            "downstream_ready_before_normalization": False,
            "normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
            "simulated_normalized_metric_name": "",
            "normalization_status_before": "UNNORMALIZED_WITH_RAW_NAME",
            "normalization_status_after_simulation": "UNNORMALIZED_WITH_RAW_NAME",
            "simulation_applied": False,
            "simulation_action": "NO_SIMULATION_APPLIED",
            "simulation_source": "",
            "simulation_rule_update_required": False,
            "simulation_only_no_write_back": True,
            "downstream_ready_after_alias_simulation": False,
            "baseline_normalization_status": "UNNORMALIZED_WITH_RAW_NAME",
            "first_batch_simulated_normalized_metric_name": "",
            "normalization_status_after_first_batch": "UNNORMALIZED_WITH_RAW_NAME",
            "first_batch_simulation_applied": False,
            "first_batch_simulation_action": "NO_SIMULATION_APPLIED",
            "first_batch_simulation_source": "",
            "downstream_ready_after_first_batch": False,
            "second_batch_simulated_normalized_metric_name": "",
            "second_batch_simulation_applied": False,
            "second_batch_simulation_action": "NO_SECOND_BATCH_SIMULATION_APPLIED",
            "second_batch_simulation_source": "",
            "normalization_status_after_second_batch": "UNNORMALIZED_WITH_RAW_NAME",
            "cumulative_simulated_normalized_metric_name": "",
            "cumulative_simulation_action": "NO_SIMULATION_APPLIED",
            "downstream_ready_after_second_batch": False,
        },
    ]
    manifest = {
        "decision": "SECOND_BATCH_ALIAS_APPLY_SIMULATION_345C11_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "metric_candidate_row_count": 5,
        "coverage_ratio_after_second_batch": 0.8,
        "cumulative_simulated_newly_normalized_row_count": 2,
        "remaining_unnormalized_raw_metric_name_count": 1,
        "remaining_unnormalized_metric_row_count": 1,
        "remaining_ready_candidate_count": 0,
        "alias_branch_final_recommendation": "STOP_ALIAS_BRANCH_AND_RETURN_TO_345D",
        "full_structured_demo_export_reasonable_after_345c11": True,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
    }
    _write_json(dir_345c11 / "second_batch_alias_apply_simulation_345c11_manifest.json", manifest)
    _write_json(dir_345c11 / "second_batch_alias_apply_simulation_345c11_simulated_metric_rows.json", rows)
    _write_json(
        dir_345c11 / "second_batch_alias_apply_simulation_345c11_combined_alias_map.json",
        [{"alias_batch": "FIRST_BATCH_345C6"}, {"alias_batch": "SECOND_BATCH_345C11"}],
    )
    _write_json(
        dir_345c11 / "second_batch_alias_apply_simulation_345c11_coverage_before_after.json",
        {"coverage_ratio_before": 0.4, "coverage_ratio_after_second_batch": 0.8},
    )
    _write_json(
        dir_345c11 / "second_batch_alias_apply_simulation_345c11_incremental_impact_summary.json",
        {"first_batch_alias_count": 1, "second_batch_applied_alias_key_count": 1},
    )
    _write_json(
        dir_345c11 / "second_batch_alias_apply_simulation_345c11_remaining_blind_spots.json",
        [{"raw_metric_name": "Still Blind", "remaining_row_count": 1, "remaining_ready_candidate_count": 0}],
    )
    _write_json(
        dir_345c11 / "second_batch_alias_apply_simulation_345c11_stop_or_return_to_345d_decision.json",
        {"alias_branch_final_recommendation": "STOP_ALIAS_BRANCH_AND_RETURN_TO_345D", "full_structured_demo_export_reasonable_after_345c11": True},
    )
    (dir_345c11 / "second_batch_alias_apply_simulation_345c11_simulated_metric_rows.csv").write_text("stub\n", encoding="utf-8")
    (dir_345c11 / "second_batch_alias_apply_simulation_345c11_combined_alias_map.csv").write_text("stub\n", encoding="utf-8")
    return dir_345c11


def test_345d_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_345a = _seed_345a_outputs(case_root)
        dir_345b = _seed_345b_outputs(case_root)
        dir_345c = _seed_345c_outputs(case_root)
        dir_345c11 = _seed_345c11_outputs(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_full_structured_demo_export_package_345d(
            full_structured_data_inventory_345a_dir=dir_345a,
            full_extraction_quality_audit_345b_dir=dir_345b,
            metric_candidate_normalization_coverage_345c_dir=dir_345c,
            second_batch_alias_apply_simulation_345c11_dir=dir_345c11,
            output_dir=case_root / "output" / "full_structured_demo_export_package_345d",
            repo_root=case_root,
            ledger_path=ledger_path,
            include_quality_limited_rows=False,
            max_sample_rows_per_caveat=5,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345D
        assert manifest["qa_fail_count"] == 0
        assert manifest["demo_export_row_count"] == 1
        assert manifest["quality_limited_row_count"] == 1
        assert manifest["excluded_row_count"] == 3
        assert manifest["coverage_ratio_before_alias_simulation"] == 0.4
        assert manifest["coverage_ratio_after_alias_simulation"] == 0.8
        assert manifest["baseline_normalized_demo_row_count"] == 1
        assert manifest["alias_simulated_demo_row_count"] == 1
        assert manifest["first_batch_alias_simulated_demo_row_count"] == 1
        assert manifest["second_batch_alias_simulated_demo_row_count"] == 0
        assert manifest["remaining_unnormalized_raw_metric_name_count"] == 1
        assert manifest["remaining_unnormalized_metric_row_count"] == 1
        assert manifest["missing_unit_count"] == 1
        assert manifest["missing_period_count"] == 0
        assert manifest["missing_source_trace_count"] == 0
        assert manifest["official_rules_modified"] is False
        assert manifest["official_alias_assets_modified"] is False
        assert manifest["alias_simulation_sidecar_used"] is True
        assert manifest["formal_export_generated"] is False
        assert manifest["demo_export_only"] is True
        assert manifest["full_structured_demo_export_reasonable"] is True
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        assert manifest["milestone_ledger_updated"] is True
        assert len(artifacts["demo_rows"]) == 1
        assert len(artifacts["quality_limited_rows"]) == 1
        assert len(artifacts["excluded_rows"]) == 3
        assert len(artifacts["alias_simulation_sidecar"]) == 1
        assert artifacts["alias_simulation_sidecar"][0]["alias_simulation_batch"] == "FIRST_BATCH"
        assert "## 345D Full Structured Demo Export Package" in ledger_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345d_missing_required_inputs_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing"
        missing_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_full_structured_demo_export_package_345d(
                full_structured_data_inventory_345a_dir=missing_dir,
                full_extraction_quality_audit_345b_dir=missing_dir,
                metric_candidate_normalization_coverage_345c_dir=missing_dir,
                second_batch_alias_apply_simulation_345c11_dir=missing_dir,
                output_dir=case_root / "output" / "full_structured_demo_export_package_345d",
                repo_root=case_root,
                ledger_path=case_root / "ledger.md",
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345A/345B/345C/345C11 inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
