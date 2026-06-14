from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.full_structured_demo_export_package_345d import (  # noqa: E402
    ALIAS_SIMULATION_SIDECAR_CSV_FILE_NAME,
    ALIAS_SIMULATION_SIDECAR_JSON_FILE_NAME,
    ARTIFACT_INDEX_MD_FILE_NAME,
    DEFAULT_FULL_EXTRACTION_QUALITY_AUDIT_345B_DIR,
    DEFAULT_FULL_STRUCTURED_DATA_INVENTORY_345A_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SECOND_BATCH_ALIAS_APPLY_SIMULATION_345C11_DIR,
    DEMO_EXPORT_SUMMARY_JSON_FILE_NAME,
    DEMO_ROWS_CSV_FILE_NAME,
    DEMO_ROWS_JSON_FILE_NAME,
    DEMO_ROWS_XLSX_FILE_NAME,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    EXCLUDED_ROWS_CSV_FILE_NAME,
    EXCLUDED_ROWS_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    QUALITY_CAVEATS_JSON_FILE_NAME,
    QUALITY_CAVEATS_MD_FILE_NAME,
    QUALITY_LIMITED_ROWS_CSV_FILE_NAME,
    QUALITY_LIMITED_ROWS_JSON_FILE_NAME,
    REMAINING_BLIND_SPOTS_CSV_FILE_NAME,
    REMAINING_BLIND_SPOTS_JSON_FILE_NAME,
    build_full_structured_demo_export_package_345d,
)
from datefac.benchmark.full_structured_demo_export_package_345d_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    quality_caveats_markdown,
    write_csv,
    write_excel,
    write_json,
)


WORKBOOK_SHEET_ORDER = [
    "demo_rows",
    "quality_limited_rows",
    "excluded_rows",
    "remaining_blind_spots",
    "alias_sidecar",
    "quality_caveats",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 345D full structured demo export package.")
    parser.add_argument(
        "--full-structured-data-inventory-345a-dir",
        default=str(DEFAULT_FULL_STRUCTURED_DATA_INVENTORY_345A_DIR),
    )
    parser.add_argument(
        "--full-extraction-quality-audit-345b-dir",
        default=str(DEFAULT_FULL_EXTRACTION_QUALITY_AUDIT_345B_DIR),
    )
    parser.add_argument(
        "--metric-candidate-normalization-coverage-345c-dir",
        default=str(DEFAULT_METRIC_CANDIDATE_NORMALIZATION_COVERAGE_345C_DIR),
    )
    parser.add_argument(
        "--second-batch-alias-apply-simulation-345c11-dir",
        default=str(DEFAULT_SECOND_BATCH_ALIAS_APPLY_SIMULATION_345C11_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--include-quality-limited-rows", action="store_true")
    parser.add_argument("--max-sample-rows-per-caveat", type=int, default=20)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_full_structured_demo_export_package_345d(
        full_structured_data_inventory_345a_dir=Path(args.full_structured_data_inventory_345a_dir),
        full_extraction_quality_audit_345b_dir=Path(args.full_extraction_quality_audit_345b_dir),
        metric_candidate_normalization_coverage_345c_dir=Path(args.metric_candidate_normalization_coverage_345c_dir),
        second_batch_alias_apply_simulation_345c11_dir=Path(args.second_batch_alias_apply_simulation_345c11_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        include_quality_limited_rows=args.include_quality_limited_rows,
        max_sample_rows_per_caveat=args.max_sample_rows_per_caveat,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / DEMO_ROWS_JSON_FILE_NAME, artifacts["demo_rows"])
    write_csv(output_dir / DEMO_ROWS_CSV_FILE_NAME, artifacts["demo_rows"])
    write_json(output_dir / QUALITY_LIMITED_ROWS_JSON_FILE_NAME, artifacts["quality_limited_rows"])
    write_csv(output_dir / QUALITY_LIMITED_ROWS_CSV_FILE_NAME, artifacts["quality_limited_rows"])
    write_json(output_dir / EXCLUDED_ROWS_JSON_FILE_NAME, artifacts["excluded_rows"])
    write_csv(output_dir / EXCLUDED_ROWS_CSV_FILE_NAME, artifacts["excluded_rows"])
    write_json(output_dir / REMAINING_BLIND_SPOTS_JSON_FILE_NAME, artifacts["remaining_blind_spots"])
    write_csv(output_dir / REMAINING_BLIND_SPOTS_CSV_FILE_NAME, artifacts["remaining_blind_spots"])
    write_json(output_dir / ALIAS_SIMULATION_SIDECAR_JSON_FILE_NAME, artifacts["alias_simulation_sidecar"])
    write_csv(output_dir / ALIAS_SIMULATION_SIDECAR_CSV_FILE_NAME, artifacts["alias_simulation_sidecar"])
    write_json(output_dir / QUALITY_CAVEATS_JSON_FILE_NAME, artifacts["quality_caveats"])
    write_json(output_dir / DEMO_EXPORT_SUMMARY_JSON_FILE_NAME, artifacts["demo_export_summary"])
    write_excel(output_dir / DEMO_ROWS_XLSX_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEET_ORDER)
    (output_dir / QUALITY_CAVEATS_MD_FILE_NAME).write_text(
        quality_caveats_markdown(artifacts["quality_caveats"]),
        encoding="utf-8",
    )
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(
        executive_summary_markdown(artifacts["manifest"]),
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(
        artifact_index_markdown(artifacts["artifact_index_rows"]),
        encoding="utf-8",
    )
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(
        next_plan_markdown(artifacts["manifest"]),
        encoding="utf-8",
    )

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"demo_export_row_count: {manifest.get('demo_export_row_count', '')}")
    print(f"quality_limited_row_count: {manifest.get('quality_limited_row_count', '')}")
    print(f"excluded_row_count: {manifest.get('excluded_row_count', '')}")
    print(f"coverage_ratio_before_alias_simulation: {manifest.get('coverage_ratio_before_alias_simulation', '')}")
    print(f"coverage_ratio_after_alias_simulation: {manifest.get('coverage_ratio_after_alias_simulation', '')}")
    print(f"alias_simulated_demo_row_count: {manifest.get('alias_simulated_demo_row_count', '')}")
    print(f"remaining_unnormalized_metric_row_count: {manifest.get('remaining_unnormalized_metric_row_count', '')}")
    print(f"formal_export_generated: {manifest.get('formal_export_generated', '')}")
    print(f"demo_export_only: {manifest.get('demo_export_only', '')}")
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
