from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datefac.router.router_benchmark import RouterBenchmarkConfig, run_router_benchmark


def _path_or_none(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run 321C recognizer router planning benchmark.")
    parser.add_argument("--vlm-benchmark-dir", required=True)
    parser.add_argument("--vlm-quality-dir", required=False, default="")
    parser.add_argument("--ppstructure-benchmark-dir", required=False, default="")
    parser.add_argument("--mineru-benchmark-dir", required=False, default="")
    parser.add_argument("--mineru-output-root", required=True)
    parser.add_argument("--vlm-output-root", required=False, default="")
    parser.add_argument("--output-dir", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_router_benchmark(
        RouterBenchmarkConfig(
            vlm_benchmark_dir=_path_or_none(args.vlm_benchmark_dir),
            vlm_quality_dir=_path_or_none(args.vlm_quality_dir),
            ppstructure_benchmark_dir=_path_or_none(args.ppstructure_benchmark_dir),
            mineru_benchmark_dir=_path_or_none(args.mineru_benchmark_dir),
            mineru_output_root=Path(args.mineru_output_root),
            vlm_output_root=_path_or_none(args.vlm_output_root),
            output_dir=Path(args.output_dir),
        )
    )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
