from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.client_style_export_preview_330l import (  # noqa: E402
    DEFAULT_DELIVERY_REPORT_REFRESH_DIR,
    DEFAULT_FIXED_PREPARED_DIR,
    DEFAULT_OPTIONAL_RERUN_330F_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_UNIT_SIGNAL_REVIEW_DIR,
    build_client_style_export_preview_330l,
)
from datefac.trust.client_style_export_preview_330l_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    client_style_export_preview_330l_markdown,
    write_excel,
    write_json,
)
from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330L client-style export preview.")
    parser.add_argument(
        "--delivery-report-refresh-dir",
        default=str(DEFAULT_DELIVERY_REPORT_REFRESH_DIR),
    )
    parser.add_argument("--fixed-prepared-dir", default=str(DEFAULT_FIXED_PREPARED_DIR))
    parser.add_argument(
        "--unit-signal-review-dir",
        default=str(DEFAULT_UNIT_SIGNAL_REVIEW_DIR),
    )
    parser.add_argument(
        "--optional-rerun-330f-dir",
        default=str(DEFAULT_OPTIONAL_RERUN_330F_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    delivery_report_refresh_dir = Path(args.delivery_report_refresh_dir)
    fixed_prepared_dir = Path(args.fixed_prepared_dir)
    unit_signal_review_dir = Path(args.unit_signal_review_dir)
    optional_rerun_330f_dir = Path(args.optional_rerun_330f_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_client_style_export_preview_330l(
        delivery_report_refresh_dir=delivery_report_refresh_dir,
        fixed_prepared_dir=fixed_prepared_dir,
        unit_signal_review_dir=unit_signal_review_dir,
        optional_rerun_330f_dir=optional_rerun_330f_dir,
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(
                delivery_report_refresh_dir
                / "delivery_report_refresh_after_330k_330j2_summary.json"
            ),
            str(fixed_prepared_dir / "unfamiliar_candidate_rows.jsonl"),
            str(unit_signal_review_dir / "unit_signal_review_330k_summary.json"),
            str(unit_signal_review_dir / "unit_signal_review_330k_workbook.xlsx"),
            str(
                optional_rerun_330f_dir
                / "unfamiliar_pdf_trust_benchmark_330f_scored_records.jsonl"
            ),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "client_style_export_preview_330l_summary.json"
    qa_json = output_dir / "client_style_export_preview_330l_qa.json"
    no_apply_json = output_dir / "client_style_export_preview_330l_no_apply_proof.json"
    summary_xlsx = output_dir / "client_style_export_preview_330l_summary.xlsx"
    report_md = output_dir / "client_style_export_preview_330l_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "readme": artifacts["readme_df"],
            "exec_summary": artifacts["exec_summary_df"],
            "trusted_suggestions": artifacts["trusted_sheet_df"],
            "review_required": artifacts["review_required_df"],
            "unit_review_sample": artifacts["unit_review_sample_df"],
            "source_provenance": artifacts["source_provenance_df"],
            "qa_caveats": artifacts["qa_caveats_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(
        client_style_export_preview_330l_markdown(artifacts["summary"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"client_style_export_preview_330l_summary_json: {summary_json}")
    print(f"client_style_export_preview_330l_qa_json: {qa_json}")
    print(f"client_style_export_preview_330l_no_apply_proof_json: {no_apply_json}")
    print(f"client_style_export_preview_330l_summary_xlsx: {summary_xlsx}")
    print(f"client_style_export_preview_330l_report_md: {report_md}")
    print(f"client_style_export_preview_330l_preview_xlsx: {summary.get('preview_workbook_path', '')}")
    for key in [
        "validated_330j2_delivery_refresh",
        "preview_workbook_generated",
        "source_pdf_unique_count",
        "prepared_candidate_row_count",
        "strict_deduped_candidate_count",
        "unit_missing_count",
        "trusted_sheet_row_count",
        "review_required_sheet_row_count",
        "unit_review_sheet_row_count",
        "source_provenance_sheet_row_count",
        "qa_caveat_count",
        "delivery_readiness_judgment",
        "recommended_next_step",
        "no_official_asset_modification_during_330l",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
