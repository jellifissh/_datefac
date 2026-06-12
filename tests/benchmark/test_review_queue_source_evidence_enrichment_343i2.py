from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_audit_summary_343h import (  # noqa: E402
    build_review_queue_audit_summary_343h,
)
from datefac.benchmark.review_queue_source_evidence_enrichment_343i2 import (  # noqa: E402
    NOT_READY_DECISION_343I2,
    READY_DECISION_343I2,
    build_review_queue_source_evidence_enrichment_343i2,
)
from datefac.benchmark.review_queue_strict_human_review_package_343i import (  # noqa: E402
    build_review_queue_strict_human_review_package_343i,
)
from tests.benchmark.test_review_queue_audit_summary_343h import _seed_343h_inputs  # noqa: E402


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_source_evidence_enrichment_343i2"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_343i2_inputs(root: Path) -> tuple[Path, Path, Path, Path, Path, Path]:
    dir_343g, dir_343f, dir_343e, dir_343d, dir_343a = _seed_343h_inputs(root)

    dir_343h = root / "output" / "review_queue_audit_summary_343h"
    artifacts_343h = build_review_queue_audit_summary_343h(
        spot_check_ingestion_343g_dir=dir_343g,
        spot_check_package_343f_dir=dir_343f,
        apply_simulation_343e_dir=dir_343e,
        excel_ingestion_343d_dir=dir_343d,
        review_queue_schema_343a_dir=dir_343a,
        output_dir=dir_343h,
        repo_root=root,
    )
    _write_json(dir_343h / "review_queue_audit_summary_343h_summary.json", artifacts_343h["summary"])
    _write_json(dir_343h / "review_queue_audit_summary_343h_qa.json", artifacts_343h["qa_json"])
    _write_json(dir_343h / "review_queue_audit_summary_343h_manifest.json", artifacts_343h["manifest"])
    _write_json(
        dir_343h / "review_queue_audit_summary_343h_no_write_back_proof.json",
        artifacts_343h["no_write_back_proof_json"],
    )
    _write_json(
        dir_343h / "review_queue_audit_summary_343h_client_export_gate.json",
        artifacts_343h["client_export_gate"],
    )
    _write_json(
        dir_343h / "review_queue_audit_summary_343h_next_action_plan.json",
        artifacts_343h["next_action_plan"],
    )
    _write_jsonl(
        dir_343h / "review_queue_audit_summary_343h_confirmed_ai_assisted_items.jsonl",
        artifacts_343h["confirmed_items"],
    )
    _write_jsonl(
        dir_343h / "review_queue_audit_summary_343h_gap_items.jsonl",
        artifacts_343h["gap_items"],
    )
    (dir_343h / "review_queue_audit_summary_343h_report.md").write_text("ok", encoding="utf-8")
    (
        dir_343h / "review_queue_audit_summary_343h_strict_human_gap_report.md"
    ).write_text("ok", encoding="utf-8")

    dir_343i = root / "output" / "review_queue_strict_human_review_package_343i"
    artifacts_343i = build_review_queue_strict_human_review_package_343i(
        audit_summary_343h_dir=dir_343h,
        spot_check_ingestion_343g_dir=dir_343g,
        review_queue_schema_343a_dir=dir_343a,
        output_dir=dir_343i,
        repo_root=root,
    )
    _write_json(dir_343i / "review_queue_strict_human_review_package_343i_summary.json", artifacts_343i["summary"])
    _write_json(dir_343i / "review_queue_strict_human_review_package_343i_qa.json", artifacts_343i["qa_json"])
    _write_json(
        dir_343i / "review_queue_strict_human_review_package_343i_manifest.json",
        artifacts_343i["manifest"],
    )
    _write_json(
        dir_343i / "review_queue_strict_human_review_package_343i_no_write_back_proof.json",
        artifacts_343i["no_write_back_proof_json"],
    )
    _write_json(
        dir_343i / "review_queue_strict_human_review_package_343i_expected_import_contract.json",
        artifacts_343i["expected_import_contract"],
    )
    _write_jsonl(
        dir_343i / "review_queue_strict_human_review_package_343i_review_items.jsonl",
        artifacts_343i["strict_review_items"],
    )
    (dir_343i / "review_queue_strict_human_review_package_343i_review_template.xlsx").write_text(
        "placeholder",
        encoding="utf-8",
    )

    reviewed_rows = [
        json.loads(line)
        for line in (dir_343d / "review_queue_excel_ingestion_343d_reviewed_result.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    export_rows = []
    for row in reviewed_rows:
        if row["resulting_status"] != "REVIEWED_CONFIRMED":
            continue
        export_rows.append(
            {
                "export_candidate_row_id": row["source_row_id"],
                "source_preview_row_id": f"preview::{row['queue_item_id']}",
                "review_item_id": row["review_item_id"],
                "metric_standardized": row["metric_standardized"],
                "year_standardized": row["year_standardized"],
                "value_numeric": row["value_numeric"],
                "normalized_unit": row["normalized_unit"],
                "data_trust_level": "HUMAN_REVIEWED",
                "export_scope_status": "AUDIT_LABELED_HUMAN_SCOPE",
                "display_warning": "human reviewed pilot row",
                "required_disclaimer": "False",
                "required_disclaimer_text": "",
                "not_formal_client_export": "True",
                "formal_client_export_allowed": "False",
                "client_ready": "False",
                "production_ready": "False",
                "final_confirmed": "False",
                "package_row_status": "INCLUDED_IN_AUDIT_LABELED_PACKAGE",
                "package_warning_level": "MEDIUM",
                "requires_later_audit": "False",
                "source_stage": "342Q",
                "upstream_source_stage": "342J",
                "preview_source_type": "HUMAN_REVIEWED",
                "review_status_for_client_display": "REVIEWED",
                "audit_status": "PASS",
                "audit_reason": "seeded for 343I2 test",
                "audit_label": "AUDIT_LABEL_HUMAN_REVIEWED",
                "display_badge": "REVIEWED_PILOT",
                "package_note": "seeded row",
                "corpus_pdf_id": row["source_pdf_id"],
                "file_name": f"{row['source_pdf_id']}.pdf",
                "table_id": f"{row['source_pdf_id']}_table_001",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": "0",
                "bbox": "[1, 2, 3, 4]",
                "image_path": f"D:\\seeded\\{row['source_pdf_id']}\\image.jpg",
                "evidence": "<table><tr><td>EPS</td><td>2024A</td><td>1.2</td></tr></table>",
                "adoption_confidence": "0.97",
                "adoption_evidence": "seeded evidence",
                "correction_pattern": "",
                "correction_reason": "",
                "original_metric_standardized": "",
                "original_normalized_unit": "",
                "collision_key": f"{row['queue_item_id']}::collision",
            }
        )
    dir_342r = root / "output" / "audit_labeled_export_candidate_package_342r"
    _write_csv(dir_342r / "audit_labeled_export_candidate_package_342r_candidates.csv", export_rows)
    _write_json(
        dir_342r / "audit_labeled_export_candidate_package_342r_summary.json",
        {"decision": "AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_READY"},
    )
    (root / "output" / "preview_audit_export_readiness_gate_342q").mkdir(parents=True, exist_ok=True)
    _write_json(
        root / "output" / "preview_audit_export_readiness_gate_342q" / "preview_audit_export_readiness_gate_342q_summary.json",
        {"decision": "PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY"},
    )
    (root / "output" / "package_audit_snapshot_demo_handoff_342s").mkdir(parents=True, exist_ok=True)
    _write_json(
        root / "output" / "package_audit_snapshot_demo_handoff_342s" / "package_audit_snapshot_demo_handoff_342s_artifact_index.json",
        [{"artifact_name": "342R workbook"}],
    )

    return dir_343i, dir_343h, dir_343g, dir_343e, dir_343d, dir_343a


def test_343i2_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_343i, dir_343h, dir_343g, dir_343e, dir_343d, dir_343a = _seed_343i2_inputs(case_root)
        artifacts = build_review_queue_source_evidence_enrichment_343i2(
            strict_human_review_package_343i_dir=dir_343i,
            audit_summary_343h_dir=dir_343h,
            spot_check_ingestion_343g_dir=dir_343g,
            apply_simulation_343e_dir=dir_343e,
            excel_ingestion_343d_dir=dir_343d,
            review_queue_schema_343a_dir=dir_343a,
            audit_labeled_export_candidate_342r_dir=case_root / "output" / "audit_labeled_export_candidate_package_342r",
            preview_audit_342q_dir=case_root / "output" / "preview_audit_export_readiness_gate_342q",
            snapshot_342s_dir=case_root / "output" / "package_audit_snapshot_demo_handoff_342s",
            output_dir=case_root / "output" / "review_queue_source_evidence_enrichment_343i2",
            repo_root=case_root,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION_343I2
        assert summary["input_strict_review_item_count"] == 10
        assert summary["enriched_review_item_count"] == 10
        assert summary["evidence_resolved_count"] == 10
        assert summary["evidence_partial_count"] == 0
        assert summary["evidence_unresolved_count"] == 0
        assert summary["source_pdf_name_available_count"] == 10
        assert summary["source_pdf_path_available_count"] == 0
        assert summary["page_number_available_count"] == 10
        assert summary["source_text_snippet_available_count"] == 10
        assert summary["image_path_available_count"] == 10
        assert summary["enriched_review_template_generated"] is True
        assert summary["source_evidence_enrichment_completed"] is True
        assert summary["waiting_for_strict_human_review"] is True
        assert summary["strict_human_review_result_ingested"] is False
        assert summary["strict_human_review_completed"] is False
        assert summary["requires_strict_human_review"] is True
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["ready_for_343j"] is False
        assert summary["recommended_343j_scope"] == "strict_human_review_result_ingestion_after_user_fills_enriched_workbook"
        assert summary["qa_fail_count"] == 0
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343i2_partial_if_342r_locator_missing() -> None:
    case_root = _make_case_root()
    try:
        dir_343i, dir_343h, dir_343g, dir_343e, dir_343d, dir_343a = _seed_343i2_inputs(case_root)
        csv_path = case_root / "output" / "audit_labeled_export_candidate_package_342r" / "audit_labeled_export_candidate_package_342r_candidates.csv"
        rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8-sig", newline="")))
        rows[0]["source_page"] = ""
        rows[0]["table_id"] = ""
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        artifacts = build_review_queue_source_evidence_enrichment_343i2(
            strict_human_review_package_343i_dir=dir_343i,
            audit_summary_343h_dir=dir_343h,
            spot_check_ingestion_343g_dir=dir_343g,
            apply_simulation_343e_dir=dir_343e,
            excel_ingestion_343d_dir=dir_343d,
            review_queue_schema_343a_dir=dir_343a,
            audit_labeled_export_candidate_342r_dir=case_root / "output" / "audit_labeled_export_candidate_package_342r",
            preview_audit_342q_dir=case_root / "output" / "preview_audit_export_readiness_gate_342q",
            snapshot_342s_dir=case_root / "output" / "package_audit_snapshot_demo_handoff_342s",
            output_dir=case_root / "output" / "review_queue_source_evidence_enrichment_343i2",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == READY_DECISION_343I2
        assert artifacts["summary"]["evidence_partial_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343i2_not_ready_if_343i_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_343i, dir_343h, dir_343g, dir_343e, dir_343d, dir_343a = _seed_343i2_inputs(case_root)
        summary_path = dir_343i / "review_queue_strict_human_review_package_343i_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["decision"] = "STRICT_HUMAN_REVIEW_PACKAGE_343I_NOT_READY"
        _write_json(summary_path, summary)
        artifacts = build_review_queue_source_evidence_enrichment_343i2(
            strict_human_review_package_343i_dir=dir_343i,
            audit_summary_343h_dir=dir_343h,
            spot_check_ingestion_343g_dir=dir_343g,
            apply_simulation_343e_dir=dir_343e,
            excel_ingestion_343d_dir=dir_343d,
            review_queue_schema_343a_dir=dir_343a,
            audit_labeled_export_candidate_342r_dir=case_root / "output" / "audit_labeled_export_candidate_package_342r",
            preview_audit_342q_dir=case_root / "output" / "preview_audit_export_readiness_gate_342q",
            snapshot_342s_dir=case_root / "output" / "package_audit_snapshot_demo_handoff_342s",
            output_dir=case_root / "output" / "review_queue_source_evidence_enrichment_343i2",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION_343I2
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
