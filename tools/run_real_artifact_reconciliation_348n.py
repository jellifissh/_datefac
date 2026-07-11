from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datefac_agent.reconciliation.real_artifact_compatibility_348n import (  # noqa: E402
    load_and_reconcile_real_artifacts,
)


SUMMARY_KEYS = (
    "mineru_record_count",
    "original_record_count",
    "comparison_row_count",
    "match_count",
    "conflict_count",
    "mineru_only_count",
    "original_only_count",
    "unparseable_count",
    "unit_review_count",
    "review_required_count",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="R7CD demo-only real artifact reconciliation smoke.")
    parser.add_argument("--mineru-json", required=True)
    parser.add_argument("--original-xlsx", required=True)
    args = parser.parse_args()

    result = load_and_reconcile_real_artifacts(args.mineru_json, args.original_xlsx)
    summary = result["summary"]
    for key in SUMMARY_KEYS:
        print(f"{key}={summary[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
