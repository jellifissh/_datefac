from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.llm_suggestion_apply_simulation_342l import (  # noqa: E402
    NOT_READY_DECISION,
    READY_DECISION,
    build_llm_suggestion_apply_simulation_342l,
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


def _seed_342l_inputs(root: Path, *, ready_342k: bool = True) -> tuple[Path, Path]:
    llm_review_342k_dir = root / "output" / "llm_assisted_review_adjudication_342k"
    reviewed_preview_342j_dir = root / "output" / "table_first_reviewed_client_preview_pilot_342j"
    llm_review_342k_dir.mkdir(parents=True, exist_ok=True)
    reviewed_preview_342j_dir.mkdir(parents=True, exist_ok=True)

    summary_342k = {
        "decision": "LLM_ASSISTED_REVIEW_ADJUDICATION_342K_READY" if ready_342k else "LLM_ASSISTED_REVIEW_ADJUDICATION_342K_NOT_READY",
        "ready_for_342l": ready_342k,
        "pending_review_count": 4,
        "auto_confirm_candidate_count": 2,
        "human_required_count": 2,
        "conflict_count": 1,
        "unit_year_risk_count": 2,
        "duplicate_risk_count": 1,
        "growth_row_risk_count": 1,
        "source_trace_risk_count": 1,
        "metric_mapping_risk_count": 1,
        "qa_fail_count": 0 if ready_342k else 1,
        "client_ready": False,
        "production_ready": False,
    }
    _write_json(llm_review_342k_dir / "llm_assisted_review_adjudication_342k_summary.json", summary_342k)
    _write_json(llm_review_342k_dir / "llm_assisted_review_adjudication_342k_qa.json", {"qa_fail_count": 0 if ready_342k else 1, "checks": []})
    _write_json(llm_review_342k_dir / "llm_assisted_review_adjudication_342k_no_write_back_proof.json", {"upstream_workbooks_unchanged": True})
    (llm_review_342k_dir / "llm_assisted_review_adjudication_342k_report.md").write_text("342K report", encoding="utf-8")

    candidate_pool_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_1",
                "review_priority": "MEDIUM",
                "review_bucket": "UNIT_YEAR_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc1.pdf",
                "table_id": "t1",
                "table_type": "INCOME_STATEMENT",
                "source_page": 1,
                "bbox": "[1,2,3,4]",
                "image_path": "img1.jpg",
                "metric_raw": "每股收益",
                "metric_standardized": "EPS",
                "year_raw": "2025",
                "year_standardized": "2025A",
                "value_raw": "1.45",
                "value_numeric": 1.45,
                "unit_raw": "",
                "normalized_unit": "",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_UNIT_MISSING",
                "risk_flags": "UNIT_MISSING",
                "confidence_signal": "MEDIUM",
                "candidate_reason": "unit_inferable_from_value",
                "llm_route": "LLM_UNIT_YEAR_CHECK",
                "source_html_snippet": "<table>eps row</table>",
            },
            {
                "review_item_id": "item_2",
                "review_priority": "LOW",
                "review_bucket": "TRUSTED_AUDIT_SAMPLE",
                "corpus_pdf_id": "pdf_2",
                "file_name": "doc2.pdf",
                "table_id": "t2",
                "table_type": "CORE_FORECAST_SUMMARY",
                "source_page": 2,
                "bbox": "[2,3,4,5]",
                "image_path": "img2.jpg",
                "metric_raw": "ROE",
                "metric_standardized": "ROE",
                "year_raw": "2026E",
                "year_standardized": "2026E",
                "value_raw": "12%",
                "value_numeric": 12.0,
                "unit_raw": "%",
                "normalized_unit": "%",
                "extraction_status": "TRUSTED_CELL",
                "review_reason": "TRUSTED_AUDIT_SPOT_CHECK",
                "risk_flags": "",
                "confidence_signal": "HIGH",
                "candidate_reason": "trusted_audit_candidate",
                "llm_route": "LLM_SOURCE_TRACE_CHECK",
                "source_html_snippet": "<table>roe row</table>",
            },
            {
                "review_item_id": "item_3",
                "review_priority": "HIGH",
                "review_bucket": "DUPLICATE_REVIEW",
                "corpus_pdf_id": "pdf_1",
                "file_name": "doc1.pdf",
                "table_id": "t3",
                "table_type": "INCOME_STATEMENT",
                "source_page": 3,
                "bbox": "[3,4,5,6]",
                "image_path": "img3.jpg",
                "metric_raw": "收入增长",
                "metric_standardized": "revenue",
                "year_raw": "2025",
                "year_standardized": "2025A",
                "value_raw": "10%",
                "value_numeric": 10.0,
                "unit_raw": "",
                "normalized_unit": "",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_DUPLICATE",
                "risk_flags": "UNIT_MISSING|DUPLICATE_DROPPED",
                "confidence_signal": "LOW",
                "candidate_reason": "duplicate_review_candidate",
                "llm_route": "HUMAN_ONLY_HIGH_RISK",
                "source_html_snippet": "<table>dup row</table>",
            },
            {
                "review_item_id": "item_4",
                "review_priority": "MEDIUM",
                "review_bucket": "UNIT_YEAR_REVIEW",
                "corpus_pdf_id": "pdf_3",
                "file_name": "doc3.pdf",
                "table_id": "t4",
                "table_type": "BALANCE_SHEET",
                "source_page": 4,
                "bbox": "[4,5,6,7]",
                "image_path": "",
                "metric_raw": "未知指标",
                "metric_standardized": "",
                "year_raw": "2026E",
                "year_standardized": "",
                "value_raw": "0",
                "value_numeric": 0.0,
                "unit_raw": "",
                "normalized_unit": "",
                "extraction_status": "REVIEW_REQUIRED",
                "review_reason": "REVIEW_REQUIRED_UNIT_AMBIGUITY",
                "risk_flags": "",
                "confidence_signal": "MEDIUM",
                "candidate_reason": "metric_mapping_candidate",
                "llm_route": "HUMAN_ONLY_HIGH_RISK",
                "source_html_snippet": "",
            },
        ]
    )
    rule_baseline_df = candidate_pool_df.copy()
    rule_baseline_df["rule_suggested_decision"] = ["CORRECT_AND_CONFIRM", "CONFIRM_CELL", "KEEP_REVIEW_REQUIRED", "KEEP_REVIEW_REQUIRED"]
    rule_baseline_df["rule_suggested_metric_standardized"] = ["EPS", "ROE", "revenue_yoy", ""]
    rule_baseline_df["rule_suggested_year_standardized"] = ["2025A", "2026E", "2025A", ""]
    rule_baseline_df["rule_suggested_value_numeric"] = [1.45, 12.0, 10.0, 0.0]
    rule_baseline_df["rule_suggested_normalized_unit"] = ["元", "%", "%", ""]
    rule_baseline_df["rule_confidence"] = [0.97, 0.99, 0.68, 0.40]
    rule_baseline_df["rule_reason"] = ["unit_year_rule", "trusted_source_rule", "duplicate_conflict_requires_check", "source_html_missing"]
    rule_baseline_df["rule_human_required"] = [False, False, True, True]

    dry_run_df = pd.DataFrame(
        [
            {"review_item_id": "item_1", "dry_run_suggested_decision": "CORRECT_AND_CONFIRM", "dry_run_suggested_metric_standardized": "EPS", "dry_run_suggested_year_standardized": "2025A", "dry_run_suggested_value_numeric": 1.45, "dry_run_suggested_normalized_unit": "元", "dry_run_confidence": 0.97, "dry_run_reason": "DRY_RUN_BASELINE_ONLY | unit_year_rule", "human_required": False, "can_auto_confirm_candidate": True},
            {"review_item_id": "item_2", "dry_run_suggested_decision": "CONFIRM_CELL", "dry_run_suggested_metric_standardized": "ROE", "dry_run_suggested_year_standardized": "2026E", "dry_run_suggested_value_numeric": 12.0, "dry_run_suggested_normalized_unit": "%", "dry_run_confidence": 0.99, "dry_run_reason": "DRY_RUN_BASELINE_ONLY | trusted_source_rule", "human_required": False, "can_auto_confirm_candidate": True},
            {"review_item_id": "item_3", "dry_run_suggested_decision": "KEEP_REVIEW_REQUIRED", "dry_run_suggested_metric_standardized": "revenue_yoy", "dry_run_suggested_year_standardized": "2025A", "dry_run_suggested_value_numeric": 10.0, "dry_run_suggested_normalized_unit": "%", "dry_run_confidence": 0.68, "dry_run_reason": "DRY_RUN_BASELINE_ONLY | duplicate_conflict_requires_check", "human_required": True, "can_auto_confirm_candidate": False},
            {"review_item_id": "item_4", "dry_run_suggested_decision": "KEEP_REVIEW_REQUIRED", "dry_run_suggested_metric_standardized": "", "dry_run_suggested_year_standardized": "", "dry_run_suggested_value_numeric": 0.0, "dry_run_suggested_normalized_unit": "", "dry_run_confidence": 0.40, "dry_run_reason": "DRY_RUN_BASELINE_ONLY | source_html_missing", "human_required": True, "can_auto_confirm_candidate": False},
        ]
    )
    human_required_df = rule_baseline_df[rule_baseline_df["rule_human_required"]].copy()
    auto_confirm_df = dry_run_df[dry_run_df["can_auto_confirm_candidate"]].copy()
    conflicts_df = pd.DataFrame(
        [
            {
                "review_item_id": "item_3",
                "llm_route": "HUMAN_ONLY_HIGH_RISK",
                "conflict_types": "duplicate_conflict | unit_mismatch",
                "conflict_count": 2,
                "rule_suggested_decision": "KEEP_REVIEW_REQUIRED",
                "rule_reason": "duplicate_conflict_requires_check",
                "human_required": True,
            },
            {
                "review_item_id": "item_4",
                "llm_route": "HUMAN_ONLY_HIGH_RISK",
                "conflict_types": "source_trace_missing | suspicious_zero_value | not_core_vs_reviewable_conflict",
                "conflict_count": 3,
                "rule_suggested_decision": "KEEP_REVIEW_REQUIRED",
                "rule_reason": "source_html_missing",
                "human_required": True,
            },
        ]
    )
    risk_buckets_df = pd.DataFrame(
        [
            {"risk_bucket": "unit_year_risk", "row_count": 2, "sample_review_item_ids": "item_1 | item_4"},
            {"risk_bucket": "duplicate_risk", "row_count": 1, "sample_review_item_ids": "item_3"},
            {"risk_bucket": "growth_row_risk", "row_count": 1, "sample_review_item_ids": "item_3"},
            {"risk_bucket": "source_trace_risk", "row_count": 1, "sample_review_item_ids": "item_4"},
            {"risk_bucket": "metric_mapping_risk", "row_count": 1, "sample_review_item_ids": "item_4"},
            {"risk_bucket": "high_priority_risk", "row_count": 1, "sample_review_item_ids": "item_3"},
        ]
    )
    review_template_draft_df = pd.DataFrame(
        [
            {"review_item_id": row["review_item_id"], "rule_suggested_decision": row["rule_suggested_decision"], "dry_run_suggested_decision": dry_run_df[dry_run_df["review_item_id"].eq(row["review_item_id"])]["dry_run_suggested_decision"].iloc[0], "suggested_metric_standardized": row["rule_suggested_metric_standardized"], "suggested_year_standardized": row["rule_suggested_year_standardized"], "suggested_value_numeric": row["rule_suggested_value_numeric"], "suggested_normalized_unit": row["rule_suggested_normalized_unit"], "suggested_confidence": row["rule_confidence"], "human_required": row["rule_human_required"], "reviewer_decision": "", "reviewer_metric_standardized": "", "reviewer_year_standardized": "", "reviewer_value_numeric": "", "reviewer_normalized_unit": "", "reviewer_note": "", "reviewer_id": "", "reviewed_at": ""}
            for row in rule_baseline_df.to_dict(orient="records")
        ]
    )
    _write_excel(
        llm_review_342k_dir / "llm_assisted_review_adjudication_342k.xlsx",
        {
            "03_LLM_CANDIDATE_POOL": candidate_pool_df,
            "04_RULE_BASELINE": rule_baseline_df,
            "05_PROMPT_PACKAGE": pd.DataFrame([{"request_id": "342k::item_1"}, {"request_id": "342k::item_2"}]),
            "06_EXPECTED_SCHEMA": pd.DataFrame([{"field_name": "review_item_id"}]),
            "07_DRY_RUN_SUGGESTIONS": dry_run_df,
            "08_HUMAN_REQUIRED": human_required_df,
            "09_AUTO_CONFIRM_CANDIDATES": auto_confirm_df,
            "10_CONFLICTS": conflicts_df,
            "11_RISK_BUCKETS": risk_buckets_df,
            "12_REVIEW_TEMPLATE_DRAFT": review_template_draft_df,
            "13_342L_READINESS": pd.DataFrame([{"ready_for_342l": ready_342k, "decision": summary_342k["decision"]}]),
            "14_NO_WRITE_BACK": pd.DataFrame([{"path": "input.xlsx", "unchanged": True}]),
        },
    )
    _write_jsonl(
        llm_review_342k_dir / "llm_assisted_review_adjudication_342k_prompt_pack.jsonl",
        [
            {"request_id": "342k::item_1", "review_item_id": "item_1", "prompt_version": "342k.v1", "system_prompt": "prompt", "user_prompt": "user", "evidence_json": "{}", "expected_schema_name": "schema", "max_tokens_hint": 400, "temperature_hint": 0.0},
            {"request_id": "342k::item_2", "review_item_id": "item_2", "prompt_version": "342k.v1", "system_prompt": "prompt", "user_prompt": "user", "evidence_json": "{}", "expected_schema_name": "schema", "max_tokens_hint": 400, "temperature_hint": 0.0},
        ],
    )
    _write_jsonl(
        llm_review_342k_dir / "llm_assisted_review_adjudication_342k_request_pack.jsonl",
        [
            {"request_id": "342k::item_1", "review_item_id": "item_1", "prompt_version": "342k.v1", "expected_schema_name": "schema", "llm_route": "LLM_UNIT_YEAR_CHECK", "evidence_json": "{}"},
            {"request_id": "342k::item_2", "review_item_id": "item_2", "prompt_version": "342k.v1", "expected_schema_name": "schema", "llm_route": "LLM_SOURCE_TRACE_CHECK", "evidence_json": "{}"},
        ],
    )

    summary_342j = {
        "decision": "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY",
        "ready_for_342k": True,
        "reviewed_preview_row_count": 2,
        "confirmed_preview_row_count": 1,
        "corrected_preview_row_count": 1,
        "pending_review_count": 4,
        "qa_fail_count": 0,
        "client_ready": False,
        "production_ready": False,
    }
    _write_json(reviewed_preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j_summary.json", summary_342j)
    _write_json(reviewed_preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j_qa.json", {"qa_fail_count": 0, "checks": []})
    _write_json(reviewed_preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j_no_write_back_proof.json", {"upstream_workbooks_unchanged": True})
    (reviewed_preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j_report.md").write_text("342J report", encoding="utf-8")
    _write_excel(
        reviewed_preview_342j_dir / "table_first_reviewed_client_preview_pilot_342j.xlsx",
        {
            "03_REVIEWED_PREVIEW": pd.DataFrame([{"review_item_id": "done_1"}, {"review_item_id": "done_2"}]),
            "04_CONFIRMED_PREVIEW": pd.DataFrame([{"review_item_id": "done_1"}]),
            "05_CORRECTED_PREVIEW": pd.DataFrame([{"review_item_id": "done_2"}]),
            "09_REMAINING_REVIEW": candidate_pool_df,
            "12_342K_READINESS": pd.DataFrame([{"ready_for_342k": True, "decision": summary_342j["decision"]}]),
        },
    )
    return llm_review_342k_dir, reviewed_preview_342j_dir


def test_build_342l_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    llm_review_342k_dir, reviewed_preview_342j_dir = _seed_342l_inputs(repo_root)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_llm_suggestion_apply_simulation_342l(
        llm_review_342k_dir=llm_review_342k_dir,
        reviewed_preview_342j_dir=reviewed_preview_342j_dir,
        output_dir=repo_root / "output" / "llm_suggestion_apply_simulation_342l",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["auto_confirm_candidate_count"] == 2
    assert summary["spot_check_sample_count"] == 2
    assert summary["human_required_count"] == 2
    assert summary["conflict_count"] == 2
    assert summary["prefill_review_draft_count"] == 4
    assert summary["prompt_pack_count"] == 2
    assert summary["request_pack_count"] == 2
    assert summary["jsonl_parse_error_count"] == 0
    assert summary["theoretical_review_reduction_count"] == 2
    assert summary["risk_adjusted_reduction_count"] == 0
    assert summary["required_human_review_after_strategy"] == 4
    assert summary["ready_for_342m"] is True

    auto_df = artifacts["workbook_sheets"]["03_AUTO_CANDIDATES"]
    assert auto_df["simulation_status"].astype(str).eq("AUTO_CONFIRM_CANDIDATE").all()
    assert auto_df["not_final_confirmation"].astype(bool).all()

    spot_df = artifacts["workbook_sheets"]["04_SPOT_CHECK_SAMPLE"]
    assert spot_df["reviewer_decision"].astype(str).eq("").all()
    assert spot_df["reviewed_at"].astype(str).eq("").all()

    prefill_df = artifacts["workbook_sheets"]["05_PREFILL_REVIEW_DRAFT"]
    assert prefill_df["reviewer_decision"].astype(str).eq("").all()
    assert prefill_df["reviewer_metric_standardized"].astype(str).eq("").all()


def test_build_342l_not_ready_when_342k_not_ready(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    llm_review_342k_dir, reviewed_preview_342j_dir = _seed_342l_inputs(repo_root, ready_342k=False)

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    artifacts = build_llm_suggestion_apply_simulation_342l(
        llm_review_342k_dir=llm_review_342k_dir,
        reviewed_preview_342j_dir=reviewed_preview_342j_dir,
        output_dir=repo_root / "output" / "llm_suggestion_apply_simulation_342l",
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    assert artifacts["summary"]["decision"] == NOT_READY_DECISION
    assert artifacts["summary"]["ready_for_342m"] is False
    assert artifacts["summary"]["auto_confirm_candidate_count"] == 0
