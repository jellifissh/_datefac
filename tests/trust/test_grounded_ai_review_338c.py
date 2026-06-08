from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.grounded_ai_review_338c import (  # noqa: E402
    GROUNDING_STILL_TOO_WEAK,
    READY_DECISION,
    SWITCH_TO_AI_REVIEW_MODEL,
    _build_recommendation,
    build_grounded_ai_review_338c,
    build_prompt_text,
    parse_model_json,
    validate_grounding_source,
    validate_quote_against_text,
)


class MockClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def adjudicate(self, prompt: str):
        self.calls += 1
        if not self.responses:
            raise RuntimeError("no mocked response")
        return {"raw_response": {"mocked": True}, "content": self.responses.pop(0)}


def _write_338b_workbook(path: Path) -> None:
    plan_df = pd.DataFrame(
        [
            {
                "adjudication_id": "row-1",
                "document": "demo.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": 2,
                "metric_before": "revenue",
                "metric_display_zh": "营业收入",
                "year_before": "2026E",
                "value_before": "123",
                "unit_before": "百万元",
                "source_page": 10,
                "status_before": "reviewed_preview",
                "evidence": "营业收入 | 100 | 123 | 150",
                "suspicious_reason": "year_alignment_unclear",
                "notes": "REMOVE_DUPLICATE_REVIEWED",
                "route_change_context": "reviewed_preview | rejected_or_excluded",
                "table_role_337d": "CORE_FINANCIAL_SUMMARY",
                "table_year_headers": "2025A | 2026E | 2027E",
                "matched_table_line": "营业收入 | 100 | 123 | 150",
                "nearby_previous_row": "指标 | 2025A | 2026E | 2027E",
                "nearby_next_row": "归母净利润 | 30 | 40 | 50",
                "model_decision_status": "VALID",
                "model_decision": "CONFIRM_REVIEWED",
                "suggested_metric": "revenue",
                "suggested_year": "2026E",
                "suggested_value": "123",
                "suggested_unit": "百万元",
                "table_role_guess": "CORE_FINANCIAL_SUMMARY",
                "confidence": 0.95,
                "risk_flags": "",
                "reason": "可确认",
                "evidence_quote": "营业收入 | 100 | 123 | 150",
                "evidence_quote_grounded": True,
                "deterministic_guard_result": "PASS",
                "recommended_final_action": "CONFIRM_REVIEWED",
                "model_name": "gpt-5.5",
                "prompt_hash": "p1",
                "cache_hit": False,
                "parse_method": "raw_json",
                "validation_errors": "",
            },
            {
                "adjudication_id": "row-2",
                "document": "demo.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": 3,
                "metric_before": "revenue",
                "metric_display_zh": "营业收入",
                "year_before": "2027E",
                "value_before": "150",
                "unit_before": "百万元",
                "source_page": 10,
                "status_before": "reviewed_preview",
                "evidence": "营业收入 | 100 | 123 | 150",
                "suspicious_reason": "year_alignment_unclear",
                "notes": "REMOVE_DUPLICATE_REVIEWED",
                "route_change_context": "reviewed_preview | rejected_or_excluded",
                "table_role_337d": "CORE_FINANCIAL_SUMMARY",
                "table_year_headers": "2025A | 2026E | 2027E",
                "matched_table_line": "营业收入 | 100 | 123 | 150",
                "nearby_previous_row": "指标 | 2025A | 2026E | 2027E",
                "nearby_next_row": "归母净利润 | 30 | 40 | 50",
                "model_decision_status": "VALID",
                "model_decision": "CONFIRM_REVIEWED",
                "suggested_metric": "revenue",
                "suggested_year": "2027E",
                "suggested_value": "150",
                "suggested_unit": "百万元",
                "table_role_guess": "CORE_FINANCIAL_SUMMARY",
                "confidence": 0.95,
                "risk_flags": "",
                "reason": "可确认",
                "evidence_quote": "指标 | 2025A | 2026E | 2027E 营业收入 | 100 | 123 | 150",
                "evidence_quote_grounded": True,
                "deterministic_guard_result": "PASS",
                "recommended_final_action": "CONFIRM_REVIEWED",
                "model_name": "gpt-5.5",
                "prompt_hash": "p2",
                "cache_hit": False,
                "parse_method": "raw_json",
                "validation_errors": "",
            },
        ]
    )
    context_df = pd.DataFrame(
        [
            {
                "adjudication_id": "row-1",
                "document": "demo.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": 2,
                "table_role_337d": "CORE_FINANCIAL_SUMMARY",
                "table_year_headers": "2025A | 2026E | 2027E",
                "matched_table_line": "营业收入 | 100 | 123 | 150",
                "nearby_previous_row": "指标 | 2025A | 2026E | 2027E",
                "nearby_next_row": "归母净利润 | 30 | 40 | 50",
                "source_page": 10,
                "suspicious_reason": "year_alignment_unclear",
                "deterministic_guard_result": "PASS",
                "route_change_context": "reviewed_preview | rejected_or_excluded",
            },
            {
                "adjudication_id": "row-2",
                "document": "demo.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": 3,
                "table_role_337d": "CORE_FINANCIAL_SUMMARY",
                "table_year_headers": "2025A | 2026E | 2027E",
                "matched_table_line": "营业收入 | 100 | 123 | 150",
                "nearby_previous_row": "指标 | 2025A | 2026E | 2027E",
                "nearby_next_row": "归母净利润 | 30 | 40 | 50",
                "source_page": 10,
                "suspicious_reason": "year_alignment_unclear",
                "deterministic_guard_result": "PASS",
                "route_change_context": "reviewed_preview | rejected_or_excluded",
            },
        ]
    )
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        plan_df.to_excel(writer, sheet_name="02_NEW_MODEL_ADJUDICATION_PLAN", index=False)
        context_df.to_excel(writer, sheet_name="08_PROMPT_CONTEXT_UPGRADE", index=False)


def test_quote_validation() -> None:
    assert validate_quote_against_text("营业收入 | 100 | 123 | 150", "营业收入 | 100 | 123 | 150")
    assert not validate_quote_against_text("指标 | 2025A", "营业收入 | 100 | 123 | 150")


def test_grounding_source_validation() -> None:
    assert validate_grounding_source("RAW_EVIDENCE", raw_quote_valid=True, context_quote_valid=False)
    assert validate_grounding_source("BOTH", raw_quote_valid=True, context_quote_valid=True)
    assert not validate_grounding_source("SUPPORTING_CONTEXT", raw_quote_valid=True, context_quote_valid=False)


def test_prompt_contains_split_quote_schema() -> None:
    prompt = build_prompt_text(
        {
            "adjudication_id": "row-1",
            "document": "demo.pdf",
            "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
            "source_row_no": 2,
            "metric_before": "revenue",
            "metric_display_zh": "营业收入",
            "year_before": "2026E",
            "value_before": "123",
            "unit_before": "百万元",
            "source_page": 10,
            "status_before": "reviewed_preview",
            "suspicious_reason": "year_alignment_unclear",
            "notes": "REMOVE_DUPLICATE_REVIEWED",
            "deterministic_guard_result": "PASS",
            "table_role_337d": "CORE_FINANCIAL_SUMMARY",
            "evidence": "营业收入 | 100 | 123 | 150",
            "table_year_headers": "2025A | 2026E | 2027E",
            "matched_table_line": "营业收入 | 100 | 123 | 150",
            "nearby_previous_row": "指标 | 2025A | 2026E | 2027E",
            "nearby_next_row": "归母净利润 | 30 | 40 | 50",
            "route_change_context": "reviewed_preview | rejected_or_excluded",
        }
    )
    assert "raw_evidence_quote" in prompt
    assert "supporting_context_quote" in prompt
    assert "grounding_source" in prompt


def test_parse_model_json_repairs_fenced_json() -> None:
    parsed, method = parse_model_json(
        """```json
        {"decision":"NEEDS_MORE_CONTEXT","suggested_metric":null,"suggested_year":null,"suggested_value":null,"suggested_unit":null,"table_role_guess":"UNKNOWN","risk_flags":[],"confidence":0.8,"reason":"证据不足","raw_evidence_quote":"营业收入","supporting_context_quote":null,"grounding_source":"RAW_EVIDENCE"}
        ```"""
    )
    assert parsed is not None
    assert parsed["decision"] == "NEEDS_MORE_CONTEXT"
    assert method == "fence_repair"


def test_build_grounded_review_with_mocked_rows(tmp_path: Path) -> None:
    ab_dir = tmp_path / "338b"
    reviewed_dir = tmp_path / "337d"
    output_dir = tmp_path / "338c"
    ab_dir.mkdir()
    reviewed_dir.mkdir()

    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    (ab_dir / "ai_review_model_ab_338b_summary.json").write_text(
        json.dumps(
            {
                "invalid_response_count_new": 3,
                "needs_more_context_count_new": 3,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_338b_workbook(ab_dir / "ai_review_model_ab_338b_plan.xlsx")
    (reviewed_dir / "real_test_mineru_client_export_337d.xlsx").write_bytes(b"placeholder")
    (reviewed_dir / "reviewed_strictness_year_alignment_337d_before_after.xlsx").write_bytes(b"placeholder")
    (reviewed_dir / "reviewed_strictness_year_alignment_337d_summary.json").write_text(
        json.dumps({"decision": "REVIEWED_STRICTNESS_YEAR_ALIGNMENT_337D_READY"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    client = MockClient(
        [
            '{"decision":"CONFIRM_REVIEWED","suggested_metric":"revenue","suggested_year":"2026E","suggested_value":"123","suggested_unit":"百万元","table_role_guess":"CORE_FINANCIAL_SUMMARY","risk_flags":[],"confidence":0.91,"reason":"原始证据足够","raw_evidence_quote":"营业收入 | 100 | 123 | 150","supporting_context_quote":"指标 | 2025A | 2026E | 2027E","grounding_source":"BOTH"}',
            '{"decision":"CONFIRM_REVIEWED","suggested_metric":"revenue","suggested_year":"2027E","suggested_value":"150","suggested_unit":"百万元","table_role_guess":"CORE_FINANCIAL_SUMMARY","risk_flags":[],"confidence":0.95,"reason":"仅靠表头可确认","raw_evidence_quote":"","supporting_context_quote":"指标 | 2025A | 2026E | 2027E","grounding_source":"SUPPORTING_CONTEXT"}',
        ]
    )

    artifacts = build_grounded_ai_review_338c(
        ab_338b_dir=ab_dir,
        reviewed_strictness_337d_dir=reviewed_dir,
        output_dir=output_dir,
        limit=2,
        dry_run_prompts_only=False,
        timeout_seconds=5,
        client=client,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
        env={
            "AI_REVIEW_API_KEY": "secret-ai-key",
            "AI_REVIEW_BASE_URL": "https://ai.example",
            "AI_MODEL": "ai-model-x",
        },
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["row_count"] == 2
    assert summary["invalid_response_count_338c"] == 1
    assert summary["confirm_reviewed_count_338c"] == 1
    assert summary["confirm_with_context_only_count"] == 1
    assert summary["confirm_rejected_by_grounding_count"] == 0
    assert summary["raw_quote_valid_count"] == 1
    assert summary["context_quote_valid_count"] == 2
    assert summary["AI_REVIEW_API_KEY"] == "SET"

    grounded_df = artifacts["workbook_sheets"]["02_GROUNDED_ADJUDICATION_PLAN"]
    assert grounded_df.loc[0, "recommended_final_action"] == "CONFIRM_REVIEWED"
    assert grounded_df.loc[1, "recommended_final_action"] == "NEEDS_MORE_CONTEXT"
    serialized = json.dumps(artifacts, ensure_ascii=False, default=str)
    assert "secret-ai-key" not in serialized


def test_recommendation_logic_variants() -> None:
    assert (
        _build_recommendation(
            {
                "row_count": 50,
                "invalid_response_count_338b": 3,
                "invalid_response_count_338c": 0,
                "needs_more_context_count_338b": 3,
                "needs_more_context_count_338c": 2,
                "raw_quote_valid_count": 45,
                "confirm_with_context_only_count": 0,
                "confirm_rejected_by_grounding_count": 1,
                "rule_model_conflict_count": 0,
            }
        )
        == SWITCH_TO_AI_REVIEW_MODEL
    )
    assert (
        _build_recommendation(
            {
                "row_count": 50,
                "invalid_response_count_338b": 3,
                "invalid_response_count_338c": 3,
                "needs_more_context_count_338b": 3,
                "needs_more_context_count_338c": 3,
                "raw_quote_valid_count": 20,
                "confirm_with_context_only_count": 2,
                "confirm_rejected_by_grounding_count": 6,
                "rule_model_conflict_count": 0,
            }
        )
        == GROUNDING_STILL_TOO_WEAK
    )
