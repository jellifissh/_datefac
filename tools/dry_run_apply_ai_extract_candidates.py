import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd


PRODUCTION_PREFIX_PATTERNS = ["01_*.xlsx", "02_*.xlsx", "02A_*.xlsx", "06_*.xlsx"]
YEAR_RE = re.compile(r"^20\d{2}(A|E)?$", re.IGNORECASE)


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_float(v: Any) -> Optional[float]:
    s = _norm(v).replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _safe_sheet_name(name: str, used: Set[str]) -> str:
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
    used: Set[str] = set()
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
        rows.append(
            {
                "path": k,
                "before_exists": b.get("exists", "0"),
                "after_exists": a.get("exists", "0"),
                "before_size": b.get("size", "0"),
                "after_size": a.get("size", "0"),
                "changed": "1" if b != a else "0",
            }
        )
    return rows


def _run_delivery_check_json(delivery_dir: Path) -> Dict[str, Any]:
    script = Path(r"D:\_datefac\tools\check_delivery_state.py")
    p = subprocess.run([sys.executable, str(script), "--delivery-dir", str(delivery_dir), "--json"], capture_output=True, text=True, check=False)
    try:
        return json.loads((p.stdout or "").strip() or "{}")
    except Exception:
        return {"overall_status": "UNKNOWN", "pass_count": 0, "warn_count": 0, "fail_count": 0, "check_count": 0}


def _load_06(path: Path) -> pd.DataFrame:
    return pd.read_excel(path)


def _is_valid_year(year: str) -> bool:
    return bool(YEAR_RE.match(_norm(year)))


def _key(asset: str, metric: str, year: str) -> str:
    return "|".join([_norm(asset), _norm(metric), _norm(year)])


def _value_unit_equal(cand_value: str, cand_unit: str, row_value: str, row_unit: str) -> bool:
    cv = _to_float(cand_value)
    rv = _to_float(row_value)
    if cv is not None and rv is not None:
        value_equal = abs(cv - rv) <= 1e-6
    else:
        value_equal = _norm(cand_value) == _norm(row_value)
    cu = _norm(cand_unit)
    ru = _norm(row_unit)
    unit_equal = cu == ru or cu == "" or ru == ""
    return value_equal and unit_equal


def _build_new_06_row(columns: List[str], c: Dict[str, Any]) -> Dict[str, Any]:
    row = {col: "" for col in columns}
    row.update(
        {
            "source_pdf": "",
            "asset_package": _norm(c.get("resolved_asset_package")),
            "report_type": "stage1_sandbox_dry_run",
            "data_usability_tier": "sandbox_only",
            "standard_metric": _norm(c.get("standardized_metric")),
            "year": _norm(c.get("year")),
            "final_value": _norm(c.get("value")),
            "final_unit": _norm(c.get("unit")),
            "final_value_source": "ai_extract_safe_dry_run",
            "final_review_status": "dry_run_applied",
            "original_auto_value": "",
            "original_auto_unit": "",
            "corrected_value": "",
            "corrected_unit": "",
            "value_validation_status": "dry_run_only",
            "value_repair_applied": "",
            "source_row_label": _norm(c.get("original_metric")),
            "source_table_index": "",
            "source_row_index": "",
            "source_column": _norm(c.get("source_cell_or_segment")),
            "evidence_crop_path": "",
            "trace_note": f"dry_run_from_{_norm(c.get('source_trace_id'))}",
            "reviewer": "codex_dry_run",
            "reviewed_at": datetime.now().strftime("%Y-%m-%d"),
            "reviewer_note": _norm(c.get("evidence"))[:500],
        }
    )
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run apply safe AI extract candidates into sandbox 06 copy.")
    parser.add_argument("--safe-apply-xlsx", required=True)
    parser.add_argument("--final-06-xlsx", required=True)
    parser.add_argument("--delivery-dir", required=True)
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    task_title = "Dry-run apply safe AI extract candidates to sandbox copy"
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    helper_path = Path(__file__)
    safe_apply_xlsx = Path(args.safe_apply_xlsx)
    final_06_xlsx = Path(args.final_06_xlsx)
    delivery_dir = Path(args.delivery_dir)
    output_dir = Path(args.output_dir) if _norm(args.output_dir) else safe_apply_xlsx.parent

    if not safe_apply_xlsx.exists() or not final_06_xlsx.exists():
        print("BLOCKED_REQUIRED_INPUT_MISSING")
        return 3

    before = _snapshot_files(_collect_production_guard_files(delivery_dir))

    safe_df = pd.read_excel(safe_apply_xlsx, sheet_name="safe_apply")
    base_06_df = _load_06(final_06_xlsx)
    sandbox_06_df = base_06_df.copy()
    base_cols = list(base_06_df.columns)

    input_safe_apply_count = len(safe_df)
    applied_rows: List[Dict[str, Any]] = []
    skipped_rows: List[Dict[str, Any]] = []
    diff_rows: List[Dict[str, Any]] = []

    seen_input_keys: Set[str] = set()
    existing_key_to_rows: Dict[str, List[Dict[str, str]]] = {}
    for _, r in sandbox_06_df.iterrows():
        k = _key(r.get("asset_package"), r.get("standard_metric"), r.get("year"))
        existing_key_to_rows.setdefault(k, []).append(
            {"final_value": _norm(r.get("final_value")), "final_unit": _norm(r.get("final_unit"))}
        )

    for _, row in safe_df.iterrows():
        c = {k: row.get(k) for k in safe_df.columns}
        asset = _norm(c.get("resolved_asset_package"))
        metric = _norm(c.get("standardized_metric"))
        year = _norm(c.get("year"))
        value = _norm(c.get("value"))
        unit = _norm(c.get("unit"))
        ckey = _key(asset, metric, year)
        skip_reason = ""

        if _norm(c.get("apply_plan_decision")) != "SAFE_APPLY_CANDIDATE":
            skip_reason = "apply_plan_not_safe_apply"
        elif not asset or not metric or not year:
            skip_reason = "missing_asset_metric_or_year"
        elif not _is_valid_year(year):
            skip_reason = "invalid_year_label"
        elif ckey in seen_input_keys:
            skip_reason = "duplicate_candidate_key_in_input"
        elif _to_float(value) is None:
            skip_reason = "non_numeric_value"
        else:
            matches = existing_key_to_rows.get(ckey, [])
            if matches:
                has_same = any(_value_unit_equal(value, unit, m.get("final_value", ""), m.get("final_unit", "")) for m in matches)
                if has_same:
                    skip_reason = "duplicate_against_existing_06"
                else:
                    skip_reason = "conflict_against_existing_06"

        seen_input_keys.add(ckey)
        if skip_reason:
            skipped = dict(c)
            skipped["skip_reason"] = skip_reason
            skipped_rows.append(skipped)
            continue

        new_row = _build_new_06_row(base_cols, c)
        sandbox_06_df = pd.concat([sandbox_06_df, pd.DataFrame([new_row])], ignore_index=True)
        existing_key_to_rows.setdefault(ckey, []).append({"final_value": _norm(new_row.get("final_value")), "final_unit": _norm(new_row.get("final_unit"))})
        applied = dict(c)
        applied["dry_run_action"] = "applied_to_sandbox_copy"
        applied_rows.append(applied)
        diff_rows.append(
            {
                "diff_action": "ADD",
                "asset_package": asset,
                "standard_metric": metric,
                "year": year,
                "final_value": value,
                "final_unit": unit,
                "final_value_source": "ai_extract_safe_dry_run",
                "trace_note": new_row.get("trace_note", ""),
            }
        )

    # post-check duplicates/conflicts in sandbox copy
    duplicate_count_after = 0
    conflict_count_after = 0
    gcols = ["asset_package", "standard_metric", "year"]
    dup_groups = sandbox_06_df.groupby(gcols, dropna=False).size().reset_index(name="count")
    duplicate_count_after = int((dup_groups["count"] > 1).sum())
    for _, grp in sandbox_06_df.groupby(gcols, dropna=False):
        if len(grp) <= 1:
            continue
        vals = set((round(_to_float(v), 8) if _to_float(v) is not None else _norm(v), _norm(u)) for v, u in zip(grp["final_value"], grp["final_unit"]))
        if len(vals) > 1:
            conflict_count_after += 1

    applied_df = pd.DataFrame(applied_rows)
    skipped_df = pd.DataFrame(skipped_rows)
    diff_df = pd.DataFrame(diff_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_copy = _safe_write_excel({"dry_run_06": sandbox_06_df}, output_dir / "ai_extract_apply_dry_run_06_copy.xlsx")
    out_diff = _safe_write_excel({"diff": diff_df if not diff_df.empty else pd.DataFrame(columns=["diff_action"])}, output_dir / "ai_extract_apply_dry_run_diff.xlsx")
    out_applied = _safe_write_excel({"applied_rows": applied_df if not applied_df.empty else pd.DataFrame(columns=["dry_run_action"])}, output_dir / "ai_extract_apply_dry_run_applied_rows.xlsx")
    out_skipped = _safe_write_excel({"skipped_rows": skipped_df if not skipped_df.empty else pd.DataFrame(columns=["skip_reason"])}, output_dir / "ai_extract_apply_dry_run_skipped_rows.xlsx")

    after = _snapshot_files(_collect_production_guard_files(delivery_dir))
    guard_rows = _compare_snapshot(before, after)
    changed_count = sum(1 for r in guard_rows if r.get("changed") == "1")
    production_unchanged = changed_count == 0
    delivery_status_after = _run_delivery_check_json(delivery_dir)

    dry_run_applied_count = len(applied_rows)
    skipped_count = len(skipped_rows)

    generated_outputs = [
        str(out_copy),
        str(out_diff),
        str(out_applied),
        str(out_skipped),
        str(delivery_dir / "66_ai_extract_apply_dry_run_log.md"),
        str(delivery_dir / "66_ai_extract_apply_dry_run_log.xlsx"),
        str(delivery_dir / "67_ai_extract_apply_dry_run_evaluation.md"),
        str(delivery_dir / "67_ai_extract_apply_dry_run_evaluation.xlsx"),
    ]

    commands_run = [
        f"{sys.executable} -m py_compile {helper_path}",
        f"{sys.executable} {helper_path} --safe-apply-xlsx {safe_apply_xlsx} --final-06-xlsx {final_06_xlsx} --delivery-dir {delivery_dir} --output-dir {output_dir}",
        f"{sys.executable} D:/_datefac/tools/check_delivery_state.py --json",
    ]

    skip_reason_counts = Counter([_norm(r.get("skip_reason")) for r in skipped_rows])
    eval_status = "PASS"
    if changed_count > 0 or delivery_status_after.get("overall_status") != "PASS":
        eval_status = "FAIL"
    elif dry_run_applied_count == 0:
        eval_status = "WARN"

    _safe_write_text(
        delivery_dir / "66_ai_extract_apply_dry_run_log.md",
        "\n".join(
            [
                "# AI Extract Apply Dry Run Log",
                "",
                f"- task_title: {task_title}",
                f"- started_at: {started_at}",
                f"- finished_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- commands_run: {json.dumps(commands_run, ensure_ascii=False)}",
                f"- input_safe_apply_count: {input_safe_apply_count}",
                f"- dry_run_applied_count: {dry_run_applied_count}",
                f"- skipped_count: {skipped_count}",
                f"- duplicate_count_after: {duplicate_count_after}",
                f"- conflict_count_after: {conflict_count_after}",
                f"- skip_reason_counts: {json.dumps(dict(skip_reason_counts), ensure_ascii=False)}",
                f"- production_guard_changed_count: {changed_count}",
                f"- generated_outputs: {json.dumps(generated_outputs, ensure_ascii=False)}",
            ]
        ),
    )

    _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": task_title},
                    {"field": "input_safe_apply_count", "value": input_safe_apply_count},
                    {"field": "dry_run_applied_count", "value": dry_run_applied_count},
                    {"field": "skipped_count", "value": skipped_count},
                    {"field": "duplicate_count_after", "value": duplicate_count_after},
                    {"field": "conflict_count_after", "value": conflict_count_after},
                    {"field": "production_guard_changed_count", "value": changed_count},
                ]
            ),
            "applied_rows": applied_df if not applied_df.empty else pd.DataFrame(columns=["dry_run_action"]),
            "skipped_rows": skipped_df if not skipped_df.empty else pd.DataFrame(columns=["skip_reason"]),
            "diff": diff_df if not diff_df.empty else pd.DataFrame(columns=["diff_action"]),
            "skip_reason_counts": pd.DataFrame([{"skip_reason": k, "count": v} for k, v in sorted(skip_reason_counts.items())]),
            "post_duplicate_groups": dup_groups[dup_groups["count"] > 1].copy(),
            "production_guard": pd.DataFrame(guard_rows),
        },
        delivery_dir / "66_ai_extract_apply_dry_run_log.xlsx",
    )

    _safe_write_text(
        delivery_dir / "67_ai_extract_apply_dry_run_evaluation.md",
        "\n".join(
            [
                "# AI Extract Apply Dry Run Evaluation",
                "",
                f"- evaluation_status: {eval_status}",
                f"- input_safe_apply_count: {input_safe_apply_count}",
                f"- dry_run_applied_count: {dry_run_applied_count}",
                f"- skipped_count: {skipped_count}",
                f"- duplicate_count_after: {duplicate_count_after}",
                f"- conflict_count_after: {conflict_count_after}",
                f"- production_delivery_status_after: {json.dumps(delivery_status_after, ensure_ascii=False)}",
                f"- production_files_unchanged: {production_unchanged}",
                "- next_step: inspect skipped conflict rows and decide whether to route into manual_review before any real apply writer is enabled.",
            ]
        ),
    )

    _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "evaluation_status", "value": eval_status},
                    {"field": "input_safe_apply_count", "value": input_safe_apply_count},
                    {"field": "dry_run_applied_count", "value": dry_run_applied_count},
                    {"field": "skipped_count", "value": skipped_count},
                    {"field": "duplicate_count_after", "value": duplicate_count_after},
                    {"field": "conflict_count_after", "value": conflict_count_after},
                    {"field": "production_delivery_status_after", "value": json.dumps(delivery_status_after, ensure_ascii=False)},
                    {"field": "production_files_unchanged", "value": "1" if production_unchanged else "0"},
                ]
            ),
            "applied_rows": applied_df if not applied_df.empty else pd.DataFrame(columns=["dry_run_action"]),
            "skipped_rows": skipped_df if not skipped_df.empty else pd.DataFrame(columns=["skip_reason"]),
            "diff": diff_df if not diff_df.empty else pd.DataFrame(columns=["diff_action"]),
            "production_guard": pd.DataFrame(guard_rows),
        },
        delivery_dir / "67_ai_extract_apply_dry_run_evaluation.xlsx",
    )

    print(f"task_title: {task_title}")
    print(f"helper_path: {helper_path}")
    print(f"input_safe_apply_count: {input_safe_apply_count}")
    print(f"dry_run_applied_count: {dry_run_applied_count}")
    print(f"skipped_count: {skipped_count}")
    print(f"duplicate_count_after: {duplicate_count_after}")
    print(f"conflict_count_after: {conflict_count_after}")
    print(f"generated_outputs: {json.dumps(generated_outputs, ensure_ascii=False)}")
    print(f"production_delivery_status_after: {json.dumps(delivery_status_after, ensure_ascii=False)}")
    print(f"production_files_unchanged: {production_unchanged}")

    return 0 if eval_status != "FAIL" else 4


if __name__ == "__main__":
    raise SystemExit(main())
