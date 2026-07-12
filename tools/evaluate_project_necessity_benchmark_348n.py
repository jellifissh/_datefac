from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datefac_agent.benchmark.project_necessity_benchmark_348n import (  # noqa: E402
    build_benchmark_summary,
    read_review_pack,
    write_summary_files,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate an R7CF completed ground-truth review pack.")
    parser.add_argument("--review-pack", default="output/benchmark/r7cf_anjing_foods_ground_truth_review_pack.xlsx")
    parser.add_argument("--summary-json", default="output/benchmark/r7cf_project_necessity_benchmark_summary.json")
    parser.add_argument("--summary-md", default="output/benchmark/r7cf_project_necessity_benchmark_summary.md")
    parser.add_argument("--candidate-report-package-count", type=int, default=0)
    parser.add_argument("--ready-report-package-count", type=int, default=0)
    args = parser.parse_args()

    rows = read_review_pack(args.review_pack)
    summary = build_benchmark_summary(
        rows,
        candidate_report_package_count=args.candidate_report_package_count,
        ready_report_package_count=args.ready_report_package_count,
    )
    json_path, markdown_path = write_summary_files(
        summary,
        json_path=args.summary_json,
        markdown_path=args.summary_md,
    )
    print(f"sampled_cell_count={summary['sampled_cell_count']}")
    print(f"verified_cell_count={summary['verified_cell_count']}")
    print(f"provisional_project_value_result={summary['provisional_project_value_result']}")
    print(f"summary_json={json_path}")
    print(f"summary_md={markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
