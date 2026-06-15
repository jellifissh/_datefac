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

from datefac.benchmark.mineru_image_path_binding_fix_346a2 import (  # noqa: E402
    READY_DECISION_346A2,
    build_mineru_image_path_binding_fix_346a2,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_mineru_image_path_binding_fix_346a2"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_346a_outputs(root: Path, rows: list[dict]) -> Path:
    dir_346a = root / "output" / "vision_assisted_table_evidence_pilot_346a"
    dir_346a.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY",
        "qa_fail_count": 0,
        "selected_pilot_row_count": len(rows),
        "image_bound_count": 0,
        "image_missing_count": len(rows),
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
    }
    bundles = [
        {
            **row,
            "image_bound": False,
            "image_resolution_status": "NO_IMAGE_EVIDENCE_PROVIDED",
            "context_file_paths": [],
            "context_snippet": "",
            "context_available": False,
            "bbox": "",
            "table_image_path": "",
            "page_image_path": "",
            "chosen_image_path": "",
            "image_evidence_type": "",
            "request_eligible": False,
        }
        for row in rows
    ]
    schema = {
        "request_id": "string",
        "source_row_id": "string",
        "vision_decision": "CONFIRM_EXISTING | SUGGEST_FIELD_REPAIR | FLAG_CONFLICT | INSUFFICIENT_VISUAL_EVIDENCE | NOT_A_DATA_ROW",
    }
    _write_json(dir_346a / "vision_assisted_table_evidence_pilot_346a_manifest.json", manifest)
    _write_json(dir_346a / "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json", rows)
    _write_json(dir_346a / "vision_assisted_table_evidence_pilot_346a_evidence_bundle_index.json", bundles)
    _write_json(dir_346a / "vision_assisted_table_evidence_pilot_346a_vlm_output_schema.json", schema)
    return dir_346a


def _seed_mineru_output_root(root: Path) -> Path:
    mineru_root = root / "mineru_outputs"
    package_dir = mineru_root / "demo_pdf" / "auto"
    image_dir = package_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    (image_dir / "table_1.jpg").write_bytes(b"table1")
    (image_dir / "table_2.jpg").write_bytes(b"table2")
    (package_dir / "demo_pdf.md").write_text("# demo pdf\n", encoding="utf-8")
    _write_json(
        package_dir / "demo_pdf_content_list.json",
        [
            {"type": "text", "text": "intro", "page_idx": 0},
            {"type": "table", "img_path": "images/table_1.jpg", "bbox": [10, 20, 100, 120], "page_idx": 0, "table_body": "<table><tr><td>Revenue</td></tr></table>"},
            {"type": "table", "img_path": "images/table_2.jpg", "bbox": [20, 30, 120, 160], "page_idx": 2, "table_body": "<table><tr><td>EPS</td></tr></table>"},
        ],
    )
    _write_json(
        package_dir / "demo_pdf_content_list_v2.json",
        [
            {"type": "text", "text": "intro", "page_idx": 0},
            {"type": "table", "img_path": "images/table_1.jpg", "bbox": [10, 20, 100, 120], "page_idx": 0, "table_body": "<table><tr><td>Revenue</td></tr></table>"},
            {"type": "table", "img_path": "images/table_2.jpg", "bbox": [20, 30, 120, 160], "page_idx": 2, "table_body": "<table><tr><td>EPS</td></tr></table>"},
        ],
    )
    _write_json(package_dir / "demo_pdf_middle.json", {"middle": True})
    _write_json(package_dir / "demo_pdf_model.json", {"model": True})
    return mineru_root


def _seed_page_images(root: Path) -> Path:
    page_dir = root / "page_images"
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir / "demo_pdf_page_3_a.png").write_bytes(b"a")
    (page_dir / "demo_pdf_page_3_b.png").write_bytes(b"b")
    return page_dir


def test_346a2_no_evidence_baseline_runner_ready() -> None:
    case_root = _make_case_root()
    try:
        rows = [
            {
                "pilot_row_id": "346a::pilot::00001",
                "source_row_id": "row-001",
                "source_pdf_name": "demo_pdf.pdf",
                "source_page": "0.0",
                "source_table_id": "342b_pdf_001_content_list_001",
                "raw_metric_name": "Revenue",
                "demo_normalized_metric_name": "revenue",
                "value": "100",
                "unit": "",
                "period": "2024A",
                "quality_issue_codes": "MISSING_UNIT",
                "quality_severity": "HIGH",
                "target_field_types": ["unit", "value"],
            },
            {
                "pilot_row_id": "346a::pilot::00002",
                "source_row_id": "row-002",
                "source_pdf_name": "demo_pdf.pdf",
                "source_page": "2.0",
                "source_table_id": "342b_pdf_001_content_list_v2_002",
                "raw_metric_name": "EPS",
                "demo_normalized_metric_name": "eps",
                "value": "3.2",
                "unit": "元",
                "period": "2025E",
                "quality_issue_codes": "HEADER_ALIGNMENT_REVIEW",
                "quality_severity": "MEDIUM",
                "target_field_types": ["value"],
            },
        ]
        dir_346a = _seed_346a_outputs(case_root, rows)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        output_dir = case_root / "output" / "mineru_image_path_binding_fix_346a2"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_mineru_image_path_binding_fix_346a2.py"),
            "--vision-assisted-table-evidence-pilot-346a-dir",
            str(dir_346a),
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        manifest = json.loads((output_dir / "mineru_image_path_binding_fix_346a2_manifest.json").read_text(encoding="utf-8"))
        assert manifest["decision"] == READY_DECISION_346A2
        assert manifest["qa_fail_count"] == 0
        assert manifest["selected_pilot_row_count"] == 2
        assert manifest["image_bound_count"] == 0
        assert manifest["image_missing_count"] == 2
        assert manifest["vlm_request_count"] == 0
        assert manifest["recommended_next_step"] == "346A2R Provide MinerU Evidence Roots"
        assert manifest["milestone_ledger_updated"] is True
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346a2_deterministic_binding_and_context_only_rows() -> None:
    case_root = _make_case_root()
    try:
        rows = [
            {
                "pilot_row_id": "346a::pilot::00001",
                "source_row_id": "row-001",
                "source_pdf_name": "demo_pdf.pdf",
                "source_page": "0.0",
                "source_table_id": "342b_pdf_001_content_list_001",
                "raw_metric_name": "Revenue",
                "demo_normalized_metric_name": "revenue",
                "value": "100",
                "unit": "",
                "period": "2024A",
                "quality_issue_codes": "MISSING_UNIT",
                "quality_severity": "HIGH",
                "target_field_types": ["unit", "value"],
            },
            {
                "pilot_row_id": "346a::pilot::00002",
                "source_row_id": "row-002",
                "source_pdf_name": "demo_pdf.pdf",
                "source_page": "2.0",
                "source_table_id": "342b_pdf_001_content_list_v2_002",
                "raw_metric_name": "EPS",
                "demo_normalized_metric_name": "eps",
                "value": "3.2",
                "unit": "元",
                "period": "2025E",
                "quality_issue_codes": "HEADER_ALIGNMENT_REVIEW",
                "quality_severity": "MEDIUM",
                "target_field_types": ["value"],
            },
            {
                "pilot_row_id": "346a::pilot::00003",
                "source_row_id": "row-003",
                "source_pdf_name": "demo_pdf.pdf",
                "source_page": "8.0",
                "source_table_id": "342b_pdf_001_content_list_999",
                "raw_metric_name": "ROE",
                "demo_normalized_metric_name": "roe",
                "value": "12%",
                "unit": "%",
                "period": "2025E",
                "quality_issue_codes": "SOURCE_TRACE_CHECK",
                "quality_severity": "MEDIUM",
                "target_field_types": ["source_trace"],
            },
        ]
        dir_346a = _seed_346a_outputs(case_root, rows)
        mineru_root = _seed_mineru_output_root(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_mineru_image_path_binding_fix_346a2(
            vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
            output_dir=case_root / "output" / "mineru_image_path_binding_fix_346a2",
            repo_root=case_root,
            ledger_path=ledger_path,
            mineru_output_root=mineru_root,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_346A2
        assert manifest["qa_fail_count"] == 0
        assert manifest["image_bound_count"] == 2
        assert manifest["table_crop_bound_count"] == 2
        assert manifest["page_image_bound_count"] == 0
        assert manifest["json_md_context_bound_count"] == 3
        assert manifest["bound_row_count"] == 3
        assert manifest["vlm_request_count"] == 2
        assert manifest["live_vlm_call_count"] == 0
        statuses = {row["pilot_row_id"]: row["image_resolution_status"] for row in artifacts["bound_rows"]}
        assert statuses["346a::pilot::00001"] == "BOUND_TABLE_CROP_IMAGE"
        assert statuses["346a::pilot::00002"] == "BOUND_TABLE_CROP_IMAGE"
        assert statuses["346a::pilot::00003"] == "BOUND_TEXT_CONTEXT_ONLY"
        assert artifacts["vlm_request_rows"][0]["live_vlm_call_allowed"] is False
        assert artifacts["no_write_back_proof"]["upstream_inputs_unchanged"] is True
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346a2_ambiguous_page_candidates_not_image_bound() -> None:
    case_root = _make_case_root()
    try:
        rows = [
            {
                "pilot_row_id": "346a::pilot::00001",
                "source_row_id": "row-001",
                "source_pdf_name": "demo_pdf.pdf",
                "source_page": "3.0",
                "source_table_id": "",
                "raw_metric_name": "Revenue",
                "demo_normalized_metric_name": "revenue",
                "value": "100",
                "unit": "",
                "period": "2024A",
                "quality_issue_codes": "MISSING_UNIT",
                "quality_severity": "HIGH",
                "target_field_types": ["unit", "value"],
            }
        ]
        dir_346a = _seed_346a_outputs(case_root, rows)
        mineru_root = _seed_mineru_output_root(case_root)
        page_dir = _seed_page_images(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_mineru_image_path_binding_fix_346a2(
            vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
            output_dir=case_root / "output" / "mineru_image_path_binding_fix_346a2",
            repo_root=case_root,
            ledger_path=ledger_path,
            mineru_output_root=mineru_root,
            mineru_page_image_dir=page_dir,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_346A2
        assert manifest["qa_fail_count"] == 0
        assert manifest["image_bound_count"] == 0
        assert manifest["ambiguous_image_candidate_count"] == 1
        assert manifest["vlm_request_count"] == 0
        assert artifacts["ambiguous_rows"][0]["image_resolution_status"] == "AMBIGUOUS_IMAGE_CANDIDATE"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
