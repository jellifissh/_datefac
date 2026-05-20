import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd


PRODUCTION_PREFIX_PATTERNS = ["01_*.xlsx", "02_*.xlsx", "02A_*.xlsx", "06_*.xlsx"]
YEAR_RE = re.compile(r"^20\d{2}(A|E)?$", re.IGNORECASE)
RATIO_METRICS = {"P/E", "P/B", "EV/EBITDA", "ROE", "毛利率", "净利率"}
AMOUNT_METRICS = {"营业收入", "归属母公司净利润", "EBITDA"}
UNIT_ALLOWED_RATIO = {"", "倍", "x", "X", "%", "％"}
UNIT_ALLOWED_AMOUNT = {"百万元", "亿元", "万元", "元"}
UNIT_ALLOWED_EPS = {"", "元/股", "元"}


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


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


def _to_float(v: Any) -> Optional[float]:
    s = _norm(v)
    if not s:
        return None
    s = s.replace(",", "")
    try:
        return float(s)
    except Exception:
        return None


def _year_valid(year: str) -> bool:
    return bool(YEAR_RE.match(_norm(year)))


def _unit_decision(metric: str, unit: str) -> Tuple[bool, bool, str]:
    m = _norm(metric)
    u = _norm(unit)
    if m in RATIO_METRICS:
        if u in UNIT_ALLOWED_RATIO:
            return True, False, "ratio_unit_ok_or_blank"
        return False, True, "ratio_unit_invalid"
    if m in AMOUNT_METRICS:
        if u in UNIT_ALLOWED_AMOUNT:
            return True, False, "amount_unit_ok"
        if u == "":
            return False, False, "amount_unit_missing"
        return False, True, "amount_unit_invalid"
    if m == "EPS":
        if u in UNIT_ALLOWED_EPS:
            return True, False, "eps_unit_ok_or_blank"
        return False, True, "eps_unit_invalid"
    if u == "":
        return True, False, "unit_blank_unknown_metric"
    return False, False, "unit_nonempty_unknown_metric_manual_review"


def _normalize_unit(unit: str) -> str:
    u = _norm(unit)
    if u in {"x", "X"}:
        return "倍"
    if u == "％":
        return "%"
    return u


def _load_06(delivery_dir: Path) -> Tuple[Path, pd.DataFrame]:
    exact = delivery_dir / "06_最终核心财务指标.xlsx"
    if exact.exists():
        return exact, pd.read_excel(exact)
    all_06 = sorted(delivery_dir.glob("06_*核心财务指标*.xlsx"))
    if not all_06:
        raise FileNotFoundError("06 file not found in delivery dir")
    primary = [p for p in all_06 if "_copy_" not in p.name]
    pick = primary[0] if primary else all_06[0]
    return pick, pd.read_excel(pick)


def _load_company_asset_map(accepted_path: Path) -> Tuple[Dict[str, str], Dict[str, str], List[Dict[str, str]]]:
    run_root = accepted_path.parent.parent.parent
    assets_root = run_root / "assets"
    company_to_asset: Dict[str, str] = {}
    sample_to_asset: Dict[str, str] = {}
    rows: List[Dict[str, str]] = []
    if not assets_root.exists():
        return company_to_asset, sample_to_asset, rows
    summary_files = sorted(assets_root.glob("*_资产包/stage1_sandbox_asset_summary.xlsx"))
    for path in summary_files:
        try:
            df = pd.read_excel(path, sheet_name="summary")
        except Exception:
            continue
        for _, r in df.iterrows():
            asset = _norm(r.get("asset_package"))
            company = _norm(r.get("company"))
            pdf_file = _norm(r.get("pdf_file"))
            sample = ""
            if company == "三鑫医疗":
                sample = "S1"
            elif company == "冠豪高新":
                sample = "S2"
            elif company == "科锐国际":
                sample = "S3"
            if company and asset:
                company_to_asset[company] = asset
            if sample and asset:
                sample_to_asset[sample] = asset
            rows.append({"summary_file": str(path), "company": company, "sample_id": sample, "asset_package": asset, "pdf_file": pdf_file})
    return company_to_asset, sample_to_asset, rows


def _candidate_key(sample_id: str, company: str, metric: str, year: str) -> str:
    return "|".join([_norm(sample_id), _norm(company), _norm(metric), _norm(year)])


def _resolve_asset_package(sample_id: str, company: str, c2a: Dict[str, str], s2a: Dict[str, str]) -> str:
    sid = _norm(sample_id)
    cmpy = _norm(company)
    if sid in s2a:
        return s2a[sid]
    if cmpy in c2a:
        return c2a[cmpy]
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate merge decisions for accepted AI extract candidates (read-only).")
    parser.add_argument("--accepted-xlsx", required=True)
    parser.add_argument("--delivery-dir", required=True)
    parser.add_argument("--manual-queue-xlsx", default="")
    parser.add_argument("--manual-year-override-xlsx", default="")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    task_title = "Simulate accepted AI extract candidate merge"
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    helper_path = Path(__file__)
    accepted_xlsx = Path(args.accepted_xlsx)
    delivery_dir = Path(args.delivery_dir)
    output_dir = Path(args.output_dir) if _norm(args.output_dir) else accepted_xlsx.parent
    manual_queue_xlsx = Path(args.manual_queue_xlsx) if _norm(args.manual_queue_xlsx) else None
    manual_year_override_xlsx = Path(args.manual_year_override_xlsx) if _norm(args.manual_year_override_xlsx) else None

    if not accepted_xlsx.exists():
        print("BLOCKED_MISSING_ACCEPTED_XLSX")
        return 3

    before = _snapshot_files(_collect_production_guard_files(delivery_dir))

    accepted_df = pd.read_excel(accepted_xlsx, sheet_name="accepted")
    d06_path, d06_df = _load_06(delivery_dir)

    if manual_queue_xlsx and manual_queue_xlsx.exists():
        _ = pd.read_excel(manual_queue_xlsx)
    if manual_year_override_xlsx and manual_year_override_xlsx.exists():
        _ = pd.read_excel(manual_year_override_xlsx)

    c2a, s2a, map_rows = _load_company_asset_map(accepted_xlsx)

    d06_rows: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for _, r in d06_df.iterrows():
        asset = _norm(r.get("asset_package"))
        metric = _norm(r.get("standard_metric"))
        year = _norm(r.get("year"))
        if not asset or not metric or not year:
            continue
        key = "|".join([asset, metric, year])
        d06_rows[key].append(
            {
                "final_value": _norm(r.get("final_value")),
                "final_unit": _norm(r.get("final_unit")),
                "final_value_source": _norm(r.get("final_value_source")),
            }
        )

    cand_key_counts: Counter[str] = Counter()
    for _, r in accepted_df.iterrows():
        ck = _candidate_key(r.get("sample_id"), r.get("company"), r.get("standardized_metric"), r.get("year"))
        cand_key_counts[ck] += 1

    rows: List[Dict[str, Any]] = []
    duplicate_count = 0
    conflict_count = 0
    for _, r in accepted_df.iterrows():
        sample_id = _norm(r.get("sample_id"))
        company = _norm(r.get("company"))
        original_metric = _norm(r.get("original_metric"))
        metric = _norm(r.get("standardized_metric"))
        year = _norm(r.get("year"))
        value = _norm(r.get("value"))
        unit = _norm(r.get("unit"))
        source_trace_id = _norm(r.get("source_trace_id"))
        source_cell_or_segment = _norm(r.get("source_cell_or_segment"))
        evidence = _norm(r.get("evidence"))
        gate_decision = _norm(r.get("gate_decision"))
        candidate_key = _candidate_key(sample_id, company, metric, year)

        merge_decision = "SAFE_MERGE_CANDIDATE"
        merge_reason = "passed_all_checks"
        risk_flags: List[str] = []

        if not _year_valid(year):
            merge_decision = "BLOCK_INVALID_YEAR"
            merge_reason = "year_label_not_supported"
            risk_flags.append("invalid_year")

        unit_ok, unit_block, unit_reason = _unit_decision(metric, unit)
        if merge_decision == "SAFE_MERGE_CANDIDATE" and not unit_ok:
            if unit_block:
                merge_decision = "BLOCK_INVALID_UNIT"
                merge_reason = unit_reason
                risk_flags.append("invalid_unit")
            else:
                merge_decision = "MANUAL_REVIEW_REQUIRED"
                merge_reason = unit_reason
                risk_flags.append("unit_needs_review")

        if cand_key_counts.get(candidate_key, 0) > 1:
            duplicate_count += 1
            if merge_decision in {"SAFE_MERGE_CANDIDATE", "MANUAL_REVIEW_REQUIRED"}:
                merge_decision = "BLOCK_DUPLICATE"
                merge_reason = "candidate_key_duplicate_within_accepted_set"
            risk_flags.append("duplicate_in_candidates")

        resolved_asset_package = _resolve_asset_package(sample_id, company, c2a, s2a)
        existing_count = 0
        existing_values_json = "[]"
        if resolved_asset_package:
            d06_key = "|".join([resolved_asset_package, metric, year])
            existing = d06_rows.get(d06_key, [])
            existing_count = len(existing)
            existing_values_json = json.dumps(existing, ensure_ascii=False)
            if existing:
                existing_has_same = False
                existing_has_conflict = False
                cand_value = _to_float(value)
                cand_unit_n = _normalize_unit(unit)
                for ex in existing:
                    ex_value_s = _norm(ex.get("final_value"))
                    ex_unit_n = _normalize_unit(_norm(ex.get("final_unit")))
                    ex_value = _to_float(ex_value_s)
                    value_equal = False
                    if cand_value is not None and ex_value is not None:
                        value_equal = abs(cand_value - ex_value) <= 1e-6
                    elif value == ex_value_s:
                        value_equal = True

                    unit_compatible = False
                    if cand_unit_n == ex_unit_n:
                        unit_compatible = True
                    elif cand_unit_n == "" or ex_unit_n == "":
                        unit_compatible = True

                    if value_equal and unit_compatible:
                        existing_has_same = True
                    else:
                        existing_has_conflict = True

                if existing_has_same:
                    if merge_decision in {"SAFE_MERGE_CANDIDATE", "MANUAL_REVIEW_REQUIRED"}:
                        merge_decision = "BLOCK_DUPLICATE"
                        merge_reason = "same_metric_year_already_exists_in_06"
                    risk_flags.append("duplicate_against_06")
                elif existing_has_conflict:
                    conflict_count += 1
                    merge_decision = "BLOCK_CONFLICT"
                    merge_reason = "same_metric_year_conflicts_with_06"
                    risk_flags.append("conflict_against_06")
        else:
            if merge_decision == "SAFE_MERGE_CANDIDATE":
                merge_decision = "MANUAL_REVIEW_REQUIRED"
                merge_reason = "cannot_map_candidate_to_asset_package"
                risk_flags.append("missing_asset_mapping")

        rows.append(
            {
                "sample_id": sample_id,
                "company": company,
                "resolved_asset_package": resolved_asset_package,
                "candidate_key": candidate_key,
                "original_metric": original_metric,
                "standardized_metric": metric,
                "year": year,
                "value": value,
                "unit": unit,
                "source_trace_id": source_trace_id,
                "source_cell_or_segment": source_cell_or_segment,
                "evidence": evidence,
                "gate_decision": gate_decision,
                "merge_decision": merge_decision,
                "merge_reason": merge_reason,
                "risk_flags": "|".join(risk_flags),
                "candidate_key_count_in_accepted": cand_key_counts.get(candidate_key, 0),
                "existing_06_match_count": existing_count,
                "existing_06_values": existing_values_json,
            }
        )

    all_df = pd.DataFrame(rows)
    safe_df = all_df[all_df["merge_decision"] == "SAFE_MERGE_CANDIDATE"].copy()
    manual_df = all_df[all_df["merge_decision"] == "MANUAL_REVIEW_REQUIRED"].copy()
    blocked_df = all_df[all_df["merge_decision"].str.startswith("BLOCK_")].copy()

    input_accepted_count = len(all_df)
    safe_count = len(safe_df)
    manual_count = len(manual_df)
    blocked_count = len(blocked_df)
    decision_counts = Counter(all_df["merge_decision"].tolist())

    metric_summary_df = (
        all_df.groupby(["standardized_metric", "merge_decision"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "standardized_metric"], ascending=[False, True])
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    out_all = _safe_write_excel({"all": all_df}, output_dir / "ai_extract_merge_simulation_all.xlsx")
    out_safe = _safe_write_excel({"safe_candidates": safe_df}, output_dir / "ai_extract_merge_safe_candidates.xlsx")
    out_manual = _safe_write_excel({"manual_review": manual_df}, output_dir / "ai_extract_merge_manual_review.xlsx")
    out_blocked = _safe_write_excel({"blocked": blocked_df}, output_dir / "ai_extract_merge_blocked.xlsx")

    after = _snapshot_files(_collect_production_guard_files(delivery_dir))
    guard_rows = _compare_snapshot(before, after)
    changed_count = sum(1 for r in guard_rows if r.get("changed") == "1")
    production_unchanged = changed_count == 0
    delivery_status_after = _run_delivery_check_json(delivery_dir)

    report_files = [
        str(out_all),
        str(out_safe),
        str(out_manual),
        str(out_blocked),
        str(delivery_dir / "62_ai_extract_candidate_merge_simulation_log.md"),
        str(delivery_dir / "62_ai_extract_candidate_merge_simulation_log.xlsx"),
        str(delivery_dir / "63_ai_extract_candidate_merge_simulation_evaluation.md"),
        str(delivery_dir / "63_ai_extract_candidate_merge_simulation_evaluation.xlsx"),
    ]

    commands_run = [
        f"{sys.executable} -m py_compile {helper_path}",
        f"{sys.executable} {helper_path} --accepted-xlsx {accepted_xlsx} --delivery-dir {delivery_dir} --manual-queue-xlsx {manual_queue_xlsx} --manual-year-override-xlsx {manual_year_override_xlsx} --output-dir {output_dir}",
        f"{sys.executable} D:/_datefac/tools/check_delivery_state.py --json",
    ]

    _safe_write_text(
        delivery_dir / "62_ai_extract_candidate_merge_simulation_log.md",
        "\n".join(
            [
                "# AI Extract Candidate Merge Simulation Log",
                "",
                f"- task_title: {task_title}",
                f"- started_at: {started_at}",
                f"- finished_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- accepted_input_path: {accepted_xlsx}",
                f"- delivery_06_path: {d06_path}",
                f"- commands_run: {json.dumps(commands_run, ensure_ascii=False)}",
                f"- input_accepted_count: {input_accepted_count}",
                f"- safe_merge_candidate_count: {safe_count}",
                f"- manual_review_required_count: {manual_count}",
                f"- blocked_count: {blocked_count}",
                f"- duplicate_count: {duplicate_count}",
                f"- conflict_count: {conflict_count}",
                f"- sample_asset_mapping_rows: {len(map_rows)}",
                f"- production_guard_changed_count: {changed_count}",
                f"- generated_outputs: {json.dumps(report_files, ensure_ascii=False)}",
            ]
        ),
    )

    _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": task_title},
                    {"field": "input_accepted_count", "value": input_accepted_count},
                    {"field": "safe_merge_candidate_count", "value": safe_count},
                    {"field": "manual_review_required_count", "value": manual_count},
                    {"field": "blocked_count", "value": blocked_count},
                    {"field": "duplicate_count", "value": duplicate_count},
                    {"field": "conflict_count", "value": conflict_count},
                    {"field": "production_guard_changed_count", "value": changed_count},
                ]
            ),
            "all": all_df,
            "safe_candidates": safe_df,
            "manual_review": manual_df,
            "blocked": blocked_df,
            "metric_summary": metric_summary_df,
            "decision_counts": pd.DataFrame([{"merge_decision": k, "count": v} for k, v in sorted(decision_counts.items())]),
            "sample_asset_mapping": pd.DataFrame(map_rows),
            "production_guard": pd.DataFrame(guard_rows),
        },
        delivery_dir / "62_ai_extract_candidate_merge_simulation_log.xlsx",
    )

    status = "PASS"
    if changed_count > 0 or delivery_status_after.get("overall_status") != "PASS":
        status = "FAIL"
    elif safe_count == 0:
        status = "WARN"

    _safe_write_text(
        delivery_dir / "63_ai_extract_candidate_merge_simulation_evaluation.md",
        "\n".join(
            [
                "# AI Extract Candidate Merge Simulation Evaluation",
                "",
                f"- simulation_status: {status}",
                f"- input_accepted_count: {input_accepted_count}",
                f"- safe_merge_candidate_count: {safe_count}",
                f"- manual_review_required_count: {manual_count}",
                f"- blocked_count: {blocked_count}",
                f"- duplicate_count: {duplicate_count}",
                f"- conflict_count: {conflict_count}",
                f"- merge_decision_counts: {json.dumps(dict(decision_counts), ensure_ascii=False)}",
                f"- production_delivery_status_after: {json.dumps(delivery_status_after, ensure_ascii=False)}",
                f"- production_files_unchanged: {production_unchanged}",
                "- next_step: review SAFE_MERGE_CANDIDATE rows first, then manually adjudicate CONFLICT / INVALID_UNIT / INVALID_YEAR rows.",
            ]
        ),
    )

    _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "simulation_status", "value": status},
                    {"field": "input_accepted_count", "value": input_accepted_count},
                    {"field": "safe_merge_candidate_count", "value": safe_count},
                    {"field": "manual_review_required_count", "value": manual_count},
                    {"field": "blocked_count", "value": blocked_count},
                    {"field": "duplicate_count", "value": duplicate_count},
                    {"field": "conflict_count", "value": conflict_count},
                    {"field": "production_delivery_status_after", "value": json.dumps(delivery_status_after, ensure_ascii=False)},
                    {"field": "production_files_unchanged", "value": "1" if production_unchanged else "0"},
                ]
            ),
            "decision_counts": pd.DataFrame([{"merge_decision": k, "count": v} for k, v in sorted(decision_counts.items())]),
            "metric_summary": metric_summary_df,
            "safe_candidates": safe_df,
            "manual_review": manual_df,
            "blocked": blocked_df,
            "all": all_df,
            "production_guard": pd.DataFrame(guard_rows),
        },
        delivery_dir / "63_ai_extract_candidate_merge_simulation_evaluation.xlsx",
    )

    print(f"task_title: {task_title}")
    print(f"helper_path: {helper_path}")
    print(f"input_accepted_count: {input_accepted_count}")
    print(f"safe_merge_candidate_count: {safe_count}")
    print(f"manual_review_required_count: {manual_count}")
    print(f"blocked_count: {blocked_count}")
    print(f"duplicate_count: {duplicate_count}")
    print(f"conflict_count: {conflict_count}")
    print(f"generated_outputs: {json.dumps(report_files, ensure_ascii=False)}")
    print(f"production_delivery_status_after: {json.dumps(delivery_status_after, ensure_ascii=False)}")
    print(f"production_files_unchanged: {production_unchanged}")

    return 0 if status != "FAIL" else 4


if __name__ == "__main__":
    raise SystemExit(main())
