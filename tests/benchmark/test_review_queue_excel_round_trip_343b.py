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

from datefac.benchmark.review_queue_excel_round_trip_343b import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_review_queue_excel_round_trip_343b,
)
from datefac.benchmark.review_queue_schema_343a import build_review_queue_schema_343a  # noqa: E402
from tests.benchmark.test_review_queue_schema_343a import _seed_343a_inputs  # noqa: E402


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
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_excel_round_trip_343b"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_343b_inputs(root: Path) -> tuple[Path, Path, Path]:
    dir_342s, dir_342r, dir_342q, dir_342p = _seed_343a_inputs(root)
    dir_343a = root / "output" / "review_queue_schema_343a"
    artifacts = build_review_queue_schema_343a(
        snapshot_342s_dir=dir_342s,
        audit_labeled_package_342r_dir=dir_342r,
        preview_audit_342q_dir=dir_342q,
        reviewed_plus_preview_342p_dir=dir_342p,
        output_dir=dir_343a,
        repo_root=root,
    )
    _write_json(dir_343a / "review_queue_schema_343a_summary.json", artifacts["summary"])
    _write_json(dir_343a / "review_queue_schema_343a_qa.json", artifacts["qa_json"])
    _write_json(dir_343a / "review_queue_schema_343a_schema.json", artifacts["schema_json"])
    _write_json(dir_343a / "review_queue_schema_343a_json_schema.json", artifacts["json_schema"])
    _write_json(dir_343a / "review_queue_schema_343a_excel_template_spec.json", artifacts["excel_template_spec"])
    _write_jsonl(dir_343a / "review_queue_schema_343a_sample_items.jsonl", artifacts["sample_items"])
    _write_excel(dir_343a / "review_queue_schema_343a.xlsx", artifacts["workbook_sheets"])
    (dir_343a / "review_queue_schema_343a_report.md").write_text("ok", encoding="utf-8")
    return dir_343a, dir_342s, dir_342r


def test_343b_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_343a, dir_342s, dir_342r = _seed_343b_inputs(case_root)
        artifacts = build_review_queue_excel_round_trip_343b(
            review_queue_schema_343a_dir=dir_343a,
            snapshot_342s_dir=dir_342s,
            audit_labeled_package_342r_dir=dir_342r,
            output_dir=case_root / "output" / "review_queue_excel_round_trip_343b",
            repo_root=case_root,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION
        assert summary["ready_for_343c"] is True
        assert summary["template_row_count"] == 12
        assert summary["import_simulation_row_count"] == 12
        assert summary["reviewed_result_row_count"] == 12
        assert summary["confirmed_count"] == 3
        assert summary["corrected_count"] == 2
        assert summary["rejected_count"] == 2
        assert summary["needs_source_check_count"] == 3
        assert summary["skipped_count"] == 2
        assert summary["validation_error_count"] == 0
        assert summary["reviewed_result_jsonl_generated"] is True
        assert len(artifacts["validation_errors_json"]["intentional_error_cases"]) == 2
        assert all(case["validation_status"] == "FAIL" for case in artifacts["validation_errors_json"]["intentional_error_cases"])
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343b_not_ready_if_343a_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_343a, dir_342s, dir_342r = _seed_343b_inputs(case_root)
        summary_path = dir_343a / "review_queue_schema_343a_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["decision"] = "REVIEW_QUEUE_SCHEMA_HUMAN_REVIEW_UI_PILOT_343A_NOT_READY"
        summary["ready_for_343b"] = False
        _write_json(summary_path, summary)

        artifacts = build_review_queue_excel_round_trip_343b(
            review_queue_schema_343a_dir=dir_343a,
            snapshot_342s_dir=dir_342s,
            audit_labeled_package_342r_dir=dir_342r,
            output_dir=case_root / "output" / "review_queue_excel_round_trip_343b",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["ready_for_343c"] is False
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
