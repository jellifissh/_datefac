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

from datefac.benchmark.review_queue_excel_ingestion_343d import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_review_queue_excel_ingestion_343d,
)
from datefac.benchmark.review_queue_real_excel_review_343c import build_review_queue_real_excel_review_343c  # noqa: E402
from tests.benchmark.test_review_queue_real_excel_review_343c import _seed_343c_inputs  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_excel_ingestion_343d"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_343d_inputs(root: Path) -> tuple[Path, Path, Path]:
    dir_343b, dir_343a, dir_342s = _seed_343c_inputs(root)
    dir_343c = root / "output" / "review_queue_real_excel_review_343c"
    artifacts = build_review_queue_real_excel_review_343c(
        excel_round_trip_343b_dir=dir_343b,
        review_queue_schema_343a_dir=dir_343a,
        snapshot_342s_dir=dir_342s,
        output_dir=dir_343c,
        repo_root=root,
    )
    _write_json(dir_343c / "review_queue_real_excel_review_343c_summary.json", artifacts["summary"])
    _write_json(dir_343c / "review_queue_real_excel_review_343c_qa.json", artifacts["qa_json"])
    _write_json(dir_343c / "review_queue_real_excel_review_343c_manifest.json", artifacts["manifest"])
    _write_json(dir_343c / "review_queue_real_excel_review_343c_no_write_back_proof.json", artifacts["no_write_back_proof_json"])
    _write_json(dir_343c / "review_queue_real_excel_review_343c_expected_import_contract.json", artifacts["expected_import_contract"])
    _write_excel(dir_343c / "review_queue_real_excel_review_343c_review_template.xlsx", artifacts["review_template_sheets"])

    filled_dir = root / "input" / "review_queue_real_excel_review_343c_filled"
    filled_dir.mkdir(parents=True, exist_ok=True)
    fill_df = pd.DataFrame(artifacts["selected_rows"])
    fill_df["reviewer_decision"] = ["CONFIRM", "NEEDS_SOURCE_CHECK", "SKIP"] + ["CONFIRM"] * (len(fill_df) - 3)
    fill_df["reviewer_note"] = ["", "need source check", "skip for later"] + ["confirmed"] * (len(fill_df) - 3)
    fill_df["reviewer_id"] = "chatgpt_assisted_review"
    fill_df["reviewed_at"] = "2026-06-12"
    _write_excel(
        filled_dir / "review_queue_real_excel_review_343c_review_template_filled.xlsx",
        {"04_FILLABLE_REVIEW": fill_df},
    )
    return dir_343c, dir_343a, filled_dir / "review_queue_real_excel_review_343c_review_template_filled.xlsx"


def test_343d_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_343c, dir_343a, filled_workbook = _seed_343d_inputs(case_root)
        artifacts = build_review_queue_excel_ingestion_343d(
            real_excel_review_343c_dir=dir_343c,
            review_queue_schema_343a_dir=dir_343a,
            filled_workbook=filled_workbook,
            output_dir=case_root / "output" / "review_queue_excel_ingestion_343d",
            repo_root=case_root,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION
        assert summary["filled_row_count"] == 12
        assert summary["valid_row_count"] == 12
        assert summary["invalid_row_count"] == 0
        assert summary["review_source_type"] == "AI_ASSISTED_REVIEW"
        assert summary["not_pure_human_review"] is True
        assert summary["strict_human_review_completed"] is False
        assert summary["requires_human_spot_check"] is True
        assert summary["reviewed_result_ingested"] is True
        assert summary["reviewed_result_jsonl_generated"] is True
        assert summary["ready_for_343e"] is True
        assert summary["recommended_343e_scope"] == "ai_assisted_review_result_apply_simulation_and_audit_gate"
        assert summary["qa_fail_count"] == 0
        assert all(row["review_source_type"] == "AI_ASSISTED_REVIEW" for row in artifacts["reviewed_result_rows"])
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343d_not_ready_if_empty_decision_exists() -> None:
    case_root = _make_case_root()
    try:
        dir_343c, dir_343a, filled_workbook = _seed_343d_inputs(case_root)
        df = pd.read_excel(filled_workbook, sheet_name="04_FILLABLE_REVIEW")
        df.loc[0, "reviewer_decision"] = ""
        _write_excel(filled_workbook, {"04_FILLABLE_REVIEW": df})
        artifacts = build_review_queue_excel_ingestion_343d(
            real_excel_review_343c_dir=dir_343c,
            review_queue_schema_343a_dir=dir_343a,
            filled_workbook=filled_workbook,
            output_dir=case_root / "output" / "review_queue_excel_ingestion_343d",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["invalid_row_count"] >= 1
        assert artifacts["summary"]["validation_error_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
