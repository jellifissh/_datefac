from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402
from datefac.trust.reviewed_export_refresh_330k4 import (  # noqa: E402
    DEFAULT_APPLY_SIMULATION_DIR,
    DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR,
    DEFAULT_HUMAN_UNIT_REVIEW_DIR,
    DEFAULT_OUTPUT_DIR,
    build_reviewed_export_refresh_330k4,
)
from datefac.trust.reviewed_export_refresh_330k4_report import (  # noqa: E402
    WORKBOOK_SHEET_ORDER,
    reviewed_export_refresh_330k4_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330K4 reviewed export refresh.")
    parser.add_argument(
        "--client-style-export-preview-dir",
        default=str(DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR),
    )
    parser.add_argument("--human-unit-review-dir", default=str(DEFAULT_HUMAN_UNIT_REVIEW_DIR))
    parser.add_argument("--apply-simulation-dir", default=str(DEFAULT_APPLY_SIMULATION_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    client_style_export_preview_dir = Path(args.client_style_export_preview_dir)
    human_unit_review_dir = Path(args.human_unit_review_dir)
    apply_simulation_dir = Path(args.apply_simulation_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_reviewed_export_refresh_330k4(
        client_style_export_preview_dir=client_style_export_preview_dir,
        human_unit_review_dir=human_unit_review_dir,
        apply_simulation_dir=apply_simulation_dir,
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(client_style_export_preview_dir / "client_style_export_preview_330l_summary.json"),
            str(client_style_export_preview_dir / "client_style_export_preview_330l_preview.xlsx"),
            str(human_unit_review_dir / "human_unit_review_330k2_summary.json"),
            str(human_unit_review_dir / "human_unit_review_330k2_review_filled.xlsx"),
            str(apply_simulation_dir / "human_unit_review_apply_simulation_330k3_summary.json"),
            str(apply_simulation_dir / "human_unit_review_apply_simulation_330k3_apply_plan.json"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "reviewed_export_refresh_330k4_summary.json"
    manifest_json = output_dir / "reviewed_export_refresh_330k4_manifest.json"
    qa_json = output_dir / "reviewed_export_refresh_330k4_qa.json"
    no_apply_json = output_dir / "reviewed_export_refresh_330k4_no_apply_proof.json"
    preview_xlsx = output_dir / "reviewed_export_refresh_330k4_preview.xlsx"
    report_md = output_dir / "reviewed_export_refresh_330k4_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        preview_xlsx,
        {
            "00_README": artifacts["readme_df"],
            "01_REVIEWED_TRUSTED_PREVIEW": artifacts["reviewed_trusted_preview_df"],
            "02_REMAINING_REVIEW_REQUIRED": artifacts["remaining_review_required_df"],
            "03_HUMAN_REJECTED_BY_UNIT_REV": artifacts["human_rejected_df"],
            "04_APPLY_PLAN_TRACE": artifacts["apply_plan_trace_df"],
            "05_QA_CONTEXT": artifacts["qa_context_df"],
        },
    )
    report_md.write_text(
        reviewed_export_refresh_330k4_markdown(artifacts["summary"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"reviewed_export_refresh_330k4_summary_json: {summary_json}")
    print(f"reviewed_export_refresh_330k4_manifest_json: {manifest_json}")
    print(f"reviewed_export_refresh_330k4_qa_json: {qa_json}")
    print(f"reviewed_export_refresh_330k4_no_apply_proof_json: {no_apply_json}")
    print(f"reviewed_export_refresh_330k4_preview_xlsx: {preview_xlsx}")
    print(f"reviewed_export_refresh_330k4_report_md: {report_md}")
    for key in [
        "validated_330l_preview",
        "validated_330k3_apply_simulation",
        "original_trusted_sheet_row_count",
        "reviewed_unit_confirmed_count",
        "human_rejected_row_count",
        "remaining_review_required_after_unit_review_count",
        "reviewed_trusted_preview_row_count",
        "duplicate_confirmed_candidate_overlap_count",
        "apply_plan_row_count",
        "no_official_asset_modification_during_330k4",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
