from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402
from datefac.trust.unfamiliar_output_preparation_330f2 import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PREPARED_OUTPUT_DIR,
    build_unfamiliar_output_preparation_330f2,
)
from datefac.trust.unfamiliar_output_preparation_330f2_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    unfamiliar_output_preparation_330f2_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330F2 unfamiliar output preparation.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--prepared-output-dir", default=str(DEFAULT_PREPARED_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    prepared_output_dir = Path(args.prepared_output_dir)

    artifacts = build_unfamiliar_output_preparation_330f2(
        output_dir=output_dir,
        prepared_output_dir=prepared_output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            r"D:\_datefac\input",
            r"D:\_datefac\input\unfamiliar",
            r"D:\_datefac\output",
            r"D:\_datefac\output\router_mineru_trust_split_322b2",
            r"D:\_datefac\output\delivery",
            r"D:\_datefac\output\batch_outputs",
            r"D:\_datefac\output\mineru_outputs",
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "unfamiliar_output_preparation_330f2_summary.json"
    qa_json = output_dir / "unfamiliar_output_preparation_330f2_qa.json"
    no_apply_json = output_dir / "unfamiliar_output_preparation_330f2_no_apply_proof.json"
    summary_xlsx = output_dir / "unfamiliar_output_preparation_330f2_summary.xlsx"
    report_md = output_dir / "unfamiliar_output_preparation_330f2_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "unfamiliar_inputs": artifacts["unfamiliar_inputs_df"],
            "cached_matches": artifacts["cached_matches_df"],
            "prepared_candidate_rows": artifacts["prepared_candidate_rows_df"],
            "recommendation": artifacts["recommendation_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(unfamiliar_output_preparation_330f2_markdown(artifacts["summary"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"unfamiliar_output_preparation_330f2_summary_json: {summary_json}")
    print(f"unfamiliar_output_preparation_330f2_qa_json: {qa_json}")
    print(f"unfamiliar_output_preparation_330f2_no_apply_proof_json: {no_apply_json}")
    print(f"unfamiliar_output_preparation_330f2_summary_xlsx: {summary_xlsx}")
    print(f"unfamiliar_output_preparation_330f2_report_md: {report_md}")
    for key in [
        "unfamiliar_output_preparation_status",
        "discovered_unfamiliar_input_pdf_count",
        "matched_cached_output_count",
        "prepared_candidate_row_count",
        "can_rerun_330f",
        "no_official_asset_modification_during_330f2",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
