from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.full_extraction_quality_audit_345b import (  # noqa: E402
    NOT_READY_DECISION_345B,
    READY_DECISION_345B,
    build_full_extraction_quality_audit_345b,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_full_extraction_quality_audit_345b"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345a_outputs(root: Path) -> Path:
    dir_345a = root / "output" / "full_structured_data_inventory_345a"
    dir_345a.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "FULL_STRUCTURED_DATA_INVENTORY_345A_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "total_inventory_row_count": 4,
    }
    row_inventory = [
        {
            "inventory_row_id": "r1",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_stage": "LONG_FORM_CELL",
            "source_row_id": "src1",
            "pdf_id": "pdf1",
            "pdf_name": "file1.pdf",
            "table_id": "t1",
            "metric_name": "Revenue",
            "normalized_metric_name": "revenue",
            "value_raw": "10",
            "value_normalized": "10",
            "unit": "亿元",
            "period": "2024A",
            "source_page": "1",
            "trust_status": "LONG_FORM",
            "review_status": "LONG_FORM_CELL",
            "human_review_status": "NOT_REVIEWED",
            "is_metric_candidate": True,
            "is_normalized_metric": True,
            "is_downstream_ready_candidate": True,
            "missing_required_field_count": 0,
            "missing_required_fields": "",
        },
        {
            "inventory_row_id": "r2",
            "source_artifact": "342F::05_REVIEW_REQUIRED",
            "source_stage": "REVIEW_REQUIRED",
            "source_row_id": "src2",
            "pdf_id": "pdf1",
            "pdf_name": "file1.pdf",
            "table_id": "t1",
            "metric_name": "ROE",
            "normalized_metric_name": "ROE",
            "value_raw": "10%",
            "value_normalized": "10",
            "unit": "",
            "period": "2024A",
            "source_page": "",
            "trust_status": "REVIEW_REQUIRED",
            "review_status": "REVIEW_REQUIRED",
            "human_review_status": "PENDING_HUMAN_REVIEW",
            "is_metric_candidate": True,
            "is_normalized_metric": True,
            "is_downstream_ready_candidate": True,
            "missing_required_field_count": 2,
            "missing_required_fields": "unit|source_page",
        },
        {
            "inventory_row_id": "r3",
            "source_artifact": "342H::06_REJECTED_CELLS",
            "source_stage": "REJECTED_OR_EXCLUDED",
            "source_row_id": "src3",
            "pdf_id": "pdf2",
            "pdf_name": "file2.pdf",
            "table_id": "t2",
            "metric_name": "",
            "normalized_metric_name": "",
            "value_raw": "",
            "value_normalized": "",
            "unit": "",
            "period": "",
            "source_page": "",
            "trust_status": "HUMAN_REJECTED",
            "review_status": "REJECTED_OR_EXCLUDED",
            "human_review_status": "REJECTED",
            "is_metric_candidate": False,
            "is_normalized_metric": False,
            "is_downstream_ready_candidate": False,
            "missing_required_field_count": 5,
            "missing_required_fields": "metric_name|value|unit|period|source_page",
        },
        {
            "inventory_row_id": "r4",
            "source_artifact": "344F::review_rows_json",
            "source_stage": "STRICT_HUMAN_REVIEW_PENDING_ROW",
            "source_row_id": "src4",
            "pdf_id": "",
            "pdf_name": "file3.pdf",
            "table_id": "",
            "metric_name": "EPS",
            "normalized_metric_name": "EPS",
            "value_raw": "1.2",
            "value_normalized": "1.2",
            "unit": "元",
            "period": "2024A",
            "source_page": "2",
            "trust_status": "Prior demo trusted arc",
            "review_status": "STRICT_HUMAN_REVIEW_PENDING_ROW",
            "human_review_status": "STRICT_REVIEW_NOT_FILLED",
            "is_metric_candidate": True,
            "is_normalized_metric": True,
            "is_downstream_ready_candidate": True,
            "missing_required_field_count": 0,
            "missing_required_fields": "",
        },
    ]
    stage_status = [{"source_stage": "LONG_FORM_CELL", "row_count": 1}]
    missing_field = [{"source_stage": "REVIEW_REQUIRED", "missing_unit_count": 1}]
    executive_summary = "# seeded 345A executive summary"

    _write_json(dir_345a / "full_structured_data_inventory_345a_manifest.json", manifest)
    _write_json(dir_345a / "full_structured_data_inventory_345a_row_inventory.json", row_inventory)
    _write_json(
        dir_345a / "full_structured_data_inventory_345a_stage_status_summary.json",
        stage_status,
    )
    _write_json(
        dir_345a / "full_structured_data_inventory_345a_missing_field_summary.json",
        missing_field,
    )
    (dir_345a / "full_structured_data_inventory_345a_executive_summary.md").write_text(
        executive_summary,
        encoding="utf-8",
    )
    return dir_345a


def test_345b_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_345a = _seed_345a_outputs(case_root)
        artifacts = build_full_extraction_quality_audit_345b(
            full_structured_data_inventory_345a_dir=dir_345a,
            output_dir=case_root / "output" / "full_extraction_quality_audit_345b",
            repo_root=case_root,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345B
        assert manifest["qa_fail_count"] == 0
        assert manifest["audited_row_count"] == 4
        assert manifest["input_inventory_row_count"] == 4
        assert manifest["high_severity_issue_count"] >= 1
        assert manifest["priority_fix_queue_count"] >= 1
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        assert manifest["global_strict_human_review_completed"] is False
        assert len(artifacts["stage_quality_summary"]) > 0
        assert len(artifacts["priority_fix_queue"]) > 0
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345b_missing_required_345a_input_fails() -> None:
    case_root = _make_case_root()
    try:
        missing = case_root / "missing_345a"
        missing.mkdir(parents=True, exist_ok=True)
        try:
            build_full_extraction_quality_audit_345b(
                full_structured_data_inventory_345a_dir=missing,
                output_dir=case_root / "output" / "full_extraction_quality_audit_345b",
                repo_root=case_root,
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing required 345A inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345b_not_ready_if_345a_manifest_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_345a = _seed_345a_outputs(case_root)
        manifest_path = dir_345a / "full_structured_data_inventory_345a_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["decision"] = "FULL_STRUCTURED_DATA_INVENTORY_345A_NOT_READY"
        _write_json(manifest_path, manifest)
        artifacts = build_full_extraction_quality_audit_345b(
            full_structured_data_inventory_345a_dir=dir_345a,
            output_dir=case_root / "output" / "full_extraction_quality_audit_345b",
            repo_root=case_root,
        )
        assert artifacts["manifest"]["decision"] == NOT_READY_DECISION_345B
        assert artifacts["manifest"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
