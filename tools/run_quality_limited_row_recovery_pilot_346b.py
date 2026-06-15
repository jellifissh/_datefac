from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.quality_limited_row_recovery_pilot_346b import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    CONTEXT_INJECTION_RESULTS_CSV_FILE_NAME,
    CONTEXT_INJECTION_RESULTS_JSON_FILE_NAME,
    DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_MINERU_IMAGE_PATH_BINDING_FIX_346A2_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_DIR,
    DOWNGRADED_ROWS_CSV_FILE_NAME,
    DOWNGRADED_ROWS_JSON_FILE_NAME,
    EVIDENCE_ASSISTED_RESULTS_CSV_FILE_NAME,
    EVIDENCE_ASSISTED_RESULTS_JSON_FILE_NAME,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    INPUT_ROWS_CSV_FILE_NAME,
    INPUT_ROWS_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEEDS_HUMAN_ROWS_CSV_FILE_NAME,
    NEEDS_HUMAN_ROWS_JSON_FILE_NAME,
    NEEDS_VLM_ROWS_CSV_FILE_NAME,
    NEEDS_VLM_ROWS_JSON_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    REAUDIT_SUMMARY_JSON_FILE_NAME,
    RECOVERED_ROWS_CSV_FILE_NAME,
    RECOVERED_ROWS_JSON_FILE_NAME,
    RECOVERY_FAIL_REASONS_CSV_FILE_NAME,
    RECOVERY_FAIL_REASONS_JSON_FILE_NAME,
    STILL_LIMITED_ROWS_CSV_FILE_NAME,
    STILL_LIMITED_ROWS_JSON_FILE_NAME,
    VALUE_SANITIZER_RESULTS_CSV_FILE_NAME,
    VALUE_SANITIZER_RESULTS_JSON_FILE_NAME,
    build_quality_limited_row_recovery_pilot_346b,
)
from datefac.benchmark.quality_limited_row_recovery_pilot_346b_report import (  # noqa: E402
    write_csv,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 346B Quality-Limited Row Recovery Pilot.")
    parser.add_argument(
        "--full-structured-demo-export-package-345d-dir",
        default=str(DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR),
    )
    parser.add_argument(
        "--vision-assisted-table-evidence-pilot-346a-dir",
        default=str(DEFAULT_VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_DIR),
    )
    parser.add_argument(
        "--mineru-image-path-binding-fix-346a2-dir",
        default=str(DEFAULT_MINERU_IMAGE_PATH_BINDING_FIX_346A2_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--max-pilot-rows", type=int, default=100)
    parser.add_argument("--require-image-bound", action="store_true")
    parser.add_argument("--include-json-md-context-only", default="true")
    parser.add_argument("--strict-promotion", action="store_true")
    parser.add_argument("--max-context-chars", type=int, default=4000)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    include_json_md_context_only = str(args.include_json_md_context_only).strip().lower() not in {"0", "false", "no"}

    artifacts = build_quality_limited_row_recovery_pilot_346b(
        full_structured_demo_export_package_345d_dir=Path(args.full_structured_demo_export_package_345d_dir),
        vision_assisted_table_evidence_pilot_346a_dir=Path(args.vision_assisted_table_evidence_pilot_346a_dir),
        mineru_image_path_binding_fix_346a2_dir=Path(args.mineru_image_path_binding_fix_346a2_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        max_pilot_rows=args.max_pilot_rows,
        require_image_bound=args.require_image_bound,
        include_json_md_context_only=include_json_md_context_only,
        strict_promotion=args.strict_promotion,
        max_context_chars=args.max_context_chars,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / INPUT_ROWS_JSON_FILE_NAME, artifacts["input_rows"])
    write_csv(output_dir / INPUT_ROWS_CSV_FILE_NAME, artifacts["input_rows"])
    write_json(output_dir / VALUE_SANITIZER_RESULTS_JSON_FILE_NAME, artifacts["value_sanitizer_results"])
    write_csv(output_dir / VALUE_SANITIZER_RESULTS_CSV_FILE_NAME, artifacts["value_sanitizer_results"])
    write_json(output_dir / CONTEXT_INJECTION_RESULTS_JSON_FILE_NAME, artifacts["context_injection_results"])
    write_csv(output_dir / CONTEXT_INJECTION_RESULTS_CSV_FILE_NAME, artifacts["context_injection_results"])
    write_json(output_dir / EVIDENCE_ASSISTED_RESULTS_JSON_FILE_NAME, artifacts["evidence_assisted_recovery_results"])
    write_csv(output_dir / EVIDENCE_ASSISTED_RESULTS_CSV_FILE_NAME, artifacts["evidence_assisted_recovery_results"])
    write_json(output_dir / RECOVERED_ROWS_JSON_FILE_NAME, artifacts["recovered_demo_candidates"])
    write_csv(output_dir / RECOVERED_ROWS_CSV_FILE_NAME, artifacts["recovered_demo_candidates"])
    write_json(output_dir / STILL_LIMITED_ROWS_JSON_FILE_NAME, artifacts["still_limited_rows"])
    write_csv(output_dir / STILL_LIMITED_ROWS_CSV_FILE_NAME, artifacts["still_limited_rows"])
    write_json(output_dir / NEEDS_VLM_ROWS_JSON_FILE_NAME, artifacts["needs_vlm_rows"])
    write_csv(output_dir / NEEDS_VLM_ROWS_CSV_FILE_NAME, artifacts["needs_vlm_rows"])
    write_json(output_dir / NEEDS_HUMAN_ROWS_JSON_FILE_NAME, artifacts["needs_human_review_rows"])
    write_csv(output_dir / NEEDS_HUMAN_ROWS_CSV_FILE_NAME, artifacts["needs_human_review_rows"])
    write_json(output_dir / DOWNGRADED_ROWS_JSON_FILE_NAME, artifacts["downgraded_excluded_rows"])
    write_csv(output_dir / DOWNGRADED_ROWS_CSV_FILE_NAME, artifacts["downgraded_excluded_rows"])
    write_json(output_dir / RECOVERY_FAIL_REASONS_JSON_FILE_NAME, artifacts["recovery_fail_reasons"])
    write_csv(output_dir / RECOVERY_FAIL_REASONS_CSV_FILE_NAME, artifacts["recovery_fail_reasons"])
    write_json(output_dir / REAUDIT_SUMMARY_JSON_FILE_NAME, artifacts["reaudit_summary"])
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(artifacts["executive_summary_md"], encoding="utf-8")
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_md"], encoding="utf-8")
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(artifacts["next_plan_md"], encoding="utf-8")

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"pilot_input_row_count: {manifest.get('pilot_input_row_count', '')}")
    print(f"recovered_demo_candidate_count: {manifest.get('recovered_demo_candidate_count', '')}")
    print(f"still_quality_limited_count: {manifest.get('still_quality_limited_count', '')}")
    print(f"needs_vlm_count: {manifest.get('needs_vlm_count', '')}")
    print(f"needs_human_review_count: {manifest.get('needs_human_review_count', '')}")
    print(f"recommended_next_step: {manifest.get('recommended_next_step', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
