from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust import (  # noqa: E402
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    ROUTING_REJECTED,
    ROUTING_REVIEW_REQUIRED,
    ROUTING_TRUSTED,
    build_no_apply_proof,
    build_trust_record,
    capture_official_asset_hashes,
    coerce_risk_registry_summary,
    risk_registry_rows,
    routing_policy_smoke_cases,
)
from datefac.trust.trust_engine_foundation_330a_report import (  # noqa: E402
    trust_engine_foundation_330a_markdown,
    write_excel,
    write_json,
)


READY_325P_DECISIONS = {
    "ALIAS_PATCH_CYCLE_325P_CLOSED_READY_FOR_TRUST_ENGINE_CONSOLIDATION",
    "ALIAS_PATCH_CYCLE_325P_CLOSED_WITH_WARNINGS_READY_FOR_TRUST_ENGINE_CONSOLIDATION",
}
READY_DECISION = "TRUST_ENGINE_FOUNDATION_330A_READY_FOR_330B_RISK_REGISTRY_AND_SCORING_INTEGRATION"
NOT_READY_DECISION = "TRUST_ENGINE_FOUNDATION_330A_NOT_READY"
DEFAULT_CYCLE_CLOSURE_DIR = Path(r"D:\_datefac\output\alias_patch_cycle_closure_325p")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\trust_engine_foundation_330a")


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "330A",
        "output_dir": str(output_dir),
        "risk_registry_count": 0,
        "example_trust_record_count": 0,
        "routing_policy_smoke_test_count": 0,
        "routing_policy_smoke_test_passed": False,
        "validated_325p_closure": False,
        "no_official_asset_modification_during_330a": True,
        "official_assets_written": [],
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision": NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    no_apply_proof = build_no_apply_proof(
        stage="330A",
        files_read=[],
        official_assets_before=capture_official_asset_hashes(),
        official_assets_after=capture_official_asset_hashes(),
        official_assets_written=[],
    )
    write_json(output_dir / "trust_engine_foundation_330a_summary.json", summary)
    write_json(output_dir / "trust_engine_foundation_330a_qa.json", qa_json)
    write_json(output_dir / "trust_engine_foundation_330a_no_apply_proof.json", no_apply_proof)
    write_json(output_dir / "trust_engine_foundation_330a_example_trust_records.json", {"records": []})
    sheets = {
        "summary": pd.DataFrame([summary]),
        "risk_registry": pd.DataFrame(),
        "example_trust_records": pd.DataFrame(),
        "routing_smoke_tests": pd.DataFrame(),
        "closure_validation": pd.DataFrame(),
        "official_asset_proof": pd.DataFrame(),
        "qa_summary": pd.DataFrame([{"qa_fail_count": 1, "decision": NOT_READY_DECISION}]),
        "qa_checks": pd.DataFrame(qa_json["checks"]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": code}]),
    }
    write_excel(output_dir / "trust_engine_foundation_330a_summary.xlsx", sheets)
    (output_dir / "trust_engine_foundation_330a_report.md").write_text(
        trust_engine_foundation_330a_markdown(summary),
        encoding="utf-8",
    )
    return summary


def _build_example_records() -> List[Dict[str, Any]]:
    return [
        build_trust_record(
            {
                "candidate_id": "trust_330a_example_001",
                "metric_label_raw": "归母净利润",
                "normalized_metric": "attributable_net_profit",
                "value": 128.6,
                "unit": "CNY_million",
                "year": "2025E",
                "parser_sources": ["pdfplumber", "table_postprocess"],
                "evidence_refs": ["325p_summary", "fixture://high_confidence"],
                "risk_flags": [],
                "evidence_score": 96,
                "semantic_score": 94,
                "unit_year_score": 90,
                "parser_agreement_score": 92,
                "risk_penalty": 0,
                "provenance": {
                    "stage": "330A",
                    "fixture_type": "high_confidence_trusted_candidate",
                    "source_cycle": "325P",
                },
            }
        ),
        build_trust_record(
            {
                "candidate_id": "trust_330a_example_002",
                "metric_label_raw": "经调整归母净利润（预测）说明口径",
                "normalized_metric": "adjusted_parent_net_profit",
                "value": 88.2,
                "unit": "CNY_million",
                "year": "2026E",
                "parser_sources": ["pdfplumber"],
                "evidence_refs": ["325p_summary", "fixture://warning_review_required"],
                "risk_flags": ["ADJUSTED_METRIC_RISK", "LOW_EVIDENCE_STRENGTH", "LONG_NARRATIVE_LABEL"],
                "evidence_score": 72,
                "semantic_score": 70,
                "unit_year_score": 76,
                "parser_agreement_score": 74,
                "risk_penalty": 2,
                "provenance": {
                    "stage": "330A",
                    "fixture_type": "review_required_warning_risks",
                    "source_cycle": "325P",
                },
            }
        ),
        build_trust_record(
            {
                "candidate_id": "trust_330a_example_003",
                "metric_label_raw": "P/E(调整后?)",
                "normalized_metric": "price_earnings_ratio",
                "value": None,
                "unit": "x",
                "year": "",
                "parser_sources": ["pdfplumber", "marker_cached"],
                "evidence_refs": ["325p_summary", "fixture://blocking_rejected"],
                "risk_flags": ["OFFICIAL_RULE_CONFLICT", "VALUE_PARSE_FAILED", "TARGET_METRIC_AMBIGUOUS"],
                "evidence_score": 28,
                "semantic_score": 34,
                "unit_year_score": 15,
                "parser_agreement_score": 20,
                "risk_penalty": 6,
                "provenance": {
                    "stage": "330A",
                    "fixture_type": "rejected_blocking_risks",
                    "source_cycle": "325P",
                },
            },
            blocking_policy="reject",
            low_score_policy="reject",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330A trust engine foundation.")
    parser.add_argument("--cycle-closure-dir", default=str(DEFAULT_CYCLE_CLOSURE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    cycle_closure_dir = Path(args.cycle_closure_dir)
    output_dir = Path(args.output_dir)
    summary_path = cycle_closure_dir / "alias_patch_cycle_closure_325p_summary.json"
    no_apply_path = cycle_closure_dir / "alias_patch_cycle_closure_325p_no_apply_proof.json"
    if not summary_path.exists():
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_325P_SUMMARY")
        print(f"trust_engine_foundation_330a_summary_json: {output_dir / 'trust_engine_foundation_330a_summary.json'}")
        print(f"qa_fail_count: {summary['qa_fail_count']}")
        print(f"decision: {summary['decision']}")
        return 0
    if not no_apply_path.exists():
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_325P_NO_APPLY_PROOF")
        print(f"trust_engine_foundation_330a_summary_json: {output_dir / 'trust_engine_foundation_330a_summary.json'}")
        print(f"qa_fail_count: {summary['qa_fail_count']}")
        print(f"decision: {summary['decision']}")
        return 0

    summary_325p = _read_json(summary_path)
    no_apply_325p = _read_json(no_apply_path)
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    official_assets_before = capture_official_asset_hashes()

    add_qa(
        "readiness::325p_decision",
        str(summary_325p.get("decision", "")).strip() in READY_325P_DECISIONS,
        str(summary_325p.get("decision", "")).strip(),
    )
    add_qa("readiness::325p_qa_fail_count", int(summary_325p.get("qa_fail_count", 1)) == 0, str(summary_325p.get("qa_fail_count", "")))
    for key, expected in [
        ("official_alias_rule_count_325", 6),
        ("trusted_gain_325", 45),
        ("review_reduction_325", 45),
        ("out_of_scope_or_rejected_gain_325", 0),
        ("affected_candidate_count_325", 45),
    ]:
        add_qa(f"readiness::325p_{key}", int(summary_325p.get(key, -1)) == expected, f"expected={expected} actual={summary_325p.get(key, '')}")
    add_qa(
        "readiness::325p_primary_next_direction",
        str(summary_325p.get("primary_next_direction", "")).strip() == "330A Trust Engine Consolidation",
        str(summary_325p.get("primary_next_direction", "")).strip(),
    )
    add_qa(
        "readiness::325p_no_official_asset_modification",
        bool(summary_325p.get("no_official_asset_modification_during_325p")) is True,
        str(summary_325p.get("no_official_asset_modification_during_325p", "")),
    )
    add_qa(
        "readiness::325p_no_apply_proof_present",
        bool(no_apply_325p.get("no_official_asset_modification_during_325p")) is True,
        str(no_apply_325p.get("no_official_asset_modification_during_325p", "")),
    )

    risk_rows = risk_registry_rows()
    add_qa("risk_registry::minimum_count", len(risk_rows) >= 18, f"actual={len(risk_rows)}")

    example_records = _build_example_records()
    add_qa("example_records::count", len(example_records) == 3, f"actual={len(example_records)}")
    trusted_count = sum(1 for row in example_records if row["routing_decision"] == ROUTING_TRUSTED)
    review_count = sum(1 for row in example_records if row["routing_decision"] == ROUTING_REVIEW_REQUIRED)
    rejected_count = sum(1 for row in example_records if row["routing_decision"] == ROUTING_REJECTED)
    add_qa("example_records::trusted_case_present", trusted_count >= 1, f"actual={trusted_count}")
    add_qa("example_records::review_case_present", review_count >= 1, f"actual={review_count}")
    add_qa("example_records::rejected_case_present", rejected_count >= 1, f"actual={rejected_count}")

    smoke_rows = routing_policy_smoke_cases()
    smoke_passed = all(bool(row.get("passed")) for row in smoke_rows) and len(smoke_rows) >= 3
    add_qa("routing_policy::smoke_test_count", len(smoke_rows) >= 3, f"actual={len(smoke_rows)}")
    add_qa("routing_policy::smoke_tests_passed", smoke_passed, f"actual={smoke_passed}")

    official_assets_after = capture_official_asset_hashes()
    no_apply_proof = build_no_apply_proof(
        stage="330A",
        files_read=[
            str(summary_path),
            str(no_apply_path),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_key = "no_official_asset_modification_during_330a"
    add_qa("safety::no_official_asset_modification_during_330a", bool(no_apply_proof.get(no_apply_key)) is True, str(no_apply_proof.get(no_apply_key, "")))

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "330A",
        "output_dir": str(output_dir),
        "risk_registry_count": len(risk_rows),
        "example_trust_record_count": len(example_records),
        "routing_policy_smoke_test_count": len(smoke_rows),
        "routing_policy_smoke_test_passed": smoke_passed,
        "validated_325p_closure": qa_fail_count == 0,
        "no_official_asset_modification_during_330a": bool(no_apply_proof.get(no_apply_key)),
        "official_assets_written": [],
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "trust_engine_foundation_330a_summary.json"
    qa_json = output_dir / "trust_engine_foundation_330a_qa.json"
    records_json = output_dir / "trust_engine_foundation_330a_example_trust_records.json"
    no_apply_json = output_dir / "trust_engine_foundation_330a_no_apply_proof.json"
    report_md = output_dir / "trust_engine_foundation_330a_report.md"
    summary_xlsx = output_dir / "trust_engine_foundation_330a_summary.xlsx"

    write_json(summary_json, summary)
    write_json(
        qa_json,
        {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
    )
    write_json(records_json, {"records": example_records})
    write_json(no_apply_json, no_apply_proof)

    closure_validation_df = pd.DataFrame(
        [
            {
                "decision": summary_325p.get("decision", ""),
                "qa_fail_count": summary_325p.get("qa_fail_count", ""),
                "official_alias_rule_count_325": summary_325p.get("official_alias_rule_count_325", ""),
                "trusted_gain_325": summary_325p.get("trusted_gain_325", ""),
                "review_reduction_325": summary_325p.get("review_reduction_325", ""),
                "out_of_scope_or_rejected_gain_325": summary_325p.get("out_of_scope_or_rejected_gain_325", ""),
                "affected_candidate_count_325": summary_325p.get("affected_candidate_count_325", ""),
                "primary_next_direction": summary_325p.get("primary_next_direction", ""),
                "validated_325p_closure": qa_fail_count == 0,
            }
        ]
    ).fillna("")
    official_asset_proof_df = pd.DataFrame(
        [
            {"asset_path": path, "hash_before": before_hash, "hash_after": official_assets_after.get(path, ""), "modified_during_330a": before_hash != official_assets_after.get(path, "")}
            for path, before_hash in official_assets_before.items()
        ]
    ).fillna("")
    qa_summary_df = pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": qa_warn_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": summary["decision"],
            }
        ]
    ).fillna("")
    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "foundation_only",
                "detail": "330A standardizes trust-layer schema and routing only; it does not wire the foundation into production execution.",
            },
            {
                "limitation": "cached_fixture_examples",
                "detail": "Example trust records are smoke fixtures informed by cached 323/324/325 artifacts rather than fresh production recomputation.",
            },
            {
                "limitation": "read_only_assets",
                "detail": "Official alias and scope assets are read-only in 330A and checked with before/after hash proof.",
            },
        ]
    ).fillna("")
    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "risk_registry": pd.DataFrame(risk_rows).fillna(""),
        "example_trust_records": pd.DataFrame(example_records).fillna(""),
        "routing_smoke_tests": pd.DataFrame(smoke_rows).fillna(""),
        "closure_validation": closure_validation_df,
        "official_asset_proof": official_asset_proof_df,
        "qa_summary": qa_summary_df,
        "qa_checks": qa_df,
        "known_limitations": known_limitations_df,
    }
    write_excel(summary_xlsx, sheets)
    report_md.write_text(trust_engine_foundation_330a_markdown(summary), encoding="utf-8")

    print(f"trust_engine_foundation_330a_summary_json: {summary_json}")
    print(f"trust_engine_foundation_330a_qa_json: {qa_json}")
    print(f"trust_engine_foundation_330a_example_trust_records_json: {records_json}")
    print(f"trust_engine_foundation_330a_no_apply_proof_json: {no_apply_json}")
    print(f"trust_engine_foundation_330a_summary_xlsx: {summary_xlsx}")
    print(f"trust_engine_foundation_330a_report_md: {report_md}")
    for key in [
        "risk_registry_count",
        "example_trust_record_count",
        "routing_policy_smoke_test_count",
        "routing_policy_smoke_test_passed",
        "validated_325p_closure",
        "no_official_asset_modification_during_330a",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
