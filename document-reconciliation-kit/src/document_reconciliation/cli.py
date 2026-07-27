"""Console interface for deterministic document reconciliation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .adapters.excel import load_excel_records
from .adapters.mineru import extract_mineru_records
from .benchmark import read_review_pack, write_benchmark_summary
from .discrepancy import write_review_report
from .models import NormalizedRecord
from .reconciliation import reconcile_records


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "compare":
            return _compare(args)
        if args.command == "report":
            return _report(args)
        if args.command == "benchmark":
            return _benchmark(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="doc-reconcile", description="Compare structured document outputs safely.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    compare = subcommands.add_parser("compare", help="compare MinerU JSON with Excel or normalized JSON")
    compare.add_argument("--left", required=True, help="MinerU content_list_v2 JSON")
    compare.add_argument("--right", required=True, help="Excel workbook or normalized JSON records")
    compare.add_argument("--output", required=True, help="new comparison JSON path")
    report = subcommands.add_parser("report", help="render compact JSON and Markdown discrepancy reports")
    report.add_argument("--comparison", required=True, help="comparison JSON produced by compare")
    report.add_argument("--output-dir", required=True, help="new empty report directory")
    benchmark = subcommands.add_parser("benchmark", help="evaluate a manually reviewed benchmark pack")
    benchmark.add_argument("--review-pack", required=True, help="reviewed benchmark workbook")
    benchmark.add_argument("--output-dir", required=True, help="new empty summary directory")
    return parser


def _compare(args: argparse.Namespace) -> int:
    left_path = _required_file(args.left)
    right_path = _required_file(args.right)
    output_path = Path(args.output)
    _ensure_new_output_file(output_path)
    left_payload = json.loads(left_path.read_text(encoding="utf-8"))
    left_records = extract_mineru_records(left_payload, source="left")
    right_records = load_excel_records(right_path, source="right") if right_path.suffix.casefold() in {".xlsx", ".xlsm", ".xls"} else _normalized_json_records(right_path, source="right")
    result = reconcile_records(left_records, right_records)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"comparison_row_count={result['summary']['comparison_row_count']}")
    print(f"review_required_count={result['summary']['review_required_count']}")
    print(f"output={output_path}")
    return 0


def _report(args: argparse.Namespace) -> int:
    comparison_path = _required_file(args.comparison)
    payload = json.loads(comparison_path.read_text(encoding="utf-8"))
    rows = payload.get("comparison_rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("comparison JSON must contain a comparison_rows list")
    paths = write_review_report(rows, args.output_dir)
    print(f"report_json={paths['json_path']}")
    print(f"report_markdown={paths['markdown_path']}")
    return 0


def _benchmark(args: argparse.Namespace) -> int:
    review_pack = _required_file(args.review_pack)
    paths = write_benchmark_summary(read_review_pack(review_pack), args.output_dir)
    print(f"benchmark_json={paths['json_path']}")
    print(f"benchmark_markdown={paths['markdown_path']}")
    return 0


def _required_file(value: str) -> Path:
    path = Path(value)
    if not path.is_file():
        raise ValueError(f"missing input file: {path}")
    return path


def _ensure_new_output_file(path: Path) -> None:
    if path.exists():
        raise ValueError(f"output file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)


def _normalized_json_records(path: Path, *, source: str) -> list[NormalizedRecord]:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    values = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(values, list):
        raise ValueError("normalized JSON input must be a record list or contain a records list")
    records: list[NormalizedRecord] = []
    for value in values:
        if not isinstance(value, dict):
            raise ValueError("normalized JSON record must be an object")
        record_value = dict(value)
        record_value.setdefault("source", source)
        records.append(NormalizedRecord.from_mapping(record_value))
    return records


if __name__ == "__main__":
    raise SystemExit(main())
