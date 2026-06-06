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

from datefac.trust.cached_candidate_benchmark_330c import (  # noqa: E402
    DEFAULT_CANDIDATE_SOURCE_DIRS,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_TRUST_SCORING_DIR,
    NOT_READY_DECISION,
    build_cached_candidate_benchmark_330c,
)
from datefac.trust.cached_candidate_benchmark_330c_report import (  # noqa: E402
    CALIBRATION_SHEET_ORDER,
    SHEET_ORDER,
    cached_candidate_benchmark_330c_markdown,
    write_excel,
    write_json,
)
from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402


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
        "stage": "330C",
        "output_dir": str(output_dir),
        "validated_330b_scoring": False,
        "candidate_source_dir_count": 0,
        "cached_candidate_count": 0,
        "fallback_fixture_count": 0,
        "candidate_source_status": "blocked",
        "scored_record_count": 0,
        "confidence_level_distribution": {},
        "routing_decision_distribution": {},
        "risk_flag_distribution": {},
        "score_bucket_distribution": {},
        "calibration_sample_count": 0,
        "potential_false_trusted_count": 0,
        "trusted_with_warning_risk_count": 0,
        "trusted_with_low_evidence_count": 0,
        "review_required_high_score_count": 0,
        "rejected_or_needs_more_info_high_score_count": 0,
        "missing_evidence_count": 0,
        "no_official_asset_modification_during_330c": True,
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
    no_apply = {
        "stage": "330C",
        "official_assets_before": {},
        "official_assets_after": {},
        "official_assets_written": [],
        "no_official_asset_modification_during_330c": True,
    }
    write_json(output_dir / "cached_candidate_trust_scoring_330c_summary.json", summary)
    write_json(output_dir / "cached_candidate_trust_scoring_330c_qa.json", qa_json)
    write_json(output_dir / "cached_candidate_trust_scoring_330c_no_apply_proof.json", no_apply)
    write_json(output_dir / "cached_candidate_trust_scoring_330c_benchmark_records.jsonl", {"records": []})
    sheets = {
        "summary": pd.DataFrame([summary]),
        "source_artifacts": pd.DataFrame(),
        "scored_records": pd.DataFrame(),
        "confidence_distribution": pd.DataFrame(),
        "routing_distribution": pd.DataFrame(),
        "risk_distribution": pd.DataFrame(),
        "score_bucket_distribution": pd.DataFrame(),
        "existing_status_distribution": pd.DataFrame(),
        "sidecar_vs_existing_status": pd.DataFrame(),
        "calibration_summary": pd.DataFrame(),
        "official_asset_proof": pd.DataFrame(),
        "qa_summary": pd.DataFrame([{"qa_fail_count": 1, "decision": NOT_READY_DECISION}]),
        "qa_checks": pd.DataFrame(qa_json["checks"]),
        "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": code}]),
    }
    write_excel(output_dir / "cached_candidate_trust_scoring_330c_summary.xlsx", sheets, SHEET_ORDER)
    write_excel(output_dir / "cached_candidate_trust_scoring_330c_calibration_samples.xlsx", {"summary": pd.DataFrame()}, CALIBRATION_SHEET_ORDER)
    (output_dir / "cached_candidate_trust_scoring_330c_report.md").write_text(
        cached_candidate_benchmark_330c_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330C cached candidate trust scoring benchmark.")
    parser.add_argument("--trust-scoring-dir", default=str(DEFAULT_TRUST_SCORING_DIR))
    parser.add_argument(
        "--candidate-source-dir",
        action="append",
        default=[],
        help="Candidate source directory. Repeat for multiple dirs.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    trust_scoring_dir = Path(args.trust_scoring_dir)
    candidate_source_dirs = [Path(item) for item in args.candidate_source_dir] or list(DEFAULT_CANDIDATE_SOURCE_DIRS)
    output_dir = Path(args.output_dir)

    summary_path = trust_scoring_dir / "trust_engine_scoring_330b_summary.json"
    qa_path = trust_scoring_dir / "trust_engine_scoring_330b_qa.json"
    no_apply_path = trust_scoring_dir / "trust_engine_scoring_330b_no_apply_proof.json"
    for path, code in [
        (summary_path, "BLOCKED_MISSING_330B_SUMMARY"),
        (qa_path, "BLOCKED_MISSING_330B_QA"),
        (no_apply_path, "BLOCKED_MISSING_330B_NO_APPLY_PROOF"),
    ]:
        if not path.exists():
            summary = _blocked_result(output_dir, code)
            print(f"cached_candidate_trust_scoring_330c_summary_json: {output_dir / 'cached_candidate_trust_scoring_330c_summary.json'}")
            print(f"qa_fail_count: {summary['qa_fail_count']}")
            print(f"decision: {summary['decision']}")
            return 0

    artifacts = build_cached_candidate_benchmark_330c(
        trust_scoring_summary=_read_json(summary_path),
        trust_scoring_qa=_read_json(qa_path),
        trust_scoring_no_apply=_read_json(no_apply_path),
        candidate_source_dirs=candidate_source_dirs,
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "cached_candidate_trust_scoring_330c_summary.json"
    qa_json = output_dir / "cached_candidate_trust_scoring_330c_qa.json"
    benchmark_json = output_dir / "cached_candidate_trust_scoring_330c_benchmark.json"
    no_apply_json = output_dir / "cached_candidate_trust_scoring_330c_no_apply_proof.json"
    summary_xlsx = output_dir / "cached_candidate_trust_scoring_330c_summary.xlsx"
    calibration_xlsx = output_dir / "cached_candidate_trust_scoring_330c_calibration_samples.xlsx"
    report_md = output_dir / "cached_candidate_trust_scoring_330c_report.md"
    records_jsonl = output_dir / "cached_candidate_trust_scoring_330c_benchmark_records.jsonl"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(benchmark_json, artifacts["benchmark_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    sheets = {
        "summary": pd.DataFrame([artifacts["summary"]]).fillna(""),
        "source_artifacts": artifacts["artifact_inventory_df"],
        "scored_records": artifacts["scored_records_df"],
        "confidence_distribution": artifacts["confidence_distribution_df"],
        "routing_distribution": artifacts["routing_distribution_df"],
        "risk_distribution": artifacts["risk_distribution_df"],
        "score_bucket_distribution": artifacts["score_bucket_distribution_df"],
        "existing_status_distribution": artifacts["existing_status_distribution_df"],
        "sidecar_vs_existing_status": artifacts["sidecar_vs_existing_df"],
        "calibration_summary": artifacts["calibration_summary_df"],
        "official_asset_proof": artifacts["official_asset_proof_df"],
        "qa_summary": artifacts["qa_summary_df"],
        "qa_checks": artifacts["qa_checks_df"],
        "known_limitations": artifacts["known_limitations_df"],
    }
    write_excel(summary_xlsx, sheets, SHEET_ORDER)
    calibration_sheets = {
        "summary": artifacts["calibration_summary_df"],
        "potential_false_trusted": artifacts["calibration_sets"]["potential_false_trusted"],
        "trusted_with_warning": artifacts["calibration_sets"]["trusted_with_warning_risk"],
        "trusted_with_low_evidence": artifacts["calibration_sets"]["trusted_with_low_evidence"],
        "review_required_high_score": artifacts["calibration_sets"]["review_required_high_score"],
        "rejected_or_needs_more_info_high": artifacts["calibration_sets"]["rejected_or_needs_more_info_high_score"],
        "missing_evidence": artifacts["calibration_sets"]["missing_evidence"],
    }
    write_excel(calibration_xlsx, calibration_sheets, CALIBRATION_SHEET_ORDER)
    report_md.write_text(cached_candidate_benchmark_330c_markdown(artifacts["summary"]), encoding="utf-8")

    records_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with records_jsonl.open("w", encoding="utf-8") as handle:
        for row in artifacts["scored_records_df"].to_dict(orient="records"):
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    summary = artifacts["summary"]
    print(f"cached_candidate_trust_scoring_330c_summary_json: {summary_json}")
    print(f"cached_candidate_trust_scoring_330c_qa_json: {qa_json}")
    print(f"cached_candidate_trust_scoring_330c_benchmark_json: {benchmark_json}")
    print(f"cached_candidate_trust_scoring_330c_no_apply_proof_json: {no_apply_json}")
    print(f"cached_candidate_trust_scoring_330c_summary_xlsx: {summary_xlsx}")
    print(f"cached_candidate_trust_scoring_330c_calibration_samples_xlsx: {calibration_xlsx}")
    print(f"cached_candidate_trust_scoring_330c_report_md: {report_md}")
    print(f"cached_candidate_trust_scoring_330c_benchmark_records_jsonl: {records_jsonl}")
    for key in [
        "validated_330b_scoring",
        "candidate_source_dir_count",
        "cached_candidate_count",
        "fallback_fixture_count",
        "scored_record_count",
        "calibration_sample_count",
        "potential_false_trusted_count",
        "trusted_with_warning_risk_count",
        "missing_evidence_count",
        "no_official_asset_modification_during_330c",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
