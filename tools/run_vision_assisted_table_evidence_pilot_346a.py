from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.vision_assisted_table_evidence_pilot_346a import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    CANDIDATE_POOL_CSV_FILE_NAME,
    CANDIDATE_POOL_JSON_FILE_NAME,
    CONFLICT_HANDLING_POLICY_MD_FILE_NAME,
    COST_LATENCY_ESTIMATE_JSON_FILE_NAME,
    DEFAULT_DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_DIR,
    DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_OUTPUT_DIR,
    EVIDENCE_BUNDLE_INDEX_CSV_FILE_NAME,
    EVIDENCE_BUNDLE_INDEX_JSON_FILE_NAME,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    FIELD_REPAIR_TARGETS_CSV_FILE_NAME,
    FIELD_REPAIR_TARGETS_JSON_FILE_NAME,
    IMAGE_RESOLUTION_STATUS_CSV_FILE_NAME,
    IMAGE_RESOLUTION_STATUS_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    SELECTED_PILOT_ROWS_CSV_FILE_NAME,
    SELECTED_PILOT_ROWS_JSON_FILE_NAME,
    VLM_OUTPUT_SCHEMA_JSON_FILE_NAME,
    VLM_PROMPT_TEMPLATES_MD_FILE_NAME,
    VLM_REQUEST_PACKAGE_JSONL_FILE_NAME,
    VLM_REQUEST_PACKAGE_PREVIEW_JSON_FILE_NAME,
    build_vision_assisted_table_evidence_pilot_346a,
)
from datefac.benchmark.vision_assisted_table_evidence_pilot_346a_report import (  # noqa: E402
    write_csv,
    write_json,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 346A vision-assisted table evidence pilot.")
    parser.add_argument(
        "--full-structured-demo-export-package-345d-dir",
        default=str(DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR),
    )
    parser.add_argument(
        "--demo-export-review-qa-checklist-345e-dir",
        default=str(DEFAULT_DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--mineru-json-md-dir")
    parser.add_argument("--mineru-table-image-dir")
    parser.add_argument("--mineru-page-image-dir")
    parser.add_argument("--table-image-manifest")
    parser.add_argument("--max-pilot-rows", type=int, default=100)
    parser.add_argument("--max-context-rows-per-request", type=int, default=5)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_vision_assisted_table_evidence_pilot_346a(
        full_structured_demo_export_package_345d_dir=Path(args.full_structured_demo_export_package_345d_dir),
        demo_export_review_qa_checklist_345e_dir=Path(args.demo_export_review_qa_checklist_345e_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        mineru_json_md_dir=Path(args.mineru_json_md_dir) if args.mineru_json_md_dir else None,
        mineru_table_image_dir=Path(args.mineru_table_image_dir) if args.mineru_table_image_dir else None,
        mineru_page_image_dir=Path(args.mineru_page_image_dir) if args.mineru_page_image_dir else None,
        table_image_manifest=Path(args.table_image_manifest) if args.table_image_manifest else None,
        max_pilot_rows=args.max_pilot_rows,
        max_context_rows_per_request=args.max_context_rows_per_request,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / CANDIDATE_POOL_JSON_FILE_NAME, artifacts["candidate_pool_rows"])
    write_csv(output_dir / CANDIDATE_POOL_CSV_FILE_NAME, artifacts["candidate_pool_rows"])
    write_json(output_dir / SELECTED_PILOT_ROWS_JSON_FILE_NAME, artifacts["selected_pilot_rows"])
    write_csv(output_dir / SELECTED_PILOT_ROWS_CSV_FILE_NAME, artifacts["selected_pilot_rows"])
    write_json(output_dir / EVIDENCE_BUNDLE_INDEX_JSON_FILE_NAME, artifacts["evidence_bundle_rows"])
    write_csv(output_dir / EVIDENCE_BUNDLE_INDEX_CSV_FILE_NAME, artifacts["evidence_bundle_rows"])
    write_json(output_dir / IMAGE_RESOLUTION_STATUS_JSON_FILE_NAME, artifacts["image_resolution_rows"])
    write_csv(output_dir / IMAGE_RESOLUTION_STATUS_CSV_FILE_NAME, artifacts["image_resolution_rows"])
    write_json(output_dir / FIELD_REPAIR_TARGETS_JSON_FILE_NAME, artifacts["field_repair_target_rows"])
    write_csv(output_dir / FIELD_REPAIR_TARGETS_CSV_FILE_NAME, artifacts["field_repair_target_rows"])
    _write_jsonl(output_dir / VLM_REQUEST_PACKAGE_JSONL_FILE_NAME, artifacts["vlm_request_rows"])
    write_json(output_dir / VLM_REQUEST_PACKAGE_PREVIEW_JSON_FILE_NAME, artifacts["vlm_request_preview"])
    write_json(output_dir / VLM_OUTPUT_SCHEMA_JSON_FILE_NAME, artifacts["vlm_output_schema"])
    (output_dir / VLM_PROMPT_TEMPLATES_MD_FILE_NAME).write_text(artifacts["vlm_prompt_templates_md"], encoding="utf-8")
    (output_dir / CONFLICT_HANDLING_POLICY_MD_FILE_NAME).write_text(
        artifacts["conflict_handling_policy_md"], encoding="utf-8"
    )
    write_json(output_dir / COST_LATENCY_ESTIMATE_JSON_FILE_NAME, artifacts["cost_latency_estimate"])
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(artifacts["executive_summary_md"], encoding="utf-8")
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_md"], encoding="utf-8")
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(artifacts["next_plan_md"], encoding="utf-8")

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"candidate_pool_row_count: {manifest.get('candidate_pool_row_count', '')}")
    print(f"selected_pilot_row_count: {manifest.get('selected_pilot_row_count', '')}")
    print(f"image_bound_count: {manifest.get('image_bound_count', '')}")
    print(f"image_missing_count: {manifest.get('image_missing_count', '')}")
    print(f"vlm_request_count: {manifest.get('vlm_request_count', '')}")
    print(f"live_vlm_call_count: {manifest.get('live_vlm_call_count', '')}")
    print(f"recommended_next_step: {manifest.get('recommended_next_step', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
