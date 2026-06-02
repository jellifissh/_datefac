from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.router.recognizer_router_321f import RecognizerRouter321FConfig, run_recognizer_router_321f


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 321F recognizer router implementation benchmark.")
    parser.add_argument("--bakeoff-dir", required=True)
    parser.add_argument("--router-revision-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_recognizer_router_321f(
        RecognizerRouter321FConfig(
            bakeoff_dir=Path(args.bakeoff_dir),
            router_revision_dir=Path(args.router_revision_dir),
            output_dir=Path(args.output_dir),
        )
    )
    summary = result.get("summary", {})
    print(f"recognizer_router_321f_excel: {result.get('excel_path', '')}")
    print(f"recognizer_router_321f_summary_json: {result.get('summary_json_path', '')}")
    print(f"recognizer_router_321f_report_md: {result.get('report_md_path', '')}")
    print(f"router_plan_321f_json: {result.get('router_json_path', '')}")
    for key in [
        "route_total_count",
        "mineru_default_count",
        "structtable_default_count",
        "pure_vlm_adjudicator_count",
        "docling_backup_count",
        "ppstructure_fallback_count",
        "manual_review_count",
        "qa_fail_count",
        "router_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
