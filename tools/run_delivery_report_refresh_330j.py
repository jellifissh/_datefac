from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.delivery_report_refresh_330j import (  # noqa: E402
    DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR,
    DEFAULT_FIXED_PREPARED_DIR,
    DEFAULT_FULL_UNFAMILIAR_BENCHMARK_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PREVIOUS_DELIVERY_REPORT_DIR,
    DEFAULT_RERUN_330F_OUTPUT_DIR,
    DEFAULT_SOURCE_ATTRIBUTION_UNIT_FIX_DIR,
    DEFAULT_TRUST_SCORING_DIR,
    build_delivery_report_refresh_330j,
)
from datefac.trust.delivery_report_refresh_330j_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    delivery_report_refresh_330j_markdown,
    write_excel,
    write_json,
)
from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330J delivery report refresh.")
    parser.add_argument(
        "--source-attribution-unit-fix-dir",
        default=str(DEFAULT_SOURCE_ATTRIBUTION_UNIT_FIX_DIR),
    )
    parser.add_argument("--fixed-prepared-dir", default=str(DEFAULT_FIXED_PREPARED_DIR))
    parser.add_argument(
        "--previous-delivery-report-dir",
        default=str(DEFAULT_PREVIOUS_DELIVERY_REPORT_DIR),
    )
    parser.add_argument(
        "--full-unfamiliar-benchmark-dir",
        default=str(DEFAULT_FULL_UNFAMILIAR_BENCHMARK_DIR),
    )
    parser.add_argument(
        "--deduped-candidate-benchmark-dir",
        default=str(DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR),
    )
    parser.add_argument(
        "--trust-scoring-dir",
        default=str(DEFAULT_TRUST_SCORING_DIR),
    )
    parser.add_argument("--rerun-330f", action="store_true")
    parser.add_argument(
        "--rerun-330f-output-dir",
        default=str(DEFAULT_RERUN_330F_OUTPUT_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    source_attribution_unit_fix_dir = Path(args.source_attribution_unit_fix_dir)
    fixed_prepared_dir = Path(args.fixed_prepared_dir)
    previous_delivery_report_dir = Path(args.previous_delivery_report_dir)
    full_unfamiliar_benchmark_dir = Path(args.full_unfamiliar_benchmark_dir)
    deduped_candidate_benchmark_dir = Path(args.deduped_candidate_benchmark_dir)
    trust_scoring_dir = Path(args.trust_scoring_dir)
    rerun_330f_output_dir = Path(args.rerun_330f_output_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_delivery_report_refresh_330j(
        source_attribution_unit_fix_dir=source_attribution_unit_fix_dir,
        fixed_prepared_dir=fixed_prepared_dir,
        previous_delivery_report_dir=previous_delivery_report_dir,
        full_unfamiliar_benchmark_dir=full_unfamiliar_benchmark_dir,
        deduped_candidate_benchmark_dir=deduped_candidate_benchmark_dir,
        trust_scoring_dir=trust_scoring_dir,
        rerun_330f=bool(args.rerun_330f),
        output_dir=output_dir,
        rerun_330f_output_dir=rerun_330f_output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(
                source_attribution_unit_fix_dir
                / "source_attribution_unit_signal_fix_330i_summary.json"
            ),
            str(fixed_prepared_dir / "unfamiliar_candidate_manifest.json"),
            str(fixed_prepared_dir / "unfamiliar_candidate_rows.jsonl"),
            str(
                previous_delivery_report_dir
                / "end_to_end_delivery_quality_report_330g_summary.json"
            ),
            str(
                full_unfamiliar_benchmark_dir
                / "full_unfamiliar_export_benchmark_330h_summary.json"
            ),
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
    summary_json = output_dir / "delivery_report_refresh_330j_summary.json"
    qa_json = output_dir / "delivery_report_refresh_330j_qa.json"
    no_apply_json = output_dir / "delivery_report_refresh_330j_no_apply_proof.json"
    summary_xlsx = output_dir / "delivery_report_refresh_330j_summary.xlsx"
    report_md = output_dir / "delivery_report_refresh_330j_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "refreshed_metrics": artifacts["refreshed_metrics_df"],
            "comparison": artifacts["comparison_df"],
            "risk_flag_delta": artifacts["risk_flag_delta_df"],
            "distribution": artifacts["distribution_df"],
            "rerun_330f_summary": artifacts["rerun_330f_summary_df"],
            "fixed_manifest": artifacts["fixed_manifest_df"],
            "fixed_candidate_rows": artifacts["fixed_candidate_rows_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(
        delivery_report_refresh_330j_markdown(artifacts["summary"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"delivery_report_refresh_330j_summary_json: {summary_json}")
    print(f"delivery_report_refresh_330j_qa_json: {qa_json}")
    print(f"delivery_report_refresh_330j_no_apply_proof_json: {no_apply_json}")
    print(f"delivery_report_refresh_330j_summary_xlsx: {summary_xlsx}")
    print(f"delivery_report_refresh_330j_report_md: {report_md}")
    for key in [
        "validated_330i_unit_fix",
        "reran_330f",
        "330f_unfamiliar_source_status",
        "processed_pdf_count",
        "source_pdf_unique_count",
        "prepared_candidate_row_count",
        "artifact_row_count",
        "strict_deduped_candidate_count",
        "sidecar_trusted_suggestion_count",
        "sidecar_review_required_suggestion_count",
        "unit_missing_count",
        "source_page_missing_count",
        "delivery_readiness_judgment",
        "recommended_next_step",
        "no_official_asset_modification_during_330j",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
