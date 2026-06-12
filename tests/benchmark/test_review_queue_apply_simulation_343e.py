from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_apply_simulation_343e import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_review_queue_apply_simulation_343e,
)
from tests.benchmark.test_review_queue_excel_ingestion_343d import _seed_343d_inputs  # noqa: E402
from datefac.benchmark.review_queue_excel_ingestion_343d import build_review_queue_excel_ingestion_343d  # noqa: E402


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_apply_simulation_343e"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_343e_inputs(root: Path) -> tuple[Path, Path]:
    dir_343c, dir_343a, filled_workbook = _seed_343d_inputs(root)
    dir_343d = root / "output" / "review_queue_excel_ingestion_343d"
    artifacts = build_review_queue_excel_ingestion_343d(
        real_excel_review_343c_dir=dir_343c,
        review_queue_schema_343a_dir=dir_343a,
        filled_workbook=filled_workbook,
        output_dir=dir_343d,
        repo_root=root,
    )
    _write_json(dir_343d / "review_queue_excel_ingestion_343d_summary.json", artifacts["summary"])
    _write_json(dir_343d / "review_queue_excel_ingestion_343d_qa.json", artifacts["qa_json"])
    _write_json(dir_343d / "review_queue_excel_ingestion_343d_no_write_back_proof.json", artifacts["no_write_back_proof_json"])
    _write_jsonl(dir_343d / "review_queue_excel_ingestion_343d_reviewed_result.jsonl", artifacts["reviewed_result_rows"])
    (dir_343d / "review_queue_excel_ingestion_343d_ai_assisted_review_disclosure.md").write_text("ok", encoding="utf-8")
    return dir_343d, dir_343a


def test_343e_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_343d, dir_343a = _seed_343e_inputs(case_root)
        artifacts = build_review_queue_apply_simulation_343e(
            excel_ingestion_343d_dir=dir_343d,
            review_queue_schema_343a_dir=dir_343a,
            output_dir=case_root / "output" / "review_queue_apply_simulation_343e",
            repo_root=case_root,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION
        assert summary["input_reviewed_result_row_count"] == 12
        assert summary["apply_plan_row_count"] == 12
        assert summary["simulated_sidecar_row_count"] == 10
        assert summary["hold_row_count"] == 2
        assert summary["simulate_confirm_apply_count"] == 10
        assert summary["simulate_correction_apply_count"] == 0
        assert summary["hold_rejected_count"] == 0
        assert summary["hold_source_check_required_count"] == 1
        assert summary["hold_skipped_count"] == 1
        assert summary["review_source_type"] == "AI_ASSISTED_REVIEW"
        assert summary["not_pure_human_review"] is True
        assert summary["strict_human_review_completed"] is False
        assert summary["requires_human_spot_check"] is True
        assert summary["apply_mode"] == "SIMULATION_ONLY"
        assert summary["apply_simulation_completed"] is True
        assert summary["audit_gate_passed_for_spot_check_package"] is True
        assert summary["ready_for_343f"] is True
        assert summary["recommended_343f_scope"] == "ai_assisted_review_spot_check_package"
        assert summary["qa_fail_count"] == 0
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343e_not_ready_if_disclosure_broken() -> None:
    case_root = _make_case_root()
    try:
        dir_343d, dir_343a = _seed_343e_inputs(case_root)
        result_path = dir_343d / "review_queue_excel_ingestion_343d_reviewed_result.jsonl"
        rows = [json.loads(line) for line in result_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        rows[0]["strict_human_review_completed"] = True
        _write_jsonl(result_path, rows)
        artifacts = build_review_queue_apply_simulation_343e(
            excel_ingestion_343d_dir=dir_343d,
            review_queue_schema_343a_dir=dir_343a,
            output_dir=case_root / "output" / "review_queue_apply_simulation_343e",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
