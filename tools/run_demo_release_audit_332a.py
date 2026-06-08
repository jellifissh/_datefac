from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.demo_release_audit_332a import (  # noqa: E402
    DEFAULT_DEMO_PACKAGING_331A_DIR,
    DEFAULT_DEMO_PACKAGING_331B_DIR,
    DEFAULT_DOCS_DEMO_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_EXPORT_REFRESH_DIR,
    build_demo_release_audit_332a,
)
from datefac.trust.demo_release_audit_332a_report import write_json  # noqa: E402
from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 332A demo release audit.")
    parser.add_argument("--demo-packaging-331b-dir", default=str(DEFAULT_DEMO_PACKAGING_331B_DIR))
    parser.add_argument("--reviewed-export-refresh-dir", default=str(DEFAULT_REVIEWED_EXPORT_REFRESH_DIR))
    parser.add_argument("--demo-packaging-331a-dir", default=str(DEFAULT_DEMO_PACKAGING_331A_DIR))
    parser.add_argument("--docs-demo-dir", default=str(DEFAULT_DOCS_DEMO_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    demo_packaging_331b_dir = Path(args.demo_packaging_331b_dir)
    reviewed_export_refresh_dir = Path(args.reviewed_export_refresh_dir)
    demo_packaging_331a_dir = Path(args.demo_packaging_331a_dir)
    docs_demo_dir = Path(args.docs_demo_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_demo_release_audit_332a(
        demo_packaging_331b_dir=demo_packaging_331b_dir,
        reviewed_export_refresh_dir=reviewed_export_refresh_dir,
        demo_packaging_331a_dir=demo_packaging_331a_dir,
        docs_demo_dir=docs_demo_dir,
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(demo_packaging_331b_dir / "demo_packaging_331b_summary.json"),
            str(reviewed_export_refresh_dir / "reviewed_export_refresh_330k4_summary.json"),
            str(demo_packaging_331a_dir / "demo_packaging_331a_summary.json"),
            str(docs_demo_dir / "datefac_demo_overview_331b.md"),
            str(docs_demo_dir / "datefac_resume_bullets_331b.md"),
            str(docs_demo_dir / "datefac_github_readme_section_331b.md"),
            str(docs_demo_dir / "datefac_demo_script_331b.md"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "demo_release_audit_332a_summary.json"
    manifest_json = output_dir / "demo_release_audit_332a_manifest.json"
    qa_json = output_dir / "demo_release_audit_332a_qa.json"
    no_apply_json = output_dir / "demo_release_audit_332a_no_apply_proof.json"
    checklist_md = output_dir / "demo_release_audit_332a_checklist.md"
    report_md = output_dir / "demo_release_audit_332a_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    checklist_md.write_text(artifacts["checklist_md"], encoding="utf-8")
    report_md.write_text(artifacts["report_md"], encoding="utf-8")

    summary = artifacts["summary"]
    print(f"demo_release_audit_332a_summary_json: {summary_json}")
    print(f"demo_release_audit_332a_manifest_json: {manifest_json}")
    print(f"demo_release_audit_332a_qa_json: {qa_json}")
    print(f"demo_release_audit_332a_no_apply_proof_json: {no_apply_json}")
    print(f"demo_release_audit_332a_checklist_md: {checklist_md}")
    print(f"demo_release_audit_332a_report_md: {report_md}")
    for key in [
        "validated_331b_demo_packaging",
        "validated_330k4_reviewed_export_refresh",
        "validated_331a_demo_packaging",
        "project_status",
        "client_ready",
        "production_ready",
        "reviewed_trusted_preview_row_count",
        "human_rejected_row_count",
        "remaining_review_required_after_unit_review_count",
        "apply_plan_row_count",
        "doc_consistency_passed",
        "overclaim_risk_count",
        "no_official_asset_modification_during_332a",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
