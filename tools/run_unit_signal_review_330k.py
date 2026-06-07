from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402
from datefac.trust.unit_signal_review_330k import (  # noqa: E402
    DEFAULT_DELIVERY_REPORT_REFRESH_DIR,
    DEFAULT_FIXED_PREPARED_DIR,
    DEFAULT_OPTIONAL_FIXED_PREPARED_OUTPUT_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SOURCE_ATTRIBUTION_UNIT_FIX_DIR,
    build_unit_signal_review_330k,
)
from datefac.trust.unit_signal_review_330k_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    unit_signal_review_330k_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330K unit signal review.")
    parser.add_argument(
        "--delivery-report-refresh-dir",
        default=str(DEFAULT_DELIVERY_REPORT_REFRESH_DIR),
    )
    parser.add_argument(
        "--source-attribution-unit-fix-dir",
        default=str(DEFAULT_SOURCE_ATTRIBUTION_UNIT_FIX_DIR),
    )
    parser.add_argument("--fixed-prepared-dir", default=str(DEFAULT_FIXED_PREPARED_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--optional-fixed-prepared-output-dir",
        default=str(DEFAULT_OPTIONAL_FIXED_PREPARED_OUTPUT_DIR),
    )
    args = parser.parse_args()

    delivery_report_refresh_dir = Path(args.delivery_report_refresh_dir)
    source_attribution_unit_fix_dir = Path(args.source_attribution_unit_fix_dir)
    fixed_prepared_dir = Path(args.fixed_prepared_dir)
    output_dir = Path(args.output_dir)
    optional_fixed_prepared_output_dir = Path(args.optional_fixed_prepared_output_dir)

    artifacts = build_unit_signal_review_330k(
        delivery_report_refresh_dir=delivery_report_refresh_dir,
        source_attribution_unit_fix_dir=source_attribution_unit_fix_dir,
        fixed_prepared_dir=fixed_prepared_dir,
        output_dir=output_dir,
        optional_fixed_prepared_output_dir=optional_fixed_prepared_output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(delivery_report_refresh_dir / "delivery_report_refresh_330j_summary.json"),
            str(source_attribution_unit_fix_dir / "source_attribution_unit_signal_fix_330i_summary.json"),
            str(fixed_prepared_dir / "unfamiliar_candidate_manifest.json"),
            str(fixed_prepared_dir / "unfamiliar_candidate_rows.jsonl"),
            str(
                Path(r"D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f_330j")
                / "unfamiliar_pdf_trust_benchmark_330f_scored_records.jsonl"
            ),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "unit_signal_review_330k_summary.json"
    qa_json = output_dir / "unit_signal_review_330k_qa.json"
    no_apply_json = output_dir / "unit_signal_review_330k_no_apply_proof.json"
    summary_xlsx = output_dir / "unit_signal_review_330k_summary.xlsx"
    report_md = output_dir / "unit_signal_review_330k_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "status_distribution": artifacts["status_distribution_df"],
            "category_distribution": artifacts["category_distribution_df"],
            "review_burden": artifacts["review_burden_df"],
            "review_candidates": artifacts["review_df"],
            "reviewed_rows": artifacts["reviewed_rows_df"],
            "fixed_manifest": artifacts["fixed_manifest_df"],
            "optional_fixed_manifest": artifacts["optional_fixed_manifest_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(
        unit_signal_review_330k_markdown(artifacts["summary"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"unit_signal_review_330k_summary_json: {summary_json}")
    print(f"unit_signal_review_330k_qa_json: {qa_json}")
    print(f"unit_signal_review_330k_no_apply_proof_json: {no_apply_json}")
    print(f"unit_signal_review_330k_summary_xlsx: {summary_xlsx}")
    print(f"unit_signal_review_330k_report_md: {report_md}")
    for key in [
        "validated_330j_delivery_refresh",
        "input_candidate_row_count",
        "unit_missing_count_input",
        "unit_conflict_count_input",
        "additional_safe_unit_fix_count",
        "unit_missing_count_after_330k",
        "review_sample_row_count",
        "human_review_workbook_generated",
        "unit_review_required_count",
        "recommended_next_step",
        "no_official_asset_modification_during_330k",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
