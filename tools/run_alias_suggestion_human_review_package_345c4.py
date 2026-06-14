from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.alias_suggestion_human_review_package_345c4 import (  # noqa: E402
    ARTIFACT_INDEX_FILE_NAME,
    DECISION_OPTIONS_FILE_NAME,
    DEFAULT_345C2_LIVE_DIR,
    DEFAULT_OUTPUT_DIR,
    EXECUTIVE_SUMMARY_FILE_NAME,
    LLM_SUGGESTION_SUMMARY_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_FILE_NAME,
    PRIORITY_SUMMARY_FILE_NAME,
    REVIEW_ROWS_CSV_FILE_NAME,
    REVIEW_ROWS_JSON_FILE_NAME,
    REVIEW_ROW_FIELDS,
    REVIEWER_CHECKLIST_FILE_NAME,
    WORKBOOK_FILE_NAME,
    WORKBOOK_SHEETS,
    build_alias_suggestion_human_review_package_345c4,
)
from datefac.benchmark.alias_suggestion_human_review_package_345c4_report import (  # noqa: E402
    artifact_index_markdown,
    decision_options_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    reviewer_checklist_markdown,
    write_csv,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 345C4 alias suggestion human review package."
    )
    parser.add_argument(
        "--llm-assisted-metric-alias-adjudication-345c2-live-dir",
        default=str(DEFAULT_345C2_LIVE_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_alias_suggestion_human_review_package_345c4(
        llm_assisted_metric_alias_adjudication_345c2_live_dir=Path(
            args.llm_assisted_metric_alias_adjudication_345c2_live_dir
        ),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / REVIEW_ROWS_JSON_FILE_NAME, artifacts["review_rows"])
    write_csv(output_dir / REVIEW_ROWS_CSV_FILE_NAME, artifacts["review_rows"], REVIEW_ROW_FIELDS)
    write_json(
        output_dir / LLM_SUGGESTION_SUMMARY_FILE_NAME,
        artifacts["llm_suggestion_summary"],
    )
    write_json(
        output_dir / PRIORITY_SUMMARY_FILE_NAME,
        artifacts["priority_summary"],
    )
    write_excel(output_dir / WORKBOOK_FILE_NAME, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    (output_dir / REVIEWER_CHECKLIST_FILE_NAME).write_text(
        reviewer_checklist_markdown(artifacts["manifest"]),
        encoding="utf-8",
    )
    (output_dir / DECISION_OPTIONS_FILE_NAME).write_text(
        decision_options_markdown(),
        encoding="utf-8",
    )
    (output_dir / EXECUTIVE_SUMMARY_FILE_NAME).write_text(
        executive_summary_markdown(artifacts["manifest"]),
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_FILE_NAME).write_text(
        artifact_index_markdown(artifacts["artifact_index_rows"]),
        encoding="utf-8",
    )
    (output_dir / NEXT_PLAN_FILE_NAME).write_text(
        next_plan_markdown(),
        encoding="utf-8",
    )

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"workbook: {output_dir / WORKBOOK_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"input_345c2_decision: {manifest.get('input_345c2_decision', '')}")
    print(f"input_llm_mode: {manifest.get('input_llm_mode', '')}")
    print(f"review_row_count: {manifest.get('review_row_count', '')}")
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
