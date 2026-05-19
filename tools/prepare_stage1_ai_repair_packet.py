import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


YEAR_RE = re.compile(r"\b(20\d{2}(?:[AE])?)\b", re.IGNORECASE)
PRODUCTION_PREFIX_PATTERNS = ["01_*.xlsx", "02_*.xlsx", "02A_*.xlsx", "06_*.xlsx"]
PDF_STEM_TO_SAMPLE_ID = {
    "H3_AP202605141822317484_1": "S1",
    "H3_AP202605121822223662_1": "S2",
    "H3_AP202605141822318060_1": "S3",
}


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _safe_sheet_name(name: str, used: set) -> str:
    safe = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = safe
    i = 1
    while safe in used:
        suffix = f"_{i}"
        safe = f"{base[:31-len(suffix)]}{suffix}"
        i += 1
    used.add(safe)
    return safe


def _safe_write_text(path: Path, text: str) -> Path:
    final = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final.parent.mkdir(parents=True, exist_ok=True)
    final.write_text(text, encoding="utf-8")
    return final


def _safe_write_json(path: Path, payload: object) -> Path:
    final = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final.parent.mkdir(parents=True, exist_ok=True)
    final.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return final


def _safe_write_excel(sheets: Dict[str, pd.DataFrame], path: Path) -> Path:
    final = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(final, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)
    return final


def _collect_production_guard_files(delivery_dir: Path) -> List[Path]:
    out: List[Path] = []
    for pattern in PRODUCTION_PREFIX_PATTERNS:
        matched = sorted(delivery_dir.glob(pattern))
        if matched:
            out.append(matched[0])
    return out


def _snapshot_files(files: List[Path]) -> Dict[str, Dict[str, str]]:
    snap: Dict[str, Dict[str, str]] = {}
    for file in files:
        if not file.exists():
            snap[str(file)] = {"exists": "0", "size": "0"}
        else:
            snap[str(file)] = {"exists": "1", "size": str(file.stat().st_size)}
    return snap


def _compare_snapshot(before: Dict[str, Dict[str, str]], after: Dict[str, Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    keys = sorted(set(before.keys()) | set(after.keys()))
    for k in keys:
        b = before.get(k, {"exists": "0", "size": "0"})
        a = after.get(k, {"exists": "0", "size": "0"})
        changed = "1" if b != a else "0"
        rows.append(
            {
                "path": k,
                "before_exists": b.get("exists", "0"),
                "after_exists": a.get("exists", "0"),
                "before_size": b.get("size", "0"),
                "after_size": a.get("size", "0"),
                "changed": changed,
            }
        )
    return rows


def _run_delivery_check_json(delivery_dir: Path) -> Dict[str, str]:
    script = Path(r"D:\_datefac\tools\check_delivery_state.py")
    if not script.exists():
        return {"overall_status": "UNKNOWN", "pass_count": "0", "warn_count": "0", "fail_count": "0", "check_count": "0"}
    cmd = [sys.executable, str(script), "--delivery-dir", str(delivery_dir), "--json"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        data = json.loads(p.stdout) if p.stdout.strip() else {}
        return {
            "overall_status": _norm(data.get("overall_status")),
            "pass_count": _norm(data.get("pass_count")),
            "warn_count": _norm(data.get("warn_count")),
            "fail_count": _norm(data.get("fail_count")),
            "check_count": _norm(data.get("check_count")),
        }
    except Exception:
        return {"overall_status": "UNKNOWN", "pass_count": "0", "warn_count": "0", "fail_count": "0", "check_count": "0"}


def _find_one(prefix: str, folder: Path, exclude_prefix: Optional[str] = None) -> Optional[Path]:
    files = sorted(folder.glob(f"{prefix}*.xlsx"))
    if exclude_prefix:
        files = [p for p in files if not p.name.startswith(exclude_prefix)]
    return files[0] if files else None


def _parse_flags(flag_text: str) -> List[str]:
    return [x.strip() for x in _norm(flag_text).split("|") if x.strip()]


def _detected_years_from_row(row: Dict[str, object]) -> List[str]:
    years = set()
    y = _norm(row.get("year"))
    if y:
        years.add(y)
    for field in ["row_preview", "table_header_context", "source_label"]:
        txt = _norm(row.get(field))
        for m in YEAR_RE.finditer(txt):
            years.add(m.group(1).upper())
    return sorted(years)


def _df_row_to_cells(df: pd.DataFrame, row_idx_1_based: int) -> List[str]:
    if row_idx_1_based <= 0 or row_idx_1_based > len(df):
        return []
    vals = [_norm(x) for x in df.iloc[row_idx_1_based - 1].tolist()]
    return [x for x in vals if x]


def _nearby_rows(df: pd.DataFrame, row_idx_1_based: int, span: int = 2) -> List[List[str]]:
    rows: List[List[str]] = []
    if row_idx_1_based <= 0:
        return rows
    start = max(1, row_idx_1_based - span)
    end = min(len(df), row_idx_1_based + span)
    for r in range(start, end + 1):
        rows.append(_df_row_to_cells(df, r))
    return rows


def _table_preview(df: pd.DataFrame, max_rows: int = 8) -> List[List[str]]:
    rows: List[List[str]] = []
    n = min(len(df), max_rows)
    for i in range(n):
        vals = [_norm(x) for x in df.iloc[i].tolist()]
        rows.append([x for x in vals if x])
    return rows


def _build_source_trace_id(sample_id: str, page: int, table_idx: int, row_idx: int) -> str:
    return f"{sample_id}|p{page:03d}|t{table_idx:03d}|r{max(0, row_idx):03d}"


def _task_type_for_row(row: Dict[str, object]) -> Optional[str]:
    flags = set(_parse_flags(_norm(row.get("flags"))))
    if "multi_metric_row_ambiguous" in flags:
        return "row_segment_repair"
    if any(f in flags for f in {"ambiguous_year_value_alignment", "partial_year_value_alignment", "no_numeric_value_after_metric_match"}):
        return "metric_year_value_alignment"
    if any(f in flags for f in {"source_row_semantic_risk", "forbidden_source_label_for_metric", "broad_keyword_unsafe"}):
        return "semantic_guard_review"
    return None


def _priority_for_row(row: Dict[str, object], task_type: str) -> int:
    score_map = {"row_segment_repair": 100, "metric_year_value_alignment": 90, "semantic_guard_review": 75}
    score = score_map.get(task_type, 50)
    role = _norm(row.get("table_role"))
    if role == "core_metrics":
        score += 25
    elif role == "full_financial_forecast":
        score += 18
    elif role == "business_forecast":
        score += 8
    if _norm(row.get("sample_id")) == "S1" and int(row.get("source_page") or 0) == 4:
        score -= 10
    flags = _parse_flags(_norm(row.get("flags")))
    score -= len(flags)
    return score


def _build_schema_json() -> Dict[str, object]:
    return {
        "type": "object",
        "required": ["repair_task_id", "decision", "repairs", "manual_review_items", "notes"],
        "properties": {
            "repair_task_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["extract", "manual_review", "ignore", "non_target"]},
            "repairs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["standard_metric", "year", "value", "unit", "confidence", "evidence", "source_cell_or_segment", "flags"],
                    "properties": {
                        "standard_metric": {"type": "string"},
                        "year": {"type": "string"},
                        "value": {"type": ["number", "string", "null"]},
                        "unit": {"type": ["string", "null"]},
                        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                        "evidence": {"type": "string"},
                        "source_cell_or_segment": {"type": "string"},
                        "flags": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "manual_review_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["reason", "evidence"],
                    "properties": {
                        "reason": {"type": "string"},
                        "evidence": {"type": "string"},
                    },
                },
            },
            "notes": {"type": "string"},
        },
        "additionalProperties": False,
    }


def _contains_garbled(text: str) -> bool:
    return "????" in text or "�" in text


def _read_sample_assets(assets_root: Path, std_root: Path) -> Tuple[List[Dict[str, object]], List[str], Dict[str, Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    all_manual: List[Dict[str, object]] = []
    input_files: List[str] = []
    sample_meta: Dict[str, Dict[str, object]] = {}
    raw_table_index_rows: List[Dict[str, object]] = []
    s2_diagnosis: List[Dict[str, object]] = []

    for sdir in sorted([p for p in std_root.iterdir() if p.is_dir()]):
        sid = sdir.name
        pstd = sdir / "05_stage1_standardized_core_metric_trial.xlsx"
        pdiag = sdir / "05_stage1_standardizer_diagnostics.xlsx"
        if pstd.exists():
            input_files.append(str(pstd))
        if pdiag.exists():
            input_files.append(str(pdiag))
        manual_df = pd.DataFrame()
        if pdiag.exists():
            try:
                manual_df = pd.read_excel(pdiag, sheet_name="manual_review_candidates", engine="openpyxl").fillna("")
            except Exception:
                manual_df = pd.DataFrame()
        if not manual_df.empty:
            for _, row in manual_df.iterrows():
                record = {k: row.get(k, "") for k in manual_df.columns}
                record["sample_id"] = _norm(record.get("sample_id")) or sid
                all_manual.append(record)

    for adir in sorted([p for p in assets_root.iterdir() if p.is_dir()]):
        p02a = _find_one("02A_", adir)
        p02 = _find_one("02_", adir, exclude_prefix="02A_")
        p05 = adir / "05_stage1_core_metric_candidates.xlsx"
        ps = adir / "stage1_sandbox_asset_summary.xlsx"
        if p02a:
            input_files.append(str(p02a))
        if p02:
            input_files.append(str(p02))
        if p05.exists():
            input_files.append(str(p05))
        if ps.exists():
            input_files.append(str(ps))

        company = ""
        pdf_file = ""
        if ps.exists():
            try:
                sdf = pd.read_excel(ps, engine="openpyxl").fillna("")
                if not sdf.empty:
                    company = _norm(sdf.iloc[0].get("company"))
                    pdf_file = _norm(sdf.iloc[0].get("pdf_file"))
            except Exception:
                pass

        sid = ""
        for r in all_manual:
            if _norm(r.get("asset_package")) == adir.name:
                sid = _norm(r.get("sample_id"))
                break
        if not sid:
            stem = Path(pdf_file).stem if pdf_file else ""
            sid = PDF_STEM_TO_SAMPLE_ID.get(stem, "")
        if not sid:
            sid = "S_UNKNOWN"

        sample_meta[sid] = {
            "sample_id": sid,
            "company": company,
            "pdf_stem": Path(pdf_file).stem if pdf_file else "",
            "asset_package": adir.name,
            "asset_dir": adir,
            "file_02a": p02a,
            "file_02": p02,
            "file_05": p05 if p05.exists() else None,
        }

        if p02a and sid == "S2":
            try:
                raw_index = pd.read_excel(p02a, sheet_name="raw_tables_index", engine="openpyxl").fillna("")
            except Exception:
                raw_index = pd.DataFrame()
            if not raw_index.empty:
                for _, rr in raw_index.iterrows():
                    raw_table_index_rows.append(
                        {
                            "sample_id": sid,
                            "asset_package": adir.name,
                            "company": company,
                            "page": int(rr.get("page") or 0),
                            "table_index": int(rr.get("table_index") or 0),
                            "detected_year_cells": _norm(rr.get("detected_year_cells")),
                            "metric_keyword_hits": _norm(rr.get("metric_keyword_hits")),
                            "candidate_type": _norm(rr.get("candidate_type")),
                            "confidence": _norm(rr.get("confidence")),
                        }
                    )
                s2_diagnosis.append(
                    {
                        "sample_id": sid,
                        "company": company,
                        "asset_package": adir.name,
                        "raw_table_count": len(raw_index),
                        "year_evidence_count": int((raw_index["detected_year_cells"].astype(str).str.strip() != "").sum()) if "detected_year_cells" in raw_index.columns else 0,
                        "label_examples": "",
                        "keyword_hit_examples": "none",
                        "label_fragmented_suspected": 1,
                        "negative_values_without_labels": 0,
                        "recommendation": "Tune extraction heuristics / AI repair / manual visual review",
                    }
                )

    return all_manual, sorted(set(input_files)), sample_meta, raw_table_index_rows, s2_diagnosis


def _load_sheet_cache(file_02: Optional[Path]) -> Dict[str, pd.DataFrame]:
    cache: Dict[str, pd.DataFrame] = {}
    if not file_02 or not file_02.exists():
        return cache
    try:
        xls = pd.ExcelFile(file_02, engine="openpyxl")
    except Exception:
        return cache
    for sh in xls.sheet_names:
        try:
            cache[sh] = pd.read_excel(file_02, sheet_name=sh, engine="openpyxl").fillna("").astype(str)
        except Exception:
            continue
    return cache


def _sheet_name_for_source(page: int, table_idx: int) -> str:
    return f"p{page:03d}_t{table_idx:03d}"


def _build_repair_tasks(
    manual_rows: List[Dict[str, object]],
    sample_meta: Dict[str, Dict[str, object]],
    raw_table_index_rows: List[Dict[str, object]],
    s2_diagnosis: List[Dict[str, object]],
    max_tasks: int,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], Dict[str, int], Dict[str, int], int]:
    rows_with_priority: List[Tuple[int, Dict[str, object], str]] = []
    sheet_cache_by_sample: Dict[str, Dict[str, pd.DataFrame]] = {}

    for row in manual_rows:
        task_type = _task_type_for_row(row)
        if not task_type:
            continue
        sid = _norm(row.get("sample_id"))
        if sid not in sheet_cache_by_sample:
            meta = sample_meta.get(sid, {})
            sheet_cache_by_sample[sid] = _load_sheet_cache(meta.get("file_02")) if meta else {}
        score = _priority_for_row(row, task_type)
        rows_with_priority.append((score, row, task_type))

    rows_with_priority.sort(key=lambda x: (-x[0], _norm(x[1].get("sample_id")), int(x[1].get("source_page") or 0), int(x[1].get("source_row_index") or 0)))

    tasks: List[Dict[str, object]] = []
    trace_index_rows: List[Dict[str, object]] = []
    task_type_counts: Dict[str, int] = {}
    sample_task_counts: Dict[str, int] = {}
    seq = 1

    reserve_for_s2 = min(8, max(1, max_tasks // 10))
    non_s2_limit = max_tasks - reserve_for_s2
    for score, row, task_type in rows_with_priority:
        sid = _norm(row.get("sample_id"))
        if sid == "S2":
            continue
        if len(tasks) >= non_s2_limit:
            break
        meta = sample_meta.get(sid, {})
        page = int(row.get("source_page") or 0)
        table_idx = int(row.get("source_table_index") or 0)
        row_idx = int(row.get("source_row_index") or 0)
        trace_id = _build_source_trace_id(sid, page, table_idx, row_idx)

        sheet_name = _sheet_name_for_source(page, table_idx)
        df = sheet_cache_by_sample.get(sid, {}).get(sheet_name, pd.DataFrame())
        row_cells = _df_row_to_cells(df, row_idx) if not df.empty else []
        nearby = _nearby_rows(df, row_idx) if not df.empty else []
        header_ctx = _table_preview(df, max_rows=3) if not df.empty else []
        raw_preview = _table_preview(df, max_rows=8) if not df.empty else []

        task_id = f"RPR-{sid}-{seq:04d}"
        seq += 1
        task = {
            "repair_task_id": task_id,
            "task_type": task_type,
            "sample_id": sid,
            "company": _norm(row.get("company")) or _norm(meta.get("company")),
            "asset_package": _norm(row.get("asset_package")) or _norm(meta.get("asset_package")),
            "source": {
                "source_page": page,
                "source_table_index": table_idx,
                "source_row_index": row_idx,
                "table_role": _norm(row.get("table_role")) or "unknown",
                "source_trace_id": trace_id,
            },
            "evidence": {
                "detected_years": _detected_years_from_row(row),
                "row_cells": row_cells,
                "row_preview": _norm(row.get("row_preview")),
                "nearby_rows_context": nearby,
                "table_header_context": header_ctx,
                "raw_table_preview": raw_preview,
            },
            "current_rule_result": {
                "standard_metric_hint": _norm(row.get("standard_metric")),
                "route_recommendation": _norm(row.get("route_recommendation")) or "manual_review_candidate",
                "confidence": _norm(row.get("confidence")) or "low",
                "flags": _parse_flags(_norm(row.get("flags"))),
                "semantic_score": _norm(row.get("semantic_score")),
                "promotion_reason": _norm(row.get("promotion_reason")),
            },
            "ai_instruction": {
                "task_goal": f"Repair task for {task_type} based strictly on provided evidence.",
                "allowed_actions": ["extract", "manual_review", "ignore", "non_target"],
                "forbidden_actions": ["invent_values", "guess_missing_year", "cross_metric_assignment_without_evidence"],
                "must_not_invent_values": True,
                "require_evidence": True,
                "require_json_only": True,
            },
            "output_schema_name": "stage1_ai_repair_v1",
            "standard_metric_hint": _norm(row.get("standard_metric")),
            "detected_years": "|".join(_detected_years_from_row(row)),
            "row_preview": _norm(row.get("row_preview")),
            "risk_flags": _norm(row.get("flags")),
            "current_route": _norm(row.get("route_recommendation")) or "manual_review_candidate",
            "reason_for_ai_repair": _norm(row.get("promotion_reason")) or task_type,
            "expected_output_schema_name": "stage1_ai_repair_v1",
            "must_not_invent_values": True,
            "source_trace_id": trace_id,
            "priority_score": score,
        }
        tasks.append(task)
        trace_index_rows.append(
            {
                "repair_task_id": task_id,
                "source_trace_id": trace_id,
                "sample_id": sid,
                "company": task["company"],
                "asset_package": task["asset_package"],
                "source_page": page,
                "source_table_index": table_idx,
                "source_row_index": row_idx,
                "table_role": task["source"]["table_role"],
            }
        )
        task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1
        sample_task_counts[sid] = sample_task_counts.get(sid, 0) + 1

    s2_rows_added = 0
    for rr in raw_table_index_rows:
        if len(tasks) >= max_tasks:
            break
        if s2_rows_added >= reserve_for_s2:
            break
        sid = "S2"
        trace_id = _build_source_trace_id(sid, int(rr.get("page") or 0), int(rr.get("table_index") or 0), 0)
        task_id = f"RPR-{sid}-{seq:04d}"
        seq += 1
        row_preview = f"candidate_type={_norm(rr.get('candidate_type'))}; confidence={_norm(rr.get('confidence'))}; year_cells={_norm(rr.get('detected_year_cells'))}; keyword_hits={_norm(rr.get('metric_keyword_hits'))}"
        task = {
            "repair_task_id": task_id,
            "task_type": "s2_table_level_repair",
            "sample_id": sid,
            "company": _norm(rr.get("company")),
            "asset_package": _norm(rr.get("asset_package")),
            "source": {
                "source_page": int(rr.get("page") or 0),
                "source_table_index": int(rr.get("table_index") or 0),
                "source_row_index": 0,
                "table_role": "unknown",
                "source_trace_id": trace_id,
            },
            "evidence": {
                "detected_years": [x for x in _norm(rr.get("detected_year_cells")).split("|") if x],
                "row_cells": [],
                "row_preview": row_preview,
                "nearby_rows_context": [],
                "table_header_context": [],
                "raw_table_preview": [row_preview],
            },
            "current_rule_result": {
                "standard_metric_hint": "",
                "route_recommendation": "manual_review_candidate",
                "confidence": "low",
                "flags": ["standardizer_no_metric_candidates"],
                "semantic_score": "",
                "promotion_reason": "s2_no_metric_table_level_diagnosis",
            },
            "ai_instruction": {
                "task_goal": "Identify whether any target financial metrics exist in this table segment without inventing values.",
                "allowed_actions": ["manual_review", "non_target", "extract"],
                "forbidden_actions": ["invent_values", "guess_labels", "fake_metric_alignment"],
                "must_not_invent_values": True,
                "require_evidence": True,
                "require_json_only": True,
            },
            "output_schema_name": "stage1_ai_repair_v1",
            "standard_metric_hint": "",
            "detected_years": _norm(rr.get("detected_year_cells")),
            "row_preview": row_preview,
            "risk_flags": "standardizer_no_metric_candidates",
            "current_route": "manual_review_candidate",
            "reason_for_ai_repair": "S2 has year evidence but missing recoverable metric labels",
            "expected_output_schema_name": "stage1_ai_repair_v1",
            "must_not_invent_values": True,
            "source_trace_id": trace_id,
            "priority_score": 110,
        }
        tasks.append(task)
        trace_index_rows.append(
            {
                "repair_task_id": task_id,
                "source_trace_id": trace_id,
                "sample_id": sid,
                "company": task["company"],
                "asset_package": task["asset_package"],
                "source_page": task["source"]["source_page"],
                "source_table_index": task["source"]["source_table_index"],
                "source_row_index": 0,
                "table_role": "unknown",
            }
        )
        task_type_counts["s2_table_level_repair"] = task_type_counts.get("s2_table_level_repair", 0) + 1
        sample_task_counts[sid] = sample_task_counts.get(sid, 0) + 1
        s2_rows_added += 1

    return tasks, trace_index_rows, task_type_counts, sample_task_counts, s2_rows_added


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare sandbox-only Stage 1 AI repair packet.")
    parser.add_argument("--trial-run-root", type=str, required=True)
    parser.add_argument("--delivery-dir", type=str, required=True)
    parser.add_argument("--max-tasks", type=int, default=80)
    args = parser.parse_args()

    trial_run_root = Path(args.trial_run_root)
    delivery_dir = Path(args.delivery_dir)
    assets_root = trial_run_root / "assets"
    std_root = trial_run_root / "standardizer_trial"
    if not assets_root.exists() or not std_root.exists():
        print("BLOCKED_TRIAL_INPUT_MISSING")
        return 3

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    before = _snapshot_files(_collect_production_guard_files(delivery_dir))

    manual_rows, input_files, sample_meta, raw_table_index_rows, s2_diagnosis = _read_sample_assets(assets_root, std_root)
    tasks, trace_index_rows, task_type_counts, sample_task_counts, s2_table_level_count = _build_repair_tasks(
        manual_rows=manual_rows,
        sample_meta=sample_meta,
        raw_table_index_rows=raw_table_index_rows,
        s2_diagnosis=s2_diagnosis,
        max_tasks=max(1, int(args.max_tasks)),
    )

    task_ids = [_norm(t.get("repair_task_id")) for t in tasks]
    duplicate_task_ids = sorted({x for x in task_ids if task_ids.count(x) > 1})
    parse_errors = 0
    missing_fields_rows: List[Dict[str, object]] = []
    garbled_count = 0
    required_fields = ["repair_task_id", "task_type", "sample_id", "company", "asset_package", "source", "evidence", "current_rule_result", "ai_instruction", "output_schema_name"]
    for t in tasks:
        if any(not _norm(t.get(k)) for k in ["repair_task_id", "task_type", "sample_id", "company", "asset_package"]):
            missing_fields_rows.append({"repair_task_id": _norm(t.get("repair_task_id")), "missing": "basic_fields"})
        src = t.get("source", {})
        ev = t.get("evidence", {})
        aii = t.get("ai_instruction", {})
        if not isinstance(src, dict) or not isinstance(ev, dict) or not isinstance(aii, dict):
            missing_fields_rows.append({"repair_task_id": _norm(t.get("repair_task_id")), "missing": "nested_objects"})
        txt = json.dumps(t, ensure_ascii=False)
        if _contains_garbled(txt):
            garbled_count += 1

    output_37_jsonl = delivery_dir / "37_stage1_ai_repair_input_packet.jsonl"
    output_37_md = delivery_dir / "37_stage1_ai_repair_input_packet.md"
    output_37_xlsx = delivery_dir / "37_stage1_ai_repair_input_packet.xlsx"
    output_38_md = delivery_dir / "38_stage1_ai_repair_schema_and_prompt.md"
    output_38_xlsx = delivery_dir / "38_stage1_ai_repair_schema_and_prompt.xlsx"
    output_38_json = delivery_dir / "38_stage1_ai_repair_schema.json"
    output_38_validation = delivery_dir / "38_stage1_ai_repair_packet_validation.xlsx"
    output_39_md = delivery_dir / "39_stage1_ai_repair_packet_build_log.md"
    output_39_xlsx = delivery_dir / "39_stage1_ai_repair_packet_build_log.xlsx"

    jsonl_lines: List[str] = []
    for t in tasks:
        obj = {k: t[k] for k in ["repair_task_id", "task_type", "sample_id", "company", "asset_package", "source", "evidence", "current_rule_result", "ai_instruction", "output_schema_name"]}
        line = json.dumps(obj, ensure_ascii=False)
        jsonl_lines.append(line)
        try:
            json.loads(line)
        except Exception:
            parse_errors += 1
    output_37_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_37_jsonl.write_text("\n".join(jsonl_lines), encoding="utf-8")

    schema_payload = _build_schema_json()
    p38json = _safe_write_json(output_38_json, schema_payload)

    task_rows = []
    for t in tasks:
        task_rows.append(
            {
                "repair_task_id": _norm(t.get("repair_task_id")),
                "task_type": _norm(t.get("task_type")),
                "sample_id": _norm(t.get("sample_id")),
                "company": _norm(t.get("company")),
                "asset_package": _norm(t.get("asset_package")),
                "source_page": int(t.get("source", {}).get("source_page") or 0),
                "source_table_index": int(t.get("source", {}).get("source_table_index") or 0),
                "source_row_index": int(t.get("source", {}).get("source_row_index") or 0),
                "table_role": _norm(t.get("source", {}).get("table_role")),
                "standard_metric_hint": _norm(t.get("standard_metric_hint")),
                "detected_years": _norm(t.get("detected_years")),
                "row_preview": _norm(t.get("row_preview")),
                "risk_flags": _norm(t.get("risk_flags")),
                "current_route": _norm(t.get("current_route")),
                "reason_for_ai_repair": _norm(t.get("reason_for_ai_repair")),
                "expected_output_schema_name": _norm(t.get("expected_output_schema_name")),
                "must_not_invent_values": True,
                "source_trace_id": _norm(t.get("source_trace_id")),
                "priority_score": int(t.get("priority_score") or 0),
            }
        )

    task_type_rows = [{"task_type": k, "count": v} for k, v in sorted(task_type_counts.items(), key=lambda x: (-x[1], x[0]))]
    sample_rows = [{"sample_id": k, "task_count": v} for k, v in sorted(sample_task_counts.items(), key=lambda x: x[0])]
    high_priority_rows = [r for r in task_rows if int(r.get("priority_score") or 0) >= 100]
    s2_rows = [r for r in task_rows if _norm(r.get("sample_id")) == "S2"]

    p37xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": "Prepare Stage 1 sandbox AI repair packet"},
                    {"field": "repair_task_count", "value": len(tasks)},
                    {"field": "max_tasks", "value": args.max_tasks},
                    {"field": "jsonl_lines", "value": len(jsonl_lines)},
                    {"field": "duplicate_task_ids", "value": len(duplicate_task_ids)},
                    {"field": "json_parse_errors", "value": parse_errors},
                    {"field": "garbled_text_count", "value": garbled_count},
                ]
            ),
            "repair_tasks": pd.DataFrame(task_rows),
            "task_type_summary": pd.DataFrame(task_type_rows),
            "sample_summary": pd.DataFrame(sample_rows),
            "high_priority_tasks": pd.DataFrame(high_priority_rows),
            "s2_table_level_tasks": pd.DataFrame(s2_rows),
            "source_trace_index": pd.DataFrame(trace_index_rows),
        },
        output_37_xlsx,
    )

    p37md = _safe_write_text(
        output_37_md,
        "\n".join(
            [
                "# Stage1 AI Repair Input Packet",
                "",
                "- task_title: Prepare Stage 1 sandbox AI repair packet",
                f"- task_count: {len(tasks)}",
                f"- max_tasks: {args.max_tasks}",
                f"- task_type_counts: {json.dumps(task_type_counts, ensure_ascii=False)}",
                f"- sample_task_counts: {json.dumps(sample_task_counts, ensure_ascii=False)}",
                f"- s2_table_level_task_count: {s2_table_level_count}",
                f"- jsonl_path: {output_37_jsonl}",
            ]
        ),
    )

    p38md = _safe_write_text(
        output_38_md,
        "\n".join(
            [
                "# Stage1 AI Repair Schema and Prompt",
                "",
                "## System Prompt",
                "You are a strict financial table repair worker. Use evidence only. Return JSON only.",
                "",
                "## User Prompt Template",
                "Given one repair task object, decide extract/manual_review/ignore/non_target and produce schema-compliant JSON.",
                "",
                "## JSON Output Schema",
                "See `38_stage1_ai_repair_schema.json`.",
                "",
                "## Good Examples",
                "- Safe segmented row extraction with explicit year-value mapping.",
                "- Ambiguous multi-metric row routed to manual_review.",
                "- S2 table-level no-label case routed to manual_review.",
                "",
                "## Bad Examples",
                "- Inventing missing year/value.",
                "- Assigning later metric-block values to earlier metric.",
                "- Treating accounts receivable row as revenue.",
                "",
                "## Mandatory Constraints",
                "- Must not invent values.",
                "- Must copy numeric values from evidence only.",
                "- Must preserve year labels exactly unless `year_normalized` flag is provided.",
                "- If ambiguous, choose `manual_review`.",
            ]
        ),
    )

    p38xlsx = _safe_write_excel(
        {
            "schema_summary": pd.DataFrame(
                [
                    {"field": "schema_name", "value": "stage1_ai_repair_v1"},
                    {"field": "decision_values", "value": "extract|manual_review|ignore|non_target"},
                    {"field": "must_not_invent_values", "value": "true"},
                    {"field": "require_json_only", "value": "true"},
                ]
            ),
            "allowed_decisions": pd.DataFrame([{"decision": x} for x in ["extract", "manual_review", "ignore", "non_target"]]),
            "required_fields": pd.DataFrame([{"field": x} for x in required_fields]),
            "prompt_sections": pd.DataFrame([{"section": x} for x in ["system_prompt", "user_template", "good_examples", "bad_examples", "constraints"]]),
            "validation_rules": pd.DataFrame(
                [
                    {"rule": "no_invented_values"},
                    {"rule": "copy_numeric_from_evidence"},
                    {"rule": "json_only_response"},
                    {"rule": "manual_review_if_ambiguous"},
                ]
            ),
        },
        output_38_xlsx,
    )

    p38val = _safe_write_excel(
        {
            "jsonl_validation": pd.DataFrame(
                [
                    {"field": "line_count", "value": len(jsonl_lines)},
                    {"field": "parse_errors", "value": parse_errors},
                    {"field": "duplicate_task_ids", "value": len(duplicate_task_ids)},
                    {"field": "missing_field_rows", "value": len(missing_fields_rows)},
                    {"field": "garbled_text_count", "value": garbled_count},
                ]
            ),
            "missing_fields": pd.DataFrame(missing_fields_rows),
            "duplicate_task_ids": pd.DataFrame([{"repair_task_id": x} for x in duplicate_task_ids]),
            "sample_task_counts": pd.DataFrame(sample_rows),
        },
        output_38_validation,
    )

    after = _snapshot_files(_collect_production_guard_files(delivery_dir))
    guard_rows = _compare_snapshot(before, after)
    changed_count = sum(1 for r in guard_rows if r.get("changed") == "1")
    delivery_status = _run_delivery_check_json(delivery_dir)
    finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    jsonl_validation_status = "PASS"
    if parse_errors > 0 or duplicate_task_ids or missing_fields_rows or garbled_count > 0 or len(tasks) == 0:
        jsonl_validation_status = "WARN"
    if s2_table_level_count <= 0:
        jsonl_validation_status = "WARN"

    safety_checks = [
        {"check_name": "factory_core_not_run", "status": "PASS", "detail": "helper reads existing trial assets only"},
        {"check_name": "vision_or_ocr_not_triggered", "status": "PASS", "detail": "no OCR/vision/model paths"},
        {"check_name": "no_ai_model_called", "status": "PASS", "detail": "packet preparation only, no inference"},
        {"check_name": "production_files_unchanged", "status": "PASS" if changed_count == 0 else "FAIL", "detail": f"changed={changed_count}"},
    ]

    p39md = _safe_write_text(
        output_39_md,
        "\n".join(
            [
                "# Stage1 AI Repair Packet Build Log",
                "",
                "- task_title: Prepare Stage 1 sandbox AI repair packet",
                f"- started_at: {started_at}",
                f"- finished_at: {finished_at}",
                f"- commands_run: {sys.executable} {Path(__file__).name} --trial-run-root {trial_run_root} --delivery-dir {delivery_dir} --max-tasks {args.max_tasks}",
                f"- task_count: {len(tasks)}",
                f"- task_type_counts: {json.dumps(task_type_counts, ensure_ascii=False)}",
                f"- sample_task_counts: {json.dumps(sample_task_counts, ensure_ascii=False)}",
                f"- s2_table_level_task_count: {s2_table_level_count}",
                f"- jsonl_validation_status: {jsonl_validation_status}",
                f"- production_guard_changed_count: {changed_count}",
                f"- next_step_recommendation: Use packet as strict input for a no-invention AI repair MVP worker.",
            ]
        ),
    )

    p39xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": "Prepare Stage 1 sandbox AI repair packet"},
                    {"field": "started_at", "value": started_at},
                    {"field": "finished_at", "value": finished_at},
                    {"field": "task_count", "value": len(tasks)},
                    {"field": "jsonl_validation_status", "value": jsonl_validation_status},
                    {"field": "production_guard_changed_count", "value": changed_count},
                ]
            ),
            "commands_run": pd.DataFrame(
                [
                    {"command": f"{sys.executable} -m py_compile {Path(__file__)}"},
                    {"command": f"{sys.executable} {Path(__file__)} --trial-run-root {trial_run_root} --delivery-dir {delivery_dir} --max-tasks {args.max_tasks}"},
                    {"command": f"{sys.executable} D:\\_datefac\\tools\\check_delivery_state.py --json"},
                ]
            ),
            "input_files_read": pd.DataFrame([{"path": p} for p in input_files]),
            "output_files_generated": pd.DataFrame(
                [
                    {"path": str(output_37_md)},
                    {"path": str(output_37_xlsx)},
                    {"path": str(output_37_jsonl)},
                    {"path": str(output_38_md)},
                    {"path": str(output_38_xlsx)},
                    {"path": str(output_38_json)},
                    {"path": str(output_38_validation)},
                    {"path": str(output_39_md)},
                    {"path": str(output_39_xlsx)},
                ]
            ),
            "task_type_counts": pd.DataFrame(task_type_rows),
            "sample_task_counts": pd.DataFrame(sample_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "production_guard": pd.DataFrame(guard_rows),
        },
        output_39_xlsx,
    )

    print(f"helper_path: {Path(__file__)}")
    print("packet_build_status: PASS" if len(tasks) > 0 else "packet_build_status: WARN_NO_TASKS")
    print(f"generated_outputs: {json.dumps([str(p37md), str(p37xlsx), str(output_37_jsonl), str(p38md), str(p38xlsx), str(p38json), str(p38val), str(p39md), str(p39xlsx)], ensure_ascii=False)}")
    print(f"repair_task_count: {len(tasks)}")
    print(f"task_type_counts: {json.dumps(task_type_counts, ensure_ascii=False)}")
    print(f"sample_task_counts: {json.dumps(sample_task_counts, ensure_ascii=False)}")
    print(f"s2_table_level_task_count: {s2_table_level_count}")
    print(f"jsonl_validation_status: {jsonl_validation_status}")
    print(f"production_delivery_status_after: {json.dumps(delivery_status, ensure_ascii=False)}")
    print(f"production_guard_changed_count: {changed_count}")
    return 0 if changed_count == 0 else 5


if __name__ == "__main__":
    raise SystemExit(main())
