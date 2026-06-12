from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_apply_simulation_343e import build_review_queue_apply_simulation_343e  # noqa: E402
from datefac.benchmark.review_queue_spot_check_package_343f import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_review_queue_spot_check_package_343f,
)
from tests.benchmark.test_review_queue_apply_simulation_343e import _seed_343e_inputs  # noqa: E402


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_spot_check_package_343f"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_343f_inputs(root: Path) -> tuple[Path, Path, Path]:
    dir_343d, dir_343a = _seed_343e_inputs(root)
    dir_343e = root / "output" / "review_queue_apply_simulation_343e"
    artifacts = build_review_queue_apply_simulation_343e(
        excel_ingestion_343d_dir=dir_343d,
        review_queue_schema_343a_dir=dir_343a,
        output_dir=dir_343e,
        repo_root=root,
    )
    _write_json(dir_343e / "review_queue_apply_simulation_343e_summary.json", artifacts["summary"])
    _write_json(dir_343e / "review_queue_apply_simulation_343e_qa.json", artifacts["qa_json"])
    _write_json(dir_343e / "review_queue_apply_simulation_343e_audit_gate.json", artifacts["audit_gate"])
    _write_json(dir_343e / "review_queue_apply_simulation_343e_risk_register.json", artifacts["risk_register"])
    _write_json(dir_343e / "review_queue_apply_simulation_343e_no_write_back_proof.json", artifacts["no_write_back_proof_json"])
    _write_jsonl(dir_343e / "review_queue_apply_simulation_343e_apply_plan.jsonl", artifacts["apply_plan_rows"])
    _write_jsonl(dir_343e / "review_queue_apply_simulation_343e_simulated_sidecar.jsonl", artifacts["simulated_sidecar_rows"])
    (dir_343e / "review_queue_apply_simulation_343e_ai_assisted_boundary.md").write_text("ok", encoding="utf-8")
    return dir_343e, dir_343d, dir_343a


def test_343f_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_343e, dir_343d, dir_343a = _seed_343f_inputs(case_root)
        artifacts = build_review_queue_spot_check_package_343f(
            apply_simulation_343e_dir=dir_343e,
            excel_ingestion_343d_dir=dir_343d,
            review_queue_schema_343a_dir=dir_343a,
            output_dir=case_root / "output" / "review_queue_spot_check_package_343f",
            repo_root=case_root,
        )
        summary = artifacts["summary"]
        source_check_count = sum(1 for row in artifacts["spot_check_items"] if row["priority_tier"] == "P0_SOURCE_CHECK_REQUIRED")
        sim_applied_count = sum(1 for row in artifacts["spot_check_items"] if row["priority_tier"] == "P1_AI_ASSISTED_SIM_APPLIED")
        skipped_count = sum(1 for row in artifacts["spot_check_items"] if row["priority_tier"] == "P2_SKIPPED_OR_AMBIGUOUS")
        assert summary["decision"] == READY_DECISION
        assert summary["input_apply_plan_row_count"] == 12
        assert summary["input_simulated_sidecar_row_count"] == 10
        assert summary["spot_check_item_count"] == 12
        assert summary["simulated_applied_spot_check_count"] == sim_applied_count == 10
        assert summary["source_check_required_count"] == source_check_count == 1
        assert summary["skipped_hold_count"] == skipped_count == 1
        assert summary["priority_tier_count"] == 3
        assert summary["review_template_generated"] is True
        assert summary["source_check_todo_generated"] is True
        assert summary["expected_import_contract_generated"] is True
        assert summary["review_source_type"] == "AI_ASSISTED_REVIEW"
        assert summary["not_pure_human_review"] is True
        assert summary["strict_human_review_completed"] is False
        assert summary["requires_human_spot_check"] is True
        assert summary["apply_mode"] == "SIMULATION_ONLY"
        assert summary["spot_check_package_generated"] is True
        assert summary["waiting_for_spot_check"] is True
        assert summary["spot_check_result_ingested"] is False
        assert summary["ready_for_343g"] is False
        assert summary["recommended_343g_scope"] == "ai_assisted_review_spot_check_result_ingestion_after_user_fills_workbook"
        assert summary["qa_fail_count"] == 0
        assert len(artifacts["source_check_todo"]) == source_check_count
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343f_not_ready_if_apply_mode_broken() -> None:
    case_root = _make_case_root()
    try:
        dir_343e, dir_343d, dir_343a = _seed_343f_inputs(case_root)
        apply_plan_path = dir_343e / "review_queue_apply_simulation_343e_apply_plan.jsonl"
        rows = [json.loads(line) for line in apply_plan_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        rows[0]["apply_mode"] = "REAL_APPLY"
        _write_jsonl(apply_plan_path, rows)
        artifacts = build_review_queue_spot_check_package_343f(
            apply_simulation_343e_dir=dir_343e,
            excel_ingestion_343d_dir=dir_343d,
            review_queue_schema_343a_dir=dir_343a,
            output_dir=case_root / "output" / "review_queue_spot_check_package_343f",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
