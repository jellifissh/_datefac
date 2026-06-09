from __future__ import annotations

import json
from pathlib import Path
import sys
import warnings

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.full_human_review_apply_plan_340d import READY_DECISION as READY_340D_DECISION  # noqa: E402
from datefac.trust.post_human_review_sidecar_result_340e import (  # noqa: E402
    READY_DECISION,
    _contains_forbidden_claim,
    build_post_human_review_sidecar_result_340e,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Title is more than 31 characters.*", category=UserWarning)
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)


def _build_340d_plan() -> pd.DataFrame:
    rows = []
    for idx in range(1, 78):
        if idx <= 22:
            action = "FINAL_WOULD_CONFIRM_REVIEWED"
            route = "reviewed_after_human"
            decision = "CONFIRM_AS_REVIEWED"
            corrected_metric = ""
            corrected_year = ""
            corrected_value = ""
            corrected_unit = ""
        elif idx <= 34:
            action = "FINAL_WOULD_APPLY_CORRECTION_AND_CONFIRM"
            route = "reviewed_after_human_corrected"
            decision = "CORRECT_AND_CONFIRM"
            corrected_metric = "net_profit" if idx % 3 else "EPS"
            corrected_year = "2027E"
            corrected_value = f"{1000 + idx}.00"
            corrected_unit = "million_CNY" if corrected_metric == "net_profit" else "yuan"
        elif idx <= 65:
            action = "FINAL_WOULD_REJECT"
            route = "rejected_after_human"
            decision = "REJECT"
            corrected_metric = ""
            corrected_year = ""
            corrected_value = ""
            corrected_unit = ""
        else:
            action = "FINAL_WOULD_KEEP_NEEDS_REVIEW"
            route = "needs_review_after_human"
            decision = "KEEP_NEEDS_REVIEW"
            corrected_metric = ""
            corrected_year = ""
            corrected_value = ""
            corrected_unit = ""

        rows.append(
            {
                "final_apply_id": f"340d::{idx:03d}",
                "review_id": f"340b::{idx:03d}",
                "document": f"doc_{(idx % 3) + 1}.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": idx + 10,
                "metric_before": "net_profit" if idx % 4 else "EPS",
                "year_before": "2027E",
                "value_before": str(100 + idx),
                "unit_before": "" if idx % 5 else "million_CNY",
                "reviewer_decision": decision,
                "corrected_metric": corrected_metric,
                "corrected_year": corrected_year,
                "corrected_value": corrected_value,
                "corrected_unit": corrected_unit,
                "final_dry_run_action": action,
                "final_route_after_apply": route,
                "source_page": (idx % 10) + 1,
                "evidence": f"evidence {idx}",
                "reviewer_notes": f"note {idx}",
                "risk_flags": "duplicate" if idx % 7 == 0 else "",
                "adoption_action_338d": "HOLD_FOR_HUMAN_REVIEW",
                "dry_run_action_340c": "WOULD_CONFIRM_REVIEWED" if action == "FINAL_WOULD_CONFIRM_REVIEWED" else action,
            }
        )
    return pd.DataFrame(rows)


def _build_runtime_artifacts(tmp_path: Path) -> dict:
    repo_root = tmp_path / "repo"
    input_dir = repo_root / "output" / "full_human_review_apply_plan_340d"
    output_dir = repo_root / "output" / "post_human_review_sidecar_result_340e"
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    plan_df = _build_340d_plan()
    risk_df = pd.DataFrame(
        [
            {
                "review_id": row["review_id"],
                "document": row["document"],
                "metric_before": row["metric_before"],
                "reviewer_decision": row["reviewer_decision"],
                "corrected_metric": row["corrected_metric"],
                "corrected_unit": row["corrected_unit"],
                "risk_flags": row["risk_flags"],
                "duplicate_risk_flag": "duplicate" in str(row["risk_flags"]),
                "missing_unit_risk_flag": False,
                "percent_value_risk_flag": False,
            }
            for row in plan_df.to_dict(orient="records")
        ]
    )

    _write_json(alias_asset, {})
    _write_json(scope_asset, {})
    _write_json(
        input_dir / "full_human_review_apply_plan_340d_summary.json",
        {
            "total_review_queue_count": 77,
            "final_confirm_count": 22,
            "final_correct_and_confirm_count": 12,
            "final_reject_count": 31,
            "final_keep_needs_review_count": 12,
            "final_needs_more_context_count": 0,
            "final_reviewed_after_human_candidate_count": 34,
            "final_non_reviewed_after_human_count": 43,
            "qa_fail_count": 0,
            "decision": READY_340D_DECISION,
        },
    )
    _write_excel(
        input_dir / "full_human_review_apply_plan_340d.xlsx",
        {
            "02_FINAL_APPLY_PLAN": plan_df,
            "07_DUPLICATE_AND_UNIT_RISK_AUDIT": risk_df,
        },
    )

    artifacts = build_post_human_review_sidecar_result_340e(
        full_human_review_apply_340d_dir=input_dir,
        output_dir=output_dir,
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )
    return {"artifacts": artifacts}


def test_contains_forbidden_claim_respects_negation() -> None:
    assert _contains_forbidden_claim("This is production-ready.", ["production-ready"])
    assert not _contains_forbidden_claim("This is not production-ready.", ["production-ready"])


def test_build_post_human_review_sidecar_result_340e(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path)["artifacts"]
    summary = artifacts["summary"]
    assert summary["total_input_rows"] == 77
    assert summary["reviewed_after_human_count"] == 22
    assert summary["reviewed_after_human_corrected_count"] == 12
    assert summary["reviewed_after_human_total_count"] == 34
    assert summary["rejected_after_human_count"] == 31
    assert summary["needs_review_after_human_count"] == 12
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_DECISION
    corrected_df = artifacts["workbook_sheets"]["02_REVIEWED_HUMAN_CORRECTED"]
    assert len(corrected_df) == 12
    assert "final_metric" in corrected_df.columns


def test_invalid_340d_state_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    input_dir = repo_root / "output" / "full_human_review_apply_plan_340d"
    output_dir = repo_root / "output" / "post_human_review_sidecar_result_340e"
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    plan_df = _build_340d_plan()
    risk_df = pd.DataFrame([{"review_id": "340b::001"}])
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})
    _write_json(input_dir / "full_human_review_apply_plan_340d_summary.json", {"qa_fail_count": 1, "decision": "BAD"})
    _write_excel(input_dir / "full_human_review_apply_plan_340d.xlsx", {"02_FINAL_APPLY_PLAN": plan_df, "07_DUPLICATE_AND_UNIT_RISK_AUDIT": risk_df})
    artifacts = build_post_human_review_sidecar_result_340e(
        full_human_review_apply_340d_dir=input_dir,
        output_dir=output_dir,
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )
    assert artifacts["summary"]["qa_fail_count"] > 0
