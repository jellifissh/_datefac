from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.demo_export_review_qa_checklist_345e import (  # noqa: E402
    ARTIFACT_COMPLETENESS_CSV_FILE_NAME,
    ARTIFACT_COMPLETENESS_JSON_FILE_NAME,
    ARTIFACT_INDEX_MD_FILE_NAME,
    CAVEAT_COMPLETENESS_JSON_FILE_NAME,
    DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_OUTPUT_DIR,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    EXCLUDED_SAMPLE_ROWS_CSV_FILE_NAME,
    EXCLUDED_SAMPLE_ROWS_JSON_FILE_NAME,
    GATE_SAFETY_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    PRESENTATION_READINESS_JSON_FILE_NAME,
    QUALITY_LIMITED_SAMPLE_ROWS_CSV_FILE_NAME,
    QUALITY_LIMITED_SAMPLE_ROWS_JSON_FILE_NAME,
    ROW_COUNT_RECONCILIATION_CSV_FILE_NAME,
    ROW_COUNT_RECONCILIATION_JSON_FILE_NAME,
    REVIEW_CHECKLIST_MD_FILE_NAME,
    SAMPLE_DEMO_ROWS_CSV_FILE_NAME,
    SAMPLE_DEMO_ROWS_JSON_FILE_NAME,
    build_demo_export_review_qa_checklist_345e,
)
from datefac.benchmark.demo_export_review_qa_checklist_345e_report import (  # noqa: E402
    render_review_checklist_markdown,
    write_csv,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 345E demo export review / QA checklist.")
    parser.add_argument(
        "--full-structured-demo-export-package-345d-dir",
        default=str(DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--max-display-sample-rows", type=int, default=30)
    parser.add_argument("--strict-artifact-check", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_demo_export_review_qa_checklist_345e(
        full_structured_demo_export_package_345d_dir=Path(args.full_structured_demo_export_package_345d_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        max_display_sample_rows=args.max_display_sample_rows,
        strict_artifact_check=args.strict_artifact_check,
    )

    manifest = artifacts["manifest"]
    write_json(output_dir / MANIFEST_FILE_NAME, manifest)
    write_json(output_dir / ARTIFACT_COMPLETENESS_JSON_FILE_NAME, artifacts["artifact_completeness_rows"])
    write_csv(output_dir / ARTIFACT_COMPLETENESS_CSV_FILE_NAME, artifacts["artifact_completeness_rows"])
    write_json(output_dir / ROW_COUNT_RECONCILIATION_JSON_FILE_NAME, artifacts["row_count_reconciliation_rows"])
    write_csv(output_dir / ROW_COUNT_RECONCILIATION_CSV_FILE_NAME, artifacts["row_count_reconciliation_rows"])
    write_json(output_dir / GATE_SAFETY_JSON_FILE_NAME, artifacts["gate_safety_check"])
    write_json(output_dir / CAVEAT_COMPLETENESS_JSON_FILE_NAME, artifacts["caveat_completeness_check"])
    write_json(output_dir / PRESENTATION_READINESS_JSON_FILE_NAME, artifacts["demo_presentation_readiness"])
    write_json(output_dir / SAMPLE_DEMO_ROWS_JSON_FILE_NAME, artifacts["sample_demo_rows_package"])
    write_csv(
        output_dir / SAMPLE_DEMO_ROWS_CSV_FILE_NAME,
        artifacts["sample_demo_rows_package"]["rows"],
    )
    write_json(output_dir / QUALITY_LIMITED_SAMPLE_ROWS_JSON_FILE_NAME, artifacts["quality_limited_sample_rows_package"])
    write_csv(
        output_dir / QUALITY_LIMITED_SAMPLE_ROWS_CSV_FILE_NAME,
        artifacts["quality_limited_sample_rows_package"]["rows"],
    )
    write_json(output_dir / EXCLUDED_SAMPLE_ROWS_JSON_FILE_NAME, artifacts["excluded_sample_rows_package"])
    write_csv(
        output_dir / EXCLUDED_SAMPLE_ROWS_CSV_FILE_NAME,
        artifacts["excluded_sample_rows_package"]["rows"],
    )

    (output_dir / REVIEW_CHECKLIST_MD_FILE_NAME).write_text(
        artifacts["review_checklist_markdown"]
        or render_review_checklist_markdown(
            manifest,
            artifacts["artifact_completeness_rows"],
            artifacts["row_count_reconciliation_rows"],
            artifacts["gate_safety_check"],
            artifacts["caveat_completeness_check"],
            artifacts["demo_presentation_readiness"],
        ),
        encoding="utf-8",
    )
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(
        artifacts["executive_summary_markdown"],
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(
        artifacts["artifact_index_markdown"],
        encoding="utf-8",
    )
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(
        artifacts["next_plan_markdown"],
        encoding="utf-8",
    )

    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"row_count_closure_passed: {manifest.get('row_count_closure_passed', '')}")
    print(f"artifact_completeness_passed: {manifest.get('artifact_completeness_passed', '')}")
    print(f"gate_safety_check_passed: {manifest.get('gate_safety_check_passed', '')}")
    print(f"caveat_completeness_passed: {manifest.get('caveat_completeness_passed', '')}")
    print(f"presentation_ready_for_demo_only: {manifest.get('presentation_ready_for_demo_only', '')}")
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
