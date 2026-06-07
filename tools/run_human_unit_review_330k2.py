from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.human_unit_review_330k2 import (  # noqa: E402
    DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR,
    DEFAULT_DELIVERY_REPORT_REFRESH_DIR,
    DEFAULT_DEMO_PACKAGING_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_UNIT_SIGNAL_REVIEW_DIR,
    build_human_unit_review_330k2,
)
from datefac.trust.human_unit_review_330k2_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    human_unit_review_330k2_markdown,
    write_excel,
    write_json,
)
from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330K2 human unit review packaging.")
    parser.add_argument("--demo-packaging-dir", default=str(DEFAULT_DEMO_PACKAGING_DIR))
    parser.add_argument(
        "--client-style-export-preview-dir",
        default=str(DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR),
    )
    parser.add_argument("--unit-signal-review-dir", default=str(DEFAULT_UNIT_SIGNAL_REVIEW_DIR))
    parser.add_argument(
        "--delivery-report-refresh-dir",
        default=str(DEFAULT_DELIVERY_REPORT_REFRESH_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    demo_packaging_dir = Path(args.demo_packaging_dir)
    client_style_export_preview_dir = Path(args.client_style_export_preview_dir)
    unit_signal_review_dir = Path(args.unit_signal_review_dir)
    delivery_report_refresh_dir = Path(args.delivery_report_refresh_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_human_unit_review_330k2(
        demo_packaging_dir=demo_packaging_dir,
        client_style_export_preview_dir=client_style_export_preview_dir,
        unit_signal_review_dir=unit_signal_review_dir,
        delivery_report_refresh_dir=delivery_report_refresh_dir,
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(demo_packaging_dir / "demo_packaging_331a_summary.json"),
            str(client_style_export_preview_dir / "client_style_export_preview_330l_summary.json"),
            str(client_style_export_preview_dir / "client_style_export_preview_330l_preview.xlsx"),
            str(unit_signal_review_dir / "unit_signal_review_330k_summary.json"),
            str(delivery_report_refresh_dir / "delivery_report_refresh_after_330k_330j2_summary.json"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "human_unit_review_330k2_summary.json"
    manifest_json = output_dir / "human_unit_review_330k2_manifest.json"
    qa_json = output_dir / "human_unit_review_330k2_qa.json"
    no_apply_json = output_dir / "human_unit_review_330k2_no_apply_proof.json"
    summary_xlsx = output_dir / "human_unit_review_330k2_summary.xlsx"
    report_md = output_dir / "human_unit_review_330k2_report.md"

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
            "readme": artifacts["readme_df"],
            "review_queue": artifacts["review_queue_df"],
            "upstream_context": artifacts["context_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(human_unit_review_330k2_markdown(artifacts["summary"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"human_unit_review_330k2_summary_json: {summary_json}")
    print(f"human_unit_review_330k2_manifest_json: {manifest_json}")
    print(f"human_unit_review_330k2_qa_json: {qa_json}")
    print(f"human_unit_review_330k2_no_apply_proof_json: {no_apply_json}")
    print(f"human_unit_review_330k2_summary_xlsx: {summary_xlsx}")
    print(f"human_unit_review_330k2_report_md: {report_md}")
    print(f"human_unit_review_330k2_review_template_xlsx: {summary.get('review_template_workbook_path', '')}")
    for key in [
        "validated_330l_export_preview",
        "validated_331a_demo_packaging",
        "packaged_unit_review_row_count",
        "review_template_workbook_generated",
        "source_page_missing_count",
        "unit_missing_count",
        "unit_conflict_risk_count",
        "no_official_asset_modification_during_330k2",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
