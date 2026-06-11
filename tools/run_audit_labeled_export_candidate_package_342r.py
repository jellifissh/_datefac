from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.audit_labeled_export_candidate_package_342r import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR,
    DEFAULT_PREVIEW_AUDIT_342Q_DIR,
    DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR,
    DEFAULT_REVIEWED_PREVIEW_342J_DIR,
    build_audit_labeled_export_candidate_package_342r,
)
from datefac.benchmark.audit_labeled_export_candidate_package_342r_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342R audit-labeled export candidate package.")
    parser.add_argument("--preview-audit-342q-dir", default=str(DEFAULT_PREVIEW_AUDIT_342Q_DIR))
    parser.add_argument("--reviewed-plus-preview-342p-dir", default=str(DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR))
    parser.add_argument("--post-adoption-sidecar-342o-dir", default=str(DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR))
    parser.add_argument("--reviewed-preview-342j-dir", default=str(DEFAULT_REVIEWED_PREVIEW_342J_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_audit_labeled_export_candidate_package_342r(
        preview_audit_342q_dir=Path(args.preview_audit_342q_dir),
        reviewed_plus_preview_342p_dir=Path(args.reviewed_plus_preview_342p_dir),
        post_adoption_sidecar_342o_dir=Path(args.post_adoption_sidecar_342o_dir),
        reviewed_preview_342j_dir=Path(args.reviewed_preview_342j_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    summary_json = output_dir / "audit_labeled_export_candidate_package_342r_summary.json"
    manifest_json = output_dir / "audit_labeled_export_candidate_package_342r_manifest.json"
    qa_json = output_dir / "audit_labeled_export_candidate_package_342r_qa.json"
    no_write_back_json = output_dir / "audit_labeled_export_candidate_package_342r_no_write_back_proof.json"
    metadata_json = output_dir / "audit_labeled_export_candidate_package_342r_metadata.json"
    report_md = output_dir / "audit_labeled_export_candidate_package_342r_report.md"
    workbook_xlsx = output_dir / "audit_labeled_export_candidate_package_342r.xlsx"
    candidates_csv = output_dir / "audit_labeled_export_candidate_package_342r_candidates.csv"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_json(metadata_json, artifacts["metadata_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    artifacts["candidates_csv_df"].to_csv(candidates_csv, index=False, encoding="utf-8-sig")
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"audit_labeled_export_candidate_package_342r_summary_json: {summary_json}")
    print(f"audit_labeled_export_candidate_package_342r_manifest_json: {manifest_json}")
    print(f"audit_labeled_export_candidate_package_342r_qa_json: {qa_json}")
    print(f"audit_labeled_export_candidate_package_342r_no_write_back_proof_json: {no_write_back_json}")
    print(f"audit_labeled_export_candidate_package_342r_metadata_json: {metadata_json}")
    print(f"audit_labeled_export_candidate_package_342r_report_md: {report_md}")
    print(f"audit_labeled_export_candidate_package_342r_xlsx: {workbook_xlsx}")
    print(f"audit_labeled_export_candidate_package_342r_candidates_csv: {candidates_csv}")
    for key in [
        "decision",
        "export_candidate_package_row_count",
        "human_reviewed_candidate_count",
        "simulated_candidate_count",
        "simulated_direct_candidate_count",
        "simulated_corrected_candidate_count",
        "formal_client_export_allowed",
        "export_candidate_scope_allowed",
        "export_risk_level",
        "collision_logged_count",
        "duplicate_metric_year_source_count",
        "severe_collision_count",
        "human_over_simulation_override_count",
        "simulated_duplicate_dropped_count",
        "still_human_required_count",
        "remaining_review_count",
        "disclaimer_required_count",
        "later_audit_required_count",
        "package_row_fail_count",
        "ready_for_342s",
        "recommended_342s_scope",
        "client_ready",
        "production_ready",
        "qa_fail_count",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
