from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402
from datefac.trust.unfamiliar_candidate_export_smoke_330f4 import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PREPARED_OUTPUT_DIR,
    DEFAULT_PREVIOUS_330F3_DIR,
    DEFAULT_UNFAMILIAR_INPUT_DIR,
    build_unfamiliar_candidate_export_smoke_330f4,
)
from datefac.trust.unfamiliar_candidate_export_smoke_330f4_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    unfamiliar_candidate_export_smoke_330f4_markdown,
    write_excel,
    write_json,
)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330F4 unfamiliar candidate export smoke.")
    parser.add_argument("--unfamiliar-input-dir", default=str(DEFAULT_UNFAMILIAR_INPUT_DIR))
    parser.add_argument("--prepared-output-dir", default=str(DEFAULT_PREPARED_OUTPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    unfamiliar_input_dir = Path(args.unfamiliar_input_dir)
    prepared_output_dir = Path(args.prepared_output_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_unfamiliar_candidate_export_smoke_330f4(
        unfamiliar_input_dir=unfamiliar_input_dir,
        previous_330f3_dir=DEFAULT_PREVIOUS_330F3_DIR,
        prepared_output_dir=prepared_output_dir,
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(DEFAULT_PREVIOUS_330F3_DIR / "unfamiliar_candidate_output_generation_330f3_summary.json"),
            str(unfamiliar_input_dir),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "unfamiliar_candidate_export_smoke_330f4_summary.json"
    qa_json = output_dir / "unfamiliar_candidate_export_smoke_330f4_qa.json"
    no_apply_json = output_dir / "unfamiliar_candidate_export_smoke_330f4_no_apply_proof.json"
    manifest_json = output_dir / "unfamiliar_candidate_export_smoke_330f4_manifest.json"
    summary_xlsx = output_dir / "unfamiliar_candidate_export_smoke_330f4_summary.xlsx"
    report_md = output_dir / "unfamiliar_candidate_export_smoke_330f4_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_json(manifest_json, artifacts["manifest_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "scan_inventory": artifacts["scan_df"],
            "prepared_candidate_rows": artifacts["prepared_df"],
            "missing_field_counts": artifacts["missing_field_counts_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(unfamiliar_candidate_export_smoke_330f4_markdown(artifacts["summary"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"unfamiliar_candidate_export_smoke_330f4_summary_json: {summary_json}")
    print(f"unfamiliar_candidate_export_smoke_330f4_qa_json: {qa_json}")
    print(f"unfamiliar_candidate_export_smoke_330f4_no_apply_proof_json: {no_apply_json}")
    print(f"unfamiliar_candidate_export_smoke_330f4_manifest_json: {manifest_json}")
    print(f"unfamiliar_candidate_export_smoke_330f4_summary_xlsx: {summary_xlsx}")
    print(f"unfamiliar_candidate_export_smoke_330f4_report_md: {report_md}")
    for key in [
        "selected_pdf_count",
        "selected_pdfs",
        "processed_pdf_count",
        "prepared_candidate_row_count",
        "can_rerun_330f",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
