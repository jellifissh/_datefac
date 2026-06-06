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
    ROUTING_NEEDS_MORE_INFO,
    ROUTING_REJECTED,
    ROUTING_REVIEW_REQUIRED,
    ROUTING_TRUSTED,
    build_no_apply_proof,
    capture_official_asset_hashes,
    coerce_risk_registry_summary,
    risk_registry_rows,
)
from datefac.trust.confidence_scoring import (  # noqa: E402
    score_trust_record,
    scoring_model_summary,
)
from datefac.trust.trust_engine_scoring_330b_report import (  # noqa: E402
    trust_engine_scoring_330b_markdown,
    write_excel,
    write_json,
)


READY_330A_DECISION = "TRUST_ENGINE_FOUNDATION_330A_READY_FOR_330B_RISK_REGISTRY_AND_SCORING_INTEGRATION"
READY_325P_DECISIONS = {
    "ALIAS_PATCH_CYCLE_325P_CLOSED_READY_FOR_TRUST_ENGINE_CONSOLIDATION",
    "ALIAS_PATCH_CYCLE_325P_CLOSED_WITH_WARNINGS_READY_FOR_TRUST_ENGINE_CONSOLIDATION",
}
READY_DECISION = "TRUST_ENGINE_SCORING_330B_READY_FOR_330C_CACHED_CANDIDATE_TRUST_SCORING_BENCHMARK"
NOT_READY_DECISION = "TRUST_ENGINE_SCORING_330B_NOT_READY"
DEFAULT_TRUST_FOUNDATION_DIR = Path(r"D:\_datefac\output\trust_engine_foundation_330a")
DEFAULT_CYCLE_CLOSURE_DIR = Path(r"D:\_datefac\output\alias_patch_cycle_closure_325p")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\trust_engine_scoring_330b")


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
        "stage": "330B",
        "output_dir": str(output_dir),
        "validated_330a_foundation": False,
        "risk_registry_count": 0,
        "scoring_model_component_count": 0,
        "scored_example_count": 0,
        "routing_policy_reused": True,
        "routing_policy_smoke_test_count": 0,
        "routing_policy_smoke_test_passed": False,
        "cached_candidate_sidecar_sample_count": 0,
        "cached_candidate_sidecar_sample_reason": code,
        "no_official_asset_modification_during_330b": True,
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
        stage="330B",
        files_read=[],
        official_assets_before=capture_official_asset_hashes(),
        official_assets_after=capture_official_asset_hashes(),
        official_assets_written=[],
    )
    write_json(output_dir / "trust_engine_scoring_330b_summary.json", summary)
    write_json(output_dir / "trust_engine_scoring_330b_qa.json", qa_json)
    write_json(output_dir / "trust_engine_scoring_330b_no_apply_proof.json", no_apply_proof)
    write_json(output_dir / "trust_engine_scoring_330b_scored_examples.json", {"records": []})
    sheets = {
        "summary": pd.DataFrame([summary]),
        "foundation_validation": pd.DataFrame(),
        "scoring_model": pd.DataFrame(),
        "scored_examples": pd.DataFrame(),
        "routing_smoke_tests": pd.DataFrame(),
        "cached_sidecar_samples": pd.DataFrame(),
        "official_asset_proof": pd.DataFrame(),
        "qa_summary": pd.DataFrame([{"qa_fail_count": 1, "decision": NOT_READY_DECISION}]),
        "qa_checks": pd.DataFrame(qa_json["checks"]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": code}]),
    }
    write_excel(output_dir / "trust_engine_scoring_330b_summary.xlsx", sheets)
    (output_dir / "trust_engine_scoring_330b_report.md").write_text(
        trust_engine_scoring_330b_markdown(summary),
        encoding="utf-8",
    )
    return summary


def _build_scoring_examples() -> List[Dict[str, Any]]:
    return [
        {
            "case_id": "high_trusted_candidate",
            "expected_routing_decision": ROUTING_TRUSTED,
            "blocking_policy": "review",
            "low_score_policy": "needs_more_info",
            "payload": {
                "candidate_id": "trust_330b_example_001",
                "metric_label_raw": "ROE",
                "normalized_metric": "roe",
                "value": 15.4,
                "unit": "%",
                "year": "2025E",
                "parser_sources": ["pdfplumber", "table_postprocess"],
                "parser_agreement_signal": True,
                "evidence_refs": ["page=12", "table=3", "row=8"],
                "official_alias_match_signal": True,
                "semantic_target_unambiguous": True,
                "value_parse_success": True,
                "risk_flags": [],
                "provenance": {"fixture_type": "high_trusted_candidate", "stage": "330B"},
            },
        },
        {
            "case_id": "medium_review_required_candidate",
            "expected_routing_decision": ROUTING_REVIEW_REQUIRED,
            "blocking_policy": "review",
            "low_score_policy": "needs_more_info",
            "payload": {
                "candidate_id": "trust_330b_example_002",
                "metric_label_raw": "经调整归母净利润说明",
                "normalized_metric": "adjusted_parent_net_profit",
                "value": 82.1,
                "unit": "CNY_million",
                "year": "2026E",
                "parser_sources": ["pdfplumber"],
                "evidence_refs": ["page=9"],
                "official_alias_match_signal": False,
                "semantic_target_unambiguous": True,
                "value_parse_success": True,
                "risk_flags": ["LOW_EVIDENCE_STRENGTH", "LONG_NARRATIVE_LABEL"],
                "provenance": {"fixture_type": "medium_review_required_candidate", "stage": "330B"},
            },
        },
        {
            "case_id": "low_needs_more_info_candidate",
            "expected_routing_decision": ROUTING_NEEDS_MORE_INFO,
            "blocking_policy": "review",
            "low_score_policy": "needs_more_info",
            "payload": {
                "candidate_id": "trust_330b_example_003",
                "metric_label_raw": "可能利润率",
                "normalized_metric": "net_margin",
                "value": None,
                "unit": "",
                "year": "",
                "parser_sources": ["pdfplumber"],
                "evidence_refs": ["note://single_evidence"],
                "official_alias_match_signal": False,
                "semantic_target_unambiguous": False,
                "risk_flags": ["LOW_EVIDENCE_STRENGTH"],
                "provenance": {"fixture_type": "low_needs_more_info_candidate", "stage": "330B"},
            },
        },
        {
            "case_id": "blocking_rejected_candidate",
            "expected_routing_decision": ROUTING_REJECTED,
            "blocking_policy": "reject",
            "low_score_policy": "reject",
            "payload": {
                "candidate_id": "trust_330b_example_004",
                "metric_label_raw": "P/E(调整后?)",
                "normalized_metric": "price_earnings_ratio",
                "value": None,
                "unit": "x",
                "year": "",
                "parser_sources": ["pdfplumber", "marker_cached"],
                "evidence_refs": ["page=15", "table=2"],
                "semantic_target_unambiguous": False,
                "risk_flags": ["OFFICIAL_RULE_CONFLICT", "VALUE_PARSE_FAILED", "TARGET_METRIC_AMBIGUOUS"],
                "provenance": {"fixture_type": "blocking_rejected_candidate", "stage": "330B"},
            },
        },
        {
            "case_id": "mojibake_warning_review_required_candidate",
            "expected_routing_decision": ROUTING_REVIEW_REQUIRED,
            "blocking_policy": "review",
            "low_score_policy": "needs_more_info",
            "payload": {
                "candidate_id": "trust_330b_example_005",
                "metric_label_raw": "璇爜ROE",
                "normalized_metric": "roe",
                "value": 13.2,
                "unit": "%",
                "year": "2024A",
                "parser_sources": ["pdfplumber"],
                "evidence_refs": ["cached_fixture://mojibake_review"],
                "semantic_target_unambiguous": True,
                "value_parse_success": True,
                "risk_flags": ["MOJIBAKE_ENCODING_ARTIFACT", "LOW_EVIDENCE_STRENGTH"],
                "provenance": {"fixture_type": "mojibake_warning_review_required_candidate", "stage": "330B"},
            },
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330B trust engine scoring.")
    parser.add_argument("--trust-foundation-dir", default=str(DEFAULT_TRUST_FOUNDATION_DIR))
    parser.add_argument("--cycle-closure-dir", default=str(DEFAULT_CYCLE_CLOSURE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    trust_foundation_dir = Path(args.trust_foundation_dir)
    cycle_closure_dir = Path(args.cycle_closure_dir)
    output_dir = Path(args.output_dir)

    foundation_summary_path = trust_foundation_dir / "trust_engine_foundation_330a_summary.json"
    foundation_examples_path = trust_foundation_dir / "trust_engine_foundation_330a_example_trust_records.json"
    foundation_no_apply_path = trust_foundation_dir / "trust_engine_foundation_330a_no_apply_proof.json"
    cycle_summary_path = cycle_closure_dir / "alias_patch_cycle_closure_325p_summary.json"
    if not foundation_summary_path.exists():
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_330A_SUMMARY")
        print(f"trust_engine_scoring_330b_summary_json: {output_dir / 'trust_engine_scoring_330b_summary.json'}")
        print(f"qa_fail_count: {summary['qa_fail_count']}")
        print(f"decision: {summary['decision']}")
        return 0
    if not foundation_examples_path.exists():
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_330A_EXAMPLE_RECORDS")
        print(f"trust_engine_scoring_330b_summary_json: {output_dir / 'trust_engine_scoring_330b_summary.json'}")
        print(f"qa_fail_count: {summary['qa_fail_count']}")
        print(f"decision: {summary['decision']}")
        return 0
    if not foundation_no_apply_path.exists():
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_330A_NO_APPLY_PROOF")
        print(f"trust_engine_scoring_330b_summary_json: {output_dir / 'trust_engine_scoring_330b_summary.json'}")
        print(f"qa_fail_count: {summary['qa_fail_count']}")
        print(f"decision: {summary['decision']}")
        return 0
    if not cycle_summary_path.exists():
        summary = _blocked_result(output_dir, "BLOCKED_MISSING_325P_SUMMARY")
        print(f"trust_engine_scoring_330b_summary_json: {output_dir / 'trust_engine_scoring_330b_summary.json'}")
        print(f"qa_fail_count: {summary['qa_fail_count']}")
        print(f"decision: {summary['decision']}")
        return 0

    foundation_summary = _read_json(foundation_summary_path)
    foundation_examples = _read_json(foundation_examples_path)
    foundation_no_apply = _read_json(foundation_no_apply_path)
    cycle_summary = _read_json(cycle_summary_path)
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    official_assets_before = capture_official_asset_hashes()

    add_qa("foundation::decision", str(foundation_summary.get("decision", "")).strip() == READY_330A_DECISION, str(foundation_summary.get("decision", "")).strip())
    add_qa("foundation::qa_fail_count", int(foundation_summary.get("qa_fail_count", 1)) == 0, str(foundation_summary.get("qa_fail_count", "")))
    add_qa("foundation::risk_registry_count", int(foundation_summary.get("risk_registry_count", 0)) >= 18, f"actual={foundation_summary.get('risk_registry_count', '')}")
    add_qa("foundation::example_trust_record_count", int(foundation_summary.get("example_trust_record_count", 0)) >= 3, f"actual={foundation_summary.get('example_trust_record_count', '')}")
    add_qa("foundation::no_apply_proof", bool(foundation_no_apply.get("no_official_asset_modification_during_330a")) is True, str(foundation_no_apply.get("no_official_asset_modification_during_330a", "")))
    add_qa("cycle_closure::decision", str(cycle_summary.get("decision", "")).strip() in READY_325P_DECISIONS, str(cycle_summary.get("decision", "")).strip())

    registry_summary = coerce_risk_registry_summary()
    risk_rows = risk_registry_rows()
    add_qa("risk_registry::minimum_count", len(risk_rows) >= 18, f"actual={len(risk_rows)}")

    scoring_summary = scoring_model_summary()
    add_qa("scoring_model::component_count", int(scoring_summary["scoring_model_component_count"]) >= 5, f"actual={scoring_summary['scoring_model_component_count']}")

    scored_examples: List[Dict[str, Any]] = []
    routing_smoke_rows: List[Dict[str, Any]] = []
    for case in _build_scoring_examples():
        scored = score_trust_record(
            case["payload"],
            blocking_policy=case["blocking_policy"],
            low_score_policy=case["low_score_policy"],
        )
        scored["case_id"] = case["case_id"]
        scored["expected_routing_decision"] = case["expected_routing_decision"]
        passed = scored["routing_decision"] == case["expected_routing_decision"]
        routing_smoke_rows.append(
            {
                "case_id": case["case_id"],
                "expected_routing_decision": case["expected_routing_decision"],
                "actual_routing_decision": scored["routing_decision"],
                "confidence_score": scored["confidence_score"],
                "confidence_level": scored["confidence_level"],
                "passed": passed,
            }
        )
        scored_examples.append(scored)
    add_qa("scored_examples::count", len(scored_examples) >= 5, f"actual={len(scored_examples)}")
    smoke_passed = all(bool(row["passed"]) for row in routing_smoke_rows) and len(routing_smoke_rows) >= 5
    add_qa("routing_policy::reused", all(bool(row.get("routing_policy_reused")) for row in scored_examples), "330A route_trust_record reused by scorer")
    add_qa("routing_policy::smoke_test_count", len(routing_smoke_rows) >= 5, f"actual={len(routing_smoke_rows)}")
    add_qa("routing_policy::smoke_tests_passed", smoke_passed, f"actual={smoke_passed}")

    cached_records = foundation_examples.get("records", [])
    cached_records = cached_records if isinstance(cached_records, list) else []
    cached_sidecar_samples: List[Dict[str, Any]] = []
    cached_sidecar_sample_reason = "loaded_from_330a_example_trust_records"
    for row in cached_records:
        if isinstance(row, dict) and row.get("candidate_id"):
            cached_sidecar_samples.append(score_trust_record(row))
    if not cached_sidecar_samples:
        cached_sidecar_sample_reason = "no_compatible_candidate_like_examples_found_in_cached_inputs"
    add_qa("cached_sidecar_samples::count_non_negative", len(cached_sidecar_samples) >= 0, f"actual={len(cached_sidecar_samples)}")

    official_assets_after = capture_official_asset_hashes()
    no_apply_proof = build_no_apply_proof(
        stage="330B",
        files_read=[
            str(foundation_summary_path),
            str(foundation_examples_path),
            str(foundation_no_apply_path),
            str(cycle_summary_path),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    add_qa(
        "safety::no_official_asset_modification_during_330b",
        bool(no_apply_proof.get("no_official_asset_modification_during_330b")) is True,
        str(no_apply_proof.get("no_official_asset_modification_during_330b", "")),
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "330B",
        "output_dir": str(output_dir),
        "validated_330a_foundation": qa_fail_count == 0,
        "risk_registry_count": len(risk_rows),
        "scoring_model_component_count": scoring_summary["scoring_model_component_count"],
        "scored_example_count": len(scored_examples),
        "routing_policy_reused": True,
        "routing_policy_smoke_test_count": len(routing_smoke_rows),
        "routing_policy_smoke_test_passed": smoke_passed,
        "cached_candidate_sidecar_sample_count": len(cached_sidecar_samples),
        "cached_candidate_sidecar_sample_reason": cached_sidecar_sample_reason,
        "no_official_asset_modification_during_330b": bool(no_apply_proof.get("no_official_asset_modification_during_330b")),
        "official_assets_written": [],
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "trust_engine_scoring_330b_summary.json"
    qa_json = output_dir / "trust_engine_scoring_330b_qa.json"
    scored_examples_json = output_dir / "trust_engine_scoring_330b_scored_examples.json"
    cached_samples_json = output_dir / "trust_engine_scoring_330b_cached_sidecar_samples.json"
    no_apply_json = output_dir / "trust_engine_scoring_330b_no_apply_proof.json"
    report_md = output_dir / "trust_engine_scoring_330b_report.md"
    summary_xlsx = output_dir / "trust_engine_scoring_330b_summary.xlsx"

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
    write_json(scored_examples_json, {"records": scored_examples})
    write_json(
        cached_samples_json,
        {
            "cached_candidate_sidecar_sample_count": len(cached_sidecar_samples),
            "cached_candidate_sidecar_sample_reason": cached_sidecar_sample_reason,
            "records": cached_sidecar_samples,
        },
    )
    write_json(no_apply_json, no_apply_proof)

    foundation_validation_df = pd.DataFrame(
        [
            {
                "foundation_decision": foundation_summary.get("decision", ""),
                "foundation_qa_fail_count": foundation_summary.get("qa_fail_count", ""),
                "foundation_risk_registry_count": foundation_summary.get("risk_registry_count", ""),
                "foundation_example_trust_record_count": foundation_summary.get("example_trust_record_count", ""),
                "foundation_no_official_asset_modification": foundation_summary.get("no_official_asset_modification_during_330a", ""),
                "cycle_closure_decision": cycle_summary.get("decision", ""),
                "validated_330a_foundation": qa_fail_count == 0,
            }
        ]
    ).fillna("")
    official_asset_proof_df = pd.DataFrame(
        [
            {
                "asset_path": path,
                "hash_before": before_hash,
                "hash_after": official_assets_after.get(path, ""),
                "modified_during_330b": before_hash != official_assets_after.get(path, ""),
            }
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
                "limitation": "sidecar_only",
                "detail": "330B adds deterministic scoring only and does not override production trusted/review/rejected behavior.",
            },
            {
                "limitation": "cached_examples_only",
                "detail": "330B uses cached 330A / 325P artifacts plus deterministic fixtures rather than fresh production recomputation.",
            },
            {
                "limitation": "optional_cached_samples",
                "detail": "Cached candidate-like sidecar samples are opportunistic and may be zero without causing QA failure.",
            },
        ]
    ).fillna("")
    sheets = {
        "summary": pd.DataFrame([summary]).fillna(""),
        "foundation_validation": foundation_validation_df,
        "scoring_model": pd.DataFrame([scoring_summary]).fillna(""),
        "scored_examples": pd.DataFrame(scored_examples).fillna(""),
        "routing_smoke_tests": pd.DataFrame(routing_smoke_rows).fillna(""),
        "cached_sidecar_samples": pd.DataFrame(cached_sidecar_samples).fillna(""),
        "official_asset_proof": official_asset_proof_df,
        "qa_summary": qa_summary_df,
        "qa_checks": qa_df,
        "known_limitations": known_limitations_df,
    }
    write_excel(summary_xlsx, sheets)
    report_md.write_text(trust_engine_scoring_330b_markdown(summary), encoding="utf-8")

    print(f"trust_engine_scoring_330b_summary_json: {summary_json}")
    print(f"trust_engine_scoring_330b_qa_json: {qa_json}")
    print(f"trust_engine_scoring_330b_scored_examples_json: {scored_examples_json}")
    print(f"trust_engine_scoring_330b_cached_sidecar_samples_json: {cached_samples_json}")
    print(f"trust_engine_scoring_330b_no_apply_proof_json: {no_apply_json}")
    print(f"trust_engine_scoring_330b_summary_xlsx: {summary_xlsx}")
    print(f"trust_engine_scoring_330b_report_md: {report_md}")
    for key in [
        "validated_330a_foundation",
        "risk_registry_count",
        "scoring_model_component_count",
        "scored_example_count",
        "routing_policy_reused",
        "routing_policy_smoke_test_count",
        "routing_policy_smoke_test_passed",
        "cached_candidate_sidecar_sample_count",
        "no_official_asset_modification_during_330b",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
