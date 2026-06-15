from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.mineru_image_path_binding_fix_346a2 import (  # noqa: E402
    AMBIGUOUS_ROWS_CSV_FILE_NAME,
    AMBIGUOUS_ROWS_JSON_FILE_NAME,
    ARTIFACT_INDEX_MD_FILE_NAME,
    BINDING_CANDIDATES_CSV_FILE_NAME,
    BINDING_CANDIDATES_JSON_FILE_NAME,
    BINDING_SUMMARY_JSON_FILE_NAME,
    BOUND_ROWS_CSV_FILE_NAME,
    BOUND_ROWS_JSON_FILE_NAME,
    DEFAULT_LEDGER_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_DIR,
    EVIDENCE_CATALOG_CSV_FILE_NAME,
    EVIDENCE_CATALOG_JSON_FILE_NAME,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    IMAGE_RESOLUTION_STATUS_CSV_FILE_NAME,
    IMAGE_RESOLUTION_STATUS_JSON_FILE_NAME,
    JSON_MD_CONTEXT_INDEX_CSV_FILE_NAME,
    JSON_MD_CONTEXT_INDEX_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    UNRESOLVED_ROWS_CSV_FILE_NAME,
    UNRESOLVED_ROWS_JSON_FILE_NAME,
    VLM_REQUEST_PACKAGE_JSONL_FILE_NAME,
    VLM_REQUEST_PACKAGE_PREVIEW_JSON_FILE_NAME,
    build_mineru_image_path_binding_fix_346a2,
)
from datefac.benchmark.mineru_image_path_binding_fix_346a2_report import (  # noqa: E402
    write_csv,
    write_json,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 346A2 MinerU image path binding fix.")
    parser.add_argument(
        "--vision-assisted-table-evidence-pilot-346a-dir",
        default=str(DEFAULT_VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--mineru-output-root")
    parser.add_argument("--mineru-json-md-dir")
    parser.add_argument("--mineru-table-image-dir")
    parser.add_argument("--mineru-page-image-dir")
    parser.add_argument("--table-image-manifest")
    parser.add_argument("--page-image-manifest")
    parser.add_argument("--max-binding-candidates-per-row", type=int, default=5)
    parser.add_argument("--max-context-chars", type=int, default=4000)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_mineru_image_path_binding_fix_346a2(
        vision_assisted_table_evidence_pilot_346a_dir=Path(args.vision_assisted_table_evidence_pilot_346a_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        mineru_output_root=Path(args.mineru_output_root) if args.mineru_output_root else None,
        mineru_json_md_dir=Path(args.mineru_json_md_dir) if args.mineru_json_md_dir else None,
        mineru_table_image_dir=Path(args.mineru_table_image_dir) if args.mineru_table_image_dir else None,
        mineru_page_image_dir=Path(args.mineru_page_image_dir) if args.mineru_page_image_dir else None,
        table_image_manifest=Path(args.table_image_manifest) if args.table_image_manifest else None,
        page_image_manifest=Path(args.page_image_manifest) if args.page_image_manifest else None,
        max_binding_candidates_per_row=args.max_binding_candidates_per_row,
        max_context_chars=args.max_context_chars,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / EVIDENCE_CATALOG_JSON_FILE_NAME, artifacts["evidence_catalog_rows"])
    write_csv(output_dir / EVIDENCE_CATALOG_CSV_FILE_NAME, artifacts["evidence_catalog_rows"])
    write_json(output_dir / BINDING_CANDIDATES_JSON_FILE_NAME, artifacts["binding_candidate_rows"])
    write_csv(output_dir / BINDING_CANDIDATES_CSV_FILE_NAME, artifacts["binding_candidate_rows"])
    write_json(output_dir / BOUND_ROWS_JSON_FILE_NAME, artifacts["bound_rows"])
    write_csv(output_dir / BOUND_ROWS_CSV_FILE_NAME, artifacts["bound_rows"])
    write_json(output_dir / UNRESOLVED_ROWS_JSON_FILE_NAME, artifacts["unresolved_rows"])
    write_csv(output_dir / UNRESOLVED_ROWS_CSV_FILE_NAME, artifacts["unresolved_rows"])
    write_json(output_dir / AMBIGUOUS_ROWS_JSON_FILE_NAME, artifacts["ambiguous_rows"])
    write_csv(output_dir / AMBIGUOUS_ROWS_CSV_FILE_NAME, artifacts["ambiguous_rows"])
    write_json(output_dir / IMAGE_RESOLUTION_STATUS_JSON_FILE_NAME, artifacts["image_resolution_rows"])
    write_csv(output_dir / IMAGE_RESOLUTION_STATUS_CSV_FILE_NAME, artifacts["image_resolution_rows"])
    write_json(output_dir / JSON_MD_CONTEXT_INDEX_JSON_FILE_NAME, artifacts["context_index_rows"])
    write_csv(output_dir / JSON_MD_CONTEXT_INDEX_CSV_FILE_NAME, artifacts["context_index_rows"])
    _write_jsonl(output_dir / VLM_REQUEST_PACKAGE_JSONL_FILE_NAME, artifacts["vlm_request_rows"])
    write_json(output_dir / VLM_REQUEST_PACKAGE_PREVIEW_JSON_FILE_NAME, artifacts["vlm_request_preview"])
    write_json(output_dir / BINDING_SUMMARY_JSON_FILE_NAME, artifacts["binding_summary"])
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(artifacts["executive_summary_md"], encoding="utf-8")
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_md"], encoding="utf-8")
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(artifacts["next_plan_md"], encoding="utf-8")

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"selected_pilot_row_count: {manifest.get('selected_pilot_row_count', '')}")
    print(f"image_bound_count: {manifest.get('image_bound_count', '')}")
    print(f"image_missing_count: {manifest.get('image_missing_count', '')}")
    print(f"ambiguous_image_candidate_count: {manifest.get('ambiguous_image_candidate_count', '')}")
    print(f"vlm_request_count: {manifest.get('vlm_request_count', '')}")
    print(f"recommended_next_step: {manifest.get('recommended_next_step', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
