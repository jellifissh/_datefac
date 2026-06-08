from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.deepseek_text_adjudicator_338a import (  # noqa: E402
    READY_DECISION,
    build_cache_key,
    build_deepseek_text_adjudicator_338a,
    build_prompt_text,
    deterministic_guard,
    parse_model_json,
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


def _write_337d_workbook(path: Path) -> None:
    needs_review = pd.DataFrame(
        [
            {
                "row_no": 1,
                "document": "a.pdf",
                "metric": "rating",
                "metric_display_zh": "投资评级",
                "year": "",
                "value": "增持",
                "unit": "",
                "source_page": 1,
                "status": "needs_review",
                "source_evidence_excerpt": "投资评级：增持（首次）",
                "notes": "metric_not_allowed_for_reviewed",
            },
            {
                "row_no": 2,
                "document": "b.pdf",
                "metric": "revenue",
                "metric_display_zh": "营业收入",
                "year": "2026E",
                "value": "123",
                "unit": "百万元",
                "source_page": 2,
                "status": "needs_review",
                "source_evidence_excerpt": "营业收入 | 100 | 123 | 140",
                "notes": "manual_review",
            },
        ]
    )
    suspicious = pd.DataFrame(
        [
            {
                "candidate_id": "c1",
                "document": "c.pdf",
                "metric": "net_profit",
                "year": "2026E",
                "value": "15%",
                "unit": "%",
                "source_page": 9,
                "evidence": "归属于母公司净利润 | 4.29% | 15% | 30%",
                "suspicious_reason": "percent_value_for_amount_metric",
                "337d_action": "DOWNGRADE_PERCENT_AS_AMOUNT",
            }
        ]
    )
    route_change = pd.DataFrame(
        [
            {
                "candidate_id": "c1",
                "document": "c.pdf",
                "metric_before_337d": "net_profit",
                "metric_after_337d": "net_profit",
                "year_before_337d": "2026E",
                "year_after_337d": "2026E",
                "unit_before_337d": "%",
                "unit_after_337d": "%",
                "status_before_337d": "reviewed_preview",
                "status_after_337d": "needs_review",
                "route_reason_before_337d": "core_financial_context_repaired",
                "route_reason_after_337d": "percent_amount_guard_downgraded",
                "duplicate_of": "",
                "337d_action": "DOWNGRADE_PERCENT_AS_AMOUNT",
                "suspicious_reason": "percent_value_for_amount_metric",
                "source_evidence_excerpt": "归属于母公司净利润 | 4.29% | 15% | 30%",
            }
        ]
    )
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "x", "message": "y"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"row_no": 1}]).to_excel(writer, sheet_name="01_REVIEWED_CORE_METRICS", index=False)
        needs_review.to_excel(writer, sheet_name="02_NEEDS_REVIEW", index=False)
        pd.DataFrame([{"row_no": 1}]).to_excel(writer, sheet_name="03_REJECTED_OR_EXCLUDED", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="04_SOURCE_TRACE", index=False)
        pd.DataFrame([{"document": "a.pdf"}]).to_excel(writer, sheet_name="05_DOCUMENT_SUMMARY", index=False)
        pd.DataFrame([{"document": "a.pdf"}]).to_excel(writer, sheet_name="06_TABLE_CLASSIFICATION_SUMMARY", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="07_CONTEXT_REPAIR_SUMMARY", index=False)
        suspicious.to_excel(writer, sheet_name="08_SUSPICIOUS_REVIEWED_AUDIT", index=False)
        route_change.to_excel(writer, sheet_name="09_ROUTE_CHANGE_TRACE", index=False)


def test_prompt_construction_contains_compact_fields() -> None:
    prompt = build_prompt_text(
        {
            "document": "a.pdf",
            "source_sheet": "02_NEEDS_REVIEW",
            "source_row_no": 2,
            "metric_before": "revenue",
            "metric_display_zh": "营业收入",
            "year_before": "2026E",
            "value_before": "123",
            "unit_before": "百万元",
            "source_page": 2,
            "status_before": "needs_review",
            "evidence": "营业收入 | 100 | 123 | 140",
            "suspicious_reason": "",
            "notes": "manual_review",
            "route_change_context": "status_before=reviewed",
        }
    )
    assert "营业收入" in prompt
    assert "source_evidence_excerpt" in prompt
    assert "strict JSON" in prompt or "JSON" in prompt


def test_parse_model_json_repairs_fenced_json() -> None:
    parsed, method = parse_model_json(
        """```json
        {"decision":"NEEDS_MORE_CONTEXT","suggested_metric":null,"suggested_year":null,"suggested_value":null,"suggested_unit":null,"table_role_guess":"UNKNOWN","risk_flags":[],"confidence":0.8,"reason":"证据不足","evidence_quote":"营业收入"}
        ```"""
    )
    assert parsed is not None
    assert parsed["decision"] == "NEEDS_MORE_CONTEXT"
    assert method == "fence_repair"


def test_deterministic_guard_priority_rejects_percent_amount() -> None:
    guard = deterministic_guard(
        {
            "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
            "metric_before": "net_profit",
            "value_before": "15%",
            "unit_before": "%",
            "notes": "",
        },
        {
            "suggested_metric": "net_profit",
            "suggested_value": "15%",
            "suggested_unit": "%",
            "table_role_guess": "FINANCIAL_STATEMENT_DETAIL",
        },
    )
    assert guard == "HARD_REJECT_PERCENT_AS_AMOUNT"


def test_cache_key_stability() -> None:
    row = {
        "document": "a.pdf",
        "metric_before": "revenue",
        "year_before": "2026E",
        "value_before": "123",
        "unit_before": "百万元",
        "evidence": "营业收入 | 100 | 123 | 140",
        "suspicious_reason": "",
    }
    assert build_cache_key(row) == build_cache_key(dict(row))


def test_build_deepseek_text_adjudicator_with_mocked_rows(tmp_path: Path, monkeypatch) -> None:
    reviewed_dir = tmp_path / "337d"
    output_dir = tmp_path / "338a"
    reviewed_dir.mkdir()
    alias_asset = tmp_path / "semantic_alias_candidates.json"
    scope_asset = tmp_path / "formal_scope_rules.json"
    alias_asset.write_text("{}", encoding="utf-8")
    scope_asset.write_text("{}", encoding="utf-8")

    (reviewed_dir / "reviewed_strictness_year_alignment_337d_summary.json").write_text(
        json.dumps({"reviewed_after_count": 112, "needs_review_after_count": 28}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (reviewed_dir / "reviewed_strictness_year_alignment_337d_before_after.xlsx").write_bytes(b"placeholder")
    _write_337d_workbook(reviewed_dir / "real_test_mineru_client_export_337d.xlsx")

    monkeypatch.setenv("DEEPSEEK_API_KEY", "x")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://example.invalid")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-test")

    client = MockClient(
        [
            '{"decision":"CONFIRM_REVIEWED","suggested_metric":"net_profit","suggested_year":"2026E","suggested_value":"15%","suggested_unit":"%","table_role_guess":"FINANCIAL_STATEMENT_DETAIL","risk_flags":["percent_amount"],"confidence":0.92,"reason":"仍是百分比金额冲突","evidence_quote":"归属于母公司净利润 | 4.29% | 15% | 30%"}',
            'not-json',
            '{"decision":"CONFIRM_REVIEWED","suggested_metric":"revenue","suggested_year":"2026E","suggested_value":"123","suggested_unit":"百万元","table_role_guess":"CORE_FINANCIAL_SUMMARY","risk_flags":[],"confidence":0.55,"reason":"证据有限","evidence_quote":"营业收入 | 100 | 123 | 140"}',
        ]
    )

    artifacts = build_deepseek_text_adjudicator_338a(
        reviewed_strictness_337d_dir=reviewed_dir,
        output_dir=output_dir,
        limit=10,
        dry_run_prompts_only=False,
        timeout_seconds=5,
        client=client,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["decision"] == READY_DECISION
    assert summary["adjudication_row_count"] == 3
    assert summary["api_call_count"] == 3
    assert summary["invalid_response_count"] == 1
    assert summary["low_confidence_count"] == 1
    assert summary["rule_model_conflict_count"] >= 1
    assert summary["qa_fail_count"] == 0

    plan_df = artifacts["workbook_sheets"]["02_MODEL_ADJUDICATION_PLAN"]
    assert len(plan_df) == 3
    assert "recommended_final_action" in plan_df.columns
    assert "DOWNGRADE_TO_NEEDS_REVIEW" in set(plan_df["recommended_final_action"])
    assert "NEEDS_MORE_CONTEXT" in set(plan_df["recommended_final_action"])
    invalid_df = artifacts["workbook_sheets"]["04_INVALID_OR_LOW_CONFIDENCE"]
    assert len(invalid_df) == 2
