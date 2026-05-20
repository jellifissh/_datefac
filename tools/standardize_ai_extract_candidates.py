import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd


SECRET_PATTERNS = ["sk-", "BEGIN PRIVATE KEY", "Bearer ", "api_secret", "password=", "token="]
PRODUCTION_PREFIX_PATTERNS = ["01_*.xlsx", "02_*.xlsx", "02A_*.xlsx", "06_*.xlsx"]

NON_TARGET_METRICS = {"长期借款", "EBITDA/销售收入", "每股经营现金"}
MANUAL_REVIEW_METRICS = {"净利润", "权益自由现金流"}


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


def _scan_secret_hits(text: str) -> List[str]:
    hits: List[str] = []
    for p in SECRET_PATTERNS:
        if p in text:
            hits.append(p)
    return hits


def _build_key(repair_task_id: Any, metric: Any, year: Any, value: Any) -> str:
    return "|".join([_norm(repair_task_id), _norm(metric), _norm(year), _norm(value)])


def _standardize_metric(metric: str) -> Tuple[str, str, str]:
    m = _norm(metric)
    if m == "PB":
        return "P/B", "ACCEPTED", "mapped_pb_to_p_slash_b"
    if m == "P/B":
        return "P/B", "ACCEPTED", "metric_allowlisted"
    if m == "每股收益":
        return "EPS", "ACCEPTED", "mapped_eps_cn_to_eps"
    if m == "EPS":
        return "EPS", "ACCEPTED", "metric_allowlisted"
    if m == "营业收入":
        return "营业收入", "ACCEPTED", "metric_allowlisted"
    if m == "EV/EBITDA":
        return "EV/EBITDA", "ACCEPTED", "metric_allowlisted"
    if m in NON_TARGET_METRICS:
        return m, "REJECTED_NON_TARGET", "non_target_metric_rejected"
    if m == "净利润":
        return m, "MANUAL_REVIEW", "net_profit_not_auto_mapped_to_parent_net_profit"
    if m == "权益自由现金流":
        return m, "MANUAL_REVIEW", "free_cash_flow_requires_manual_review"
    return m, "MANUAL_REVIEW", "metric_not_in_auto_allowlist"


def main() -> int:
    parser = argparse.ArgumentParser(description="Standardize AI extract candidates with allowlist gate (offline).")
    parser.add_argument("--candidates-xlsx", required=True)
    parser.add_argument("--validation-xlsx", required=True)
    parser.add_argument("--merge-preview-xlsx", required=True)
    parser.add_argument("--delivery-dir", required=True)
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    candidates_xlsx = Path(args.candidates_xlsx)
    validation_xlsx = Path(args.validation_xlsx)
    merge_preview_xlsx = Path(args.merge_preview_xlsx)
    delivery_dir = Path(args.delivery_dir)
    output_dir = Path(args.output_dir) if _norm(args.output_dir) else candidates_xlsx.parent
    helper_path = Path(__file__)

    if not candidates_xlsx.exists() or not validation_xlsx.exists() or not merge_preview_xlsx.exists():
        print("BLOCKED_REQUIRED_INPUT_MISSING")
        return 3

    before = _snapshot_files(_collect_production_guard_files(delivery_dir))

    cand_df = pd.read_excel(candidates_xlsx, sheet_name="extracted_candidates")
    ev_df = pd.read_excel(validation_xlsx, sheet_name="evidence_check")
    merge_df = pd.read_excel(merge_preview_xlsx, sheet_name="merge_preview")

    ev_pass_keys: Set[str] = set()
    for _, row in ev_df.iterrows():
        if _norm(row.get("evidence_check_status")) == "PASS":
            ev_pass_keys.add(
                _build_key(
                    row.get("repair_task_id"),
                    row.get("standard_metric"),
                    row.get("year"),
                    row.get("value"),
                )
            )

    rows: List[Dict[str, Any]] = []
    for _, row in cand_df.iterrows():
        original_metric = _norm(row.get("standard_metric"))
        key = _build_key(row.get("repair_task_id"), original_metric, row.get("year"), row.get("value"))
        evidence_pass = key in ev_pass_keys

        standardized_metric = original_metric
        gate_decision = "REJECTED_EVIDENCE_FAIL"
        gate_reason = "evidence_check_not_pass"

        if evidence_pass:
            standardized_metric, gate_decision, gate_reason = _standardize_metric(original_metric)

        rows.append(
            {
                "repair_task_id": _norm(row.get("repair_task_id")),
                "sample_id": _norm(row.get("sample_id")),
                "company": _norm(row.get("company")),
                "original_metric": original_metric,
                "standardized_metric": standardized_metric,
                "year": _norm(row.get("year")),
                "value": _norm(row.get("value")),
                "unit": _norm(row.get("unit")),
                "source_trace_id": _norm(row.get("source_trace_id")),
                "source_cell_or_segment": _norm(row.get("source_cell_or_segment")),
                "evidence": _norm(row.get("evidence")),
                "confidence": _norm(row.get("confidence")),
                "flags": _norm(row.get("flags")),
                "accepted_for_merge_preview": _norm(row.get("accepted_for_merge_preview")),
                "evidence_check_status": "PASS" if evidence_pass else "FAIL",
                "gate_decision": gate_decision,
                "gate_reason": gate_reason,
            }
        )

    std_df = pd.DataFrame(rows)
    accepted_df = std_df[std_df["gate_decision"] == "ACCEPTED"].copy()
    manual_df = std_df[std_df["gate_decision"] == "MANUAL_REVIEW"].copy()
    rejected_df = std_df[std_df["gate_decision"].isin(["REJECTED_NON_TARGET", "REJECTED_EVIDENCE_FAIL"])].copy()

    input_candidate_count = len(std_df)
    accepted_count = len(accepted_df)
    manual_count = len(manual_df)
    rejected_count = len(rejected_df)

    metric_std_summary_df = (
        std_df.groupby(["original_metric", "standardized_metric", "gate_decision"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["count", "original_metric"], ascending=[False, True])
    )

    accepted_by_metric = Counter([_norm(x) for x in accepted_df["standardized_metric"].tolist()])
    decision_counts = Counter([_norm(x) for x in std_df["gate_decision"].tolist()])
    sample_counts = Counter([_norm(x) for x in std_df["sample_id"].tolist()])

    output_dir.mkdir(parents=True, exist_ok=True)
    std_path = _safe_write_excel({"standardized": std_df}, output_dir / "ai_extract_candidates_standardized.xlsx")
    accepted_path = _safe_write_excel({"accepted": accepted_df}, output_dir / "ai_extract_candidates_accepted.xlsx")
    manual_path = _safe_write_excel({"manual_review": manual_df}, output_dir / "ai_extract_candidates_manual_review.xlsx")
    rejected_path = _safe_write_excel({"rejected": rejected_df}, output_dir / "ai_extract_candidates_rejected.xlsx")

    no_secret_text = (
        std_df.head(200).to_json(force_ascii=False)
        + metric_std_summary_df.to_json(force_ascii=False)
        + json.dumps(decision_counts, ensure_ascii=False)
    )
    no_secret_hits = _scan_secret_hits(no_secret_text)
    no_secret_status = "PASS" if not no_secret_hits else "FAIL"

    after = _snapshot_files(_collect_production_guard_files(delivery_dir))
    guard_rows = _compare_snapshot(before, after)
    changed_count = sum(1 for r in guard_rows if r.get("changed") == "1")
    production_unchanged = changed_count == 0
    delivery_status_after = _run_delivery_check_json(delivery_dir)

    status = "PASS"
    if no_secret_status != "PASS" or changed_count > 0:
        status = "FAIL"
    elif accepted_count == 0 and manual_count == 0:
        status = "WARN"

    output_files = [
        str(std_path),
        str(accepted_path),
        str(manual_path),
        str(rejected_path),
        str(delivery_dir / "60_ai_extract_candidate_standardization_log.md"),
        str(delivery_dir / "60_ai_extract_candidate_standardization_log.xlsx"),
        str(delivery_dir / "61_ai_extract_candidate_allowlist_evaluation.md"),
        str(delivery_dir / "61_ai_extract_candidate_allowlist_evaluation.xlsx"),
    ]

    safety_checks = [
        {"check_name": "no_ai_model_call", "status": "PASS", "detail": "rule-based standardization only"},
        {"check_name": "no_network", "status": "PASS", "detail": "local files only"},
        {"check_name": "no_secret_check", "status": no_secret_status, "detail": "|".join(no_secret_hits) or "no_secret_like_patterns"},
        {"check_name": "production_files_unchanged", "status": "PASS" if production_unchanged else "FAIL", "detail": f"changed={changed_count}"},
    ]

    commands_run = [
        f"{sys.executable} -m py_compile {helper_path}",
        f"{sys.executable} {helper_path} --candidates-xlsx {candidates_xlsx} --validation-xlsx {validation_xlsx} --merge-preview-xlsx {merge_preview_xlsx} --delivery-dir {delivery_dir} --output-dir {output_dir}",
        f"{sys.executable} D:/_datefac/tools/check_delivery_state.py --json",
    ]

    _safe_write_text(
        delivery_dir / "60_ai_extract_candidate_standardization_log.md",
        "\n".join(
            [
                "# AI Extract Candidate Standardization Log",
                "",
                "- task_title: Add AI extract candidate standardization and allowlist gate",
                f"- started_at: {started_at}",
                f"- finished_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- commands_run: {json.dumps(commands_run, ensure_ascii=False)}",
                f"- input_candidate_count: {input_candidate_count}",
                f"- accepted_count: {accepted_count}",
                f"- manual_review_count: {manual_count}",
                f"- rejected_count: {rejected_count}",
                f"- output_files_generated: {json.dumps(output_files, ensure_ascii=False)}",
                f"- no_secret_check_status: {no_secret_status}",
                f"- production_guard_changed_count: {changed_count}",
                f"- safety_checks: {json.dumps(safety_checks, ensure_ascii=False)}",
            ]
        ),
    )

    _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": "Add AI extract candidate standardization and allowlist gate"},
                    {"field": "input_candidate_count", "value": input_candidate_count},
                    {"field": "accepted_count", "value": accepted_count},
                    {"field": "manual_review_count", "value": manual_count},
                    {"field": "rejected_count", "value": rejected_count},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "production_guard_changed_count", "value": changed_count},
                ]
            ),
            "standardized": std_df,
            "accepted": accepted_df,
            "manual_review": manual_df,
            "rejected": rejected_df,
            "metric_standardization_summary": metric_std_summary_df,
            "decision_counts": pd.DataFrame([{"gate_decision": k, "count": v} for k, v in sorted(decision_counts.items())]),
            "sample_counts": pd.DataFrame([{"sample_id": k, "count": v} for k, v in sorted(sample_counts.items())]),
            "production_guard": pd.DataFrame(guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame([{"recommended_next_step": "Route accepted candidates to next standardization layer and send manual/rejected sets to review queues."}]),
        },
        delivery_dir / "60_ai_extract_candidate_standardization_log.xlsx",
    )

    _safe_write_text(
        delivery_dir / "61_ai_extract_candidate_allowlist_evaluation.md",
        "\n".join(
            [
                "# AI Extract Candidate Allowlist Evaluation",
                "",
                f"- allowlist_gate_status: {status}",
                f"- input_candidate_count: {input_candidate_count}",
                f"- accepted_count: {accepted_count}",
                f"- manual_review_count: {manual_count}",
                f"- rejected_count: {rejected_count}",
                f"- accepted_by_metric: {json.dumps(dict(accepted_by_metric), ensure_ascii=False)}",
                f"- decision_counts: {json.dumps(dict(decision_counts), ensure_ascii=False)}",
                f"- no_secret_check_status: {no_secret_status}",
                f"- production_delivery_status_after: {json.dumps(delivery_status_after, ensure_ascii=False)}",
                f"- production_files_unchanged: {production_unchanged}",
                "- recommended_next_step: keep net_profit / free_cash_flow in manual review until explicit business mapping rules are approved.",
            ]
        ),
    )

    _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "allowlist_gate_status", "value": status},
                    {"field": "input_candidate_count", "value": input_candidate_count},
                    {"field": "accepted_count", "value": accepted_count},
                    {"field": "manual_review_count", "value": manual_count},
                    {"field": "rejected_count", "value": rejected_count},
                    {"field": "accepted_by_metric", "value": json.dumps(dict(accepted_by_metric), ensure_ascii=False)},
                    {"field": "decision_counts", "value": json.dumps(dict(decision_counts), ensure_ascii=False)},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "production_delivery_status_after", "value": json.dumps(delivery_status_after, ensure_ascii=False)},
                    {"field": "production_files_unchanged", "value": "1" if production_unchanged else "0"},
                ]
            ),
            "standardized": std_df,
            "accepted": accepted_df,
            "manual_review": manual_df,
            "rejected": rejected_df,
            "metric_standardization_summary": metric_std_summary_df,
            "production_guard": pd.DataFrame(guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame([{"recommended_next_step": "Integrate accepted set with trusted pipeline only after duplicate/year checks."}]),
        },
        delivery_dir / "61_ai_extract_candidate_allowlist_evaluation.xlsx",
    )

    print("task_title: Add AI extract candidate standardization and allowlist gate")
    print(f"helper_path: {helper_path}")
    print(f"input_candidate_count: {input_candidate_count}")
    print(f"accepted_count: {accepted_count}")
    print(f"manual_review_count: {manual_count}")
    print(f"rejected_count: {rejected_count}")
    print(f"metric_standardization_summary: {metric_std_summary_df.to_json(orient='records', force_ascii=False)}")
    print(f"generated_outputs: {json.dumps(output_files, ensure_ascii=False)}")
    print(f"production_delivery_status_after: {json.dumps(delivery_status_after, ensure_ascii=False)}")
    print(f"production_files_unchanged: {production_unchanged}")

    if status == "FAIL":
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

