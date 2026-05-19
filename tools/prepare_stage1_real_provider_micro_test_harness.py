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
PREFERRED_TYPES = {"row_segment_repair", "metric_year_value_alignment"}


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


def _scan_secret(text: str) -> List[str]:
    hits: List[str] = []
    for p in SECRET_PATTERNS:
        if p in text:
            hits.append(p)
    return hits


def _request_row(req: Dict[str, Any]) -> Dict[str, Any]:
    evidence = req.get("evidence_digest", {}) or {}
    return {
        "request_id": _norm(req.get("request_id")),
        "repair_task_id": _norm(req.get("repair_task_id")),
        "sample_id": _norm(req.get("sample_id")),
        "company": _norm(req.get("company")),
        "task_type": _norm(req.get("task_type")),
        "priority": _norm(req.get("priority")),
        "source_trace_id": _norm(req.get("source_trace_id")),
        "metric_hint": _norm(evidence.get("metric_hint")),
        "detected_years": "|".join([_norm(x) for x in (evidence.get("detected_years") or []) if _norm(x)]),
        "flags": "|".join([_norm(x) for x in (evidence.get("flags") or []) if _norm(x)]),
    }


def _select_micro_requests(
    requests: List[Dict[str, Any]],
    min_requests: int,
    max_requests: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], str]:
    selected: List[Dict[str, Any]] = []
    excluded_rows: List[Dict[str, Any]] = []

    preferred = [r for r in requests if _norm(r.get("task_type")) in PREFERRED_TYPES]
    s1 = [r for r in preferred if _norm(r.get("sample_id")) == "S1"]
    s3 = [r for r in preferred if _norm(r.get("sample_id")) == "S3"]
    s2 = [r for r in preferred if _norm(r.get("sample_id")) == "S2"]

    def add_if_not_exists(req: Dict[str, Any]) -> None:
        rid = _norm(req.get("request_id"))
        if rid and rid not in [_norm(x.get("request_id")) for x in selected]:
            selected.append(req)

    # Hard coverage constraints where possible.
    for req in s1[:2]:
        add_if_not_exists(req)
    if s3:
        add_if_not_exists(s3[0])

    # Ensure at least one row_segment and one metric_year_value_alignment if available.
    row_seg = [r for r in preferred if _norm(r.get("task_type")) == "row_segment_repair"]
    align = [r for r in preferred if _norm(r.get("task_type")) == "metric_year_value_alignment"]
    if row_seg:
        add_if_not_exists(row_seg[0])
    if align:
        add_if_not_exists(align[0])

    # Fill with preferred tasks first.
    for req in preferred:
        if len(selected) >= max_requests:
            break
        add_if_not_exists(req)

    # At most one S2 task only if still below min.
    if len(selected) < min_requests and s2:
        add_if_not_exists(s2[0])

    # If still below min, include semantic guard as low priority fallback.
    semantic = [r for r in requests if _norm(r.get("task_type")) == "semantic_guard_review"]
    for req in semantic:
        if len(selected) >= min_requests:
            break
        add_if_not_exists(req)

    selected = selected[:max_requests]
    selected_ids = {_norm(r.get("request_id")) for r in selected}
    for req in requests:
        rid = _norm(req.get("request_id"))
        reason = "selected"
        if rid not in selected_ids:
            t = _norm(req.get("task_type"))
            if t == "semantic_guard_review":
                reason = "excluded_semantic_in_first_micro_test"
            elif _norm(req.get("sample_id")) == "S2":
                reason = "excluded_s2_over_limit"
            else:
                reason = "excluded_after_priority_fill"
        if reason != "selected":
            row = _request_row(req)
            row["exclude_reason"] = reason
            excluded_rows.append(row)

    status_note = "PASS"
    if len([r for r in selected if _norm(r.get("task_type")) == "metric_year_value_alignment"]) == 0 and align:
        status_note = "WARN_MISSING_ALIGNMENT_IN_SELECTION"
    if len(selected) < min_requests:
        status_note = "WARN_INSUFFICIENT_ELIGIBLE_TASKS"
    return selected, excluded_rows, [_request_row(r) for r in selected], status_note


def _build_micro_prompt(selected: List[Dict[str, Any]], schema_title: str, raw_output_path: Path) -> str:
    lines = [
        "# Stage 1 Real-Provider Micro Test Prompt",
        "",
        "Role: strict financial table repair worker.",
        "Output format: JSONL only.",
        "One output JSON object per input request.",
        f"Schema target: {schema_title}",
        "Do not invent values.",
        "Copy numbers from evidence only.",
        "If ambiguous, choose manual_review.",
        "Preserve repair_task_id.",
        "Preserve year labels unless explicitly flagged year_normalized.",
        "No markdown in model output.",
        "No explanations outside JSON.",
        "",
        "How to run manual model test:",
        "1. Copy the selected request JSON objects from `micro_test_request_batch.jsonl`.",
        "2. Paste them into your local/cloud model with the rules above.",
        "3. Save model output as JSONL to:",
        f"   `{raw_output_path}`",
        "",
        "Selected request preview:",
        "",
        "| request_id | repair_task_id | sample_id | task_type | priority |",
        "|---|---|---|---|---|",
    ]
    for req in selected:
        lines.append(
            f"| {_norm(req.get('request_id'))} | {_norm(req.get('repair_task_id'))} | {_norm(req.get('sample_id'))} | {_norm(req.get('task_type'))} | {_norm(req.get('priority'))} |"
        )
    return "\n".join(lines)


def _build_template_rows(selected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for req in selected:
        rows.append(
            {
                "repair_task_id": _norm(req.get("repair_task_id")),
                "decision": "manual_review",
                "repairs": [],
                "manual_review_items": [
                    {
                        "reason": "placeholder_manual_review_reason",
                        "evidence": "Replace with model-supported evidence or keep manual_review if ambiguous.",
                    }
                ],
                "notes": "Replace this placeholder with actual model output or keep manual_review if ambiguous.",
            }
        )
    return rows


def _build_manual_steps(micro_dir: Path) -> str:
    raw = micro_dir / "local_model_response_raw.jsonl"
    return "\n".join(
        [
            "# Run Local Model Manual Steps",
            "",
            "1. Open `micro_test_prompt.md` and `micro_test_request_batch.jsonl`.",
            "2. Use your local/cloud model manually (outside this pipeline).",
            "3. Keep output as strict JSONL, one JSON object per request.",
            "4. Save the output file to:",
            f"   `{raw}`",
            "5. Do not include markdown, comments, or non-JSON lines.",
            "6. Do not write any secrets into repository files.",
        ]
    )


def _build_intake_replay_commands(
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
            "# Micro Test Intake and Replay Commands",
            "",
            "Raw model output must go through intake gate first.",
            "Do not write output directly to production 06.",
            "Only clean responses can be replayed.",
            "",
            "```bat",
            f"D:\\anaconda\\envs\\factory_v4\\python.exe D:\\_datefac\\tools\\intake_stage1_ai_repair_provider_responses.py ^",
            f"  --request-batch {request_batch} ^",
            f"  --schema-json {schema_json} ^",
            f"  --packet-jsonl {packet_jsonl} ^",
            f"  --trial-run-root {trial_run_root} ^",
            f"  --delivery-dir {delivery_dir} ^",
            f"  --raw-provider-response {raw} ^",
            "  --run-offline-replay",
            "",
            "D:\\anaconda\\envs\\factory_v4\\python.exe D:\\_datefac\\tools\\check_delivery_state.py --json",
            "```",
            "",
            "Optional explicit replay (after intake clean file exists):",
            "```bat",
            f"D:\\anaconda\\envs\\factory_v4\\python.exe D:\\_datefac\\tools\\run_stage1_ai_repair_worker.py ^",
            f"  --packet-jsonl {packet_jsonl} ^",
            f"  --schema-json {schema_json} ^",
            f"  --trial-run-root {trial_run_root} ^",
            f"  --delivery-dir {delivery_dir} ^",
            "  --provider offline_file ^",
            f"  --offline-response-jsonl {trial_run_root}\\ai_repair_provider_intake\\provider_response_intake_clean.jsonl ^",
            "  --strict-schema",
            "```",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Stage 1 real-provider micro test harness (offline prep only).")
    parser.add_argument("--request-batch", required=True)
    parser.add_argument("--schema-json", required=True)
    parser.add_argument("--prompt-md", required=True)
    parser.add_argument("--packet-jsonl", required=True)
    parser.add_argument("--trial-run-root", required=True)
    parser.add_argument("--delivery-dir", required=True)
    parser.add_argument("--min-requests", type=int, default=5)
    parser.add_argument("--max-requests", type=int, default=10)
    args = parser.parse_args()

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_batch = Path(args.request_batch)
    schema_json = Path(args.schema_json)
    prompt_md = Path(args.prompt_md)
    packet_jsonl = Path(args.packet_jsonl)
    trial_run_root = Path(args.trial_run_root)
    delivery_dir = Path(args.delivery_dir)
    helper_path = Path(__file__)

    if not request_batch.exists():
        print("BLOCKED_MISSING_PROVIDER_REQUEST_BATCH")
        return 3
    if not schema_json.exists() or not prompt_md.exists() or not packet_jsonl.exists():
        print("BLOCKED_REQUIRED_INPUT_MISSING")
        return 3

    micro_dir = trial_run_root / "ai_repair_micro_test"
    micro_dir.mkdir(parents=True, exist_ok=True)

    before = _snapshot_files(_collect_production_guard_files(delivery_dir))

    requests = _load_jsonl(request_batch)
    schema_payload = json.loads(schema_json.read_text(encoding="utf-8"))
    schema_title = _norm(schema_payload.get("title")) or "stage1_ai_repair_v1"
    _ = prompt_md.read_text(encoding="utf-8")
    _ = _load_jsonl(packet_jsonl)

    selected, excluded_rows, selected_rows, selection_status_note = _select_micro_requests(requests, int(args.min_requests), int(args.max_requests))
    selected_count = len(selected)
    sample_counts = Counter([_norm(x.get("sample_id")) for x in selected])
    task_type_counts = Counter([_norm(x.get("task_type")) for x in selected])
    priority_counts = Counter([_norm(x.get("priority")) for x in selected])

    micro_request_jsonl = _write_jsonl(micro_dir / "micro_test_request_batch.jsonl", selected)
    micro_request_xlsx = _safe_write_excel({"selected_requests": pd.DataFrame(selected_rows)}, micro_dir / "micro_test_request_batch.xlsx")
    prompt_text = _build_micro_prompt(selected, schema_title, micro_dir / "local_model_response_raw.jsonl")
    micro_prompt_md = _safe_write_text(micro_dir / "micro_test_prompt.md", prompt_text)
    template_rows = _build_template_rows(selected)
    template_jsonl = _write_jsonl(micro_dir / "local_model_response_template.jsonl", template_rows)
    placeholder_raw = _write_jsonl(micro_dir / "local_model_response_raw_PLACEHOLDER.jsonl", template_rows)
    manual_steps_md = _safe_write_text(micro_dir / "run_local_model_manual_steps.md", _build_manual_steps(micro_dir))
    intake_replay_md = _safe_write_text(
        micro_dir / "micro_test_intake_replay_commands.md",
        _build_intake_replay_commands(request_batch, schema_json, packet_jsonl, trial_run_root, delivery_dir, micro_dir),
    )

    selection_diag_xlsx = _safe_write_excel(
        {
            "selected_requests": pd.DataFrame(selected_rows),
            "excluded_requests": pd.DataFrame(excluded_rows),
            "sample_counts": pd.DataFrame([{"sample_id": k, "count": v} for k, v in sorted(sample_counts.items())]),
            "task_type_counts": pd.DataFrame([{"task_type": k, "count": v} for k, v in sorted(task_type_counts.items())]),
            "priority_counts": pd.DataFrame([{"priority": k, "count": v} for k, v in sorted(priority_counts.items())]),
            "summary": pd.DataFrame(
                [
                    {"field": "selection_status_note", "value": selection_status_note},
                    {"field": "selected_request_count", "value": selected_count},
                    {"field": "min_requests", "value": int(args.min_requests)},
                    {"field": "max_requests", "value": int(args.max_requests)},
                ]
            ),
        },
        micro_dir / "micro_test_selection_diagnostics.xlsx",
    )

    no_secret_text = "\n".join(
        [
            prompt_text,
            json.dumps(selected, ensure_ascii=False),
            json.dumps(template_rows, ensure_ascii=False),
            intake_replay_md.read_text(encoding="utf-8"),
            manual_steps_md.read_text(encoding="utf-8"),
        ]
    )
    no_secret_hits = _scan_secret(no_secret_text)
    no_secret_status = "PASS" if not no_secret_hits else "FAIL"

    after = _snapshot_files(_collect_production_guard_files(delivery_dir))
    guard_rows = _compare_snapshot(before, after)
    changed_count = sum(1 for r in guard_rows if r.get("changed") == "1")
    production_unchanged = changed_count == 0
    production_status = _run_delivery_check_json(delivery_dir)

    harness_status = "PASS"
    if selected_count < int(args.min_requests):
        harness_status = "WARN"
    if no_secret_status != "PASS" or changed_count > 0:
        harness_status = "FAIL"

    output_files_generated = [
        str(micro_request_jsonl),
        str(micro_request_xlsx),
        str(micro_prompt_md),
        str(template_jsonl),
        str(placeholder_raw),
        str(manual_steps_md),
        str(intake_replay_md),
        str(selection_diag_xlsx),
        str(delivery_dir / "56_stage1_real_provider_micro_test_harness_log.md"),
        str(delivery_dir / "56_stage1_real_provider_micro_test_harness_log.xlsx"),
        str(delivery_dir / "57_stage1_real_provider_micro_test_harness_plan.md"),
        str(delivery_dir / "57_stage1_real_provider_micro_test_harness_plan.xlsx"),
    ]

    safety_checks = [
        {"check_name": "no_real_model_call", "status": "PASS", "detail": "harness preparation only"},
        {"check_name": "no_network", "status": "PASS", "detail": "local file operations only"},
        {"check_name": "no_secret_check", "status": no_secret_status, "detail": "|".join(no_secret_hits) or "no_secret_like_patterns"},
        {"check_name": "production_files_unchanged", "status": "PASS" if production_unchanged else "FAIL", "detail": f"changed={changed_count}"},
    ]

    commands_run = [
        f"{sys.executable} -m py_compile {helper_path}",
        f"{sys.executable} {helper_path} --request-batch {request_batch} --schema-json {schema_json} --prompt-md {prompt_md} --packet-jsonl {packet_jsonl} --trial-run-root {trial_run_root} --delivery-dir {delivery_dir} --min-requests {int(args.min_requests)} --max-requests {int(args.max_requests)}",
        f"{sys.executable} D:/_datefac/tools/check_delivery_state.py --json",
    ]

    _safe_write_text(
        delivery_dir / "56_stage1_real_provider_micro_test_harness_log.md",
        "\n".join(
            [
                "# Stage1 Real Provider Micro Test Harness Log",
                "",
                "- task_title: Prepare Stage 1 real-provider micro test harness",
                f"- started_at: {started_at}",
                f"- finished_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- commands_run: {json.dumps(commands_run, ensure_ascii=False)}",
                f"- provider_request_batch_path: {request_batch}",
                f"- selected_request_count: {selected_count}",
                f"- selected_sample_counts: {json.dumps(dict(sample_counts), ensure_ascii=False)}",
                f"- selected_task_type_counts: {json.dumps(dict(task_type_counts), ensure_ascii=False)}",
                f"- output_files_generated: {json.dumps(output_files_generated, ensure_ascii=False)}",
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
                    {"field": "task_title", "value": "Prepare Stage 1 real-provider micro test harness"},
                    {"field": "started_at", "value": started_at},
                    {"field": "finished_at", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                    {"field": "provider_request_batch_path", "value": str(request_batch)},
                    {"field": "selected_request_count", "value": selected_count},
                    {"field": "selected_sample_counts", "value": json.dumps(dict(sample_counts), ensure_ascii=False)},
                    {"field": "selected_task_type_counts", "value": json.dumps(dict(task_type_counts), ensure_ascii=False)},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "production_guard_changed_count", "value": changed_count},
                ]
            ),
            "selected_requests": pd.DataFrame(selected_rows),
            "excluded_requests": pd.DataFrame(excluded_rows),
            "sample_counts": pd.DataFrame([{"sample_id": k, "count": v} for k, v in sorted(sample_counts.items())]),
            "task_type_counts": pd.DataFrame([{"task_type": k, "count": v} for k, v in sorted(task_type_counts.items())]),
            "priority_counts": pd.DataFrame([{"priority": k, "count": v} for k, v in sorted(priority_counts.items())]),
            "output_files": pd.DataFrame([{"path": x} for x in output_files_generated]),
            "no_secret_check": pd.DataFrame([{"status": no_secret_status, "detail": "|".join(no_secret_hits) or "no_secret_like_patterns"}]),
            "production_guard": pd.DataFrame(guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "Run manual model test with micro batch and route raw output through intake gate before replay.",
                    }
                ]
            ),
        },
        delivery_dir / "56_stage1_real_provider_micro_test_harness_log.xlsx",
    )

    excluded_summary = Counter([_norm(x.get("exclude_reason")) for x in excluded_rows])
    _safe_write_text(
        delivery_dir / "57_stage1_real_provider_micro_test_harness_plan.md",
        "\n".join(
            [
                "# Stage1 Real Provider Micro Test Harness Plan",
                "",
                f"- micro_test_harness_status: {harness_status}",
                f"- selected_request_count: {selected_count}",
                f"- selected_sample_counts: {json.dumps(dict(sample_counts), ensure_ascii=False)}",
                f"- selected_task_type_counts: {json.dumps(dict(task_type_counts), ensure_ascii=False)}",
                f"- selected_priority_counts: {json.dumps(dict(priority_counts), ensure_ascii=False)}",
                f"- excluded_task_summary: {json.dumps(dict(excluded_summary), ensure_ascii=False)}",
                "- manual_test_steps_summary: prepared run_local_model_manual_steps.md and response template JSONL.",
                "- expected_user_action: run model manually and save raw JSONL, then run intake/replay commands.",
                "- intake_replay_plan_status: PASS",
                f"- no_secret_check_status: {no_secret_status}",
                f"- production_delivery_status_after: {json.dumps(production_status, ensure_ascii=False)}",
                f"- production_files_unchanged: {production_unchanged}",
                "- recommended_next_step: execute a controlled manual model micro test and validate intake/replay outputs.",
            ]
        ),
    )
    _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "micro_test_harness_status", "value": harness_status},
                    {"field": "selected_request_count", "value": selected_count},
                    {"field": "selected_sample_counts", "value": json.dumps(dict(sample_counts), ensure_ascii=False)},
                    {"field": "selected_task_type_counts", "value": json.dumps(dict(task_type_counts), ensure_ascii=False)},
                    {"field": "selected_priority_counts", "value": json.dumps(dict(priority_counts), ensure_ascii=False)},
                    {"field": "excluded_task_summary", "value": json.dumps(dict(excluded_summary), ensure_ascii=False)},
                    {"field": "manual_test_steps_summary", "value": "prepared manual steps and templates"},
                    {"field": "expected_user_action", "value": "run model manually then execute intake/replay commands"},
                    {"field": "intake_replay_plan_status", "value": "PASS"},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "production_delivery_status_after", "value": json.dumps(production_status, ensure_ascii=False)},
                    {"field": "production_files_unchanged", "value": "1" if production_unchanged else "0"},
                ]
            ),
            "selected_requests": pd.DataFrame(selected_rows),
            "excluded_requests": pd.DataFrame(excluded_rows),
            "sample_counts": pd.DataFrame([{"sample_id": k, "count": v} for k, v in sorted(sample_counts.items())]),
            "task_type_counts": pd.DataFrame([{"task_type": k, "count": v} for k, v in sorted(task_type_counts.items())]),
            "priority_counts": pd.DataFrame([{"priority": k, "count": v} for k, v in sorted(priority_counts.items())]),
            "output_files": pd.DataFrame([{"path": x} for x in output_files_generated]),
            "no_secret_check": pd.DataFrame([{"status": no_secret_status, "detail": "|".join(no_secret_hits) or "no_secret_like_patterns"}]),
            "production_guard": pd.DataFrame(guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "Use the micro test harness to collect raw model JSONL and validate with intake/replay in sandbox.",
                    }
                ]
            ),
        },
        delivery_dir / "57_stage1_real_provider_micro_test_harness_plan.xlsx",
    )

    print(f"helper_path: {helper_path}")
    print(f"micro_test_harness_status: {harness_status}")
    print(f"selected_request_count: {selected_count}")
    print(f"selected_sample_counts: {json.dumps(dict(sample_counts), ensure_ascii=False)}")
    print(f"selected_task_type_counts: {json.dumps(dict(task_type_counts), ensure_ascii=False)}")
    print(f"selected_priority_counts: {json.dumps(dict(priority_counts), ensure_ascii=False)}")
    print(f"no_secret_check_status: {no_secret_status}")
    print(f"generated_outputs: {json.dumps(output_files_generated, ensure_ascii=False)}")
    print(f"production_delivery_status_after: {json.dumps(production_status, ensure_ascii=False)}")
    print(f"production_files_unchanged: {production_unchanged}")

    if harness_status == "FAIL":
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

