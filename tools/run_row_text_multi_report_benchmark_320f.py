from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.recognizer_worklist_builder import build_recognizer_worklist
from datefac.benchmark.row_text_delivery_benchmark import benchmark_delivery_outputs


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


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_table_level_metrics(delivery_seed_df: pd.DataFrame, table_assets_df: pd.DataFrame) -> pd.DataFrame:
    if delivery_seed_df.empty and table_assets_df.empty:
        return pd.DataFrame(columns=[
            "source_report_name",
            "table_asset_id",
            "table_role_guess",
            "image_path",
            "image_exists",
            "has_ppstructure_output",
            "has_320c4_candidates",
            "has_320d2_mapping",
            "has_320e_delivery",
            "candidate_count",
            "trusted_count",
            "review_required_count",
            "key_metric_hit_count",
            "table_status",
        ])

    d = delivery_seed_df.copy() if not delivery_seed_df.empty else pd.DataFrame(columns=[
        "source_report_name",
        "source_table_id",
        "candidate_count",
        "trusted_count",
        "review_required_count",
        "rejected_count",
        "key_metric_hit_count",
        "has_320c4_candidates",
        "has_320d2_mapping",
        "has_320e_delivery",
    ])
    d["source_report_name"] = d.get("source_report_name", "").astype(str)
    d["source_table_id"] = d.get("source_table_id", "").astype(str)

    t = table_assets_df.copy() if not table_assets_df.empty else pd.DataFrame(columns=[
        "report_name",
        "table_asset_id",
        "table_role_guess",
        "image_path",
        "image_exists",
        "role_category",
    ])
    t["source_report_name"] = t.get("report_name", "").astype(str)

    # fuzzy join: if report has exactly one delivery table, map all metrics to first high-priority table asset
    if not d.empty and not t.empty:
        selected_assets: List[pd.Series] = []
        for report_name, g in t.groupby("source_report_name", dropna=False):
            g2 = g.copy()
            g2["role_rank"] = g2.get("role_category", "").astype(str).map(
                {
                    "BALANCE_SHEET": 1,
                    "INCOME_STATEMENT": 1,
                    "CASH_FLOW_STATEMENT": 1,
                    "CORE_METRIC_TABLE": 2,
                    "FINANCIAL_FORECAST_VALUATION": 2,
                    "BUSINESS_ASSUMPTION": 3,
                    "BASIC_DATA": 4,
                    "RATING_STANDARD": 8,
                    "DISCLAIMER_OR_LEGAL": 8,
                    "UNKNOWN_TABLE": 9,
                }
            ).fillna(9)
            g2 = g2.sort_values(["role_rank", "image_exists"], ascending=[True, False])
            selected_assets.append(g2.iloc[0])
        asset_pick_df = pd.DataFrame(selected_assets)
        merged = d.merge(asset_pick_df[["source_report_name", "table_asset_id", "table_role_guess", "image_path", "image_exists"]], on="source_report_name", how="left")
    else:
        merged = d.copy()
        if "table_asset_id" not in merged.columns:
            merged["table_asset_id"] = merged.get("source_table_id", "")
        if "table_role_guess" not in merged.columns:
            merged["table_role_guess"] = ""
        if "image_path" not in merged.columns:
            merged["image_path"] = ""
        if "image_exists" not in merged.columns:
            merged["image_exists"] = False

    if merged.empty and not t.empty:
        merged = pd.DataFrame(
            {
                "source_report_name": t["source_report_name"],
                "source_table_id": "",
                "table_asset_id": t.get("table_asset_id", ""),
                "table_role_guess": t.get("table_role_guess", ""),
                "image_path": t.get("image_path", ""),
                "image_exists": t.get("image_exists", False),
                "candidate_count": 0,
                "trusted_count": 0,
                "review_required_count": 0,
                "key_metric_hit_count": 0,
                "has_320c4_candidates": False,
                "has_320d2_mapping": False,
                "has_320e_delivery": False,
            }
        )

    merged["has_ppstructure_output"] = merged.get("candidate_count", 0).fillna(0).astype(int) > 0
    merged["table_status"] = merged.apply(
        lambda r: "READY_SAMPLE"
        if int(r.get("trusted_count", 0)) > 0
        else ("MAPPING_ONLY_AVAILABLE" if int(r.get("candidate_count", 0)) > 0 else "MINERU_TABLE_ASSET_ONLY"),
        axis=1,
    )

    out = merged[[
        "source_report_name",
        "table_asset_id",
        "table_role_guess",
        "image_path",
        "image_exists",
        "has_ppstructure_output",
        "has_320c4_candidates",
        "has_320d2_mapping",
        "has_320e_delivery",
        "candidate_count",
        "trusted_count",
        "review_required_count",
        "key_metric_hit_count",
        "table_status",
    ]].copy()

    out = out.drop_duplicates(subset=["source_report_name", "table_asset_id", "table_role_guess", "image_path"], keep="first")
    return out.reset_index(drop=True)


def _build_report_level_metrics(sample_report_df: pd.DataFrame, table_assets_df: pd.DataFrame, provenance_df: pd.DataFrame, qa_fail_count: int) -> pd.DataFrame:
    reports = pd.DataFrame(columns=["report_name"])
    if not sample_report_df.empty:
        reports = sample_report_df[["report_name"]].drop_duplicates()
    if not table_assets_df.empty:
        x = table_assets_df[["report_name"]].rename(columns={"report_name": "report_name"}).drop_duplicates()
        reports = pd.concat([reports, x], ignore_index=True).drop_duplicates()

    if reports.empty:
        return pd.DataFrame(columns=[
            "report_name",
            "table_asset_count_from_mineru",
            "recognized_table_count",
            "delivery_sample_count",
            "trusted_count",
            "review_required_count",
            "rejected_count",
            "unique_metric_count",
            "metric_family_coverage",
            "provenance_coverage_rate",
            "qa_fail_count",
            "report_status",
        ])

    out = reports.copy()

    if table_assets_df.empty:
        out["table_asset_count_from_mineru"] = 0
    else:
        t = table_assets_df.groupby("report_name", dropna=False).size().reset_index(name="table_asset_count_from_mineru")
        out = out.merge(t, on="report_name", how="left")
        out["table_asset_count_from_mineru"] = out["table_asset_count_from_mineru"].fillna(0).astype(int)

    if sample_report_df.empty:
        fill_cols = [
            "recognized_table_count",
            "delivery_sample_count",
            "trusted_count",
            "review_required_count",
            "rejected_count",
            "unique_metric_count",
            "metric_family_coverage",
        ]
        for c in fill_cols:
            out[c] = 0
    else:
        out = out.merge(sample_report_df, on="report_name", how="left")
        for c in [
            "recognized_table_count",
            "delivery_sample_count",
            "trusted_count",
            "review_required_count",
            "rejected_count",
            "unique_metric_count",
            "metric_family_coverage",
        ]:
            out[c] = out[c].fillna(0).astype(int)

    if provenance_df.empty:
        out["provenance_coverage_rate"] = 0.0
    else:
        p = provenance_df.groupby("source_report_name", dropna=False)["provenance_complete"].mean().reset_index()
        p = p.rename(columns={"source_report_name": "report_name", "provenance_complete": "provenance_coverage_rate"})
        out = out.merge(p, on="report_name", how="left")
        out["provenance_coverage_rate"] = out["provenance_coverage_rate"].fillna(0.0)

    out["qa_fail_count"] = qa_fail_count
    out["report_status"] = out.apply(
        lambda r: (
            "HAS_QA_FAILURE"
            if qa_fail_count > 0
            else (
                "READY_SAMPLE"
                if int(r.get("trusted_count", 0)) > 0
                else (
                    "NO_RECOGNIZER_OUTPUT"
                    if int(r.get("delivery_sample_count", 0)) == 0
                    else "NEEDS_MORE_TABLE_RECOGNITION"
                )
            )
        ),
        axis=1,
    )

    return out[[
        "report_name",
        "table_asset_count_from_mineru",
        "recognized_table_count",
        "delivery_sample_count",
        "trusted_count",
        "review_required_count",
        "rejected_count",
        "unique_metric_count",
        "metric_family_coverage",
        "provenance_coverage_rate",
        "qa_fail_count",
        "report_status",
    ]].sort_values("report_name").reset_index(drop=True)


def _build_decision(summary: Dict[str, Any]) -> str:
    qa_fail_count = int(summary.get("qa_fail_count", 0))
    benchmarked_report_count = int(summary.get("benchmarked_report_count", 0))
    trusted_rate = float(summary.get("trusted_rate", 0.0))
    provenance_complete_rate = float(summary.get("provenance_complete_rate", 0.0))
    worklist_count = int(summary.get("worklist_count", 0))

    if qa_fail_count > 0:
        return "MULTI_REPORT_BENCHMARK_BLOCKED_BY_QA_FAILURE"
    if benchmarked_report_count >= 5 and trusted_rate >= 0.60 and provenance_complete_rate >= 0.95 and qa_fail_count == 0:
        return "MULTI_REPORT_BENCHMARK_READY_FOR_320G_PIPELINE_INTEGRATION_PLAN"
    if benchmarked_report_count >= 2 and qa_fail_count == 0:
        return "MULTI_REPORT_BENCHMARK_PARTIAL_NEEDS_MORE_REPORTS"
    if benchmarked_report_count < 2 and worklist_count > 0:
        return "NEED_MORE_RECOGNIZER_OUTPUTS_FROM_WORKLIST"
    return "MULTI_REPORT_BENCHMARK_NOT_READY"


def _build_report_md(path: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# Row Text Multi-Report Benchmark 320F",
        "",
        "## Input",
        f"- delivery_root: `{summary.get('delivery_root', '')}`",
        f"- mineru_output_root: `{summary.get('mineru_output_root', '')}`",
        f"- mineru_benchmark_dir: `{summary.get('mineru_benchmark_dir', '')}`",
        "",
        "## Snapshot",
        f"- discovered_delivery_bundle_count: {summary.get('discovered_delivery_bundle_count', 0)}",
        f"- benchmarked_report_count: {summary.get('benchmarked_report_count', 0)}",
        f"- benchmarked_table_count: {summary.get('benchmarked_table_count', 0)}",
        f"- mineru_report_count: {summary.get('mineru_report_count', 0)}",
        f"- mineru_table_asset_count: {summary.get('mineru_table_asset_count', 0)}",
        f"- recognizer_output_coverage_rate: {summary.get('recognizer_output_coverage_rate', 0.0)}",
        f"- trusted_total_count: {summary.get('trusted_total_count', 0)}",
        f"- review_required_total_count: {summary.get('review_required_total_count', 0)}",
        f"- rejected_total_count: {summary.get('rejected_total_count', 0)}",
        f"- trusted_rate: {summary.get('trusted_rate', 0.0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        f"- provenance_complete_rate: {summary.get('provenance_complete_rate', 0.0)}",
        f"- worklist_count: {summary.get('worklist_count', 0)}",
        f"- benchmark_decision: {summary.get('benchmark_decision', '')}",
        "",
        "## Next Recommendation",
        "- 若 worklist_count > 0，优先按 recognizer_worklist 逐条在本地 ppstructure_legacy 环境补齐识别输出，再重跑 320F。",
        "- 保持 sandbox-only，不改生产 01/02/02A/05/06，不触发 apply。",
        "",
        "## Output",
        f"- excel: `{summary.get('excel_path', '')}`",
        f"- summary_json: `{summary.get('summary_json_path', '')}`",
        f"- report_md: `{path}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 320F multi-report sandbox benchmark for row-text delivery and MinerU worklist.")
    parser.add_argument("--delivery-root", required=True)
    parser.add_argument("--mineru-output-root", required=True)
    parser.add_argument("--mineru-benchmark-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-worklist", type=int, default=30)
    args = parser.parse_args()

    delivery_root = Path(args.delivery_root).resolve()
    mineru_output_root = Path(args.mineru_output_root).resolve()
    mineru_benchmark_dir = Path(args.mineru_benchmark_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    delivery_result = benchmark_delivery_outputs(delivery_root)
    worklist_result = build_recognizer_worklist(
        mineru_output_root=mineru_output_root,
        mineru_benchmark_dir=mineru_benchmark_dir,
        recognized_report_table_keys=delivery_result.get("recognized_report_table_keys", set()),
        recognized_report_names=delivery_result.get("recognized_report_names", set()),
        recognized_source_table_ids=delivery_result.get("recognized_source_table_ids", set()),
        max_worklist=max(1, int(args.max_worklist)),
    )

    table_level_df = _build_table_level_metrics(
        delivery_seed_df=delivery_result.get("delivery_table_seed_df", pd.DataFrame()),
        table_assets_df=worklist_result.get("table_assets_df", pd.DataFrame()),
    )

    report_level_df = _build_report_level_metrics(
        sample_report_df=delivery_result.get("report_level_seed_df", pd.DataFrame()),
        table_assets_df=worklist_result.get("table_assets_df", pd.DataFrame()),
        provenance_df=delivery_result.get("provenance_coverage_df", pd.DataFrame()),
        qa_fail_count=int(delivery_result.get("qa_fail_count", 0)),
    )

    benchmarked_report_count = int(report_level_df[(report_level_df["delivery_sample_count"] > 0)]["report_name"].nunique()) if not report_level_df.empty else 0
    benchmarked_table_count = int(table_level_df[table_level_df["candidate_count"] > 0][["source_report_name", "table_asset_id"]].drop_duplicates().shape[0]) if not table_level_df.empty else 0

    summary = {
        "delivery_root": str(delivery_root),
        "mineru_output_root": str(mineru_output_root),
        "mineru_benchmark_dir": str(mineru_benchmark_dir),
        "output_dir": str(output_dir),
        "discovered_delivery_bundle_count": int(delivery_result.get("discovered_delivery_bundle_count", 0)),
        "benchmarked_report_count": benchmarked_report_count,
        "benchmarked_table_count": benchmarked_table_count,
        "mineru_report_count": int(worklist_result.get("mineru_report_count", 0)),
        "mineru_table_asset_count": int(worklist_result.get("mineru_table_asset_count", 0)),
        "recognizer_output_coverage_rate": float(worklist_result.get("recognizer_output_coverage_rate", 0.0)),
        "trusted_total_count": int(delivery_result.get("trusted_total_count", 0)),
        "review_required_total_count": int(delivery_result.get("review_required_total_count", 0)),
        "rejected_total_count": int(delivery_result.get("rejected_total_count", 0)),
        "trusted_rate": float(delivery_result.get("trusted_rate", 0.0)),
        "qa_fail_count": int(delivery_result.get("qa_fail_count", 0)),
        "provenance_complete_rate": float(delivery_result.get("provenance_complete_rate", 0.0)),
        "worklist_count": int(len(worklist_result.get("worklist_df", pd.DataFrame()))),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    summary["benchmark_decision"] = _build_decision(summary)

    summary_df = pd.DataFrame([{"metric": k, "value": v} for k, v in summary.items()])

    # benchmark decision audit
    decision_audit_df = pd.DataFrame(
        [
            {"rule": "qa_fail_count > 0", "result": int(summary["qa_fail_count"] > 0), "detail": summary["benchmark_decision"]},
            {
                "rule": "ready_threshold",
                "result": int(
                    summary["benchmarked_report_count"] >= 5
                    and summary["trusted_rate"] >= 0.60
                    and summary["provenance_complete_rate"] >= 0.95
                    and summary["qa_fail_count"] == 0
                ),
                "detail": "benchmarked_report_count>=5 & trusted_rate>=0.60 & provenance_complete_rate>=0.95 & qa_fail_count==0",
            },
            {
                "rule": "partial_threshold",
                "result": int(summary["benchmarked_report_count"] >= 2 and summary["qa_fail_count"] == 0),
                "detail": "benchmarked_report_count>=2 & qa_fail_count==0",
            },
            {
                "rule": "need_worklist",
                "result": int(summary["benchmarked_report_count"] < 2 and summary["worklist_count"] > 0),
                "detail": "benchmarked_report_count<2 & worklist_count>0",
            },
            {"rule": "final_decision", "result": 1, "detail": summary["benchmark_decision"]},
        ]
    )

    # missing recognizer outputs (ensure columns)
    missing_df = worklist_result.get("missing_recognizer_outputs_df", pd.DataFrame())
    if missing_df.empty:
        missing_df = pd.DataFrame(columns=["source_report_name", "table_asset_count", "existing_recognizer_output_count", "missing_core_table_count", "next_action"])

    # available output inventory from delivery discovery
    available_outputs_df = delivery_result.get("available_delivery_outputs_df", pd.DataFrame())

    # benchmark samples jsonl
    all_samples_df = delivery_result.get("all_samples_df", pd.DataFrame())
    samples_jsonl_path = output_dir / "benchmark_samples.jsonl"
    if not all_samples_df.empty:
        with samples_jsonl_path.open("w", encoding="utf-8") as f:
            for _, r in all_samples_df.iterrows():
                f.write(json.dumps({k: (v.item() if hasattr(v, "item") else v) for k, v in r.to_dict().items()}, ensure_ascii=False) + "\n")

    # worklist csv/jsonl
    worklist_df = worklist_result.get("worklist_df", pd.DataFrame())
    worklist_csv_path = output_dir / "recognizer_worklist.csv"
    worklist_jsonl_path = output_dir / "recognizer_worklist.jsonl"
    if not worklist_df.empty:
        worklist_df.to_csv(worklist_csv_path, index=False, encoding="utf-8-sig")
        with worklist_jsonl_path.open("w", encoding="utf-8") as f:
            for _, r in worklist_df.iterrows():
                f.write(json.dumps({k: (v.item() if hasattr(v, "item") else v) for k, v in r.to_dict().items()}, ensure_ascii=False) + "\n")

    excel_path = output_dir / "row_text_multi_report_benchmark_320f.xlsx"
    _write_excel(
        excel_path,
        {
            "summary": summary_df,
            "available_delivery_outputs": available_outputs_df,
            "benchmark_sample_inventory": delivery_result.get("benchmark_sample_inventory_df", pd.DataFrame()),
            "report_level_metrics": report_level_df,
            "table_level_metrics": table_level_df,
            "metric_coverage": delivery_result.get("metric_coverage_df", pd.DataFrame()),
            "trust_split_summary": delivery_result.get("trust_split_summary_df", pd.DataFrame()),
            "unit_year_context_summary": delivery_result.get("unit_year_context_summary_df", pd.DataFrame()),
            "provenance_coverage": delivery_result.get("provenance_coverage_df", pd.DataFrame()),
            "qa_summary": delivery_result.get("qa_summary_df", pd.DataFrame()),
            "known_limitations": delivery_result.get("known_limitations_df", pd.DataFrame()),
            "recognizer_worklist": worklist_df,
            "recognizer_worklist_commands": worklist_result.get("worklist_commands_df", pd.DataFrame()),
            "missing_recognizer_outputs": missing_df,
            "benchmark_decision_audit": decision_audit_df,
        },
    )

    summary_json_path = output_dir / "row_text_multi_report_benchmark_320f_summary.json"
    summary["excel_path"] = str(excel_path)
    summary["summary_json_path"] = str(summary_json_path)
    summary["report_md_path"] = str(output_dir / "row_text_multi_report_benchmark_320f_report.md")
    _write_json(summary_json_path, summary)

    report_md_path = output_dir / "row_text_multi_report_benchmark_320f_report.md"
    _build_report_md(report_md_path, summary)

    print(f"row_text_multi_report_benchmark_excel: {excel_path}")
    print(f"row_text_multi_report_benchmark_summary_json: {summary_json_path}")
    print(f"row_text_multi_report_benchmark_report_md: {report_md_path}")
    print(f"discovered_delivery_bundle_count: {summary['discovered_delivery_bundle_count']}")
    print(f"benchmarked_report_count: {summary['benchmarked_report_count']}")
    print(f"benchmarked_table_count: {summary['benchmarked_table_count']}")
    print(f"mineru_report_count: {summary['mineru_report_count']}")
    print(f"mineru_table_asset_count: {summary['mineru_table_asset_count']}")
    print(f"recognizer_output_coverage_rate: {summary['recognizer_output_coverage_rate']}")
    print(f"trusted_total_count: {summary['trusted_total_count']}")
    print(f"review_required_total_count: {summary['review_required_total_count']}")
    print(f"rejected_total_count: {summary['rejected_total_count']}")
    print(f"trusted_rate: {summary['trusted_rate']}")
    print(f"qa_fail_count: {summary['qa_fail_count']}")
    print(f"provenance_complete_rate: {summary['provenance_complete_rate']}")
    print(f"worklist_count: {summary['worklist_count']}")
    print(f"benchmark_decision: {summary['benchmark_decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
