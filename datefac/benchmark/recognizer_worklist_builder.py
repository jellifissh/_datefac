from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from datefac.parser.mineru_output_reader import read_mineru_output


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return _norm(v).lower() in {"1", "true", "yes", "y"}


def _stable_asset_id(report_name: str, source_file: str, block_index: Any, bbox: Any) -> str:
    seed = f"{_norm(report_name)}|{_norm(source_file)}|{_norm(block_index)}|{_norm(bbox)}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def _role_priority(role: str) -> int:
    r = _norm(role)
    if r in {"BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW_STATEMENT"}:
        return 1
    if r in {"CORE_METRIC_TABLE", "FINANCIAL_FORECAST_VALUATION"}:
        return 2
    if r in {"BUSINESS_ASSUMPTION", "BASIC_DATA"}:
        return 3
    if r in {"RATING_STANDARD", "DISCLAIMER_OR_LEGAL"}:
        return 5
    if r in {"UNKNOWN_TABLE", "", "CHART_OR_MARKET_TREND"}:
        return 9
    return 4


def _expected_metric_family(role: str) -> str:
    r = _norm(role)
    if r == "BALANCE_SHEET":
        return "balance_sheet"
    if r == "INCOME_STATEMENT":
        return "profitability"
    if r == "CASH_FLOW_STATEMENT":
        return "cash_flow"
    if r in {"CORE_METRIC_TABLE", "FINANCIAL_FORECAST_VALUATION"}:
        return "valuation"
    if r == "BUSINESS_ASSUMPTION":
        return "growth"
    return "other"


def _reason_selected(role: str, image_exists: bool) -> str:
    role_norm = _norm(role)
    reasons: List[str] = []
    if role_norm in {"BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW_STATEMENT"}:
        reasons.append("core_financial_statement")
    elif role_norm in {"CORE_METRIC_TABLE", "FINANCIAL_FORECAST_VALUATION"}:
        reasons.append("key_metric_or_valuation_table")
    else:
        reasons.append("supplementary_table")
    reasons.append("image_exists" if image_exists else "image_missing")
    return "|".join(reasons)


def _normalize_assets_df(df: pd.DataFrame, mineru_output_root: Path) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[
            "report_name",
            "source_file",
            "block_index",
            "bbox",
            "table_asset_id",
            "table_role_guess",
            "role_category",
            "image_path",
            "image_exists",
            "page_idx",
            "caption",
            "nearby_text_preview",
            "mineru_report_dir",
        ])

    out = df.copy()
    if "report_name" not in out.columns:
        out["report_name"] = ""
    if "role_category" not in out.columns:
        out["role_category"] = out.get("table_role_guess", "")
    if "table_role_guess" not in out.columns:
        out["table_role_guess"] = out.get("role_category", "")
    if "image_exists" not in out.columns:
        out["image_exists"] = out.get("image_path", "").astype(str).str.len() > 0
    else:
        out["image_exists"] = out["image_exists"].apply(_to_bool)
    if "nearby_text_preview" not in out.columns:
        if "nearby_text" in out.columns:
            out["nearby_text_preview"] = out["nearby_text"].astype(str).str[:200]
        else:
            out["nearby_text_preview"] = ""
    if "table_asset_id" not in out.columns:
        out["table_asset_id"] = out.apply(
            lambda r: _stable_asset_id(
                report_name=_norm(r.get("report_name")),
                source_file=_norm(r.get("source_file")),
                block_index=r.get("block_index"),
                bbox=r.get("bbox"),
            ),
            axis=1,
        )
    if "page_idx" not in out.columns:
        out["page_idx"] = None
    if "caption" not in out.columns:
        out["caption"] = ""
    if "bbox" not in out.columns:
        out["bbox"] = ""

    out["mineru_report_dir"] = out["report_name"].apply(lambda n: str((mineru_output_root / _norm(n)).resolve()))
    keep = [
        "report_name",
        "source_file",
        "block_index",
        "bbox",
        "table_asset_id",
        "table_role_guess",
        "role_category",
        "image_path",
        "image_exists",
        "page_idx",
        "caption",
        "nearby_text_preview",
        "mineru_report_dir",
    ]
    for c in keep:
        if c not in out.columns:
            out[c] = ""
    return out[keep].copy()


def _load_assets_from_320b2(mineru_benchmark_dir: Optional[Path]) -> pd.DataFrame:
    if not mineru_benchmark_dir:
        return pd.DataFrame()
    xlsx = mineru_benchmark_dir / "mineru_benchmark_320b2.xlsx"
    if not xlsx.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(xlsx, sheet_name="table_assets_all")
    except Exception:
        return pd.DataFrame()


def _collect_assets_from_root(mineru_output_root: Path) -> pd.DataFrame:
    if not mineru_output_root.exists():
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for report_dir in sorted([p for p in mineru_output_root.iterdir() if p.is_dir()]):
        report_name = report_dir.name
        try:
            res = read_mineru_output(report_dir)
        except Exception:
            continue
        for a in res.table_assets:
            ad = a.to_dict()
            extra = ad.get("extra", {}) if isinstance(ad.get("extra"), dict) else {}
            rows.append(
                {
                    "report_name": report_name,
                    "source_file": _norm(ad.get("source_file")),
                    "block_index": ad.get("block_index"),
                    "bbox": _norm(ad.get("bbox")),
                    "table_asset_id": _stable_asset_id(
                        report_name=report_name,
                        source_file=_norm(ad.get("source_file")),
                        block_index=ad.get("block_index"),
                        bbox=ad.get("bbox"),
                    ),
                    "table_role_guess": _norm(ad.get("table_role_guess")),
                    "role_category": _norm(extra.get("role_category") or ad.get("table_role_guess")),
                    "image_path": _norm(ad.get("image_path")),
                    "image_exists": _to_bool(extra.get("image_exists")),
                    "page_idx": ad.get("page_idx"),
                    "caption": _norm(ad.get("caption")),
                    "nearby_text_preview": _norm(ad.get("nearby_text"))[:200],
                }
            )
    return pd.DataFrame(rows)


def _prioritized_round_robin(df: pd.DataFrame, max_items: int) -> pd.DataFrame:
    if df.empty:
        return df
    work = df.copy()
    work["priority_score"] = work["role_category"].apply(_role_priority)
    work["image_penalty"] = work["image_exists"].apply(lambda x: 0 if _to_bool(x) else 1)
    work = work.sort_values(["priority_score", "image_penalty", "report_name", "table_asset_id"]).reset_index(drop=True)

    buckets: Dict[str, List[int]] = {}
    for idx, row in work.iterrows():
        buckets.setdefault(_norm(row.get("report_name")), []).append(idx)

    picked: List[int] = []
    while len(picked) < max_items:
        progressed = False
        for report_name in sorted(buckets.keys()):
            if not buckets[report_name]:
                continue
            picked.append(buckets[report_name].pop(0))
            progressed = True
            if len(picked) >= max_items:
                break
        if not progressed:
            break
    return work.loc[picked].copy().reset_index(drop=True)


def build_recognizer_worklist(
    mineru_output_root: Path,
    mineru_benchmark_dir: Optional[Path],
    recognized_report_table_keys: Set[Tuple[str, str]],
    recognized_report_names: Optional[Set[str]] = None,
    recognized_source_table_ids: Optional[Set[str]] = None,
    max_worklist: int = 30,
) -> Dict[str, Any]:
    raw_assets = _load_assets_from_320b2(mineru_benchmark_dir)
    if raw_assets.empty:
        raw_assets = _collect_assets_from_root(mineru_output_root)

    assets_df = _normalize_assets_df(raw_assets, mineru_output_root=mineru_output_root)
    mineru_report_count = int(assets_df["report_name"].replace("", pd.NA).dropna().nunique()) if not assets_df.empty else 0
    mineru_table_asset_count = int(len(assets_df))

    if assets_df.empty:
        empty_cols = [
            "priority",
            "source_report_name",
            "mineru_report_dir",
            "table_asset_id",
            "table_role_guess",
            "image_path",
            "image_exists",
            "page_idx",
            "bbox",
            "caption",
            "nearby_text_preview",
            "reason_selected",
            "expected_metric_family",
            "recommended_output_dir",
            "already_has_recognizer_output",
        ]
        return {
            "table_assets_df": assets_df,
            "worklist_df": pd.DataFrame(columns=empty_cols),
            "worklist_commands_df": pd.DataFrame(columns=["priority", "source_report_name", "table_asset_id", "image_path", "recommended_output_dir", "command_template", "manual_command_note"]),
            "missing_recognizer_outputs_df": pd.DataFrame(columns=["source_report_name", "table_asset_count", "existing_recognizer_output_count", "missing_core_table_count", "next_action"]),
            "mineru_report_count": 0,
            "mineru_table_asset_count": 0,
            "recognizer_output_coverage_rate": 0.0,
        }

    report_names = set(recognized_report_names or set())
    source_table_ids = set(recognized_source_table_ids or set())
    exact_pairs = set(recognized_report_table_keys or set())

    def _is_already(row: pd.Series) -> bool:
        rn = _norm(row.get("report_name"))
        tid = _norm(row.get("table_asset_id"))
        bbox = _norm(row.get("bbox"))
        if (rn, tid) in exact_pairs:
            return True
        if rn in report_names:
            # report-level recognizer evidence exists, treat as partially covered
            if tid in source_table_ids or bbox in source_table_ids:
                return True
        return False

    assets_df["already_has_recognizer_output"] = assets_df.apply(_is_already, axis=1)
    assets_df["reason_selected"] = assets_df.apply(lambda r: _reason_selected(_norm(r.get("role_category")), _to_bool(r.get("image_exists"))), axis=1)
    assets_df["expected_metric_family"] = assets_df["role_category"].apply(_expected_metric_family)
    assets_df["recommended_output_dir"] = assets_df.apply(
        lambda r: str(
            Path("D:/_datefac/output/row_text_multi_report_benchmark_320f/recognizer_outputs")
            / _norm(r.get("report_name"))
            / _norm(r.get("table_asset_id"))
        ),
        axis=1,
    )

    coverage_rate = float(assets_df["already_has_recognizer_output"].mean()) if len(assets_df) else 0.0

    to_run = assets_df[~assets_df["already_has_recognizer_output"]].copy()
    worklist = _prioritized_round_robin(to_run, max_items=max_worklist)
    if not worklist.empty:
        worklist = worklist.reset_index(drop=True)
        worklist["priority"] = worklist.index + 1
        worklist = worklist.rename(columns={"report_name": "source_report_name"})
        worklist = worklist[
            [
                "priority",
                "source_report_name",
                "mineru_report_dir",
                "table_asset_id",
                "table_role_guess",
                "image_path",
                "image_exists",
                "page_idx",
                "bbox",
                "caption",
                "nearby_text_preview",
                "reason_selected",
                "expected_metric_family",
                "recommended_output_dir",
                "already_has_recognizer_output",
            ]
        ].copy()
    else:
        worklist = pd.DataFrame(columns=[
            "priority",
            "source_report_name",
            "mineru_report_dir",
            "table_asset_id",
            "table_role_guess",
            "image_path",
            "image_exists",
            "page_idx",
            "bbox",
            "caption",
            "nearby_text_preview",
            "reason_selected",
            "expected_metric_family",
            "recommended_output_dir",
            "already_has_recognizer_output",
        ])

    command_rows: List[Dict[str, Any]] = []
    for _, r in worklist.iterrows():
        image_path = _norm(r.get("image_path"))
        rec_out = _norm(r.get("recommended_output_dir"))
        manual_note = "if script lacks args, add argument support in local ppstructure runner"
        if not image_path:
            manual_note = "missing image_path; locate source image manually before recognizer run"
        command_rows.append(
            {
                "priority": r.get("priority"),
                "source_report_name": _norm(r.get("source_report_name")),
                "table_asset_id": _norm(r.get("table_asset_id")),
                "image_path": image_path,
                "recommended_output_dir": rec_out,
                "command_template": (
                    "conda activate ppstructure_legacy; "
                    "$env:USERPROFILE='E:\\paddle_user_legacy'; "
                    "$env:HOME='E:\\paddle_user_legacy'; "
                    f"python E:\\mineru_lab\\test_ppstructure_legacy.py --image \"{image_path}\" --output-dir \"{rec_out}\""
                ),
                "manual_command_note": manual_note,
            }
        )
    commands_df = pd.DataFrame(command_rows)

    # report-level missing outputs
    temp = assets_df.copy()
    temp["is_core_table"] = temp["role_category"].isin(
        ["BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW_STATEMENT", "CORE_METRIC_TABLE", "FINANCIAL_FORECAST_VALUATION"]
    )
    missing_report = temp.groupby("report_name", dropna=False).agg(
        table_asset_count=("table_asset_id", "count"),
        existing_recognizer_output_count=("already_has_recognizer_output", lambda s: int(sum(bool(x) for x in s))),
        missing_core_table_count=("is_core_table", lambda s: int(sum(bool(x) for x in s))),
    ).reset_index().rename(columns={"report_name": "source_report_name"})
    missing_report["next_action"] = missing_report.apply(
        lambda r: "run_top_priority_core_tables" if int(r.get("existing_recognizer_output_count", 0)) == 0 else "expand_recognizer_coverage",
        axis=1,
    )

    # enrich table_assets df for output
    table_assets_out = assets_df.copy()
    table_assets_out["role_counts_json"] = ""
    table_assets_out["already_has_recognizer_output"] = table_assets_out["already_has_recognizer_output"].apply(_to_bool)

    return {
        "table_assets_df": table_assets_out,
        "worklist_df": worklist,
        "worklist_commands_df": commands_df,
        "missing_recognizer_outputs_df": missing_report,
        "mineru_report_count": mineru_report_count,
        "mineru_table_asset_count": mineru_table_asset_count,
        "recognizer_output_coverage_rate": coverage_rate,
    }
