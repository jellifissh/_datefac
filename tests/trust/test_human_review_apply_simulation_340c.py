from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.human_review_apply_simulation_340c import (  # noqa: E402
    ACTION_BY_DECISION,
    READY_340B_DECISION,
    READY_FULL_DECISION,
    READY_INCREMENTAL_DECISION,
    _build_apply_plan_df,
    _contains_forbidden_claim,
    _validate_filled_rows,
    build_human_review_apply_simulation_340c,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _build_review_queue() -> pd.DataFrame:
    rows = []
    for idx in range(1, 78):
        row = {
            "review_id": f"340b::{idx:03d}",
            "priority": "P1",
            "document": "doc_a.pdf" if idx <= 40 else "doc_b.pdf",
            "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
            "source_row_no": idx + 1,
            "metric_before": "net_profit" if idx in {1, 2, 5} else ("EPS" if idx == 4 else "net_profit_yoy"),
            "year_before": "2028E" if idx == 1 else ("2026E" if idx in {2, 4, 5} else "2028E"),
            "value_before": "2442" if idx == 1 else ("71" if idx == 2 else ("30.20%" if idx == 3 else ("0.64" if idx == 4 else "1816"))),
            "unit_before": "" if idx in {1, 5} else ("million_CNY" if idx == 2 else ("%")),
            "source_page": 12,
            "evidence": f"evidence {idx}",
            "model_decision": "CONFIRM_REVIEWED",
            "model_confidence": "0.91",
            "adoption_action": "HOLD_FOR_HUMAN_REVIEW",
            "adoption_reason": "needs_human_review",
            "deterministic_guard_result": "PASS",
            "risk_flags": "test",
            "recommended_reviewer_action": "review",
            "reviewer_decision": "",
            "reviewer_corrected_metric": "",
            "reviewer_corrected_year": "",
            "reviewer_corrected_value": "",
            "reviewer_corrected_unit": "",
            "reviewer_notes": "",
        }
        rows.append(row)

    rows[0]["reviewer_decision"] = "CORRECT_AND_CONFIRM"
    rows[0]["reviewer_corrected_metric"] = "net_profit"
    rows[0]["reviewer_corrected_year"] = "2028E"
    rows[0]["reviewer_corrected_value"] = "2442.00"
    rows[0]["reviewer_corrected_unit"] = "million_CNY"
    rows[0]["reviewer_notes"] = "add amount unit"

    rows[1]["reviewer_decision"] = "CONFIRM_AS_REVIEWED"
    rows[1]["reviewer_notes"] = "confirm"

    rows[2]["reviewer_decision"] = "CONFIRM_AS_REVIEWED"
    rows[2]["reviewer_notes"] = "yoy percent is correct"

    rows[3]["reviewer_decision"] = "CORRECT_AND_CONFIRM"
    rows[3]["reviewer_corrected_metric"] = "EPS"
    rows[3]["reviewer_corrected_year"] = "2026E"
    rows[3]["reviewer_corrected_value"] = "0.64"
    rows[3]["reviewer_corrected_unit"] = "yuan"
    rows[3]["reviewer_notes"] = "fix unit"

    rows[4]["reviewer_decision"] = "CORRECT_AND_CONFIRM"
    rows[4]["reviewer_corrected_metric"] = "net_profit"
    rows[4]["reviewer_corrected_year"] = "2026E"
    rows[4]["reviewer_corrected_value"] = "1816.00"
    rows[4]["reviewer_corrected_unit"] = "million_CNY"
    rows[4]["reviewer_notes"] = "add amount unit"
    return pd.DataFrame(rows)


def _extend_to_15_filled_rows(df: pd.DataFrame) -> pd.DataFrame:
    queue_df = df.copy()
    for index in range(5, 15):
        if index < 8:
            queue_df.loc[index, "reviewer_decision"] = "CORRECT_AND_CONFIRM"
            queue_df.loc[index, "reviewer_corrected_metric"] = "net_profit" if index != 7 else "EPS"
            queue_df.loc[index, "reviewer_corrected_year"] = "2027E"
            queue_df.loc[index, "reviewer_corrected_value"] = f"{2000 + index}.00"
            queue_df.loc[index, "reviewer_corrected_unit"] = (
                "million_CNY" if queue_df.loc[index, "reviewer_corrected_metric"] == "net_profit" else "yuan"
            )
            queue_df.loc[index, "reviewer_notes"] = "batch correction"
        else:
            queue_df.loc[index, "reviewer_decision"] = "CONFIRM_AS_REVIEWED"
            queue_df.loc[index, "reviewer_notes"] = "batch confirm"
    return queue_df


def _fill_all_rows(df: pd.DataFrame) -> pd.DataFrame:
    queue_df = df.copy()
    for index in range(len(queue_df)):
        if not str(queue_df.loc[index, "reviewer_decision"]).strip():
            queue_df.loc[index, "reviewer_decision"] = "CONFIRM_AS_REVIEWED"
            queue_df.loc[index, "reviewer_notes"] = "full confirm"
    return queue_df


def _build_runtime_artifacts(tmp_path: Path, review_queue: pd.DataFrame) -> dict:
    repo_root = tmp_path / "repo"
    human_review_dir = repo_root / "output" / "human_review_after_ai_adoption_340b"
    reviewed_dir = repo_root / "output" / "reviewed_strictness_year_alignment_337d"
    adoption_dir = repo_root / "output" / "ai_review_adoption_simulation_338d"
    output_dir = repo_root / "output" / "human_review_apply_simulation_340c"
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    _write_json(alias_asset, {})
    _write_json(scope_asset, {})
    _write_json(
        human_review_dir / "human_review_after_ai_adoption_340b_summary.json",
        {
            "decision": READY_340B_DECISION,
            "qa_fail_count": 0,
            "total_review_queue_count": 77,
        },
    )
    _write_excel(
        human_review_dir / "human_review_after_ai_adoption_340b_review_template.xlsx",
        {"01_REVIEW_QUEUE": review_queue},
    )
    _write_excel(reviewed_dir / "real_test_mineru_client_export_337d.xlsx", {"00_README": pd.DataFrame([{"x": 1}])})
    _write_excel(adoption_dir / "ai_review_adoption_simulation_338d_plan.xlsx", {"00_README": pd.DataFrame([{"x": 1}])})
    artifacts = build_human_review_apply_simulation_340c(
        human_review_340b_dir=human_review_dir,
        reviewed_strictness_337d_dir=reviewed_dir,
        ai_adoption_338d_dir=adoption_dir,
        output_dir=output_dir,
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )
    return {"artifacts": artifacts, "repo_root": repo_root}


def test_validate_filled_rows_matches_partial_pattern() -> None:
    queue_df = _build_review_queue()
    filled_df, pending_df, warnings_df, _, decision_counts = _validate_filled_rows(queue_df)
    assert len(filled_df) == 5
    assert len(pending_df) == 72
    assert len(warnings_df) == 0
    assert decision_counts["CONFIRM_AS_REVIEWED"] == 2
    assert decision_counts["CORRECT_AND_CONFIRM"] == 3


def test_build_apply_plan_maps_actions() -> None:
    queue_df = _build_review_queue()
    filled_df, _, _, _, _ = _validate_filled_rows(queue_df)
    apply_plan_df = _build_apply_plan_df(filled_df)
    first_row = apply_plan_df.to_dict(orient="records")[0]
    assert first_row["dry_run_action"] == ACTION_BY_DECISION["CORRECT_AND_CONFIRM"]
    assert first_row["action_status"] == "NOT_EXECUTED_DRY_RUN_ONLY"


def test_contains_forbidden_claim_respects_negation() -> None:
    assert _contains_forbidden_claim("This is production-ready.", ["production-ready"])
    assert not _contains_forbidden_claim("This is not production-ready.", ["production-ready"])


def test_first_5_row_case_passes_incremental(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path, _build_review_queue())["artifacts"]
    summary = artifacts["summary"]
    assert summary["filled_review_row_count"] == 5
    assert summary["pending_review_row_count"] == 72
    assert summary["confirm_as_reviewed_count"] == 2
    assert summary["correct_and_confirm_count"] == 3
    assert summary["validation_warning_count"] == 0
    assert summary["qa_fail_count"] == 0
    assert summary["no_apply_proof_passed"] is True
    assert summary["decision"] == READY_INCREMENTAL_DECISION


def test_15_filled_row_case_passes_incremental(tmp_path: Path) -> None:
    queue_df = _extend_to_15_filled_rows(_build_review_queue())
    artifacts = _build_runtime_artifacts(tmp_path, queue_df)["artifacts"]
    summary = artifacts["summary"]
    assert summary["filled_review_row_count"] == 15
    assert summary["pending_review_row_count"] == 62
    assert summary["confirm_as_reviewed_count"] == 9
    assert summary["correct_and_confirm_count"] == 6
    assert summary["validation_warning_count"] == 0
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_INCREMENTAL_DECISION


def test_invalid_reviewer_decision_fails(tmp_path: Path) -> None:
    queue_df = _build_review_queue()
    queue_df.loc[0, "reviewer_decision"] = "BAD_DECISION"
    artifacts = _build_runtime_artifacts(tmp_path, queue_df)["artifacts"]
    summary = artifacts["summary"]
    assert summary["validation_warning_count"] >= 1
    assert summary["qa_fail_count"] > 0
    assert summary["decision"] != READY_INCREMENTAL_DECISION


def test_missing_corrected_unit_for_net_profit_fails(tmp_path: Path) -> None:
    queue_df = _build_review_queue()
    queue_df.loc[0, "reviewer_corrected_unit"] = ""
    artifacts = _build_runtime_artifacts(tmp_path, queue_df)["artifacts"]
    summary = artifacts["summary"]
    assert summary["validation_warning_count"] >= 1
    assert summary["qa_fail_count"] > 0


def test_pending_rows_are_allowed(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path, _build_review_queue())["artifacts"]
    summary = artifacts["summary"]
    assert summary["pending_review_row_count"] > 0
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_INCREMENTAL_DECISION


def test_no_write_back_proof_is_required(tmp_path: Path) -> None:
    artifacts = _build_runtime_artifacts(tmp_path, _build_review_queue())["artifacts"]
    summary = artifacts["summary"]
    qa_checks = artifacts["qa_json"]["checks"]
    assert summary["no_apply_proof_passed"] is True
    assert any(
        row["check_name"] == "safety::no_apply_proof_passed" and row["status"] == "PASS"
        for row in qa_checks
    )


def test_full_review_case_can_become_full_ready(tmp_path: Path) -> None:
    queue_df = _fill_all_rows(_build_review_queue())
    artifacts = _build_runtime_artifacts(tmp_path, queue_df)["artifacts"]
    summary = artifacts["summary"]
    assert summary["pending_review_row_count"] == 0
    assert summary["qa_fail_count"] == 0
    assert summary["decision"] == READY_FULL_DECISION
