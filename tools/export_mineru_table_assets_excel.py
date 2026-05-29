from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.parser.mineru_output_reader import read_mineru_output


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    s = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _build_dataframes(result: Any) -> Dict[str, pd.DataFrame]:
    table_assets_rows = [a.to_dict() for a in result.table_assets]
    warnings_rows = [w.to_dict() for w in result.warnings]
    source_files_rows = [s.to_dict() for s in result.source_files]

    table_assets_df = pd.DataFrame(table_assets_rows)
    if table_assets_df.empty:
        table_assets_df = pd.DataFrame(
            columns=[
                "source_root",
                "source_file",
                "source_kind",
                "block_index",
                "page_idx",
                "bbox",
                "image_path",
                "caption",
                "footnote",
                "nearby_text",
                "table_role_guess",
                "table_role_reason",
                "raw_block_type",
                "raw_block_id",
                "source_doc_id",
                "extra",
            ]
        )

    warnings_df = pd.DataFrame(warnings_rows)
    if warnings_df.empty:
        warnings_df = pd.DataFrame(columns=["source_file", "warning_code", "warning_message", "block_index", "block_id"])

    source_files_df = pd.DataFrame(source_files_rows)
    if source_files_df.empty:
        source_files_df = pd.DataFrame(columns=["source_file", "source_kind", "file_exists", "file_size", "related_images_dir", "notes"])

    role_counts_df = (
        table_assets_df.groupby("table_role_guess", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    if role_counts_df.empty:
        role_counts_df = pd.DataFrame(columns=["table_role_guess", "count"])

    summary = result.summary()
    summary_rows = [
        {"metric": "source_root", "value": summary.get("source_root", "")},
        {"metric": "table_asset_count", "value": summary.get("table_asset_count", 0)},
        {"metric": "warning_count", "value": summary.get("warning_count", 0)},
        {"metric": "source_file_count", "value": summary.get("source_file_count", 0)},
        {"metric": "content_list_file_count", "value": int((source_files_df["source_kind"] == "content_list").sum()) if "source_kind" in source_files_df.columns else 0},
        {"metric": "content_list_v2_file_count", "value": int((source_files_df["source_kind"] == "content_list_v2").sum()) if "source_kind" in source_files_df.columns else 0},
        {"metric": "markdown_file_count", "value": int((source_files_df["source_kind"] == "markdown").sum()) if "source_kind" in source_files_df.columns else 0},
        {"metric": "images_dir_count", "value": int((source_files_df["source_kind"] == "images_dir").sum()) if "source_kind" in source_files_df.columns else 0},
    ]
    summary_df = pd.DataFrame(summary_rows)

    return {
        "summary": summary_df,
        "table_assets": table_assets_df,
        "warnings": warnings_df,
        "role_counts": role_counts_df,
        "source_files": source_files_df,
    }


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export MinerU table assets to DateFac standard excel/json summary.")
    parser.add_argument("--mineru-output-dir", required=True, help="MinerU output directory path (single report folder).")
    parser.add_argument("--output-dir", required=True, help="Output directory path for mineru_table_assets artifacts.")
    args = parser.parse_args()

    source_root = Path(args.mineru_output_dir).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    result = read_mineru_output(source_root)
    dfs = _build_dataframes(result)

    out_excel = out_dir / "mineru_table_assets.xlsx"
    out_assets_json = out_dir / "mineru_table_assets.json"
    out_summary_json = out_dir / "mineru_table_assets_summary.json"
    out_report_md = out_dir / "mineru_table_assets_report.md"

    _write_excel(out_excel, dfs)

    assets_payload = {
        "source_root": result.source_root,
        "table_assets": [a.to_dict() for a in result.table_assets],
        "warnings": [w.to_dict() for w in result.warnings],
        "source_files": [s.to_dict() for s in result.source_files],
    }
    _write_json(out_assets_json, assets_payload)

    summary = result.summary()
    summary["output_excel"] = str(out_excel)
    summary["output_json"] = str(out_assets_json)
    summary["source_files_detected"] = [s.to_dict() for s in result.source_files]
    _write_json(out_summary_json, summary)

    report_lines: List[str] = [
        "# MinerU TableAsset Export Report",
        "",
        "## Input",
        f"- mineru_output_dir: `{source_root}`",
        "",
        "## Output",
        f"- excel: `{out_excel}`",
        f"- assets_json: `{out_assets_json}`",
        f"- summary_json: `{out_summary_json}`",
        "",
        "## Snapshot",
        f"- table_asset_count: {summary.get('table_asset_count', 0)}",
        f"- warning_count: {summary.get('warning_count', 0)}",
        f"- source_file_count: {summary.get('source_file_count', 0)}",
        "",
        "## Role Counts",
    ]
    role_counts = summary.get("role_counts", {})
    if isinstance(role_counts, dict) and role_counts:
        for role, count in sorted(role_counts.items(), key=lambda x: str(x[0])):
            report_lines.append(f"- {role}: {count}")
    else:
        report_lines.append("- (none)")

    report_lines.extend(
        [
            "",
            "## Notes",
            "- deterministic table_role_guess (no LLM).",
            "- missing fields are captured as warnings and do not crash export.",
            "- UTF-8 output enabled for Chinese content.",
        ]
    )
    out_report_md.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"mineru_table_assets_excel: {out_excel}")
    print(f"mineru_table_assets_json: {out_assets_json}")
    print(f"mineru_table_assets_summary_json: {out_summary_json}")
    print(f"mineru_table_assets_report_md: {out_report_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
