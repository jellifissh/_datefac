from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.demo_narrative_report_package_345f import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    CLAIMS_ALLOWED_VS_FORBIDDEN_MD_FILE_NAME,
    DEFAULT_DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_DIR,
    DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_OUTPUT_DIR,
    FRONTEND_DEMO_COPY_MD_FILE_NAME,
    INTERVIEW_PROJECT_SUMMARY_MD_FILE_NAME,
    MANIFEST_FILE_NAME,
    METRICS_SUMMARY_CSV_FILE_NAME,
    METRICS_SUMMARY_JSON_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    RISK_AND_CAVEAT_SECTION_MD_FILE_NAME,
    SAMPLE_ROWS_FOR_STORY_CSV_FILE_NAME,
    SAMPLE_ROWS_FOR_STORY_JSON_FILE_NAME,
    STAKEHOLDER_REPORT_MD_FILE_NAME,
    TALKING_POINTS_MD_FILE_NAME,
    TEAM_UPDATE_MD_FILE_NAME,
    TEACHER_BRIEF_MD_FILE_NAME,
    build_demo_narrative_report_package_345f,
)
from datefac.benchmark.demo_narrative_report_package_345f_report import (  # noqa: E402
    write_csv,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 345F demo narrative report package.")
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
    parser.add_argument("--max-sample-rows-in-report", type=int, default=10)
    parser.add_argument("--audience", action="append", default=[])
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_demo_narrative_report_package_345f(
        full_structured_demo_export_package_345d_dir=Path(args.full_structured_demo_export_package_345d_dir),
        demo_export_review_qa_checklist_345e_dir=Path(args.demo_export_review_qa_checklist_345e_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        max_sample_rows_in_report=args.max_sample_rows_in_report,
        audiences=args.audience or ["teacher"],
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    (output_dir / STAKEHOLDER_REPORT_MD_FILE_NAME).write_text(artifacts["stakeholder_report_md"], encoding="utf-8")
    (output_dir / TEACHER_BRIEF_MD_FILE_NAME).write_text(artifacts["teacher_brief_md"], encoding="utf-8")
    (output_dir / TEAM_UPDATE_MD_FILE_NAME).write_text(artifacts["team_update_md"], encoding="utf-8")
    (output_dir / INTERVIEW_PROJECT_SUMMARY_MD_FILE_NAME).write_text(
        artifacts["interview_project_summary_md"], encoding="utf-8"
    )
    (output_dir / FRONTEND_DEMO_COPY_MD_FILE_NAME).write_text(artifacts["frontend_demo_copy_md"], encoding="utf-8")
    (output_dir / TALKING_POINTS_MD_FILE_NAME).write_text(artifacts["talking_points_md"], encoding="utf-8")
    (output_dir / RISK_AND_CAVEAT_SECTION_MD_FILE_NAME).write_text(
        artifacts["risk_and_caveat_section_md"], encoding="utf-8"
    )
    write_json(output_dir / METRICS_SUMMARY_JSON_FILE_NAME, artifacts["metrics_summary_json"])
    write_csv(output_dir / METRICS_SUMMARY_CSV_FILE_NAME, artifacts["metrics_summary_rows"])
    write_json(output_dir / SAMPLE_ROWS_FOR_STORY_JSON_FILE_NAME, artifacts["sample_rows_for_story_json"])
    write_csv(output_dir / SAMPLE_ROWS_FOR_STORY_CSV_FILE_NAME, artifacts["sample_rows_for_story_rows"])
    (output_dir / CLAIMS_ALLOWED_VS_FORBIDDEN_MD_FILE_NAME).write_text(
        artifacts["claims_allowed_vs_forbidden_md"], encoding="utf-8"
    )
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_md"], encoding="utf-8")
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(artifacts["next_plan_md"], encoding="utf-8")

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"generated_report_count: {manifest.get('generated_report_count', '')}")
    print(f"sample_rows_for_story_count: {manifest.get('sample_rows_for_story_count', '')}")
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
