import argparse
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output")
DEFAULT_REPORT_PATH = DEFAULT_OUTPUT_DIR / "17_raw_table_business_relevance_report.xlsx"

FINANCIAL_TABLE_KEYWORDS = [
    "财务报表",
    "财务预测",
    "主要财务指标",
    "利润表",
    "资产负债表",
    "现金流量表",
    "财务比率",
    "估值指标",
    "盈利预测",
]

METRIC_KEYWORDS = [
    "营业收入",
    "归母净利润",
    "归属母公司",
    "毛利率",
    "ROE",
    "EPS",
    "每股收益",
    "PE",
    "P/E",
    "PB",
    "P/B",
    "EV/EBITDA",
]

DISCLAIMER_KEYWORDS = [
    "免责声明",
    "风险提示",
    "评级说明",
    "股票评级",
    "行业评级",
    "版权声明",
    "法律声明",
    "本报告",
    "投资建议",
]

YEAR_PATTERN = re.compile(r"(20\d{2}\s*[AE]?|20\d{2}\s*年)", flags=re.IGNORECASE)
NUMERIC_PATTERN = re.compile(r"^[+-]?\d+(?:\.\d+)?%?$")
CONTROL_WS_PATTERN = re.compile(r"\s+")


def _normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_sheet_name(name: str, used: set) -> str:
    cleaned = re.sub(r"[\\/*?:\[\]]", "_", _normalize_text(name) or "sheet")
    cleaned = cleaned[:31]
    base = cleaned
    idx = 1
    while cleaned in used:
        suffix = f"_{idx}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        idx += 1
    used.add(cleaned)
    return cleaned


def _save_excel_robustly(sheet_map: Dict[str, pd.DataFrame], report_path: Path) -> Path:
    final_path = report_path
    if report_path.exists():
        try:
            with open(report_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = report_path.with_name(f"{report_path.stem}_copy_{ts}{report_path.suffix}")

    used_names = set()
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for sheet_name, df in sheet_map.items():
            safe = _safe_sheet_name(sheet_name, used_names)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=safe, index=False)
    return final_path


def _find_asset_packages(output_dir: Path) -> List[Path]:
    if not output_dir.exists():
        return []
    return sorted([p for p in output_dir.iterdir() if p.is_dir() and p.name.endswith("_资产包")])


def _find_consistency_ok_packages(output_dir: Path) -> Optional[set]:
    files = sorted(output_dir.glob("12_*.xlsx"))
    if not files:
        return None
    try:
        xls = pd.ExcelFile(files[0], engine="openpyxl")
        sheet = "summary" if "summary" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(files[0], sheet_name=sheet, engine="openpyxl")
        if df.empty or "asset_package" not in df.columns or "consistency_status" not in df.columns:
            return None
        ok_rows = df[df["consistency_status"].astype(str).str.upper() == "OK"]
        return set(ok_rows["asset_package"].astype(str).tolist())
    except Exception:
        return None


def _find_02a_file(asset_pkg: Path) -> Optional[Path]:
    candidates = sorted(asset_pkg.glob("02A_*.xlsx"))
    return candidates[0] if candidates else None


def _count_keyword_hits(text: str, keywords: List[str]) -> Tuple[int, List[str], Dict[str, int]]:
    t = _normalize_text(text)
    total = 0
    hit_keywords: List[str] = []
    per_keyword: Dict[str, int] = {}
    for kw in keywords:
        cnt = t.count(kw)
        if cnt > 0:
            hit_keywords.append(kw)
            per_keyword[kw] = cnt
            total += cnt
    return total, hit_keywords, per_keyword


def _build_preview(df: pd.DataFrame, max_rows: int = 3, max_cols: int = 5, max_len: int = 300) -> str:
    if df is None or df.empty:
        return ""
    sample = df.iloc[:max_rows, :max_cols].fillna("").astype(str)
    lines = []
    for _, row in sample.iterrows():
        lines.append(" | ".join([_normalize_text(v) for v in row.tolist()]))
    text = " || ".join(lines)
    text = CONTROL_WS_PATTERN.sub(" ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def _collect_cells(df: pd.DataFrame) -> List[str]:
    if df is None or df.empty:
        return []
    values = df.fillna("").astype(str).values.flatten().tolist()
    cells = []
    for v in values:
        text = _normalize_text(v)
        if text:
            cells.append(text)
    return cells


def _density_scores(cells: List[str]) -> Tuple[float, float]:
    if not cells:
        return 0.0, 0.0
    numeric_count = 0
    text_like_count = 0
    for cell in cells:
        compact = cell.replace(",", "").replace("，", "")
        if NUMERIC_PATTERN.match(compact):
            numeric_count += 1
        if re.search(r"[A-Za-z\u4e00-\u9fff]", cell) and not NUMERIC_PATTERN.match(compact):
            text_like_count += 1
    total = len(cells)
    return round(text_like_count / total, 4), round(numeric_count / total, 4)


def _extract_year_token_count(text: str) -> int:
    if not text:
        return 0
    return len(YEAR_PATTERN.findall(text))


def _to_int(value, default: int = 0) -> int:
    try:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return default
        return int(float(value))
    except Exception:
        return default


def _score_business_relevance(
    col_count: int,
    metric_keyword_count: int,
    statement_keyword_count: int,
    year_token_count: int,
    disclaimer_keyword_count: int,
    text_density_score: float,
    numeric_density_score: float,
) -> float:
    score = 0.0
    if metric_keyword_count >= 3:
        score += 0.30
    elif metric_keyword_count >= 1:
        score += 0.10
    if statement_keyword_count >= 1:
        score += 0.20
    if year_token_count >= 3:
        score += 0.20
    elif year_token_count >= 1:
        score += 0.10
    if col_count >= 5:
        score += 0.15
    if numeric_density_score >= 0.20:
        score += 0.15
    if disclaimer_keyword_count >= 2:
        score -= 0.25
    if col_count <= 1:
        score -= 0.20
    if text_density_score >= 0.80 and numeric_density_score <= 0.15 and year_token_count < 2:
        score -= 0.20
    score = max(0.0, min(1.0, score))
    return round(score, 4)


def _classify_business_table_type(
    col_count: int,
    financial_keyword_count: int,
    metric_keyword_count: int,
    year_token_count: int,
    disclaimer_keyword_count: int,
    text_density_score: float,
    numeric_density_score: float,
    quality_flags: str,
) -> Tuple[str, List[str], str]:
    flags: List[str] = []
    qf = _normalize_text(quality_flags)
    if "possible_glued_table" in qf:
        flags.append("possible_glued_table")
    if col_count <= 1:
        flags.append("single_column")
    if disclaimer_keyword_count >= 2:
        flags.append("disclaimer_heavy")
    if text_density_score >= 0.80 and numeric_density_score <= 0.15:
        flags.append("text_heavy_low_numeric")

    if col_count <= 1 and disclaimer_keyword_count > 0:
        return "disclaimer_or_rating_table", flags, "排除免责声明/评级类单列表"
    if col_count <= 1 and financial_keyword_count < 2:
        return "single_column_text", flags, "单列表正文型内容，非结构化财务表"
    if disclaimer_keyword_count >= 2 and metric_keyword_count == 0:
        return "disclaimer_or_rating_table", flags, "免责声明/评级关键词密集，且无核心指标"
    if metric_keyword_count >= 3 and year_token_count >= 3 and "possible_glued_table" in flags:
        return "glued_financial_table", flags, "检测到并排粘连财务表，建议拆分后再标准化"
    if metric_keyword_count >= 3 and year_token_count >= 3 and col_count >= 5:
        return "financial_candidate", flags, "可作为财务标准化候选表"
    if text_density_score >= 0.80 and numeric_density_score <= 0.15 and year_token_count < 2:
        return "narrative_text_table", flags, "正文叙述占比高，缺少结构化数值列"
    return "unknown", flags, "建议人工复核表结构与业务相关性"


def _resolve_backend_profile(row: pd.Series) -> str:
    if "backend_profile" in row and _normalize_text(row.get("backend_profile", "")):
        return _normalize_text(row.get("backend_profile", ""))
    return ""


def _build_summary_recommendation(status: str, primary_issue: str) -> str:
    if status == "good":
        return "原始层业务相关性较好，可优先优化后处理与标准化映射。"
    if primary_issue == "glued_financial_table_unhandled":
        return "优先处理并排粘连财务表拆分，提升 05 可解析性。"
    if primary_issue == "mostly_non_financial_tables":
        return "原始抽取多为正文/声明，需增强抽取业务筛选。"
    if primary_issue == "insufficient_financial_tables":
        return "有效财务候选不足，优先提升抽取覆盖率与后端仲裁。"
    return "建议人工复核并结合 06A/10 probe 继续定位。"


def diagnose(output_dir: Path, report_path: Path) -> Tuple[Path, pd.DataFrame]:
    consistency_ok_set = _find_consistency_ok_packages(output_dir)
    asset_pkgs = _find_asset_packages(output_dir)
    if consistency_ok_set is not None:
        asset_pkgs = [p for p in asset_pkgs if p.name in consistency_ok_set]

    detail_rows: List[Dict[str, object]] = []
    summary_rows: List[Dict[str, object]] = []
    matrix_rows: List[Dict[str, object]] = []

    for pkg in asset_pkgs:
        try:
            file_02a = _find_02a_file(pkg)
            if file_02a is None or not file_02a.exists():
                summary_rows.append(
                    {
                        "asset_package": pkg.name,
                        "total_raw_tables": 0,
                        "financial_candidate_count": 0,
                        "glued_financial_table_count": 0,
                        "narrative_text_table_count": 0,
                        "disclaimer_or_rating_count": 0,
                        "single_column_text_count": 0,
                        "unknown_count": 0,
                        "usable_financial_table_count": 0,
                        "business_relevance_status": "bad",
                        "primary_issue": "insufficient_financial_tables",
                        "recommendation": "缺少 02A，无法进行业务相关性评估。",
                    }
                )
                continue

            xls = pd.ExcelFile(file_02a, engine="openpyxl")
            idx_sheet = "00_表格索引" if "00_表格索引" in xls.sheet_names else xls.sheet_names[0]
            idx_df = pd.read_excel(file_02a, sheet_name=idx_sheet, engine="openpyxl")
            if idx_df.empty:
                summary_rows.append(
                    {
                        "asset_package": pkg.name,
                        "total_raw_tables": 0,
                        "financial_candidate_count": 0,
                        "glued_financial_table_count": 0,
                        "narrative_text_table_count": 0,
                        "disclaimer_or_rating_count": 0,
                        "single_column_text_count": 0,
                        "unknown_count": 0,
                        "usable_financial_table_count": 0,
                        "business_relevance_status": "bad",
                        "primary_issue": "insufficient_financial_tables",
                        "recommendation": "02A 索引为空，需检查抽取层。",
                    }
                )
                continue

            type_counts = {
                "financial_candidate": 0,
                "glued_financial_table": 0,
                "narrative_text_table": 0,
                "disclaimer_or_rating_table": 0,
                "single_column_text": 0,
                "unknown": 0,
            }

            for _, row in idx_df.iterrows():
                sheet_name = _normalize_text(row.get("sheet_name", ""))
                if not sheet_name or sheet_name not in xls.sheet_names:
                    continue
                raw_df = pd.read_excel(file_02a, sheet_name=sheet_name, engine="openpyxl")
                row_count = _to_int(row.get("row_count", raw_df.shape[0]))
                col_count = _to_int(row.get("col_count", raw_df.shape[1]))
                source_pdf = _normalize_text(row.get("source_pdf", ""))
                backend = _normalize_text(row.get("backend", ""))
                backend_profile = _resolve_backend_profile(row)
                page = row.get("page", "")
                table_index = row.get("table_index", "")
                quality_level = _normalize_text(row.get("quality_level", ""))
                quality_flags = _normalize_text(row.get("quality_flags", ""))
                preview = _normalize_text(row.get("preview", "")) or _build_preview(raw_df)

                cells = _collect_cells(raw_df)
                all_text = " ".join(cells)
                financial_keyword_count, financial_keywords, financial_counts = _count_keyword_hits(
                    all_text, FINANCIAL_TABLE_KEYWORDS
                )
                statement_keyword_count = financial_keyword_count
                statement_keywords = financial_keywords
                metric_keyword_count, metric_keywords, metric_counts = _count_keyword_hits(all_text, METRIC_KEYWORDS)
                disclaimer_keyword_count, disclaimer_keywords, disclaimer_counts = _count_keyword_hits(
                    all_text, DISCLAIMER_KEYWORDS
                )
                year_token_count = _extract_year_token_count(all_text)
                text_density_score, numeric_density_score = _density_scores(cells)

                business_relevance_score = _score_business_relevance(
                    col_count=col_count,
                    metric_keyword_count=metric_keyword_count,
                    statement_keyword_count=statement_keyword_count,
                    year_token_count=year_token_count,
                    disclaimer_keyword_count=disclaimer_keyword_count,
                    text_density_score=text_density_score,
                    numeric_density_score=numeric_density_score,
                )

                business_table_type, issue_flags, recommendation = _classify_business_table_type(
                    col_count=col_count,
                    financial_keyword_count=financial_keyword_count,
                    metric_keyword_count=metric_keyword_count,
                    year_token_count=year_token_count,
                    disclaimer_keyword_count=disclaimer_keyword_count,
                    text_density_score=text_density_score,
                    numeric_density_score=numeric_density_score,
                    quality_flags=quality_flags,
                )
                type_counts[business_table_type] = type_counts.get(business_table_type, 0) + 1

                detail_rows.append(
                    {
                        "asset_package": pkg.name,
                        "source_pdf": source_pdf,
                        "sheet_name": sheet_name,
                        "backend": backend,
                        "backend_profile": backend_profile,
                        "page": page,
                        "table_index": table_index,
                        "row_count": row_count,
                        "col_count": col_count,
                        "quality_level": quality_level,
                        "quality_flags": quality_flags,
                        "preview": preview,
                        "financial_keyword_count": financial_keyword_count,
                        "financial_keywords": "|".join(financial_keywords),
                        "statement_keyword_count": statement_keyword_count,
                        "statement_keywords": "|".join(statement_keywords),
                        "year_token_count": year_token_count,
                        "metric_keyword_count": metric_keyword_count,
                        "metric_keywords": "|".join(metric_keywords),
                        "disclaimer_keyword_count": disclaimer_keyword_count,
                        "disclaimer_keywords": "|".join(disclaimer_keywords),
                        "text_density_score": text_density_score,
                        "numeric_density_score": numeric_density_score,
                        "business_relevance_score": business_relevance_score,
                        "business_table_type": business_table_type,
                        "issue_flags": "|".join(issue_flags),
                        "recommendation": recommendation,
                    }
                )

                for kw, cnt in financial_counts.items():
                    matrix_rows.append(
                        {
                            "asset_package": pkg.name,
                            "sheet_name": sheet_name,
                            "keyword": kw,
                            "keyword_type": "financial_table",
                            "hit_count": cnt,
                        }
                    )
                for kw, cnt in metric_counts.items():
                    matrix_rows.append(
                        {
                            "asset_package": pkg.name,
                            "sheet_name": sheet_name,
                            "keyword": kw,
                            "keyword_type": "metric",
                            "hit_count": cnt,
                        }
                    )
                for kw, cnt in disclaimer_counts.items():
                    matrix_rows.append(
                        {
                            "asset_package": pkg.name,
                            "sheet_name": sheet_name,
                            "keyword": kw,
                            "keyword_type": "disclaimer",
                            "hit_count": cnt,
                        }
                    )

            total_raw_tables = sum(type_counts.values())
            usable_financial_table_count = type_counts["financial_candidate"] + type_counts["glued_financial_table"]
            if usable_financial_table_count >= 2:
                status = "good"
            elif usable_financial_table_count == 1:
                status = "partial"
            else:
                status = "bad"

            primary_issue = "ok_or_need_manual_review"
            if type_counts["glued_financial_table"] > 0 and usable_financial_table_count <= 1:
                primary_issue = "glued_financial_table_unhandled"
            elif (
                type_counts["narrative_text_table"]
                + type_counts["disclaimer_or_rating_table"]
                + type_counts["single_column_text"]
            ) >= max(1, total_raw_tables - usable_financial_table_count):
                primary_issue = "mostly_non_financial_tables"
            elif usable_financial_table_count < 2:
                primary_issue = "insufficient_financial_tables"

            summary_rows.append(
                {
                    "asset_package": pkg.name,
                    "total_raw_tables": total_raw_tables,
                    "financial_candidate_count": type_counts["financial_candidate"],
                    "glued_financial_table_count": type_counts["glued_financial_table"],
                    "narrative_text_table_count": type_counts["narrative_text_table"],
                    "disclaimer_or_rating_count": type_counts["disclaimer_or_rating_table"],
                    "single_column_text_count": type_counts["single_column_text"],
                    "unknown_count": type_counts["unknown"],
                    "usable_financial_table_count": usable_financial_table_count,
                    "business_relevance_status": status,
                    "primary_issue": primary_issue,
                    "recommendation": _build_summary_recommendation(status, primary_issue),
                }
            )
        except Exception as exc:
            summary_rows.append(
                {
                    "asset_package": pkg.name,
                    "total_raw_tables": 0,
                    "financial_candidate_count": 0,
                    "glued_financial_table_count": 0,
                    "narrative_text_table_count": 0,
                    "disclaimer_or_rating_count": 0,
                    "single_column_text_count": 0,
                    "unknown_count": 0,
                    "usable_financial_table_count": 0,
                    "business_relevance_status": "bad",
                    "primary_issue": "insufficient_financial_tables",
                    "recommendation": f"读取失败: {exc}",
                }
            )

    details_df = pd.DataFrame(detail_rows)
    summary_df = pd.DataFrame(summary_rows)
    matrix_df = pd.DataFrame(matrix_rows)

    final_path = _save_excel_robustly(
        {
            "table_relevance_details": details_df,
            "asset_relevance_summary": summary_df,
            "keyword_hit_matrix": matrix_df,
        },
        report_path,
    )
    return final_path, summary_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose business relevance of raw tables in 02A assets.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory containing asset packages.")
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH), help="Output report path.")
    args = parser.parse_args()

    report_path, summary_df = diagnose(Path(args.output_dir), Path(args.report_path))
    print(f"report_path={report_path}")
    print(f"summary_rows={len(summary_df)}")
    if not summary_df.empty:
        fields = [
            "asset_package",
            "total_raw_tables",
            "financial_candidate_count",
            "glued_financial_table_count",
            "narrative_text_table_count",
            "disclaimer_or_rating_count",
            "business_relevance_status",
            "primary_issue",
            "recommendation",
        ]
        print(summary_df[fields].to_string(index=False))


if __name__ == "__main__":
    main()

