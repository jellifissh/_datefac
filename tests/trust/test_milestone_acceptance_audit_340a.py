from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.milestone_acceptance_audit_340a import (  # noqa: E402
    MILESTONE_ACCEPTED_WITH_REVIEW_CAVEATS,
    build_milestone_acceptance_audit_340a,
)


EXPECTED_PDFS = [
    "H3_AP202606081823352620_1.pdf",
    "H3_AP202606081823352906_1.pdf",
    "H3_AP202606081823356439_1.pdf",
]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_simple_xlsx(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([{"ok": 1}]).to_excel(writer, sheet_name="Sheet1", index=False)


def _write_337d_workbook(path: Path) -> None:
    reviewed_rows = []
    for doc, count in [
        ("H3_AP202606081823352620_1.pdf", 12),
        ("H3_AP202606081823352906_1.pdf", 5),
        ("H3_AP202606081823356439_1.pdf", 11),
    ]:
        for index in range(count):
            reviewed_rows.append(
                {
                    "candidate_id": f"{doc}::{index}",
                    "document": doc,
                    "metric_after_337d": "revenue",
                    "metric_display_zh_after_337d": "营业收入",
                    "year_after_337d": "2026E",
                    "value": str(100 + index),
                    "unit_after_337d": "百万元",
                    "source_page": index + 1,
                    "status_after_337d": "reviewed_preview",
                    "source_evidence_excerpt": f"evidence {doc} {index}",
                    "table_role_337c": "CORE_FINANCIAL_SUMMARY",
                }
            )
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "x", "message": "y"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"row_no": 1, "document": "x"}]).to_excel(writer, sheet_name="01_REVIEWED_CORE_METRICS", index=False)
        pd.DataFrame([{"row_no": 1, "document": "x"}]).to_excel(writer, sheet_name="02_NEEDS_REVIEW", index=False)
        pd.DataFrame([{"row_no": 1, "document": "x"}]).to_excel(writer, sheet_name="03_REJECTED_OR_EXCLUDED", index=False)
        pd.DataFrame(reviewed_rows).to_excel(writer, sheet_name="04_SOURCE_TRACE", index=False)
        pd.DataFrame([{"document": "x"}]).to_excel(writer, sheet_name="05_DOCUMENT_SUMMARY", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="06_TABLE_CLASSIFICATION_SUMMARY", index=False)
        pd.DataFrame([{"x": 1}]).to_excel(writer, sheet_name="07_CONTEXT_REPAIR_SUMMARY", index=False)
        pd.DataFrame([{"candidate_id": "x"}]).to_excel(writer, sheet_name="08_SUSPICIOUS_REVIEWED_AUDIT", index=False)
        pd.DataFrame([{"candidate_id": "x"}]).to_excel(writer, sheet_name="09_ROUTE_CHANGE_TRACE", index=False)


def _write_338d_plan(path: Path) -> None:
    rows = []
    action_specs = [
        ("ACCEPT_MODEL_CONFIRM", 39),
        ("ACCEPT_MODEL_REJECT", 3),
        ("HOLD_FOR_HUMAN_REVIEW", 3),
        ("INVALID_MODEL_RESPONSE", 1),
        ("REJECT_BY_DETERMINISTIC_RULE", 4),
    ]
    running = 0
    for action, count in action_specs:
        for _ in range(count):
            running += 1
            rows.append(
                {
                    "adoption_id": f"a-{running}",
                    "adjudication_id": f"j-{running}",
                    "document": EXPECTED_PDFS[running % 3],
                    "metric_before": "revenue",
                    "year_before": "2026E",
                    "value_before": str(100 + running),
                    "unit_before": "百万元",
                    "model_name": "gpt-5.5",
                    "confidence": 0.9,
                    "grounding_source": "BOTH",
                    "adoption_action": action,
                    "adoption_reason": action.lower(),
                    "recommended_route_after_adoption": "reviewed_preview",
                    "human_review_required": action in {"HOLD_FOR_HUMAN_REVIEW", "INVALID_MODEL_RESPONSE", "REJECT_BY_DETERMINISTIC_RULE"},
                    "source_row_no": running,
                }
            )
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([{"topic": "x", "message": "y"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"decision": "ready"}]).to_excel(writer, sheet_name="01_ADOPTION_SUMMARY", index=False)
        pd.DataFrame(rows).to_excel(writer, sheet_name="02_ADOPTION_PLAN", index=False)


def test_build_milestone_acceptance_audit(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    docs_root = repo_root / "docs"
    output_root = repo_root / "output"
    input_pdf_dir = repo_root / "input" / "real_test"
    output_dir = output_root / "milestone_acceptance_audit_340a"

    input_pdf_dir.mkdir(parents=True, exist_ok=True)
    for pdf_name in EXPECTED_PDFS:
        (input_pdf_dir / pdf_name).write_bytes(b"%PDF-1.4")

    # Official assets
    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    # 337A
    _write_json(output_root / "mineru_real_test_337a" / "00_batch_summary.json", {"pdf_processed_count": 3})
    _write_simple_xlsx(output_root / "mineru_real_test_337a" / "real_test_mineru_client_export_337a.xlsx")
    for pdf_name, count in zip(EXPECTED_PDFS, [134, 111, 102]):
        _write_json(
            output_root / "mineru_real_test_337a" / "datefac_debug" / Path(pdf_name).stem / "document_summary.json",
            {"metric_candidate_count": count},
        )

    # 337B / 337C / 337D
    _write_json(output_root / "mineru_candidate_precision_337b" / "mineru_candidate_precision_337b_summary.json", {"reviewed_after_count": 98})
    _write_simple_xlsx(output_root / "mineru_candidate_precision_337b" / "real_test_mineru_client_export_337b.xlsx")

    _write_json(output_root / "core_financial_context_repair_337c" / "core_financial_context_repair_337c_summary.json", {"reviewed_after_count": 148})
    _write_simple_xlsx(output_root / "core_financial_context_repair_337c" / "real_test_mineru_client_export_337c.xlsx")

    _write_json(output_root / "reviewed_strictness_year_alignment_337d" / "reviewed_strictness_year_alignment_337d_summary.json", {"reviewed_after_count": 112})
    _write_337d_workbook(output_root / "reviewed_strictness_year_alignment_337d" / "real_test_mineru_client_export_337d.xlsx")

    # 338C / 338D
    _write_simple_xlsx(output_root / "grounded_ai_review_338c" / "grounded_ai_review_338c_plan.xlsx")
    _write_json(
        output_root / "ai_review_adoption_simulation_338d" / "ai_review_adoption_simulation_338d_summary.json",
        {
            "input_338c_row_count": 50,
            "accept_model_confirm_count": 39,
            "accept_model_reject_count": 3,
            "hold_for_human_review_count": 3,
            "invalid_model_response_count": 1,
            "deterministic_rule_override_count": 0,
        },
    )
    _write_338d_plan(output_root / "ai_review_adoption_simulation_338d" / "ai_review_adoption_simulation_338d_plan.xlsx")

    # Docs
    docs = {
        repo_root / "README.md": "\n".join(
            [
                "MinerU-first real PDF intake",
                "AI review dry-run / no-write-back",
                "not client-ready",
                "not production-ready",
                "AI_REVIEW_MODEL as candidate text adjudicator",
                "DeepSeek flash as fallback / baseline",
                "vision model only for future visual / layout uncertainty",
                "Unsafe Claims",
                "- client-ready",
                "- production-ready",
                "- fully automatic commercial SaaS",
            ]
        ),
        docs_root / "demo" / "datefac_real_pdf_mineru_ai_review_runbook_339a_zh.md": "MinerU 真实 PDF dry-run 不写回 不是 client-ready 不是 production-ready",
        docs_root / "demo" / "datefac_real_pdf_mineru_ai_review_runbook_339a_en.md": "MinerU real PDF dry-run no-write-back not client-ready not production-ready",
        docs_root / "demo" / "datefac_ai_review_architecture_339a_zh.md": "AI_REVIEW_MODEL DeepSeek flash vision model dry-run 不写回 不是 client-ready 不是 production-ready",
        docs_root / "demo" / "datefac_ai_review_architecture_339a_en.md": "AI_REVIEW_MODEL DeepSeek flash vision model dry-run not a write-back path not client-ready not production-ready",
    }
    for path, text in docs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    artifacts = build_milestone_acceptance_audit_340a(
        input_pdf_dir=input_pdf_dir,
        output_root=output_root,
        docs_root=docs_root,
        repo_root=repo_root,
        output_dir=output_dir,
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )

    summary = artifacts["summary"]
    assert summary["input_pdf_count"] == 3
    assert summary["candidate_count_352620_1"] == 134
    assert summary["candidate_count_352906_1"] == 111
    assert summary["candidate_count_356439_1"] == 102
    assert summary["reviewed_after_count_337d"] == 112
    assert summary["accept_model_confirm_count_338d"] == 39
    assert summary["documentation_consistency_passed"] is True
    assert summary["unsafe_claim_audit_passed"] is True
    assert summary["milestone_judgment"] == MILESTONE_ACCEPTED_WITH_REVIEW_CAVEATS
    assert summary["next_step_recommendation"] == "HUMAN_REVIEW_PACKAGE"

    reviewed_sample_df = artifacts["workbook_sheets"]["05_337D_REVIEWED_SAMPLE"]
    assert len(reviewed_sample_df) == 25
    ai_audit_df = artifacts["workbook_sheets"]["06_338D_AI_ADOPTION_AUDIT"]
    assert len(ai_audit_df) == 50


def test_unsafe_claim_scan_blocks_positive_phrase(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    docs_root = repo_root / "docs"
    output_root = repo_root / "output"
    input_pdf_dir = repo_root / "input" / "real_test"
    input_pdf_dir.mkdir(parents=True, exist_ok=True)
    for pdf_name in EXPECTED_PDFS:
        (input_pdf_dir / pdf_name).write_bytes(b"%PDF-1.4")

    alias_asset = repo_root / "data" / "overrides" / "semantic_alias_candidates.json"
    scope_asset = repo_root / "data" / "mapping" / "formal_scope_rules.json"
    _write_json(alias_asset, {})
    _write_json(scope_asset, {})

    _write_json(output_root / "mineru_real_test_337a" / "00_batch_summary.json", {"pdf_processed_count": 3})
    _write_simple_xlsx(output_root / "mineru_real_test_337a" / "real_test_mineru_client_export_337a.xlsx")
    for pdf_name, count in zip(EXPECTED_PDFS, [134, 111, 102]):
        _write_json(output_root / "mineru_real_test_337a" / "datefac_debug" / Path(pdf_name).stem / "document_summary.json", {"metric_candidate_count": count})
    _write_json(output_root / "mineru_candidate_precision_337b" / "mineru_candidate_precision_337b_summary.json", {"reviewed_after_count": 98})
    _write_simple_xlsx(output_root / "mineru_candidate_precision_337b" / "real_test_mineru_client_export_337b.xlsx")
    _write_json(output_root / "core_financial_context_repair_337c" / "core_financial_context_repair_337c_summary.json", {"reviewed_after_count": 148})
    _write_simple_xlsx(output_root / "core_financial_context_repair_337c" / "real_test_mineru_client_export_337c.xlsx")
    _write_json(output_root / "reviewed_strictness_year_alignment_337d" / "reviewed_strictness_year_alignment_337d_summary.json", {"reviewed_after_count": 112})
    _write_337d_workbook(output_root / "reviewed_strictness_year_alignment_337d" / "real_test_mineru_client_export_337d.xlsx")
    _write_simple_xlsx(output_root / "grounded_ai_review_338c" / "grounded_ai_review_338c_plan.xlsx")
    _write_json(output_root / "ai_review_adoption_simulation_338d" / "ai_review_adoption_simulation_338d_summary.json", {"input_338c_row_count": 50, "accept_model_confirm_count": 39, "accept_model_reject_count": 3, "hold_for_human_review_count": 3, "invalid_model_response_count": 1, "deterministic_rule_override_count": 0})
    _write_338d_plan(output_root / "ai_review_adoption_simulation_338d" / "ai_review_adoption_simulation_338d_plan.xlsx")

    bad_readme = repo_root / "README.md"
    bad_readme.write_text("This project is client-ready.", encoding="utf-8")
    for rel in [
        docs_root / "demo" / "datefac_real_pdf_mineru_ai_review_runbook_339a_zh.md",
        docs_root / "demo" / "datefac_real_pdf_mineru_ai_review_runbook_339a_en.md",
        docs_root / "demo" / "datefac_ai_review_architecture_339a_zh.md",
        docs_root / "demo" / "datefac_ai_review_architecture_339a_en.md",
    ]:
        rel.parent.mkdir(parents=True, exist_ok=True)
        rel.write_text("placeholder with not client-ready and not production-ready and AI_REVIEW_MODEL and DeepSeek flash and vision model and dry-run", encoding="utf-8")

    artifacts = build_milestone_acceptance_audit_340a(
        input_pdf_dir=input_pdf_dir,
        output_root=output_root,
        docs_root=docs_root,
        repo_root=repo_root,
        output_dir=output_root / "milestone_acceptance_audit_340a",
        alias_asset_path=alias_asset,
        scope_asset_path=scope_asset,
    )
    assert artifacts["summary"]["unsafe_claim_audit_passed"] is False
    assert artifacts["summary"]["milestone_judgment"] == "MILESTONE_BLOCKED"
