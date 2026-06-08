from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.human_unit_review_apply_simulation_330k3 import (  # noqa: E402
    DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR,
    DEFAULT_DEMO_PACKAGING_DIR,
    DEFAULT_FILLED_REVIEW_WORKBOOK,
    DEFAULT_HUMAN_UNIT_REVIEW_DIR,
    DEFAULT_OUTPUT_DIR,
    build_human_unit_review_apply_simulation_330k3,
)
from datefac.trust.human_unit_review_apply_simulation_330k3_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    human_unit_review_apply_simulation_330k3_markdown,
    write_excel,
    write_json,
)
from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330K3 human unit review apply simulation.")
    parser.add_argument("--filled-review-workbook", default=str(DEFAULT_FILLED_REVIEW_WORKBOOK))
    parser.add_argument("--human-unit-review-dir", default=str(DEFAULT_HUMAN_UNIT_REVIEW_DIR))
    parser.add_argument("--demo-packaging-dir", default=str(DEFAULT_DEMO_PACKAGING_DIR))
    parser.add_argument(
        "--client-style-export-preview-dir",
        default=str(DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    filled_review_workbook = Path(args.filled_review_workbook)
    human_unit_review_dir = Path(args.human_unit_review_dir)
    demo_packaging_dir = Path(args.demo_packaging_dir)
    client_style_export_preview_dir = Path(args.client_style_export_preview_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_human_unit_review_apply_simulation_330k3(
        filled_review_workbook=filled_review_workbook,
        human_unit_review_dir=human_unit_review_dir,
        demo_packaging_dir=demo_packaging_dir,
        client_style_export_preview_dir=client_style_export_preview_dir,
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(filled_review_workbook),
            str(human_unit_review_dir / "human_unit_review_330k2_summary.json"),
            str(demo_packaging_dir / "demo_packaging_331a_summary.json"),
            str(client_style_export_preview_dir / "client_style_export_preview_330l_summary.json"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "human_unit_review_apply_simulation_330k3_summary.json"
    manifest_json = output_dir / "human_unit_review_apply_simulation_330k3_manifest.json"
    qa_json = output_dir / "human_unit_review_apply_simulation_330k3_qa.json"
    no_apply_json = output_dir / "human_unit_review_apply_simulation_330k3_no_apply_proof.json"
    apply_plan_json = output_dir / "human_unit_review_apply_simulation_330k3_apply_plan.json"
    apply_plan_xlsx = output_dir / "human_unit_review_apply_simulation_330k3_apply_plan.xlsx"
    report_md = output_dir / "human_unit_review_apply_simulation_330k3_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_json(apply_plan_json, {"apply_plan": artifacts["apply_plan_json"]})
    write_excel(
        apply_plan_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "readme": artifacts["readme_df"],
            "apply_plan": artifacts["apply_plan_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(
        human_unit_review_apply_simulation_330k3_markdown(artifacts["summary"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"human_unit_review_apply_simulation_330k3_summary_json: {summary_json}")
    print(f"human_unit_review_apply_simulation_330k3_manifest_json: {manifest_json}")
    print(f"human_unit_review_apply_simulation_330k3_qa_json: {qa_json}")
    print(f"human_unit_review_apply_simulation_330k3_no_apply_proof_json: {no_apply_json}")
    print(f"human_unit_review_apply_simulation_330k3_apply_plan_json: {apply_plan_json}")
    print(f"human_unit_review_apply_simulation_330k3_apply_plan_xlsx: {apply_plan_xlsx}")
    print(f"human_unit_review_apply_simulation_330k3_report_md: {report_md}")
    for key in [
        "validated_330k2_review_package",
        "reviewed_row_count",
        "confirm_unit_count",
        "reject_unit_count",
        "needs_more_context_count",
        "keep_unit_unknown_count",
        "apply_plan_row_count",
        "no_official_asset_modification_during_330k3",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
