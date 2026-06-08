from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.ai_review_model_ab_338b import (  # noqa: E402
    KEEP_DEEPSEEK_FLASH,
    NEED_MORE_PRO_MODEL_TEST,
    READY_DECISION,
    SWITCH_TO_AI_REVIEW_MODEL,
    _build_recommendation,
    build_ai_review_model_ab_338b,
    build_prompt_text,
    parse_model_json,
    resolve_runtime_config,
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


def _write_338a_workbook(path: Path) -> None:
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
                "model_decision_status": "VALID",
                "model_decision": "NEEDS_MORE_CONTEXT",
                "suggested_metric": "",
                "suggested_year": "",
                "suggested_value": "",
                "suggested_unit": "",
                "table_role_guess": "CORE_FINANCIAL_SUMMARY",
                "confidence": 0.30,
                "risk_flags": "missing_year_headers",
                "reason": "年份映射不明确",
                "evidence_quote": "营业收入 | 100 | 123 | 150",
                "deterministic_guard_result": "PASS",
                "recommended_final_action": "NEEDS_MORE_CONTEXT",
                "model_name": "deepseek-v4-flash",
                "prompt_hash": "p1",
                "cache_hit": False,
                "parse_method": "raw_json",
                "validation_errors": "",
            },
            {
                "adjudication_id": "row-2",
                "document": "demo.pdf",
                "source_sheet": "02_NEEDS_REVIEW",
                "source_row_no": 7,
                "metric_before": "revenue",
                "metric_display_zh": "营业收入",
                "year_before": "2027E",
                "value_before": "200",
                "unit_before": "百万元",
                "source_page": 11,
                "status_before": "needs_review",
                "evidence": "营业收入 | 180 | 200 | 240",
                "suspicious_reason": "",
                "notes": "manual_review",
                "route_change_context": "",
                "model_decision_status": "VALID",
                "model_decision": "CONFIRM_REVIEWED",
                "suggested_metric": "revenue",
                "suggested_year": "2027E",
                "suggested_value": "200",
                "suggested_unit": "百万元",
                "table_role_guess": "CORE_FINANCIAL_SUMMARY",
                "confidence": 0.92,
                "risk_flags": "",
                "reason": "证据匹配",
                "evidence_quote": "营业收入 | 180 | 200 | 240",
                "deterministic_guard_result": "PASS",
                "recommended_final_action": "CONFIRM_REVIEWED",
                "model_name": "deepseek-v4-flash",
                "prompt_hash": "p2",
                "cache_hit": False,
                "parse_method": "raw_json",
                "validation_errors": "",
            },
        ]
    )
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        plan_df.to_excel(writer, sheet_name="02_MODEL_ADJUDICATION_PLAN", index=False)
        pd.DataFrame([{"prompt_text": "x"}]).to_excel(writer, sheet_name="03_PROMPT_PREVIEW", index=False)


def _write_337d_workbook(path: Path) -> None:
    suspicious_df = pd.DataFrame(
        [
            {
                "candidate_id": "c1",
                "document": "demo.pdf",
                "metric": "revenue",
                "year": "2026E",
                "value": "123",
                "unit": "百万元",
                "source_page": 10,
                "evidence": "营业收入 | 100 | 123 | 150",
                "suspicious_reason": "year_alignment_unclear",
                "337d_action": "REMOVE_DUPLICATE_REVIEWED",
            }
        ]
    )
    needs_review_df = pd.DataFrame(
        [
            {
                "row_no": 7,
                "document": "demo.pdf",
                "metric": "revenue",
                "metric_display_zh": "营业收入",
                "year": "2027E",
                "value": "200",
                "unit": "百万元",
                "source_page": 11,
                "status": "needs_review",
                "source_evidence_excerpt": "营业收入 | 180 | 200 | 240",
                "notes": "manual_review",
            }
        ]
    )
    table_summary_df = pd.DataFrame(
        [
            {
                "document": "demo.pdf",
                "page_no": 10,
                "table_index": 1,
                "table_role_337c": "CORE_FINANCIAL_SUMMARY",
                "table_role_repair_reason": "core_financial_summary_rescue",
                "candidate_score": 22,
                "table_preview": "指标 | 2025A | 2026E | 2027E\n营业收入 | 100 | 123 | 150\n归母净利润 | 30 | 40 | 50",
                "reviewed_after_337d_count": 1,
            },
            {
                "document": "demo.pdf",
                "page_no": 11,
                "table_index": 2,
                "table_role_337c": "CORE_FINANCIAL_SUMMARY",
                "table_role_repair_reason": "core_financial_summary_rescue",
                "candidate_score": 20,
                "table_preview": "指标 | 2026E | 2027E | 2028E\n营业收入 | 180 | 200 | 240\n毛利率 | 12 | 13 | 14",
                "reviewed_after_337d_count": 1,
            },
        ]
    )
    route_df = pd.DataFrame(
        [
            {
                "candidate_id": "c1",
                "document": "demo.pdf",
                "metric_before_337d": "revenue",
                "metric_after_337d": "revenue",
                "year_before_337d": "2026E",
                "year_after_337d": "2026E",
                "unit_before_337d": "百万元",
                "unit_after_337d": "百万元",
                "status_before_337d": "reviewed_preview",
                "status_after_337d": "rejected_or_excluded",
                "route_reason_before_337d": "core_financial_context_repaired",
                "route_reason_after_337d": "duplicate_reviewed_row",
                "duplicate_of": "dup",
                "337d_action": "REMOVE_DUPLICATE_REVIEWED",
                "suspicious_reason": "year_alignment_unclear",
                "source_evidence_excerpt": "营业收入 | 100 | 123 | 150",
            }
        ]
    )
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "x", "message": "y"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="01_REVIEWED_CORE_METRICS", index=False)
        needs_review_df.to_excel(writer, sheet_name="02_NEEDS_REVIEW", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="03_REJECTED_OR_EXCLUDED", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="04_SOURCE_TRACE", index=False)
        pd.DataFrame([{"document": "demo.pdf"}]).to_excel(writer, sheet_name="05_DOCUMENT_SUMMARY", index=False)
        table_summary_df.to_excel(writer, sheet_name="06_TABLE_CLASSIFICATION_SUMMARY", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="07_CONTEXT_REPAIR_SUMMARY", index=False)
        suspicious_df.to_excel(writer, sheet_name="08_SUSPICIOUS_REVIEWED_AUDIT", index=False)
        route_df.to_excel(writer, sheet_name="09_ROUTE_CHANGE_TRACE", index=False)


def test_env_preference_ai_review_over_deepseek() -> None:
    config, statuses = resolve_runtime_config(
        env={
            "AI_REVIEW_API_KEY": "ai-key",
            "AI_REVIEW_BASE_URL": "https://ai.example",
            "AI_MODEL": "ai-model",
            "DEEPSEEK_API_KEY": "deepseek-key",
            "DEEPSEEK_BASE_URL": "https://deepseek.example",
            "DEEPSEEK_MODEL": "deepseek-model",
        }
    )
    assert config is not None
    assert config.env_source == "AI_REVIEW"
    assert config.model == "ai-model"
    assert statuses["AI_REVIEW_API_KEY"] == "SET"


def test_env_fallback_to_deepseek() -> None:
    config, _ = resolve_runtime_config(
        env={
            "DEEPSEEK_API_KEY": "deepseek-key",
            "DEEPSEEK_BASE_URL": "https://deepseek.example",
            "DEEPSEEK_MODEL": "deepseek-model",
        }
    )
    assert config is not None
    assert config.env_source == "DEEPSEEK_FALLBACK"
    assert config.model == "deepseek-model"


def test_prompt_contains_year_header_context_fields() -> None:
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
            "route_change_context": "reviewed_preview | rejected_or_excluded",
            "deterministic_guard_result": "PASS",
            "table_role_337d": "CORE_FINANCIAL_SUMMARY",
            "table_year_headers": ["2025A", "2026E", "2027E"],
            "matched_table_line": "营业收入 | 100 | 123 | 150",
            "previous_row": "指标 | 2025A | 2026E | 2027E",
            "next_row": "归母净利润 | 30 | 40 | 50",
            "table_preview_excerpt": "指标 | 2025A | 2026E | 2027E",
            "evidence": "营业收入 | 100 | 123 | 150",
            "source_record": {"candidate_id": "c1"},
        }
    )
    assert "table_year_headers" in prompt
    assert "nearby_previous_row" in prompt
    assert "nearby_next_row" in prompt
    assert "2026E" in prompt


def test_parse_model_json_repairs_fenced_json() -> None:
    parsed, method = parse_model_json(
        """```json
        {"decision":"NEEDS_MORE_CONTEXT","suggested_metric":null,"suggested_year":null,"suggested_value":null,"suggested_unit":null,"table_role_guess":"UNKNOWN","risk_flags":[],"confidence":0.8,"reason":"证据不足","evidence_quote":"营业收入"}
        ```"""
    )
    assert parsed is not None
    assert parsed["decision"] == "NEEDS_MORE_CONTEXT"
    assert method == "fence_repair"


def test_build_ab_with_mocked_rows_and_no_key_written(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "338a"
    reviewed_dir = tmp_path / "337d"
    output_dir = tmp_path / "338b"
    baseline_dir.mkdir()
    reviewed_dir.mkdir()

    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    (baseline_dir / "deepseek_text_adjudicator_338a_summary.json").write_text(
        json.dumps(
            {
                "model_name": "deepseek-v4-flash",
                "invalid_response_count": 0,
                "low_confidence_count": 1,
                "needs_more_context_count": 1,
                "confirm_reviewed_count": 1,
                "downgrade_to_needs_review_count": 0,
                "reject_count": 0,
                "rule_model_conflict_count": 0,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_338a_workbook(baseline_dir / "deepseek_text_adjudication_plan_338a.xlsx")
    _write_337d_workbook(reviewed_dir / "real_test_mineru_client_export_337d.xlsx")
    (reviewed_dir / "reviewed_strictness_year_alignment_337d_before_after.xlsx").write_bytes(b"placeholder")
    (reviewed_dir / "reviewed_strictness_year_alignment_337d_summary.json").write_text(
        json.dumps({"decision": "REVIEWED_STRICTNESS_YEAR_ALIGNMENT_337D_READY"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    client = MockClient(
        [
            '{"decision":"CONFIRM_REVIEWED","suggested_metric":"revenue","suggested_year":"2026E","suggested_value":"123","suggested_unit":"百万元","table_role_guess":"CORE_FINANCIAL_SUMMARY","risk_flags":[],"confidence":0.91,"reason":"证据可支持确认","evidence_quote":"营业收入 | 100 | 123 | 150"}',
            'not-json',
        ]
    )

    artifacts = build_ai_review_model_ab_338b(
        baseline_338a_dir=baseline_dir,
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
    assert summary["invalid_response_count_new"] == 1
    assert summary["low_confidence_count_new"] == 0
    assert summary["decision_changed_count"] == 2
    assert summary["evidence_quote_invalid_count"] == 1
    assert summary["AI_REVIEW_API_KEY"] == "SET"
    serialized = json.dumps(artifacts, ensure_ascii=False, default=str)
    assert "secret-ai-key" not in serialized
    assert summary["recommendation"] in {NEED_MORE_PRO_MODEL_TEST, SWITCH_TO_AI_REVIEW_MODEL, KEEP_DEEPSEEK_FLASH}

    comparison_df = artifacts["workbook_sheets"]["04_ROW_LEVEL_COMPARISON"]
    assert list(comparison_df["adjudication_id"]) == ["row-1", "row-2"]
    assert comparison_df.loc[0, "new_final_action"] == "CONFIRM_REVIEWED"
    assert comparison_df.loc[1, "new_final_action"] == "NEEDS_MORE_CONTEXT"


def test_recommendation_logic_variants() -> None:
    assert (
        _build_recommendation(
            {
                "row_count": 50,
                "invalid_response_count_baseline": 0,
                "invalid_response_count_new": 0,
                "low_confidence_count_baseline": 34,
                "low_confidence_count_new": 20,
                "needs_more_context_count_baseline": 33,
                "needs_more_context_count_new": 20,
                "rule_model_conflict_count_baseline": 0,
                "rule_model_conflict_count_new": 0,
                "evidence_quote_invalid_count": 0,
                "decision_changed_count": 10,
                "prompt_year_header_hit_count": 30,
            }
        )
        == SWITCH_TO_AI_REVIEW_MODEL
    )
    assert (
        _build_recommendation(
            {
                "row_count": 50,
                "invalid_response_count_baseline": 0,
                "invalid_response_count_new": 1,
                "low_confidence_count_baseline": 34,
                "low_confidence_count_new": 18,
                "needs_more_context_count_baseline": 33,
                "needs_more_context_count_new": 18,
                "rule_model_conflict_count_baseline": 0,
                "rule_model_conflict_count_new": 0,
                "evidence_quote_invalid_count": 0,
                "decision_changed_count": 12,
                "prompt_year_header_hit_count": 30,
            }
        )
        == NEED_MORE_PRO_MODEL_TEST
    )
    assert (
        _build_recommendation(
            {
                "row_count": 50,
                "invalid_response_count_baseline": 0,
                "invalid_response_count_new": 0,
                "low_confidence_count_baseline": 34,
                "low_confidence_count_new": 34,
                "needs_more_context_count_baseline": 33,
                "needs_more_context_count_new": 33,
                "rule_model_conflict_count_baseline": 0,
                "rule_model_conflict_count_new": 0,
                "evidence_quote_invalid_count": 0,
                "decision_changed_count": 0,
                "prompt_year_header_hit_count": 30,
            }
        )
        == KEEP_DEEPSEEK_FLASH
    )
