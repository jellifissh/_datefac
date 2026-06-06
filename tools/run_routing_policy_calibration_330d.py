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

from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402
from datefac.trust.routing_policy_calibration_330d import (  # noqa: E402
    BENCHMARK_RECORDS_JSONL,
    DEFAULT_CACHED_CANDIDATE_BENCHMARK_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_TRUST_FOUNDATION_DIR,
    DEFAULT_TRUST_SCORING_DIR,
    NOT_READY_DECISION,
    build_routing_policy_calibration_330d,
)
from datefac.trust.routing_policy_calibration_330d_report import (  # noqa: E402
    SAMPLES_SHEET_ORDER,
    SUMMARY_SHEET_ORDER,
    routing_policy_calibration_330d_markdown,
    write_excel,
    write_json,
)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_jsonl(path: Path) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
            except Exception:
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
    return pd.DataFrame(rows)


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "330D",
        "output_dir": str(output_dir),
        "validated_330c_benchmark": False,
        "artifact_row_benchmark": True,
        "deduped_candidate_benchmark": False,
        "scored_record_count": 0,
        "artifact_row_count": 0,
        "deduped_candidate_count": 0,
        "duplicate_artifact_row_count": 0,
        "potential_false_trusted_count": 0,
        "target_metric_ambiguous_count": 0,
        "policy_proposal_generated": False,
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330d": True,
        "files_written_to_official_assets": [],
        "qa_pass_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "decision_warning": "",
        "decision": NOT_READY_DECISION,
    }
    qa_json = {
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "blocking_reasons": [code],
        "checks": [{"check_name": "blocked_input", "status": "FAIL", "detail": code}],
    }
    no_apply = {
        "stage": "330D",
        "files_read": [],
        "official_assets_before": {},
        "official_assets_after": {},
        "official_assets_written": [],
        "no_official_asset_modification_during_330d": True,
    }
    policy_proposal = {
        "policy_stage": "330D",
        "policy_proposal_generated": False,
        "production_apply_allowed": False,
    }

    write_json(output_dir / "routing_policy_calibration_330d_summary.json", summary)
    write_json(output_dir / "routing_policy_calibration_330d_qa.json", qa_json)
    write_json(output_dir / "routing_policy_calibration_330d_no_apply_proof.json", no_apply)
    write_json(output_dir / "routing_policy_calibration_330d_policy_proposal.json", policy_proposal)
    write_excel(
        output_dir / "routing_policy_calibration_330d_summary.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "qa_summary": pd.DataFrame([{"qa_fail_count": 1, "decision": NOT_READY_DECISION}]),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
            "policy_preview": pd.DataFrame([policy_proposal]),
            "dedupe_summary": pd.DataFrame(),
            "potential_false_trusted_distribution": pd.DataFrame(),
            "target_metric_ambiguous_distribution": pd.DataFrame(),
            "official_asset_proof": pd.DataFrame(),
            "risk_registry": pd.DataFrame(),
            "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": code}]),
        },
        SUMMARY_SHEET_ORDER,
    )
    write_excel(
        output_dir / "routing_policy_calibration_330d_samples.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "potential_false_trusted": pd.DataFrame(),
            "target_metric_ambiguous": pd.DataFrame(),
            "candidate_identity_duplicates": pd.DataFrame(),
            "row_fingerprint_duplicates": pd.DataFrame(),
            "policy_preview": pd.DataFrame([policy_proposal]),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
        },
        SAMPLES_SHEET_ORDER,
    )
    (output_dir / "routing_policy_calibration_330d_report.md").write_text(
        routing_policy_calibration_330d_markdown(summary, policy_proposal),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330D routing policy calibration.")
    parser.add_argument("--cached-candidate-benchmark-dir", default=str(DEFAULT_CACHED_CANDIDATE_BENCHMARK_DIR))
    parser.add_argument("--trust-scoring-dir", default=str(DEFAULT_TRUST_SCORING_DIR))
    parser.add_argument("--trust-foundation-dir", default=str(DEFAULT_TRUST_FOUNDATION_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    cached_candidate_benchmark_dir = Path(args.cached_candidate_benchmark_dir)
    trust_scoring_dir = Path(args.trust_scoring_dir)
    trust_foundation_dir = Path(args.trust_foundation_dir)
    output_dir = Path(args.output_dir)

    required_paths = [
        (cached_candidate_benchmark_dir / "cached_candidate_trust_scoring_330c_summary.json", "BLOCKED_MISSING_330C_SUMMARY"),
        (cached_candidate_benchmark_dir / "cached_candidate_trust_scoring_330c_qa.json", "BLOCKED_MISSING_330C_QA"),
        (cached_candidate_benchmark_dir / "cached_candidate_trust_scoring_330c_no_apply_proof.json", "BLOCKED_MISSING_330C_NO_APPLY_PROOF"),
        (cached_candidate_benchmark_dir / BENCHMARK_RECORDS_JSONL, "BLOCKED_MISSING_330C_BENCHMARK_RECORDS"),
        (trust_scoring_dir / "trust_engine_scoring_330b_summary.json", "BLOCKED_MISSING_330B_SUMMARY"),
        (trust_foundation_dir / "trust_engine_foundation_330a_summary.json", "BLOCKED_MISSING_330A_SUMMARY"),
    ]
    for path, code in required_paths:
        if not path.exists():
            summary = _blocked_result(output_dir, code)
            print(f"routing_policy_calibration_330d_summary_json: {output_dir / 'routing_policy_calibration_330d_summary.json'}")
            print(f"qa_fail_count: {summary['qa_fail_count']}")
            print(f"decision: {summary['decision']}")
            return 0

    cached_candidate_summary_path = cached_candidate_benchmark_dir / "cached_candidate_trust_scoring_330c_summary.json"
    cached_candidate_qa_path = cached_candidate_benchmark_dir / "cached_candidate_trust_scoring_330c_qa.json"
    cached_candidate_no_apply_path = cached_candidate_benchmark_dir / "cached_candidate_trust_scoring_330c_no_apply_proof.json"
    benchmark_records_path = cached_candidate_benchmark_dir / BENCHMARK_RECORDS_JSONL
    trust_scoring_summary_path = trust_scoring_dir / "trust_engine_scoring_330b_summary.json"
    trust_foundation_summary_path = trust_foundation_dir / "trust_engine_foundation_330a_summary.json"

    artifacts = build_routing_policy_calibration_330d(
        cached_candidate_summary=_read_json(cached_candidate_summary_path),
        cached_candidate_qa=_read_json(cached_candidate_qa_path),
        cached_candidate_no_apply=_read_json(cached_candidate_no_apply_path),
        trust_scoring_summary=_read_json(trust_scoring_summary_path),
        trust_foundation_summary=_read_json(trust_foundation_summary_path),
        scored_records_df=_read_jsonl(benchmark_records_path),
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(cached_candidate_summary_path),
            str(cached_candidate_qa_path),
            str(cached_candidate_no_apply_path),
            str(benchmark_records_path),
            str(trust_scoring_summary_path),
            str(trust_foundation_summary_path),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "routing_policy_calibration_330d_summary.json"
    qa_json = output_dir / "routing_policy_calibration_330d_qa.json"
    no_apply_json = output_dir / "routing_policy_calibration_330d_no_apply_proof.json"
    policy_json = output_dir / "routing_policy_calibration_330d_policy_proposal.json"
    summary_xlsx = output_dir / "routing_policy_calibration_330d_summary.xlsx"
    samples_xlsx = output_dir / "routing_policy_calibration_330d_samples.xlsx"
    report_md = output_dir / "routing_policy_calibration_330d_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_json(policy_json, artifacts["policy_proposal_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "policy_preview": artifacts["policy_preview_df"],
            "dedupe_summary": artifacts["dedupe_summary_df"],
            "potential_false_trusted_distribution": artifacts["potential_false_trusted_distribution_df"],
            "target_metric_ambiguous_distribution": artifacts["target_metric_ambiguous_distribution_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
            "risk_registry": artifacts["risk_registry_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    write_excel(
        samples_xlsx,
        {
            "summary": artifacts["summary_df"],
            "potential_false_trusted": artifacts["potential_false_trusted_df"],
            "target_metric_ambiguous": artifacts["target_metric_ambiguous_df"],
            "candidate_identity_duplicates": artifacts["candidate_identity_duplicates_df"],
            "row_fingerprint_duplicates": artifacts["row_fingerprint_duplicates_df"],
            "policy_preview": artifacts["policy_preview_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
        SAMPLES_SHEET_ORDER,
    )
    report_md.write_text(
        routing_policy_calibration_330d_markdown(artifacts["summary"], artifacts["policy_proposal_json"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"routing_policy_calibration_330d_summary_json: {summary_json}")
    print(f"routing_policy_calibration_330d_qa_json: {qa_json}")
    print(f"routing_policy_calibration_330d_no_apply_proof_json: {no_apply_json}")
    print(f"routing_policy_calibration_330d_policy_proposal_json: {policy_json}")
    print(f"routing_policy_calibration_330d_summary_xlsx: {summary_xlsx}")
    print(f"routing_policy_calibration_330d_samples_xlsx: {samples_xlsx}")
    print(f"routing_policy_calibration_330d_report_md: {report_md}")
    for key in [
        "validated_330c_benchmark",
        "artifact_row_benchmark",
        "deduped_candidate_benchmark",
        "scored_record_count",
        "artifact_row_count",
        "deduped_candidate_count",
        "duplicate_artifact_row_count",
        "potential_false_trusted_count",
        "target_metric_ambiguous_count",
        "policy_proposal_generated",
        "production_routing_modified",
        "official_assets_modified",
        "no_official_asset_modification_during_330d",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
