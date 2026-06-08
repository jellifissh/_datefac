from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.ai_review_adoption_simulation_338d import (  # noqa: E402
    ADOPTION_ACCEPT_CONFIRM,
    ADOPTION_ACCEPT_DOWNGRADE,
    ADOPTION_ACCEPT_REJECT,
    ADOPTION_HOLD,
    ADOPTION_INVALID,
    ADOPTION_REJECT_BY_RULE,
    READY_DECISION,
    build_ai_review_adoption_simulation_338d,
    decide_adoption,
)


def _write_338c_workbook(path: Path) -> None:
    template_rows = [
            {
                "adjudication_id": "row-1",
                "document": "demo.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": 2,
                "metric_before": "revenue",
                "year_before": "2026E",
                "value_before": "123",
                "unit_before": "百万元",
                "model_decision": "CONFIRM_REVIEWED",
                "model_decision_status": "VALID",
                "recommended_final_action": "CONFIRM_REVIEWED",
                "confidence": 0.91,
                "grounding_source": "BOTH",
                "raw_quote_valid": True,
                "context_quote_valid": True,
                "deterministic_guard_result": "PASS",
                "table_role_guess": "CORE_FINANCIAL_SUMMARY",
                "table_role_337d": "CORE_FINANCIAL_SUMMARY",
                "table_year_headers": "2025A | 2026E | 2027E",
                "matched_table_line": "营业收入 | 100 | 123 | 150",
                "nearby_previous_row": "指标 | 2025A | 2026E | 2027E",
                "nearby_next_row": "归母净利润 | 30 | 40 | 50",
                "risk_flags": "",
                "reason": "可确认",
                "suspicious_reason": "",
                "notes": "",
                "model_name": "gpt-5.5",
            },
            {
                "adjudication_id": "row-2",
                "document": "demo.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": 3,
                "metric_before": "revenue",
                "year_before": "2027E",
                "value_before": "150",
                "unit_before": "百万元",
                "model_decision": "DOWNGRADE_TO_NEEDS_REVIEW",
                "model_decision_status": "VALID",
                "recommended_final_action": "DOWNGRADE_TO_NEEDS_REVIEW",
                "confidence": 0.80,
                "grounding_source": "BOTH",
                "raw_quote_valid": True,
                "context_quote_valid": True,
                "deterministic_guard_result": "PASS",
                "table_role_guess": "CORE_FINANCIAL_SUMMARY",
                "table_role_337d": "CORE_FINANCIAL_SUMMARY",
                "table_year_headers": "2025A | 2026E | 2027E",
                "matched_table_line": "营业收入 | 100 | 123 | 150",
                "nearby_previous_row": "",
                "nearby_next_row": "",
                "risk_flags": "year_alignment_unclear",
                "reason": "建议回退人工复核",
                "suspicious_reason": "year_alignment_unclear",
                "notes": "",
                "model_name": "gpt-5.5",
            },
            {
                "adjudication_id": "row-3",
                "document": "demo.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": 4,
                "metric_before": "revenue",
                "year_before": "2028E",
                "value_before": "180",
                "unit_before": "百万元",
                "model_decision": "REJECT",
                "model_decision_status": "VALID",
                "recommended_final_action": "REJECT",
                "confidence": 0.88,
                "grounding_source": "BOTH",
                "raw_quote_valid": True,
                "context_quote_valid": True,
                "deterministic_guard_result": "PASS",
                "table_role_guess": "CORE_FINANCIAL_SUMMARY",
                "table_role_337d": "CORE_FINANCIAL_SUMMARY",
                "table_year_headers": "2025A | 2026E | 2027E",
                "matched_table_line": "营业收入 | 100 | 123 | 150",
                "nearby_previous_row": "",
                "nearby_next_row": "",
                "risk_flags": "duplicate_reviewed_row",
                "reason": "duplicate_reviewed_row remove_duplicate_reviewed",
                "suspicious_reason": "duplicate_reviewed_row",
                "notes": "REMOVE_DUPLICATE_REVIEWED",
                "model_name": "gpt-5.5",
            },
            {
                "adjudication_id": "row-4",
                "document": "demo.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": 5,
                "metric_before": "net_profit",
                "year_before": "2028E",
                "value_before": "2442",
                "unit_before": "",
                "model_decision": "CONFIRM_REVIEWED",
                "model_decision_status": "INVALID_RESPONSE",
                "recommended_final_action": "NEEDS_MORE_CONTEXT",
                "confidence": 0.78,
                "grounding_source": "INSUFFICIENT",
                "raw_quote_valid": True,
                "context_quote_valid": True,
                "deterministic_guard_result": "HARD_REJECT_MISSING_MONEY_UNIT",
                "table_role_guess": "PROFIT_FORECAST_VALUATION",
                "table_role_337d": "PROFIT_FORECAST_VALUATION",
                "table_year_headers": "2024A | 2025A | 2026E | 2027E | 2028E",
                "matched_table_line": "净利润 | 1514 | 1370 | 1816 | 2129 | 2442",
                "nearby_previous_row": "",
                "nearby_next_row": "",
                "risk_flags": "missing_unit_for_amount_metric",
                "reason": "单位缺失",
                "suspicious_reason": "missing_unit_for_amount_metric",
                "notes": "",
                "model_name": "gpt-5.5",
            },
            {
                "adjudication_id": "row-5",
                "document": "demo.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": 6,
                "metric_before": "net_profit_yoy",
                "year_before": "2028E",
                "value_before": "30.20%",
                "unit_before": "%",
                "model_decision": "NEEDS_MORE_CONTEXT",
                "model_decision_status": "VALID",
                "recommended_final_action": "NEEDS_MORE_CONTEXT",
                "confidence": 0.78,
                "grounding_source": "BOTH",
                "raw_quote_valid": True,
                "context_quote_valid": True,
                "deterministic_guard_result": "PASS",
                "table_role_guess": "FINANCIAL_STATEMENT_DETAIL",
                "table_role_337d": "FINANCIAL_STATEMENT_DETAIL",
                "table_year_headers": "2025A | 2026E | 2027E | 2028E",
                "matched_table_line": "归属于母公司净利润 | 4.29% | 174.10% | 45.36% | 30.20%",
                "nearby_previous_row": "",
                "nearby_next_row": "",
                "risk_flags": "",
                "reason": "同比口径仍需人工复核",
                "suspicious_reason": "",
                "notes": "",
                "model_name": "gpt-5.5",
            },
        ]
    grounded_rows = []
    for batch in range(10):
        for index, row in enumerate(template_rows, start=1):
            copied = dict(row)
            copied["adjudication_id"] = f"row-{batch + 1}-{index}"
            copied["source_row_no"] = batch * 10 + index
            grounded_rows.append(copied)
    grounded_df = pd.DataFrame(grounded_rows)
    notes_df = pd.DataFrame([{"schema_note": "x"}])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        grounded_df.to_excel(writer, sheet_name="02_GROUNDED_ADJUDICATION_PLAN", index=False)
        notes_df.to_excel(writer, sheet_name="09_PROMPT_AND_SCHEMA_NOTES", index=False)


def test_decide_adoption_confirm_accept() -> None:
    decision = decide_adoption(
        {
            "metric_before": "revenue",
            "year_before": "2026E",
            "value_before": "123",
            "unit_before": "百万元",
            "model_decision": "CONFIRM_REVIEWED",
            "model_decision_status": "VALID",
            "confidence": 0.91,
            "grounding_source": "BOTH",
            "raw_quote_valid": True,
            "context_quote_valid": True,
            "deterministic_guard_result": "PASS",
            "table_role_guess": "CORE_FINANCIAL_SUMMARY",
            "table_role_337d": "CORE_FINANCIAL_SUMMARY",
            "table_year_headers": "2025A | 2026E | 2027E",
            "matched_table_line": "营业收入 | 100 | 123 | 150",
        }
    )
    assert decision["adoption_action"] == ADOPTION_ACCEPT_CONFIRM


def test_decide_adoption_reject_by_rule() -> None:
    decision = decide_adoption(
        {
            "metric_before": "net_profit",
            "year_before": "2028E",
            "value_before": "2442",
            "unit_before": "",
            "model_decision": "CONFIRM_REVIEWED",
            "model_decision_status": "VALID",
            "confidence": 0.95,
            "grounding_source": "BOTH",
            "raw_quote_valid": True,
            "context_quote_valid": True,
            "deterministic_guard_result": "HARD_REJECT_MISSING_MONEY_UNIT",
            "table_role_guess": "PROFIT_FORECAST_VALUATION",
            "table_role_337d": "PROFIT_FORECAST_VALUATION",
            "table_year_headers": "2024A | 2025A | 2026E | 2027E | 2028E",
            "matched_table_line": "净利润 | 1514 | 1370 | 1816 | 2129 | 2442",
        }
    )
    assert decision["adoption_action"] == ADOPTION_REJECT_BY_RULE


def test_decide_adoption_invalid_response() -> None:
    decision = decide_adoption(
        {
            "model_decision": "CONFIRM_REVIEWED",
            "model_decision_status": "INVALID_RESPONSE",
        }
    )
    assert decision["adoption_action"] == ADOPTION_INVALID


def test_decide_adoption_needs_more_context_hold() -> None:
    decision = decide_adoption(
        {
            "model_decision": "NEEDS_MORE_CONTEXT",
            "model_decision_status": "VALID",
            "deterministic_guard_result": "PASS",
        }
    )
    assert decision["adoption_action"] == ADOPTION_HOLD


def test_build_adoption_simulation(tmp_path: Path) -> None:
    grounded_dir = tmp_path / "338c"
    reviewed_dir = tmp_path / "337d"
    output_dir = tmp_path / "338d"
    grounded_dir.mkdir()
    reviewed_dir.mkdir()

    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    (grounded_dir / "grounded_ai_review_338c_summary.json").write_text(
        json.dumps({"confirm_reviewed_count_338c": 10}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_338c_workbook(grounded_dir / "grounded_ai_review_338c_plan.xlsx")
    (reviewed_dir / "real_test_mineru_client_export_337d.xlsx").write_bytes(b"placeholder")

    artifacts = build_ai_review_adoption_simulation_338d(
        grounded_ai_review_338c_dir=grounded_dir,
        reviewed_strictness_337d_dir=reviewed_dir,
        output_dir=output_dir,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["input_338c_row_count"] == 50
    assert summary["accept_model_confirm_count"] == 10
    assert summary["accept_model_downgrade_count"] == 10
    assert summary["accept_model_reject_count"] == 10
    assert summary["hold_for_human_review_count"] == 10
    assert summary["reject_by_deterministic_rule_count"] == 0
    assert summary["invalid_model_response_count"] == 10
    assert summary["deterministic_rule_override_count"] == 0

    adoption_df = artifacts["workbook_sheets"]["02_ADOPTION_PLAN"]
    assert adoption_df["adoption_action"].tolist()[:5] == [
        ADOPTION_ACCEPT_CONFIRM,
        ADOPTION_ACCEPT_DOWNGRADE,
        ADOPTION_ACCEPT_REJECT,
        ADOPTION_INVALID,
        ADOPTION_HOLD,
    ]
