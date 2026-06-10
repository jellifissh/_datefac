from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.mineru_pilot_network_recovery_342c6 import (  # noqa: E402
    DEFAULT_CORPUS_342B_DIR,
    DEFAULT_MINERU_342C2_DIR,
    DEFAULT_OUTPUT_DIR,
    build_mineru_pilot_network_recovery_342c6,
)
from datefac.benchmark.mineru_pilot_network_recovery_342c6_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342C6 MinerU pilot network recovery rerun.")
    parser.add_argument("--corpus-342b-dir", default=str(DEFAULT_CORPUS_342B_DIR))
    parser.add_argument("--mineru-342c2-dir", default=str(DEFAULT_MINERU_342C2_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--mineru-command", required=True)
    args = parser.parse_args()

    artifacts = build_mineru_pilot_network_recovery_342c6(
        corpus_342b_dir=Path(args.corpus_342b_dir),
        mineru_342c2_dir=Path(args.mineru_342c2_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
        mineru_command=args.mineru_command,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "mineru_pilot_network_recovery_342c6_summary.json"
    manifest_json = output_dir / "mineru_pilot_network_recovery_342c6_manifest.json"
    qa_json = output_dir / "mineru_pilot_network_recovery_342c6_qa.json"
    no_write_back_json = output_dir / "mineru_pilot_network_recovery_342c6_no_write_back_proof.json"
    report_md = output_dir / "mineru_pilot_network_recovery_342c6_report.md"
    workbook_xlsx = output_dir / "mineru_pilot_network_recovery_342c6.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"mineru_pilot_network_recovery_342c6_summary_json: {summary_json}")
    print(f"mineru_pilot_network_recovery_342c6_manifest_json: {manifest_json}")
    print(f"mineru_pilot_network_recovery_342c6_qa_json: {qa_json}")
    print(f"mineru_pilot_network_recovery_342c6_no_write_back_proof_json: {no_write_back_json}")
    print(f"mineru_pilot_network_recovery_342c6_report_md: {report_md}")
    print(f"mineru_pilot_network_recovery_342c6_xlsx: {workbook_xlsx}")
    for key in [
        "original_success_count",
        "original_failed_count",
        "rerun_target_count",
        "rerun_success_count",
        "rerun_failed_count",
        "final_success_count",
        "final_failed_count",
        "final_empty_output_count",
        "ready_for_342d",
        "recommended_342d_scope",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
