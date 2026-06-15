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

from datefac.benchmark.vision_assisted_table_evidence_pilot_346a import (  # noqa: E402
    READY_DECISION_346A,
    VLM_OUTPUT_SCHEMA_JSON_FILE_NAME,
    build_vision_assisted_table_evidence_pilot_346a,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_vision_assisted_table_evidence_pilot_346a"
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
        "quality_limited_row_count": 4,
        "demo_export_only": True,
        "formal_export_generated": False,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
    }
    quality_rows = [
        {
            "demo_export_row_id": "q1",
            "source_row_id": "row-001",
            "source_pdf_name": "demo_pdf.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "1",
            "source_table_id": "table_demo_001",
            "stage": "LONG_FORM_CELL",
            "raw_metric_name": "Revenue",
            "demo_normalized_metric_name": "revenue",
            "normalization_source": "BASELINE_345C",
            "alias_simulation_batch": "NONE",
            "value": "100",
            "unit": "",
            "period": "2024A",
            "currency": "CNY",
            "company_name": "DemoCo",
            "report_type": "initiation",
            "quality_severity": "HIGH",
            "quality_issue_codes": "MISSING_UNIT,HUMAN_REVIEW_PENDING",
            "source_trace_available": True,
            "demo_export_eligible": True,
            "demo_export_caveat_level": "HIGH",
            "demo_export_caveats": "MISSING_UNIT",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
        {
            "demo_export_row_id": "q2",
            "source_row_id": "row-002",
            "source_pdf_name": "demo_pdf.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "1",
            "source_table_id": "table_demo_001",
            "stage": "LONG_FORM_CELL",
            "raw_metric_name": "Net Profit",
            "demo_normalized_metric_name": "net_profit",
            "normalization_source": "BASELINE_345C",
            "alias_simulation_batch": "BATCH_1",
            "value": "80",
            "unit": "亿元",
            "period": "",
            "currency": "CNY",
            "company_name": "DemoCo",
            "report_type": "initiation",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "HEADER_ALIGNMENT_REVIEW",
            "source_trace_available": True,
            "demo_export_eligible": True,
            "demo_export_caveat_level": "MEDIUM",
            "demo_export_caveats": "HEADER_ALIGNMENT_REVIEW",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
        {
            "demo_export_row_id": "q3",
            "source_row_id": "row-003",
            "source_pdf_name": "other_pdf.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "2",
            "source_table_id": "table_other_001",
            "stage": "LONG_FORM_CELL",
            "raw_metric_name": "ROE",
            "demo_normalized_metric_name": "roe",
            "normalization_source": "BASELINE_345C",
            "alias_simulation_batch": "NONE",
            "value": "12%",
            "unit": "%",
            "period": "2025E",
            "currency": "CNY",
            "company_name": "OtherCo",
            "report_type": "update",
            "quality_severity": "MEDIUM",
            "quality_issue_codes": "SOURCE_TRACE_CHECK",
            "source_trace_available": False,
            "demo_export_eligible": True,
            "demo_export_caveat_level": "MEDIUM",
            "demo_export_caveats": "SOURCE_TRACE_CHECK",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
        {
            "demo_export_row_id": "q4",
            "source_row_id": "row-004",
            "source_pdf_name": "other_pdf.pdf",
            "source_artifact": "342F::03_LONG_FORM_CELLS",
            "source_page": "2",
            "source_table_id": "table_other_002",
            "stage": "LONG_FORM_CELL",
            "raw_metric_name": "Gross Margin",
            "demo_normalized_metric_name": "gross_margin",
            "normalization_source": "BASELINE_345C",
            "alias_simulation_batch": "NONE",
            "value": "33%",
            "unit": "%",
            "period": "2025E",
            "currency": "CNY",
            "company_name": "OtherCo",
            "report_type": "update",
            "quality_severity": "LOW",
            "quality_issue_codes": "HUMAN_REVIEW_PENDING",
            "source_trace_available": True,
            "demo_export_eligible": True,
            "demo_export_caveat_level": "LOW",
            "demo_export_caveats": "HUMAN_REVIEW_PENDING",
            "formal_client_export_allowed": False,
            "client_ready": False,
            "production_ready": False,
        },
    ]
    demo_rows = [dict(row) for row in quality_rows[:2]]
    _write_json(dir_345d / "full_structured_demo_export_package_345d_manifest.json", manifest)
    _write_json(dir_345d / "full_structured_demo_export_package_345d_quality_limited_rows.json", quality_rows)
    (dir_345d / "full_structured_demo_export_package_345d_quality_limited_rows.csv").write_text(
        "source_row_id,source_pdf_name\nrow-001,demo_pdf.pdf\n", encoding="utf-8-sig"
    )
    _write_json(dir_345d / "full_structured_demo_export_package_345d_demo_rows.json", demo_rows)
    (dir_345d / "full_structured_demo_export_package_345d_demo_rows.csv").write_text(
        "source_row_id,source_pdf_name\nrow-001,demo_pdf.pdf\n", encoding="utf-8-sig"
    )
    _write_json(
        dir_345d / "full_structured_demo_export_package_345d_quality_caveats.json",
        {"missing_unit_count": 1, "high_severity_issue_count": 1},
    )
    (dir_345d / "full_structured_demo_export_package_345d_quality_caveats.md").write_text("# caveats\n", encoding="utf-8")
    (dir_345d / "full_structured_demo_export_package_345d_artifact_index.md").write_text("# artifact index\n", encoding="utf-8")
    return dir_345d


def _seed_345e_outputs(root: Path) -> Path:
    dir_345e = root / "output" / "demo_export_review_qa_checklist_345e"
    dir_345e.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY",
        "qa_fail_count": 0,
        "gate_safety_check_passed": True,
        "caveat_completeness_passed": True,
        "presentation_ready_for_demo_only": True,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
    }
    sample_rows = [
        {
            "source_row_id": "row-001",
            "source_pdf_name": "demo_pdf.pdf",
            "source_page": "1",
            "source_table_id": "table_demo_001",
        }
    ]
    _write_json(dir_345e / "demo_export_review_qa_checklist_345e_manifest.json", manifest)
    _write_json(dir_345e / "demo_export_review_qa_checklist_345e_quality_limited_sample_rows.json", sample_rows)
    (dir_345e / "demo_export_review_qa_checklist_345e_quality_limited_sample_rows.csv").write_text(
        "source_row_id,source_pdf_name\nrow-001,demo_pdf.pdf\n", encoding="utf-8-sig"
    )
    _write_json(
        dir_345e / "demo_export_review_qa_checklist_345e_caveat_completeness_check.json",
        {"passed": True, "missing_topics": [], "present_topics": ["missing unit"]},
    )
    _write_json(
        dir_345e / "demo_export_review_qa_checklist_345e_demo_presentation_readiness.json",
        {"safe_for_demo_only": True, "recommended_first_files": ["review_checklist.md"]},
    )
    return dir_345e


def _seed_evidence(root: Path) -> tuple[Path, Path, Path, Path]:
    mineru_json_md_dir = root / "mineru_json_md"
    table_image_dir = root / "mineru_table_images"
    page_image_dir = root / "mineru_page_images"
    manifest_path = root / "table_image_manifest.json"

    (mineru_json_md_dir / "demo_pdf" / "auto").mkdir(parents=True, exist_ok=True)
    (mineru_json_md_dir / "demo_pdf" / "auto" / "demo_pdf.md").write_text("# demo table context\nunit: 亿元\n", encoding="utf-8")
    (table_image_dir / "table_demo_001.png").parent.mkdir(parents=True, exist_ok=True)
    (table_image_dir / "table_demo_001.png").write_bytes(b"fake")
    (page_image_dir / "demo_pdf_page_1.png").parent.mkdir(parents=True, exist_ok=True)
    (page_image_dir / "demo_pdf_page_1.png").write_bytes(b"fake")
    _write_json(
        manifest_path,
        [
            {
                "source_row_id": "row-001",
                "source_table_id": "table_demo_001",
                "source_pdf_name": "demo_pdf.pdf",
                "source_page": "1",
                "image_path": str(table_image_dir / "table_demo_001.png"),
                "image_evidence_type": "TABLE_CROP_IMAGE",
                "bbox": "[10,20,200,260]",
            }
        ],
    )
    return mineru_json_md_dir, table_image_dir, page_image_dir, manifest_path


def test_346a_runner_ready_without_image_evidence() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d_outputs(case_root)
        dir_345e = _seed_345e_outputs(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")
        output_dir = case_root / "output" / "vision_assisted_table_evidence_pilot_346a"

        command = [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "run_vision_assisted_table_evidence_pilot_346a.py"),
            "--full-structured-demo-export-package-345d-dir",
            str(dir_345d),
            "--demo-export-review-qa-checklist-345e-dir",
            str(dir_345e),
            "--output-dir",
            str(output_dir),
            "--ledger-path",
            str(ledger_path),
            "--max-pilot-rows",
            "3",
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)

        manifest = json.loads((output_dir / "vision_assisted_table_evidence_pilot_346a_manifest.json").read_text(encoding="utf-8"))
        assert manifest["decision"] == READY_DECISION_346A
        assert manifest["qa_fail_count"] == 0
        assert manifest["candidate_pool_row_count"] == 4
        assert manifest["selected_pilot_row_count"] == 3
        assert manifest["image_bound_count"] == 0
        assert manifest["image_missing_count"] == 3
        assert manifest["vlm_request_count"] == 0
        assert manifest["live_vlm_call_count"] == 0
        assert manifest["milestone_ledger_updated"] is True
        assert manifest["recommended_next_step"] == "346A2 MinerU Image Path Binding Fix"
        assert (output_dir / VLM_OUTPUT_SCHEMA_JSON_FILE_NAME).exists()
        assert (output_dir / "vision_assisted_table_evidence_pilot_346a_vlm_request_package.jsonl").exists()
        assert "## 346A Vision-Assisted Table Evidence Pilot" in ledger_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346a_generates_requests_only_for_image_bound_rows() -> None:
    case_root = _make_case_root()
    try:
        dir_345d = _seed_345d_outputs(case_root)
        dir_345e = _seed_345e_outputs(case_root)
        mineru_json_md_dir, table_image_dir, page_image_dir, manifest_path = _seed_evidence(case_root)
        ledger_path = case_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("# Ledger\n", encoding="utf-8")

        artifacts = build_vision_assisted_table_evidence_pilot_346a(
            full_structured_demo_export_package_345d_dir=dir_345d,
            demo_export_review_qa_checklist_345e_dir=dir_345e,
            output_dir=case_root / "output" / "vision_assisted_table_evidence_pilot_346a",
            repo_root=case_root,
            ledger_path=ledger_path,
            mineru_json_md_dir=mineru_json_md_dir,
            mineru_table_image_dir=table_image_dir,
            mineru_page_image_dir=page_image_dir,
            table_image_manifest=manifest_path,
            max_pilot_rows=2,
            max_context_rows_per_request=2,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_346A
        assert manifest["qa_fail_count"] == 0
        assert manifest["selected_pilot_row_count"] == 2
        assert manifest["image_bound_count"] == 2
        assert manifest["vlm_request_count"] == 2
        assert manifest["live_vlm_call_count"] == 0
        assert manifest["official_rules_modified"] is False
        assert manifest["official_alias_assets_modified"] is False
        assert manifest["formal_export_generated"] is False
        assert manifest["demo_export_only"] is True
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        assert artifacts["vlm_request_rows"][0]["image_path"].endswith("table_demo_001.png")
        assert artifacts["vlm_request_rows"][1]["image_evidence_type"] in {"TABLE_CROP_IMAGE", "PAGE_IMAGE"}
        assert artifacts["vlm_request_rows"][0]["live_vlm_call_allowed"] is False
        assert artifacts["no_write_back_proof"]["upstream_inputs_unchanged"] is True
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_346a_missing_required_inputs_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing"
        missing_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_vision_assisted_table_evidence_pilot_346a(
                full_structured_demo_export_package_345d_dir=missing_dir,
                demo_export_review_qa_checklist_345e_dir=missing_dir,
                output_dir=case_root / "output" / "vision_assisted_table_evidence_pilot_346a",
                repo_root=case_root,
                ledger_path=case_root / "ledger.md",
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345D/345E inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
