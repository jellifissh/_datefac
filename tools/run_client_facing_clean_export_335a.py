from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.client_facing_clean_export_335a import (  # noqa: E402
    CUSTOMER_SHEETS,
    DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR,
    DEFAULT_DEMO_PACKAGING_331B_DIR,
    DEFAULT_DEMO_RELEASE_AUDIT_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REVIEWED_EXPORT_REFRESH_DIR,
    build_client_facing_clean_export_335a,
)
from datefac.trust.client_facing_clean_export_335a_report import (  # noqa: E402
    client_facing_clean_export_335a_markdown,
    write_excel,
    write_json,
)
from datefac.trust.no_apply_proof import (  # noqa: E402
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 335A client-facing clean export.")
    parser.add_argument(
        "--reviewed-export-refresh-dir",
        default=str(DEFAULT_REVIEWED_EXPORT_REFRESH_DIR),
    )
    parser.add_argument(
        "--demo-packaging-331b-dir",
        default=str(DEFAULT_DEMO_PACKAGING_331B_DIR),
    )
    parser.add_argument(
        "--demo-release-audit-dir",
        default=str(DEFAULT_DEMO_RELEASE_AUDIT_DIR),
    )
    parser.add_argument(
        "--client-style-export-preview-dir",
        default=str(DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    reviewed_export_refresh_dir = Path(args.reviewed_export_refresh_dir)
    demo_packaging_331b_dir = Path(args.demo_packaging_331b_dir)
    demo_release_audit_dir = Path(args.demo_release_audit_dir)
    client_style_export_preview_dir = Path(args.client_style_export_preview_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_client_facing_clean_export_335a(
        reviewed_export_refresh_dir=reviewed_export_refresh_dir,
        demo_packaging_331b_dir=demo_packaging_331b_dir,
        demo_release_audit_dir=demo_release_audit_dir,
        client_style_export_preview_dir=client_style_export_preview_dir,
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(reviewed_export_refresh_dir / "reviewed_export_refresh_330k4_summary.json"),
            str(reviewed_export_refresh_dir / "reviewed_export_refresh_330k4_qa.json"),
            str(reviewed_export_refresh_dir / "reviewed_export_refresh_330k4_preview.xlsx"),
            str(demo_packaging_331b_dir / "demo_packaging_331b_summary.json"),
            str(demo_release_audit_dir / "demo_release_audit_332a_summary.json"),
            str(client_style_export_preview_dir / "client_style_export_preview_330l_summary.json"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "client_facing_clean_export_335a_summary.json"
    manifest_json = output_dir / "client_facing_clean_export_335a_manifest.json"
    qa_json = output_dir / "client_facing_clean_export_335a_qa.json"
    no_apply_json = output_dir / "client_facing_clean_export_335a_no_apply_proof.json"
    preview_xlsx = output_dir / "client_facing_clean_export_335a_preview.xlsx"
    report_md = output_dir / "client_facing_clean_export_335a_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        preview_xlsx,
        {
            CUSTOMER_SHEETS["readme"]: artifacts["customer_readme_df"],
            CUSTOMER_SHEETS["reviewed"]: artifacts["core_metrics_reviewed_df"],
            CUSTOMER_SHEETS["needs_review"]: artifacts["needs_review_df"],
            CUSTOMER_SHEETS["rejected"]: artifacts["excluded_or_rejected_df"],
            CUSTOMER_SHEETS["trace"]: artifacts["source_trace_df"],
            CUSTOMER_SHEETS["summary"]: artifacts["delivery_summary_df"],
        },
    )
    report_md.write_text(
        client_facing_clean_export_335a_markdown(artifacts["summary"]),
        encoding="utf-8",
    )

    summary = artifacts["summary"]
    print(f"client_facing_clean_export_335a_summary_json: {summary_json}")
    print(f"client_facing_clean_export_335a_manifest_json: {manifest_json}")
    print(f"client_facing_clean_export_335a_qa_json: {qa_json}")
    print(f"client_facing_clean_export_335a_no_apply_proof_json: {no_apply_json}")
    print(f"client_facing_clean_export_335a_preview_xlsx: {preview_xlsx}")
    print(f"client_facing_clean_export_335a_report_md: {report_md}")
    for key in [
        "project_status",
        "client_facing_preview",
        "client_ready",
        "production_ready",
        "source_reviewed_trusted_preview_row_count",
        "core_metrics_reviewed_row_count",
        "needs_review_row_count",
        "excluded_or_rejected_row_count",
        "source_page_missing_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
