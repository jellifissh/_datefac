from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.full_unfamiliar_export_benchmark_330h import (  # noqa: E402
    DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PREPARED_OUTPUT_DIR,
    DEFAULT_PREVIOUS_DELIVERY_REPORT_DIR,
    DEFAULT_TRUST_SCORING_DIR,
    DEFAULT_UNFAMILIAR_INPUT_DIR,
    build_full_unfamiliar_export_benchmark_330h,
)
from datefac.trust.full_unfamiliar_export_benchmark_330h_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    full_unfamiliar_export_benchmark_330h_markdown,
    write_excel,
    write_json,
)
from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330H full unfamiliar export benchmark.")
    parser.add_argument("--unfamiliar-input-dir", default=str(DEFAULT_UNFAMILIAR_INPUT_DIR))
    parser.add_argument("--previous-delivery-report-dir", default=str(DEFAULT_PREVIOUS_DELIVERY_REPORT_DIR))
    parser.add_argument("--prepared-output-dir", default=str(DEFAULT_PREPARED_OUTPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--rerun-330f", action="store_true")
    parser.add_argument("--deduped-candidate-benchmark-dir", default=str(DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR))
    parser.add_argument("--trust-scoring-dir", default=str(DEFAULT_TRUST_SCORING_DIR))
    args = parser.parse_args()

    unfamiliar_input_dir = Path(args.unfamiliar_input_dir)
    previous_delivery_report_dir = Path(args.previous_delivery_report_dir)
    prepared_output_dir = Path(args.prepared_output_dir)
    output_dir = Path(args.output_dir)
    deduped_candidate_benchmark_dir = Path(args.deduped_candidate_benchmark_dir)
    trust_scoring_dir = Path(args.trust_scoring_dir)

    artifacts = build_full_unfamiliar_export_benchmark_330h(
        unfamiliar_input_dir=unfamiliar_input_dir,
        previous_delivery_report_dir=previous_delivery_report_dir,
        prepared_output_dir=prepared_output_dir,
        output_dir=output_dir,
        deduped_candidate_benchmark_dir=deduped_candidate_benchmark_dir,
        trust_scoring_dir=trust_scoring_dir,
        rerun_330f=bool(args.rerun_330f),
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(previous_delivery_report_dir / "end_to_end_delivery_quality_report_330g_summary.json"),
            str(unfamiliar_input_dir),
            str(deduped_candidate_benchmark_dir / "deduped_candidate_trust_benchmark_330e_summary.json"),
            str(deduped_candidate_benchmark_dir / "deduped_candidate_trust_benchmark_330e_qa.json"),
            str(trust_scoring_dir / "trust_engine_scoring_330b_summary.json"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "full_unfamiliar_export_benchmark_330h_summary.json"
    qa_json = output_dir / "full_unfamiliar_export_benchmark_330h_qa.json"
    no_apply_json = output_dir / "full_unfamiliar_export_benchmark_330h_no_apply_proof.json"
    manifest_json = output_dir / "full_unfamiliar_export_benchmark_330h_manifest.json"
    summary_xlsx = output_dir / "full_unfamiliar_export_benchmark_330h_summary.xlsx"
    report_md = output_dir / "full_unfamiliar_export_benchmark_330h_report.md"

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
            "full_pdf_list": artifacts["pdf_list_df"],
            "per_pdf_summary": artifacts["per_pdf_df"],
            "prepared_manifest": artifacts["prepared_manifest_df"],
            "prepared_candidate_rows": artifacts["prepared_df"],
            "missing_field_counts": artifacts["missing_field_counts_df"],
            "rerun_330f_summary": artifacts["rerun_330f_summary_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(full_unfamiliar_export_benchmark_330h_markdown(artifacts["summary"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"full_unfamiliar_export_benchmark_330h_summary_json: {summary_json}")
    print(f"full_unfamiliar_export_benchmark_330h_qa_json: {qa_json}")
    print(f"full_unfamiliar_export_benchmark_330h_no_apply_proof_json: {no_apply_json}")
    print(f"full_unfamiliar_export_benchmark_330h_manifest_json: {manifest_json}")
    print(f"full_unfamiliar_export_benchmark_330h_summary_xlsx: {summary_xlsx}")
    print(f"full_unfamiliar_export_benchmark_330h_report_md: {report_md}")
    for key in [
        "validated_330g_delivery_report",
        "unfamiliar_pdf_count",
        "processed_pdf_count",
        "failed_pdf_count",
        "no_candidate_pdf_count",
        "pdf_with_candidate_count",
        "prepared_output_dir",
        "prepared_candidate_row_count",
        "source_pdf_preserved",
        "reran_330f",
        "330f_unfamiliar_source_status",
        "330f_scored_unfamiliar_record_count",
        "330f_decision",
        "recommended_next_step",
        "no_official_asset_modification_during_330h",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
