from __future__ import annotations

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
from datefac.benchmark.review_queue_strict_human_review_package_343i import (  # noqa: E402
    NOT_READY_DECISION_343I,
    READY_DECISION_343I,
    build_review_queue_strict_human_review_package_343i,
)
from tests.benchmark.test_review_queue_audit_summary_343h import _seed_343h_inputs  # noqa: E402


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_review_queue_strict_human_review_package_343i"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_343i_inputs(root: Path) -> tuple[Path, Path, Path]:
    dir_343g, dir_343f, dir_343e, dir_343d, dir_343a = _seed_343h_inputs(root)
    dir_343h = root / "output" / "review_queue_audit_summary_343h"
    artifacts = build_review_queue_audit_summary_343h(
        spot_check_ingestion_343g_dir=dir_343g,
        spot_check_package_343f_dir=dir_343f,
        apply_simulation_343e_dir=dir_343e,
        excel_ingestion_343d_dir=dir_343d,
        review_queue_schema_343a_dir=dir_343a,
        output_dir=dir_343h,
        repo_root=root,
    )
    _write_json(dir_343h / "review_queue_audit_summary_343h_summary.json", artifacts["summary"])
    _write_json(dir_343h / "review_queue_audit_summary_343h_qa.json", artifacts["qa_json"])
    _write_json(dir_343h / "review_queue_audit_summary_343h_manifest.json", artifacts["manifest"])
    _write_json(
        dir_343h / "review_queue_audit_summary_343h_no_write_back_proof.json",
        artifacts["no_write_back_proof_json"],
    )
    _write_json(
        dir_343h / "review_queue_audit_summary_343h_audit_matrix.json",
        artifacts["audit_matrix"],
    )
    _write_json(
        dir_343h / "review_queue_audit_summary_343h_client_export_gate.json",
        artifacts["client_export_gate"],
    )
    _write_json(
        dir_343h / "review_queue_audit_summary_343h_next_action_plan.json",
        artifacts["next_action_plan"],
    )
    _write_jsonl(
        dir_343h / "review_queue_audit_summary_343h_gap_items.jsonl",
        artifacts["gap_items"],
    )
    _write_jsonl(
        dir_343h / "review_queue_audit_summary_343h_confirmed_ai_assisted_items.jsonl",
        artifacts["confirmed_items"],
    )
    _write_jsonl(
        dir_343h / "review_queue_audit_summary_343h_source_check_backlog.jsonl",
        artifacts["source_check_backlog"],
    )
    (dir_343h / "review_queue_audit_summary_343h_report.md").write_text("ok", encoding="utf-8")
    (
        dir_343h / "review_queue_audit_summary_343h_strict_human_gap_report.md"
    ).write_text("ok", encoding="utf-8")
    return dir_343h, dir_343g, dir_343a


def test_343i_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_343h, dir_343g, dir_343a = _seed_343i_inputs(case_root)
        artifacts = build_review_queue_strict_human_review_package_343i(
            audit_summary_343h_dir=dir_343h,
            spot_check_ingestion_343g_dir=dir_343g,
            review_queue_schema_343a_dir=dir_343a,
            output_dir=case_root / "output" / "review_queue_strict_human_review_package_343i",
            repo_root=case_root,
        )
        summary = artifacts["summary"]
        assert summary["decision"] == READY_DECISION_343I
        assert summary["review_queue_schema_version"] == "343A.review_queue.v1"
        assert summary["input_ai_assisted_confirmed_count"] == 10
        assert summary["strict_review_item_count"] == 10
        assert summary["source_check_backlog_context_count"] == 1
        assert summary["strict_human_gap_item_count"] == 12
        assert summary["strict_human_review_package_generated"] is True
        assert summary["review_template_generated"] is True
        assert summary["reviewer_instructions_generated"] is True
        assert summary["fill_guide_generated"] is True
        assert summary["expected_import_contract_generated"] is True
        assert summary["waiting_for_strict_human_review"] is True
        assert summary["strict_human_review_result_ingested"] is False
        assert summary["strict_human_review_completed"] is False
        assert summary["requires_strict_human_review"] is True
        assert summary["formal_client_export_allowed"] is False
        assert summary["client_ready"] is False
        assert summary["production_ready"] is False
        assert summary["ready_for_343j"] is False
        assert summary["recommended_343j_scope"] == "strict_human_review_result_ingestion_after_user_fills_workbook"
        assert summary["qa_fail_count"] == 0
        assert all(
            item["strict_review_decision"] == ""
            for item in artifacts["strict_review_items"]
        )
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343i_not_ready_if_343h_not_ready() -> None:
    case_root = _make_case_root()
    try:
        dir_343h, dir_343g, dir_343a = _seed_343i_inputs(case_root)
        summary_path = dir_343h / "review_queue_audit_summary_343h_summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["decision"] = "AI_ASSISTED_SPOT_CHECK_AUDIT_SUMMARY_343H_NOT_READY"
        _write_json(summary_path, summary)
        artifacts = build_review_queue_strict_human_review_package_343i(
            audit_summary_343h_dir=dir_343h,
            spot_check_ingestion_343g_dir=dir_343g,
            review_queue_schema_343a_dir=dir_343a,
            output_dir=case_root / "output" / "review_queue_strict_human_review_package_343i",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION_343I
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_343i_not_ready_if_gate_turns_true() -> None:
    case_root = _make_case_root()
    try:
        dir_343h, dir_343g, dir_343a = _seed_343i_inputs(case_root)
        gate_path = dir_343h / "review_queue_audit_summary_343h_client_export_gate.json"
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        gate["formal_client_export_allowed"] = True
        _write_json(gate_path, gate)
        artifacts = build_review_queue_strict_human_review_package_343i(
            audit_summary_343h_dir=dir_343h,
            spot_check_ingestion_343g_dir=dir_343g,
            review_queue_schema_343a_dir=dir_343a,
            output_dir=case_root / "output" / "review_queue_strict_human_review_package_343i",
            repo_root=case_root,
        )
        assert artifacts["summary"]["decision"] == NOT_READY_DECISION_343I
        assert artifacts["summary"]["qa_fail_count"] >= 1
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
