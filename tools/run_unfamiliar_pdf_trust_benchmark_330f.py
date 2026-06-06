from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402
from datefac.trust.unfamiliar_pdf_trust_benchmark_330f import (  # noqa: E402
    DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_TRUST_SCORING_DIR,
    DEFAULT_UNFAMILIAR_SOURCE_DIRS,
    NOT_READY_DECISION,
    build_unfamiliar_pdf_trust_benchmark_330f,
)
from datefac.trust.unfamiliar_pdf_trust_benchmark_330f_report import (  # noqa: E402
    SAMPLES_SHEET_ORDER,
    SUMMARY_SHEET_ORDER,
    unfamiliar_pdf_trust_benchmark_330f_markdown,
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


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "330F",
        "output_dir": str(output_dir),
        "validated_330e_benchmark": False,
        "unfamiliar_source_status": "blocked",
        "unfamiliar_source_dir_count": 0,
        "unfamiliar_candidate_artifact_row_count": 0,
        "unfamiliar_strict_deduped_candidate_count": 0,
        "unfamiliar_cross_artifact_deduped_candidate_count": 0,
        "scored_unfamiliar_record_count": 0,
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330f": True,
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
        "stage": "330F",
        "files_read": [],
        "official_assets_before": {},
        "official_assets_after": {},
        "official_assets_written": [],
        "no_official_asset_modification_during_330f": True,
    }
    write_json(output_dir / "unfamiliar_pdf_trust_benchmark_330f_summary.json", summary)
    write_json(output_dir / "unfamiliar_pdf_trust_benchmark_330f_qa.json", qa_json)
    write_json(output_dir / "unfamiliar_pdf_trust_benchmark_330f_no_apply_proof.json", no_apply)
    write_excel(
        output_dir / "unfamiliar_pdf_trust_benchmark_330f_summary.xlsx",
        {
            "summary": pd.DataFrame([summary]),
            "qa_summary": pd.DataFrame([{"qa_fail_count": 1, "decision": NOT_READY_DECISION}]),
            "qa_checks": pd.DataFrame(qa_json["checks"]),
            "source_inventory": pd.DataFrame(),
            "coverage": pd.DataFrame(),
            "distribution": pd.DataFrame(),
            "delivery_summary": pd.DataFrame(),
            "official_asset_proof": pd.DataFrame(),
            "known_limitations": pd.DataFrame([{"limitation": "blocked_input", "detail": code}]),
        },
        SUMMARY_SHEET_ORDER,
    )
    write_excel(
        output_dir / "unfamiliar_pdf_trust_benchmark_330f_samples.xlsx",
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
    (output_dir / "unfamiliar_pdf_trust_benchmark_330f_report.md").write_text(
        unfamiliar_pdf_trust_benchmark_330f_markdown(summary),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330F unfamiliar PDF trust benchmark.")
    parser.add_argument("--deduped-candidate-benchmark-dir", default=str(DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR))
    parser.add_argument("--trust-scoring-dir", default=str(DEFAULT_TRUST_SCORING_DIR))
    parser.add_argument("--unfamiliar-source-dir", action="append", default=[])
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    deduped_candidate_benchmark_dir = Path(args.deduped_candidate_benchmark_dir)
    trust_scoring_dir = Path(args.trust_scoring_dir)
    unfamiliar_source_dirs = [Path(item) for item in args.unfamiliar_source_dir] or list(DEFAULT_UNFAMILIAR_SOURCE_DIRS)
    output_dir = Path(args.output_dir)

    required_paths = [
        (deduped_candidate_benchmark_dir / "deduped_candidate_trust_benchmark_330e_summary.json", "BLOCKED_MISSING_330E_SUMMARY"),
        (deduped_candidate_benchmark_dir / "deduped_candidate_trust_benchmark_330e_qa.json", "BLOCKED_MISSING_330E_QA"),
        (trust_scoring_dir / "trust_engine_scoring_330b_summary.json", "BLOCKED_MISSING_330B_SUMMARY"),
    ]
    for path, code in required_paths:
        if not path.exists():
            summary = _blocked_result(output_dir, code)
            print(f"unfamiliar_pdf_trust_benchmark_330f_summary_json: {output_dir / 'unfamiliar_pdf_trust_benchmark_330f_summary.json'}")
            print(f"qa_fail_count: {summary['qa_fail_count']}")
            print(f"decision: {summary['decision']}")
            return 0

    deduped_candidate_summary_path = deduped_candidate_benchmark_dir / "deduped_candidate_trust_benchmark_330e_summary.json"
    deduped_candidate_qa_path = deduped_candidate_benchmark_dir / "deduped_candidate_trust_benchmark_330e_qa.json"
    trust_scoring_summary_path = trust_scoring_dir / "trust_engine_scoring_330b_summary.json"

    artifacts = build_unfamiliar_pdf_trust_benchmark_330f(
        deduped_candidate_summary=_read_json(deduped_candidate_summary_path),
        deduped_candidate_qa=_read_json(deduped_candidate_qa_path),
        trust_scoring_summary=_read_json(trust_scoring_summary_path),
        unfamiliar_source_dirs=unfamiliar_source_dirs,
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(deduped_candidate_summary_path),
            str(deduped_candidate_qa_path),
            str(trust_scoring_summary_path),
            *[str(path) for path in unfamiliar_source_dirs],
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "unfamiliar_pdf_trust_benchmark_330f_summary.json"
    qa_json = output_dir / "unfamiliar_pdf_trust_benchmark_330f_qa.json"
    no_apply_json = output_dir / "unfamiliar_pdf_trust_benchmark_330f_no_apply_proof.json"
    summary_xlsx = output_dir / "unfamiliar_pdf_trust_benchmark_330f_summary.xlsx"
    samples_xlsx = output_dir / "unfamiliar_pdf_trust_benchmark_330f_samples.xlsx"
    report_md = output_dir / "unfamiliar_pdf_trust_benchmark_330f_report.md"
    scored_jsonl = output_dir / "unfamiliar_pdf_trust_benchmark_330f_scored_records.jsonl"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "source_inventory": artifacts["source_inventory_df"],
            "coverage": artifacts["coverage_df"],
            "distribution": artifacts["distribution_df"],
            "delivery_summary": artifacts["delivery_summary_df"],
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
    report_md.write_text(unfamiliar_pdf_trust_benchmark_330f_markdown(artifacts["summary"]), encoding="utf-8")

    with scored_jsonl.open("w", encoding="utf-8") as handle:
        for row in artifacts["artifact_row_view_df"].to_dict(orient="records"):
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    summary = artifacts["summary"]
    print(f"unfamiliar_pdf_trust_benchmark_330f_summary_json: {summary_json}")
    print(f"unfamiliar_pdf_trust_benchmark_330f_qa_json: {qa_json}")
    print(f"unfamiliar_pdf_trust_benchmark_330f_no_apply_proof_json: {no_apply_json}")
    print(f"unfamiliar_pdf_trust_benchmark_330f_summary_xlsx: {summary_xlsx}")
    print(f"unfamiliar_pdf_trust_benchmark_330f_samples_xlsx: {samples_xlsx}")
    print(f"unfamiliar_pdf_trust_benchmark_330f_report_md: {report_md}")
    print(f"unfamiliar_pdf_trust_benchmark_330f_scored_records_jsonl: {scored_jsonl}")
    for key in [
        "validated_330e_benchmark",
        "unfamiliar_source_status",
        "unfamiliar_source_dir_count",
        "unfamiliar_candidate_artifact_row_count",
        "scored_unfamiliar_record_count",
        "potential_false_trusted_count",
        "sidecar_trusted_suggestion_count",
        "sidecar_review_required_suggestion_count",
        "estimated_auto_trusted_ratio",
        "no_official_asset_modification_during_330f",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
