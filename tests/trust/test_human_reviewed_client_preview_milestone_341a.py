from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.client_preview_export_audit_340g import READY_DECISION as READY_340G_DECISION  # noqa: E402
from datefac.trust.human_review_apply_simulation_340c import READY_FULL_DECISION as READY_340C_FULL_DECISION  # noqa: E402
from datefac.trust.human_reviewed_client_preview_milestone_341a import (  # noqa: E402
    READY_DECISION,
    WORKBOOK_SHEETS,
    build_human_reviewed_client_preview_milestone_341a,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_runtime_artifacts(tmp_path: Path, *, ready_340g: bool = True, inconsistent_counts: bool = False) -> dict:
    repo_root = tmp_path / "repo"
    dir_340b = repo_root / "output" / "human_review_after_ai_adoption_340b"
    dir_340c = repo_root / "output" / "human_review_apply_simulation_340c"
    dir_340d = repo_root / "output" / "full_human_review_apply_plan_340d"
    dir_340e = repo_root / "output" / "post_human_review_sidecar_result_340e"
    dir_340f = repo_root / "output" / "client_preview_after_human_review_340f"
    dir_340g = repo_root / "output" / "client_preview_export_audit_340g"
    output_dir = repo_root / "output" / "human_reviewed_client_preview_milestone_341a"
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    _write_json(
        dir_340b / "human_review_after_ai_adoption_340b_summary.json",
        {
            "total_review_queue_count": 77,
            "qa_fail_count": 0,
            "client_ready": False,
            "production_ready": False,
            "decision": "HUMAN_REVIEW_PACKAGE_AFTER_AI_ADOPTION_340B_READY_FOR_MANUAL_REVIEW",
        },
    )
    _write_json(
        dir_340c / "human_review_apply_simulation_340c_summary.json",
        {
            "total_review_queue_count": 77,
            "filled_review_row_count": 77,
            "pending_review_row_count": 0,
            "qa_fail_count": 0,
            "client_ready": False,
            "production_ready": False,
                "decision": READY_340C_FULL_DECISION,
        },
    )
    _write_json(
        dir_340d / "full_human_review_apply_plan_340d_summary.json",
        {
            "final_reviewed_after_human_candidate_count": 35 if inconsistent_counts else 34,
            "qa_fail_count": 0,
            "client_ready": False,
            "production_ready": False,
            "decision": "FULL_HUMAN_REVIEW_APPLY_PLAN_340D_READY",
        },
    )
    _write_json(
        dir_340e / "post_human_review_sidecar_result_340e_summary.json",
        {
            "reviewed_after_human_total_count": 34,
            "qa_fail_count": 0,
            "client_ready": False,
            "production_ready": False,
            "decision": "POST_HUMAN_REVIEW_SIDECAR_RESULT_340E_READY",
        },
    )
    _write_json(
        dir_340f / "client_preview_after_human_review_340f_summary.json",
        {
            "client_preview_core_metric_count": 34,
            "client_preview_ready": True,
            "qa_fail_count": 0,
            "client_ready": False,
            "production_ready": False,
            "decision": "CLIENT_PREVIEW_AFTER_HUMAN_REVIEW_340F_READY",
        },
    )
    _write_json(
        dir_340g / "client_preview_export_audit_340g_summary.json",
        {
            "audited_core_metric_count": 34,
            "confirmed_count": 22,
            "corrected_count": 12,
            "needs_review_count": 12,
            "rejected_count": 31,
            "duplicate_issue_count": 0,
            "unit_issue_count": 0,
            "missing_source_trace_count": 0,
            "unsafe_claim_count": 0,
            "client_preview_audit_passed": ready_340g,
            "qa_fail_count": 0 if ready_340g else 1,
            "client_ready": False,
            "production_ready": False,
            "decision": READY_340G_DECISION if ready_340g else "BAD",
        },
    )

    artifacts = build_human_reviewed_client_preview_milestone_341a(
        human_review_340b_dir=dir_340b,
        human_review_apply_340c_dir=dir_340c,
        full_human_review_apply_340d_dir=dir_340d,
        post_human_review_340e_dir=dir_340e,
        client_preview_340f_dir=dir_340f,
        client_preview_audit_340g_dir=dir_340g,
        output_dir=output_dir,
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )
    return {"artifacts": artifacts}


def test_build_human_reviewed_client_preview_milestone_341a(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path)["artifacts"]
    summary = artifacts["summary"]
    assert summary["demo_ready"] is True
    assert summary["client_preview_ready"] is True
    assert summary["client_ready"] is False
    assert summary["production_ready"] is False
    assert summary["total_review_queue_count_340b"] == 77
    assert summary["reviewed_after_human_candidate_count_340d"] == 34
    assert summary["reviewed_after_human_total_count_340e"] == 34
    assert summary["client_preview_core_metric_count_340f"] == 34
    assert summary["audited_core_metric_count_340g"] == 34
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_DECISION
    assert set(artifacts["workbook_sheets"].keys()) == set(WORKBOOK_SHEETS)


def test_340g_not_ready_fails(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path, ready_340g=False)["artifacts"]
    assert artifacts["summary"]["qa_fail_count"] > 0


def test_inconsistent_counts_fail(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path, inconsistent_counts=True)["artifacts"]
    assert artifacts["summary"]["qa_fail_count"] > 0
