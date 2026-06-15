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

from datefac.benchmark.quality_limited_row_recovery_pilot_346b import (  # noqa: E402
    READY_DECISION_346B,
    build_quality_limited_row_recovery_pilot_346b,
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
    base_dir = PROJECT_ROOT / "_codex_test_tmp_quality_limited_row_recovery_pilot_346b"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345d_outputs(root: Path, rows: list[dict]) -> Path:
    dir_345d = root / "output" / "full_structured_demo_export_package_345d"
    dir_345d.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY",
        "qa_fail_count": 0,
        "quality_limited_row_count": len(rows),
        "demo_export_only": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_export_generated": False,
    }
    _write_json(dir_345d / "full_structured_demo_export_package_345d_manifest.json", manifest)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_limited_rows.json", rows)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_demo_rows.json", [])
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_caveats.json", {"note": "demo only"})
    (dir_345d / "full_structured_demo_export_package_345d_quality_caveats.md").write_text("# caveats\n", encoding="utf-8")
    _write_json(dir_345d / "full_structured_demo_export_package_345d_alias_simulation_sidecar.json", [])
    return dir_345d


def _seed_346a_outputs(root: Path, rows: list[dict]) -> Path:
    dir_346a = root / "output" / "vision_assisted_table_evidence_pilot_346a"
    dir_346a.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY",
        "qa_fail_count": 0,
        "selected_pilot_row_count": len(rows),
        "quality_limited_row_count": len(rows),
        "demo_export_only": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
    }
    field_targets = []
    for row in rows:
        for field in row.get("target_field_types", []):
            field_targets.append(
                {
                    "pilot_row_id": row["pilot_row_id"],
                    "source_row_id": row["source_row_id"],
                    "target_field_type": field,
                }
            )
    _write_json(dir_346a / "vision_assisted_table_evidence_pilot_346a_manifest.json", manifest)
    _write_json(dir_346a / "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json", rows)
    _write_json(dir_346a / "vision_assisted_table_evidence_pilot_346a_field_repair_targets.json", field_targets)
    (dir_346a / "vision_assisted_table_evidence_pilot_346a_conflict_handling_policy.md").write_text("# conflict policy\n", encoding="utf-8")
    return dir_346a


def _seed_346a2_outputs(root: Path, bound_rows: list[dict], unresolved_rows: list[dict]) -> Path:
    dir_346a2 = root / "output" / "mineru_image_path_binding_fix_346a2"
    dir_346a2.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY",
        "qa_fail_count": 0,
        "selected_pilot_row_count": len(bound_rows) + len(unresolved_rows),
        "image_bound_count": sum(1 for row in bound_rows + unresolved_rows if row.get("image_bound")),
        "json_md_context_bound_count": sum(1 for row in bound_rows + unresolved_rows if row.get("context_available")),
        "live_vlm_call_count": 0,
        "upstream_data_mutated": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
    }
    image_status_rows = []
    vlm_request_rows = []
    for row in bound_rows + unresolved_rows:
        image_status_rows.append(
            {
                "pilot_row_id": row["pilot_row_id"],
                "source_row_id": row["source_row_id"],
                "image_resolution_status": row["image_resolution_status"],
                "image_bound": row["image_bound"],
                "chosen_image_path": row.get("chosen_image_path", ""),
            }
        )
        if row.get("image_bound"):
            vlm_request_rows.append({"pilot_row_id": row["pilot_row_id"], "source_row_id": row["source_row_id"]})
    _write_json(dir_346a2 / "mineru_image_path_binding_fix_346a2_manifest.json", manifest)
    _write_json(dir_346a2 / "mineru_image_path_binding_fix_346a2_bound_rows.json", bound_rows)
    _write_json(dir_346a2 / "mineru_image_path_binding_fix_346a2_unresolved_rows.json", unresolved_rows)
    _write_json(dir_346a2 / "mineru_image_path_binding_fix_346a2_image_resolution_status.json", image_status_rows)
    _write_json(
        dir_346a2 / "mineru_image_path_binding_fix_346a2_json_md_context_index.json",
        [{"source_pdf_stem": "demo_pdf", "json_paths": [], "md_paths": [], "table_entry_count": 1}],
    )
    _write_json(dir_346a2 / "mineru_image_path_binding_fix_346a2_binding_summary.json", {"ready": True})
    _write_jsonl(dir_346a2 / "mineru_image_path_binding_fix_346a2_vlm_request_package.jsonl", vlm_request_rows)
    return dir_346a2


def test_346b_runner_ready_and_counts_close() -> None:
    case_root = _make_case_root()
    try:
        row_ratio = {
            "demo_export_row_id": "345d::demo::00001",
            "source_row_id": "row-001",
            "source_pdf_name": "demo_pdf.pdf",
            "source_page": "0.0",
            "source_table_id": "table-001",
            "raw_metric_name": "EV/EBITDA",
            "demo_normalized_metric_name": "ev_to_ebitda",
            "value": "15.3",
            "unit": "",
            "period": "2024A",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "MISSING_UNIT|UNNORMALIZED_METRIC|HUMAN_REVIEW_PENDING",
            "source_trace_available": True,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "pilot_row_id": "346a::pilot::00001",
            "target_field_types": ["unit", "value"],
            "image_bound": True,
            "image_resolution_status": "BOUND_TABLE_CROP_IMAGE",
            "context_available": True,
            "chosen_image_path": str(case_root / "images" / "table_1.jpg"),
            "json_context_path": str(case_root / "ctx" / "demo_pdf_content_list.json"),
            "md_context_path": str(case_root / "ctx" / "demo_pdf.md"),
            "context_snippet": "<table><tr><td>EV/EBITDA</td><td>15.3</td></tr></table>",
            "image_evidence_type": "TABLE_CROP_IMAGE",
            "neighbor_context_rows": [],
        }
        row_per_share = {
            "demo_export_row_id": "345d::demo::00002",
            "source_row_id": "row-002",
            "source_pdf_name": "demo_pdf.pdf",
            "source_page": "0.0",
            "source_table_id": "table-001",
            "raw_metric_name": "每股净资产",
            "demo_normalized_metric_name": "book_value_per_share",
            "value": "8.59",
            "unit": "",
            "period": "2024A",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "MISSING_UNIT|HUMAN_REVIEW_PENDING",
            "source_trace_available": True,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "pilot_row_id": "346a::pilot::00002",
            "target_field_types": ["unit", "value"],
            "image_bound": True,
            "image_resolution_status": "BOUND_TABLE_CROP_IMAGE",
            "context_available": True,
            "chosen_image_path": str(case_root / "images" / "table_1.jpg"),
            "json_context_path": str(case_root / "ctx" / "demo_pdf_content_list.json"),
            "md_context_path": str(case_root / "ctx" / "demo_pdf.md"),
            "context_snippet": "<table><tr><td>每股收益（元）</td><td>1.20</td></tr><tr><td>每股净资产</td><td>8.59</td></tr></table>",
            "image_evidence_type": "TABLE_CROP_IMAGE",
            "neighbor_context_rows": [],
        }
        row_context_only = {
            "demo_export_row_id": "345d::demo::00003",
            "source_row_id": "row-003",
            "source_pdf_name": "demo_pdf.pdf",
            "source_page": "5.0",
            "source_table_id": "table-002",
            "raw_metric_name": "营业利润",
            "demo_normalized_metric_name": "operating_profit",
            "value": "(15.4)",
            "unit": "",
            "period": "2025A",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "MISSING_UNIT|UNNORMALIZED_METRIC|HUMAN_REVIEW_PENDING",
            "source_trace_available": True,
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
            "pilot_row_id": "346a::pilot::00003",
            "target_field_types": ["unit", "value"],
            "image_bound": False,
            "image_resolution_status": "NO_MATCH_FOUND",
            "context_available": False,
            "chosen_image_path": "",
            "json_context_path": "",
            "md_context_path": "",
            "context_snippet": "",
            "image_evidence_type": "",
            "neighbor_context_rows": [],
        }
        rows = [row_ratio, row_per_share, row_context_only]
        dir_345d = _seed_345d_outputs(case_root, rows)
        dir_346a = _seed_346a_outputs(case_root, rows)
        dir_346a2 = _seed_346a2_outputs(case_root, [row_ratio, row_per_share], [row_context_only])
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        output_dir = case_root / "output" / "quality_limited_row_recovery_pilot_346b"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_quality_limited_row_recovery_pilot_346b.py"),
            "--full-structured-demo-export-package-345d-dir",
            str(dir_345d),
            "--vision-assisted-table-evidence-pilot-346a-dir",
            str(dir_346a),
            "--mineru-image-path-binding-fix-346a2-dir",
            str(dir_346a2),
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        manifest = json.loads((output_dir / "quality_limited_row_recovery_pilot_346b_manifest.json").read_text(encoding="utf-8"))
        assert manifest["decision"] == READY_DECISION_346B
        assert manifest["qa_fail_count"] == 0
        assert manifest["pilot_input_row_count"] == 3
        assert manifest["image_bound_input_count"] == 2
        assert manifest["json_md_context_bound_input_count"] == 2
        assert manifest["recovered_demo_candidate_count"] == 2
        assert manifest["still_quality_limited_count"] == 1
        assert manifest["needs_human_review_count"] == 0
        assert manifest["needs_vlm_count"] == 0
        assert manifest["milestone_ledger_updated"] is True
        assert "346B Quality-Limited Row Recovery Pilot" in ledger_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b_ratio_and_per_share_unit_rules() -> None:
    case_root = _make_case_root()
    try:
        row_ratio = {
            "source_row_id": "row-001",
            "source_pdf_name": "demo_pdf.pdf",
            "source_page": "0.0",
            "source_table_id": "table-001",
            "raw_metric_name": "EV/EBITDA",
            "demo_normalized_metric_name": "ev_to_ebitda",
            "value": "15.3",
            "unit": "",
            "period": "2024A",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "MISSING_UNIT|HUMAN_REVIEW_PENDING",
            "pilot_row_id": "346a::pilot::00001",
            "target_field_types": ["unit"],
            "image_bound": True,
            "image_resolution_status": "BOUND_TABLE_CROP_IMAGE",
            "context_available": True,
            "chosen_image_path": str(case_root / "images" / "table_1.jpg"),
            "json_context_path": "",
            "md_context_path": "",
            "context_snippet": "<table><tr><td>EV/EBITDA</td><td>15.3</td></tr></table>",
            "image_evidence_type": "TABLE_CROP_IMAGE",
            "neighbor_context_rows": [],
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
        row_per_share = {
            "source_row_id": "row-002",
            "source_pdf_name": "demo_pdf.pdf",
            "source_page": "0.0",
            "source_table_id": "table-001",
            "raw_metric_name": "每股净资产",
            "demo_normalized_metric_name": "book_value_per_share",
            "value": "8.59",
            "unit": "",
            "period": "2024A",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "MISSING_UNIT|HUMAN_REVIEW_PENDING",
            "pilot_row_id": "346a::pilot::00002",
            "target_field_types": ["unit"],
            "image_bound": True,
            "image_resolution_status": "BOUND_TABLE_CROP_IMAGE",
            "context_available": True,
            "chosen_image_path": str(case_root / "images" / "table_1.jpg"),
            "json_context_path": "",
            "md_context_path": "",
            "context_snippet": "<table><tr><td>每股收益（元）</td><td>1.20</td></tr><tr><td>每股净资产</td><td>8.59</td></tr></table>",
            "image_evidence_type": "TABLE_CROP_IMAGE",
            "neighbor_context_rows": [],
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        }
        dir_345d = _seed_345d_outputs(case_root, [row_ratio, row_per_share])
        dir_346a = _seed_346a_outputs(case_root, [row_ratio, row_per_share])
        dir_346a2 = _seed_346a2_outputs(case_root, [row_ratio, row_per_share], [])
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_quality_limited_row_recovery_pilot_346b(
            full_structured_demo_export_package_345d_dir=dir_345d,
            vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
            mineru_image_path_binding_fix_346a2_dir=dir_346a2,
            output_dir=case_root / "output" / "quality_limited_row_recovery_pilot_346b",
            repo_root=case_root,
            ledger_path=ledger_path,
        )
        rows = {row["source_row_id"]: row for row in artifacts["context_injection_results"]}
        assert rows["row-001"]["unit_repair_action"] == "UNIT_NOT_APPLICABLE_RATIO_MULTIPLE"
        assert rows["row-001"]["inherited_unit"] == ""
        assert rows["row-002"]["unit_repair_action"] == "UNIT_INFERRED_PER_SHARE"
        assert rows["row-002"]["inherited_unit"] == "元"
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346b_missing_346a2_input_fails_clearly() -> None:
    case_root = _make_case_root()
    try:
        rows = []
        dir_345d = _seed_345d_outputs(case_root, rows)
        dir_346a = _seed_346a_outputs(case_root, rows)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        try:
            build_quality_limited_row_recovery_pilot_346b(
                full_structured_demo_export_package_345d_dir=dir_345d,
                vision_assisted_table_evidence_pilot_346a_dir=dir_346a,
                mineru_image_path_binding_fix_346a2_dir=case_root / "missing_346a2",
                output_dir=case_root / "output" / "quality_limited_row_recovery_pilot_346b",
                repo_root=case_root,
                ledger_path=ledger_path,
            )
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError as exc:
            assert "346A2 input directory missing" in str(exc)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
