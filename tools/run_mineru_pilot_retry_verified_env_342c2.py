from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.mineru_pilot_retry_verified_env_342c2 import (  # noqa: E402
    DEFAULT_CORPUS_342B_DIR,
    DEFAULT_MINERU_342C_DIR,
    DEFAULT_MINERU_CONFIG_PATH,
    DEFAULT_MODEL_CACHE_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_WORKING_LAB_DIR,
    build_mineru_pilot_retry_verified_env_342c2,
)
from datefac.benchmark.mineru_pilot_retry_verified_env_342c2_report import (  # noqa: E402
    WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 342C2 MinerU pilot retry with verified local environment.")
    parser.add_argument("--corpus-342b-dir", default=str(DEFAULT_CORPUS_342B_DIR))
    parser.add_argument("--mineru-342c-dir", default=str(DEFAULT_MINERU_342C_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--mineru-command", default="mineru")
    parser.add_argument("--working-lab-dir", default=str(DEFAULT_WORKING_LAB_DIR))
    parser.add_argument("--model-cache-dir", default=str(DEFAULT_MODEL_CACHE_DIR))
    parser.add_argument("--mineru-config-path", default=str(DEFAULT_MINERU_CONFIG_PATH))
    args = parser.parse_args()

    artifacts = build_mineru_pilot_retry_verified_env_342c2(
        corpus_342b_dir=Path(args.corpus_342b_dir),
        mineru_342c_dir=Path(args.mineru_342c_dir),
        output_dir=Path(args.output_dir),
        repo_root=PROJECT_ROOT,
        mineru_command=args.mineru_command,
        limit=args.limit if args.limit and args.limit > 0 else None,
        working_lab_dir=Path(args.working_lab_dir),
        model_cache_dir=Path(args.model_cache_dir),
        mineru_config_path=Path(args.mineru_config_path) if args.mineru_config_path else None,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "mineru_pilot_retry_verified_env_342c2_summary.json"
    manifest_json = output_dir / "mineru_pilot_retry_verified_env_342c2_manifest.json"
    qa_json = output_dir / "mineru_pilot_retry_verified_env_342c2_qa.json"
    no_write_back_json = output_dir / "mineru_pilot_retry_verified_env_342c2_no_write_back_proof.json"
    report_md = output_dir / "mineru_pilot_retry_verified_env_342c2_report.md"
    workbook_xlsx = output_dir / "mineru_pilot_retry_verified_env_342c2.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_write_back_json, artifacts["no_write_back_proof_json"])
    write_excel(workbook_xlsx, artifacts["workbook_sheets"], WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"mineru_pilot_retry_verified_env_342c2_summary_json: {summary_json}")
    print(f"mineru_pilot_retry_verified_env_342c2_manifest_json: {manifest_json}")
    print(f"mineru_pilot_retry_verified_env_342c2_qa_json: {qa_json}")
    print(f"mineru_pilot_retry_verified_env_342c2_no_write_back_proof_json: {no_write_back_json}")
    print(f"mineru_pilot_retry_verified_env_342c2_report_md: {report_md}")
    print(f"mineru_pilot_retry_verified_env_342c2_xlsx: {workbook_xlsx}")
    for key in [
        "retry_pilot_total_count",
        "retry_mineru_success_count",
        "retry_mineru_failed_count",
        "empty_output_count",
        "ready_for_342d",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
