from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datefac_agent.benchmark.project_necessity_benchmark_348n import (  # noqa: E402
    DEFAULT_INVENTORY_ROOTS,
    READY,
    build_one_report_review_pack_rows,
    inventory_report_packages,
    select_one_report_package,
    write_review_pack,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build R7CF one-report ground-truth review pack.")
    parser.add_argument("--output-xlsx", default="output/benchmark/r7cf_anjing_foods_ground_truth_review_pack.xlsx")
    parser.add_argument("--sample-size", type=int, default=30)
    parser.add_argument("--roots", nargs="*", default=list(DEFAULT_INVENTORY_ROOTS))
    args = parser.parse_args()

    candidates = inventory_report_packages(args.roots)
    selected_package = select_one_report_package(candidates)
    if selected_package is None:
        print("selected_report_package=NONE")
        print(f"candidate_report_package_count={len(candidates)}")
        print("ready_report_package_count=0")
        return 2

    rows = build_one_report_review_pack_rows(selected_package, sample_size=args.sample_size)
    output_path = write_review_pack(args.output_xlsx, rows)
    ready_count = 1 if selected_package is not None else 0
    print(f"candidate_report_package_count={len(candidates)}")
    print(f"ready_report_package_count={ready_count}")
    print(f"selected_report_id={selected_package.report_id}")
    print(f"sampled_cell_count={len(rows)}")
    print(f"review_pack_xlsx={output_path}")
    print("selected_package=" + json.dumps(selected_package.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
