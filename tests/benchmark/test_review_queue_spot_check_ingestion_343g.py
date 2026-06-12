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

from datefac.benchmark.review_queue_spot_check_ingestion_343g import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_review_queue_spot_check_ingestion_343g,
)
from datefac.benchmark.review_queue_spot_check_package_343f import (  # noqa: E402
    build_review_queue_spot_check_package_343f,
)
from tests.benchmark.test_review_queue_spot_check_package_343f import _seed_343f_inputs  # noqa: E402


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_spot_check_ingestion_343g"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_343g_inputs(root: Path) -> tuple[Path, Path, Path, Path]:
    dir_343e, dir_343d, dir_343a = _seed_343f_inputs(root)
    dir_343f = root / "output" / "review_queue_spot_check_package_343f"
    artifacts = build_review_queue_spot_check_package_343f(
        apply_simulation_343e_dir=dir_343e,
        excel_ingestion_343d_dir=dir_343d,
        review_queue_schema_343a_dir=dir_343a,
        output_dir=dir_343f,
        repo_root=root,
    )
    _write_json(dir_343f / "review_queue_spot_check_package_343f_summary.json", artifacts["summary"])
    _write_json(dir_343f / "review_queue_spot_check_package_343f_qa.json", artifacts["qa_json"])
    _write_json(dir_343f / "review_queue_spot_check_package_343f_manifest.json", artifacts["manifest"])
    _write_json(dir_343f / "review_queue_spot_check_package_343f_no_write_back_proof.json", artifacts["no_write_back_proof_json"])
    _write_json(dir_343f / "review_queue_spot_check_package_343f_expected_import_contract.json", artifacts["expected_import_contract"])
    _write_json(dir_343f / "review_queue_spot_check_package_343f_priority_plan.json", artifacts["priority_plan"])
    _write_jsonl(dir_343f / "review_queue_spot_check_package_343f_spot_check_items.jsonl", artifacts["spot_check_items"])
    _write_jsonl(dir_343f / "review_queue_spot_check_package_343f_source_check_todo.jsonl", artifacts["source_check_todo"])
    _write_excel(
        dir_343f / "review_queue_spot_check_package_343f_review_template.xlsx",
        {"04_REVIEW_TEMPLATE": artifacts["workbook_sheets"]["04_REVIEW_TEMPLATE"]},
    )

    filled_dir = root / "input" / "review_queue_spot_check_package_343f_filled"
    filled_dir.mkdir(parents=True, exist_ok=True)
    fill_df = pd.DataFrame(artifacts["spot_check_items"])
    fill_df["spot_check_decision"] = [
        "CONFIRM_AI_ASSISTED_RESULT",
        "CORRECT_AI_ASSISTED_RESULT",
        "REJECT_AI_ASSISTED_RESULT",
        "SOURCE_CHECK_REQUIRED",
        "KEEP_HOLD",
        "SKIP_SPOT_CHECK",
    ] + ["CONFIRM_AI_ASSISTED_RESULT"] * (len(fill_df) - 6)
    fill_df["spot_check_metric_standardized"] = ""
    fill_df["spot_check_year_standardized"] = ""
    fill_df["spot_check_value_numeric"] = ""
    fill_df["spot_check_normalized_unit"] = ""
    fill_df.loc[1, "spot_check_metric_standardized"] = "NET_PROFIT"
    fill_df.loc[1, "spot_check_year_standardized"] = "2026E"
    fill_df.loc[1, "spot_check_value_numeric"] = "88.5"
    fill_df.loc[1, "spot_check_normalized_unit"] = "百万元"
    fill_df["spot_check_note"] = ""
    fill_df.loc[2, "spot_check_note"] = "reject in test"
    fill_df.loc[3, "spot_check_note"] = "source check needed"
    fill_df.loc[4, "spot_check_note"] = "hold for later"
    fill_df.loc[5, "spot_check_note"] = "skip in this batch"
    fill_df["spot_checker_id"] = "chatgpt_assisted_spot_check"
    fill_df["spot_checked_at"] = "2026-06-12"
    filled_workbook = filled_dir / "review_queue_spot_check_package_343f_review_template_filled.xlsx"
    _write_excel(filled_workbook, {"04_REVIEW_TEMPLATE": fill_df})
    return dir_343f, dir_343e, dir_343a, filled_workbook


def test_343g_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_343f, dir_343e, dir_343a, filled_workbook = _seed_343g_inputs(case_root)
        artifacts = build_review_queue_spot_check_ingestion_343g(
            spot_check_package_343f_dir=dir_343f,
            apply_simulation_343e_dir=dir_343e,
            review_queue_schema_343a_dir=dir_343a,
            filled_workbook=filled_workbook,
            output_dir=case_root / "output" / "review_queue_spot_check_ingestion_343g",
            repo_root=case_root,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION
        assert summary["filled_spot_check_row_count"] == 12
        assert summary["valid_row_count"] == 12
        assert summary["invalid_row_count"] == 0
        assert summary["confirm_ai_assisted_result_count"] == 7
        assert summary["correct_ai_assisted_result_count"] == 1
        assert summary["reject_ai_assisted_result_count"] == 1
        assert summary["source_check_required_count"] == 1
        assert summary["keep_hold_count"] == 1
        assert summary["skip_spot_check_count"] == 1
        assert summary["validation_error_count"] == 0
        assert summary["review_source_type"] == "AI_ASSISTED_REVIEW"
        assert summary["spot_check_source_type"] == "AI_ASSISTED_SPOT_CHECK"
        assert summary["not_pure_human_review"] is True
        assert summary["strict_human_review_completed"] is False
        assert summary["requires_strict_human_review"] is True
        assert summary["apply_mode"] == "SIMULATION_ONLY"
        assert summary["spot_check_result_ingested"] is True
        assert summary["spot_check_result_jsonl_generated"] is True
        assert summary["ready_for_343h"] is True
        assert summary["recommended_343h_scope"] == "ai_assisted_spot_check_audit_summary_and_strict_human_gap_report"
        assert summary["qa_fail_count"] == 0
        assert all(row["spot_check_source_type"] == "AI_ASSISTED_SPOT_CHECK" for row in artifacts["result_rows"])
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343g_not_ready_if_empty_decision_exists() -> None:
    case_root = _make_case_root()
    try:
        dir_343f, dir_343e, dir_343a, filled_workbook = _seed_343g_inputs(case_root)
        df = pd.read_excel(filled_workbook, sheet_name="04_REVIEW_TEMPLATE")
        df.loc[0, "spot_check_decision"] = ""
        _write_excel(filled_workbook, {"04_REVIEW_TEMPLATE": df})
        artifacts = build_review_queue_spot_check_ingestion_343g(
            spot_check_package_343f_dir=dir_343f,
            apply_simulation_343e_dir=dir_343e,
            review_queue_schema_343a_dir=dir_343a,
            filled_workbook=filled_workbook,
            output_dir=case_root / "output" / "review_queue_spot_check_ingestion_343g",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["invalid_row_count"] >= 1
        assert artifacts["summary"]["validation_error_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343g_not_ready_if_correct_missing_unit() -> None:
    case_root = _make_case_root()
    try:
        dir_343f, dir_343e, dir_343a, filled_workbook = _seed_343g_inputs(case_root)
        df = pd.read_excel(filled_workbook, sheet_name="04_REVIEW_TEMPLATE")
        df.loc[1, "spot_check_normalized_unit"] = ""
        _write_excel(filled_workbook, {"04_REVIEW_TEMPLATE": df})
        artifacts = build_review_queue_spot_check_ingestion_343g(
            spot_check_package_343f_dir=dir_343f,
            apply_simulation_343e_dir=dir_343e,
            review_queue_schema_343a_dir=dir_343a,
            filled_workbook=filled_workbook,
            output_dir=case_root / "output" / "review_queue_spot_check_ingestion_343g",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["validation_error_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343g_not_ready_if_source_check_missing_note() -> None:
    case_root = _make_case_root()
    try:
        dir_343f, dir_343e, dir_343a, filled_workbook = _seed_343g_inputs(case_root)
        df = pd.read_excel(filled_workbook, sheet_name="04_REVIEW_TEMPLATE")
        df.loc[3, "spot_check_note"] = ""
        _write_excel(filled_workbook, {"04_REVIEW_TEMPLATE": df})
        artifacts = build_review_queue_spot_check_ingestion_343g(
            spot_check_package_343f_dir=dir_343f,
            apply_simulation_343e_dir=dir_343e,
            review_queue_schema_343a_dir=dir_343a,
            filled_workbook=filled_workbook,
            output_dir=case_root / "output" / "review_queue_spot_check_ingestion_343g",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["validation_error_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
