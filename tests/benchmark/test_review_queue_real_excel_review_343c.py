from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_excel_round_trip_343b import build_review_queue_excel_round_trip_343b  # noqa: E402
from datefac.benchmark.review_queue_real_excel_review_343c import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_review_queue_real_excel_review_343c,
)
from datefac.review_queue.real_excel_review_343c import EDITABLE_REVIEWER_COLUMNS  # noqa: E402
from tests.benchmark.test_review_queue_excel_round_trip_343b import _seed_343b_inputs  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_real_excel_review_343c"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_343c_inputs(root: Path) -> tuple[Path, Path, Path]:
    dir_343a, dir_342s, dir_342r = _seed_343b_inputs(root)
    dir_343b = root / "output" / "review_queue_excel_round_trip_343b"
    artifacts = build_review_queue_excel_round_trip_343b(
        review_queue_schema_343a_dir=dir_343a,
        snapshot_342s_dir=dir_342s,
        audit_labeled_package_342r_dir=dir_342r,
        output_dir=dir_343b,
        repo_root=root,
    )
    _write_json(dir_343b / "review_queue_excel_round_trip_343b_summary.json", artifacts["summary"])
    _write_json(dir_343b / "review_queue_excel_round_trip_343b_qa.json", artifacts["qa_json"])
    _write_json(dir_343b / "review_queue_excel_round_trip_343b_manifest.json", artifacts["manifest"])
    _write_json(dir_343b / "review_queue_excel_round_trip_343b_no_write_back_proof.json", artifacts["no_write_back_proof_json"])
    _write_excel(dir_343b / "review_queue_excel_round_trip_343b.xlsx", artifacts["workbook_sheets"])
    _write_excel(dir_343b / "review_queue_excel_round_trip_343b_review_template.xlsx", artifacts["review_template_sheets"])
    _write_excel(dir_343b / "review_queue_excel_round_trip_343b_import_simulation.xlsx", artifacts["import_simulation_sheets"])
    _write_jsonl(dir_343b / "review_queue_excel_round_trip_343b_reviewed_result.jsonl", artifacts["reviewed_result_rows"])
    (dir_343b / "review_queue_excel_round_trip_343b_report.md").write_text("ok", encoding="utf-8")
    return dir_343b, dir_343a, dir_342s


def test_343c_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_343b, dir_343a, dir_342s = _seed_343c_inputs(case_root)
        artifacts = build_review_queue_real_excel_review_343c(
            excel_round_trip_343b_dir=dir_343b,
            review_queue_schema_343a_dir=dir_343a,
            snapshot_342s_dir=dir_342s,
            output_dir=case_root / "output" / "review_queue_real_excel_review_343c",
            repo_root=case_root,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION
        assert summary["review_queue_schema_version"] == "343A.review_queue.v1"
        assert summary["real_review_template_row_count"] == 12
        assert summary["fillable_review_row_count"] == 12
        assert summary["human_reviewed_audit_row_count"] == 3
        assert summary["simulated_direct_review_row_count"] == 4
        assert summary["simulated_corrected_review_row_count"] == 4
        assert summary["summary_derived_review_row_count"] == 1
        assert summary["allowed_decision_count"] == 5
        assert summary["real_review_template_generated"] is True
        assert summary["reviewer_instructions_generated"] is True
        assert summary["fill_guide_generated"] is True
        assert summary["expected_import_contract_generated"] is True
        assert summary["waiting_for_human_review"] is True
        assert summary["reviewed_result_ingested"] is False
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["ready_for_343d"] is False
        assert summary["recommended_343d_scope"] == "real_excel_review_result_ingestion_after_user_fills_workbook"
        assert summary["qa_fail_count"] == 0
        assert summary["no_write_back_proof_passed"] is True
        first_row = artifacts["selected_rows"][0]
        assert all(column in first_row for column in EDITABLE_REVIEWER_COLUMNS)
        assert all(first_row.get(column, "") == "" for column in EDITABLE_REVIEWER_COLUMNS)
        assert artifacts["expected_import_contract"]["required_sheets"] == ["04_FILLABLE_REVIEW"]
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343c_not_ready_if_343b_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_343b, dir_343a, dir_342s = _seed_343c_inputs(case_root)
        summary_path = dir_343b / "review_queue_excel_round_trip_343b_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["decision"] = "REVIEW_QUEUE_EXCEL_ROUND_TRIP_343B_NOT_READY"
        summary["ready_for_343c"] = False
        _write_json(summary_path, summary)

        artifacts = build_review_queue_real_excel_review_343c(
            excel_round_trip_343b_dir=dir_343b,
            review_queue_schema_343a_dir=dir_343a,
            snapshot_342s_dir=dir_342s,
            output_dir=case_root / "output" / "review_queue_real_excel_review_343c",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
