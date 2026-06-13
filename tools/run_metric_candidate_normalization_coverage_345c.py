from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.metric_candidate_normalization_coverage_345c import (  # noqa: E402
    ALIAS_CANDIDATE_QUEUE_CSV_FILE_NAME,
    ALIAS_CANDIDATE_QUEUE_JSON_FILE_NAME,
    ARTIFACT_INDEX_FILE_NAME,
    DEFAULT_FULL_EXTRACTION_QUALITY_AUDIT_345B_DIR,
    DEFAULT_FULL_STRUCTURED_DATA_INVENTORY_345A_DIR,
    DEFAULT_OUTPUT_DIR,
    EXECUTIVE_SUMMARY_FILE_NAME,
    MANIFEST_FILE_NAME,
    METRIC_ROW_FIELDS,
    METRIC_ROWS_CSV_FILE_NAME,
    METRIC_ROWS_JSON_FILE_NAME,
    NEXT_PLAN_FILE_NAME,
    NORMALIZATION_BLIND_SPOTS_FILE_NAME,
    PDF_COVERAGE_SUMMARY_CSV_FILE_NAME,
    PDF_COVERAGE_SUMMARY_JSON_FILE_NAME,
    RAW_METRIC_SUMMARY_CSV_FILE_NAME,
    RAW_METRIC_SUMMARY_JSON_FILE_NAME,
    STAGE_COVERAGE_SUMMARY_CSV_FILE_NAME,
    STAGE_COVERAGE_SUMMARY_JSON_FILE_NAME,
    build_metric_candidate_normalization_coverage_345c,
)
from datefac.benchmark.metric_candidate_normalization_coverage_345c_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    write_csv,
    write_json,
)


def _fieldnames(rows: list[dict], fallback: list[str]) -> list[str]:
    return list(rows[0].keys()) if rows else fallback


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 345C metric candidate normalization coverage.")
    parser.add_argument(
        "--full-structured-data-inventory-345a-dir",
        default=str(DEFAULT_FULL_STRUCTURED_DATA_INVENTORY_345A_DIR),
    )
    parser.add_argument(
        "--full-extraction-quality-audit-345b-dir",
        default=str(DEFAULT_FULL_EXTRACTION_QUALITY_AUDIT_345B_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_metric_candidate_normalization_coverage_345c(
        full_structured_data_inventory_345a_dir=Path(
            args.full_structured_data_inventory_345a_dir
        ),
        full_extraction_quality_audit_345b_dir=Path(
            args.full_extraction_quality_audit_345b_dir
        ),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / METRIC_ROWS_JSON_FILE_NAME, artifacts["metric_rows"])
    write_csv(output_dir / METRIC_ROWS_CSV_FILE_NAME, artifacts["metric_rows"], METRIC_ROW_FIELDS)
    write_json(output_dir / RAW_METRIC_SUMMARY_JSON_FILE_NAME, artifacts["raw_metric_summary"])
    write_csv(
        output_dir / RAW_METRIC_SUMMARY_CSV_FILE_NAME,
        artifacts["raw_metric_summary"],
        _fieldnames(
            artifacts["raw_metric_summary"],
            [
                "raw_metric_name",
                "row_count",
                "normalized_metric_row_count",
                "unnormalized_metric_row_count",
                "normalization_coverage_ratio",
                "source_stages",
                "pdf_names",
                "top_normalization_statuses",
                "suggested_alias_priority",
            ],
        ),
    )
    write_json(
        output_dir / STAGE_COVERAGE_SUMMARY_JSON_FILE_NAME,
        artifacts["stage_coverage_summary"],
    )
    write_csv(
        output_dir / STAGE_COVERAGE_SUMMARY_CSV_FILE_NAME,
        artifacts["stage_coverage_summary"],
        _fieldnames(
            artifacts["stage_coverage_summary"],
            [
                "source_stage",
                "metric_candidate_row_count",
                "normalized_metric_row_count",
                "unnormalized_metric_row_count",
                "normalization_coverage_ratio",
                "top_unnormalized_raw_metric_names",
            ],
        ),
    )
    write_json(
        output_dir / PDF_COVERAGE_SUMMARY_JSON_FILE_NAME,
        artifacts["pdf_coverage_summary"],
    )
    write_csv(
        output_dir / PDF_COVERAGE_SUMMARY_CSV_FILE_NAME,
        artifacts["pdf_coverage_summary"],
        _fieldnames(
            artifacts["pdf_coverage_summary"],
            [
                "pdf_name",
                "metric_candidate_row_count",
                "normalized_metric_row_count",
                "unnormalized_metric_row_count",
                "normalization_coverage_ratio",
                "top_unnormalized_raw_metric_names",
            ],
        ),
    )
    write_json(
        output_dir / ALIAS_CANDIDATE_QUEUE_JSON_FILE_NAME,
        artifacts["alias_candidate_queue"],
    )
    if artifacts["alias_candidate_queue"]:
        write_csv(
            output_dir / ALIAS_CANDIDATE_QUEUE_CSV_FILE_NAME,
            artifacts["alias_candidate_queue"],
            list(artifacts["alias_candidate_queue"][0].keys()),
        )
    else:
        write_csv(output_dir / ALIAS_CANDIDATE_QUEUE_CSV_FILE_NAME, [], ["raw_metric_name"])
    write_json(
        output_dir / NORMALIZATION_BLIND_SPOTS_FILE_NAME,
        artifacts["normalization_blind_spots"],
    )
    (output_dir / EXECUTIVE_SUMMARY_FILE_NAME).write_text(
        executive_summary_markdown(
            artifacts["manifest"],
            artifacts["stage_coverage_summary"],
            artifacts["pdf_coverage_summary"],
            artifacts["alias_candidate_queue"],
            artifacts["normalization_blind_spots"],
        ),
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_FILE_NAME).write_text(
        artifact_index_markdown(artifacts["artifact_index_rows"]),
        encoding="utf-8",
    )
    (output_dir / NEXT_PLAN_FILE_NAME).write_text(
        next_plan_markdown(),
        encoding="utf-8",
    )

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"metric_rows_json: {output_dir / METRIC_ROWS_JSON_FILE_NAME}")
    print(f"metric_rows_csv: {output_dir / METRIC_ROWS_CSV_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"metric_candidate_row_count: {manifest.get('metric_candidate_row_count', '')}")
    print(f"normalized_metric_row_count: {manifest.get('normalized_metric_row_count', '')}")
    print(f"unnormalized_metric_row_count: {manifest.get('unnormalized_metric_row_count', '')}")
    print(f"normalization_coverage_ratio: {manifest.get('normalization_coverage_ratio', '')}")
    print(f"alias_candidate_count: {manifest.get('alias_candidate_count', '')}")
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
