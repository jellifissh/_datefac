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

from datefac.benchmark.review_queue_audit_summary_343h import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_review_queue_audit_summary_343h,
)
from tests.benchmark.test_review_queue_spot_check_ingestion_343g import _seed_343g_inputs  # noqa: E402
from datefac.benchmark.review_queue_spot_check_ingestion_343g import build_review_queue_spot_check_ingestion_343g  # noqa: E402


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
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_audit_summary_343h"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_343h_inputs(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    dir_343f, dir_343e, dir_343a, filled_workbook = _seed_343g_inputs(root)
    filled_df = pd.read_excel(filled_workbook, sheet_name="04_REVIEW_TEMPLATE")
    filled_df["spot_check_decision"] = "CONFIRM_AI_ASSISTED_RESULT"
    filled_df["spot_check_note"] = ""
    filled_df["spot_check_metric_standardized"] = ""
    filled_df["spot_check_year_standardized"] = ""
    filled_df["spot_check_value_numeric"] = ""
    filled_df["spot_check_normalized_unit"] = ""
    filled_df.loc[
        filled_df["priority_tier"] == "P0_SOURCE_CHECK_REQUIRED",
        ["spot_check_decision", "spot_check_note"],
    ] = ["SOURCE_CHECK_REQUIRED", "source check needed"]
    filled_df.loc[
        filled_df["priority_tier"] == "P2_SKIPPED_OR_AMBIGUOUS",
        ["spot_check_decision", "spot_check_note"],
    ] = ["KEEP_HOLD", "keep hold for later"]
    _write_excel(filled_workbook, {"04_REVIEW_TEMPLATE": filled_df})

    dir_343g = root / "output" / "review_queue_spot_check_ingestion_343g"
    artifacts = build_review_queue_spot_check_ingestion_343g(
        spot_check_package_343f_dir=dir_343f,
        apply_simulation_343e_dir=dir_343e,
        review_queue_schema_343a_dir=dir_343a,
        filled_workbook=filled_workbook,
        output_dir=dir_343g,
        repo_root=root,
    )
    _write_json(dir_343g / "review_queue_spot_check_ingestion_343g_summary.json", artifacts["summary"])
    _write_json(dir_343g / "review_queue_spot_check_ingestion_343g_qa.json", artifacts["qa_json"])
    _write_json(dir_343g / "review_queue_spot_check_ingestion_343g_manifest.json", artifacts["manifest"])
    _write_json(dir_343g / "review_queue_spot_check_ingestion_343g_no_write_back_proof.json", artifacts["no_write_back_proof_json"])
    _write_json(dir_343g / "review_queue_spot_check_ingestion_343g_decision_summary.json", artifacts["decision_summary"])
    _write_jsonl(dir_343g / "review_queue_spot_check_ingestion_343g_result.jsonl", artifacts["result_rows"])
    (dir_343g / "review_queue_spot_check_ingestion_343g_ai_assisted_spot_check_disclosure.md").write_text("ok", encoding="utf-8")

    dir_343d = root / "output" / "review_queue_excel_ingestion_343d"
    if not dir_343d.exists():
        raise AssertionError("expected 343D dir from upstream seed")
    return dir_343g, dir_343f, dir_343e, dir_343d, dir_343a


def test_343h_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_343g, dir_343f, dir_343e, dir_343d, dir_343a = _seed_343h_inputs(case_root)
        artifacts = build_review_queue_audit_summary_343h(
            spot_check_ingestion_343g_dir=dir_343g,
            spot_check_package_343f_dir=dir_343f,
            apply_simulation_343e_dir=dir_343e,
            excel_ingestion_343d_dir=dir_343d,
            review_queue_schema_343a_dir=dir_343a,
            output_dir=case_root / "output" / "review_queue_audit_summary_343h",
            repo_root=case_root,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION
        assert summary["input_spot_check_result_row_count"] == 12
        assert summary["ai_assisted_confirmed_count"] == 10
        assert summary["source_check_required_count"] == 1
        assert summary["keep_hold_count"] == 1
        assert summary["strict_human_gap_item_count"] == 12
        assert summary["source_check_backlog_count"] == 1
        assert summary["audit_stage_count"] == 5
        assert summary["audit_summary_generated"] is True
        assert summary["strict_human_gap_report_generated"] is True
        assert summary["client_export_gate_generated"] is True
        assert summary["next_action_plan_generated"] is True
        assert summary["review_source_type"] == "AI_ASSISTED_REVIEW"
        assert summary["spot_check_source_type"] == "AI_ASSISTED_SPOT_CHECK"
        assert summary["not_pure_human_review"] is True
        assert summary["strict_human_review_completed"] is False
        assert summary["requires_strict_human_review"] is True
        assert summary["apply_mode"] == "SIMULATION_ONLY"
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["ready_for_343i"] is True
        assert summary["recommended_343i_scope"] == "strict_human_review_package_for_ai_assisted_confirmed_rows"
        assert summary["qa_fail_count"] == 0
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343h_not_ready_if_343g_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_343g, dir_343f, dir_343e, dir_343d, dir_343a = _seed_343h_inputs(case_root)
        summary_path = dir_343g / "review_queue_spot_check_ingestion_343g_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["decision"] = "AI_ASSISTED_SPOT_CHECK_INGESTION_343G_NOT_READY"
        _write_json(summary_path, summary)
        artifacts = build_review_queue_audit_summary_343h(
            spot_check_ingestion_343g_dir=dir_343g,
            spot_check_package_343f_dir=dir_343f,
            apply_simulation_343e_dir=dir_343e,
            excel_ingestion_343d_dir=dir_343d,
            review_queue_schema_343a_dir=dir_343a,
            output_dir=case_root / "output" / "review_queue_audit_summary_343h",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
