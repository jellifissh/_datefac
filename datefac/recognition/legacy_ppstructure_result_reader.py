from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from datefac.domain.extracted_table import ExtractedTable


@dataclass
class LegacyPPStructureReadResult:
    extracted_tables: List[ExtractedTable] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    source_files: List[Dict[str, Any]] = field(default_factory=list)


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _normalize_number_token(token: str) -> str:
    t = _norm(token)
    if not t:
        return ""
    t = t.replace("（", "(").replace("）", ")")
    if re.match(r"^\([+-]?[0-9,]+(\.[0-9]+)?%?\)$", t):
        t = "-" + t[1:-1]
    return t


def _row_text_from_series(s: pd.Series) -> str:
    vals = []
    for x in s.tolist():
        t = _norm(x)
        if t:
            vals.append(t)
    return " | ".join(vals)


def _build_cells_from_df(df: pd.DataFrame, max_cells: int = 2000) -> List[Dict[str, Any]]:
    cells: List[Dict[str, Any]] = []
    count = 0
    for r in range(len(df)):
        row = df.iloc[r]
        for c in range(len(df.columns)):
            text = _norm(row.iloc[c])
            if text:
                cells.append({"row": r, "col": c, "text": text})
                count += 1
                if count >= max_cells:
                    return cells
    return cells


def _recognition_status_by_df(df: pd.DataFrame) -> str:
    if df.empty:
        return "EMPTY_RESULT"
    non_empty_per_row = []
    for i in range(len(df)):
        cnt = 0
        for x in df.iloc[i].tolist():
            if _norm(x):
                cnt += 1
        non_empty_per_row.append(cnt)
    if not non_empty_per_row:
        return "EMPTY_RESULT"
    if max(non_empty_per_row) <= 1:
        return "RECOGNIZED_ROW_TEXT"
    if max(non_empty_per_row) == 2:
        return "RECOGNIZED_GRID_WEAK"
    return "RECOGNIZED_GRID"


def _to_extracted_table_from_df(
    df: pd.DataFrame,
    source_file: Path,
    extracted_table_id: str,
    table_asset_id: str | None = None,
    source_doc_name: str = "",
    table_role_guess: str = "",
) -> ExtractedTable:
    nd = df.fillna("").astype(str)
    row_texts = [_row_text_from_series(nd.iloc[i]) for i in range(len(nd))]
    row_texts = [x for x in row_texts if x]
    cells = _build_cells_from_df(nd)
    non_empty = len(cells)
    row_count = int(len(nd))
    col_count = int(len(nd.columns))
    status = _recognition_status_by_df(nd)

    return ExtractedTable(
        extracted_table_id=extracted_table_id,
        table_asset_id=table_asset_id or "",
        source_doc_name=source_doc_name or source_file.stem,
        table_role_guess=table_role_guess,
        image_path="",
        recognizer_name="legacy_ppstructure",
        recognizer_version="legacy",
        recognition_status=status,
        row_count=row_count,
        col_count=col_count,
        cell_count=row_count * col_count,
        non_empty_cell_count=non_empty,
        raw_text="\n".join(row_texts),
        table_grid=nd.values.tolist(),
        cells=cells,
        warnings=[],
    )


def _parse_res_txt(path: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
    txt = _read_text_file(path)
    warnings: List[Dict[str, Any]] = []
    row_texts: List[str] = []

    parsed: Any = None
    try:
        parsed = json.loads(txt)
    except Exception:
        try:
            parsed = ast.literal_eval(txt)
        except Exception:
            parsed = None

    if parsed is None:
        # fallback plain lines
        lines = [x.strip() for x in txt.splitlines() if x.strip()]
        row_texts = lines
        warnings.append(
            {
                "source_file": str(path),
                "warning_code": "FAILED_PARSE_RESULT",
                "warning_message": "res_*.txt 非 JSON/literal_eval，已按纯文本行读取。",
            }
        )
        return row_texts, warnings

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for k in ("text", "html", "res", "content"):
                if k in obj:
                    v = _norm(obj.get(k))
                    if v:
                        row_texts.append(v)
            for v in obj.values():
                walk(v)
            return
        if isinstance(obj, list):
            for x in obj:
                walk(x)
            return
        if isinstance(obj, str):
            t = _norm(obj)
            if t and len(t) >= 2:
                row_texts.append(t)

    walk(parsed)
    # dedupe keep order
    out: List[str] = []
    seen = set()
    for x in row_texts:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out, warnings


def read_legacy_ppstructure_results(ppstructure_result_dir: Path | str) -> LegacyPPStructureReadResult:
    root = Path(ppstructure_result_dir)
    result = LegacyPPStructureReadResult()

    if not root.exists():
        result.warnings.append(
            {
                "source_file": str(root),
                "warning_code": "BLOCKED_MISSING_PPSTRUCTURE_RESULT_DIR",
                "warning_message": "PPStructure 结果目录不存在。",
            }
        )
        return result

    txt_files = sorted(root.rglob("res_*.txt"))
    xlsx_files = sorted([p for p in root.rglob("*.xlsx") if not p.name.startswith("~$")])
    html_files = sorted(root.rglob("*.html"))

    for p in txt_files:
        result.source_files.append({"source_file": str(p), "source_kind": "res_txt"})
    for p in xlsx_files:
        result.source_files.append({"source_file": str(p), "source_kind": "xlsx"})
    for p in html_files:
        result.source_files.append({"source_file": str(p), "source_kind": "html"})

    # parse txt files as row-text extracted tables
    for i, p in enumerate(txt_files):
        row_texts, warns = _parse_res_txt(p)
        result.warnings.extend(warns)
        status = "RECOGNIZED_ROW_TEXT" if row_texts else "EMPTY_RESULT"
        et = ExtractedTable(
            extracted_table_id=f"{p.stem}__txt_{i}",
            table_asset_id="",
            source_doc_name=p.parent.name,
            table_role_guess="",
            image_path="",
            recognizer_name="legacy_ppstructure",
            recognizer_version="legacy",
            recognition_status=status,
            row_count=len(row_texts),
            col_count=1 if row_texts else 0,
            cell_count=len(row_texts),
            non_empty_cell_count=len(row_texts),
            raw_text="\n".join(row_texts),
            row_texts=row_texts,  # type: ignore[arg-type]
            table_grid=[[x] for x in row_texts],
            cells=[{"row": idx, "col": 0, "text": t} for idx, t in enumerate(row_texts)],
            warnings=[w["warning_code"] for w in warns] if warns else [],
        )
        result.extracted_tables.append(et)

    # parse xlsx as weak grid / row-text tables
    for p in xlsx_files:
        try:
            xl = pd.ExcelFile(p)
        except Exception as exc:
            result.warnings.append(
                {
                    "source_file": str(p),
                    "warning_code": "FAILED_PARSE_RESULT",
                    "warning_message": f"xlsx 打开失败: {exc}",
                }
            )
            continue
        for s in xl.sheet_names:
            try:
                df = pd.read_excel(p, sheet_name=s).fillna("")
            except Exception as exc:
                result.warnings.append(
                    {
                        "source_file": f"{p}#{s}",
                        "warning_code": "FAILED_PARSE_RESULT",
                        "warning_message": f"sheet 读取失败: {exc}",
                    }
                )
                continue
            et = _to_extracted_table_from_df(
                df=df,
                source_file=p,
                extracted_table_id=f"{p.stem}__{s}",
                source_doc_name=p.parent.name,
            )
            result.extracted_tables.append(et)

    if not result.extracted_tables:
        result.warnings.append(
            {
                "source_file": str(root),
                "warning_code": "EMPTY_RESULT",
                "warning_message": "未解析到任何 PPStructure 表格结果。",
            }
        )

    return result

