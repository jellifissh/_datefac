import argparse
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output")
DEFAULT_INPUT_DIR = Path(r"D:\_datefac\input")
DEFAULT_REPORT_08 = Path(r"D:\_datefac\output\08_批量回归报告.xlsx")
DEFAULT_REPORT_19 = Path(r"D:\_datefac\output\19_financial_value_validation_report.xlsx")
DEFAULT_REPORT_22 = Path(r"D:\_datefac\output\22_manual_review_queue.xlsx")
DEFAULT_REPORT_12 = Path(r"D:\_datefac\output\12_asset_consistency_report.xlsx")
DEFAULT_REPORT_09 = Path(r"D:\_datefac\output\09_batch_run_status.xlsx")
DEFAULT_OUTPUT_23_XLSX = Path(r"D:\_datefac\output\23_baseline_evaluation_report.xlsx")
DEFAULT_OUTPUT_23_MD = Path(r"D:\_datefac\output\23_baseline_evaluation_summary.md")

TIER_ORDER = [
    "A_usable",
    "B_partial_review",
    "C_label_only_untrusted",
    "D_insufficient",
    "E_hard_sample",
]


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_int(v, default: int = 0) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _to_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    text = _norm(v).lower()
    return text in {"1", "true", "yes", "y"}


def _split_flags(s: str) -> List[str]:
    text = _norm(s)
    if not text:
        return []
    out = []
    for part in text.replace(";", "|").replace(",", "|").split("|"):
        p = part.strip()
        if p:
            out.append(p)
    return out


def _safe_sheet_name(name: str, used: set) -> str:
    raw = _norm(name) or "Sheet"
    clean = "".join("_" if c in "\\/*?:[]"
                    else c for c in raw)[:31] or "Sheet"
    base = clean
    i = 1
    while clean in used:
        suffix = f"_{i}"
        clean = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(clean)
    return clean


def _save_excel_robust(sheet_map: Dict[str, pd.DataFrame], output_path: Path) -> str:
    final_path = output_path
    if output_path.exists():
        try:
            with open(output_path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = output_path.with_name(f"{output_path.stem}_copy_{ts}{output_path.suffix}")

    used = set()
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for sheet, df in sheet_map.items():
            safe = _safe_sheet_name(sheet, used)
            out_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            out_df.to_excel(writer, sheet_name=safe, index=False)
    return str(final_path)


def _write_text_robust(path: Path, text: str) -> str:
    final_path = path
    if path.exists():
        try:
            path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final_path.write_text(text, encoding="utf-8")
    return str(final_path)


def _find_latest_by_prefix(root: Path, prefix: str) -> Optional[Path]:
    cands = [p for p in root.glob(f"{prefix}_*.xlsx") if p.is_file()]
    if not cands:
        return None
    return sorted(cands, key=lambda x: x.stat().st_mtime, reverse=True)[0]


def _resolve_path(preferred: Optional[Path], root: Path, prefix: str) -> Optional[Path]:
    if preferred and preferred.exists():
        return preferred
    return _find_latest_by_prefix(root, prefix)


def _read_sheet(path: Optional[Path], sheet_name: str) -> pd.DataFrame:
    if not path or not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl").fillna("")
    except Exception:
        return pd.DataFrame()


def _get_git_head(repo_root: Path) -> str:
    try:
        cp = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return cp.stdout.strip()
    except Exception:
        return ""


def _metric_top_flags(metric_detail_df: pd.DataFrame, topn: int = 3) -> str:
    cnt = Counter()
    for _, r in metric_detail_df.iterrows():
        for f in _split_flags(r.get("issue_flags", "")):
            cnt[f] += 1
    if not cnt:
        return ""
    return "|".join([f"{k}:{v}" for k, v in cnt.most_common(topn)])


def _mode_or_empty(values: List[str]) -> str:
    vals = [v for v in values if _norm(v)]
    if not vals:
        return ""
    return Counter(vals).most_common(1)[0][0]


def _find_asset_dirs(output_dir: Path) -> List[Path]:
    return sorted([p for p in output_dir.iterdir() if p.is_dir() and p.name.endswith("_资产包")]) if output_dir.exists() else []


def _best_probe_for_asset(asset_dir: Path) -> str:
    try:
        cands = [p for p in asset_dir.glob("21_*.xlsx") if p.is_file()]
        if not cands:
            return ""
        p = sorted(cands, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        g = _read_sheet(p, "group_summary")
        if g.empty or "value_valid_metric_count" not in g.columns:
            return "probe_exists_no_value"
        best = _to_int(pd.to_numeric(g["value_valid_metric_count"], errors="coerce").fillna(0).max(), 0)
        return f"best_value_valid_metric_count={best}"
    except Exception as exc:
        return f"probe_read_error:{exc}"


def build_baseline_report(
    output_dir: Path,
    input_dir: Path,
    report_08: Optional[Path],
    report_19: Optional[Path],
    report_22: Optional[Path],
    report_12: Optional[Path],
    report_09: Optional[Path],
    output_xlsx: Path,
    output_md: Path,
) -> Tuple[str, str, Dict[str, object]]:
    r08 = _resolve_path(report_08, output_dir, "08")
    r19 = _resolve_path(report_19, output_dir, "19")
    r22 = _resolve_path(report_22, output_dir, "22")

    if not r08 or not r08.exists():
        raise FileNotFoundError("08 regression report not found.")
    if not r19 or not r19.exists():
        raise FileNotFoundError("19 value validation report not found.")
    if not r22 or not r22.exists():
        raise FileNotFoundError("22 manual review queue report not found.")

    s08 = _read_sheet(r08, "summary")
    fm08 = _read_sheet(r08, "financial_metrics")
    a19 = _read_sheet(r19, "asset_value_summary")
    c19 = _read_sheet(r19, "metric_candidate_summary")
    d19 = _read_sheet(r19, "metric_value_details")
    rs22 = _read_sheet(r22, "review_summary")
    mr22 = _read_sheet(r22, "metric_review_queue")
    iv22 = _read_sheet(r22, "invalid_value_examples")
    hs22 = _read_sheet(r22, "hard_samples")
    s12 = _read_sheet(report_12 if report_12 and report_12.exists() else None, "summary")
    s09 = _read_sheet(report_09 if report_09 and report_09.exists() else None, "summary")

    if s08.empty:
        raise RuntimeError("08 summary sheet is empty.")

    # baseline_summary
    total_pdf_count = len(list(input_dir.glob("*.pdf"))) if input_dir.exists() else 0
    total_asset_packages = len(s08)
    eligible_mask = s08["regression_eligible"].apply(_to_bool) if "regression_eligible" in s08.columns else pd.Series([False] * len(s08))
    eligible_df = s08[eligible_mask].copy()

    tier_counts = {t: 0 for t in TIER_ORDER}
    if "data_usability_tier" in eligible_df.columns:
        vc = eligible_df["data_usability_tier"].astype(str).value_counts()
        for t in TIER_ORDER:
            tier_counts[t] = _to_int(vc.get(t, 0), 0)

    total_label_hit_metrics = _to_int(pd.to_numeric(eligible_df.get("label_hit_metric_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum(), 0)
    total_value_valid_metrics = _to_int(pd.to_numeric(eligible_df.get("value_valid_metric_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum(), 0)
    denom = max(1, len(eligible_df) * 8)
    overall_value_valid_ratio = round(total_value_valid_metrics / denom, 4)
    invalid_blocked_count = _to_int(pd.to_numeric(eligible_df.get("invalid_blocked_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum(), 0)

    p_counter = Counter(rs22.get("review_priority", pd.Series(dtype=str)).astype(str).tolist()) if not rs22.empty else Counter()

    repo_root = Path(__file__).resolve().parents[1]
    git_head = _get_git_head(repo_root)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    baseline_summary_df = pd.DataFrame([
        {
            "generated_at": generated_at,
            "git_head": git_head,
            "total_pdf_count": total_pdf_count,
            "total_asset_packages": total_asset_packages,
            "regression_eligible_asset_count": len(eligible_df),
            "A_usable_count": tier_counts["A_usable"],
            "B_partial_review_count": tier_counts["B_partial_review"],
            "C_label_only_untrusted_count": tier_counts["C_label_only_untrusted"],
            "D_insufficient_count": tier_counts["D_insufficient"],
            "E_hard_sample_count": tier_counts["E_hard_sample"],
            "total_label_hit_metrics": total_label_hit_metrics,
            "total_value_valid_metrics": total_value_valid_metrics,
            "overall_value_valid_ratio": overall_value_valid_ratio,
            "invalid_blocked_count": invalid_blocked_count,
            "manual_review_p0_count": _to_int(p_counter.get("P0", 0)),
            "manual_review_p1_count": _to_int(p_counter.get("P1", 0)),
            "manual_review_p2_count": _to_int(p_counter.get("P2", 0)),
            "manual_review_p3_count": _to_int(p_counter.get("P3", 0)),
        }
    ])

    # asset_quality_matrix
    asset_matrix = s08.copy()
    if "asset_package" not in asset_matrix.columns:
        raise RuntimeError("08 summary missing asset_package.")

    value_issue_map = {}
    if not a19.empty and "asset_package" in a19.columns:
        for _, r in a19.iterrows():
            value_issue_map[_norm(r.get("asset_package"))] = _norm(r.get("primary_value_issue"))

    review_map = {}
    if not rs22.empty and "asset_package" in rs22.columns:
        for _, r in rs22.iterrows():
            review_map[_norm(r.get("asset_package"))] = {
                "review_priority": _norm(r.get("review_priority")),
                "recommended_action": _norm(r.get("recommended_action")),
            }

    asset_rows = []
    for _, r in asset_matrix.iterrows():
        asset = _norm(r.get("asset_package"))
        rr = review_map.get(asset, {})
        asset_rows.append(
            {
                "asset_package": asset,
                "consistency_status": _norm(r.get("consistency_status")),
                "regression_eligible": _to_bool(r.get("regression_eligible")),
                "data_usability_tier": _norm(r.get("data_usability_tier")),
                "label_hit_metric_count": _to_int(r.get("label_hit_metric_count")),
                "value_valid_metric_count": _to_int(r.get("value_valid_metric_count")),
                "value_valid_ratio": _to_float(r.get("value_valid_ratio")),
                "primary_bottleneck": _norm(r.get("primary_bottleneck")),
                "primary_value_issue": value_issue_map.get(asset, ""),
                "review_priority": rr.get("review_priority", ""),
                "recommended_action": rr.get("recommended_action", ""),
            }
        )
    asset_quality_matrix_df = pd.DataFrame(asset_rows)

    # metric_quality_matrix
    metric_rows = []
    if not c19.empty and "standard_metric" in c19.columns and "asset_package" in c19.columns:
        assets_in_scope = sorted(c19["asset_package"].astype(str).unique().tolist())
        metric_names = sorted(c19["standard_metric"].astype(str).unique().tolist())
        for metric in metric_names:
            mdf = c19[c19["standard_metric"].astype(str) == metric]
            label_hit_count = _to_int((pd.to_numeric(mdf.get("candidate_count", 0), errors="coerce").fillna(0) > 0).sum(), 0)
            value_valid_count = _to_int((mdf.get("metric_value_status", "").astype(str) == "valid").sum(), 0)
            value_invalid_count = _to_int((mdf.get("metric_value_status", "").astype(str) == "invalid").sum(), 0)
            value_suspicious_count = _to_int((mdf.get("metric_value_status", "").astype(str) == "suspicious").sum(), 0)
            missing_count = _to_int((mdf.get("metric_value_status", "").astype(str) == "missing").sum(), 0)
            denom_metric = max(1, len(assets_in_scope))
            valid_ratio = round(value_valid_count / denom_metric, 4)
            dmetric = d19[d19["standard_metric"].astype(str) == metric] if not d19.empty else pd.DataFrame()
            top_flags = _metric_top_flags(dmetric)
            metric_rows.append(
                {
                    "standard_metric": metric,
                    "label_hit_count": label_hit_count,
                    "value_valid_count": value_valid_count,
                    "value_invalid_count": value_invalid_count,
                    "value_suspicious_count": value_suspicious_count,
                    "missing_count": missing_count,
                    "valid_ratio": valid_ratio,
                    "top_issue_flags": top_flags,
                }
            )
    metric_quality_matrix_df = pd.DataFrame(metric_rows)

    # issue_distribution
    issue_acc = defaultdict(lambda: {"occurrence_count": 0, "assets": set(), "metrics": set(), "examples": []})
    if not d19.empty:
        for _, r in d19.iterrows():
            flags = _split_flags(r.get("issue_flags", ""))
            if not flags:
                continue
            asset = _norm(r.get("asset_package"))
            metric = _norm(r.get("standard_metric"))
            raw = _norm(r.get("raw_value"))
            for f in flags:
                rec = issue_acc[f]
                rec["occurrence_count"] += 1
                if asset:
                    rec["assets"].add(asset)
                if metric:
                    rec["metrics"].add(metric)
                if raw and len(rec["examples"]) < 3 and raw not in rec["examples"]:
                    rec["examples"].append(raw)

    issue_rows = []
    for flag, rec in issue_acc.items():
        issue_rows.append(
            {
                "issue_flag": flag,
                "occurrence_count": rec["occurrence_count"],
                "affected_asset_count": len(rec["assets"]),
                "affected_metrics": "|".join(sorted(rec["metrics"])),
                "example_values": "|".join(rec["examples"]),
            }
        )
    issue_distribution_df = pd.DataFrame(issue_rows).sort_values("occurrence_count", ascending=False) if issue_rows else pd.DataFrame()

    # manual_review_overview
    manual_rows = []
    if not rs22.empty and "review_priority" in rs22.columns:
        priorities = sorted([p for p in rs22["review_priority"].astype(str).unique().tolist() if p])
        metric_join = pd.DataFrame()
        invalid_join = pd.DataFrame()
        if not mr22.empty and "asset_package" in mr22.columns:
            metric_join = mr22.merge(rs22[["asset_package", "review_priority"]], on="asset_package", how="left")
        if not iv22.empty and "asset_package" in iv22.columns:
            invalid_join = iv22.merge(rs22[["asset_package", "review_priority"]], on="asset_package", how="left")
        for p in priorities:
            s = rs22[rs22["review_priority"].astype(str) == p]
            asset_count = len(s["asset_package"].astype(str).unique())
            metric_review_count = len(metric_join[metric_join["review_priority"].astype(str) == p]) if not metric_join.empty else 0
            invalid_value_count = len(invalid_join[invalid_join["review_priority"].astype(str) == p]) if not invalid_join.empty else 0
            typical_reason = _mode_or_empty(s.get("review_reason", pd.Series(dtype=str)).astype(str).tolist())
            action = _mode_or_empty(s.get("recommended_action", pd.Series(dtype=str)).astype(str).tolist())
            manual_rows.append(
                {
                    "review_priority": p,
                    "asset_count": asset_count,
                    "metric_review_count": metric_review_count,
                    "invalid_value_count": invalid_value_count,
                    "typical_reason": typical_reason,
                    "recommended_action": action,
                }
            )
    manual_review_overview_df = pd.DataFrame(manual_rows)

    # hard_samples
    hard_rows = []
    if not hs22.empty and "asset_package" in hs22.columns:
        for _, r in hs22.iterrows():
            asset = _norm(r.get("asset_package"))
            asset_dir = output_dir / asset
            best_probe = _best_probe_for_asset(asset_dir) if asset_dir.exists() else ""
            hard_rows.append(
                {
                    "asset_package": asset,
                    "reason": _norm(r.get("reason")),
                    "best_probe_result": best_probe or _norm(r.get("best_value_valid_metric_count")),
                    "next_action": _norm(r.get("next_action")),
                }
            )
    else:
        # fallback from 08 tier
        for _, r in s08.iterrows():
            if _norm(r.get("data_usability_tier")) != "E_hard_sample":
                continue
            asset = _norm(r.get("asset_package"))
            asset_dir = output_dir / asset
            hard_rows.append(
                {
                    "asset_package": asset,
                    "reason": "tier=E_hard_sample",
                    "best_probe_result": _best_probe_for_asset(asset_dir) if asset_dir.exists() else "",
                    "next_action": "consider stronger backend or manual review",
                }
            )
    hard_samples_df = pd.DataFrame(hard_rows)

    # next_iteration_plan static
    next_iteration_plan_df = pd.DataFrame(
        [
            {
                "priority": "P0",
                "task": "审计并隔离 hard sample",
                "target_files": "22_manual_review_queue.xlsx, 21_column_group_binding_probe.xlsx",
                "expected_gain": "避免困难样本误导整体迭代方向",
                "risk_level": "low",
                "should_do_next": True,
            },
            {
                "priority": "P1",
                "task": "优化 D_insufficient 样本抽取覆盖",
                "target_files": "02A/06A 诊断报告, 08 summary",
                "expected_gain": "提升 label_hit 覆盖与可回归样本质量",
                "risk_level": "medium",
                "should_do_next": True,
            },
            {
                "priority": "P1",
                "task": "增强列绑定/表头对齐诊断与策略",
                "target_files": "financial_standardizer.py probes, 19 report",
                "expected_gain": "提升 value_valid_ratio",
                "risk_level": "medium",
                "should_do_next": True,
            },
            {
                "priority": "P2",
                "task": "扩展到 30 份样本回归",
                "target_files": "08/19/22 aggregate reports",
                "expected_gain": "验证泛化，识别过拟合",
                "risk_level": "low",
                "should_do_next": True,
            },
            {
                "priority": "P2",
                "task": "接入更强后端 POC（隔离分支）",
                "target_files": "extractor probes only",
                "expected_gain": "改善 hard sample 与低覆盖样本",
                "risk_level": "medium",
                "should_do_next": False,
            },
            {
                "priority": "P3",
                "task": "加入人工复核 UI/API",
                "target_files": "22/23 reports as backend data source",
                "expected_gain": "缩短人工闭环时间",
                "risk_level": "medium",
                "should_do_next": False,
            },
        ]
    )

    excel_path = _save_excel_robust(
        {
            "baseline_summary": baseline_summary_df,
            "asset_quality_matrix": asset_quality_matrix_df,
            "metric_quality_matrix": metric_quality_matrix_df,
            "issue_distribution": issue_distribution_df,
            "manual_review_overview": manual_review_overview_df,
            "hard_samples": hard_samples_df,
            "next_iteration_plan": next_iteration_plan_df,
        },
        output_xlsx,
    )

    top_issues = []
    if not issue_distribution_df.empty:
        for _, r in issue_distribution_df.head(5).iterrows():
            top_issues.append(f"- `{_norm(r.get('issue_flag'))}`: {_to_int(r.get('occurrence_count'))}")
    top_issues_text = "\n".join(top_issues) if top_issues else "- 无明显 issue flag 记录"

    md_text = "\n".join(
        [
            "# Baseline Evaluation Summary",
            "",
            "## 1. 一句话结论",
            f"当前基线在标签命中上可用，但值有效性仍是主要瓶颈（overall_value_valid_ratio={overall_value_valid_ratio}）。",
            "",
            "## 2. 样本覆盖情况",
            f"- total_pdf_count: {total_pdf_count}",
            f"- total_asset_packages: {total_asset_packages}",
            f"- regression_eligible_asset_count: {len(eligible_df)}",
            f"- consistency_report_available: {not s12.empty}",
            f"- batch_status_available: {not s09.empty}",
            "",
            "## 3. A/B/C/D/E 分层统计",
            f"- A_usable: {tier_counts['A_usable']}",
            f"- B_partial_review: {tier_counts['B_partial_review']}",
            f"- C_label_only_untrusted: {tier_counts['C_label_only_untrusted']}",
            f"- D_insufficient: {tier_counts['D_insufficient']}",
            f"- E_hard_sample: {tier_counts['E_hard_sample']}",
            "",
            "## 4. 标签命中 vs 值有效统计",
            f"- total_label_hit_metrics: {total_label_hit_metrics}",
            f"- total_value_valid_metrics: {total_value_valid_metrics}",
            f"- overall_value_valid_ratio: {overall_value_valid_ratio}",
            f"- invalid_blocked_count: {invalid_blocked_count}",
            "",
            "## 5. 主要问题分布",
            top_issues_text,
            "",
            "## 6. 当前可上线能力边界",
            "- A/B 层样本可用于半自动分析，需保留人工复核。",
            "- D/E 层样本不应直接进入自动结论链路。",
            "- hard sample 需单独策略或更强后端支持。",
            "",
            "## 7. 下一轮建议",
            "- 先处理 P0/P1 人工复核队列并固化修复收益口径。",
            "- 对 D_insufficient 做抽取覆盖审计后再扩样本到 30 份。",
            "- 保持主流程稳定，优先在独立 probe 中验证高风险改动。",
            "",
        ]
    )
    md_path = _write_text_robust(output_md, md_text)

    stats = {
        "A_usable_count": tier_counts["A_usable"],
        "B_partial_review_count": tier_counts["B_partial_review"],
        "C_label_only_untrusted_count": tier_counts["C_label_only_untrusted"],
        "D_insufficient_count": tier_counts["D_insufficient"],
        "E_hard_sample_count": tier_counts["E_hard_sample"],
        "total_label_hit_metrics": total_label_hit_metrics,
        "total_value_valid_metrics": total_value_valid_metrics,
        "overall_value_valid_ratio": overall_value_valid_ratio,
        "manual_review_p0_count": _to_int(p_counter.get("P0", 0)),
        "manual_review_p1_count": _to_int(p_counter.get("P1", 0)),
        "manual_review_p2_count": _to_int(p_counter.get("P2", 0)),
        "manual_review_p3_count": _to_int(p_counter.get("P3", 0)),
    }
    return excel_path, md_path, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Build baseline evaluation report from 08/19/22.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--report-08", default=str(DEFAULT_REPORT_08))
    parser.add_argument("--report-19", default=str(DEFAULT_REPORT_19))
    parser.add_argument("--report-22", default=str(DEFAULT_REPORT_22))
    parser.add_argument("--report-12", default=str(DEFAULT_REPORT_12))
    parser.add_argument("--report-09", default=str(DEFAULT_REPORT_09))
    parser.add_argument("--output-xlsx", default=str(DEFAULT_OUTPUT_23_XLSX))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_23_MD))
    args = parser.parse_args()

    excel_path, md_path, stats = build_baseline_report(
        output_dir=Path(args.output_dir),
        input_dir=Path(args.input_dir),
        report_08=Path(args.report_08),
        report_19=Path(args.report_19),
        report_22=Path(args.report_22),
        report_12=Path(args.report_12),
        report_09=Path(args.report_09),
        output_xlsx=Path(args.output_xlsx),
        output_md=Path(args.output_md),
    )

    print(f"Excel 路径: {excel_path}")
    print(f"Markdown 路径: {md_path}")
    print(
        "A/B/C/D/E: "
        f"{stats['A_usable_count']}/{stats['B_partial_review_count']}/"
        f"{stats['C_label_only_untrusted_count']}/{stats['D_insufficient_count']}/"
        f"{stats['E_hard_sample_count']}"
    )
    print(f"total_label_hit_metrics: {stats['total_label_hit_metrics']}")
    print(f"total_value_valid_metrics: {stats['total_value_valid_metrics']}")
    print(f"overall_value_valid_ratio: {stats['overall_value_valid_ratio']}")
    print(
        "manual_review_priority: "
        f"P0={stats['manual_review_p0_count']}, "
        f"P1={stats['manual_review_p1_count']}, "
        f"P2={stats['manual_review_p2_count']}, "
        f"P3={stats['manual_review_p3_count']}"
    )


if __name__ == "__main__":
    main()

