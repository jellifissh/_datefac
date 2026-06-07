from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402
from datefac.trust.source_attribution_unit_signal_fix_330i import (  # noqa: E402
    DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR,
    DEFAULT_FIXED_PREPARED_OUTPUT_DIR,
    DEFAULT_FULL_UNFAMILIAR_BENCHMARK_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PREPARED_UNFAMILIAR_DIR,
    DEFAULT_TRUST_SCORING_DIR,
    build_source_attribution_unit_signal_fix_330i,
)
from datefac.trust.source_attribution_unit_signal_fix_330i_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    source_attribution_unit_signal_fix_330i_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 330I source attribution and unit signal fix."
    )
    parser.add_argument(
        "--full-unfamiliar-benchmark-dir",
        default=str(DEFAULT_FULL_UNFAMILIAR_BENCHMARK_DIR),
    )
    parser.add_argument(
        "--prepared-unfamiliar-dir",
        default=str(DEFAULT_PREPARED_UNFAMILIAR_DIR),
    )
    parser.add_argument(
        "--fixed-prepared-output-dir",
        default=str(DEFAULT_FIXED_PREPARED_OUTPUT_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--rerun-330f", action="store_true")
    parser.add_argument(
        "--deduped-candidate-benchmark-dir",
        default=str(DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR),
    )
    parser.add_argument(
        "--trust-scoring-dir",
        default=str(DEFAULT_TRUST_SCORING_DIR),
    )
    args = parser.parse_args()

    full_unfamiliar_benchmark_dir = Path(args.full_unfamiliar_benchmark_dir)
    prepared_unfamiliar_dir = Path(args.prepared_unfamiliar_dir)
    fixed_prepared_output_dir = Path(args.fixed_prepared_output_dir)
    output_dir = Path(args.output_dir)
    deduped_candidate_benchmark_dir = Path(args.deduped_candidate_benchmark_dir)
    trust_scoring_dir = Path(args.trust_scoring_dir)

    artifacts = build_source_attribution_unit_signal_fix_330i(
        full_unfamiliar_benchmark_dir=full_unfamiliar_benchmark_dir,
        prepared_unfamiliar_dir=prepared_unfamiliar_dir,
        fixed_prepared_output_dir=fixed_prepared_output_dir,
        output_dir=output_dir,
        rerun_330f=bool(args.rerun_330f),
        deduped_candidate_benchmark_dir=deduped_candidate_benchmark_dir,
        trust_scoring_dir=trust_scoring_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(
                full_unfamiliar_benchmark_dir
                / "full_unfamiliar_export_benchmark_330h_summary.json"
            ),
            str(prepared_unfamiliar_dir / "unfamiliar_candidate_manifest.json"),
            str(prepared_unfamiliar_dir / "unfamiliar_candidate_rows.jsonl"),
            str(
                deduped_candidate_benchmark_dir
                / "deduped_candidate_trust_benchmark_330e_summary.json"
            ),
            str(
                deduped_candidate_benchmark_dir
                / "deduped_candidate_trust_benchmark_330e_qa.json"
            ),
            str(trust_scoring_dir / "trust_engine_scoring_330b_summary.json"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "source_attribution_unit_signal_fix_330i_summary.json"
    qa_json = output_dir / "source_attribution_unit_signal_fix_330i_qa.json"
    no_apply_json = output_dir / "source_attribution_unit_signal_fix_330i_no_apply_proof.json"
    manifest_json = output_dir / "source_attribution_unit_signal_fix_330i_manifest.json"
    summary_xlsx = output_dir / "source_attribution_unit_signal_fix_330i_summary.xlsx"
    report_md = output_dir / "source_attribution_unit_signal_fix_330i_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_json(manifest_json, artifacts["manifest_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "source_attribution": artifacts["source_attribution_df"],
            "unit_fix_summary": artifacts["unit_fix_summary_df"],
            "confidence_distribution": artifacts["confidence_distribution_df"],
            "risk_flag_updates": artifacts["risk_flag_update_df"],
            "prepared_manifest": artifacts["prepared_manifest_df"],
            "fixed_candidate_rows": artifacts["fixed_candidate_rows_df"],
            "rerun_330f_summary": artifacts["rerun_330f_summary_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(
        source_attribution_unit_signal_fix_330i_markdown(artifacts["summary"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"source_attribution_unit_signal_fix_330i_summary_json: {summary_json}")
    print(f"source_attribution_unit_signal_fix_330i_qa_json: {qa_json}")
    print(f"source_attribution_unit_signal_fix_330i_no_apply_proof_json: {no_apply_json}")
    print(f"source_attribution_unit_signal_fix_330i_manifest_json: {manifest_json}")
    print(f"source_attribution_unit_signal_fix_330i_summary_xlsx: {summary_xlsx}")
    print(f"source_attribution_unit_signal_fix_330i_report_md: {report_md}")
    for key in [
        "validated_330h_full_benchmark",
        "input_candidate_row_count",
        "output_candidate_row_count",
        "source_pdf_nonempty_count",
        "source_pdf_unique_count",
        "source_page_nonempty_count",
        "source_page_missing_count_after",
        "unit_missing_count_before",
        "unit_missing_count_after",
        "unit_filled_count",
        "unit_inference_high_confidence_count",
        "unit_inference_medium_confidence_count",
        "unit_inference_low_confidence_count",
        "unit_unknown_risk_added_count",
        "prepared_output_dir",
        "reran_330f",
        "330f_unfamiliar_source_status",
        "330f_scored_unfamiliar_record_count",
        "330f_decision",
        "no_official_asset_modification_during_330i",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
