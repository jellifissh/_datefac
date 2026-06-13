from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.full_structured_data_inventory_345a import (  # noqa: E402
    ARTIFACT_INDEX_FILE_NAME,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_STRICT_HUMAN_REVIEW_PACKAGE_344F_DIR,
    DEFAULT_TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_DIR,
    DEFAULT_TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_DIR,
    DEFAULT_TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_DIR,
    DOWNSTREAM_READINESS_SUMMARY_FILE_NAME,
    EXECUTIVE_SUMMARY_FILE_NAME,
    MANIFEST_FILE_NAME,
    MISSING_FIELD_SUMMARY_CSV_FILE_NAME,
    MISSING_FIELD_SUMMARY_JSON_FILE_NAME,
    NEXT_PLAN_FILE_NAME,
    ROW_INVENTORY_CSV_FILE_NAME,
    ROW_INVENTORY_FIELDS,
    ROW_INVENTORY_JSON_FILE_NAME,
    SOURCE_ARTIFACT_MAP_FILE_NAME,
    STAGE_STATUS_SUMMARY_CSV_FILE_NAME,
    STAGE_STATUS_SUMMARY_JSON_FILE_NAME,
    build_full_structured_data_inventory_345a,
)
from datefac.benchmark.full_structured_data_inventory_345a_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    write_csv,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 345A full structured data inventory.")
    parser.add_argument(
        "--table-first-core-financial-extraction-342f-dir",
        default=str(DEFAULT_TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_DIR),
    )
    parser.add_argument(
        "--table-first-extraction-review-package-342g-dir",
        default=str(DEFAULT_TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_DIR),
    )
    parser.add_argument(
        "--table-first-human-review-apply-simulation-342h-dir",
        default=str(DEFAULT_TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_DIR),
    )
    parser.add_argument(
        "--review-queue-strict-human-review-package-344f-dir",
        default=str(DEFAULT_REVIEW_QUEUE_STRICT_HUMAN_REVIEW_PACKAGE_344F_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_full_structured_data_inventory_345a(
        table_first_core_financial_extraction_342f_dir=Path(
            args.table_first_core_financial_extraction_342f_dir
        ),
        table_first_extraction_review_package_342g_dir=Path(
            args.table_first_extraction_review_package_342g_dir
        ),
        table_first_human_review_apply_simulation_342h_dir=Path(
            args.table_first_human_review_apply_simulation_342h_dir
        ),
        review_queue_strict_human_review_package_344f_dir=Path(
            args.review_queue_strict_human_review_package_344f_dir
        ),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / SOURCE_ARTIFACT_MAP_FILE_NAME, artifacts["source_artifact_map"])
    write_json(output_dir / ROW_INVENTORY_JSON_FILE_NAME, artifacts["row_inventory"])
    write_csv(
        output_dir / ROW_INVENTORY_CSV_FILE_NAME,
        artifacts["row_inventory"],
        ROW_INVENTORY_FIELDS,
    )
    write_json(
        output_dir / STAGE_STATUS_SUMMARY_JSON_FILE_NAME,
        artifacts["stage_status_summary"],
    )
    if artifacts["stage_status_summary"]:
        write_csv(
            output_dir / STAGE_STATUS_SUMMARY_CSV_FILE_NAME,
            artifacts["stage_status_summary"],
            list(artifacts["stage_status_summary"][0].keys()),
        )
    else:
        write_csv(output_dir / STAGE_STATUS_SUMMARY_CSV_FILE_NAME, [], ["source_stage"])
    write_json(
        output_dir / MISSING_FIELD_SUMMARY_JSON_FILE_NAME,
        artifacts["missing_field_summary"],
    )
    if artifacts["missing_field_summary"]:
        write_csv(
            output_dir / MISSING_FIELD_SUMMARY_CSV_FILE_NAME,
            artifacts["missing_field_summary"],
            list(artifacts["missing_field_summary"][0].keys()),
        )
    else:
        write_csv(output_dir / MISSING_FIELD_SUMMARY_CSV_FILE_NAME, [], ["source_stage"])
    write_json(
        output_dir / DOWNSTREAM_READINESS_SUMMARY_FILE_NAME,
        artifacts["downstream_readiness_summary"],
    )
    (output_dir / EXECUTIVE_SUMMARY_FILE_NAME).write_text(
        executive_summary_markdown(
            artifacts["manifest"],
            artifacts["stage_status_summary"],
            artifacts["missing_field_summary"],
            artifacts["downstream_readiness_summary"],
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
    print(f"row_inventory_json: {output_dir / ROW_INVENTORY_JSON_FILE_NAME}")
    print(f"row_inventory_csv: {output_dir / ROW_INVENTORY_CSV_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"total_inventory_row_count: {manifest.get('total_inventory_row_count', '')}")
    print(
        f"downstream_ready_candidate_count: {manifest.get('downstream_ready_candidate_count', '')}"
    )
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
