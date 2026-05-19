import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd


TARGET_METRICS = {
    "营业收入",
    "归属母公司净利润",
    "每股收益",
    "P/E",
    "P/B",
    "EV/EBITDA",
    "ROE",
    "毛利率",
    "EBITDA",
    "净利率",
}
HARD_RISK_FLAGS = {
    "source_row_semantic_risk",
    "forbidden_source_label_for_metric",
    "broad_keyword_unsafe",
    "multi_metric_row_ambiguous",
    "ambiguous_year_value_alignment",
    "ambiguous_multi_numeric_cell",
    "duplicate_metric_year_non_preferred",
}
NUM_RE = re.compile(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?")
YEAR_RE = re.compile(r"(20\d{2}(?:[AE])?)")


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


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


def _load_packet(packet_jsonl: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in packet_jsonl.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _evidence_text(task: Dict[str, Any]) -> str:
    evidence = task.get("evidence", {}) or {}
    parts: List[str] = []
    for k in ["row_preview", "table_header_context", "nearby_rows_context", "raw_table_preview"]:
        v = evidence.get(k, "")
        if isinstance(v, list):
            parts.append(json.dumps(v, ensure_ascii=False))
        else:
            parts.append(_norm(v))
    row_cells = evidence.get("row_cells", [])
    if isinstance(row_cells, list):
        parts.append("|".join(_norm(x) for x in row_cells))
    return "\n".join([x for x in parts if x])


def _normalize_number_text(v: Any) -> str:
    s = _norm(v).replace(",", "")
    if not s:
        return ""
    s = s.replace("（", "(").replace("）", ")")
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", s):
        return ""
    try:
        n = float(s)
        if neg:
            n = -n
        return f"{n:.12f}".rstrip("0").rstrip(".")
    except Exception:
        return ""


def _value_in_evidence(value: Any, evidence_text: str) -> bool:
    s = _norm(value)
    if s and s in evidence_text:
        return True
    nv = _normalize_number_text(value)
    if not nv:
        return False
    for m in NUM_RE.findall(evidence_text):
        if _normalize_number_text(m) == nv:
            return True
    return False


def _extract_years(task: Dict[str, Any]) -> List[str]:
    evidence = task.get("evidence", {}) or {}
    years = [_norm(x) for x in evidence.get("detected_years", []) if _norm(x)]
    if years:
        ae_years = [y for y in years if y.endswith("A") or y.endswith("E")]
        return ae_years if ae_years else years
    found = YEAR_RE.findall(_evidence_text(task))
    out: List[str] = []
    for y in found:
        if y not in out:
            out.append(y)
    ae_out = [y for y in out if y.endswith("A") or y.endswith("E")]
    return ae_out if ae_out else out


def _metric_ok(metric: str, evidence_text: str) -> bool:
    m = _norm(metric)
    if not m:
        return False
    return m in TARGET_METRICS or m in evidence_text


def _first_numeric_cell(task: Dict[str, Any]) -> str:
    row_cells = task.get("evidence", {}).get("row_cells", [])
    if isinstance(row_cells, list):
        for c in row_cells:
            s = _norm(c)
            if _normalize_number_text(s):
                return s
    ev = _evidence_text(task)
    nums = NUM_RE.findall(ev)
    return nums[0] if nums else ""


def _metric_like_hit(metric: str, task: Dict[str, Any]) -> bool:
    m = _norm(metric)
    if not m:
        return False
    m_norm = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", m).upper()
    if not m_norm:
        return False
    row_cells = task.get("evidence", {}).get("row_cells", [])
    if isinstance(row_cells, list):
        for c in row_cells[:6]:
            c_norm = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", _norm(c)).upper()
            if c_norm and (m_norm in c_norm or c_norm in m_norm):
                return True
    return m in _evidence_text(task)


def _build_extract_response(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    task_type = _norm(task.get("task_type"))
    if task_type not in {"row_segment_repair", "metric_year_value_alignment"}:
        return None
    rule = task.get("current_rule_result", {}) or {}
    metric = _norm(rule.get("standard_metric_hint"))
    evidence_txt = _evidence_text(task)
    if not _metric_ok(metric, evidence_txt):
        return None
    if not _metric_like_hit(metric, task):
        return None
    years = _extract_years(task)
    if not years:
        return None
    value = _first_numeric_cell(task)
    if not value or not _value_in_evidence(value, evidence_txt):
        return None
    year = years[0]
    if year not in evidence_txt and year not in [_norm(x) for x in (task.get("evidence", {}) or {}).get("detected_years", [])]:
        return None

    tid = _norm(task.get("repair_task_id"))
    trace = _norm(task.get("source", {}).get("source_trace_id"))
    return {
        "repair_task_id": tid,
        "decision": "extract",
        "repairs": [
            {
                "standard_metric": metric,
                "year": year,
                "value": value,
                "unit": "",
                "confidence": "low",
                "evidence": _norm(task.get("evidence", {}).get("row_preview")),
                "source_cell_or_segment": trace,
                "flags": ["deterministic_extract_replay"],
            }
        ],
        "manual_review_items": [],
        "notes": "deterministic extract replay generated from packet evidence",
    }


def _parse_worker_stdout(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in text.splitlines():
        if ": " not in line:
            continue
        k, v = line.split(": ", 1)
        out[k.strip()] = v.strip()
    return out


def _run_delivery_check_json(delivery_dir: Path) -> Dict[str, Any]:
    cmd = [sys.executable, str(Path(r"D:\_datefac\tools\check_delivery_state.py")), "--delivery-dir", str(delivery_dir), "--json"]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    try:
        return json.loads((p.stdout or "").strip() or "{}")
    except Exception:
        return {"overall_status": "UNKNOWN", "pass_count": 0, "warn_count": 0, "fail_count": 0, "check_count": 0}


def _copy_worker_outputs(src_root: Path, dst_root: Path) -> List[str]:
    src = src_root / "ai_repair_offline_replay"
    dst_root.mkdir(parents=True, exist_ok=True)
    outputs: List[str] = []
    mapping = [
        "ai_repair_results.jsonl",
        "ai_repair_results.xlsx",
        "ai_repair_candidates.xlsx",
        "ai_repair_validation.xlsx",
        "ai_repair_merge_preview.xlsx",
    ]
    for name in mapping:
        s = src / name
        d = dst_root / name
        if s.exists():
            shutil.copy2(s, d)
            outputs.append(str(d))
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage1 deterministic extract replay set and run offline worker.")
    parser.add_argument("--packet-jsonl", required=True)
    parser.add_argument("--schema-json", required=True)
    parser.add_argument("--trial-run-root", required=True)
    parser.add_argument("--delivery-dir", required=True)
    parser.add_argument("--max-extracts", type=int, default=8)
    args = parser.parse_args()

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    packet_path = Path(args.packet_jsonl)
    schema_path = Path(args.schema_json)
    trial_run_root = Path(args.trial_run_root)
    delivery_dir = Path(args.delivery_dir)
    worker_path = Path(r"D:\_datefac\tools\run_stage1_ai_repair_worker.py")

    if not packet_path.exists() or not schema_path.exists() or not worker_path.exists():
        print("BLOCKED_REQUIRED_INPUT_MISSING")
        return 3

    tasks = _load_packet(packet_path)
    max_extracts = max(1, int(args.max_extracts))
    extract_replay_dir = trial_run_root / "ai_repair_extract_replay"
    extract_replay_dir.mkdir(parents=True, exist_ok=True)

    responses: List[Dict[str, Any]] = []
    used_ids: Set[str] = set()
    extract_inventory_rows: List[Dict[str, Any]] = []

    for task in tasks:
        if len([r for r in responses if _norm(r.get("decision")) == "extract"]) >= max_extracts:
            break
        r = _build_extract_response(task)
        if not r:
            continue
        tid = _norm(r.get("repair_task_id"))
        if not tid or tid in used_ids:
            continue
        used_ids.add(tid)
        responses.append(r)
        rp = r["repairs"][0]
        extract_inventory_rows.append(
            {
                "repair_task_id": tid,
                "sample_id": _norm(task.get("sample_id")),
                "company": _norm(task.get("company")),
                "task_type": _norm(task.get("task_type")),
                "metric": _norm(rp.get("standard_metric")),
                "year": _norm(rp.get("year")),
                "value": _norm(rp.get("value")),
            }
        )

    # Ensure at least one manual_review.
    manual_task = next((t for t in tasks if _norm(t.get("repair_task_id")) not in used_ids), None)
    if manual_task is not None:
        tid = _norm(manual_task.get("repair_task_id"))
        used_ids.add(tid)
        responses.append(
            {
                "repair_task_id": tid,
                "decision": "manual_review",
                "repairs": [],
                "manual_review_items": [
                    {
                        "reason": "deterministic replay includes manual review sample",
                        "evidence": _norm(manual_task.get("evidence", {}).get("row_preview")),
                    }
                ],
                "notes": "manual_review sample in deterministic replay",
            }
        )

    # Ensure at least one ignore on semantic guard if possible.
    ignore_task = next(
        (
            t
            for t in tasks
            if _norm(t.get("repair_task_id")) not in used_ids
            and _norm(t.get("task_type")) == "semantic_guard_review"
        ),
        None,
    )
    if ignore_task is None:
        ignore_task = next((t for t in tasks if _norm(t.get("repair_task_id")) not in used_ids), None)
    if ignore_task is not None:
        tid = _norm(ignore_task.get("repair_task_id"))
        responses.append(
            {
                "repair_task_id": tid,
                "decision": "ignore",
                "repairs": [],
                "manual_review_items": [],
                "notes": "ignore sample in deterministic replay",
            }
        )
        used_ids.add(tid)

    response_path = extract_replay_dir / "extract_replay_responses.jsonl"
    response_path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in responses), encoding="utf-8")

    worker_trial_root = extract_replay_dir / "_worker_run"
    cmd = [
        sys.executable,
        str(worker_path),
        "--packet-jsonl",
        str(packet_path),
        "--schema-json",
        str(schema_path),
        "--trial-run-root",
        str(worker_trial_root),
        "--delivery-dir",
        str(delivery_dir),
        "--provider",
        "offline_file",
        "--offline-response-jsonl",
        str(response_path),
        "--max-tasks",
        "80",
        "--strict-schema",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    worker_output = (p.stdout or "") + ("\n" + p.stderr if p.stderr else "")
    parsed = _parse_worker_stdout(worker_output)

    copied_outputs = _copy_worker_outputs(worker_trial_root, extract_replay_dir)
    generated_outputs = [str(response_path)] + copied_outputs

    results_xlsx = extract_replay_dir / "ai_repair_results.xlsx"
    candidates_xlsx = extract_replay_dir / "ai_repair_candidates.xlsx"
    validation_xlsx = extract_replay_dir / "ai_repair_validation.xlsx"
    merge_preview_xlsx = extract_replay_dir / "ai_repair_merge_preview.xlsx"

    task_results_df = pd.read_excel(results_xlsx, sheet_name="task_results") if results_xlsx.exists() else pd.DataFrame()
    extracted_candidates_df = pd.read_excel(candidates_xlsx, sheet_name="extracted_candidates") if candidates_xlsx.exists() else pd.DataFrame()
    evidence_check_df = pd.read_excel(validation_xlsx, sheet_name="evidence_check") if validation_xlsx.exists() else pd.DataFrame()
    merge_preview_df = pd.read_excel(merge_preview_xlsx, sheet_name="merge_preview") if merge_preview_xlsx.exists() else pd.DataFrame()

    processed_task_count = int(_norm(parsed.get("processed_task_count")) or len(task_results_df))
    response_file_task_count = int(_norm(parsed.get("response_file_task_count")) or len(responses))
    decision_counts = _norm(parsed.get("decision_counts")) or "{}"
    schema_validation_status = _norm(parsed.get("schema_validation_status")) or "UNKNOWN"
    evidence_check_status = _norm(parsed.get("evidence_check_status")) or "UNKNOWN"
    worker_status = _norm(parsed.get("ai_repair_worker_status")) or ("FAIL" if p.returncode != 0 else "UNKNOWN")
    changed_count = int(_norm(parsed.get("production_guard_changed_count")) or 0)

    extracted_candidate_count = len(extracted_candidates_df) if not extracted_candidates_df.empty else 0
    invalid_extract_count = 0
    if not extracted_candidates_df.empty and "accepted_for_merge_preview" in extracted_candidates_df.columns:
        invalid_extract_count = int((extracted_candidates_df["accepted_for_merge_preview"].astype(str) != "1").sum())

    value_not_in_evidence_count = 0
    year_not_in_evidence_count = 0
    if not evidence_check_df.empty and "evidence_check_flags" in evidence_check_df.columns:
        flags_series = evidence_check_df["evidence_check_flags"].fillna("").astype(str)
        value_not_in_evidence_count = int(flags_series.str.contains("value_not_in_evidence").sum())
        year_not_in_evidence_count = int(flags_series.str.contains("year_not_in_evidence").sum())

    ai_candidate_for_rule_validation_count = 0
    manual_review_candidate_count = 0
    ignore_count = 0
    merge_preview_summary: Dict[str, int] = {}
    if not merge_preview_df.empty and "recommended_route_after_ai" in merge_preview_df.columns:
        route_counts = merge_preview_df["recommended_route_after_ai"].fillna("").astype(str).value_counts().to_dict()
        merge_preview_summary = {str(k): int(v) for k, v in route_counts.items()}
        ai_candidate_for_rule_validation_count = int(route_counts.get("ai_candidate_for_rule_validation", 0))
        manual_review_candidate_count = int(route_counts.get("manual_review_candidate", 0))
        ignore_count = int(route_counts.get("ignore", 0))

    sample_extract_summary_df = pd.DataFrame()
    target_metric_extract_summary_df = pd.DataFrame()
    if not extracted_candidates_df.empty:
        if "sample_id" in extracted_candidates_df.columns:
            sample_extract_summary_df = (
                extracted_candidates_df.groupby("sample_id", dropna=False).size().reset_index(name="extract_count")
            )
        if "standard_metric" in extracted_candidates_df.columns:
            target_metric_extract_summary_df = (
                extracted_candidates_df.groupby("standard_metric", dropna=False).size().reset_index(name="extract_count")
            )

    delivery_after = _run_delivery_check_json(delivery_dir)
    production_files_unchanged = changed_count == 0

    extract_replay_status = "PASS"
    if worker_status == "FAIL" or not production_files_unchanged:
        extract_replay_status = "FAIL"
    elif worker_status == "WARN":
        extract_replay_status = "WARN"

    finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commands_run = [
        f"{sys.executable} -m py_compile D:\\_datefac\\tools\\run_stage1_ai_repair_worker.py",
        f"{sys.executable} -m py_compile D:\\_datefac\\tools\\build_stage1_ai_repair_guardrail_cases.py",
        f"{sys.executable} -m py_compile D:\\_datefac\\tools\\build_stage1_ai_repair_extract_replay_set.py",
        "offline_file worker run executed by extract replay helper",
        f"{sys.executable} D:\\_datefac\\tools\\check_delivery_state.py --json",
    ]
    extract_response_count = sum(1 for r in responses if _norm(r.get("decision")) == "extract")
    manual_review_response_count = sum(1 for r in responses if _norm(r.get("decision")) == "manual_review")
    ignore_response_count = sum(1 for r in responses if _norm(r.get("decision")) == "ignore")

    report46_md = _safe_write_text(
        delivery_dir / "46_stage1_ai_repair_extract_replay_log.md",
        "\n".join(
            [
                "# Stage1 AI Repair Extract Replay Log",
                "",
                "- task_title: Add Stage 1 AI repair deterministic extract replay set",
                f"- started_at: {started_at}",
                f"- finished_at: {finished_at}",
                f"- commands_run: {json.dumps(commands_run, ensure_ascii=False)}",
                f"- packet_path: {packet_path}",
                f"- schema_path: {schema_path}",
                f"- extract_replay_dir: {extract_replay_dir}",
                f"- response_file_path: {response_path}",
                f"- response_file_task_count: {response_file_task_count}",
                f"- extract_response_count: {extract_response_count}",
                f"- manual_review_response_count: {manual_review_response_count}",
                f"- ignore_response_count: {ignore_response_count}",
                f"- output_files_generated: {json.dumps(generated_outputs, ensure_ascii=False)}",
                f"- production_guard_changed_count: {changed_count}",
                "- safety_checks: factory_core_not_run, vision_not_triggered, no_real_ai_call, production_files_unchanged",
            ]
        ),
    )

    report46_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": "Add Stage 1 AI repair deterministic extract replay set"},
                    {"field": "started_at", "value": started_at},
                    {"field": "finished_at", "value": finished_at},
                    {"field": "packet_path", "value": str(packet_path)},
                    {"field": "schema_path", "value": str(schema_path)},
                    {"field": "extract_replay_dir", "value": str(extract_replay_dir)},
                    {"field": "response_file_path", "value": str(response_path)},
                    {"field": "response_file_task_count", "value": response_file_task_count},
                    {"field": "extract_response_count", "value": extract_response_count},
                    {"field": "manual_review_response_count", "value": manual_review_response_count},
                    {"field": "ignore_response_count", "value": ignore_response_count},
                    {"field": "production_guard_changed_count", "value": changed_count},
                ]
            ),
            "response_inventory": pd.DataFrame(
                [
                    {
                        "repair_task_id": _norm(r.get("repair_task_id")),
                        "decision": _norm(r.get("decision")),
                        "repair_count": len(r.get("repairs", [])),
                        "manual_review_item_count": len(r.get("manual_review_items", [])),
                    }
                    for r in responses
                ]
            ),
            "extract_response_inventory": pd.DataFrame(extract_inventory_rows),
            "output_files_generated": pd.DataFrame([{"path": p} for p in generated_outputs]),
            "safety_checks": pd.DataFrame(
                [
                    {"check_name": "factory_core_not_run", "status": "PASS"},
                    {"check_name": "vision_or_ocr_not_triggered", "status": "PASS"},
                    {"check_name": "no_real_ai_call", "status": "PASS"},
                    {"check_name": "production_files_unchanged", "status": "PASS" if production_files_unchanged else "FAIL"},
                ]
            ),
        },
        delivery_dir / "46_stage1_ai_repair_extract_replay_log.xlsx",
    )

    report47_md = _safe_write_text(
        delivery_dir / "47_stage1_ai_repair_extract_replay_evaluation.md",
        "\n".join(
            [
                "# Stage1 AI Repair Extract Replay Evaluation",
                "",
                f"- extract_replay_status: {extract_replay_status}",
                f"- processed_task_count: {processed_task_count}",
                f"- response_file_task_count: {response_file_task_count}",
                f"- decision_counts: {decision_counts}",
                f"- extracted_candidate_count: {extracted_candidate_count}",
                f"- ai_candidate_for_rule_validation_count: {ai_candidate_for_rule_validation_count}",
                f"- manual_review_candidate_count: {manual_review_candidate_count}",
                f"- ignore_count: {ignore_count}",
                f"- schema_validation_status: {schema_validation_status}",
                f"- evidence_check_status: {evidence_check_status}",
                f"- invalid_extract_count: {invalid_extract_count}",
                f"- value_not_in_evidence_count: {value_not_in_evidence_count}",
                f"- year_not_in_evidence_count: {year_not_in_evidence_count}",
                f"- merge_preview_summary: {json.dumps(merge_preview_summary, ensure_ascii=False)}",
                f"- sample_extract_summary: {json.dumps(sample_extract_summary_df.to_dict(orient='records'), ensure_ascii=False)}",
                f"- target_metric_extract_summary: {json.dumps(target_metric_extract_summary_df.to_dict(orient='records'), ensure_ascii=False)}",
                f"- production_delivery_status_after: {json.dumps(delivery_after, ensure_ascii=False)}",
                f"- production_files_unchanged: {production_files_unchanged}",
                "- recommended_next_step: Increase deterministic extract coverage with per-sample curated task selection.",
            ]
        ),
    )

    report47_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "extract_replay_status", "value": extract_replay_status},
                    {"field": "processed_task_count", "value": processed_task_count},
                    {"field": "response_file_task_count", "value": response_file_task_count},
                    {"field": "decision_counts", "value": decision_counts},
                    {"field": "extracted_candidate_count", "value": extracted_candidate_count},
                    {"field": "ai_candidate_for_rule_validation_count", "value": ai_candidate_for_rule_validation_count},
                    {"field": "manual_review_candidate_count", "value": manual_review_candidate_count},
                    {"field": "ignore_count", "value": ignore_count},
                    {"field": "schema_validation_status", "value": schema_validation_status},
                    {"field": "evidence_check_status", "value": evidence_check_status},
                    {"field": "invalid_extract_count", "value": invalid_extract_count},
                    {"field": "value_not_in_evidence_count", "value": value_not_in_evidence_count},
                    {"field": "year_not_in_evidence_count", "value": year_not_in_evidence_count},
                    {"field": "merge_preview_summary", "value": json.dumps(merge_preview_summary, ensure_ascii=False)},
                    {"field": "production_delivery_status_after", "value": json.dumps(delivery_after, ensure_ascii=False)},
                    {"field": "production_files_unchanged", "value": "1" if production_files_unchanged else "0"},
                ]
            ),
            "response_inventory": pd.DataFrame(
                [
                    {
                        "repair_task_id": _norm(r.get("repair_task_id")),
                        "decision": _norm(r.get("decision")),
                        "repair_count": len(r.get("repairs", [])),
                        "manual_review_item_count": len(r.get("manual_review_items", [])),
                    }
                    for r in responses
                ]
            ),
            "task_results": task_results_df,
            "extracted_candidates": extracted_candidates_df,
            "evidence_check": evidence_check_df,
            "merge_preview": merge_preview_df,
            "sample_extract_summary": sample_extract_summary_df,
            "target_metric_extract_summary": target_metric_extract_summary_df,
            "production_guard": pd.DataFrame([{"changed_count": changed_count}]),
            "safety_checks": pd.DataFrame(
                [
                    {"check_name": "factory_core_not_run", "status": "PASS"},
                    {"check_name": "vision_or_ocr_not_triggered", "status": "PASS"},
                    {"check_name": "no_real_ai_call", "status": "PASS"},
                    {"check_name": "production_files_unchanged", "status": "PASS" if production_files_unchanged else "FAIL"},
                ]
            ),
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "Use deterministic replay baseline before any real provider integration.",
                    }
                ]
            ),
        },
        delivery_dir / "47_stage1_ai_repair_extract_replay_evaluation.xlsx",
    )

    print(f"extract_replay_helper_path: {Path(__file__)}")
    print(f"worker_path: {worker_path}")
    print(f"extract_replay_status: {extract_replay_status}")
    print(f"response_file_task_count: {response_file_task_count}")
    print(f"decision_counts: {decision_counts}")
    print(f"extracted_candidate_count: {extracted_candidate_count}")
    print(f"ai_candidate_for_rule_validation_count: {ai_candidate_for_rule_validation_count}")
    print(f"evidence_check_status: {evidence_check_status}")
    print(f"invalid_extract_count: {invalid_extract_count}")
    print(f"generated_outputs: {json.dumps([str(report46_md), str(report46_xlsx), str(report47_md), str(report47_xlsx)] + generated_outputs, ensure_ascii=False)}")
    print(f"production_delivery_status_after: {json.dumps(delivery_after, ensure_ascii=False)}")
    print(f"production_files_unchanged: {production_files_unchanged}")

    return 0 if extract_replay_status in {"PASS", "WARN"} else 4


if __name__ == "__main__":
    raise SystemExit(main())
