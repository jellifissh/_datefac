from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.human_review_after_ai_adoption_340b import (  # noqa: E402
    READY_DECISION,
    build_human_review_after_ai_adoption_340b,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def _build_337d_workbook(path: Path) -> None:
    needs_rows = [
        {
            "row_no": 1,
            "document": "doc_a.pdf",
            "metric": "stock_code",
            "metric_display_zh": "股票代码",
            "year": "",
            "value": "920304",
            "unit": "",
            "source_page": 1,
            "status": "needs_review",
            "source_evidence_excerpt": "metadata evidence",
            "notes": "metric_not_allowed_for_reviewed",
        },
        {
            "row_no": 2,
            "document": "doc_b.pdf",
            "metric": "net_profit",
            "metric_display_zh": "归母净利润",
            "year": "2026E",
            "value": "1816",
            "unit": "",
            "source_page": 12,
            "status": "needs_review",
            "source_evidence_excerpt": "needs review evidence",
            "notes": "missing_money_unit",
        },
    ]
    suspicious_rows = []
    for idx in range(1, 56):
        suspicious_rows.append(
            {
                "candidate_id": f"cand::{idx:03d}",
                "document": "doc_a.pdf" if idx <= 30 else "doc_b.pdf",
                "metric": "revenue" if idx % 2 == 0 else "net_profit",
                "year": f"202{(idx % 4) + 4}A",
                "value": str(100 + idx),
                "unit": "百万元",
                "source_page": 10 + (idx % 5),
                "evidence": f"evidence {idx}",
                "suspicious_reason": "duplicate_reviewed_row" if idx <= 50 else "leftover_suspicious",
                "337d_action": "REMOVE_DUPLICATE_REVIEWED",
            }
        )
    source_trace_rows = []
    for row in needs_rows:
        source_trace_rows.append(
            {
                "candidate_id": f"trace::{row['row_no']}",
                "document": row["document"],
                "metric_after_337d": row["metric"],
                "metric_display_zh_after_337d": row["metric_display_zh"],
                "year_after_337d": row["year"],
                "value": row["value"],
                "unit_after_337d": row["unit"],
                "source_page": row["source_page"],
                "status_after_337d": "needs_review",
                "source_evidence_excerpt": row["source_evidence_excerpt"],
                "table_preview": "table preview",
                "table_role_337c": "",
                "table_role_337b": "",
            }
        )
    _write_excel(
        path,
        {
            "00_README": pd.DataFrame([{"topic": "x", "message": "y"}]),
            "02_NEEDS_REVIEW": pd.DataFrame(needs_rows),
            "04_SOURCE_TRACE": pd.DataFrame(source_trace_rows),
            "08_SUSPICIOUS_REVIEWED_AUDIT": pd.DataFrame(suspicious_rows),
        },
    )


def _build_337d_before_after(path: Path) -> None:
    _write_excel(path, {"00_SUMMARY": pd.DataFrame([{"reviewed_after_count": 112}])})


def _build_338d_workbook(path: Path) -> None:
    all_rows = []
    row_no = 2
    action_specs = [
        ("ACCEPT_MODEL_CONFIRM", 39, "CONFIRM_REVIEWED", "PASS", "VALID"),
        ("ACCEPT_MODEL_REJECT", 3, "REJECT", "PASS", "VALID"),
        ("HOLD_FOR_HUMAN_REVIEW", 3, "NEEDS_MORE_CONTEXT", "PASS", "VALID"),
        ("REJECT_BY_DETERMINISTIC_RULE", 4, "DOWNGRADE_TO_NEEDS_REVIEW", "HARD_REJECT_MISSING_MONEY_UNIT", "VALID"),
        ("INVALID_MODEL_RESPONSE", 1, "NEEDS_MORE_CONTEXT", "HARD_REJECT_MISSING_MONEY_UNIT", "INVALID_RESPONSE"),
    ]
    running = 1
    sheet_rows: dict[str, list[dict[str, object]]] = {
        "03_ACCEPTED_CONFIRMS": [],
        "05_ACCEPTED_REJECTS": [],
        "06_HOLD_FOR_HUMAN_REVIEW": [],
        "07_REJECTED_BY_RULE": [],
        "08_INVALID_MODEL_RESPONSES": [],
    }
    for action, count, model_decision, guard, status in action_specs:
        for _ in range(count):
            row = {
                "adoption_id": f"338d::{running:03d}",
                "adjudication_id": f"adj::{running:03d}",
                "document": "doc_a.pdf" if running <= 25 else "doc_b.pdf",
                "source_sheet": "08_SUSPICIOUS_REVIEWED_AUDIT",
                "source_row_no": row_no,
                "metric_before": "revenue" if running % 2 == 0 else "net_profit",
                "year_before": f"202{(running % 4) + 4}A",
                "value_before": str(100 + running),
                "unit_before": "百万元" if action not in {"REJECT_BY_DETERMINISTIC_RULE", "INVALID_MODEL_RESPONSE"} else "",
                "model_decision": model_decision,
                "confidence": 0.9,
                "grounding_source": "BOTH" if action != "INVALID_MODEL_RESPONSE" else "INSUFFICIENT",
                "raw_quote_valid": True,
                "context_quote_valid": True,
                "deterministic_guard_result": guard,
                "adoption_action": action,
                "adoption_reason": action.lower(),
                "recommended_route_after_adoption": "reviewed_preview",
                "human_review_required": action in {"HOLD_FOR_HUMAN_REVIEW", "REJECT_BY_DETERMINISTIC_RULE", "INVALID_MODEL_RESPONSE"},
                "model_name": "gpt-5.5",
                "table_role_guess": "FINANCIAL_STATEMENT_DETAIL",
                "model_decision_status": status,
            }
            all_rows.append(row)
            if action == "ACCEPT_MODEL_CONFIRM":
                sheet_rows["03_ACCEPTED_CONFIRMS"].append(row)
            elif action == "ACCEPT_MODEL_REJECT":
                sheet_rows["05_ACCEPTED_REJECTS"].append(row)
            elif action == "HOLD_FOR_HUMAN_REVIEW":
                sheet_rows["06_HOLD_FOR_HUMAN_REVIEW"].append(row)
            elif action == "REJECT_BY_DETERMINISTIC_RULE":
                sheet_rows["07_REJECTED_BY_RULE"].append(row)
            else:
                sheet_rows["08_INVALID_MODEL_RESPONSES"].append(row)
            row_no += 1
            running += 1
    _write_excel(
        path,
        {
            "00_README": pd.DataFrame([{"topic": "x", "message": "y"}]),
            "01_ADOPTION_SUMMARY": pd.DataFrame([{"decision": "AI_REVIEW_ADOPTION_SIMULATION_338D_READY"}]),
            "02_ADOPTION_PLAN": pd.DataFrame(all_rows),
            "03_ACCEPTED_CONFIRMS": pd.DataFrame(sheet_rows["03_ACCEPTED_CONFIRMS"]),
            "05_ACCEPTED_REJECTS": pd.DataFrame(sheet_rows["05_ACCEPTED_REJECTS"]),
            "06_HOLD_FOR_HUMAN_REVIEW": pd.DataFrame(sheet_rows["06_HOLD_FOR_HUMAN_REVIEW"]),
            "07_REJECTED_BY_RULE": pd.DataFrame(sheet_rows["07_REJECTED_BY_RULE"]),
            "08_INVALID_MODEL_RESPONSES": pd.DataFrame(sheet_rows["08_INVALID_MODEL_RESPONSES"]),
        },
    )


def _build_340a_workbook(path: Path) -> None:
    _write_excel(
        path,
        {
            "01_AUDIT_SUMMARY": pd.DataFrame(
                [
                    {
                        "reviewed_after_count_337d": 112,
                        "accept_model_confirm_count_338d": 39,
                        "accept_model_reject_count_338d": 3,
                        "hold_for_human_review_count_338d": 3,
                        "invalid_model_response_count_338d": 1,
                        "qa_fail_count": 0,
                    }
                ]
            )
        },
    )


def test_build_human_review_after_ai_adoption_340b(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    reviewed_dir = repo_root / "output" / "reviewed_strictness_year_alignment_337d"
    adoption_dir = repo_root / "output" / "ai_review_adoption_simulation_338d"
    audit_dir = repo_root / "output" / "milestone_acceptance_audit_340a"
    output_dir = repo_root / "output" / "human_review_after_ai_adoption_340b"

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    _write_json(reviewed_dir / "reviewed_strictness_year_alignment_337d_summary.json", {"reviewed_after_count": 112})
    _write_json(
        adoption_dir / "ai_review_adoption_simulation_338d_summary.json",
        {
            "accept_model_confirm_count": 39,
            "accept_model_reject_count": 3,
            "hold_for_human_review_count": 3,
            "reject_by_deterministic_rule_count": 4,
            "invalid_model_response_count": 1,
        },
    )
    _write_json(audit_dir / "milestone_acceptance_audit_340a_summary.json", {"qa_fail_count": 0})

    _build_337d_workbook(reviewed_dir / "real_test_mineru_client_export_337d.xlsx")
    _build_337d_before_after(reviewed_dir / "reviewed_strictness_year_alignment_337d_before_after.xlsx")
    _build_338d_workbook(adoption_dir / "ai_review_adoption_simulation_338d_plan.xlsx")
    _build_340a_workbook(audit_dir / "milestone_acceptance_audit_340a.xlsx")

    artifacts = build_human_review_after_ai_adoption_340b(
        reviewed_strictness_337d_dir=reviewed_dir,
        ai_adoption_338d_dir=adoption_dir,
        milestone_audit_340a_dir=audit_dir,
        output_dir=output_dir,
        repo_root=repo_root,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["hold_for_human_count"] == 3
    assert summary["invalid_model_response_count"] == 1
    assert summary["rejected_by_rule_check_count"] == 4
    assert summary["accepted_confirm_spot_check_count"] == 10
    assert summary["accepted_reject_spot_check_count"] == 3
    assert summary["reviewer_fields_present"] is True
    assert summary["upstream_workbooks_unchanged"] is True
    assert summary["no_write_back"] is True
    assert summary["decision"] == READY_DECISION
    queue_df = artifacts["workbook_sheets"]["01_REVIEW_QUEUE"]
    assert "reviewer_decision" in queue_df.columns
    assert len(queue_df) >= 23

