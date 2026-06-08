from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.demo_packaging_331b import (  # noqa: E402
    DEFAULT_APPLY_SIMULATION_DIR,
    DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR,
    DEFAULT_DEMO_PACKAGING_331A_DIR,
    DEFAULT_DOCS_DIR,
    DEFAULT_HUMAN_UNIT_REVIEW_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_EXPORT_REFRESH_DIR,
    build_demo_packaging_331b,
)
from datefac.trust.demo_packaging_331b_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    demo_packaging_331b_markdown,
    write_excel,
    write_json,
)
from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 331B demo packaging refresh.")
    parser.add_argument(
        "--demo-packaging-331a-dir",
        default=str(DEFAULT_DEMO_PACKAGING_331A_DIR),
    )
    parser.add_argument(
        "--reviewed-export-refresh-dir",
        default=str(DEFAULT_REVIEWED_EXPORT_REFRESH_DIR),
    )
    parser.add_argument("--apply-simulation-dir", default=str(DEFAULT_APPLY_SIMULATION_DIR))
    parser.add_argument("--human-unit-review-dir", default=str(DEFAULT_HUMAN_UNIT_REVIEW_DIR))
    parser.add_argument(
        "--client-style-export-preview-dir",
        default=str(DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--docs-dir", default=str(DEFAULT_DOCS_DIR))
    args = parser.parse_args()

    demo_packaging_331a_dir = Path(args.demo_packaging_331a_dir)
    reviewed_export_refresh_dir = Path(args.reviewed_export_refresh_dir)
    apply_simulation_dir = Path(args.apply_simulation_dir)
    human_unit_review_dir = Path(args.human_unit_review_dir)
    client_style_export_preview_dir = Path(args.client_style_export_preview_dir)
    output_dir = Path(args.output_dir)
    docs_dir = Path(args.docs_dir)

    artifacts = build_demo_packaging_331b(
        demo_packaging_331a_dir=demo_packaging_331a_dir,
        reviewed_export_refresh_dir=reviewed_export_refresh_dir,
        apply_simulation_dir=apply_simulation_dir,
        human_unit_review_dir=human_unit_review_dir,
        client_style_export_preview_dir=client_style_export_preview_dir,
        output_dir=output_dir,
        docs_dir=docs_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(demo_packaging_331a_dir / "demo_packaging_331a_summary.json"),
            str(reviewed_export_refresh_dir / "reviewed_export_refresh_330k4_summary.json"),
            str(apply_simulation_dir / "human_unit_review_apply_simulation_330k3_summary.json"),
            str(human_unit_review_dir / "human_unit_review_330k2_summary.json"),
            str(client_style_export_preview_dir / "client_style_export_preview_330l_summary.json"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "demo_packaging_331b_summary.json"
    manifest_json = output_dir / "demo_packaging_331b_manifest.json"
    qa_json = output_dir / "demo_packaging_331b_qa.json"
    no_apply_json = output_dir / "demo_packaging_331b_no_apply_proof.json"
    summary_xlsx = output_dir / "demo_packaging_331b_summary.xlsx"
    report_md = output_dir / "demo_packaging_331b_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "packaging_metrics": artifacts["packaging_metrics_df"],
            "docs_manifest": artifacts["docs_manifest_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(demo_packaging_331b_markdown(artifacts["summary"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"demo_packaging_331b_summary_json: {summary_json}")
    print(f"demo_packaging_331b_manifest_json: {manifest_json}")
    print(f"demo_packaging_331b_qa_json: {qa_json}")
    print(f"demo_packaging_331b_no_apply_proof_json: {no_apply_json}")
    print(f"demo_packaging_331b_summary_xlsx: {summary_xlsx}")
    print(f"demo_packaging_331b_report_md: {report_md}")
    for key in [
        "validated_331a_demo_packaging",
        "validated_330k4_reviewed_export_refresh",
        "project_status",
        "client_ready",
        "production_ready",
        "original_trusted_sheet_row_count",
        "reviewed_unit_confirmed_count",
        "reviewed_trusted_preview_row_count",
        "human_rejected_row_count",
        "remaining_review_required_after_unit_review_count",
        "apply_plan_row_count",
        "project_brief_generated",
        "resume_bullets_generated",
        "github_readme_section_generated",
        "demo_script_generated",
        "no_official_asset_modification_during_331b",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
