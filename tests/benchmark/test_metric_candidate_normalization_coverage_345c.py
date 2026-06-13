from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.metric_candidate_normalization_coverage_345c import (  # noqa: E402
    NOT_READY_DECISION_345C,
    READY_DECISION_345C,
    build_metric_candidate_normalization_coverage_345c,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_metric_candidate_normalization_coverage_345c"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345a_and_345b_outputs(root: Path) -> tuple[Path, Path]:
    dir_345a = root / "output" / "full_structured_data_inventory_345a"
    dir_345b = root / "output" / "full_extraction_quality_audit_345b"
    dir_345a.mkdir(parents=True, exist_ok=True)
    dir_345b.mkdir(parents=True, exist_ok=True)

    manifest_345a = {
        "decision": "FULL_STRUCTURED_DATA_INVENTORY_345A_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "total_inventory_row_count": 5,
        "metric_candidate_row_count": 4,
        "normalized_metric_row_count": 2,
        "downstream_ready_candidate_count": 4,
    }
    row_inventory = [
        {
            "inventory_row_id": "r1",
            "source_stage": "TRUSTED_CELL",
            "source_artifact": "342F::04_TRUSTED_CELLS",
            "pdf_id": "pdf1",
            "pdf_name": "alpha.pdf",
            "metric_name": "Revenue",
            "normalized_metric_name": "revenue",
            "is_metric_candidate": True,
            "is_normalized_metric": True,
            "review_status": "TRUSTED_CELL",
            "trust_status": "TRUSTED",
            "is_downstream_ready_candidate": True,
        },
        {
            "inventory_row_id": "r2",
            "source_stage": "REVIEW_REQUIRED",
            "source_artifact": "342G::03_REVIEW_QUEUE",
            "pdf_id": "pdf1",
            "pdf_name": "alpha.pdf",
            "metric_name": "净利润率",
            "normalized_metric_name": "",
            "is_metric_candidate": True,
            "is_normalized_metric": False,
            "review_status": "REVIEW_REQUIRED",
            "trust_status": "REVIEW_REQUIRED",
            "is_downstream_ready_candidate": True,
        },
        {
            "inventory_row_id": "r3",
            "source_stage": "REJECTED_OR_EXCLUDED",
            "source_artifact": "342H::06_REJECTED_CELLS",
            "pdf_id": "pdf2",
            "pdf_name": "beta.pdf",
            "metric_name": "合计",
            "normalized_metric_name": "",
            "is_metric_candidate": True,
            "is_normalized_metric": False,
            "review_status": "REJECTED_OR_EXCLUDED",
            "trust_status": "REJECTED",
            "is_downstream_ready_candidate": False,
        },
        {
            "inventory_row_id": "r4",
            "source_stage": "UNKNOWN_STAGE",
            "source_artifact": "unknown::rows",
            "pdf_id": "pdf3",
            "pdf_name": "gamma.pdf",
            "metric_name": "项目",
            "normalized_metric_name": "",
            "is_metric_candidate": True,
            "is_normalized_metric": False,
            "review_status": "REVIEW_REQUIRED",
            "trust_status": "UNKNOWN",
            "is_downstream_ready_candidate": False,
        },
        {
            "inventory_row_id": "r5",
            "source_stage": "REJECTED_OR_EXCLUDED",
            "source_artifact": "342H::06_REJECTED_CELLS",
            "pdf_id": "pdf4",
            "pdf_name": "delta.pdf",
            "metric_name": "",
            "normalized_metric_name": "",
            "is_metric_candidate": False,
            "is_normalized_metric": False,
            "review_status": "REJECTED_OR_EXCLUDED",
            "trust_status": "REJECTED",
            "is_downstream_ready_candidate": False,
        },
    ]
    manifest_345b = {
        "decision": "FULL_EXTRACTION_QUALITY_AUDIT_345B_READY",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_inventory_row_count": 5,
        "audited_row_count": 5,
    }
    quality_rows = [
        {
            "quality_row_id": "q1",
            "inventory_row_id": "r1",
            "quality_severity": "NONE",
            "quality_issues": "",
        },
        {
            "quality_row_id": "q2",
            "inventory_row_id": "r2",
            "quality_severity": "MEDIUM",
            "quality_issues": "UNNORMALIZED_METRIC|REVIEW_REQUIRED",
        },
        {
            "quality_row_id": "q3",
            "inventory_row_id": "r3",
            "quality_severity": "HIGH",
            "quality_issues": "UNNORMALIZED_METRIC|REJECTED_OR_EXCLUDED",
        },
        {
            "quality_row_id": "q4",
            "inventory_row_id": "r4",
            "quality_severity": "LOW",
            "quality_issues": "UNNORMALIZED_METRIC",
        },
        {
            "quality_row_id": "q5",
            "inventory_row_id": "r5",
            "quality_severity": "HIGH",
            "quality_issues": "REJECTED_OR_EXCLUDED",
        },
    ]

    _write_json(dir_345a / "full_structured_data_inventory_345a_manifest.json", manifest_345a)
    _write_json(dir_345a / "full_structured_data_inventory_345a_row_inventory.json", row_inventory)
    _write_json(dir_345b / "full_extraction_quality_audit_345b_manifest.json", manifest_345b)
    _write_json(dir_345b / "full_extraction_quality_audit_345b_quality_rows.json", quality_rows)
    return dir_345a, dir_345b


def test_345c_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_345a, dir_345b = _seed_345a_and_345b_outputs(case_root)
        artifacts = build_metric_candidate_normalization_coverage_345c(
            full_structured_data_inventory_345a_dir=dir_345a,
            full_extraction_quality_audit_345b_dir=dir_345b,
            output_dir=case_root / "output" / "metric_candidate_normalization_coverage_345c",
            repo_root=case_root,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345C
        assert manifest["qa_fail_count"] == 0
        assert manifest["metric_candidate_row_count"] == 4
        assert manifest["normalized_metric_row_count"] == 1
        assert manifest["unnormalized_metric_row_count"] == 3
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        assert manifest["global_strict_human_review_completed"] is False
        assert manifest["alias_candidate_count"] == 3
        assert manifest["ready_candidate_count_before_normalization_filter"] == 4
        assert manifest["ready_candidate_count_after_normalization_filter"] == 1
        assert artifacts["metric_rows"][1]["normalization_gap_reason"] == "RAW_NAME_NOT_MAPPED"
        assert artifacts["metric_rows"][2]["normalization_gap_reason"] == "REJECTED_OR_EXCLUDED_ROW"
        assert artifacts["metric_rows"][3]["normalization_gap_reason"] == "SOURCE_STAGE_NOT_TARGETED"
        assert len(artifacts["alias_candidate_queue"]) == 3
        assert artifacts["qa_json"]["qa_fail_count"] == 0
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c_missing_required_inputs_fail() -> None:
    case_root = _make_case_root()
    try:
        missing_345a = case_root / "missing_345a"
        missing_345b = case_root / "missing_345b"
        missing_345a.mkdir(parents=True, exist_ok=True)
        missing_345b.mkdir(parents=True, exist_ok=True)
        try:
            build_metric_candidate_normalization_coverage_345c(
                full_structured_data_inventory_345a_dir=missing_345a,
                full_extraction_quality_audit_345b_dir=missing_345b,
                output_dir=case_root / "output" / "metric_candidate_normalization_coverage_345c",
                repo_root=case_root,
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing required 345A/345B inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c_not_ready_if_upstream_manifest_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_345a, dir_345b = _seed_345a_and_345b_outputs(case_root)
        manifest_345b_path = dir_345b / "full_extraction_quality_audit_345b_manifest.json"
        manifest_345b = json.loads(manifest_345b_path.read_text(encoding="utf-8"))
        manifest_345b["decision"] = "FULL_EXTRACTION_QUALITY_AUDIT_345B_NOT_READY"
        _write_json(manifest_345b_path, manifest_345b)
        artifacts = build_metric_candidate_normalization_coverage_345c(
            full_structured_data_inventory_345a_dir=dir_345a,
            full_extraction_quality_audit_345b_dir=dir_345b,
            output_dir=case_root / "output" / "metric_candidate_normalization_coverage_345c",
            repo_root=case_root,
        )
        assert artifacts["manifest"]["decision"] == NOT_READY_DECISION_345C
        assert artifacts["manifest"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
