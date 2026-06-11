from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_schema_343a import (  # noqa: E402
    ARGILLA_MAPPING_FILE_NAME,
    DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PREVIEW_AUDIT_342Q_DIR,
    DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR,
    DEFAULT_SNAPSHOT_342S_DIR,
    EXCEL_TEMPLATE_SPEC_FILE_NAME,
    JSON_SCHEMA_FILE_NAME,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    SAMPLE_ITEMS_FILE_NAME,
    SCHEMA_FILE_NAME,
    SUMMARY_FILE_NAME,
    UI_CONTRACT_FILE_NAME,
    WORKBOOK_FILE_NAME,
    build_review_queue_schema_343a,
)
from datefac.benchmark.review_queue_schema_343a_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    ui_contract_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 343A review queue schema and human review UI pilot.")
    parser.add_argument("--snapshot-342s-dir", default=str(DEFAULT_SNAPSHOT_342S_DIR))
    parser.add_argument("--audit-labeled-package-342r-dir", default=str(DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR))
    parser.add_argument("--preview-audit-342q-dir", default=str(DEFAULT_PREVIEW_AUDIT_342Q_DIR))
    parser.add_argument("--reviewed-plus-preview-342p-dir", default=str(DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_schema_343a(
        snapshot_342s_dir=Path(args.snapshot_342s_dir),
        audit_labeled_package_342r_dir=Path(args.audit_labeled_package_342r_dir),
        preview_audit_342q_dir=Path(args.preview_audit_342q_dir),
        reviewed_plus_preview_342p_dir=Path(args.reviewed_plus_preview_342p_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / SCHEMA_FILE_NAME, artifacts["schema_json"])
    write_json(output_dir / JSON_SCHEMA_FILE_NAME, artifacts["json_schema"])
    write_json(output_dir / EXCEL_TEMPLATE_SPEC_FILE_NAME, artifacts["excel_template_spec"])
    write_json(output_dir / ARGILLA_MAPPING_FILE_NAME, artifacts["argilla_mapping"])
    write_jsonl(output_dir / SAMPLE_ITEMS_FILE_NAME, artifacts["sample_items"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    (output_dir / REPORT_FILE_NAME).write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")
    (output_dir / UI_CONTRACT_FILE_NAME).write_text(ui_contract_markdown(artifacts["ui_contract"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"review_queue_schema_343a_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_schema_343a_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_schema_343a_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_schema_343a_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_schema_343a_schema_json: {output_dir / SCHEMA_FILE_NAME}")
    print(f"review_queue_schema_343a_json_schema_json: {output_dir / JSON_SCHEMA_FILE_NAME}")
    print(f"review_queue_schema_343a_excel_template_spec_json: {output_dir / EXCEL_TEMPLATE_SPEC_FILE_NAME}")
    print(f"review_queue_schema_343a_argilla_mapping_json: {output_dir / ARGILLA_MAPPING_FILE_NAME}")
    print(f"review_queue_schema_343a_ui_contract_md: {output_dir / UI_CONTRACT_FILE_NAME}")
    print(f"review_queue_schema_343a_sample_items_jsonl: {output_dir / SAMPLE_ITEMS_FILE_NAME}")
    print(f"review_queue_schema_343a_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_schema_343a_xlsx: {output_dir / WORKBOOK_FILE_NAME}")
    for key in [
        "decision",
        "review_queue_schema_version",
        "field_count",
        "required_field_count",
        "status_count",
        "reason_code_count",
        "priority_level_count",
        "sample_queue_item_count",
        "human_reviewed_sample_count",
        "simulated_sample_count",
        "summary_derived_sample_count",
        "argilla_mapping_generated",
        "excel_template_spec_generated",
        "ui_contract_generated",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343b",
        "recommended_343b_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
