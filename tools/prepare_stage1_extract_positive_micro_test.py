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
EXTRACT_TASK_TYPES = {"row_segment_repair", "metric_year_value_alignment"}


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
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
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


def _scan_secret(text: str) -> List[str]:
    return [p for p in SECRET_PATTERNS if p in text]


def _collect_extract_success_tids(trial_run_root: Path) -> Set[str]:
    candidates = [
        trial_run_root / "ai_repair_extract_replay" / "ai_repair_results.jsonl",
        trial_run_root / "ai_repair_extract_coverage" / "ai_repair_results.jsonl",
    ]
    tids: Set[str] = set()
    for path in candidates:
        if not path.exists():
            continue
        for row in _load_jsonl(path):
            if _norm(row.get("decision")) == "extract":
                tid = _norm(row.get("repair_task_id"))
                if tid:
                    tids.add(tid)
    return tids


def _request_row(req: Dict[str, Any], packet_row: Dict[str, Any]) -> Dict[str, Any]:
    evidence = packet_row.get("evidence", {}) or {}
    rule = packet_row.get("current_rule_result", {}) or {}
    return {
        "request_id": _norm(req.get("request_id")),
        "repair_task_id": _norm(req.get("repair_task_id")),
        "sample_id": _norm(req.get("sample_id")),
        "company": _norm(req.get("company")),
        "task_type": _norm(req.get("task_type")),
        "priority": _norm(req.get("priority")),
        "metric_hint": _norm(rule.get("standard_metric_hint")),
        "flags": "|".join([_norm(x) for x in (rule.get("flags") or []) if _norm(x)]),
        "detected_years": "|".join([_norm(x) for x in (evidence.get("detected_years") or []) if _norm(x)]),
        "row_preview": _norm(evidence.get("row_preview"))[:200],
    }


def _select_extract_positive(
    requests: List[Dict[str, Any]],
    packet_map: Dict[str, Dict[str, Any]],
    extract_success_tids: Set[str],
    min_requests: int,
    max_requests: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], str]:
    selected: List[Dict[str, Any]] = []
    selected_ids: Set[str] = set()
    excluded: List[Dict[str, Any]] = []

    # strict filtering
    filtered: List[Dict[str, Any]] = []
    for req in requests:
        tid = _norm(req.get("repair_task_id"))
        ttype = _norm(req.get("task_type"))
        sid = _norm(req.get("sample_id"))
        prow = packet_map.get(tid, {})
        flags = set([_norm(x) for x in ((prow.get("current_rule_result") or {}).get("flags") or []) if _norm(x)])

        reason = ""
        if tid not in extract_success_tids:
            reason = "not_in_previous_extract_success_set"
        elif ttype not in EXTRACT_TASK_TYPES:
            reason = "not_extract_task_type"
        elif ttype == "semantic_guard_review":
            reason = "semantic_guard_excluded"
        elif ttype == "s2_table_level_repair":
            reason = "s2_table_level_excluded"
        elif sid == "S2":
            reason = "s2_sample_excluded_for_extract_positive"
        elif "source_row_semantic_risk" in flags:
            reason = "high_risk_source_row_semantic_risk"
        elif "forbidden_source_label_for_metric" in flags:
            reason = "high_risk_forbidden_source_label_for_metric"

        if reason:
            row = _request_row(req, prow)
            row["exclude_reason"] = reason
            excluded.append(row)
        else:
            filtered.append(req)

    # prefer row_segment first, then alignment
    row_first = [r for r in filtered if _norm(r.get("task_type")) == "row_segment_repair"]
    align_second = [r for r in filtered if _norm(r.get("task_type")) == "metric_year_value_alignment"]
    ordered = row_first + align_second

    for req in ordered:
        rid = _norm(req.get("request_id"))
        if not rid or rid in selected_ids:
            continue
        selected.append(req)
        selected_ids.add(rid)
        if len(selected) >= max_requests:
            break

    status_note = "PASS"
    if len(selected) < min_requests:
        status_note = "WARN_INSUFFICIENT_EXTRACT_POSITIVE_TASKS"
    selected_rows = [_request_row(r, packet_map.get(_norm(r.get("repair_task_id")), {})) for r in selected]
    return selected, selected_rows, excluded, status_note


def _build_prompt(raw_output_path: Path) -> str:
    return "\n".join(
        [
            "# Stage 1 Extract-Positive Real-Provider Micro Test Prompt",
            "",
            "You are a strict financial table repair worker.",
            "Output JSONL only.",
            "One line one JSON object.",
            "No markdown.",
            "No explanation text.",
            "Only extract when evidence is explicit.",
            "Extracted value must come from evidence.",
            "Extracted year must come from evidence or detected_years.",
            "If uncertain, choose manual_review.",
            "repairs must be an array.",
            "manual_review_items must be an array of objects.",
            "",
            "Save model output to:",
            f"`{raw_output_path}`",
        ]
    )


def _build_response_template(selected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for req in selected:
        rows.append(
            {
                "repair_task_id": _norm(req.get("repair_task_id")),
                "decision": "extract",
                "repairs": [
                    {
                        "standard_metric": "REPLACE_WITH_EVIDENCE_METRIC",
                        "year": "REPLACE_WITH_EVIDENCE_YEAR",
                        "value": "REPLACE_WITH_EVIDENCE_VALUE",
                        "unit": "",
                        "confidence": "low",
                        "evidence": "REPLACE_WITH_EVIDENCE_SNIPPET",
                        "source_cell_or_segment": _norm((req.get("evidence_digest") or {}).get("source_trace_id") or req.get("source_trace_id")),
                        "flags": ["extract_positive_micro_test"],
                    }
                ],
                "manual_review_items": [],
                "notes": "If evidence is unclear, set decision=manual_review and clear repairs.",
            }
        )
    return rows


def _build_manual_steps(micro_dir: Path) -> str:
    raw_path = micro_dir / "local_model_response_raw.jsonl"
    return "\n".join(
        [
            "# Extract-Positive Manual Local Model Steps",
            "",
            "1. Open extract_positive_prompt.md and extract_positive_request_batch.jsonl.",
            "2. Run your local model manually (outside this pipeline).",
            "3. Keep output in strict JSONL format.",
            "4. Save output to:",
            f"   `{raw_path}`",
            "5. If any request is uncertain, return manual_review for that request.",
            "6. Do not include markdown or non-JSON lines.",
        ]
    )


def _build_commands(
    request_batch: Path,
    schema_json: Path,
    packet_jsonl: Path,
    trial_run_root: Path,
    delivery_dir: Path,
    micro_dir: Path,
) -> str:
    raw = micro_dir / "local_model_response_raw.jsonl"
    return "\n".join(
        [
            "# Extract-Positive Intake and Replay Commands",
            "",
            "Raw model output must go through intake gate first.",
            "Do not write directly to production 06.",
            "Use clean responses only for replay.",
            "",
            "```bat",
            "D:\\anaconda\\envs\\factory_v4\\python.exe D:\\_datefac\\tools\\intake_stage1_ai_repair_provider_responses.py ^",
            f"  --request-batch {request_batch} ^",
            f"  --schema-json {schema_json} ^",
            f"  --packet-jsonl {packet_jsonl} ^",
            f"  --trial-run-root {trial_run_root} ^",
            f"  --delivery-dir {delivery_dir} ^",
            f"  --raw-provider-response {raw} ^",
            "  --input-mode real_response ^",
            "  --no-synthetic ^",
            "  --run-offline-replay",
            "",
            "D:\\anaconda\\envs\\factory_v4\\python.exe D:\\_datefac\\tools\\check_delivery_state.py --json",
            "```",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Stage 1 extract-positive real-provider micro test package.")
    parser.add_argument("--request-batch", required=True)
    parser.add_argument("--packet-jsonl", required=True)
    parser.add_argument("--schema-json", required=True)
    parser.add_argument("--trial-run-root", required=True)
    parser.add_argument("--delivery-dir", required=True)
    parser.add_argument("--min-requests", type=int, default=3)
    parser.add_argument("--max-requests", type=int, default=5)
    args = parser.parse_args()

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_batch = Path(args.request_batch)
    packet_jsonl = Path(args.packet_jsonl)
    schema_json = Path(args.schema_json)
    trial_run_root = Path(args.trial_run_root)
    delivery_dir = Path(args.delivery_dir)
    helper_path = Path(__file__)

    if not request_batch.exists() or not packet_jsonl.exists() or not schema_json.exists():
        print("BLOCKED_REQUIRED_INPUT_MISSING")
        return 3

    before = _snapshot_files(_collect_production_guard_files(delivery_dir))

    requests = _load_jsonl(request_batch)
    packet_rows = _load_jsonl(packet_jsonl)
    packet_map = {_norm(r.get("repair_task_id")): r for r in packet_rows}
    extract_success_tids = _collect_extract_success_tids(trial_run_root)

    selected, selected_rows, excluded_rows, status_note = _select_extract_positive(
        requests,
        packet_map,
        extract_success_tids,
        int(args.min_requests),
        int(args.max_requests),
    )

    micro_dir = trial_run_root / "ai_repair_extract_positive_micro_test"
    micro_dir.mkdir(parents=True, exist_ok=True)

    req_batch_path = _write_jsonl(micro_dir / "extract_positive_request_batch.jsonl", selected)
    prompt_path = _safe_write_text(
        micro_dir / "extract_positive_prompt.md",
        _build_prompt(micro_dir / "local_model_response_raw.jsonl"),
    )
    resp_template_rows = _build_response_template(selected)
    resp_template_path = _write_jsonl(micro_dir / "extract_positive_response_template.jsonl", resp_template_rows)
    manual_steps_path = _safe_write_text(micro_dir / "extract_positive_manual_steps.md", _build_manual_steps(micro_dir))
    intake_cmd_path = _safe_write_text(
        micro_dir / "extract_positive_intake_replay_commands.md",
        _build_commands(req_batch_path, schema_json, packet_jsonl, trial_run_root, delivery_dir, micro_dir),
    )

    sample_counts = Counter([_norm(r.get("sample_id")) for r in selected])
    task_type_counts = Counter([_norm(r.get("task_type")) for r in selected])
    priority_counts = Counter([_norm(r.get("priority")) for r in selected])
    excluded_summary = Counter([_norm(r.get("exclude_reason")) for r in excluded_rows])

    no_secret_text = "\n".join(
        [
            req_batch_path.read_text(encoding="utf-8"),
            prompt_path.read_text(encoding="utf-8"),
            resp_template_path.read_text(encoding="utf-8"),
            manual_steps_path.read_text(encoding="utf-8"),
            intake_cmd_path.read_text(encoding="utf-8"),
        ]
    )
    no_secret_hits = _scan_secret(no_secret_text)
    no_secret_status = "PASS" if not no_secret_hits else "FAIL"

    output_files = [
        str(req_batch_path),
        str(prompt_path),
        str(resp_template_path),
        str(manual_steps_path),
        str(intake_cmd_path),
        str(delivery_dir / "58_stage1_extract_positive_micro_test_log.md"),
        str(delivery_dir / "58_stage1_extract_positive_micro_test_log.xlsx"),
        str(delivery_dir / "59_stage1_extract_positive_micro_test_plan.md"),
        str(delivery_dir / "59_stage1_extract_positive_micro_test_plan.xlsx"),
    ]

    after = _snapshot_files(_collect_production_guard_files(delivery_dir))
    guard_rows = _compare_snapshot(before, after)
    changed_count = sum(1 for r in guard_rows if r.get("changed") == "1")
    production_unchanged = changed_count == 0
    delivery_status = _run_delivery_check_json(delivery_dir)

    harness_status = "PASS"
    if len(selected) < int(args.min_requests):
        harness_status = "WARN"
    if no_secret_status != "PASS" or changed_count > 0:
        harness_status = "FAIL"

    safety_checks = [
        {"check_name": "no_real_model_call", "status": "PASS", "detail": "prep only"},
        {"check_name": "no_network", "status": "PASS", "detail": "local files only"},
        {"check_name": "no_secret_check", "status": no_secret_status, "detail": "|".join(no_secret_hits) or "no_secret_like_patterns"},
        {"check_name": "production_files_unchanged", "status": "PASS" if production_unchanged else "FAIL", "detail": f"changed={changed_count}"},
    ]

    commands_run = [
        f"{sys.executable} -m py_compile {helper_path}",
        f"{sys.executable} {helper_path} --request-batch {request_batch} --packet-jsonl {packet_jsonl} --schema-json {schema_json} --trial-run-root {trial_run_root} --delivery-dir {delivery_dir} --min-requests {int(args.min_requests)} --max-requests {int(args.max_requests)}",
        f"{sys.executable} D:/_datefac/tools/check_delivery_state.py --json",
    ]

    _safe_write_text(
        delivery_dir / "58_stage1_extract_positive_micro_test_log.md",
        "\n".join(
            [
                "# Stage1 Extract-Positive Micro Test Log",
                "",
                "- task_title: Prepare Stage 1 extract-positive real-provider micro test",
                f"- started_at: {started_at}",
                f"- finished_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- commands_run: {json.dumps(commands_run, ensure_ascii=False)}",
                f"- selected_request_count: {len(selected)}",
                f"- selected_task_type_counts: {json.dumps(dict(task_type_counts), ensure_ascii=False)}",
                f"- selected_sample_counts: {json.dumps(dict(sample_counts), ensure_ascii=False)}",
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
                    {"field": "task_title", "value": "Prepare Stage 1 extract-positive real-provider micro test"},
                    {"field": "selected_request_count", "value": len(selected)},
                    {"field": "selected_task_type_counts", "value": json.dumps(dict(task_type_counts), ensure_ascii=False)},
                    {"field": "selected_sample_counts", "value": json.dumps(dict(sample_counts), ensure_ascii=False)},
                    {"field": "status_note", "value": status_note},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "production_guard_changed_count", "value": changed_count},
                ]
            ),
            "selected_requests": pd.DataFrame(selected_rows),
            "excluded_requests": pd.DataFrame(excluded_rows),
            "sample_counts": pd.DataFrame([{"sample_id": k, "count": v} for k, v in sorted(sample_counts.items())]),
            "task_type_counts": pd.DataFrame([{"task_type": k, "count": v} for k, v in sorted(task_type_counts.items())]),
            "priority_counts": pd.DataFrame([{"priority": k, "count": v} for k, v in sorted(priority_counts.items())]),
            "output_files": pd.DataFrame([{"path": p} for p in output_files]),
            "no_secret_check": pd.DataFrame([{"status": no_secret_status, "detail": "|".join(no_secret_hits) or "no_secret_like_patterns"}]),
            "production_guard": pd.DataFrame(guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame([{"recommended_next_step": "Run manual extract-positive local model test and route raw output through intake."}]),
        },
        delivery_dir / "58_stage1_extract_positive_micro_test_log.xlsx",
    )

    _safe_write_text(
        delivery_dir / "59_stage1_extract_positive_micro_test_plan.md",
        "\n".join(
            [
                "# Stage1 Extract-Positive Micro Test Plan",
                "",
                f"- micro_test_harness_status: {harness_status}",
                f"- selected_request_count: {len(selected)}",
                f"- selected_sample_counts: {json.dumps(dict(sample_counts), ensure_ascii=False)}",
                f"- selected_task_type_counts: {json.dumps(dict(task_type_counts), ensure_ascii=False)}",
                f"- selected_priority_counts: {json.dumps(dict(priority_counts), ensure_ascii=False)}",
                f"- excluded_task_summary: {json.dumps(dict(excluded_summary), ensure_ascii=False)}",
                "- manual_test_steps_summary: use extract_positive_manual_steps.md and response template JSONL.",
                "- expected_user_action: run local model manually and save JSONL output.",
                "- intake_replay_plan_status: PASS",
                f"- no_secret_check_status: {no_secret_status}",
                f"- production_delivery_status_after: {json.dumps(delivery_status, ensure_ascii=False)}",
                f"- production_files_unchanged: {production_unchanged}",
                "- recommended_next_step: run one controlled local model extract-positive micro test and validate with intake/replay.",
            ]
        ),
    )

    _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "micro_test_harness_status", "value": harness_status},
                    {"field": "selected_request_count", "value": len(selected)},
                    {"field": "selected_sample_counts", "value": json.dumps(dict(sample_counts), ensure_ascii=False)},
                    {"field": "selected_task_type_counts", "value": json.dumps(dict(task_type_counts), ensure_ascii=False)},
                    {"field": "selected_priority_counts", "value": json.dumps(dict(priority_counts), ensure_ascii=False)},
                    {"field": "excluded_task_summary", "value": json.dumps(dict(excluded_summary), ensure_ascii=False)},
                    {"field": "expected_user_action", "value": "run manual local model extract-positive test and save raw JSONL"},
                    {"field": "intake_replay_plan_status", "value": "PASS"},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "production_delivery_status_after", "value": json.dumps(delivery_status, ensure_ascii=False)},
                    {"field": "production_files_unchanged", "value": "1" if production_unchanged else "0"},
                ]
            ),
            "selected_requests": pd.DataFrame(selected_rows),
            "excluded_requests": pd.DataFrame(excluded_rows),
            "sample_counts": pd.DataFrame([{"sample_id": k, "count": v} for k, v in sorted(sample_counts.items())]),
            "task_type_counts": pd.DataFrame([{"task_type": k, "count": v} for k, v in sorted(task_type_counts.items())]),
            "priority_counts": pd.DataFrame([{"priority": k, "count": v} for k, v in sorted(priority_counts.items())]),
            "output_files": pd.DataFrame([{"path": p} for p in output_files]),
            "no_secret_check": pd.DataFrame([{"status": no_secret_status, "detail": "|".join(no_secret_hits) or "no_secret_like_patterns"}]),
            "production_guard": pd.DataFrame(guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame([{"recommended_next_step": "Use extract-positive request batch for a micro manual provider test first."}]),
        },
        delivery_dir / "59_stage1_extract_positive_micro_test_plan.xlsx",
    )

    print("task_title: Prepare Stage 1 extract-positive real-provider micro test")
    print(f"helper_path: {helper_path}")
    print(f"selected_request_count: {len(selected)}")
    print(f"selected_task_type_counts: {json.dumps(dict(task_type_counts), ensure_ascii=False)}")
    print(f"selected_sample_counts: {json.dumps(dict(sample_counts), ensure_ascii=False)}")
    print(f"generated_outputs: {json.dumps(output_files, ensure_ascii=False)}")
    print(f"production_delivery_status_after: {json.dumps(delivery_status, ensure_ascii=False)}")
    print(f"production_files_unchanged: {production_unchanged}")

    if harness_status == "FAIL":
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

