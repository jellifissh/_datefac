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

from datefac.trust.deduped_candidate_benchmark_330e import (  # noqa: E402
    DEFAULT_CACHED_CANDIDATE_BENCHMARK_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_ROUTING_POLICY_CALIBRATION_DIR,
    DEFAULT_TRUST_SCORING_DIR,
    FALLBACK_SCORED_RECORDS_JSONL,
    NOT_READY_DECISION,
    PRIMARY_SCORED_RECORDS_JSONL,
    build_deduped_candidate_benchmark_330e,
)
from datefac.trust.deduped_candidate_benchmark_330e_report import (  # noqa: E402
    SAMPLES_SHEET_ORDER,
    SUMMARY_SHEET_ORDER,
    deduped_candidate_benchmark_330e_markdown,
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
        "stage": "330E",
        "output_dir": str(output_dir),
        "validated_330d_calibration": False,
        "artifact_row_benchmark_retained": True,
        "strict_deduped_benchmark_generated": False,
        "cross_artifact_deduped_benchmark_generated": False,
        "artifact_row_count": 0,
        "strict_deduped_candidate_count": 0,
        "cross_artifact_deduped_candidate_count": 0,
        "strict_duplicate_count": 0,
        "cross_artifact_duplicate_count": 0,
        "source_candidate_id_coverage_count": 0,
        "source_candidate_id_coverage_rate": 0.0,
        "candidate_id_coverage_count": 0,
        "candidate_id_coverage_rate": 0.0,
        "content_fingerprint_coverage_rate": 0.0,
        "dedup_reliability_level": "",
        "policy_calibration_safe_to_continue": False,
        "recommended_next_step": "",
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330e": True,
        "files_written_to_official_assets": [],
        "qa_pass_count": 0,
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
        "stage": "330E",
        "files_read": [],
        "official_assets_before": {},
        "official_assets_after": {},
        "official_assets_written": [],
        "no_official_asset_modification_during_330e": True,
    }
    write_json(output_dir / "deduped_candidate_trust_benchmark_330e_summary.json", summary)
    write_json(output_dir / "deduped_candidate_trust_benchmark_330e_qa.json", qa_json)
    write_json(output_dir / "deduped_candidate_trust_benchmark_330e_no_apply_proof.json", no_apply)
    write_excel(
        output_dir / "deduped_candidate_trust_benchmark_330e_summary.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "qa_summary": pd.DataFrame([{"qa_fail_count": 1, "decision": NOT_READY_DECISION}]),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
            "coverage": pd.DataFrame(),
            "comparison": pd.DataFrame(),
            "official_asset_proof": pd.DataFrame(),
            "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": code}]),
        },
        SUMMARY_SHEET_ORDER,
    )
    write_excel(
        output_dir / "deduped_candidate_trust_benchmark_330e_samples.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "artifact_row_view": pd.DataFrame(),
            "strict_deduped_view": pd.DataFrame(),
            "cross_artifact_deduped_view": pd.DataFrame(),
            "strict_duplicate_rows": pd.DataFrame(),
            "cross_artifact_duplicate_rows": pd.DataFrame(),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
        },
        SAMPLES_SHEET_ORDER,
    )
    (output_dir / "deduped_candidate_trust_benchmark_330e_report.md").write_text(
        deduped_candidate_benchmark_330e_markdown(summary),
        encoding="utf-8",
    )
    return summary


def _resolve_scored_records_path(cached_candidate_benchmark_dir: Path) -> Path:
    primary = cached_candidate_benchmark_dir / PRIMARY_SCORED_RECORDS_JSONL
    if primary.exists():
        return primary
    return cached_candidate_benchmark_dir / FALLBACK_SCORED_RECORDS_JSONL


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330E deduped candidate trust benchmark.")
    parser.add_argument("--cached-candidate-benchmark-dir", default=str(DEFAULT_CACHED_CANDIDATE_BENCHMARK_DIR))
    parser.add_argument("--routing-policy-calibration-dir", default=str(DEFAULT_ROUTING_POLICY_CALIBRATION_DIR))
    parser.add_argument("--trust-scoring-dir", default=str(DEFAULT_TRUST_SCORING_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    cached_candidate_benchmark_dir = Path(args.cached_candidate_benchmark_dir)
    routing_policy_calibration_dir = Path(args.routing_policy_calibration_dir)
    trust_scoring_dir = Path(args.trust_scoring_dir)
    output_dir = Path(args.output_dir)

    scored_records_path = _resolve_scored_records_path(cached_candidate_benchmark_dir)
    required_paths = [
        (cached_candidate_benchmark_dir / "cached_candidate_trust_scoring_330c_summary.json", "BLOCKED_MISSING_330C_SUMMARY"),
        (cached_candidate_benchmark_dir / "cached_candidate_trust_scoring_330c_qa.json", "BLOCKED_MISSING_330C_QA"),
        (routing_policy_calibration_dir / "routing_policy_calibration_330d_summary.json", "BLOCKED_MISSING_330D_SUMMARY"),
        (routing_policy_calibration_dir / "routing_policy_calibration_330d_qa.json", "BLOCKED_MISSING_330D_QA"),
        (trust_scoring_dir / "trust_engine_scoring_330b_summary.json", "BLOCKED_MISSING_330B_SUMMARY"),
        (scored_records_path, "BLOCKED_MISSING_330C_SCORED_RECORDS"),
    ]
    for path, code in required_paths:
        if not path.exists():
            summary = _blocked_result(output_dir, code)
            print(f"deduped_candidate_trust_benchmark_330e_summary_json: {output_dir / 'deduped_candidate_trust_benchmark_330e_summary.json'}")
            print(f"qa_fail_count: {summary['qa_fail_count']}")
            print(f"decision: {summary['decision']}")
            return 0

    cached_candidate_summary_path = cached_candidate_benchmark_dir / "cached_candidate_trust_scoring_330c_summary.json"
    cached_candidate_qa_path = cached_candidate_benchmark_dir / "cached_candidate_trust_scoring_330c_qa.json"
    routing_policy_summary_path = routing_policy_calibration_dir / "routing_policy_calibration_330d_summary.json"
    routing_policy_qa_path = routing_policy_calibration_dir / "routing_policy_calibration_330d_qa.json"
    trust_scoring_summary_path = trust_scoring_dir / "trust_engine_scoring_330b_summary.json"

    artifacts = build_deduped_candidate_benchmark_330e(
        cached_candidate_summary=_read_json(cached_candidate_summary_path),
        cached_candidate_qa=_read_json(cached_candidate_qa_path),
        routing_policy_summary=_read_json(routing_policy_summary_path),
        routing_policy_qa=_read_json(routing_policy_qa_path),
        trust_scoring_summary=_read_json(trust_scoring_summary_path),
        scored_records_df=_read_jsonl(scored_records_path),
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(cached_candidate_summary_path),
            str(cached_candidate_qa_path),
            str(routing_policy_summary_path),
            str(routing_policy_qa_path),
            str(trust_scoring_summary_path),
            str(scored_records_path),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "deduped_candidate_trust_benchmark_330e_summary.json"
    qa_json = output_dir / "deduped_candidate_trust_benchmark_330e_qa.json"
    no_apply_json = output_dir / "deduped_candidate_trust_benchmark_330e_no_apply_proof.json"
    summary_xlsx = output_dir / "deduped_candidate_trust_benchmark_330e_summary.xlsx"
    samples_xlsx = output_dir / "deduped_candidate_trust_benchmark_330e_samples.xlsx"
    report_md = output_dir / "deduped_candidate_trust_benchmark_330e_report.md"
    strict_jsonl = output_dir / "deduped_candidate_trust_benchmark_330e_strict_deduped_records.jsonl"
    cross_jsonl = output_dir / "deduped_candidate_trust_benchmark_330e_cross_artifact_deduped_records.jsonl"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "coverage": artifacts["coverage_df"],
            "comparison": artifacts["comparison_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    write_excel(
        samples_xlsx,
        {
            "summary": artifacts["summary_df"],
            "artifact_row_view": artifacts["artifact_row_view_df"],
            "strict_deduped_view": artifacts["strict_deduped_view_df"],
            "cross_artifact_deduped_view": artifacts["cross_artifact_deduped_view_df"],
            "strict_duplicate_rows": artifacts["strict_duplicate_rows_df"],
            "cross_artifact_duplicate_rows": artifacts["cross_artifact_duplicate_rows_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
        SAMPLES_SHEET_ORDER,
    )
    report_md.write_text(deduped_candidate_benchmark_330e_markdown(artifacts["summary"]), encoding="utf-8")

    for path, frame in [
        (strict_jsonl, artifacts["strict_deduped_view_df"]),
        (cross_jsonl, artifacts["cross_artifact_deduped_view_df"]),
    ]:
        with path.open("w", encoding="utf-8") as handle:
            for row in frame.to_dict(orient="records"):
                handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    summary = artifacts["summary"]
    print(f"deduped_candidate_trust_benchmark_330e_summary_json: {summary_json}")
    print(f"deduped_candidate_trust_benchmark_330e_qa_json: {qa_json}")
    print(f"deduped_candidate_trust_benchmark_330e_no_apply_proof_json: {no_apply_json}")
    print(f"deduped_candidate_trust_benchmark_330e_summary_xlsx: {summary_xlsx}")
    print(f"deduped_candidate_trust_benchmark_330e_samples_xlsx: {samples_xlsx}")
    print(f"deduped_candidate_trust_benchmark_330e_report_md: {report_md}")
    print(f"deduped_candidate_trust_benchmark_330e_strict_deduped_records_jsonl: {strict_jsonl}")
    print(f"deduped_candidate_trust_benchmark_330e_cross_artifact_deduped_records_jsonl: {cross_jsonl}")
    for key in [
        "validated_330d_calibration",
        "artifact_row_count",
        "strict_deduped_candidate_count",
        "cross_artifact_deduped_candidate_count",
        "strict_duplicate_count",
        "cross_artifact_duplicate_count",
        "source_candidate_id_coverage_rate",
        "candidate_id_coverage_rate",
        "content_fingerprint_coverage_rate",
        "dedup_reliability_level",
        "artifact_row_benchmark_retained",
        "strict_deduped_benchmark_generated",
        "cross_artifact_deduped_benchmark_generated",
        "policy_calibration_safe_to_continue",
        "no_official_asset_modification_during_330e",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
