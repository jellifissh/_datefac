from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_source_check_backlog_package_344a import (  # noqa: E402
    build_review_queue_source_check_backlog_package_344a,
)
from datefac.benchmark.review_queue_source_check_evidence_enrichment_344a2 import (  # noqa: E402
    NOT_READY_DECISION_344A2,
    WAITING_DECISION_344A2,
    build_review_queue_source_check_evidence_enrichment_344a2,
)
from tests.benchmark.test_review_queue_source_check_backlog_package_344a import (  # noqa: E402
    AUDIT_343H_DIR,
    DEMO_343N_DIR,
    DEMO_343O_DIR,
    INGEST_343G_DIR,
    PACKAGE_343F_DIR,
    SCHEMA_343A_DIR,
    SIM_343M_DIR,
)


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_source_check_evidence_enrichment_344a2"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_344a2_inputs(case_root: Path) -> tuple[Path, Path]:
    output_root = case_root / "output"
    output_root.mkdir(parents=True, exist_ok=True)

    dir_344a = output_root / "review_queue_source_check_backlog_package_344a"
    artifacts_344a = build_review_queue_source_check_backlog_package_344a(
        demo_audit_snapshot_343o_dir=DEMO_343O_DIR,
        limited_demo_export_package_343n_dir=DEMO_343N_DIR,
        human_confirmed_sidecar_simulation_343m_dir=SIM_343M_DIR,
        audit_summary_343h_dir=AUDIT_343H_DIR,
        spot_check_ingestion_343g_dir=INGEST_343G_DIR,
        spot_check_package_343f_dir=PACKAGE_343F_DIR,
        review_queue_schema_343a_dir=SCHEMA_343A_DIR,
        output_dir=dir_344a,
        repo_root=PROJECT_ROOT,
    )

    def _write_json(path: Path, payload: dict | list) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_jsonl(path: Path, rows: list[dict]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
            encoding="utf-8",
        )

    _write_json(dir_344a / "review_queue_source_check_backlog_package_344a_summary.json", artifacts_344a["summary"])
    _write_json(dir_344a / "review_queue_source_check_backlog_package_344a_qa.json", artifacts_344a["qa_json"])
    _write_json(dir_344a / "review_queue_source_check_backlog_package_344a_manifest.json", artifacts_344a["manifest"])
    _write_json(
        dir_344a / "review_queue_source_check_backlog_package_344a_no_write_back_proof.json",
        artifacts_344a["no_write_back_proof_json"],
    )
    _write_json(
        dir_344a / "review_queue_source_check_backlog_package_344a_evidence_map.json",
        artifacts_344a["evidence_map"],
    )
    _write_json(
        dir_344a / "review_queue_source_check_backlog_package_344a_expected_import_contract.json",
        artifacts_344a["expected_import_contract"],
    )
    _write_jsonl(
        dir_344a / "review_queue_source_check_backlog_package_344a_backlog_items.jsonl",
        artifacts_344a["backlog_items"],
    )
    (dir_344a / "review_queue_source_check_backlog_package_344a_review_template.xlsx").write_text(
        "placeholder",
        encoding="utf-8",
    )
    return dir_344a, output_root


def test_344a2_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_344a, output_root = _seed_344a2_inputs(case_root)
        artifacts = build_review_queue_source_check_evidence_enrichment_344a2(
            source_check_backlog_package_344a_dir=dir_344a,
            demo_audit_snapshot_343o_dir=DEMO_343O_DIR,
            audit_summary_343h_dir=AUDIT_343H_DIR,
            spot_check_ingestion_343g_dir=INGEST_343G_DIR,
            spot_check_package_343f_dir=PACKAGE_343F_DIR,
            source_evidence_enrichment_343i2_dir=PROJECT_ROOT / "output" / "review_queue_source_evidence_enrichment_343i2",
            review_queue_schema_343a_dir=SCHEMA_343A_DIR,
            output_search_root=PROJECT_ROOT / "output",
            output_dir=output_root / "review_queue_source_check_evidence_enrichment_344a2",
            repo_root=PROJECT_ROOT,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == WAITING_DECISION_344A2
        assert summary["review_queue_schema_version"] == "343A.review_queue.v1"
        assert summary["input_source_check_backlog_item_count"] == 19
        assert summary["deduplicated_backlog_item_count"] == 19
        assert summary["evidence_resolved_count"] == 19
        assert summary["evidence_partial_count"] == 0
        assert summary["evidence_unresolved_count"] == 0
        assert summary["source_pdf_name_available_count"] == 19
        assert summary["page_number_available_count"] == 19
        assert summary["image_path_available_count"] == 19
        assert summary["source_text_snippet_available_count"] == 19
        assert summary["match_candidate_count"] >= 19
        assert summary["high_confidence_match_count"] >= 19
        assert summary["auto_enriched_item_count"] == 19
        assert summary["unresolved_item_count"] == 0
        assert summary["source_check_evidence_enrichment_completed"] is True
        assert summary["enriched_review_template_generated"] is True
        assert summary["expected_import_contract_generated"] is True
        assert summary["waiting_for_source_check_review"] is True
        assert summary["source_check_result_ingested"] is False
        assert summary["source_check_backlog_resolved"] is False
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["ready_for_344b"] is False
        assert summary["recommended_344b_scope"] == (
            "source_check_evidence_review_result_ingestion_after_user_fills_workbook"
        )
        assert summary["qa_fail_count"] == 0
        assert all(item["source_check_decision"] == "" for item in artifacts["enriched_backlog_items"])
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_344a2_partial_if_locator_removed() -> None:
    case_root = _make_case_root()
    try:
        dir_344a, output_root = _seed_344a2_inputs(case_root)
        original_csv = (
            PROJECT_ROOT
            / "output"
            / "audit_labeled_export_candidate_package_342r"
            / "audit_labeled_export_candidate_package_342r_candidates.csv"
        )
        local_342r_dir = output_root / "audit_labeled_export_candidate_package_342r"
        local_342r_dir.mkdir(parents=True, exist_ok=True)
        csv_copy = local_342r_dir / "audit_labeled_export_candidate_package_342r_candidates.csv"
        shutil.copy2(original_csv, csv_copy)
        lines = csv_copy.read_text(encoding="utf-8-sig").splitlines()
        header = lines[0].split(",")
        rows = []
        import csv as _csv
        with csv_copy.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(_csv.DictReader(handle))
        target = next(row for row in rows if row["review_item_id"] == "342g::queue::0001")
        target["source_page"] = ""
        target["table_id"] = ""
        target["image_path"] = ""
        target["evidence"] = ""
        with csv_copy.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = _csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        artifacts = build_review_queue_source_check_evidence_enrichment_344a2(
            source_check_backlog_package_344a_dir=dir_344a,
            demo_audit_snapshot_343o_dir=DEMO_343O_DIR,
            audit_summary_343h_dir=AUDIT_343H_DIR,
            spot_check_ingestion_343g_dir=INGEST_343G_DIR,
            spot_check_package_343f_dir=PACKAGE_343F_DIR,
            source_evidence_enrichment_343i2_dir=PROJECT_ROOT / "output" / "review_queue_source_evidence_enrichment_343i2",
            review_queue_schema_343a_dir=SCHEMA_343A_DIR,
            output_search_root=output_root,
            output_dir=output_root / "review_queue_source_check_evidence_enrichment_344a2",
            repo_root=PROJECT_ROOT,
        )
        assert artifacts["summary"]["decision"] == WAITING_DECISION_344A2
        assert artifacts["summary"]["evidence_partial_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_344a2_not_ready_if_344a_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_344a, output_root = _seed_344a2_inputs(case_root)
        summary_path = dir_344a / "review_queue_source_check_backlog_package_344a_summary.json"
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        payload["decision"] = "BROKEN"
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts = build_review_queue_source_check_evidence_enrichment_344a2(
            source_check_backlog_package_344a_dir=dir_344a,
            demo_audit_snapshot_343o_dir=DEMO_343O_DIR,
            audit_summary_343h_dir=AUDIT_343H_DIR,
            spot_check_ingestion_343g_dir=INGEST_343G_DIR,
            spot_check_package_343f_dir=PACKAGE_343F_DIR,
            source_evidence_enrichment_343i2_dir=PROJECT_ROOT / "output" / "review_queue_source_evidence_enrichment_343i2",
            review_queue_schema_343a_dir=SCHEMA_343A_DIR,
            output_search_root=PROJECT_ROOT / "output",
            output_dir=output_root / "review_queue_source_check_evidence_enrichment_344a2",
            repo_root=PROJECT_ROOT,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION_344A2
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
