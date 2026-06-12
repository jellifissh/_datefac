from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.review_queue_apply_simulation_343e import (  # noqa: E402
    APPLY_PLAN_FILE_NAME,
    AUDIT_GATE_FILE_NAME,
    BOUNDARY_FILE_NAME,
    DEFAULT_EXCEL_INGESTION_343D_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR,
    MANIFEST_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    RISK_REGISTER_FILE_NAME,
    SIMULATED_SIDECAR_FILE_NAME,
    SUMMARY_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS,
    build_review_queue_apply_simulation_343e,
)
from datefac.benchmark.review_queue_apply_simulation_343e_report import (  # noqa: E402
    ai_assisted_boundary_markdown,
    report_markdown,
    write_excel,
    write_json,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 343E AI-assisted review apply simulation and audit gate.")
    parser.add_argument("--excel-ingestion-343d-dir", default=str(DEFAULT_EXCEL_INGESTION_343D_DIR))
    parser.add_argument("--review-queue-schema-343a-dir", default=str(DEFAULT_REVIEW_QUEUE_SCHEMA_343A_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_review_queue_apply_simulation_343e(
        excel_ingestion_343d_dir=Path(args.excel_ingestion_343d_dir),
        review_queue_schema_343a_dir=Path(args.review_queue_schema_343a_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / SUMMARY_FILE_NAME, artifacts["summary"])
    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / QA_FILE_NAME, artifacts["qa_json"])
    write_json(output_dir / NO_WRITE_BACK_FILE_NAME, artifacts["no_write_back_proof_json"])
    write_json(output_dir / AUDIT_GATE_FILE_NAME, artifacts["audit_gate"])
    write_json(output_dir / RISK_REGISTER_FILE_NAME, artifacts["risk_register"])
    write_jsonl(output_dir / APPLY_PLAN_FILE_NAME, artifacts["apply_plan_rows"])
    write_jsonl(output_dir / SIMULATED_SIDECAR_FILE_NAME, artifacts["simulated_sidecar_rows"])
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    (output_dir / REPORT_FILE_NAME).write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")
    (output_dir / BOUNDARY_FILE_NAME).write_text(ai_assisted_boundary_markdown(artifacts["summary"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"review_queue_apply_simulation_343e_summary_json: {output_dir / SUMMARY_FILE_NAME}")
    print(f"review_queue_apply_simulation_343e_manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"review_queue_apply_simulation_343e_qa_json: {output_dir / QA_FILE_NAME}")
    print(f"review_queue_apply_simulation_343e_no_write_back_proof_json: {output_dir / NO_WRITE_BACK_FILE_NAME}")
    print(f"review_queue_apply_simulation_343e_apply_plan_jsonl: {output_dir / APPLY_PLAN_FILE_NAME}")
    print(f"review_queue_apply_simulation_343e_simulated_sidecar_jsonl: {output_dir / SIMULATED_SIDECAR_FILE_NAME}")
    print(f"review_queue_apply_simulation_343e_audit_gate_json: {output_dir / AUDIT_GATE_FILE_NAME}")
    print(f"review_queue_apply_simulation_343e_risk_register_json: {output_dir / RISK_REGISTER_FILE_NAME}")
    print(f"review_queue_apply_simulation_343e_ai_assisted_boundary_md: {output_dir / BOUNDARY_FILE_NAME}")
    print(f"review_queue_apply_simulation_343e_report_md: {output_dir / REPORT_FILE_NAME}")
    print(f"review_queue_apply_simulation_343e_xlsx: {output_dir / WORKBOOK_FILE_NAME}")
    for key in [
        "decision",
        "review_queue_schema_version",
        "input_reviewed_result_row_count",
        "apply_plan_row_count",
        "simulated_sidecar_row_count",
        "hold_row_count",
        "simulate_confirm_apply_count",
        "simulate_correction_apply_count",
        "hold_rejected_count",
        "hold_source_check_required_count",
        "hold_skipped_count",
        "review_source_type",
        "not_pure_human_review",
        "strict_human_review_completed",
        "requires_human_spot_check",
        "apply_mode",
        "apply_simulation_completed",
        "audit_gate_passed_for_spot_check_package",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "ready_for_343f",
        "recommended_343f_scope",
        "qa_fail_count",
        "no_write_back_proof_passed",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
