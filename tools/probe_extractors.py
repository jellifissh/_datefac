import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

# Ensure project root is importable when this file is executed directly.
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config_manager import ConfigManager
from extractor_adapter import (
    extract_marker_table_blocks,
    extract_pdfplumber_table_blocks,
    extract_docling_table_blocks,
)
from extractor_quality import score_table_block
from table_block import TableBlock


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def fallback_path_if_locked(path: Path) -> Path:
    if not path.exists():
        return path
    try:
        with open(path, "a", encoding="utf-8"):
            pass
        return path
    except PermissionError:
        return path.with_name(f"{path.stem}_副本_{now_stamp()}{path.suffix}")


def safe_sheet_name(name: str, used: set) -> str:
    cleaned = re.sub(r"[\\/*?:\[\]]", "_", str(name or "").strip()) or "sheet"
    cleaned = cleaned[:31]
    base = cleaned
    idx = 1
    while cleaned in used:
        suffix = f"_{idx}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        idx += 1
    used.add(cleaned)
    return cleaned


def build_preview(df: Any, max_rows: int = 3, max_cols: int = 5, max_len: int = 300) -> str:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return ""
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines = []
    for _, row in sample.iterrows():
        lines.append(" | ".join(cell.strip() for cell in row.tolist()))
    text = " || ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def table_blocks_to_rows(blocks: List[TableBlock]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for block in blocks or []:
        score = score_table_block(block)
        rows.append(
            {
                "backend": block.backend,
                "page": block.page,
                "table_index": block.table_index,
                "row_count": block.row_count,
                "col_count": block.col_count,
                "empty_cell_ratio": block.empty_cell_ratio,
                "quality_score": score["quality_score"],
                "quality_level": score["quality_level"],
                "quality_flags": score["quality_flags"],
                "preview": build_preview(block.raw_df),
            }
        )
    return rows


def summarize_backend(table_rows: List[Dict[str, Any]]) -> pd.DataFrame:
    if not table_rows:
        return pd.DataFrame(columns=["backend", "table_count", "avg_quality_score", "good_table_count", "warning_count"])
    df = pd.DataFrame(table_rows)
    df["warning"] = df["quality_level"].isin(["BAD"]) | (df["quality_flags"].astype(str) != "")
    grouped = df.groupby("backend", dropna=False)
    summary = grouped.agg(
        table_count=("backend", "count"),
        avg_quality_score=("quality_score", "mean"),
        good_table_count=("quality_level", lambda x: int((x == "GOOD").sum())),
        warning_count=("warning", lambda x: int(x.sum())),
    ).reset_index()
    summary["avg_quality_score"] = summary["avg_quality_score"].round(4)
    return summary


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Probe extractor adapters and compare table block quality.")
    ap.add_argument("--pdf", required=True, help="Target PDF path")
    ap.add_argument("--config", default="config.yaml", help="Config path (default: config.yaml)")
    return ap


def main() -> int:
    args = parser().parse_args()
    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        print(f"[probe_extractors] pdf not found: {pdf_path}")
        return 1

    cm = ConfigManager(config_path=args.config)
    config = cm.load()
    out_dir = Path(config["paths"]["output_dir"]).resolve()
    pkg_path = out_dir / f"{pdf_path.stem}_资产包"
    pkg_path.mkdir(parents=True, exist_ok=True)

    probe_cfg = config.get("extractor_probe", {}) or {}
    enabled = bool(probe_cfg.get("enabled", True))
    backends = probe_cfg.get("backends", ["pdfplumber", "marker"])
    output_report = bool(probe_cfg.get("output_report", True))
    if not enabled:
        print("[probe_extractors] extractor_probe disabled by config")
        return 0

    markdown_cache = Path(config["paths"]["temp_cache_dir"]) / f"{pdf_path.name}.txt"
    markdown_text = ""
    if markdown_cache.exists():
        markdown_text = markdown_cache.read_text(encoding="utf-8", errors="ignore")

    all_blocks: List[TableBlock] = []
    for backend in backends:
        backend = str(backend).strip().lower()
        if backend == "pdfplumber":
            all_blocks.extend(extract_pdfplumber_table_blocks(str(pdf_path), config.get("table_extraction", {}), logger=None))
        elif backend == "marker":
            all_blocks.extend(extract_marker_table_blocks(markdown_text, config.get("table_extraction", {}), logger=None))
        elif backend == "docling":
            all_blocks.extend(extract_docling_table_blocks(str(pdf_path), config.get("table_extraction", {}), logger=None))
        else:
            continue

    table_rows = table_blocks_to_rows(all_blocks)
    summary_df = summarize_backend(table_rows)

    backend_scores = []
    for row in table_rows:
        backend_scores.append(
            {
                "backend": row["backend"],
                "quality_score": row["quality_score"],
                "quality_level": row["quality_level"],
                "quality_flags": row["quality_flags"],
            }
        )
    backend_scores_df = pd.DataFrame(backend_scores)

    if not output_report:
        print("[probe_extractors] output_report disabled by config")
        return 0

    report_path = fallback_path_if_locked(pkg_path / "10_extractor_compare_report.xlsx")
    used = set()
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name=safe_sheet_name("summary", used), index=False)
        pd.DataFrame(table_rows).to_excel(writer, sheet_name=safe_sheet_name("table_blocks", used), index=False)
        backend_scores_df.to_excel(writer, sheet_name=safe_sheet_name("backend_scores", used), index=False)

    print(f"[probe_extractors] report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
