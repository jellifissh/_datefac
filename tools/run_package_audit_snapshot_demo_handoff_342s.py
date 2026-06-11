from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.package_audit_snapshot_demo_handoff_342s import (  # noqa: E402
    ARTIFACT_INDEX_FILE_NAME,
    DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR,
    DEFAULT_PREVIEW_AUDIT_342Q_DIR,
    DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR,
    DEFAULT_REVIEWED_PREVIEW_342J_DIR,
    DEMO_README_FILE_NAME,
    FORBIDDEN_STAGE_PATHS,
    HANDOFF_CHECKLIST_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_STEP_PLAN_FILE_NAME,
    NO_WRITE_BACK_FILE_NAME,
    PROTECTED_DIRTY_PATHS,
    QA_FILE_NAME,
    REPORT_FILE_NAME,
    SUMMARY_FILE_NAME,
    WORKBOOK_FILE_NAME,
    build_package_audit_snapshot_demo_handoff_342s,
)
from datefac.benchmark.package_audit_snapshot_demo_handoff_342s_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    demo_readme_markdown,
    handoff_checklist_markdown,
    next_step_plan_markdown,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342S package audit snapshot / demo handoff.")
    parser.add_argument("--audit-labeled-package-342r-dir", default=str(DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR))
    parser.add_argument("--preview-audit-342q-dir", default=str(DEFAULT_PREVIEW_AUDIT_342Q_DIR))
    parser.add_argument("--reviewed-plus-preview-342p-dir", default=str(DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR))
    parser.add_argument("--post-adoption-sidecar-342o-dir", default=str(DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR))
    parser.add_argument("--reviewed-preview-342j-dir", default=str(DEFAULT_REVIEWED_PREVIEW_342J_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_package_audit_snapshot_demo_handoff_342s(
        audit_labeled_package_342r_dir=Path(args.audit_labeled_package_342r_dir),
        preview_audit_342q_dir=Path(args.preview_audit_342q_dir),
        reviewed_plus_preview_342p_dir=Path(args.reviewed_plus_preview_342p_dir),
        post_adoption_sidecar_342o_dir=Path(args.post_adoption_sidecar_342o_dir),
        reviewed_preview_342j_dir=Path(args.reviewed_preview_342j_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    summary_json = output_dir / SUMMARY_FILE_NAME
    manifest_json = output_dir / MANIFEST_FILE_NAME
    qa_json = output_dir / QA_FILE_NAME
    no_write_back_json = output_dir / NO_WRITE_BACK_FILE_NAME
    report_md = output_dir / REPORT_FILE_NAME
    workbook_xlsx = output_dir / WORKBOOK_FILE_NAME
    demo_readme_md = output_dir / DEMO_README_FILE_NAME
    handoff_checklist_md = output_dir / HANDOFF_CHECKLIST_FILE_NAME
    artifact_index_json = output_dir / ARTIFACT_INDEX_FILE_NAME
    next_step_plan_md = output_dir / NEXT_STEP_PLAN_FILE_NAME

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_json(artifact_index_json, artifacts["artifact_index_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)

    summary = artifacts["summary"]
    context = artifacts["demo_readme_context"]
    report_md.write_text(report_markdown(summary, artifacts["qa_json"]), encoding="utf-8")
    demo_readme_md.write_text(
        demo_readme_markdown(summary, context["recommended_sheets"]),
        encoding="utf-8",
    )
    handoff_checklist_md.write_text(
        handoff_checklist_markdown(
            summary,
            summary.get("latest_commit_sha_before_342s", ""),
            FORBIDDEN_STAGE_PATHS,
            PROTECTED_DIRTY_PATHS + ["tools/mineru_new_runner.cmd"],
            context["recommended_sheets"],
        ),
        encoding="utf-8",
    )
    next_step_plan_md.write_text(next_step_plan_markdown(summary), encoding="utf-8")

    print(f"package_audit_snapshot_demo_handoff_342s_summary_json: {summary_json}")
    print(f"package_audit_snapshot_demo_handoff_342s_manifest_json: {manifest_json}")
    print(f"package_audit_snapshot_demo_handoff_342s_qa_json: {qa_json}")
    print(f"package_audit_snapshot_demo_handoff_342s_no_write_back_proof_json: {no_write_back_json}")
    print(f"package_audit_snapshot_demo_handoff_342s_artifact_index_json: {artifact_index_json}")
    print(f"package_audit_snapshot_demo_handoff_342s_report_md: {report_md}")
    print(f"package_audit_snapshot_demo_handoff_342s_demo_readme_md: {demo_readme_md}")
    print(f"package_audit_snapshot_demo_handoff_342s_handoff_checklist_md: {handoff_checklist_md}")
    print(f"package_audit_snapshot_demo_handoff_342s_next_step_plan_md: {next_step_plan_md}")
    print(f"package_audit_snapshot_demo_handoff_342s_xlsx: {workbook_xlsx}")
    for key in [
        "decision",
        "latest_completed_milestone",
        "current_milestone",
        "current_mainline",
        "export_candidate_package_row_count",
        "human_reviewed_candidate_count",
        "simulated_candidate_count",
        "simulated_direct_candidate_count",
        "simulated_corrected_candidate_count",
        "disclaimer_required_count",
        "later_audit_required_count",
        "export_risk_level",
        "collision_logged_count",
        "duplicate_metric_year_source_count",
        "severe_collision_count",
        "unresolved_collision_count",
        "still_human_required_count",
        "remaining_review_count",
        "formal_client_export_allowed",
        "client_ready",
        "production_ready",
        "demo_handoff_ready",
        "ready_for_343a",
        "recommended_343a_scope",
        "qa_fail_count",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
