import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Ensure project root is importable when this file is executed directly.
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config_manager import ConfigManager
from extractor_adapter import (
    extract_docling_table_blocks,
    extract_marker_table_blocks,
    extract_pdfplumber_table_blocks,
)
from extractor_quality import score_table_block
from table_block import TableBlock


def fallback_path_if_locked(path: Path) -> Path:
    if not path.exists():
        return path
    try:
        with open(path, "a", encoding="utf-8"):
            pass
        return path
    except PermissionError:
        return path.with_name(f"{path.stem}_副本{path.suffix}")


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


def resolve_marker_cache(temp_cache_dir: Path, pdf_path: Path) -> Optional[Path]:
    candidates = [
        temp_cache_dir / f"{pdf_path.name}.txt",
        temp_cache_dir / f"{pdf_path.stem}.txt",
        temp_cache_dir / f"{pdf_path.name}.md",
        temp_cache_dir / f"{pdf_path.stem}.md",
    ]
    for path in candidates:
        if path.exists() and path.is_file():
            return path
    return None


def table_blocks_to_rows(
    blocks: List[TableBlock],
    source_pdf: str,
    backend_status_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for block in blocks or []:
        score = score_table_block(block)
        rows.append(
            {
                "source_pdf": source_pdf,
                "backend": block.backend,
                "backend_status": backend_status_map.get(block.backend, "success"),
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


def summarize_backends(
    table_rows: List[Dict[str, Any]],
    source_pdf: str,
    backend_status_map: Dict[str, str],
    backend_error_map: Dict[str, str],
) -> pd.DataFrame:
    df = pd.DataFrame(table_rows)
    summary_rows: List[Dict[str, Any]] = []
    for backend, backend_status in backend_status_map.items():
        sub = df[df["backend"] == backend] if not df.empty else pd.DataFrame()
        table_count = int(len(sub))
        if table_count > 0:
            avg_quality_score = round(float(sub["quality_score"].mean()), 4)
            good_table_count = int((sub["quality_level"] == "GOOD").sum())
            warning_count = int(
                ((sub["quality_level"] == "BAD") | (sub["quality_flags"].fillna("").astype(str).str.strip() != "")).sum()
            )
        else:
            avg_quality_score = 0.0
            good_table_count = 0
            warning_count = 0
        summary_rows.append(
            {
                "source_pdf": source_pdf,
                "backend": backend,
                "backend_status": backend_status,
                "table_count": table_count,
                "avg_quality_score": avg_quality_score,
                "good_table_count": good_table_count,
                "warning_count": warning_count,
                "error_message": backend_error_map.get(backend, ""),
            }
        )
    return pd.DataFrame(summary_rows)


def run_backend(
    backend: str,
    pdf_path: Path,
    markdown_text: str,
    table_extraction_cfg: dict,
) -> List[TableBlock]:
    if backend == "pdfplumber":
        return extract_pdfplumber_table_blocks(str(pdf_path), table_extraction_cfg, logger=None)
    if backend == "marker":
        return extract_marker_table_blocks(markdown_text, table_extraction_cfg, logger=None)
    if backend == "docling":
        return extract_docling_table_blocks(str(pdf_path), table_extraction_cfg, logger=None)
    return []


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
    if not bool(probe_cfg.get("enabled", True)):
        print("[probe_extractors] extractor_probe disabled by config")
        return 0
    backends = [str(x).strip().lower() for x in probe_cfg.get("backends", ["pdfplumber", "marker"])]
    output_report = bool(probe_cfg.get("output_report", True))
    if not output_report:
        print("[probe_extractors] output_report disabled by config")
        return 0

    temp_cache_dir = Path(config["paths"]["temp_cache_dir"])
    marker_cache_path = resolve_marker_cache(temp_cache_dir, pdf_path)
    markdown_text = ""
    if marker_cache_path is not None:
        markdown_text = marker_cache_path.read_text(encoding="utf-8", errors="ignore")

    all_blocks: List[TableBlock] = []
    backend_status_map: Dict[str, str] = {}
    backend_error_map: Dict[str, str] = {}

    for backend in backends:
        if backend == "marker" and marker_cache_path is None:
            backend_status_map[backend] = "unavailable_no_markdown_cache"
            backend_error_map[backend] = "marker markdown cache not found"
            continue
        try:
            blocks = run_backend(backend, pdf_path, markdown_text, config.get("table_extraction", {}))
            all_blocks.extend(blocks)
            if len(blocks) == 0:
                backend_status_map[backend] = "completed_no_tables"
            else:
                backend_status_map[backend] = "success"
        except Exception as exc:
            backend_status_map[backend] = "failed"
            backend_error_map[backend] = str(exc)
            continue

    source_pdf = str(pdf_path)
    table_rows = table_blocks_to_rows(all_blocks, source_pdf=source_pdf, backend_status_map=backend_status_map)
    summary_df = summarize_backends(
        table_rows,
        source_pdf=source_pdf,
        backend_status_map=backend_status_map,
        backend_error_map=backend_error_map,
    )

    backend_scores_df = pd.DataFrame(
        [
            {
                "source_pdf": source_pdf,
                "backend": row["backend"],
                "quality_score": row["quality_score"],
                "quality_level": row["quality_level"],
                "quality_flags": row["quality_flags"],
            }
            for row in table_rows
        ]
    )

    report_path = fallback_path_if_locked(pkg_path / f"10_extractor_compare_report_{pdf_path.stem}.xlsx")
    used = set()
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name=safe_sheet_name("summary", used), index=False)
        pd.DataFrame(table_rows).to_excel(writer, sheet_name=safe_sheet_name("table_blocks", used), index=False)
        backend_scores_df.to_excel(writer, sheet_name=safe_sheet_name("backend_scores", used), index=False)

    print(f"[probe_extractors] report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

