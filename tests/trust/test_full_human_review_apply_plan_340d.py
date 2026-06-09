from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.full_human_review_apply_plan_340d import (  # noqa: E402
    READY_DECISION,
    _contains_forbidden_claim,
    build_full_human_review_apply_plan_340d,
)
from datefac.trust.human_review_apply_simulation_340c import READY_FULL_DECISION as READY_340C_FULL_DECISION  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _build_340b_queue() -> pd.DataFrame:
    rows = []
    for idx in range(1, 78):
        if idx <= 22:
            reviewer_decision = "CONFIRM_AS_REVIEWED"
            corrected_metric = ""
            corrected_year = ""
            corrected_value = ""
            corrected_unit = ""
        elif idx <= 34:
            reviewer_decision = "CORRECT_AND_CONFIRM"
            corrected_metric = "net_profit" if idx % 3 else "EPS"
            corrected_year = "2027E"
            corrected_value = f"{1000 + idx}.00"
            corrected_unit = "million_CNY" if corrected_metric == "net_profit" else "yuan"
        elif idx <= 65:
            reviewer_decision = "REJECT"
            corrected_metric = ""
            corrected_year = ""
            corrected_value = ""
            corrected_unit = ""
        else:
            reviewer_decision = "KEEP_NEEDS_REVIEW"
            corrected_metric = ""
            corrected_year = ""
            corrected_value = ""
            corrected_unit = ""

        rows.append(
            {
                "review_id": f"340b::{idx:03d}",
                "priority": "P1",
                "document": f"doc_{(idx % 3) + 1}.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": idx + 10,
                "metric_before": "net_profit" if idx % 4 else "EPS",
                "year_before": "2027E",
                "value_before": str(100 + idx),
                "unit_before": "" if idx % 5 else "million_CNY",
                "source_page": (idx % 10) + 1,
                "evidence": f"evidence {idx}",
                "model_decision": "CONFIRM_REVIEWED",
                "model_confidence": "0.88",
                "adoption_action": "HOLD_FOR_HUMAN_REVIEW",
                "adoption_reason": "needs_human_review",
                "deterministic_guard_result": "PASS",
                "risk_flags": "duplicate" if idx % 7 == 0 else "missing_unit" if idx % 5 == 0 else "",
                "recommended_reviewer_action": "review",
                "reviewer_decision": reviewer_decision,
                "reviewer_corrected_metric": corrected_metric,
                "reviewer_corrected_year": corrected_year,
                "reviewer_corrected_value": corrected_value,
                "reviewer_corrected_unit": corrected_unit,
                "reviewer_notes": f"note {idx}",
            }
        )
    return pd.DataFrame(rows)


def _build_340c_plan(review_queue_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    mapping = {
        "CONFIRM_AS_REVIEWED": "WOULD_CONFIRM_REVIEWED",
        "CORRECT_AND_CONFIRM": "WOULD_APPLY_CORRECTION_AND_CONFIRM",
        "KEEP_NEEDS_REVIEW": "WOULD_KEEP_NEEDS_REVIEW",
        "REJECT": "WOULD_REJECT",
        "NEEDS_MORE_CONTEXT": "WOULD_KEEP_NEEDS_MORE_CONTEXT",
    }
    for idx, row in enumerate(review_queue_df.to_dict(orient="records"), start=1):
        rows.append(
            {
                "apply_plan_id": f"340c::{idx:03d}",
                "review_id": row["review_id"],
                "document": row["document"],
                "metric_before": row["metric_before"],
                "year_before": row["year_before"],
                "value_before": row["value_before"],
                "unit_before": row["unit_before"],
                "reviewer_decision": row["reviewer_decision"],
                "corrected_metric": row["reviewer_corrected_metric"],
                "corrected_year": row["reviewer_corrected_year"],
                "corrected_value": row["reviewer_corrected_value"],
                "corrected_unit": row["reviewer_corrected_unit"],
                "dry_run_action": mapping[row["reviewer_decision"]],
                "action_status": "NOT_EXECUTED_DRY_RUN_ONLY",
                "validation_status": "PASS",
                "reviewer_notes": row["reviewer_notes"],
                "source_row_reference": f"01_REVIEW_QUEUE::row_{idx + 1}",
            }
        )
    return pd.DataFrame(rows)


def _build_338d_plan(review_queue_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for idx, row in enumerate(review_queue_df.to_dict(orient="records"), start=1):
        rows.append(
            {
                "adoption_id": f"338d::{idx:03d}",
                "document": row["document"],
                "source_sheet": row["source_sheet"],
                "source_row_no": row["source_row_no"],
                "metric_before": row["metric_before"],
                "year_before": row["year_before"],
                "value_before": row["value_before"],
                "unit_before": row["unit_before"],
                "model_decision": row["model_decision"],
                "confidence": row["model_confidence"],
                "grounding_source": "BOTH",
                "deterministic_guard_result": row["deterministic_guard_result"],
                "adoption_action": row["adoption_action"],
                "adoption_reason": row["adoption_reason"],
                "recommended_route_after_adoption": "reviewed_preview",
            }
        )
    return pd.DataFrame(rows)


def _build_runtime_artifacts(tmp_path: Path) -> dict:
    repo_root = tmp_path / "repo"
    human_review_dir = repo_root / "output" / "human_review_after_ai_adoption_340b"
    apply_340c_dir = repo_root / "output" / "human_review_apply_simulation_340c"
    reviewed_dir = repo_root / "output" / "reviewed_strictness_year_alignment_337d"
    adoption_dir = repo_root / "output" / "ai_review_adoption_simulation_338d"
    output_dir = repo_root / "output" / "full_human_review_apply_plan_340d"
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    review_queue_df = _build_340b_queue()
    plan_340c_df = _build_340c_plan(review_queue_df)
    plan_338d_df = _build_338d_plan(review_queue_df)

    _write_json(alias_asset, {})
    _write_json(scope_asset, {})
    _write_json(human_review_dir / "human_review_after_ai_adoption_340b_summary.json", {"decision": "HUMAN_REVIEW_PACKAGE_AFTER_AI_ADOPTION_340B_READY_FOR_MANUAL_REVIEW"})
    _write_json(
        apply_340c_dir / "human_review_apply_simulation_340c_summary.json",
        {
            "total_review_queue_count": 77,
            "filled_review_row_count": 77,
            "pending_review_row_count": 0,
            "confirm_as_reviewed_count": 22,
            "correct_and_confirm_count": 12,
            "keep_needs_review_count": 12,
            "reject_count": 31,
            "needs_more_context_count": 0,
            "validation_warning_count": 0,
            "qa_fail_count": 0,
            "decision": READY_340C_FULL_DECISION,
        },
    )
    _write_excel(human_review_dir / "human_review_after_ai_adoption_340b_review_template.xlsx", {"01_REVIEW_QUEUE": review_queue_df})
    _write_excel(apply_340c_dir / "human_review_apply_simulation_340c_apply_plan.xlsx", {"01_APPLY_PLAN": plan_340c_df})
    _write_excel(reviewed_dir / "real_test_mineru_client_export_337d.xlsx", {"04_SOURCE_TRACE": pd.DataFrame([{"x": 1}])})
    _write_excel(adoption_dir / "ai_review_adoption_simulation_338d_plan.xlsx", {"02_ADOPTION_PLAN": plan_338d_df})

    artifacts = build_full_human_review_apply_plan_340d(
        human_review_340b_dir=human_review_dir,
        human_review_apply_340c_dir=apply_340c_dir,
        reviewed_strictness_337d_dir=reviewed_dir,
        ai_adoption_338d_dir=adoption_dir,
        output_dir=output_dir,
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )
    return {"artifacts": artifacts, "output_dir": output_dir}


def test_contains_forbidden_claim_respects_negation() -> None:
    assert _contains_forbidden_claim("This is production-ready.", ["production-ready"])
    assert not _contains_forbidden_claim("This is not production-ready.", ["production-ready"])


def test_build_full_human_review_apply_plan_340d(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path)["artifacts"]
    summary = artifacts["summary"]
    assert summary["total_review_queue_count"] == 77
    assert summary["final_confirm_count"] == 22
    assert summary["final_correct_and_confirm_count"] == 12
    assert summary["final_reject_count"] == 31
    assert summary["final_keep_needs_review_count"] == 12
    assert summary["final_needs_more_context_count"] == 0
    assert summary["final_reviewed_after_human_candidate_count"] == 34
    assert summary["final_non_reviewed_after_human_count"] == 43
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_DECISION
    plan_df = artifacts["workbook_sheets"]["02_FINAL_APPLY_PLAN"]
    assert len(plan_df) == 77
    assert set(plan_df["final_dry_run_action"].unique()) == {
        "FINAL_WOULD_CONFIRM_REVIEWED",
        "FINAL_WOULD_APPLY_CORRECTION_AND_CONFIRM",
        "FINAL_WOULD_REJECT",
        "FINAL_WOULD_KEEP_NEEDS_REVIEW",
    }


def test_invalid_340c_state_fails(tmp_path: Path) -> None:
    runtime = _build_runtime_artifacts(tmp_path)
    output_dir = runtime["output_dir"]
    summary_path = output_dir.parent / "human_review_apply_simulation_340c" / "human_review_apply_simulation_340c_summary.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["pending_review_row_count"] = 1
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    repo_root = tmp_path / "repo"
    human_review_dir = repo_root / "output" / "human_review_after_ai_adoption_340b"
    apply_340c_dir = repo_root / "output" / "human_review_apply_simulation_340c"
    reviewed_dir = repo_root / "output" / "reviewed_strictness_year_alignment_337d"
    adoption_dir = repo_root / "output" / "ai_review_adoption_simulation_338d"
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    artifacts = build_full_human_review_apply_plan_340d(
        human_review_340b_dir=human_review_dir,
        human_review_apply_340c_dir=apply_340c_dir,
        reviewed_strictness_337d_dir=reviewed_dir,
        ai_adoption_338d_dir=adoption_dir,
        output_dir=output_dir,
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )
    assert artifacts["summary"]["qa_fail_count"] > 0

