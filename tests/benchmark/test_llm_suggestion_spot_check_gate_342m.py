from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.llm_suggestion_spot_check_gate_342m import (  # noqa: E402
    NOT_READY_DECISION,
    REAL_RESPONSE_READY_DECISION,
    SPOT_CHECK_READY_DECISION,
    WAITING_DECISION,
    build_llm_suggestion_spot_check_gate_342m,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _seed_342m_inputs(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    llm_suggestion_342l_dir = root / "output" / "llm_suggestion_apply_simulation_342l"
    llm_review_342k_dir = root / "output" / "llm_assisted_review_adjudication_342k"
    reviewed_preview_342j_dir = root / "output" / "table_first_reviewed_client_preview_pilot_342j"
    spot_check_reviewed_dir = root / "input" / "spot_check_reviewed_342m"
    llm_response_dir = root / "input" / "llm_review_responses_342m"
    for path in [
        llm_suggestion_342l_dir,
        llm_review_342k_dir,
        reviewed_preview_342j_dir,
        spot_check_reviewed_dir,
        llm_response_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    summary_342l = {
        "decision": "LLM_SUGGESTION_APPLY_SIMULATION_342L_READY",
        "pending_review_count": 4,
        "auto_confirm_candidate_count": 2,
        "spot_check_sample_count": 2,
        "human_required_count": 1,
        "conflict_count": 1,
        "prefill_review_draft_count": 4,
        "prompt_pack_count": 2,
        "request_pack_count": 2,
        "jsonl_parse_error_count": 0,
        "theoretical_review_reduction_count": 2,
        "risk_adjusted_reduction_count": 1,
        "required_human_review_after_strategy": 3,
        "reduction_rate": 0.5,
        "conservative_reduction_rate": 0.25,
        "unit_year_risk_count": 0,
        "duplicate_risk_count": 0,
        "growth_row_risk_count": 0,
        "source_trace_risk_count": 0,
        "metric_mapping_risk_count": 0,
        "ready_for_342m": True,
        "recommended_342m_scope": "llm_suggestion_spot_check_apply_or_real_llm_response_ingestion",
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": True,
    }
    _write_json(llm_suggestion_342l_dir / "llm_suggestion_apply_simulation_342l_summary.json", summary_342l)
    _write_json(
        llm_suggestion_342l_dir / "llm_suggestion_apply_simulation_342l_qa.json",
        {"qa_fail_count": 0, "checks": []},
    )
    _write_json(
        llm_suggestion_342l_dir / "llm_suggestion_apply_simulation_342l_no_write_back_proof.json",
        {"upstream_workbooks_unchanged": True},
    )
    (llm_suggestion_342l_dir / "llm_suggestion_apply_simulation_342l_report.md").write_text(
        "342L report",
        encoding="utf-8",
    )

    auto_candidates_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_1",
                "rule_suggested_decision": "CONFIRM_CELL",
                "dry_run_suggested_decision": "CONFIRM_CELL",
                "suggested_metric_standardized": "revenue",
                "suggested_year_standardized": "2025A",
                "suggested_value_numeric": 100.0,
                "suggested_normalized_unit": "CNYmn",
                "suggested_confidence": 0.99,
                "human_required": False,
                "candidate_reason": "high_confidence",
                "risk_flags": "",
                "review_reason": "clean_case",
                "review_priority": "LOW",
                "review_bucket": "LOW_RISK_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc1.pdf",
                "table_id": "t1",
                "table_type": "INCOME_STATEMENT",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "img1.jpg",
                "source_html_snippet": "<table>row1</table>",
                "simulation_status": "AUTO_CONFIRM_CANDIDATE",
                "not_final_confirmation": True,
            },
            {
                "review_item_id": "item_2",
                "rule_suggested_decision": "CORRECT_AND_CONFIRM",
                "dry_run_suggested_decision": "CORRECT_AND_CONFIRM",
                "suggested_metric_standardized": "net_profit",
                "suggested_year_standardized": "2025A",
                "suggested_value_numeric": 10.0,
                "suggested_normalized_unit": "CNYmn",
                "suggested_confidence": 0.98,
                "human_required": False,
                "candidate_reason": "high_confidence",
                "risk_flags": "",
                "review_reason": "clean_case",
                "review_priority": "LOW",
                "review_bucket": "LOW_RISK_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc1.pdf",
                "table_id": "t1",
                "table_type": "INCOME_STATEMENT",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "img1.jpg",
                "source_html_snippet": "<table>row2</table>",
                "simulation_status": "AUTO_CONFIRM_CANDIDATE",
                "not_final_confirmation": True,
            },
        ]
    )
    spot_check_df = pd.DataFrame(
        [
            {
                "spot_check_id": "spot_1",
                "review_item_id": "item_1",
                "spot_check_reason": "metric_coverage",
                "original_suggestion": "CONFIRM_CELL",
                "suggested_metric_standardized": "revenue",
                "suggested_year_standardized": "2025A",
                "suggested_value_numeric": 100.0,
                "suggested_normalized_unit": "CNYmn",
                "suggested_confidence": 0.99,
                "review_bucket": "LOW_RISK_REVIEW",
                "review_reason": "clean_case",
                "risk_flags": "",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc1.pdf",
                "table_id": "t1",
                "table_type": "INCOME_STATEMENT",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "img1.jpg",
                "source_html_snippet": "<table>row1</table>",
                "reviewer_decision": "",
                "reviewer_note": "",
                "reviewer_id": "",
                "reviewed_at": "",
            },
            {
                "spot_check_id": "spot_2",
                "review_item_id": "item_2",
                "spot_check_reason": "metric_coverage",
                "original_suggestion": "CORRECT_AND_CONFIRM",
                "suggested_metric_standardized": "net_profit",
                "suggested_year_standardized": "2025A",
                "suggested_value_numeric": 10.0,
                "suggested_normalized_unit": "CNYmn",
                "suggested_confidence": 0.98,
                "review_bucket": "LOW_RISK_REVIEW",
                "review_reason": "clean_case",
                "risk_flags": "",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc1.pdf",
                "table_id": "t1",
                "table_type": "INCOME_STATEMENT",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "img1.jpg",
                "source_html_snippet": "<table>row2</table>",
                "reviewer_decision": "",
                "reviewer_note": "",
                "reviewer_id": "",
                "reviewed_at": "",
            },
        ]
    )
    prefill_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_1",
                "rule_suggested_decision": "CONFIRM_CELL",
                "dry_run_suggested_decision": "CONFIRM_CELL",
                "suggested_metric_standardized": "revenue",
                "suggested_year_standardized": "2025A",
                "suggested_value_numeric": 100.0,
                "suggested_normalized_unit": "CNYmn",
                "suggested_confidence": 0.99,
                "reviewer_decision": "",
                "reviewer_metric_standardized": "",
                "reviewer_year_standardized": "",
                "reviewer_value_numeric": "",
                "reviewer_normalized_unit": "",
                "reviewer_note": "",
                "reviewer_id": "",
                "reviewed_at": "",
            },
            {
                "review_item_id": "item_2",
                "rule_suggested_decision": "CORRECT_AND_CONFIRM",
                "dry_run_suggested_decision": "CORRECT_AND_CONFIRM",
                "suggested_metric_standardized": "net_profit",
                "suggested_year_standardized": "2025A",
                "suggested_value_numeric": 10.0,
                "suggested_normalized_unit": "CNYmn",
                "suggested_confidence": 0.98,
                "reviewer_decision": "",
                "reviewer_metric_standardized": "",
                "reviewer_year_standardized": "",
                "reviewer_value_numeric": "",
                "reviewer_normalized_unit": "",
                "reviewer_note": "",
                "reviewer_id": "",
                "reviewed_at": "",
            },
        ]
    )
    human_required_df = pd.DataFrame([{"review_item_id": "item_3"}])
    conflict_blockers_df = pd.DataFrame([{"review_item_id": "item_4", "auto_apply_allowed": False}])
    _write_excel(
        llm_suggestion_342l_dir / "llm_suggestion_apply_simulation_342l.xlsx",
        {
            "03_AUTO_CANDIDATES": auto_candidates_df,
            "04_SPOT_CHECK_SAMPLE": spot_check_df,
            "05_PREFILL_REVIEW_DRAFT": prefill_df,
            "06_HUMAN_REQUIRED": human_required_df,
            "07_CONFLICT_BLOCKERS": conflict_blockers_df,
            "08_REDUCTION_SIMULATION": pd.DataFrame([{"reduction_rate": 0.5}]),
            "09_RISK_AUDIT": pd.DataFrame([{"risk": "clean_case"}]),
            "10_PROMPT_REQUEST_TRACE": pd.DataFrame([{"request_id": "req_1"}]),
            "11_DECISION_POLICY": pd.DataFrame([{"policy": "policy"}]),
            "12_342M_READINESS": pd.DataFrame([{"ready_for_342m": True}]),
            "13_NO_WRITE_BACK": pd.DataFrame([{"proof": True}]),
        },
    )

    prompt_rows = [
        {"request_id": "req_1", "review_item_id": "item_1"},
        {"request_id": "req_2", "review_item_id": "item_2"},
    ]
    request_rows = [
        {"request_id": "req_1", "review_item_id": "item_1"},
        {"request_id": "req_2", "review_item_id": "item_2"},
    ]
    _write_jsonl(
        llm_review_342k_dir / "llm_assisted_review_adjudication_342k_prompt_pack.jsonl",
        prompt_rows,
    )
    _write_jsonl(
        llm_review_342k_dir / "llm_assisted_review_adjudication_342k_request_pack.jsonl",
        request_rows,
    )

    summary_342j = {
        "decision": "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY",
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": 0,
    }
    _write_json(reviewed_preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j_summary.json", summary_342j)

    alias_asset = root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})
    return (
        llm_suggestion_342l_dir,
        llm_review_342k_dir,
        reviewed_preview_342j_dir,
        spot_check_reviewed_dir,
        llm_response_dir,
    )


def test_342m_waiting_for_evidence(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (
        llm_suggestion_342l_dir,
        llm_review_342k_dir,
        reviewed_preview_342j_dir,
        spot_check_reviewed_dir,
        llm_response_dir,
    ) = _seed_342m_inputs(repo_root)
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    artifacts = build_llm_suggestion_spot_check_gate_342m(
        llm_suggestion_342l_dir=llm_suggestion_342l_dir,
        llm_review_342k_dir=llm_review_342k_dir,
        reviewed_preview_342j_dir=reviewed_preview_342j_dir,
        spot_check_reviewed_dir=spot_check_reviewed_dir,
        llm_response_dir=llm_response_dir,
        output_dir=repo_root / "output" / "llm_suggestion_spot_check_gate_342m",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == WAITING_DECISION
    assert summary["ready_for_342n"] is False
    assert summary["reviewed_spot_check_count"] == 0
    assert summary["response_count"] == 0
    assert summary["adoption_candidate_count"] == 0
    assert summary["risk_adjusted_reduction_count"] == 0
    assert summary["required_human_review_after_gate"] == 4
    assert summary["waiting_for_human_spot_check"] is True
    assert summary["waiting_for_real_llm_responses"] is True
    assert artifacts["workbook_sheets"]["03_SPOT_CHECK_TEMPLATE"].shape[0] == 2
    assert len(artifacts["real_llm_response_template_rows"]) == 2


def test_342m_spot_check_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (
        llm_suggestion_342l_dir,
        llm_review_342k_dir,
        reviewed_preview_342j_dir,
        spot_check_reviewed_dir,
        llm_response_dir,
    ) = _seed_342m_inputs(repo_root)
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    reviewed_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_1",
                "reviewer_decision": "CONFIRM_SUGGESTION",
                "reviewer_metric_standardized": "",
                "reviewer_year_standardized": "",
                "reviewer_value_numeric": "",
                "reviewer_normalized_unit": "",
                "reviewer_note": "",
                "reviewer_id": "tester",
                "reviewed_at": "2026-06-10T12:00:00",
            },
            {
                "review_item_id": "item_2",
                "reviewer_decision": "CORRECT_SUGGESTION",
                "reviewer_metric_standardized": "net_profit",
                "reviewer_year_standardized": "",
                "reviewer_value_numeric": "",
                "reviewer_normalized_unit": "",
                "reviewer_note": "ok",
                "reviewer_id": "tester",
                "reviewed_at": "2026-06-10T12:01:00",
            },
        ]
    )
    _write_excel(
        spot_check_reviewed_dir / "llm_suggestion_spot_check_reviewed_342m.xlsx",
        {"01_SPOT_CHECK_REVIEW": reviewed_df},
    )

    artifacts = build_llm_suggestion_spot_check_gate_342m(
        llm_suggestion_342l_dir=llm_suggestion_342l_dir,
        llm_review_342k_dir=llm_review_342k_dir,
        reviewed_preview_342j_dir=reviewed_preview_342j_dir,
        spot_check_reviewed_dir=spot_check_reviewed_dir,
        llm_response_dir=llm_response_dir,
        output_dir=repo_root / "output" / "llm_suggestion_spot_check_gate_342m",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == SPOT_CHECK_READY_DECISION
    assert summary["ready_for_342n"] is True
    assert summary["reviewed_spot_check_count"] == 2
    assert summary["spot_check_validation_error_count"] == 0
    assert summary["adoption_candidate_count"] == 2


def test_342m_invalid_spot_check_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (
        llm_suggestion_342l_dir,
        llm_review_342k_dir,
        reviewed_preview_342j_dir,
        spot_check_reviewed_dir,
        llm_response_dir,
    ) = _seed_342m_inputs(repo_root)
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    reviewed_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_1",
                "reviewer_decision": "BAD_DECISION",
                "reviewer_metric_standardized": "",
                "reviewer_year_standardized": "",
                "reviewer_value_numeric": "",
                "reviewer_normalized_unit": "",
                "reviewer_note": "",
                "reviewer_id": "tester",
                "reviewed_at": "2026-06-10T12:00:00",
            }
        ]
    )
    _write_excel(
        spot_check_reviewed_dir / "llm_suggestion_spot_check_reviewed_342m.xlsx",
        {"01_SPOT_CHECK_REVIEW": reviewed_df},
    )

    artifacts = build_llm_suggestion_spot_check_gate_342m(
        llm_suggestion_342l_dir=llm_suggestion_342l_dir,
        llm_review_342k_dir=llm_review_342k_dir,
        reviewed_preview_342j_dir=reviewed_preview_342j_dir,
        spot_check_reviewed_dir=spot_check_reviewed_dir,
        llm_response_dir=llm_response_dir,
        output_dir=repo_root / "output" / "llm_suggestion_spot_check_gate_342m",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    assert artifacts["summary"]["qa_fail_count"] > 0
    assert artifacts["summary"]["decision"] == NOT_READY_DECISION


def test_342m_real_response_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (
        llm_suggestion_342l_dir,
        llm_review_342k_dir,
        reviewed_preview_342j_dir,
        spot_check_reviewed_dir,
        llm_response_dir,
    ) = _seed_342m_inputs(repo_root)
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"

    response_rows = [
        {
            "request_id": "req_1",
            "review_item_id": "item_1",
            "llm_suggested_decision": "CONFIRM_CELL",
            "llm_suggested_metric_standardized": "revenue",
            "llm_suggested_year_standardized": "2025A",
            "llm_suggested_value_numeric": 100.0,
            "llm_suggested_normalized_unit": "CNYmn",
            "llm_confidence": 0.99,
            "llm_evidence": "match",
            "llm_risk_reason": "low_risk",
            "human_required": False,
        },
        {
            "request_id": "req_2",
            "review_item_id": "item_2",
            "llm_suggested_decision": "CORRECT_AND_CONFIRM",
            "llm_suggested_metric_standardized": "net_profit",
            "llm_suggested_year_standardized": "2025A",
            "llm_suggested_value_numeric": 10.0,
            "llm_suggested_normalized_unit": "CNYmn",
            "llm_confidence": 0.98,
            "llm_evidence": "match",
            "llm_risk_reason": "low_risk",
            "human_required": False,
        },
    ]
    _write_jsonl(llm_response_dir / "responses.jsonl", response_rows)

    artifacts = build_llm_suggestion_spot_check_gate_342m(
        llm_suggestion_342l_dir=llm_suggestion_342l_dir,
        llm_review_342k_dir=llm_review_342k_dir,
        reviewed_preview_342j_dir=reviewed_preview_342j_dir,
        spot_check_reviewed_dir=spot_check_reviewed_dir,
        llm_response_dir=llm_response_dir,
        output_dir=repo_root / "output" / "llm_suggestion_spot_check_gate_342m",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == REAL_RESPONSE_READY_DECISION
    assert summary["ready_for_342n"] is True
    assert summary["response_count"] == 2
    assert summary["valid_llm_response_count"] == 2
    assert summary["agreement_count"] == 2
