import argparse
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    import pdfplumber
except Exception:  # pragma: no cover
    pdfplumber = None


DEFAULT_INPUT_DIR = Path(r"D:\_datefac\input")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output")
DEFAULT_BASELINE_23 = Path(r"D:\_datefac\output\23_baseline_evaluation_report.xlsx")
DEFAULT_REPORT_24 = Path(r"D:\_datefac\output\24_report_type_diagnostics.xlsx")

ASSET_SUFFIX = "_资产包"

TYPE_TARGET = "target_company_financial_forecast"
TYPE_INDUSTRY = "industry_research"
TYPE_WEALTH = "wealth_management_weekly"
TYPE_MACRO = "macro_or_strategy"
TYPE_NOTICE = "announcement_or_notice"
TYPE_UNKNOWN = "unknown"

KEYWORDS: Dict[str, List[str]] = {
    TYPE_TARGET: [
        "财务预测",
        "主要财务指标",
        "盈利预测",
        "利润表",
        "资产负债表",
        "现金流量表",
        "每股收益",
        "估值指标",
        "P/E",
        "P/B",
        "EV/EBITDA",
        "买入",
        "增持",
        "目标价",
    ],
    TYPE_INDUSTRY: [
        "行业",
        "板块",
        "景气",
        "产业链",
        "市场规模",
        "供需",
        "渗透率",
        "行业专题",
        "行业深度",
    ],
    TYPE_WEALTH: [
        "银行理财",
        "理财周报",
        "理财产品",
        "现金管理类",
        "固收",
        "债券基金",
        "存续规模",
        "破净率",
    ],
    TYPE_MACRO: [
        "宏观",
        "策略",
        "利率",
        "通胀",
        "PMI",
        "社融",
        "大类资产",
        "配置建议",
    ],
    TYPE_NOTICE: [
        "公告",
        "通知",
        "董事会",
        "股东大会",
        "停牌",
        "复牌",
    ],
}


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _save_excel_robust(sheet_map: Dict[str, pd.DataFrame], report_path: Path) -> str:
    final = report_path
    if report_path.exists():
        try:
            with open(report_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final = report_path.with_name(f"{report_path.stem}_copy_{ts}{report_path.suffix}")

    used = set()
    with pd.ExcelWriter(final, engine="openpyxl") as writer:
        for sheet, df in sheet_map.items():
            safe = _safe_sheet_name(sheet, used)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=safe, index=False)
    return str(final)


def _read_pdf_front_text(pdf_path: Path, max_pages: int = 3) -> Tuple[int, str, str]:
    if pdfplumber is None:
        return 0, "", "pdfplumber_not_available"
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            page_count = len(pdf.pages)
            chunks = []
            for page in pdf.pages[:max_pages]:
                text = _norm(page.extract_text())
                if text:
                    chunks.append(text)
            return page_count, "\n".join(chunks), ""
    except Exception as exc:
        return 0, "", f"pdf_read_error:{exc}"


def _extract_title_guess(text: str) -> str:
    for line in text.splitlines():
        t = _norm(line)
        if t and len(t) >= 4:
            return t[:120]
    return ""


def _read_asset_text(asset_dir: Path) -> Tuple[str, List[str]]:
    texts = []
    errors = []

    try:
        md = asset_dir / "01_全量脱水底稿.md"
        if md.exists():
            texts.append(md.read_text(encoding="utf-8", errors="ignore")[:20000])
    except Exception as exc:
        errors.append(f"md_error:{exc}")

    try:
        f02a = next(asset_dir.glob("02A_*.xlsx"), None)
        if f02a:
            xls = pd.ExcelFile(f02a, engine="openpyxl")
            idx_sheet = next((s for s in xls.sheet_names if s.startswith("00_")), xls.sheet_names[0])
            idx_df = pd.read_excel(f02a, sheet_name=idx_sheet, engine="openpyxl").fillna("")
            if "preview" in idx_df.columns:
                previews = idx_df["preview"].astype(str).head(80).tolist()
                texts.append("\n".join(previews))
    except Exception as exc:
        errors.append(f"02A_error:{exc}")

    try:
        f02 = next((p for p in asset_dir.glob("02_*.xlsx") if not p.name.startswith("02A_")), None)
        if f02:
            xls = pd.ExcelFile(f02, engine="openpyxl")
            data_sheets = [s for s in xls.sheet_names if not s.startswith("00_")]
            parts = []
            for s in data_sheets[:5]:
                try:
                    df = pd.read_excel(f02, sheet_name=s, engine="openpyxl").fillna("")
                    sample = df.iloc[:15, :8].astype(str)
                    lines = []
                    for _, row in sample.iterrows():
                        vals = [x.strip() for x in row.tolist() if _norm(x)]
                        if vals:
                            lines.append(" | ".join(vals))
                    if lines:
                        parts.append(f"[{s}] " + " || ".join(lines))
                except Exception:
                    continue
            if parts:
                texts.append("\n".join(parts))
    except Exception as exc:
        errors.append(f"02_error:{exc}")

    return "\n".join(texts), errors


def _find_asset_for_pdf(pdf_stem: str, asset_dirs: List[Path]) -> Optional[Path]:
    exact = f"{pdf_stem}{ASSET_SUFFIX}"
    for d in asset_dirs:
        if d.name == exact:
            return d
    starts = [d for d in asset_dirs if d.name.startswith(pdf_stem)]
    if starts:
        return sorted(starts, key=lambda x: x.name)[0]
    return None


def _count_keyword_hits(text: str, keyword: str) -> int:
    if not text or not keyword:
        return 0
    if keyword.isascii():
        return len(re.findall(re.escape(keyword), text, flags=re.IGNORECASE))
    return text.count(keyword)


def _sample_context(text: str, keyword: str, width: int = 30) -> str:
    if not text:
        return ""
    if keyword.isascii():
        m = re.search(re.escape(keyword), text, flags=re.IGNORECASE)
        if not m:
            return ""
        a, b = m.span()
        return text[max(0, a - width): min(len(text), b + width)].replace("\n", " ")
    idx = text.find(keyword)
    if idx < 0:
        return ""
    a = max(0, idx - width)
    b = min(len(text), idx + len(keyword) + width)
    return text[a:b].replace("\n", " ")


def _load_23_asset_map(report_23: Path) -> Dict[str, Dict[str, object]]:
    if not report_23.exists():
        return {}
    try:
        df = pd.read_excel(report_23, sheet_name="asset_quality_matrix", engine="openpyxl").fillna("")
    except Exception:
        return {}
    out = {}
    for _, r in df.iterrows():
        asset = _norm(r.get("asset_package"))
        if not asset:
            continue
        out[asset] = {
            "label_hit_metric_count": r.get("label_hit_metric_count", 0),
            "value_valid_metric_count": r.get("value_valid_metric_count", 0),
        }
    return out


def _classify_report_type(scores: Dict[str, int], has_05_candidates: bool) -> Tuple[str, str, bool, float, str]:
    s_target = scores.get(TYPE_TARGET, 0)
    s_ind = scores.get(TYPE_INDUSTRY, 0)
    s_wm = scores.get(TYPE_WEALTH, 0)
    s_macro = scores.get(TYPE_MACRO, 0)
    s_notice = scores.get(TYPE_NOTICE, 0)
    total = sum(scores.values())
    dominant = max(scores, key=lambda k: scores.get(k, 0)) if scores else TYPE_UNKNOWN
    dom_score = scores.get(dominant, 0)
    confidence = round((dom_score / total), 4) if total > 0 else 0.0

    report_type = TYPE_UNKNOWN
    target_applicability = "unknown"
    include = False
    reason = "insufficient evidence"

    if s_wm >= 2 and s_wm >= max(s_target, s_ind, s_macro, s_notice):
        report_type = TYPE_WEALTH
        target_applicability = "non_target"
        include = False
        reason = "wealth keywords strongly hit"
    elif s_notice >= 2 and s_notice >= max(s_target, s_ind, s_macro, s_wm):
        report_type = TYPE_NOTICE
        target_applicability = "non_target"
        include = False
        reason = "announcement keywords strongly hit"
    elif s_macro >= 2 and s_macro >= max(s_target, s_ind, s_wm, s_notice):
        report_type = TYPE_MACRO
        target_applicability = "non_target" if s_target == 0 else "partial"
        include = target_applicability == "partial"
        reason = "macro/strategy keywords strongly hit"
    elif s_ind >= 3 and s_ind >= max(s_target + 1, s_wm, s_macro, s_notice):
        report_type = TYPE_INDUSTRY
        if s_target >= 2:
            target_applicability = "partial"
            include = True
            reason = "industry dominant with some company-financial signals"
        else:
            target_applicability = "non_target"
            include = False
            reason = "industry dominant and target signals weak"
    elif s_target >= 4 and (has_05_candidates or any(scores.get(k, 0) > 0 for k in [TYPE_TARGET])):
        report_type = TYPE_TARGET
        target_applicability = "target"
        include = True
        reason = "target financial forecast keywords strongly hit"
    elif s_target >= 2:
        report_type = TYPE_TARGET
        target_applicability = "partial"
        include = True
        reason = "target keywords moderately hit"
    elif total == 0:
        report_type = TYPE_UNKNOWN
        target_applicability = "unknown"
        include = False
        reason = "no keyword evidence"
    else:
        report_type = dominant if dominant in KEYWORDS else TYPE_UNKNOWN
        target_applicability = "unknown"
        include = False
        reason = "mixed weak evidence"

    return report_type, target_applicability, include, confidence, reason


def diagnose_report_type(
    input_dir: Path,
    output_dir: Path,
    report_23: Path,
    output_report: Path,
) -> Tuple[str, Dict[str, object], pd.DataFrame]:
    pdf_files = sorted([p for p in input_dir.glob("*.pdf") if p.is_file()])
    asset_dirs = sorted([p for p in output_dir.iterdir() if p.is_dir() and p.name.endswith(ASSET_SUFFIX)]) if output_dir.exists() else []
    map23 = _load_23_asset_map(report_23)

    summary_rows = []
    evidence_rows = []

    for pdf in pdf_files:
        stem = pdf.stem
        asset_dir = _find_asset_for_pdf(stem, asset_dirs)
        asset_name = asset_dir.name if asset_dir else ""

        page_count, pdf_text, pdf_err = _read_pdf_front_text(pdf, max_pages=3)
        asset_text = ""
        asset_errors: List[str] = []
        if asset_dir:
            asset_text, asset_errors = _read_asset_text(asset_dir)

        full_text = "\n".join([pdf_text, asset_text]).strip()
        title_guess = _extract_title_guess(pdf_text) or _extract_title_guess(asset_text)

        hits_by_type: Dict[str, int] = {k: 0 for k in KEYWORDS.keys()}
        evidence_keywords = []

        for ktype, words in KEYWORDS.items():
            for kw in words:
                cnt = _count_keyword_hits(full_text, kw)
                if cnt <= 0:
                    continue
                hits_by_type[ktype] += cnt
                evidence_keywords.append(f"{kw}:{cnt}")
                evidence_rows.append(
                    {
                        "asset_package": asset_name,
                        "keyword": kw,
                        "keyword_type": ktype,
                        "hit_count": cnt,
                        "sample_context": _sample_context(full_text, kw),
                    }
                )

        label_hit = 0
        if asset_name in map23:
            try:
                label_hit = int(float(map23[asset_name].get("label_hit_metric_count", 0) or 0))
            except Exception:
                label_hit = 0
        has_05_candidates = label_hit > 0

        report_type, applicability, include, conf, cls_reason = _classify_report_type(hits_by_type, has_05_candidates)

        reason_parts = [cls_reason]
        if pdf_err:
            reason_parts.append(pdf_err)
        reason_parts.extend(asset_errors[:2])

        summary_rows.append(
            {
                "source_pdf": pdf.name,
                "asset_package": asset_name,
                "page_count": page_count,
                "title_guess": title_guess,
                "report_type": report_type,
                "report_type_confidence": conf,
                "target_applicability": applicability,
                "reason": "; ".join([x for x in reason_parts if x]),
                "evidence_keywords": "|".join(evidence_keywords[:30]),
                "should_include_in_8_metric_eval": bool(include),
                "recommendation": (
                    "include in 8-metric eval" if include else "exclude from strict 8-metric eval; treat as non-target or manual"
                ),
            }
        )

    # Include orphan asset packages not mapped to input pdf.
    mapped_assets = {r["asset_package"] for r in summary_rows if _norm(r["asset_package"])}
    for d in asset_dirs:
        if d.name in mapped_assets:
            continue
        summary_rows.append(
            {
                "source_pdf": "",
                "asset_package": d.name,
                "page_count": "",
                "title_guess": "",
                "report_type": TYPE_UNKNOWN,
                "report_type_confidence": 0.0,
                "target_applicability": "unknown",
                "reason": "asset package without matched input pdf",
                "evidence_keywords": "",
                "should_include_in_8_metric_eval": False,
                "recommendation": "manual check mapping between input pdf and asset package",
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    evidence_df = pd.DataFrame(evidence_rows)

    total = len(summary_df)
    target_count = int((summary_df["target_applicability"].astype(str) == "target").sum()) if total else 0
    partial_count = int((summary_df["target_applicability"].astype(str) == "partial").sum()) if total else 0
    non_target_count = int((summary_df["target_applicability"].astype(str) == "non_target").sum()) if total else 0
    unknown_count = int((summary_df["target_applicability"].astype(str) == "unknown").sum()) if total else 0
    include_cnt = int(summary_df["should_include_in_8_metric_eval"].astype(bool).sum()) if total else 0

    scope_df = pd.DataFrame(
        [
            {
                "total_pdfs": len(pdf_files),
                "target_count": target_count,
                "partial_count": partial_count,
                "non_target_count": non_target_count,
                "unknown_count": unknown_count,
                "recommended_8_metric_eval_count": include_cnt,
                "excluded_from_8_metric_eval_count": max(0, total - include_cnt),
            }
        ]
    )

    report_path = _save_excel_robust(
        {
            "report_type_summary": summary_df,
            "keyword_evidence": evidence_df,
            "eval_scope_recommendation": scope_df,
        },
        output_report,
    )

    stats = {
        "recommended_8_metric_eval_count": include_cnt,
        "target_count": target_count,
        "partial_count": partial_count,
        "non_target_count": non_target_count,
        "unknown_count": unknown_count,
    }
    return report_path, stats, summary_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose report type and applicability for 8-metric evaluation.")
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR), help="Input pdf directory.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output root directory.")
    parser.add_argument("--baseline-23", default=str(DEFAULT_BASELINE_23), help="23 baseline report path.")
    parser.add_argument("--output-report", default=str(DEFAULT_REPORT_24), help="24 output report path.")
    args = parser.parse_args()

    report_path, stats, summary_df = diagnose_report_type(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        report_23=Path(args.baseline_23),
        output_report=Path(args.output_report),
    )

    print(f"报告路径: {report_path}")
    if not summary_df.empty:
        cols = ["source_pdf", "asset_package", "report_type", "target_applicability", "should_include_in_8_metric_eval"]
        print(summary_df[cols].to_string(index=False))

        for stem in ["H3_AP202605141822320809_1", "H3_AP202605141822322093_1"]:
            sub = summary_df[
                summary_df["asset_package"].astype(str).str.contains(stem, na=False)
                | summary_df["source_pdf"].astype(str).str.contains(stem, na=False)
            ]
            if not sub.empty:
                row = sub.iloc[0]
                print(
                    f"{stem}_check: report_type={_norm(row.get('report_type'))}, "
                    f"target_applicability={_norm(row.get('target_applicability'))}"
                )

    print(f"recommended_8_metric_eval_count: {stats['recommended_8_metric_eval_count']}")


if __name__ == "__main__":
    main()

