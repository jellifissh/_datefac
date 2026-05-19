import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


PRODUCTION_PREFIX_PATTERNS = ["01_*.xlsx", "02_*.xlsx", "02A_*.xlsx", "06_*.xlsx"]
DECISIONS = {"extract", "manual_review", "ignore", "non_target"}
HARD_RISK_FLAGS = {
    "source_row_semantic_risk",
    "forbidden_source_label_for_metric",
    "broad_keyword_unsafe",
    "multi_metric_row_ambiguous",
    "ambiguous_year_value_alignment",
    "ambiguous_multi_numeric_cell",
    "duplicate_metric_year_non_preferred",
}
NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


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


def _load_packet(packet_jsonl: Path, max_tasks: int) -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    for line in packet_jsonl.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        tasks.append(obj)
        if len(tasks) >= max_tasks:
            break
    return tasks


def _evidence_text(task: Dict[str, object]) -> str:
    evidence = task.get("evidence", {}) or {}
    parts: List[str] = []
    for key in ["row_preview", "table_header_context", "raw_table_preview"]:
        val = evidence.get(key, "")
        if isinstance(val, list):
            parts.append(json.dumps(val, ensure_ascii=False))
        else:
            parts.append(_norm(val))
    row_cells = evidence.get("row_cells", [])
    if isinstance(row_cells, list):
        parts.append("|".join([_norm(x) for x in row_cells]))
    return "\n".join([p for p in parts if p])


def _offline_mock_decision(task: Dict[str, object]) -> Dict[str, object]:
    tid = _norm(task.get("repair_task_id"))
    task_type = _norm(task.get("task_type"))
    rule = task.get("current_rule_result", {}) or {}
    flags = set(rule.get("flags", []) if isinstance(rule.get("flags"), list) else [])
    source = task.get("source", {}) or {}

    decision = "manual_review"
    repairs: List[Dict[str, object]] = []
    manual_items: List[Dict[str, object]] = []
    notes = ""

    if task_type == "s2_table_level_repair":
        decision = "manual_review"
        manual_items.append(
            {
                "reason": "no metric labels detected by rule packet; requires AI/model or human visual review",
                "evidence": _norm(task.get("evidence", {}).get("row_preview")),
            }
        )
        notes = "S2 table-level conservative manual review in offline mock mode."
    elif task_type == "semantic_guard_review":
        decision = "manual_review"
        manual_items.append(
            {
                "reason": "demoted by semantic guard flags; offline mock does not override guarded decisions",
                "evidence": "|".join(sorted(flags)) or "no_flags",
            }
        )
        notes = "Conservative semantic guard review."
    elif task_type in {"metric_year_value_alignment", "row_segment_repair"}:
        if flags & HARD_RISK_FLAGS:
            decision = "manual_review"
            manual_items.append(
                {
                    "reason": "hard risk flag present, no auto extraction",
                    "evidence": "|".join(sorted(flags)),
                }
            )
            notes = "Hard-risk preserved."
        else:
            decision = "manual_review"
            manual_items.append(
                {
                    "reason": "offline mock does not perform complex segmentation/alignment extraction",
                    "evidence": _norm(task.get("evidence", {}).get("row_preview")),
                }
            )
            notes = "Conservative fallback."
    else:
        decision = "manual_review"
        manual_items.append(
            {
                "reason": "unknown task type in offline mock mode",
                "evidence": task_type,
            }
        )
        notes = "Unknown task type."

    if decision == "extract" and not repairs:
        decision = "manual_review"
        manual_items.append(
            {
                "reason": "extract decision downgraded because no repair items generated",
                "evidence": tid,
            }
        )
        notes = "Downgraded to manual review."

    if decision == "manual_review" and not manual_items:
        manual_items.append({"reason": "manual review required", "evidence": "default"})

    result = {
        "repair_task_id": tid,
        "decision": decision,
        "repairs": repairs,
        "manual_review_items": manual_items,
        "notes": notes,
        "_task_type": task_type,
        "_sample_id": _norm(task.get("sample_id")),
        "_company": _norm(task.get("company")),
        "_source_trace_id": _norm(source.get("source_trace_id")),
        "_standard_metric_hint": _norm(task.get("current_rule_result", {}).get("standard_metric_hint")),
        "_source_page": int(source.get("source_page") or 0),
        "_source_table_index": int(source.get("source_table_index") or 0),
        "_source_row_index": int(source.get("source_row_index") or 0),
        "_table_role": _norm(source.get("table_role")),
        "_validation_flags": [],
    }
    return result


def _validate_result_schema(result: Dict[str, object]) -> List[str]:
    errs: List[str] = []
    if not _norm(result.get("repair_task_id")):
        errs.append("missing_repair_task_id")
    decision = _norm(result.get("decision"))
    if decision not in DECISIONS:
        errs.append("invalid_decision")
    if not isinstance(result.get("repairs"), list):
        errs.append("repairs_not_list")
    if not isinstance(result.get("manual_review_items"), list):
        errs.append("manual_review_items_not_list")
    if decision == "extract" and len(result.get("repairs", [])) == 0:
        errs.append("extract_without_repairs")
    if decision == "manual_review" and len(result.get("manual_review_items", [])) == 0:
        errs.append("manual_review_without_items")
    return errs


def _check_extract_values_in_evidence(task: Dict[str, object], result: Dict[str, object]) -> List[str]:
    errs: List[str] = []
    if _norm(result.get("decision")) != "extract":
        return errs
    txt = _evidence_text(task)
    for rp in result.get("repairs", []):
        val = rp.get("value")
        sval = _norm(val)
        if not sval:
            continue
        if sval not in txt:
            errs.append(f"value_not_in_evidence:{sval}")
    return errs


def _write_jsonl(path: Path, rows: List[Dict[str, object]]) -> Path:
    payload_lines = []
    for r in rows:
        obj = {k: r[k] for k in ["repair_task_id", "decision", "repairs", "manual_review_items", "notes"]}
        payload_lines.append(json.dumps(obj, ensure_ascii=False))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(payload_lines), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Sandbox Stage 1 AI repair worker MVP (offline only).")
    parser.add_argument("--packet-jsonl", type=str, required=True)
    parser.add_argument("--schema-json", type=str, required=True)
    parser.add_argument("--trial-run-root", type=str, required=True)
    parser.add_argument("--delivery-dir", type=str, required=True)
    parser.add_argument("--provider", type=str, default="offline_mock")
    parser.add_argument("--max-tasks", type=int, default=80)
    parser.add_argument("--offline-response-jsonl", type=str, default="")
    parser.add_argument("--strict-schema", action="store_true")
    parser.add_argument("--no-production-write", action="store_true", default=True)
    args = parser.parse_args()

    if args.provider not in {"offline_mock", "offline_file"}:
        print("BLOCKED_PROVIDER_NOT_ALLOWED")
        return 3
    if args.provider != "offline_mock" and args.provider != "offline_file":
        print("BLOCKED_PROVIDER_NOT_ALLOWED")
        return 3
    if args.provider == "offline_file" and not _norm(args.offline_response_jsonl):
        print("BLOCKED_OFFLINE_FILE_REQUIRES_RESPONSE_JSONL")
        return 3

    packet_jsonl = Path(args.packet_jsonl)
    schema_json = Path(args.schema_json)
    trial_run_root = Path(args.trial_run_root)
    delivery_dir = Path(args.delivery_dir)
    ai_trial_dir = trial_run_root / "ai_repair_trial"

    if not packet_jsonl.exists() or not schema_json.exists():
        print("BLOCKED_REQUIRED_INPUT_MISSING")
        return 3

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    before = _snapshot_files(_collect_production_guard_files(delivery_dir))

    schema_payload = json.loads(schema_json.read_text(encoding="utf-8"))
    tasks = _load_packet(packet_jsonl, max(1, int(args.max_tasks)))
    task_map = {_norm(t.get("repair_task_id")): t for t in tasks}
    results: List[Dict[str, object]] = []

    if args.provider == "offline_file":
        resp_path = Path(args.offline_response_jsonl)
        if not resp_path.exists():
            print("BLOCKED_OFFLINE_RESPONSE_FILE_MISSING")
            return 3
        for line in resp_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            obj.setdefault("repairs", [])
            obj.setdefault("manual_review_items", [])
            obj.setdefault("notes", "")
            tid = _norm(obj.get("repair_task_id"))
            t = task_map.get(tid, {})
            obj["_task_type"] = _norm(t.get("task_type"))
            obj["_sample_id"] = _norm(t.get("sample_id"))
            obj["_company"] = _norm(t.get("company"))
            src = t.get("source", {}) if isinstance(t.get("source"), dict) else {}
            obj["_source_trace_id"] = _norm(src.get("source_trace_id"))
            obj["_standard_metric_hint"] = _norm(t.get("current_rule_result", {}).get("standard_metric_hint"))
            obj["_source_page"] = int(src.get("source_page") or 0)
            obj["_source_table_index"] = int(src.get("source_table_index") or 0)
            obj["_source_row_index"] = int(src.get("source_row_index") or 0)
            obj["_table_role"] = _norm(src.get("table_role"))
            obj["_validation_flags"] = []
            results.append(obj)
    else:
        for task in tasks:
            results.append(_offline_mock_decision(task))

    schema_validation_rows: List[Dict[str, object]] = []
    all_flags: List[str] = []
    seen_task_ids = set()
    duplicate_result_ids = set()
    unknown_task_ids = set()
    extract_evidence_err_count = 0

    for r in results:
        tid = _norm(r.get("repair_task_id"))
        if tid in seen_task_ids:
            duplicate_result_ids.add(tid)
        seen_task_ids.add(tid)
        if tid not in task_map:
            unknown_task_ids.add(tid)

        errs = _validate_result_schema(r)
        evidence_errs = _check_extract_values_in_evidence(task_map.get(tid, {}), r)
        if evidence_errs:
            extract_evidence_err_count += 1
        errs.extend(evidence_errs)
        r["_validation_flags"] = errs
        all_flags.extend(errs)
        schema_validation_rows.append(
            {
                "repair_task_id": tid,
                "decision": _norm(r.get("decision")),
                "schema_errors": "|".join(errs),
                "schema_valid": "1" if not errs else "0",
            }
        )

    missing_result_task_ids = sorted([tid for tid in task_map.keys() if tid not in seen_task_ids])
    processed_task_count = len(results)
    decision_counts: Dict[str, int] = {}
    for r in results:
        d = _norm(r.get("decision"))
        decision_counts[d] = decision_counts.get(d, 0) + 1

    extracted_candidates_rows: List[Dict[str, object]] = []
    manual_review_items_rows: List[Dict[str, object]] = []
    task_results_rows: List[Dict[str, object]] = []
    merge_preview_rows: List[Dict[str, object]] = []

    for r in results:
        tid = _norm(r.get("repair_task_id"))
        decision = _norm(r.get("decision"))
        sample_id = _norm(r.get("_sample_id"))
        company = _norm(r.get("_company"))
        source_trace_id = _norm(r.get("_source_trace_id"))
        val_flags = "|".join(r.get("_validation_flags", []))
        task_results_rows.append(
            {
                "repair_task_id": tid,
                "task_type": _norm(r.get("_task_type")),
                "sample_id": sample_id,
                "company": company,
                "source_trace_id": source_trace_id,
                "decision": decision,
                "repair_count": len(r.get("repairs", [])),
                "manual_review_item_count": len(r.get("manual_review_items", [])),
                "validation_flags": val_flags,
                "notes": _norm(r.get("notes")),
            }
        )

        if decision == "extract":
            for rp in r.get("repairs", []):
                extracted_candidates_rows.append(
                    {
                        "repair_task_id": tid,
                        "sample_id": sample_id,
                        "company": company,
                        "source_trace_id": source_trace_id,
                        "standard_metric": _norm(rp.get("standard_metric")),
                        "year": _norm(rp.get("year")),
                        "value": rp.get("value"),
                        "unit": _norm(rp.get("unit")),
                        "confidence": _norm(rp.get("confidence")),
                        "evidence": _norm(rp.get("evidence")),
                        "source_cell_or_segment": _norm(rp.get("source_cell_or_segment")),
                        "flags": "|".join(rp.get("flags", []) if isinstance(rp.get("flags"), list) else []),
                    }
                )

        if decision == "manual_review":
            for mi in r.get("manual_review_items", []):
                manual_review_items_rows.append(
                    {
                        "repair_task_id": tid,
                        "sample_id": sample_id,
                        "company": company,
                        "source_trace_id": source_trace_id,
                        "reason": _norm(mi.get("reason")),
                        "evidence": _norm(mi.get("evidence")),
                    }
                )

        route_after = "manual_review_candidate"
        if decision == "extract":
            route_after = "ai_candidate_for_rule_validation"
        elif decision == "ignore":
            route_after = "ignore"
        elif decision == "non_target":
            route_after = "non_target"

        if decision == "extract" and r.get("repairs"):
            for rp in r.get("repairs", []):
                merge_preview_rows.append(
                    {
                        "repair_task_id": tid,
                        "sample_id": sample_id,
                        "company": company,
                        "source_trace_id": source_trace_id,
                        "decision": decision,
                        "standard_metric": _norm(rp.get("standard_metric")),
                        "year": _norm(rp.get("year")),
                        "value": rp.get("value"),
                        "unit": _norm(rp.get("unit")),
                        "evidence": _norm(rp.get("evidence")),
                        "validation_flags": val_flags,
                        "recommended_route_after_ai": route_after,
                    }
                )
        else:
            merge_preview_rows.append(
                {
                    "repair_task_id": tid,
                    "sample_id": sample_id,
                    "company": company,
                    "source_trace_id": source_trace_id,
                    "decision": decision,
                    "standard_metric": _norm(r.get("_standard_metric_hint")),
                    "year": "",
                    "value": "",
                    "unit": "",
                    "evidence": _norm(r.get("notes")),
                    "validation_flags": val_flags,
                    "recommended_route_after_ai": route_after,
                }
            )

    ai_trial_dir.mkdir(parents=True, exist_ok=True)
    out_results_jsonl = _write_jsonl(ai_trial_dir / "ai_repair_results.jsonl", results)
    out_results_xlsx = _safe_write_excel({"task_results": pd.DataFrame(task_results_rows)}, ai_trial_dir / "ai_repair_results.xlsx")
    out_candidates_xlsx = _safe_write_excel({"extracted_candidates": pd.DataFrame(extracted_candidates_rows)}, ai_trial_dir / "ai_repair_candidates.xlsx")
    out_validation_xlsx = _safe_write_excel(
        {
            "schema_validation": pd.DataFrame(schema_validation_rows),
            "duplicates": pd.DataFrame([{"repair_task_id": x} for x in sorted(duplicate_result_ids)]),
            "unknown_task_ids": pd.DataFrame([{"repair_task_id": x} for x in sorted(unknown_task_ids)]),
            "missing_result_task_ids": pd.DataFrame([{"repair_task_id": x} for x in missing_result_task_ids]),
        },
        ai_trial_dir / "ai_repair_validation.xlsx",
    )
    out_merge_preview_xlsx = _safe_write_excel({"merge_preview": pd.DataFrame(merge_preview_rows)}, ai_trial_dir / "ai_repair_merge_preview.xlsx")

    schema_validation_status = "PASS"
    if duplicate_result_ids or unknown_task_ids or missing_result_task_ids or all_flags:
        schema_validation_status = "WARN"
    extraction_value_evidence_check_status = "PASS" if extract_evidence_err_count == 0 else "WARN"

    after = _snapshot_files(_collect_production_guard_files(delivery_dir))
    production_guard_rows = _compare_snapshot(before, after)
    changed_count = sum(1 for r in production_guard_rows if r.get("changed") == "1")
    production_status_after = _run_delivery_check_json(delivery_dir)

    extracted_candidate_count = decision_counts.get("extract", 0)
    manual_review_count = decision_counts.get("manual_review", 0)
    ignored_count = decision_counts.get("ignore", 0)
    non_target_count = decision_counts.get("non_target", 0)

    if changed_count > 0:
        ai_status = "FAIL"
    elif schema_validation_status == "PASS":
        ai_status = "PASS"
    else:
        ai_status = "WARN"

    task_type_decision_map: Dict[Tuple[str, str], int] = {}
    sample_decision_map: Dict[Tuple[str, str], int] = {}
    for r in results:
        task_type = _norm(r.get("_task_type"))
        decision = _norm(r.get("decision"))
        sample_id = _norm(r.get("_sample_id"))
        task_type_decision_map[(task_type, decision)] = task_type_decision_map.get((task_type, decision), 0) + 1
        sample_decision_map[(sample_id, decision)] = sample_decision_map.get((sample_id, decision), 0) + 1
    task_type_decision_summary = [{"task_type": k[0], "decision": k[1], "count": v} for k, v in sorted(task_type_decision_map.items())]
    sample_decision_summary = [{"sample_id": k[0], "decision": k[1], "count": v} for k, v in sorted(sample_decision_map.items())]

    merge_preview_summary = {
        "ai_candidate_for_rule_validation": sum(1 for r in merge_preview_rows if _norm(r.get("recommended_route_after_ai")) == "ai_candidate_for_rule_validation"),
        "manual_review_candidate": sum(1 for r in merge_preview_rows if _norm(r.get("recommended_route_after_ai")) == "manual_review_candidate"),
        "ignore": sum(1 for r in merge_preview_rows if _norm(r.get("recommended_route_after_ai")) == "ignore"),
        "non_target": sum(1 for r in merge_preview_rows if _norm(r.get("recommended_route_after_ai")) == "non_target"),
    }

    safety_checks = [
        {"check_name": "factory_core_not_run", "status": "PASS", "detail": "sandbox worker only"},
        {"check_name": "vision_or_ocr_not_triggered", "status": "PASS", "detail": "no vision/OCR/model import"},
        {"check_name": "no_real_ai_call", "status": "PASS", "detail": f"provider={args.provider}, offline path only"},
        {"check_name": "production_files_unchanged", "status": "PASS" if changed_count == 0 else "FAIL", "detail": f"changed={changed_count}"},
    ]

    finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    command_run = " ".join([sys.executable, str(Path(__file__))] + sys.argv[1:])
    generated_outputs = [
        str(out_results_jsonl),
        str(out_results_xlsx),
        str(out_candidates_xlsx),
        str(out_validation_xlsx),
        str(out_merge_preview_xlsx),
    ]

    report40_md = _safe_write_text(
        delivery_dir / "40_stage1_ai_repair_worker_log.md",
        "\n".join(
            [
                "# Stage1 AI Repair Worker Log",
                "",
                "- task_title: Implement Stage 1 sandbox AI repair worker MVP",
                f"- started_at: {started_at}",
                f"- finished_at: {finished_at}",
                f"- command_run: {command_run}",
                f"- provider: {args.provider}",
                f"- packet_path: {packet_jsonl}",
                f"- schema_path: {schema_json}",
                f"- trial_run_root: {trial_run_root}",
                f"- processed_task_count: {processed_task_count}",
                f"- decision_counts: {json.dumps(decision_counts, ensure_ascii=False)}",
                f"- validation_status: {schema_validation_status}",
                f"- output_files_generated: {json.dumps(generated_outputs, ensure_ascii=False)}",
                f"- production_guard_changed_count: {changed_count}",
            ]
        ),
    )

    report40_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": "Implement Stage 1 sandbox AI repair worker MVP"},
                    {"field": "started_at", "value": started_at},
                    {"field": "finished_at", "value": finished_at},
                    {"field": "command_run", "value": command_run},
                    {"field": "provider", "value": args.provider},
                    {"field": "packet_path", "value": str(packet_jsonl)},
                    {"field": "schema_path", "value": str(schema_json)},
                    {"field": "trial_run_root", "value": str(trial_run_root)},
                    {"field": "processed_task_count", "value": processed_task_count},
                    {"field": "decision_counts", "value": json.dumps(decision_counts, ensure_ascii=False)},
                    {"field": "validation_status", "value": schema_validation_status},
                    {"field": "production_guard_changed_count", "value": changed_count},
                ]
            ),
            "output_files_generated": pd.DataFrame([{"path": p} for p in generated_outputs]),
            "safety_checks": pd.DataFrame(safety_checks),
            "production_guard": pd.DataFrame(production_guard_rows),
        },
        delivery_dir / "40_stage1_ai_repair_worker_log.xlsx",
    )

    report41_md = _safe_write_text(
        delivery_dir / "41_stage1_ai_repair_worker_evaluation.md",
        "\n".join(
            [
                "# Stage1 AI Repair Worker Evaluation",
                "",
                f"- ai_repair_worker_status: {ai_status}",
                f"- provider: {args.provider}",
                f"- task_count: {processed_task_count}",
                f"- decision_counts: {json.dumps(decision_counts, ensure_ascii=False)}",
                f"- extracted_candidate_count: {extracted_candidate_count}",
                f"- manual_review_count: {manual_review_count}",
                f"- ignored_count: {ignored_count}",
                f"- non_target_count: {non_target_count}",
                f"- schema_validation_status: {schema_validation_status}",
                f"- extraction_value_evidence_check_status: {extraction_value_evidence_check_status}",
                f"- merge_preview_summary: {json.dumps(merge_preview_summary, ensure_ascii=False)}",
                f"- production_delivery_status_after: {json.dumps(production_status_after, ensure_ascii=False)}",
                f"- production_files_unchanged: {changed_count == 0}",
            ]
        ),
    )

    report41_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "ai_repair_worker_status", "value": ai_status},
                    {"field": "provider", "value": args.provider},
                    {"field": "task_count", "value": processed_task_count},
                    {"field": "decision_counts", "value": json.dumps(decision_counts, ensure_ascii=False)},
                    {"field": "extracted_candidate_count", "value": extracted_candidate_count},
                    {"field": "manual_review_count", "value": manual_review_count},
                    {"field": "ignored_count", "value": ignored_count},
                    {"field": "non_target_count", "value": non_target_count},
                    {"field": "schema_validation_status", "value": schema_validation_status},
                    {"field": "extraction_value_evidence_check_status", "value": extraction_value_evidence_check_status},
                    {"field": "production_delivery_status_after", "value": json.dumps(production_status_after, ensure_ascii=False)},
                    {"field": "production_files_unchanged", "value": "1" if changed_count == 0 else "0"},
                ]
            ),
            "decision_summary": pd.DataFrame([{"decision": k, "count": v} for k, v in sorted(decision_counts.items())]),
            "task_results": pd.DataFrame(task_results_rows),
            "extracted_candidates": pd.DataFrame(extracted_candidates_rows),
            "manual_review_items": pd.DataFrame(manual_review_items_rows),
            "schema_validation": pd.DataFrame(schema_validation_rows),
            "merge_preview": pd.DataFrame(merge_preview_rows),
            "sample_decision_summary": pd.DataFrame(sample_decision_summary),
            "task_type_decision_summary": pd.DataFrame(task_type_decision_summary),
            "merge_preview_summary": pd.DataFrame([merge_preview_summary]),
            "production_guard": pd.DataFrame(production_guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "Connect a real provider in a later task while preserving schema validation and no-production-write safeguards.",
                    }
                ]
            ),
        },
        delivery_dir / "41_stage1_ai_repair_worker_evaluation.xlsx",
    )

    print(f"worker_path: {Path(__file__)}")
    print(f"provider: {args.provider}")
    print(f"processed_task_count: {processed_task_count}")
    print(f"ai_repair_worker_status: {ai_status}")
    print(f"decision_counts: {json.dumps(decision_counts, ensure_ascii=False)}")
    print(f"schema_validation_status: {schema_validation_status}")
    print(f"generated_outputs: {json.dumps([str(report40_md), str(report40_xlsx), str(report41_md), str(report41_xlsx)] + generated_outputs, ensure_ascii=False)}")
    print(f"production_delivery_status_after: {json.dumps(production_status_after, ensure_ascii=False)}")
    print(f"production_guard_changed_count: {changed_count}")

    if changed_count > 0:
        return 5
    return 0 if ai_status in {"PASS", "WARN"} else 4


if __name__ == "__main__":
    raise SystemExit(main())
