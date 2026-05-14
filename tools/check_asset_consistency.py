import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = r"D:\_datefac\output"
DEFAULT_REPORT_PATH = r"D:\_datefac\output\12_asset_consistency_report.xlsx"
ASSET_SUFFIX = "\u8d44\u4ea7\u5305"  # 资产包


def _normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_sheet_name(name: str, used: set) -> str:
    cleaned = re.sub(r"[\\/*?:\[\]]", "_", _normalize_text(name) or "Sheet")
    cleaned = cleaned[:31]
    base = cleaned
    idx = 1
    while cleaned in used:
        suffix = f"_{idx}"
        cleaned = f"{base[:31 - len(suffix)]}{suffix}"
        idx += 1
    used.add(cleaned)
    return cleaned


def _save_excel_robustly(sheet_map: Dict[str, pd.DataFrame], report_path: Path) -> str:
    final_path = report_path
    if report_path.exists():
        try:
            with open(report_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = report_path.with_name(f"{report_path.stem}_copy_{ts}{report_path.suffix}")

    used = set()
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for sheet_name, df in sheet_map.items():
            safe = _safe_sheet_name(sheet_name, used)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=safe, index=False)
    return str(final_path)


def _find_asset_packages(output_dir: Path) -> List[Path]:
    if not output_dir.exists():
        return []
    return sorted(
        [p for p in output_dir.iterdir() if p.is_dir() and p.name.endswith(f"_{ASSET_SUFFIX}")],
        key=lambda x: x.name,
    )


def _select_latest_file(asset_pkg: Path, predicate) -> Optional[Path]:
    files = [p for p in asset_pkg.iterdir() if p.is_file() and predicate(p.name)]
    if not files:
        return None
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0]


def _find_prefixed_xlsx(asset_pkg: Path, prefix: str) -> Optional[Path]:
    return _select_latest_file(
        asset_pkg,
        lambda n: n.lower().endswith(".xlsx") and n.startswith(prefix),
    )


def _find_02_file(asset_pkg: Path) -> Optional[Path]:
    return _select_latest_file(
        asset_pkg,
        lambda n: n.lower().endswith(".xlsx") and n.startswith("02_") and not n.startswith("02A_"),
    )


def _find_10_file(asset_pkg: Path) -> Optional[Path]:
    return _select_latest_file(
        asset_pkg,
        lambda n: n.lower().endswith(".xlsx") and n.startswith("10_") and "extractor_compare_report" in n.lower(),
    )


def _find_09_file(output_dir: Path) -> Optional[Path]:
    files = [
        p
        for p in output_dir.iterdir()
        if p.is_file() and p.name.lower().endswith(".xlsx") and p.name.startswith("09_")
    ]
    if not files:
        return None
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0]


def _stem_from_pdf_like(value: str) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    name = Path(text).name
    if name.lower().endswith(".pdf"):
        return name[:-4]
    if name.lower().endswith(".txt"):
        return name[:-4]
    return Path(name).stem


def _package_stem(asset_package: str) -> str:
    name = Path(asset_package).name
    suffix = f"_{ASSET_SUFFIX}"
    if name.endswith(suffix):
        name = name[: -len(suffix)]
    if name.lower().endswith(".pdf"):
        name = name[:-4]
    return name


def _contains_any(text: str, keywords: List[str]) -> bool:
    t = _normalize_text(text).lower()
    return any(k.lower() in t for k in keywords)


def _find_index_sheet_name(xls: pd.ExcelFile) -> Optional[str]:
    for s in xls.sheet_names:
        if s.startswith("00_") and ("\u7d22\u5f15" in s or "index" in s.lower()):
            return s
    return xls.sheet_names[0] if xls.sheet_names else None


def _read_02a_source_pdf(file_02a: Optional[Path]) -> str:
    if not file_02a or not file_02a.exists():
        return ""
    try:
        xls = pd.ExcelFile(file_02a, engine="openpyxl")
        sheet = _find_index_sheet_name(xls)
        if not sheet:
            return ""
        df = pd.read_excel(file_02a, sheet_name=sheet, engine="openpyxl")
        if df.empty:
            return ""
        col = next((c for c in df.columns if _normalize_text(c) == "source_pdf"), None)
        if col is None:
            col = next(
                (
                    c
                    for c in df.columns
                    if _contains_any(_normalize_text(c), ["source", "pdf", "\u6765\u6e90"])
                ),
                None,
            )
        if col is None:
            return ""
        vals = [v for v in df[col].tolist() if _normalize_text(v)]
        return _normalize_text(vals[0]) if vals else ""
    except Exception:
        return ""


def _read_03_report_name(file_03: Optional[Path]) -> str:
    if not file_03 or not file_03.exists():
        return ""
    try:
        df = pd.read_excel(file_03, engine="openpyxl")
        if df.empty:
            return ""
        preferred_col = next(
            (
                c
                for c in df.columns
                if _contains_any(_normalize_text(c), ["\u7814\u62a5\u540d\u79f0", "\u62a5\u544a", "report", "doc"])
            ),
            None,
        )
        if preferred_col is not None:
            vals = [v for v in df[preferred_col].tolist() if _normalize_text(v)]
            if vals:
                return _normalize_text(vals[0])
        for _, row in df.iterrows():
            for v in row.tolist():
                text = _normalize_text(v)
                if text:
                    return text
        return ""
    except Exception:
        return ""


def _read_10_source_pdf(file_10: Optional[Path]) -> str:
    if not file_10 or not file_10.exists():
        return ""
    try:
        xls = pd.ExcelFile(file_10, engine="openpyxl")
        sheet = "summary" if "summary" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(file_10, sheet_name=sheet, engine="openpyxl")
        if df.empty:
            return ""
        col = next((c for c in df.columns if _normalize_text(c) == "source_pdf"), None)
        if col is None:
            col = next(
                (
                    c
                    for c in df.columns
                    if _contains_any(_normalize_text(c), ["source", "pdf", "\u6765\u6e90"])
                ),
                None,
            )
        if col is None:
            return ""
        vals = [v for v in df[col].tolist() if _normalize_text(v)]
        return _normalize_text(vals[0]) if vals else ""
    except Exception:
        return ""


def _read_09_map(file_09: Optional[Path]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    if not file_09 or not file_09.exists():
        return result
    try:
        xls = pd.ExcelFile(file_09, engine="openpyxl")
        sheet = "batch_status" if "batch_status" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(file_09, sheet_name=sheet, engine="openpyxl")
        if df.empty or "asset_package_path" not in df.columns or "doc_name" not in df.columns:
            return result
        for _, row in df.iterrows():
            pkg_path = _normalize_text(row.get("asset_package_path", ""))
            doc_name = _normalize_text(row.get("doc_name", ""))
            if not pkg_path or not doc_name:
                continue
            pkg_name = Path(pkg_path).name
            stem = _stem_from_pdf_like(doc_name)
            if pkg_name and stem:
                result[pkg_name] = stem
    except Exception:
        return result
    return result


def _status_from_flags(flags: List[str]) -> str:
    mismatch_flags = [
        "02A_source_mismatch",
        "03_report_mismatch",
        "probe_source_mismatch",
        "mixed_artifact_sources",
        "batch_status_mismatch",
    ]
    if not flags:
        return "OK"
    if "mixed_artifact_sources" in flags:
        return "BAD"
    if sum(1 for x in flags if x in mismatch_flags) >= 2:
        return "BAD"
    return "WARNING"


def _diagnose(
    package_stem: str,
    source_02a: str,
    report_name_03: str,
    source_10: str,
    batch_doc_stem: str,
    missing_core: List[str],
    missing_optional: List[str],
) -> Tuple[str, str, str]:
    flags: List[str] = []
    recommendations: List[str] = []

    stem_02a = _stem_from_pdf_like(source_02a)
    stem_03 = _stem_from_pdf_like(report_name_03)
    stem_10 = _stem_from_pdf_like(source_10)

    if missing_core:
        flags.append("missing_core_artifacts")
        recommendations.append("补齐核心产物 02A/02/05 后再做跨层对比")

    # Optional artifacts are recorded, but should not block consistency by themselves.
    if missing_optional:
        flags.append("missing_optional_artifacts")

    if stem_02a and stem_02a != package_stem:
        flags.append("02A_source_mismatch")
        recommendations.append("核查 02A source_pdf 与资产包 stem 是否一致")

    if stem_03 and stem_03 != package_stem:
        flags.append("03_report_mismatch")
        recommendations.append("核查 03 研报名称字段与资产包 stem 是否一致")

    if stem_10 and stem_10 != package_stem:
        flags.append("probe_source_mismatch")
        recommendations.append("核查 10 probe summary source_pdf 与资产包 stem 是否一致")

    known = [s for s in [stem_02a, stem_03, stem_10] if s]
    if len(set(known)) >= 2:
        flags.append("mixed_artifact_sources")
        recommendations.append("疑似混包：多个产物来源指向不同 PDF")

    if batch_doc_stem and batch_doc_stem != package_stem:
        flags.append("batch_status_mismatch")
        recommendations.append("核查 09_batch_run_status 的 doc_name 与资产包路径")

    # Deduplicate while preserving order.
    uniq = []
    for f in flags:
        if f not in uniq:
            uniq.append(f)
    flags = uniq

    status = _status_from_flags(flags)
    if not recommendations:
        recommendations.append("可继续沿用当前资产包")
    return status, "|".join(flags), "；".join(dict.fromkeys(recommendations))


def build_consistency_report(output_dir: str, report_path: str) -> Tuple[str, pd.DataFrame]:
    root = Path(output_dir)
    asset_pkgs = _find_asset_packages(root)
    batch_map = _read_09_map(_find_09_file(root))

    rows: List[Dict[str, object]] = []
    for pkg in asset_pkgs:
        package_stem = _package_stem(pkg.name)

        file_02a = _find_prefixed_xlsx(pkg, "02A_")
        file_02 = _find_02_file(pkg)
        file_05 = _find_prefixed_xlsx(pkg, "05_")
        file_03 = _find_prefixed_xlsx(pkg, "03_")
        file_10 = _find_10_file(pkg)

        has_02a = bool(file_02a)
        has_02 = bool(file_02)
        has_05 = bool(file_05)
        has_03 = bool(file_03)
        has_10 = bool(file_10)

        missing_core: List[str] = []
        if not has_02a:
            missing_core.append("02A")
        if not has_02:
            missing_core.append("02")
        if not has_05:
            missing_core.append("05")

        missing_optional: List[str] = []
        if not has_03:
            missing_optional.append("03")
        if not has_10:
            missing_optional.append("10_probe")

        source_02a = _read_02a_source_pdf(file_02a)
        report_03 = _read_03_report_name(file_03)
        source_10 = _read_10_source_pdf(file_10)
        batch_doc_stem = batch_map.get(pkg.name, "")

        status, flags, recommendation = _diagnose(
            package_stem=package_stem,
            source_02a=source_02a,
            report_name_03=report_03,
            source_10=source_10,
            batch_doc_stem=batch_doc_stem,
            missing_core=missing_core,
            missing_optional=missing_optional,
        )

        can_join = bool(has_02a and has_02 and has_05)

        rows.append(
            {
                "asset_package": pkg.name,
                "package_stem": package_stem,
                "source_pdf_from_02A": source_02a,
                "report_name_from_03": report_03,
                "source_pdf_from_10": source_10,
                "has_02A": has_02a,
                "has_02": has_02,
                "has_05": has_05,
                "has_03": has_03,
                "has_10_probe": has_10,
                "missing_core_artifacts": "|".join(missing_core),
                "missing_optional_artifacts": "|".join(missing_optional),
                "can_join_financial_regression": can_join,
                "consistency_status": status,
                "issue_flags": flags,
                "recommendation": recommendation,
            }
        )

    summary_df = pd.DataFrame(
        rows,
        columns=[
            "asset_package",
            "package_stem",
            "source_pdf_from_02A",
            "report_name_from_03",
            "source_pdf_from_10",
            "has_02A",
            "has_02",
            "has_05",
            "has_03",
            "has_10_probe",
            "missing_core_artifacts",
            "missing_optional_artifacts",
            "can_join_financial_regression",
            "consistency_status",
            "issue_flags",
            "recommendation",
        ],
    )

    final_path = _save_excel_robustly({"summary": summary_df}, Path(report_path))
    return final_path, summary_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Check asset package source consistency across artifacts.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory containing *_资产包")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH, help="Consistency report output path")
    args = parser.parse_args()

    report_path, summary_df = build_consistency_report(args.output_dir, args.report_path)
    print(f"report_path={report_path}")
    for _, row in summary_df.iterrows():
        print(
            f"{row['asset_package']} | {row['consistency_status']} | "
            f"{row['issue_flags']} | can_join={row['can_join_financial_regression']}"
        )


if __name__ == "__main__":
    main()
