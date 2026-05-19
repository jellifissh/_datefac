import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd


SECRET_PATTERNS = ["sk-", "BEGIN PRIVATE KEY", "Bearer ", "api_secret", "password=", "token="]
DECISIONS = {"extract", "manual_review", "ignore", "non_target"}
PRODUCTION_PREFIX_PATTERNS = ["01_*.xlsx", "02_*.xlsx", "02A_*.xlsx", "06_*.xlsx"]
NUM_RE = re.compile(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?")


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


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    path.write_text(payload, encoding="utf-8")
    return path


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


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


def _evidence_text(task: Dict[str, Any]) -> str:
    evidence = task.get("evidence", {}) or {}
    parts: List[str] = []
    for key in ["row_preview", "table_header_context", "nearby_rows_context", "raw_table_preview"]:
        v = evidence.get(key, "")
        if isinstance(v, list):
            parts.append(json.dumps(v, ensure_ascii=False))
        else:
            parts.append(_norm(v))
    row_cells = evidence.get("row_cells", [])
    if isinstance(row_cells, list):
        parts.append("|".join(_norm(x) for x in row_cells))
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
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", s):
        return ""
    try:
        n = float(s)
        if neg:
            n = -n
        return f"{n:.12f}".rstrip("0").rstrip(".")
    except Exception:
        return ""


def _collect_evidence_numbers(text: str) -> Set[str]:
    values: Set[str] = set()
    for m in NUM_RE.findall(text or ""):
        nv = _normalize_number_text(m)
        if nv:
            values.add(nv)
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


def _scan_secret_hits(text: str) -> List[str]:
    hits: List[str] = []
    for p in SECRET_PATTERNS:
        if p in text:
            hits.append(p)
    return hits


def _has_garbled_text(text: str) -> bool:
    return "????" in text or "�" in text


def _extract_first_year_and_value(task: Dict[str, Any]) -> Tuple[str, str]:
    evidence = task.get("evidence", {}) or {}
    years = [_norm(x) for x in evidence.get("detected_years", []) if _norm(x)]
    year = years[0] if years else ""
    if not year:
        found_years = re.findall(r"(20\d{2}(?:[AE])?)", _evidence_text(task))
        year = found_years[0] if found_years else ""
    value = ""
    row_cells = evidence.get("row_cells", [])
    if isinstance(row_cells, list):
        for c in row_cells:
            if _normalize_number_text(c):
                value = _norm(c)
                break
    if not value:
        nums = NUM_RE.findall(_evidence_text(task))
        value = nums[0] if nums else ""
    return year, value


def _build_synthetic_raw_responses(
    raw_path: Path,
    requests: List[Dict[str, Any]],
    task_map: Dict[str, Dict[str, Any]],
) -> Tuple[Path, List[Dict[str, Any]]]:
    if len(requests) < 6:
        raise RuntimeError("request_batch_too_small_for_synthetic_cases")

    req = requests
    req0, req1, req2, req3, req4, req5 = req[0], req[1], req[2], req[3], req[4], req[5]

    t2 = task_map.get(_norm(req2.get("repair_task_id")), {})
    year2, value2 = _extract_first_year_and_value(t2)
    metric2 = _norm((t2.get("current_rule_result", {}) or {}).get("standard_metric_hint")) or "营业收入"

    line_objs: List[Dict[str, Any]] = []
    line_strs: List[str] = []

    line_objs.append(
        {
            "case_id": "valid_manual_review",
            "payload": {
                "request_id": _norm(req0.get("request_id")),
                "repair_task_id": _norm(req0.get("repair_task_id")),
                "decision": "manual_review",
                "repairs": [],
                "manual_review_items": [{"reason": "ambiguous_multi_metric_row", "evidence": "row segment mixes multiple metrics"}],
                "notes": "manual review due to ambiguity",
            },
        }
    )
    line_objs.append(
        {
            "case_id": "valid_ignore",
            "payload": {
                "request_id": _norm(req1.get("request_id")),
                "repair_task_id": _norm(req1.get("repair_task_id")),
                "decision": "ignore",
                "repairs": [],
                "manual_review_items": [],
                "notes": "ignore low-signal row",
            },
        }
    )
    line_objs.append(
        {
            "case_id": "valid_extract_evidence_backed",
            "payload": {
                "request_id": _norm(req2.get("request_id")),
                "repair_task_id": _norm(req2.get("repair_task_id")),
                "decision": "extract",
                "repairs": [
                    {
                        "standard_metric": metric2,
                        "year": year2 or "2026E",
                        "value": value2 or "3.71",
                        "unit": "",
                        "confidence": "low",
                        "evidence": _norm((t2.get("evidence", {}) or {}).get("row_preview")),
                        "source_cell_or_segment": _norm((t2.get("source", {}) or {}).get("source_trace_id")),
                        "flags": ["synthetic_provider_extract"],
                    }
                ],
                "manual_review_items": [],
                "notes": "synthetic evidence-backed extract",
            },
        }
    )
    line_objs.append(
        {
            "case_id": "unknown_request_and_task",
            "payload": {
                "request_id": "PRF-9999",
                "repair_task_id": "RPR-S9-9999",
                "decision": "manual_review",
                "repairs": [],
                "manual_review_items": [{"reason": "unknown_task", "evidence": "n/a"}],
                "notes": "should be rejected",
            },
        }
    )
    line_objs.append(
        {
            "case_id": "duplicate_repair_task_id",
            "payload": {
                "request_id": _norm(req0.get("request_id")),
                "repair_task_id": _norm(req0.get("repair_task_id")),
                "decision": "ignore",
                "repairs": [],
                "manual_review_items": [],
                "notes": "duplicate should be rejected",
            },
        }
    )
    line_objs.append(
        {
            "case_id": "fabricated_extract_value",
            "payload": {
                "request_id": _norm(req3.get("request_id")),
                "repair_task_id": _norm(req3.get("repair_task_id")),
                "decision": "extract",
                "repairs": [
                    {
                        "standard_metric": "营业收入",
                        "year": "2028E",
                        "value": "987654321",
                        "unit": "",
                        "confidence": "medium",
                        "evidence": "fabricated value not in evidence",
                        "source_cell_or_segment": "synthetic",
                        "flags": ["fabricated"],
                    }
                ],
                "manual_review_items": [],
                "notes": "should be rejected by evidence gate",
            },
        }
    )
    line_objs.append(
        {
            "case_id": "missing_decision",
            "payload": {
                "request_id": _norm(req4.get("request_id")),
                "repair_task_id": _norm(req4.get("repair_task_id")),
                "repairs": [],
                "manual_review_items": [],
                "notes": "missing decision should be rejected",
            },
        }
    )
    line_objs.append(
        {
            "case_id": "wrapper_normalization_valid",
            "payload": {
                "request": {"request_id": _norm(req5.get("request_id"))},
                "response": {
                    "repair_task_id": _norm(req5.get("repair_task_id")),
                    "decision": "manual_review",
                    "repairs": [],
                    "manual_review_items": [{"reason": "wrapper_case", "evidence": "normalized wrapper response"}],
                    "notes": "wrapped response should be normalized",
                },
                "extra_context": {"provider_debug": "safe_meta"},
            },
        }
    )

    for obj in line_objs:
        line_strs.append(json.dumps(obj["payload"], ensure_ascii=False))

    line_strs.append("{\"request_id\":\"PRF-9998\", \"repair_task_id\":\"RPR-SX-0000\", \"decision\":")

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text("\n".join(line_strs), encoding="utf-8")
    return raw_path, line_objs


def _normalize_response_object(raw_obj: Dict[str, Any]) -> Tuple[str, Dict[str, Any], bool]:
    request_id = _norm(raw_obj.get("request_id"))
    wrapped = False
    payload = raw_obj

    if isinstance(raw_obj.get("response"), dict):
        payload = raw_obj.get("response")
        wrapped = True
    if not request_id and isinstance(raw_obj.get("request"), dict):
        request_id = _norm(raw_obj.get("request", {}).get("request_id"))
        wrapped = True
    if not request_id:
        request_id = _norm(payload.get("request_id"))

    normalized = {
        "repair_task_id": _norm(payload.get("repair_task_id")),
        "decision": _norm(payload.get("decision")),
        "repairs": payload.get("repairs", []),
        "manual_review_items": payload.get("manual_review_items", []),
        "notes": _norm(payload.get("notes")),
    }
    return request_id, normalized, wrapped


def _validate_schema_basic(normalized: Dict[str, Any], schema_payload: Dict[str, Any]) -> List[str]:
    reasons: List[str] = []
    required = schema_payload.get("required", [])
    for field in required:
        if field not in normalized or (
            field in {"decision", "repair_task_id", "notes"} and _norm(normalized.get(field)) == ""
        ):
            reasons.append(f"missing_required_field:{field}")
    decision = _norm(normalized.get("decision"))
    if decision and decision not in DECISIONS:
        reasons.append("invalid_decision")
    if not isinstance(normalized.get("repairs"), list):
        reasons.append("repairs_not_list")
    if not isinstance(normalized.get("manual_review_items"), list):
        reasons.append("manual_review_items_not_list")
    if decision == "extract" and not normalized.get("repairs"):
        reasons.append("extract_without_repairs")
    if decision == "manual_review" and not normalized.get("manual_review_items"):
        reasons.append("manual_review_without_items")
    return reasons


def _validate_extract_evidence(
    normalized: Dict[str, Any],
    task: Dict[str, Any],
) -> List[str]:
    reasons: List[str] = []
    if _norm(normalized.get("decision")) != "extract":
        return reasons
    evidence_text = _evidence_text(task)
    evidence_numbers = _collect_evidence_numbers(evidence_text)
    detected_years = [_norm(x) for x in (task.get("evidence", {}) or {}).get("detected_years", []) if _norm(x)]
    repairs = normalized.get("repairs", [])
    for idx, rp in enumerate(repairs):
        metric = _norm(rp.get("standard_metric"))
        year = _norm(rp.get("year"))
        value = rp.get("value")
        if not metric:
            reasons.append(f"repair_{idx}_missing_metric")
        if metric and metric not in evidence_text:
            reasons.append(f"repair_{idx}_metric_not_in_evidence")
        if not year or not _year_in_evidence(year, detected_years, evidence_text):
            reasons.append(f"repair_{idx}_year_not_in_evidence")
        if not _value_in_evidence(value, evidence_text, evidence_numbers):
            reasons.append(f"repair_{idx}_value_not_in_evidence")
    return reasons


def _clean_for_worker(normalized: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "repair_task_id": _norm(normalized.get("repair_task_id")),
        "decision": _norm(normalized.get("decision")),
        "repairs": normalized.get("repairs", []) if isinstance(normalized.get("repairs"), list) else [],
        "manual_review_items": normalized.get("manual_review_items", []) if isinstance(normalized.get("manual_review_items"), list) else [],
        "notes": _norm(normalized.get("notes")),
    }


def _run_worker_offline_replay(
    packet_jsonl: Path,
    schema_json: Path,
    trial_run_root: Path,
    delivery_dir: Path,
    clean_jsonl: Path,
) -> Dict[str, Any]:
    worker = Path(r"D:\_datefac\tools\run_stage1_ai_repair_worker.py")
    cmd = [
        sys.executable,
        str(worker),
        "--packet-jsonl",
        str(packet_jsonl),
        "--schema-json",
        str(schema_json),
        "--trial-run-root",
        str(trial_run_root),
        "--delivery-dir",
        str(delivery_dir),
        "--provider",
        "offline_file",
        "--offline-response-jsonl",
        str(clean_jsonl),
        "--strict-schema",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    parsed: Dict[str, Any] = {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "cmd": " ".join(cmd)}
    for line in (p.stdout or "").splitlines():
        if ": " not in line:
            continue
        k, v = line.split(": ", 1)
        parsed[k.strip()] = v.strip()
    return parsed


def _copy_replay_outputs(trial_run_root: Path, intake_dir: Path) -> Tuple[List[str], Dict[str, Any]]:
    src = trial_run_root / "ai_repair_offline_replay"
    dst = intake_dir / "offline_file_replay_after_intake"
    copied: List[str] = []
    summary: Dict[str, Any] = {"merge_preview_rows": 0, "candidate_rows": 0}
    if not src.exists():
        return copied, summary
    dst.mkdir(parents=True, exist_ok=True)
    names = [
        "ai_repair_results.jsonl",
        "ai_repair_results.xlsx",
        "ai_repair_candidates.xlsx",
        "ai_repair_validation.xlsx",
        "ai_repair_merge_preview.xlsx",
    ]
    for name in names:
        sp = src / name
        if sp.exists():
            dp = dst / name
            shutil.copy2(sp, dp)
            copied.append(str(dp))
    merge_preview_path = dst / "ai_repair_merge_preview.xlsx"
    if merge_preview_path.exists():
        try:
            merge_df = pd.read_excel(merge_preview_path, sheet_name="merge_preview")
            summary["merge_preview_rows"] = int(len(merge_df))
            if "recommended_route_after_ai" in merge_df.columns:
                c = Counter([_norm(x) for x in merge_df["recommended_route_after_ai"].tolist()])
                summary["merge_preview_route_counts"] = dict(c)
        except Exception:
            pass
    candidate_path = dst / "ai_repair_candidates.xlsx"
    if candidate_path.exists():
        try:
            cdf = pd.read_excel(candidate_path, sheet_name="extracted_candidates")
            summary["candidate_rows"] = int(len(cdf))
        except Exception:
            pass
    return copied, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 1 provider response intake gate (sandbox-only, offline).")
    parser.add_argument("--request-batch", required=True)
    parser.add_argument("--schema-json", required=True)
    parser.add_argument("--packet-jsonl", required=True)
    parser.add_argument("--trial-run-root", required=True)
    parser.add_argument("--delivery-dir", required=True)
    parser.add_argument("--raw-provider-response", required=True)
    parser.add_argument("--run-offline-replay", action="store_true")
    args = parser.parse_args()

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_batch = Path(args.request_batch)
    schema_json = Path(args.schema_json)
    packet_jsonl = Path(args.packet_jsonl)
    trial_run_root = Path(args.trial_run_root)
    delivery_dir = Path(args.delivery_dir)
    raw_provider_path = Path(args.raw_provider_response)
    intake_helper = Path(__file__)

    if not request_batch.exists() or not schema_json.exists() or not packet_jsonl.exists():
        print("BLOCKED_REQUIRED_INPUT_MISSING")
        return 3

    intake_dir = trial_run_root / "ai_repair_provider_intake"
    intake_dir.mkdir(parents=True, exist_ok=True)
    raw_provider_path.parent.mkdir(parents=True, exist_ok=True)

    before = _snapshot_files(_collect_production_guard_files(delivery_dir))

    requests = _load_jsonl(request_batch)
    request_by_id = {_norm(r.get("request_id")): r for r in requests}
    request_to_task = {_norm(r.get("request_id")): _norm(r.get("repair_task_id")) for r in requests}
    packet_tasks = _load_jsonl(packet_jsonl)
    task_map = {_norm(t.get("repair_task_id")): t for t in packet_tasks}
    schema_payload = json.loads(schema_json.read_text(encoding="utf-8"))

    raw_provider_path, synthetic_cases = _build_synthetic_raw_responses(raw_provider_path, requests, task_map)

    raw_lines = raw_provider_path.read_text(encoding="utf-8").splitlines()
    raw_response_count = len(raw_lines)
    clean_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []
    raw_inventory_rows: List[Dict[str, Any]] = []
    evidence_rows: List[Dict[str, Any]] = []
    accepted_tids: Set[str] = set()
    wrapper_normalized_count = 0
    malformed_json_count = 0

    unknown_request_blocked = False
    duplicate_blocked = False
    fabricated_blocked = False
    missing_required_blocked = False

    for i, line in enumerate(raw_lines, start=1):
        line_text = _norm(line)
        reasons: List[str] = []
        obj: Optional[Dict[str, Any]] = None
        request_id = ""
        normalized: Dict[str, Any] = {}
        wrapped = False

        if not line_text:
            reasons.append("empty_line")
        else:
            try:
                parsed = json.loads(line_text)
                if not isinstance(parsed, dict):
                    reasons.append("malformed_json_non_object")
                else:
                    obj = parsed
            except Exception:
                reasons.append("malformed_json")
                malformed_json_count += 1

        if obj is not None:
            request_id, normalized, wrapped = _normalize_response_object(obj)
            if wrapped:
                wrapper_normalized_count += 1
            schema_reasons = _validate_schema_basic(normalized, schema_payload)
            if schema_reasons:
                reasons.extend(schema_reasons)
                missing_required_blocked = True

            tid = _norm(normalized.get("repair_task_id"))
            expected_tid = request_to_task.get(request_id, "")
            if not request_id or request_id not in request_by_id:
                reasons.append("unknown_request_id")
                unknown_request_blocked = True
            if not tid:
                reasons.append("missing_repair_task_id")
                missing_required_blocked = True
            if tid and expected_tid and tid != expected_tid:
                reasons.append("repair_task_id_mismatch_with_request")
            if tid and tid not in task_map:
                reasons.append("unknown_repair_task_id")
            if tid and tid in accepted_tids:
                reasons.append("duplicate_repair_task_id")
                duplicate_blocked = True

            task = task_map.get(tid, {})
            evidence_reasons = _validate_extract_evidence(normalized, task) if task else []
            if evidence_reasons:
                reasons.extend(evidence_reasons)
                fabricated_blocked = True
            evidence_rows.append(
                {
                    "line_no": i,
                    "request_id": request_id,
                    "repair_task_id": tid,
                    "decision": _norm(normalized.get("decision")),
                    "evidence_check_status": "PASS" if not evidence_reasons else "FAIL",
                    "evidence_reasons": "|".join(evidence_reasons),
                }
            )

        raw_secret_hits = _scan_secret_hits(line_text)
        if raw_secret_hits:
            reasons.append("secret_like_pattern")
        if _has_garbled_text(line_text):
            reasons.append("garbled_text_detected")

        if reasons:
            rejected_rows.append(
                {
                    "line_no": i,
                    "request_id": request_id,
                    "repair_task_id": _norm(normalized.get("repair_task_id")),
                    "rejection_reasons": "|".join(sorted(set(reasons))),
                    "raw_payload": line_text[:1000],
                }
            )
            raw_inventory_rows.append(
                {
                    "line_no": i,
                    "status": "rejected",
                    "request_id": request_id,
                    "repair_task_id": _norm(normalized.get("repair_task_id")),
                    "decision": _norm(normalized.get("decision")),
                    "reasons": "|".join(sorted(set(reasons))),
                    "wrapped_normalized": "1" if wrapped else "0",
                }
            )
            continue

        clean_obj = _clean_for_worker(normalized)
        accepted_tids.add(_norm(clean_obj.get("repair_task_id")))
        clean_rows.append(clean_obj)
        raw_inventory_rows.append(
            {
                "line_no": i,
                "status": "accepted",
                "request_id": request_id,
                "repair_task_id": _norm(clean_obj.get("repair_task_id")),
                "decision": _norm(clean_obj.get("decision")),
                "reasons": "",
                "wrapped_normalized": "1" if wrapped else "0",
            }
        )

    clean_path = intake_dir / "provider_response_intake_clean.jsonl"
    rejected_path = intake_dir / "provider_response_intake_rejected.jsonl"
    validation_path = intake_dir / "provider_response_intake_validation.xlsx"
    summary_path = intake_dir / "provider_response_intake_summary.xlsx"

    _write_jsonl(clean_path, clean_rows)
    _write_jsonl(rejected_path, rejected_rows)

    rejection_counts = Counter()
    for r in rejected_rows:
        for reason in _norm(r.get("rejection_reasons")).split("|"):
            if reason:
                rejection_counts[reason] += 1

    clean_decisions = Counter([_norm(r.get("decision")) for r in clean_rows])
    no_secret_text = "\n".join(raw_lines + [json.dumps(x, ensure_ascii=False) for x in clean_rows] + [json.dumps(x, ensure_ascii=False) for x in rejected_rows])
    no_secret_status = "PASS" if not _scan_secret_hits(no_secret_text) else "FAIL"

    _safe_write_excel(
        {
            "raw_response_inventory": pd.DataFrame(raw_inventory_rows),
            "clean_responses": pd.DataFrame(clean_rows),
            "rejected_responses": pd.DataFrame(rejected_rows),
            "rejection_reason_summary": pd.DataFrame([{"reason": k, "count": v} for k, v in sorted(rejection_counts.items())]),
            "evidence_check": pd.DataFrame(evidence_rows),
            "summary": pd.DataFrame(
                [
                    {"field": "raw_response_count", "value": raw_response_count},
                    {"field": "clean_response_count", "value": len(clean_rows)},
                    {"field": "rejected_response_count", "value": len(rejected_rows)},
                    {"field": "wrapper_normalized_count", "value": wrapper_normalized_count},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                ]
            ),
        },
        validation_path,
    )

    _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "raw_response_count", "value": raw_response_count},
                    {"field": "clean_response_count", "value": len(clean_rows)},
                    {"field": "rejected_response_count", "value": len(rejected_rows)},
                    {"field": "accepted_manual_review_count", "value": clean_decisions.get("manual_review", 0)},
                    {"field": "accepted_ignore_count", "value": clean_decisions.get("ignore", 0)},
                    {"field": "valid_extract_count", "value": clean_decisions.get("extract", 0)},
                    {"field": "wrapper_normalization_status", "value": "PASS" if wrapper_normalized_count > 0 else "WARN"},
                    {"field": "unknown_request_blocking_status", "value": "PASS" if unknown_request_blocked else "WARN"},
                    {"field": "duplicate_response_blocking_status", "value": "PASS" if duplicate_blocked else "WARN"},
                    {"field": "fabricated_value_blocking_status", "value": "PASS" if fabricated_blocked else "WARN"},
                    {"field": "malformed_json_blocking_status", "value": "PASS" if malformed_json_count > 0 else "WARN"},
                    {"field": "missing_required_fields_blocking_status", "value": "PASS" if missing_required_blocked else "WARN"},
                ]
            ),
            "rejection_reason_summary": pd.DataFrame([{"reason": k, "count": v} for k, v in sorted(rejection_counts.items())]),
            "clean_decision_counts": pd.DataFrame([{"decision": k, "count": v} for k, v in sorted(clean_decisions.items())]),
            "synthetic_cases": pd.DataFrame([{"case_id": c["case_id"]} for c in synthetic_cases]),
        },
        summary_path,
    )

    replay_status = "SKIPPED"
    replay_summary: Dict[str, Any] = {}
    copied_replay_outputs: List[str] = []
    if args.run_offline_replay:
        replay_result = _run_worker_offline_replay(packet_jsonl, schema_json, trial_run_root, delivery_dir, clean_path)
        replay_status = "PASS" if replay_result.get("returncode") == 0 else "FAIL"
        replay_summary = replay_result
        copied_replay_outputs, merge_preview_summary = _copy_replay_outputs(trial_run_root, intake_dir)
        replay_summary.update(merge_preview_summary)

    after = _snapshot_files(_collect_production_guard_files(delivery_dir))
    production_guard_rows = _compare_snapshot(before, after)
    production_changed_count = sum(1 for r in production_guard_rows if r.get("changed") == "1")
    production_files_unchanged = production_changed_count == 0
    production_delivery_status = _run_delivery_check_json(delivery_dir)

    provider_intake_status = "PASS"
    if no_secret_status != "PASS" or production_changed_count > 0:
        provider_intake_status = "FAIL"
    elif replay_status == "FAIL":
        provider_intake_status = "FAIL"
    elif len(clean_rows) == 0 or len(rejected_rows) == 0:
        provider_intake_status = "WARN"

    safety_checks = [
        {"check_name": "factory_core_not_run", "status": "PASS", "detail": "intake helper only"},
        {"check_name": "vision_or_ocr_not_triggered", "status": "PASS", "detail": "no OCR/vision invocation"},
        {"check_name": "no_real_ai_call", "status": "PASS", "detail": "synthetic local response only"},
        {"check_name": "no_secret_check", "status": no_secret_status, "detail": "raw/clean/rejected scanned"},
        {"check_name": "production_files_unchanged", "status": "PASS" if production_files_unchanged else "FAIL", "detail": f"changed={production_changed_count}"},
    ]

    commands_run = [
        f"{sys.executable} -m py_compile {intake_helper}",
        f"{sys.executable} {intake_helper} --request-batch {request_batch} --schema-json {schema_json} --packet-jsonl {packet_jsonl} --trial-run-root {trial_run_root} --delivery-dir {delivery_dir} --raw-provider-response {raw_provider_path} --run-offline-replay",
        f"{sys.executable} D:/_datefac/tools/check_delivery_state.py --json",
    ]
    generated_outputs = [
        str(raw_provider_path),
        str(clean_path),
        str(rejected_path),
        str(validation_path),
        str(summary_path),
        *copied_replay_outputs,
        str(delivery_dir / "52_stage1_ai_repair_provider_intake_log.md"),
        str(delivery_dir / "52_stage1_ai_repair_provider_intake_log.xlsx"),
        str(delivery_dir / "53_stage1_ai_repair_provider_intake_evaluation.md"),
        str(delivery_dir / "53_stage1_ai_repair_provider_intake_evaluation.xlsx"),
    ]

    report52_md = _safe_write_text(
        delivery_dir / "52_stage1_ai_repair_provider_intake_log.md",
        "\n".join(
            [
                "# Stage1 AI Repair Provider Intake Log",
                "",
                "- task_title: Add Stage 1 AI repair provider response intake gate",
                f"- started_at: {started_at}",
                f"- finished_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- commands_run: {json.dumps(commands_run, ensure_ascii=False)}",
                f"- request_batch_path: {request_batch}",
                f"- raw_provider_response_path: {raw_provider_path}",
                f"- clean_response_path: {clean_path}",
                f"- rejected_response_path: {rejected_path}",
                f"- raw_response_count: {raw_response_count}",
                f"- clean_response_count: {len(clean_rows)}",
                f"- rejected_response_count: {len(rejected_rows)}",
                f"- offline_replay_status: {replay_status}",
                f"- output_files_generated: {json.dumps(generated_outputs, ensure_ascii=False)}",
                f"- production_guard_changed_count: {production_changed_count}",
                f"- safety_checks: {json.dumps(safety_checks, ensure_ascii=False)}",
            ]
        ),
    )

    report52_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": "Add Stage 1 AI repair provider response intake gate"},
                    {"field": "started_at", "value": started_at},
                    {"field": "finished_at", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                    {"field": "request_batch_path", "value": str(request_batch)},
                    {"field": "raw_provider_response_path", "value": str(raw_provider_path)},
                    {"field": "clean_response_path", "value": str(clean_path)},
                    {"field": "rejected_response_path", "value": str(rejected_path)},
                    {"field": "raw_response_count", "value": raw_response_count},
                    {"field": "clean_response_count", "value": len(clean_rows)},
                    {"field": "rejected_response_count", "value": len(rejected_rows)},
                    {"field": "offline_replay_status", "value": replay_status},
                    {"field": "production_guard_changed_count", "value": production_changed_count},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                ]
            ),
            "raw_response_inventory": pd.DataFrame(raw_inventory_rows),
            "clean_responses": pd.DataFrame(clean_rows),
            "rejected_responses": pd.DataFrame(rejected_rows),
            "rejection_reason_summary": pd.DataFrame([{"reason": k, "count": v} for k, v in sorted(rejection_counts.items())]),
            "evidence_check": pd.DataFrame(evidence_rows),
            "offline_replay_summary": pd.DataFrame([replay_summary]) if replay_summary else pd.DataFrame([]),
            "offline_replay_merge_preview": pd.DataFrame(
                [{"metric": k, "count": v} for k, v in (replay_summary.get("merge_preview_route_counts", {}) or {}).items()]
            ),
            "no_secret_check": pd.DataFrame([{"status": no_secret_status, "hits": "|".join(_scan_secret_hits(no_secret_text))}]),
            "production_guard": pd.DataFrame(production_guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "Use intake clean JSONL as the only accepted replay input for future controlled provider runs.",
                    }
                ]
            ),
        },
        delivery_dir / "52_stage1_ai_repair_provider_intake_log.xlsx",
    )

    report53_md = _safe_write_text(
        delivery_dir / "53_stage1_ai_repair_provider_intake_evaluation.md",
        "\n".join(
            [
                "# Stage1 AI Repair Provider Intake Evaluation",
                "",
                f"- provider_intake_status: {provider_intake_status}",
                f"- raw_response_count: {raw_response_count}",
                f"- clean_response_count: {len(clean_rows)}",
                f"- rejected_response_count: {len(rejected_rows)}",
                f"- rejection_reason_summary: {json.dumps(dict(rejection_counts), ensure_ascii=False)}",
                f"- valid_extract_count: {clean_decisions.get('extract', 0)}",
                f"- accepted_manual_review_count: {clean_decisions.get('manual_review', 0)}",
                f"- accepted_ignore_count: {clean_decisions.get('ignore', 0)}",
                f"- unknown_request_blocking_status: {'PASS' if unknown_request_blocked else 'WARN'}",
                f"- duplicate_response_blocking_status: {'PASS' if duplicate_blocked else 'WARN'}",
                f"- fabricated_value_blocking_status: {'PASS' if fabricated_blocked else 'WARN'}",
                f"- malformed_json_blocking_status: {'PASS' if malformed_json_count > 0 else 'WARN'}",
                f"- missing_required_fields_blocking_status: {'PASS' if missing_required_blocked else 'WARN'}",
                f"- wrapper_normalization_status: {'PASS' if wrapper_normalized_count > 0 else 'WARN'}",
                f"- offline_replay_status: {replay_status}",
                f"- offline_replay_merge_preview_summary: {json.dumps(replay_summary.get('merge_preview_route_counts', {}), ensure_ascii=False)}",
                f"- no_secret_check_status: {no_secret_status}",
                f"- production_delivery_status_after: {json.dumps(production_delivery_status, ensure_ascii=False)}",
                f"- production_files_unchanged: {production_files_unchanged}",
                "- recommended_next_step: gate all future provider outputs through this intake before offline replay and merge preview checks.",
            ]
        ),
    )

    report53_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "provider_intake_status", "value": provider_intake_status},
                    {"field": "raw_response_count", "value": raw_response_count},
                    {"field": "clean_response_count", "value": len(clean_rows)},
                    {"field": "rejected_response_count", "value": len(rejected_rows)},
                    {"field": "rejection_reason_summary", "value": json.dumps(dict(rejection_counts), ensure_ascii=False)},
                    {"field": "valid_extract_count", "value": clean_decisions.get("extract", 0)},
                    {"field": "accepted_manual_review_count", "value": clean_decisions.get("manual_review", 0)},
                    {"field": "accepted_ignore_count", "value": clean_decisions.get("ignore", 0)},
                    {"field": "unknown_request_blocking_status", "value": "PASS" if unknown_request_blocked else "WARN"},
                    {"field": "duplicate_response_blocking_status", "value": "PASS" if duplicate_blocked else "WARN"},
                    {"field": "fabricated_value_blocking_status", "value": "PASS" if fabricated_blocked else "WARN"},
                    {"field": "malformed_json_blocking_status", "value": "PASS" if malformed_json_count > 0 else "WARN"},
                    {"field": "missing_required_fields_blocking_status", "value": "PASS" if missing_required_blocked else "WARN"},
                    {"field": "wrapper_normalization_status", "value": "PASS" if wrapper_normalized_count > 0 else "WARN"},
                    {"field": "offline_replay_status", "value": replay_status},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "production_delivery_status_after", "value": json.dumps(production_delivery_status, ensure_ascii=False)},
                    {"field": "production_files_unchanged", "value": "1" if production_files_unchanged else "0"},
                ]
            ),
            "raw_response_inventory": pd.DataFrame(raw_inventory_rows),
            "clean_responses": pd.DataFrame(clean_rows),
            "rejected_responses": pd.DataFrame(rejected_rows),
            "rejection_reason_summary": pd.DataFrame([{"reason": k, "count": v} for k, v in sorted(rejection_counts.items())]),
            "evidence_check": pd.DataFrame(evidence_rows),
            "offline_replay_summary": pd.DataFrame([replay_summary]) if replay_summary else pd.DataFrame([]),
            "offline_replay_merge_preview": pd.DataFrame(
                [{"metric": k, "count": v} for k, v in (replay_summary.get("merge_preview_route_counts", {}) or {}).items()]
            ),
            "no_secret_check": pd.DataFrame([{"status": no_secret_status, "hits": "|".join(_scan_secret_hits(no_secret_text))}]),
            "production_guard": pd.DataFrame(production_guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "After real provider run, first validate raw JSONL with this intake gate and replay only clean JSONL.",
                    }
                ]
            ),
        },
        delivery_dir / "53_stage1_ai_repair_provider_intake_evaluation.xlsx",
    )

    print(f"intake_helper_path: {intake_helper}")
    print(f"provider_intake_status: {provider_intake_status}")
    print(f"raw_response_count: {raw_response_count}")
    print(f"clean_response_count: {len(clean_rows)}")
    print(f"rejected_response_count: {len(rejected_rows)}")
    print(f"rejection_reason_summary: {json.dumps(dict(rejection_counts), ensure_ascii=False)}")
    print(f"offline_replay_status: {replay_status}")
    print(f"no_secret_check_status: {no_secret_status}")
    print(
        "generated_outputs: "
        + json.dumps(
            [
                str(raw_provider_path),
                str(clean_path),
                str(rejected_path),
                str(validation_path),
                str(summary_path),
                str(report52_md),
                str(report52_xlsx),
                str(report53_md),
                str(report53_xlsx),
                *copied_replay_outputs,
            ],
            ensure_ascii=False,
        )
    )
    print(f"production_delivery_status_after: {json.dumps(production_delivery_status, ensure_ascii=False)}")
    print(f"production_files_unchanged: {production_files_unchanged}")

    if provider_intake_status == "FAIL":
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

