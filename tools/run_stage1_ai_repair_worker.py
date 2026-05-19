import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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
NUM_RE = re.compile(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?")
YEAR_RE = re.compile(r"(20\d{2}(?:[AE])?)")


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


def _load_packet(packet_jsonl: Path, max_tasks: int) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    for line in packet_jsonl.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        tasks.append(obj)
        if len(tasks) >= max_tasks:
            break
    return tasks


def _evidence_text(task: Dict[str, Any]) -> str:
    evidence = task.get("evidence", {}) or {}
    parts: List[str] = []
    for key in ["row_preview", "table_header_context", "nearby_rows_context", "raw_table_preview"]:
        val = evidence.get(key, "")
        if isinstance(val, list):
            parts.append(json.dumps(val, ensure_ascii=False))
        else:
            parts.append(_norm(val))
    row_cells = evidence.get("row_cells", [])
    if isinstance(row_cells, list):
        parts.append("|".join([_norm(x) for x in row_cells]))
    return "\n".join([p for p in parts if p])


def _normalize_number_text(v: Any) -> str:
    s = _norm(v).replace(",", "")
    if not s:
        return ""
    s = s.replace("（", "(").replace("）", ")")
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.strip()
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", s):
        return ""
    try:
        n = float(s)
        if neg:
            n = -n
        out = f"{n:.12f}".rstrip("0").rstrip(".")
        return out if out else "0"
    except Exception:
        return ""


def _collect_evidence_numbers(text: str) -> Set[str]:
    values: Set[str] = set()
    for m in NUM_RE.findall(text or ""):
        n = _normalize_number_text(m)
        if n:
            values.add(n)
    return values


def _value_in_evidence(value: Any, evidence_text: str, evidence_numbers: Set[str]) -> bool:
    raw = _norm(value)
    if raw and raw in evidence_text:
        return True
    nv = _normalize_number_text(value)
    if nv and nv in evidence_numbers:
        return True
    return False


def _year_in_evidence(year: str, detected_years: List[str], evidence_text: str) -> bool:
    y = _norm(year)
    if not y:
        return False
    if y in [_norm(x) for x in detected_years]:
        return True
    return y in evidence_text


def _metric_allowed_or_in_evidence(metric: str, evidence_text: str) -> bool:
    m = _norm(metric)
    if not m:
        return False
    if m in TARGET_METRICS:
        return True
    return m in evidence_text


def _validate_result_schema_basic(result: Dict[str, Any]) -> List[str]:
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


def _validate_result_against_schema_payload(result: Dict[str, Any], schema_payload: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    required = schema_payload.get("required", [])
    for key in required:
        if key not in result:
            errs.append(f"schema_missing_field:{key}")
    allow_extra = not (schema_payload.get("additionalProperties") is False)
    if not allow_extra:
        allowed_keys = set(schema_payload.get("properties", {}).keys())
        extras = [k for k in result.keys() if not str(k).startswith("_") and k not in allowed_keys]
        if extras:
            errs.append(f"schema_additional_properties:{'|'.join(sorted([str(x) for x in extras]))}")

    repairs = result.get("repairs", [])
    if isinstance(repairs, list):
        item_required = (
            schema_payload.get("properties", {})
            .get("repairs", {})
            .get("items", {})
            .get("required", [])
        )
        for i, rp in enumerate(repairs):
            if not isinstance(rp, dict):
                errs.append(f"schema_repair_not_object:{i}")
                continue
            for k in item_required:
                if k not in rp:
                    errs.append(f"schema_repair_missing:{i}:{k}")
    return errs


def _check_extract_evidence(task: Dict[str, Any], result: Dict[str, Any]) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    decision = _norm(result.get("decision"))
    if decision != "extract":
        return "PASS", [], []

    evidence = task.get("evidence", {}) or {}
    evidence_txt = _evidence_text(task)
    evidence_numbers = _collect_evidence_numbers(evidence_txt)
    detected_years = evidence.get("detected_years", []) if isinstance(evidence.get("detected_years"), list) else []

    flags: List[str] = []
    rows: List[Dict[str, Any]] = []
    for rp in result.get("repairs", []):
        metric = _norm(rp.get("standard_metric"))
        year = _norm(rp.get("year"))
        value = rp.get("value")

        row_flags: List[str] = []
        if not _value_in_evidence(value, evidence_txt, evidence_numbers):
            row_flags.append(f"value_not_in_evidence:{_norm(value)}")
        if not _year_in_evidence(year, detected_years, evidence_txt):
            row_flags.append(f"year_not_in_evidence:{year}")
        if not _metric_allowed_or_in_evidence(metric, evidence_txt):
            row_flags.append(f"metric_not_allowed_or_not_in_evidence:{metric}")

        flags.extend(row_flags)
        rows.append(
            {
                "repair_task_id": _norm(result.get("repair_task_id")),
                "standard_metric": metric,
                "year": year,
                "value": value,
                "evidence_check_flags": "|".join(row_flags),
                "evidence_check_status": "PASS" if not row_flags else "FAIL",
            }
        )
    status = "PASS" if not flags else "FAIL"
    return status, flags, rows


def _with_task_meta(result: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
    source = task.get("source", {}) if isinstance(task.get("source"), dict) else {}
    out = dict(result)
    if not isinstance(out.get("repairs"), list):
        out["repairs"] = [] if out.get("repairs") is None else out.get("repairs")
        if not isinstance(out["repairs"], list):
            out["repairs"] = []
    if not isinstance(out.get("manual_review_items"), list):
        out["manual_review_items"] = [] if out.get("manual_review_items") is None else out.get("manual_review_items")
        if not isinstance(out["manual_review_items"], list):
            out["manual_review_items"] = []
    if "decision" not in out:
        out["decision"] = ""
    out.setdefault("notes", "")
    out["_task_type"] = _norm(task.get("task_type"))
    out["_sample_id"] = _norm(task.get("sample_id"))
    out["_company"] = _norm(task.get("company"))
    out["_source_trace_id"] = _norm(source.get("source_trace_id"))
    out["_standard_metric_hint"] = _norm(task.get("current_rule_result", {}).get("standard_metric_hint"))
    out["_source_page"] = int(source.get("source_page") or 0)
    out["_source_table_index"] = int(source.get("source_table_index") or 0)
    out["_source_row_index"] = int(source.get("source_row_index") or 0)
    out["_table_role"] = _norm(source.get("table_role"))
    out["_validation_flags"] = list(out.get("_validation_flags", []))
    out["_evidence_check_status"] = _norm(out.get("_evidence_check_status")) or "PASS"
    out["_extract_valid"] = bool(out.get("_extract_valid", False))
    return out


def _offline_manual_review_missing(task: Dict[str, Any]) -> Dict[str, Any]:
    tid = _norm(task.get("repair_task_id"))
    return {
        "repair_task_id": tid,
        "decision": "manual_review",
        "repairs": [],
        "manual_review_items": [
            {
                "reason": "offline response missing for task; safe fallback to manual review",
                "evidence": _norm(task.get("evidence", {}).get("row_preview")),
            }
        ],
        "notes": "offline_file fallback because response line missing",
        "_validation_flags": ["offline_response_missing"],
    }


def _offline_mock_decision(task: Dict[str, Any]) -> Dict[str, Any]:
    tid = _norm(task.get("repair_task_id"))
    task_type = _norm(task.get("task_type"))
    rule = task.get("current_rule_result", {}) or {}
    flags = set(rule.get("flags", []) if isinstance(rule.get("flags"), list) else [])

    decision = "manual_review"
    repairs: List[Dict[str, Any]] = []
    manual_items: List[Dict[str, Any]] = []
    notes = ""

    if task_type == "s2_table_level_repair":
        manual_items.append(
            {
                "reason": "no metric labels detected by rule packet; requires AI/model or human visual review",
                "evidence": _norm(task.get("evidence", {}).get("row_preview")),
            }
        )
        notes = "S2 table-level conservative manual review in offline mock mode."
    elif task_type == "semantic_guard_review":
        manual_items.append(
            {
                "reason": "demoted by semantic guard flags; offline mock does not override guarded decisions",
                "evidence": "|".join(sorted(flags)) or "no_flags",
            }
        )
        notes = "Conservative semantic guard review."
    elif flags & HARD_RISK_FLAGS:
        manual_items.append(
            {
                "reason": "hard risk flag present, no auto extraction",
                "evidence": "|".join(sorted(flags)),
            }
        )
        notes = "Hard-risk preserved."
    else:
        manual_items.append(
            {
                "reason": "offline mock does not perform complex segmentation/alignment extraction",
                "evidence": _norm(task.get("evidence", {}).get("row_preview")),
            }
        )
        notes = "Conservative fallback."

    return {
        "repair_task_id": tid,
        "decision": decision,
        "repairs": repairs,
        "manual_review_items": manual_items,
        "notes": notes,
        "_validation_flags": [],
    }


def _extract_years_for_candidate(task: Dict[str, Any]) -> List[str]:
    evidence = task.get("evidence", {}) or {}
    years = [_norm(x) for x in evidence.get("detected_years", []) if _norm(x)]
    if years:
        return years
    txt = _evidence_text(task)
    found = YEAR_RE.findall(txt)
    uniq: List[str] = []
    for y in found:
        if y not in uniq:
            uniq.append(y)
    return uniq


def _try_build_safe_extract_response(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rule = task.get("current_rule_result", {}) or {}
    flags = set(rule.get("flags", []) if isinstance(rule.get("flags"), list) else [])
    if flags & HARD_RISK_FLAGS:
        return None

    metric = _norm(rule.get("standard_metric_hint"))
    if not metric or not _metric_allowed_or_in_evidence(metric, _evidence_text(task)):
        return None

    row_cells = task.get("evidence", {}).get("row_cells", [])
    row_values: List[str] = []
    if isinstance(row_cells, list):
        row_values = [_norm(x) for x in row_cells if _norm(x)]
    num_candidates = [x for x in row_values if _normalize_number_text(x)]
    years = _extract_years_for_candidate(task)
    if not years or not num_candidates:
        return None

    year = years[0]
    value_raw = num_candidates[0]
    evidence = _evidence_text(task)
    if not _value_in_evidence(value_raw, evidence, _collect_evidence_numbers(evidence)):
        return None
    if not _year_in_evidence(year, years, evidence):
        return None

    return {
        "repair_task_id": _norm(task.get("repair_task_id")),
        "decision": "extract",
        "repairs": [
            {
                "standard_metric": metric,
                "year": year,
                "value": value_raw,
                "unit": "",
                "confidence": "low",
                "evidence": _norm(task.get("evidence", {}).get("row_preview")),
                "source_cell_or_segment": _norm(task.get("source", {}).get("source_trace_id")),
                "flags": ["offline_file_replay_sample"],
            }
        ],
        "manual_review_items": [],
        "notes": "offline replay sample extract copied from packet evidence",
    }


def _build_sample_offline_response(tasks: List[Dict[str, Any]], path: Path) -> Dict[str, Any]:
    sample_rows: List[Dict[str, Any]] = []
    used: Set[str] = set()

    s2_task = next((t for t in tasks if _norm(t.get("task_type")) == "s2_table_level_repair"), None)
    if s2_task:
        tid = _norm(s2_task.get("repair_task_id"))
        used.add(tid)
        sample_rows.append(
            {
                "repair_task_id": tid,
                "decision": "manual_review",
                "repairs": [],
                "manual_review_items": [
                    {
                        "reason": "S2 table-level repair requires manual/AI semantic reconstruction",
                        "evidence": _norm(s2_task.get("evidence", {}).get("row_preview")),
                    }
                ],
                "notes": "sample offline replay manual_review for S2",
            }
        )

    unsafe_task = next(
        (
            t
            for t in tasks
            if _norm(t.get("task_type")) == "semantic_guard_review"
            and set((t.get("current_rule_result", {}) or {}).get("flags", [])) & HARD_RISK_FLAGS
            and _norm(t.get("repair_task_id")) not in used
        ),
        None,
    )
    if not unsafe_task:
        unsafe_task = next((t for t in tasks if _norm(t.get("task_type")) == "semantic_guard_review"), None)
    if unsafe_task:
        tid = _norm(unsafe_task.get("repair_task_id"))
        if tid not in used:
            used.add(tid)
            sample_rows.append(
                {
                    "repair_task_id": tid,
                    "decision": "ignore",
                    "repairs": [],
                    "manual_review_items": [],
                    "notes": "sample offline replay ignore for unsafe semantic-guard task",
                }
            )

    extract_added = False
    extract_reason = "no_safe_extract_candidate_found"
    for task in tasks:
        tid = _norm(task.get("repair_task_id"))
        if tid in used:
            continue
        candidate = _try_build_safe_extract_response(task)
        if candidate:
            sample_rows.append(candidate)
            used.add(tid)
            extract_added = True
            extract_reason = "safe_extract_added_from_packet_evidence"
            break

    if not sample_rows:
        fallback_task = tasks[0]
        sample_rows.append(
            {
                "repair_task_id": _norm(fallback_task.get("repair_task_id")),
                "decision": "manual_review",
                "repairs": [],
                "manual_review_items": [
                    {
                        "reason": "fallback sample response",
                        "evidence": _norm(fallback_task.get("evidence", {}).get("row_preview")),
                    }
                ],
                "notes": "minimal sample replay response",
            }
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in sample_rows), encoding="utf-8")
    return {
        "path": str(path),
        "count": len(sample_rows),
        "extract_added": extract_added,
        "extract_reason": extract_reason,
    }


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> Path:
    payload_lines = []
    for r in rows:
        obj = {
            "repair_task_id": r.get("repair_task_id"),
            "decision": r.get("decision"),
            "repairs": r.get("repairs", []),
            "manual_review_items": r.get("manual_review_items", []),
            "notes": r.get("notes", ""),
        }
        payload_lines.append(json.dumps(obj, ensure_ascii=False))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(payload_lines), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Sandbox Stage 1 AI repair worker (offline replay validation).")
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
    if args.provider == "offline_file" and not _norm(args.offline_response_jsonl):
        print("BLOCKED_OFFLINE_FILE_REQUIRES_RESPONSE_JSONL")
        return 3

    packet_jsonl = Path(args.packet_jsonl)
    schema_json = Path(args.schema_json)
    trial_run_root = Path(args.trial_run_root)
    delivery_dir = Path(args.delivery_dir)
    ai_trial_dir = trial_run_root / ("ai_repair_offline_replay" if args.provider == "offline_file" else "ai_repair_trial")

    if not packet_jsonl.exists() or not schema_json.exists():
        print("BLOCKED_REQUIRED_INPUT_MISSING")
        return 3

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    before = _snapshot_files(_collect_production_guard_files(delivery_dir))

    schema_payload = json.loads(schema_json.read_text(encoding="utf-8"))
    tasks = _load_packet(packet_jsonl, max(1, int(args.max_tasks)))
    task_map = {_norm(t.get("repair_task_id")): t for t in tasks}

    results: List[Dict[str, Any]] = []
    offline_response_validation_rows: List[Dict[str, Any]] = []
    response_file_task_count = 0
    unknown_response_task_ids: Set[str] = set()
    duplicate_response_task_ids: Set[str] = set()
    missing_response_task_ids: Set[str] = set()
    malformed_json_lines: List[int] = []
    sample_builder_meta: Dict[str, Any] = {}

    if args.provider == "offline_file":
        resp_path = Path(args.offline_response_jsonl)
        # Keep backward compatibility for single-file replay validation:
        # auto-build sample only when the specific sample file is requested and missing.
        if not resp_path.exists() and resp_path.name == "offline_model_responses_sample.jsonl":
            sample_builder_meta = _build_sample_offline_response(tasks, resp_path)
        if not resp_path.exists():
            print("BLOCKED_OFFLINE_RESPONSE_FILE_MISSING")
            return 3

        responses_by_tid: Dict[str, Dict[str, Any]] = {}
        for idx, line in enumerate(resp_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                malformed_json_lines.append(idx)
                offline_response_validation_rows.append(
                    {
                        "line_no": idx,
                        "repair_task_id": "",
                        "status": "FAIL",
                        "issue": "malformed_json_line",
                    }
                )
                continue
            if not isinstance(obj, dict):
                malformed_json_lines.append(idx)
                offline_response_validation_rows.append(
                    {
                        "line_no": idx,
                        "repair_task_id": "",
                        "status": "FAIL",
                        "issue": "malformed_json_line",
                    }
                )
                continue
            missing_required = [k for k in schema_payload.get("required", []) if k not in obj]
            if missing_required:
                obj.setdefault("_validation_flags", [])
                obj["_validation_flags"].append("missing_required_fields")
                for k in missing_required:
                    obj["_validation_flags"].append(f"schema_missing_field:{k}")
            obj.setdefault("repairs", [])
            obj.setdefault("manual_review_items", [])
            obj.setdefault("notes", "")
            tid = _norm(obj.get("repair_task_id"))
            if not tid:
                offline_response_validation_rows.append(
                    {
                        "line_no": idx,
                        "repair_task_id": "",
                        "status": "FAIL",
                        "issue": "missing_repair_task_id_in_response_file",
                    }
                )
                continue
            response_file_task_count += 1
            if tid in responses_by_tid:
                duplicate_response_task_ids.add(tid)
                offline_response_validation_rows.append(
                    {"line_no": idx, "repair_task_id": tid, "status": "FAIL", "issue": "duplicate_response_task_id"}
                )
                continue
            if tid not in task_map:
                unknown_response_task_ids.add(tid)
                offline_response_validation_rows.append(
                    {"line_no": idx, "repair_task_id": tid, "status": "FAIL", "issue": "unknown_response_task_id"}
                )
                continue
            responses_by_tid[tid] = obj
            offline_response_validation_rows.append(
                {"line_no": idx, "repair_task_id": tid, "status": "PASS", "issue": "accepted"}
            )

        for task in tasks:
            tid = _norm(task.get("repair_task_id"))
            base = responses_by_tid.get(tid)
            if base is None:
                missing_response_task_ids.add(tid)
                base = _offline_manual_review_missing(task)
                offline_response_validation_rows.append(
                    {
                        "line_no": "",
                        "repair_task_id": tid,
                        "status": "WARN",
                        "issue": "offline_response_missing_fallback_manual_review",
                    }
                )
            results.append(_with_task_meta(base, task))
    else:
        for task in tasks:
            results.append(_with_task_meta(_offline_mock_decision(task), task))
        response_file_task_count = len(results)

    schema_validation_rows: List[Dict[str, Any]] = []
    evidence_check_rows: List[Dict[str, Any]] = []
    task_results_rows: List[Dict[str, Any]] = []
    extracted_candidates_rows: List[Dict[str, Any]] = []
    manual_review_items_rows: List[Dict[str, Any]] = []
    merge_preview_rows: List[Dict[str, Any]] = []

    schema_error_count = 0
    evidence_fail_count = 0

    for r in results:
        tid = _norm(r.get("repair_task_id"))
        decision = _norm(r.get("decision"))
        task = task_map.get(tid, {})

        flags: List[str] = []
        flags.extend(r.get("_validation_flags", []))
        flags.extend(_validate_result_schema_basic(r))
        flags.extend(_validate_result_against_schema_payload(r, schema_payload))

        if tid in duplicate_response_task_ids:
            flags.append("duplicate_response_task_id")
        if tid in unknown_response_task_ids:
            flags.append("unknown_response_task_id")
        if tid in missing_response_task_ids and "offline_response_missing" not in flags:
            flags.append("offline_response_missing")
            flags.append("missing_response_task_id")

        evidence_status, evidence_flags, evidence_rows = _check_extract_evidence(task, r)
        if evidence_flags:
            flags.extend(evidence_flags)
            flags.append("extract_demoted_to_manual_review")
            evidence_fail_count += 1
        evidence_check_rows.extend(evidence_rows)

        schema_flags = [f for f in flags if f.startswith("schema_") or f in {
            "missing_repair_task_id", "invalid_decision", "repairs_not_list",
            "manual_review_items_not_list", "extract_without_repairs", "manual_review_without_items",
        }]
        if any(f.startswith("schema_missing_field:") for f in schema_flags):
            flags.append("missing_required_fields")
        if schema_flags:
            flags.append("schema_validation_failed")
        if "invalid_decision" in schema_flags:
            flags.append("invalid_decision")
        if "missing_repair_task_id" in schema_flags:
            flags.append("missing_required_fields")
        if schema_flags:
            schema_error_count += 1

        r["_validation_flags"] = sorted(set(flags))
        r["_evidence_check_status"] = evidence_status
        r["_extract_valid"] = (decision == "extract" and not evidence_flags and not schema_flags)

        schema_validation_rows.append(
            {
                "repair_task_id": tid,
                "decision": decision,
                "schema_errors": "|".join(schema_flags),
                "validation_flags": "|".join(r["_validation_flags"]),
                "schema_valid": "1" if not schema_flags else "0",
            }
        )

        task_results_rows.append(
            {
                "repair_task_id": tid,
                "task_type": _norm(r.get("_task_type")),
                "sample_id": _norm(r.get("_sample_id")),
                "company": _norm(r.get("_company")),
                "source_trace_id": _norm(r.get("_source_trace_id")),
                "decision": decision,
                "repair_count": len(r.get("repairs", [])),
                "manual_review_item_count": len(r.get("manual_review_items", [])),
                "evidence_check_status": _norm(r.get("_evidence_check_status")),
                "validation_flags": "|".join(r.get("_validation_flags", [])),
                "notes": _norm(r.get("notes")),
            }
        )

        if decision == "extract":
            for rp in r.get("repairs", []):
                extracted_candidates_rows.append(
                    {
                        "repair_task_id": tid,
                        "sample_id": _norm(r.get("_sample_id")),
                        "company": _norm(r.get("_company")),
                        "source_trace_id": _norm(r.get("_source_trace_id")),
                        "standard_metric": _norm(rp.get("standard_metric")),
                        "year": _norm(rp.get("year")),
                        "value": rp.get("value"),
                        "unit": _norm(rp.get("unit")),
                        "confidence": _norm(rp.get("confidence")),
                        "evidence": _norm(rp.get("evidence")),
                        "source_cell_or_segment": _norm(rp.get("source_cell_or_segment")),
                        "flags": "|".join(rp.get("flags", []) if isinstance(rp.get("flags"), list) else []),
                        "accepted_for_merge_preview": "1" if r.get("_extract_valid") else "0",
                    }
                )

        if decision == "manual_review":
            for mi in r.get("manual_review_items", []):
                manual_review_items_rows.append(
                    {
                        "repair_task_id": tid,
                        "sample_id": _norm(r.get("_sample_id")),
                        "company": _norm(r.get("_company")),
                        "source_trace_id": _norm(r.get("_source_trace_id")),
                        "reason": _norm(mi.get("reason")),
                        "evidence": _norm(mi.get("evidence")),
                    }
                )

        route_after = "manual_review_candidate"
        if decision == "ignore":
            route_after = "ignore"
        elif decision == "non_target":
            route_after = "non_target"
        elif decision == "extract" and r.get("_extract_valid"):
            route_after = "ai_candidate_for_rule_validation"

        if decision == "extract" and r.get("repairs"):
            for rp in r.get("repairs", []):
                merge_preview_rows.append(
                    {
                        "repair_task_id": tid,
                        "sample_id": _norm(r.get("_sample_id")),
                        "company": _norm(r.get("_company")),
                        "source_trace_id": _norm(r.get("_source_trace_id")),
                        "decision": decision,
                        "standard_metric": _norm(rp.get("standard_metric")),
                        "year": _norm(rp.get("year")),
                        "value": rp.get("value"),
                        "unit": _norm(rp.get("unit")),
                        "evidence": _norm(rp.get("evidence")),
                        "validation_flags": "|".join(r.get("_validation_flags", [])),
                        "recommended_route_after_ai": route_after,
                    }
                )
        else:
            merge_preview_rows.append(
                {
                    "repair_task_id": tid,
                    "sample_id": _norm(r.get("_sample_id")),
                    "company": _norm(r.get("_company")),
                    "source_trace_id": _norm(r.get("_source_trace_id")),
                    "decision": decision,
                    "standard_metric": _norm(r.get("_standard_metric_hint")),
                    "year": "",
                    "value": "",
                    "unit": "",
                    "evidence": _norm(r.get("notes")),
                    "validation_flags": "|".join(r.get("_validation_flags", [])),
                    "recommended_route_after_ai": route_after,
                }
            )

    processed_task_count = len(results)
    decision_counts: Dict[str, int] = {}
    for r in results:
        d = _norm(r.get("decision"))
        decision_counts[d] = decision_counts.get(d, 0) + 1

    ai_trial_dir.mkdir(parents=True, exist_ok=True)
    out_results_jsonl = _write_jsonl(ai_trial_dir / "ai_repair_results.jsonl", results)
    out_results_xlsx = _safe_write_excel({"task_results": pd.DataFrame(task_results_rows)}, ai_trial_dir / "ai_repair_results.xlsx")
    out_candidates_xlsx = _safe_write_excel({"extracted_candidates": pd.DataFrame(extracted_candidates_rows)}, ai_trial_dir / "ai_repair_candidates.xlsx")
    out_validation_xlsx = _safe_write_excel(
        {
            "schema_validation": pd.DataFrame(schema_validation_rows),
            "evidence_check": pd.DataFrame(evidence_check_rows),
            "offline_response_validation": pd.DataFrame(offline_response_validation_rows),
        },
        ai_trial_dir / "ai_repair_validation.xlsx",
    )
    out_merge_preview_xlsx = _safe_write_excel({"merge_preview": pd.DataFrame(merge_preview_rows)}, ai_trial_dir / "ai_repair_merge_preview.xlsx")

    schema_validation_status = "PASS" if schema_error_count == 0 else "FAIL"
    offline_validation_status = "PASS"
    if duplicate_response_task_ids or unknown_response_task_ids or malformed_json_lines:
        offline_validation_status = "FAIL"
    elif missing_response_task_ids:
        offline_validation_status = "WARN"
    extraction_value_evidence_check_status = "PASS" if evidence_fail_count == 0 else "WARN"

    overall_validation_status = "PASS"
    if "FAIL" in {schema_validation_status, offline_validation_status}:
        overall_validation_status = "FAIL"
    elif "WARN" in {offline_validation_status, extraction_value_evidence_check_status}:
        overall_validation_status = "WARN"

    after = _snapshot_files(_collect_production_guard_files(delivery_dir))
    production_guard_rows = _compare_snapshot(before, after)
    changed_count = sum(1 for r in production_guard_rows if r.get("changed") == "1")
    production_status_after = _run_delivery_check_json(delivery_dir)

    extracted_candidate_count = sum(
        1 for r in results if _norm(r.get("decision")) == "extract" and bool(r.get("_extract_valid"))
    )
    manual_review_count = decision_counts.get("manual_review", 0)
    ignored_count = decision_counts.get("ignore", 0)
    non_target_count = decision_counts.get("non_target", 0)

    if changed_count > 0 or overall_validation_status == "FAIL":
        ai_status = "FAIL"
    elif overall_validation_status == "WARN":
        ai_status = "WARN"
    else:
        ai_status = "PASS"

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
        {"check_name": "no_real_ai_call", "status": "PASS", "detail": f"provider={args.provider}, offline replay only"},
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

    report42_md = _safe_write_text(
        delivery_dir / "42_stage1_ai_repair_offline_replay_log.md",
        "\n".join(
            [
                "# Stage1 AI Repair Offline Replay Log",
                "",
                "- task_title: Add Stage 1 AI repair offline file replay validation",
                f"- started_at: {started_at}",
                f"- finished_at: {finished_at}",
                f"- command_run: {command_run}",
                f"- provider: {args.provider}",
                f"- packet_path: {packet_jsonl}",
                f"- schema_path: {schema_json}",
                f"- offline_response_path: {args.offline_response_jsonl if args.provider == 'offline_file' else ''}",
                f"- processed_task_count: {processed_task_count}",
                f"- response_file_task_count: {response_file_task_count}",
                f"- decision_counts: {json.dumps(decision_counts, ensure_ascii=False)}",
                f"- validation_status: {overall_validation_status}",
                f"- evidence_check_status: {extraction_value_evidence_check_status}",
                f"- output_files_generated: {json.dumps(generated_outputs, ensure_ascii=False)}",
                f"- production_guard_changed_count: {changed_count}",
                f"- safety_checks: {json.dumps(safety_checks, ensure_ascii=False)}",
            ]
        ),
    )

    report42_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": "Add Stage 1 AI repair offline file replay validation"},
                    {"field": "started_at", "value": started_at},
                    {"field": "finished_at", "value": finished_at},
                    {"field": "command_run", "value": command_run},
                    {"field": "provider", "value": args.provider},
                    {"field": "packet_path", "value": str(packet_jsonl)},
                    {"field": "schema_path", "value": str(schema_json)},
                    {"field": "offline_response_path", "value": _norm(args.offline_response_jsonl)},
                    {"field": "processed_task_count", "value": processed_task_count},
                    {"field": "response_file_task_count", "value": response_file_task_count},
                    {"field": "decision_counts", "value": json.dumps(decision_counts, ensure_ascii=False)},
                    {"field": "validation_status", "value": overall_validation_status},
                    {"field": "evidence_check_status", "value": extraction_value_evidence_check_status},
                    {"field": "production_guard_changed_count", "value": changed_count},
                    {"field": "sample_builder_extract_added", "value": _norm(sample_builder_meta.get("extract_added"))},
                    {"field": "sample_builder_extract_reason", "value": _norm(sample_builder_meta.get("extract_reason"))},
                ]
            ),
            "decision_summary": pd.DataFrame([{"decision": k, "count": v} for k, v in sorted(decision_counts.items())]),
            "task_results": pd.DataFrame(task_results_rows),
            "extracted_candidates": pd.DataFrame(extracted_candidates_rows),
            "manual_review_items": pd.DataFrame(manual_review_items_rows),
            "schema_validation": pd.DataFrame(schema_validation_rows),
            "evidence_check": pd.DataFrame(evidence_check_rows),
            "offline_response_validation": pd.DataFrame(offline_response_validation_rows),
            "merge_preview": pd.DataFrame(merge_preview_rows),
            "production_guard": pd.DataFrame(production_guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
        },
        delivery_dir / "42_stage1_ai_repair_offline_replay_log.xlsx",
    )

    report43_md = _safe_write_text(
        delivery_dir / "43_stage1_ai_repair_offline_replay_evaluation.md",
        "\n".join(
            [
                "# Stage1 AI Repair Offline Replay Evaluation",
                "",
                f"- ai_repair_worker_status: {ai_status}",
                f"- provider: {args.provider}",
                f"- task_count: {processed_task_count}",
                f"- response_file_task_count: {response_file_task_count}",
                f"- decision_counts: {json.dumps(decision_counts, ensure_ascii=False)}",
                f"- extracted_candidate_count: {extracted_candidate_count}",
                f"- manual_review_count: {manual_review_count}",
                f"- ignored_count: {ignored_count}",
                f"- non_target_count: {non_target_count}",
                f"- schema_validation_status: {schema_validation_status}",
                f"- extraction_value_evidence_check_status: {extraction_value_evidence_check_status}",
                f"- unknown_response_task_count: {len(unknown_response_task_ids)}",
                f"- duplicate_response_task_count: {len(duplicate_response_task_ids)}",
                f"- malformed_json_line_count: {len(malformed_json_lines)}",
                f"- missing_response_task_count: {len(missing_response_task_ids)}",
                f"- sample_decision_summary: {json.dumps(sample_decision_summary, ensure_ascii=False)}",
                f"- task_type_decision_summary: {json.dumps(task_type_decision_summary, ensure_ascii=False)}",
                f"- merge_preview_summary: {json.dumps(merge_preview_summary, ensure_ascii=False)}",
                f"- production_delivery_status_after: {json.dumps(production_status_after, ensure_ascii=False)}",
                f"- production_files_unchanged: {changed_count == 0}",
                "- recommended_next_step: Connect real provider later only after additional guardrail tests.",
            ]
        ),
    )

    report43_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "ai_repair_worker_status", "value": ai_status},
                    {"field": "provider", "value": args.provider},
                    {"field": "task_count", "value": processed_task_count},
                    {"field": "response_file_task_count", "value": response_file_task_count},
                    {"field": "decision_counts", "value": json.dumps(decision_counts, ensure_ascii=False)},
                    {"field": "extracted_candidate_count", "value": extracted_candidate_count},
                    {"field": "manual_review_count", "value": manual_review_count},
                    {"field": "ignored_count", "value": ignored_count},
                    {"field": "non_target_count", "value": non_target_count},
                    {"field": "schema_validation_status", "value": schema_validation_status},
                    {"field": "extraction_value_evidence_check_status", "value": extraction_value_evidence_check_status},
                    {"field": "unknown_response_task_count", "value": len(unknown_response_task_ids)},
                    {"field": "duplicate_response_task_count", "value": len(duplicate_response_task_ids)},
                    {"field": "malformed_json_line_count", "value": len(malformed_json_lines)},
                    {"field": "missing_response_task_count", "value": len(missing_response_task_ids)},
                    {"field": "production_delivery_status_after", "value": json.dumps(production_status_after, ensure_ascii=False)},
                    {"field": "production_files_unchanged", "value": "1" if changed_count == 0 else "0"},
                ]
            ),
            "decision_summary": pd.DataFrame([{"decision": k, "count": v} for k, v in sorted(decision_counts.items())]),
            "task_results": pd.DataFrame(task_results_rows),
            "extracted_candidates": pd.DataFrame(extracted_candidates_rows),
            "manual_review_items": pd.DataFrame(manual_review_items_rows),
            "schema_validation": pd.DataFrame(schema_validation_rows),
            "evidence_check": pd.DataFrame(evidence_check_rows),
            "offline_response_validation": pd.DataFrame(offline_response_validation_rows),
            "merge_preview": pd.DataFrame(merge_preview_rows),
            "production_guard": pd.DataFrame(production_guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "Add controlled real-provider dry-run after schema/evidence replay remains stable.",
                    }
                ]
            ),
        },
        delivery_dir / "43_stage1_ai_repair_offline_replay_evaluation.xlsx",
    )

    print(f"worker_path: {Path(__file__)}")
    print(f"provider: {args.provider}")
    print(f"offline_response_path: {args.offline_response_jsonl if args.provider == 'offline_file' else ''}")
    print(f"processed_task_count: {processed_task_count}")
    print(f"response_file_task_count: {response_file_task_count}")
    print(f"ai_repair_worker_status: {ai_status}")
    print(f"decision_counts: {json.dumps(decision_counts, ensure_ascii=False)}")
    print(f"schema_validation_status: {schema_validation_status}")
    print(f"evidence_check_status: {extraction_value_evidence_check_status}")
    print(f"unknown_response_task_count: {len(unknown_response_task_ids)}")
    print(f"duplicate_response_task_count: {len(duplicate_response_task_ids)}")
    print(f"malformed_json_line_count: {len(malformed_json_lines)}")
    print(f"missing_response_task_count: {len(missing_response_task_ids)}")
    print(
        "generated_outputs: "
        + json.dumps([str(report42_md), str(report42_xlsx), str(report43_md), str(report43_xlsx)] + generated_outputs, ensure_ascii=False)
    )
    print(f"production_delivery_status_after: {json.dumps(production_status_after, ensure_ascii=False)}")
    print(f"production_guard_changed_count: {changed_count}")

    if changed_count > 0:
        return 5
    return 0 if ai_status in {"PASS", "WARN"} else 4


if __name__ == "__main__":
    raise SystemExit(main())
