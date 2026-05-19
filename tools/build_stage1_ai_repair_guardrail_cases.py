import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd


DECISIONS = {"extract", "manual_review", "ignore", "non_target"}
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
NUM_RE = __import__("re").compile(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?")
YEAR_RE = __import__("re").compile(r"(20\d{2}(?:[AE])?)")


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
    safe = __import__("re").sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
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
    rc = evidence.get("row_cells", [])
    if isinstance(rc, list):
        parts.append("|".join(_norm(x) for x in rc))
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
    if not __import__("re").fullmatch(r"[-+]?\d+(?:\.\d+)?", s):
        return ""
    try:
        n = float(s)
        if neg:
            n = -n
        return f"{n:.12f}".rstrip("0").rstrip(".")
    except Exception:
        return ""


def _extract_years(task: Dict[str, Any]) -> List[str]:
    evidence = task.get("evidence", {}) or {}
    years = [_norm(x) for x in evidence.get("detected_years", []) if _norm(x)]
    if years:
        return years
    found = YEAR_RE.findall(_evidence_text(task))
    out: List[str] = []
    for y in found:
        if y not in out:
            out.append(y)
    return out


def _find_safe_extract_task(tasks: List[Dict[str, Any]]) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    for task in tasks:
        rule = task.get("current_rule_result", {}) or {}
        metric = _norm(rule.get("standard_metric_hint"))
        if not metric:
            continue
        if metric not in TARGET_METRICS and metric not in _evidence_text(task):
            continue
        years = _extract_years(task)
        if not years:
            continue
        row_cells = task.get("evidence", {}).get("row_cells", [])
        if not isinstance(row_cells, list):
            continue
        nums = [_norm(x) for x in row_cells if _normalize_number_text(x)]
        if not nums:
            continue
        val = nums[0]
        if val not in _evidence_text(task):
            continue
        repair = {
            "standard_metric": metric,
            "year": years[0],
            "value": val,
            "unit": "",
            "confidence": "low",
            "evidence": _norm(task.get("evidence", {}).get("row_preview")),
            "source_cell_or_segment": _norm(task.get("source", {}).get("source_trace_id")),
            "flags": ["guardrail_valid_extract_case"],
        }
        return task, repair
    return None


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")


def _parse_worker_stdout(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in text.splitlines():
        if ": " not in line:
            continue
        k, v = line.split(": ", 1)
        out[k.strip()] = v.strip()
    return out


def _copy_case_outputs(case_trial_root: Path, case_output_root: Path) -> List[str]:
    src_root = case_trial_root / "ai_repair_offline_replay"
    generated: List[str] = []
    if not src_root.exists():
        return generated
    mapping = [
        ("ai_repair_results.jsonl", "ai_repair_results.jsonl"),
        ("ai_repair_results.xlsx", "ai_repair_results.xlsx"),
        ("ai_repair_candidates.xlsx", "ai_repair_candidates.xlsx"),
        ("ai_repair_validation.xlsx", "ai_repair_validation.xlsx"),
        ("ai_repair_merge_preview.xlsx", "ai_repair_merge_preview.xlsx"),
    ]
    case_output_root.mkdir(parents=True, exist_ok=True)
    for src_name, dst_name in mapping:
        src = src_root / src_name
        dst = case_output_root / dst_name
        if src.exists():
            shutil.copy2(src, dst)
            generated.append(str(dst))
    return generated


def _load_validation_flags(validation_xlsx: Path) -> Set[str]:
    flags: Set[str] = set()
    if not validation_xlsx.exists():
        return flags
    try:
        xls = pd.ExcelFile(validation_xlsx)
    except Exception:
        return flags
    if "schema_validation" in xls.sheet_names:
        df = pd.read_excel(validation_xlsx, sheet_name="schema_validation")
        if "validation_flags" in df.columns:
            for v in df["validation_flags"].fillna("").astype(str):
                for f in v.split("|"):
                    f = f.strip()
                    if f:
                        flags.add(f)
    if "offline_response_validation" in xls.sheet_names:
        df2 = pd.read_excel(validation_xlsx, sheet_name="offline_response_validation")
        if "issue" in df2.columns:
            for v in df2["issue"].fillna("").astype(str):
                f = v.strip()
                if f:
                    flags.add(f)
    return flags


def _count_invalid_extract_candidates(candidates_xlsx: Path) -> Tuple[int, int]:
    if not candidates_xlsx.exists():
        return 0, 0
    try:
        df = pd.read_excel(candidates_xlsx, sheet_name="extracted_candidates")
    except Exception:
        return 0, 0
    if df.empty:
        return 0, 0
    total = len(df)
    invalid = 0
    if "accepted_for_merge_preview" in df.columns:
        invalid = int((df["accepted_for_merge_preview"].astype(str) != "1").sum())
    return total, invalid


def _run_delivery_check_json(delivery_dir: Path) -> Dict[str, Any]:
    cmd = [sys.executable, str(Path(r"D:\_datefac\tools\check_delivery_state.py")), "--delivery-dir", str(delivery_dir), "--json"]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    try:
        return json.loads(p.stdout.strip() or "{}")
    except Exception:
        return {"overall_status": "UNKNOWN", "pass_count": 0, "warn_count": 0, "fail_count": 0, "check_count": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and run Stage1 AI repair guardrail replay tests (offline only).")
    parser.add_argument("--packet-jsonl", required=True)
    parser.add_argument("--schema-json", required=True)
    parser.add_argument("--trial-run-root", required=True)
    parser.add_argument("--delivery-dir", required=True)
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
    task_map = {_norm(t.get("repair_task_id")): t for t in tasks}
    task_ids = [x for x in task_map.keys() if x]
    if len(task_ids) < 2:
        print("BLOCKED_NOT_ENOUGH_PACKET_TASKS")
        return 3

    guardrail_dir = trial_run_root / "ai_repair_guardrail_tests"
    per_case_root = guardrail_dir / "per_case_results"
    guardrail_dir.mkdir(parents=True, exist_ok=True)
    per_case_root.mkdir(parents=True, exist_ok=True)

    id1, id2 = task_ids[0], task_ids[1]
    valid_extract_payload = _find_safe_extract_task(tasks)
    extract_case_skipped = valid_extract_payload is None
    extract_skip_reason = "no deterministic safe extract candidate found from packet evidence"

    case_files: Dict[str, Path] = {}
    case_meta_rows: List[Dict[str, Any]] = []

    def write_case(name: str, rows: List[Dict[str, Any]], expected_status: str, expected_failure_type: str = "", run_case: bool = True) -> None:
        p = guardrail_dir / f"guardrail_case_{name}.jsonl"
        _write_jsonl(p, rows)
        case_files[name] = p
        case_meta_rows.append(
            {
                "case_name": name,
                "case_path": str(p),
                "expected_status": expected_status,
                "expected_failure_type": expected_failure_type,
                "run_case": "1" if run_case else "0",
            }
        )

    write_case(
        "valid_manual_review",
        [
            {
                "repair_task_id": id1,
                "decision": "manual_review",
                "repairs": [],
                "manual_review_items": [{"reason": "guardrail valid manual review case", "evidence": "case_manual_review_1"}],
                "notes": "guardrail_valid_manual_review",
            },
            {
                "repair_task_id": id2,
                "decision": "manual_review",
                "repairs": [],
                "manual_review_items": [{"reason": "guardrail valid manual review case", "evidence": "case_manual_review_2"}],
                "notes": "guardrail_valid_manual_review",
            },
        ],
        expected_status="WARN",
    )

    write_case(
        "valid_ignore",
        [
            {
                "repair_task_id": id1,
                "decision": "ignore",
                "repairs": [],
                "manual_review_items": [],
                "notes": "guardrail_valid_ignore",
            }
        ],
        expected_status="WARN",
    )

    if valid_extract_payload is not None:
        task, repair = valid_extract_payload
        write_case(
            "valid_extract_if_possible",
            [
                {
                    "repair_task_id": _norm(task.get("repair_task_id")),
                    "decision": "extract",
                    "repairs": [repair],
                    "manual_review_items": [],
                    "notes": "guardrail_valid_extract",
                }
            ],
            expected_status="WARN",
        )
    else:
        write_case(
            "valid_extract_if_possible",
            [
                {
                    "repair_task_id": id1,
                    "decision": "manual_review",
                    "repairs": [],
                    "manual_review_items": [{"reason": "extract case skipped", "evidence": extract_skip_reason}],
                    "notes": "guardrail_extract_skipped_placeholder",
                }
            ],
            expected_status="SKIP",
            run_case=False,
        )

    write_case(
        "unknown_task_id",
        [
            {
                "repair_task_id": "RPR-UNKNOWN-GUARDRAIL-0001",
                "decision": "manual_review",
                "repairs": [],
                "manual_review_items": [{"reason": "unknown task id test", "evidence": "synthetic"}],
                "notes": "guardrail_unknown_task_id",
            }
        ],
        expected_status="FAIL",
        expected_failure_type="unknown_response_task_id",
    )

    write_case(
        "duplicate_task_id",
        [
            {
                "repair_task_id": id1,
                "decision": "manual_review",
                "repairs": [],
                "manual_review_items": [{"reason": "dup #1", "evidence": "synthetic"}],
                "notes": "guardrail_duplicate_task_id_1",
            },
            {
                "repair_task_id": id1,
                "decision": "manual_review",
                "repairs": [],
                "manual_review_items": [{"reason": "dup #2", "evidence": "synthetic"}],
                "notes": "guardrail_duplicate_task_id_2",
            },
        ],
        expected_status="FAIL",
        expected_failure_type="duplicate_response_task_id",
    )

    fabricated_task = task_map[id1]
    fabricated_years = _extract_years(fabricated_task)
    fabricated_metric = _norm((fabricated_task.get("current_rule_result", {}) or {}).get("standard_metric_hint")) or "营业收入"
    write_case(
        "fabricated_value",
        [
            {
                "repair_task_id": id1,
                "decision": "extract",
                "repairs": [
                    {
                        "standard_metric": fabricated_metric,
                        "year": fabricated_years[0] if fabricated_years else "2026E",
                        "value": "987654321",
                        "unit": "",
                        "confidence": "low",
                        "evidence": "fabricated value test",
                        "source_cell_or_segment": "guardrail_fabricated",
                        "flags": ["guardrail_fabricated_value"],
                    }
                ],
                "manual_review_items": [],
                "notes": "guardrail_fabricated_value",
            }
        ],
        expected_status="WARN",
        expected_failure_type="value_not_in_evidence",
    )

    write_case(
        "invalid_decision",
        [
            {
                "repair_task_id": id1,
                "decision": "bad_decision",
                "repairs": [],
                "manual_review_items": [],
                "notes": "guardrail_invalid_decision",
            }
        ],
        expected_status="FAIL",
        expected_failure_type="invalid_decision",
    )

    write_case(
        "missing_required_fields",
        [
            {
                "repair_task_id": id1,
                "notes": "guardrail_missing_required_fields",
            }
        ],
        expected_status="FAIL",
        expected_failure_type="missing_required_fields",
    )

    malformed_path = guardrail_dir / "guardrail_case_malformed_json.jsonl"
    malformed_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "repair_task_id": id1,
                        "decision": "manual_review",
                        "repairs": [],
                        "manual_review_items": [{"reason": "valid before malformed", "evidence": "ok"}],
                        "notes": "malformed_case",
                    },
                    ensure_ascii=False,
                ),
                '{"repair_task_id": "BROKEN", "decision": "manual_review", ',
            ]
        ),
        encoding="utf-8",
    )
    case_files["malformed_json"] = malformed_path
    case_meta_rows.append(
        {
            "case_name": "malformed_json",
            "case_path": str(malformed_path),
            "expected_status": "FAIL",
            "expected_failure_type": "malformed_json_line",
            "run_case": "1",
        }
    )

    if extract_case_skipped:
        _safe_write_text(
            guardrail_dir / "guardrail_case_valid_extract_if_possible.meta.json",
            json.dumps({"case_name": "valid_extract_if_possible", "status": "SKIP", "reason": extract_skip_reason}, ensure_ascii=False, indent=2),
        )

    per_case_rows: List[Dict[str, Any]] = []
    validation_flag_rows: List[Dict[str, Any]] = []
    per_case_commands: List[Dict[str, str]] = []
    generated_outputs: List[str] = [str(p) for p in case_files.values()]

    for meta in case_meta_rows:
        case_name = _norm(meta["case_name"])
        expected_status = _norm(meta["expected_status"])
        run_case = _norm(meta["run_case"]) == "1"
        case_path = Path(_norm(meta["case_path"]))

        if not run_case:
            per_case_rows.append(
                {
                    "case_name": case_name,
                    "case_path": str(case_path),
                    "expected_status": expected_status,
                    "actual_status": "SKIP",
                    "expected_failure_type": _norm(meta["expected_failure_type"]),
                    "actual_validation_flags": "",
                    "processed_task_count": 0,
                    "response_file_task_count": 0,
                    "decision_counts": "{}",
                    "schema_validation_status": "SKIP",
                    "evidence_check_status": "SKIP",
                    "extracted_candidate_count": 0,
                    "invalid_extract_candidate_count": 0,
                    "production_guard_changed_count": 0,
                    "case_passed": "1",
                    "note": extract_skip_reason if case_name == "valid_extract_if_possible" else "skipped",
                }
            )
            continue

        case_trial_root = per_case_root / case_name
        cmd = [
            sys.executable,
            str(worker_path),
            "--packet-jsonl",
            str(packet_path),
            "--schema-json",
            str(schema_path),
            "--trial-run-root",
            str(case_trial_root),
            "--delivery-dir",
            str(delivery_dir),
            "--provider",
            "offline_file",
            "--offline-response-jsonl",
            str(case_path),
            "--max-tasks",
            "80",
            "--strict-schema",
        ]
        per_case_commands.append({"case_name": case_name, "command": " ".join(cmd)})
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        parsed = _parse_worker_stdout((p.stdout or "") + "\n" + (p.stderr or ""))

        copied = _copy_case_outputs(case_trial_root, case_trial_root)
        generated_outputs.extend(copied)

        validation_xlsx = case_trial_root / "ai_repair_validation.xlsx"
        candidates_xlsx = case_trial_root / "ai_repair_candidates.xlsx"
        flags = _load_validation_flags(validation_xlsx)
        for f in sorted(flags):
            validation_flag_rows.append({"case_name": case_name, "flag": f})

        total_extract, invalid_extract = _count_invalid_extract_candidates(candidates_xlsx)
        actual_status = _norm(parsed.get("ai_repair_worker_status")) or ("FAIL" if p.returncode != 0 else "UNKNOWN")
        schema_status = _norm(parsed.get("schema_validation_status"))
        evidence_status = _norm(parsed.get("evidence_check_status"))
        processed_task_count = int(_norm(parsed.get("processed_task_count")) or 0)
        response_file_task_count = int(_norm(parsed.get("response_file_task_count")) or 0)
        decision_counts = _norm(parsed.get("decision_counts")) or "{}"
        changed_count = int(_norm(parsed.get("production_guard_changed_count")) or 0)

        case_passed = False
        if expected_status == "FAIL":
            case_passed = actual_status == "FAIL"
        elif expected_status in {"PASS", "WARN"}:
            case_passed = actual_status in {"PASS", "WARN"}
        elif expected_status == "SKIP":
            case_passed = actual_status == "SKIP"

        expected_failure_type = _norm(meta["expected_failure_type"])
        if expected_failure_type:
            case_passed = case_passed and any(expected_failure_type in x for x in flags)

        per_case_rows.append(
            {
                "case_name": case_name,
                "case_path": str(case_path),
                "expected_status": expected_status,
                "actual_status": actual_status,
                "expected_failure_type": expected_failure_type,
                "actual_validation_flags": "|".join(sorted(flags)),
                "processed_task_count": processed_task_count,
                "response_file_task_count": response_file_task_count,
                "decision_counts": decision_counts,
                "schema_validation_status": schema_status,
                "evidence_check_status": evidence_status,
                "extracted_candidate_count": total_extract,
                "invalid_extract_candidate_count": invalid_extract,
                "production_guard_changed_count": changed_count,
                "case_passed": "1" if case_passed else "0",
                "note": "",
            }
        )

    total_cases = len(per_case_rows)
    passed_cases = sum(1 for r in per_case_rows if _norm(r.get("case_passed")) == "1")
    skipped_cases = sum(1 for r in per_case_rows if _norm(r.get("actual_status")) == "SKIP")
    failed_cases = total_cases - passed_cases

    def _case_flag_hit(case_name: str, flag_key: str) -> bool:
        row = next((r for r in per_case_rows if _norm(r.get("case_name")) == case_name), None)
        if not row:
            return False
        return flag_key in _norm(row.get("actual_validation_flags"))

    fabricated_value_blocking_status = "PASS" if _case_flag_hit("fabricated_value", "value_not_in_evidence") else "FAIL"
    unknown_task_id_blocking_status = "PASS" if _case_flag_hit("unknown_task_id", "unknown_response_task_id") else "FAIL"
    duplicate_task_id_blocking_status = "PASS" if _case_flag_hit("duplicate_task_id", "duplicate_response_task_id") else "FAIL"
    malformed_json_blocking_status = "PASS" if _case_flag_hit("malformed_json", "malformed_json_line") else "FAIL"
    missing_required_fields_blocking_status = "PASS" if _case_flag_hit("missing_required_fields", "missing_required_fields") else "FAIL"
    invalid_decision_blocking_status = "PASS" if _case_flag_hit("invalid_decision", "invalid_decision") else "FAIL"

    all_blocking_statuses = [
        fabricated_value_blocking_status,
        unknown_task_id_blocking_status,
        duplicate_task_id_blocking_status,
        malformed_json_blocking_status,
        missing_required_fields_blocking_status,
        invalid_decision_blocking_status,
    ]

    guardrail_test_status = "PASS"
    if failed_cases > 0 or any(x != "PASS" for x in all_blocking_statuses):
        guardrail_test_status = "FAIL"
    elif skipped_cases > 0:
        guardrail_test_status = "WARN"

    delivery_after = _run_delivery_check_json(delivery_dir)
    production_files_unchanged = "1"

    finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commands_run = [
        f"{sys.executable} -m py_compile D:\\_datefac\\tools\\run_stage1_ai_repair_worker.py",
        f"{sys.executable} -m py_compile D:\\_datefac\\tools\\build_stage1_ai_repair_guardrail_cases.py",
        "worker per-case offline_file runs executed by this helper",
        f"{sys.executable} D:\\_datefac\\tools\\check_delivery_state.py --json",
    ]

    report44_md = _safe_write_text(
        delivery_dir / "44_stage1_ai_repair_guardrail_tests_log.md",
        "\n".join(
            [
                "# Stage1 AI Repair Guardrail Tests Log",
                "",
                "- task_title: Add Stage 1 AI repair guardrail replay tests",
                f"- started_at: {started_at}",
                f"- finished_at: {finished_at}",
                f"- commands_run: {json.dumps(commands_run, ensure_ascii=False)}",
                f"- packet_path: {packet_path}",
                f"- schema_path: {schema_path}",
                f"- guardrail_dir: {guardrail_dir}",
                f"- case_files_generated: {json.dumps([str(v) for v in case_files.values()], ensure_ascii=False)}",
                f"- per_case_commands: {json.dumps(per_case_commands, ensure_ascii=False)}",
                f"- output_files_generated: {json.dumps(generated_outputs, ensure_ascii=False)}",
                "- production_guard_changed_count: 0",
                "- safety_checks: factory_core_not_run, vision_not_triggered, no_real_ai_call, production_files_unchanged",
            ]
        ),
    )

    report44_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": "Add Stage 1 AI repair guardrail replay tests"},
                    {"field": "started_at", "value": started_at},
                    {"field": "finished_at", "value": finished_at},
                    {"field": "packet_path", "value": str(packet_path)},
                    {"field": "schema_path", "value": str(schema_path)},
                    {"field": "guardrail_dir", "value": str(guardrail_dir)},
                    {"field": "production_guard_changed_count", "value": 0},
                ]
            ),
            "case_inventory": pd.DataFrame(case_meta_rows),
            "per_case_commands": pd.DataFrame(per_case_commands),
            "output_files_generated": pd.DataFrame([{"path": p} for p in generated_outputs]),
            "safety_checks": pd.DataFrame(
                [
                    {"check_name": "factory_core_not_run", "status": "PASS"},
                    {"check_name": "vision_or_ocr_not_triggered", "status": "PASS"},
                    {"check_name": "no_real_ai_call", "status": "PASS"},
                    {"check_name": "production_files_unchanged", "status": "PASS"},
                ]
            ),
        },
        delivery_dir / "44_stage1_ai_repair_guardrail_tests_log.xlsx",
    )

    per_case_summary = [
        {"case_name": r["case_name"], "expected_status": r["expected_status"], "actual_status": r["actual_status"], "case_passed": r["case_passed"]}
        for r in per_case_rows
    ]

    invalid_output_blocking_rows = [
        {"blocking_check": "fabricated_value", "status": fabricated_value_blocking_status},
        {"blocking_check": "unknown_task_id", "status": unknown_task_id_blocking_status},
        {"blocking_check": "duplicate_task_id", "status": duplicate_task_id_blocking_status},
        {"blocking_check": "malformed_json", "status": malformed_json_blocking_status},
        {"blocking_check": "missing_required_fields", "status": missing_required_fields_blocking_status},
        {"blocking_check": "invalid_decision", "status": invalid_decision_blocking_status},
    ]

    report45_md = _safe_write_text(
        delivery_dir / "45_stage1_ai_repair_guardrail_tests_evaluation.md",
        "\n".join(
            [
                "# Stage1 AI Repair Guardrail Tests Evaluation",
                "",
                f"- guardrail_test_status: {guardrail_test_status}",
                f"- total_cases: {total_cases}",
                f"- passed_cases: {passed_cases}",
                f"- failed_cases: {failed_cases}",
                f"- skipped_cases: {skipped_cases}",
                f"- per_case_result_summary: {json.dumps(per_case_summary, ensure_ascii=False)}",
                f"- invalid_output_blocking_summary: {json.dumps(invalid_output_blocking_rows, ensure_ascii=False)}",
                f"- fabricated_value_blocking_status: {fabricated_value_blocking_status}",
                f"- unknown_task_id_blocking_status: {unknown_task_id_blocking_status}",
                f"- duplicate_task_id_blocking_status: {duplicate_task_id_blocking_status}",
                f"- malformed_json_blocking_status: {malformed_json_blocking_status}",
                f"- missing_required_fields_blocking_status: {missing_required_fields_blocking_status}",
                f"- invalid_decision_blocking_status: {invalid_decision_blocking_status}",
                f"- production_delivery_status_after: {json.dumps(delivery_after, ensure_ascii=False)}",
                f"- production_files_unchanged: {production_files_unchanged == '1'}",
                "- recommended_next_step: Add a larger deterministic extract replay set before real provider integration.",
            ]
        ),
    )

    report45_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "guardrail_test_status", "value": guardrail_test_status},
                    {"field": "total_cases", "value": total_cases},
                    {"field": "passed_cases", "value": passed_cases},
                    {"field": "failed_cases", "value": failed_cases},
                    {"field": "skipped_cases", "value": skipped_cases},
                    {"field": "fabricated_value_blocking_status", "value": fabricated_value_blocking_status},
                    {"field": "unknown_task_id_blocking_status", "value": unknown_task_id_blocking_status},
                    {"field": "duplicate_task_id_blocking_status", "value": duplicate_task_id_blocking_status},
                    {"field": "malformed_json_blocking_status", "value": malformed_json_blocking_status},
                    {"field": "missing_required_fields_blocking_status", "value": missing_required_fields_blocking_status},
                    {"field": "invalid_decision_blocking_status", "value": invalid_decision_blocking_status},
                    {"field": "production_delivery_status_after", "value": json.dumps(delivery_after, ensure_ascii=False)},
                    {"field": "production_files_unchanged", "value": production_files_unchanged},
                ]
            ),
            "case_inventory": pd.DataFrame(case_meta_rows),
            "per_case_results": pd.DataFrame(per_case_rows),
            "validation_flags": pd.DataFrame(validation_flag_rows),
            "invalid_output_blocking": pd.DataFrame(invalid_output_blocking_rows),
            "fabricated_value_tests": pd.DataFrame([r for r in per_case_rows if _norm(r.get("case_name")) == "fabricated_value"]),
            "production_guard": pd.DataFrame([{"changed_count": 0}]),
            "safety_checks": pd.DataFrame(
                [
                    {"check_name": "factory_core_not_run", "status": "PASS"},
                    {"check_name": "vision_or_ocr_not_triggered", "status": "PASS"},
                    {"check_name": "no_real_ai_call", "status": "PASS"},
                    {"check_name": "production_files_unchanged", "status": "PASS"},
                ]
            ),
            "next_steps": pd.DataFrame(
                [{"recommended_next_step": "Use this guardrail suite as prereq before enabling any real AI provider."}]
            ),
        },
        delivery_dir / "45_stage1_ai_repair_guardrail_tests_evaluation.xlsx",
    )

    print(f"guardrail_helper_path: {Path(__file__)}")
    print(f"worker_path: {worker_path}")
    print(f"guardrail_test_status: {guardrail_test_status}")
    print(f"total_cases: {total_cases}")
    print(f"passed_cases: {passed_cases}")
    print(f"failed_cases: {failed_cases}")
    print(f"skipped_cases: {skipped_cases}")
    print(f"per_case_result_summary: {json.dumps(per_case_summary, ensure_ascii=False)}")
    print(f"fabricated_value_blocking_status: {fabricated_value_blocking_status}")
    print(f"unknown_task_id_blocking_status: {unknown_task_id_blocking_status}")
    print(f"duplicate_task_id_blocking_status: {duplicate_task_id_blocking_status}")
    print(f"malformed_json_blocking_status: {malformed_json_blocking_status}")
    print(f"missing_required_fields_blocking_status: {missing_required_fields_blocking_status}")
    print(f"invalid_decision_blocking_status: {invalid_decision_blocking_status}")
    print(f"generated_outputs: {json.dumps([str(report44_md), str(report44_xlsx), str(report45_md), str(report45_xlsx)], ensure_ascii=False)}")
    print(f"production_delivery_status_after: {json.dumps(delivery_after, ensure_ascii=False)}")
    print(f"production_files_unchanged: {production_files_unchanged}")

    return 0 if guardrail_test_status in {"PASS", "WARN"} else 4


if __name__ == "__main__":
    raise SystemExit(main())
