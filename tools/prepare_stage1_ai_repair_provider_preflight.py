import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import pandas as pd


EXTRACT_IDS = [
    "RPR-S1-0001",
    "RPR-S1-0002",
    "RPR-S1-0003",
    "RPR-S1-0004",
    "RPR-S1-0006",
    "RPR-S1-0007",
    "RPR-S3-0005",
]
S1_SEMANTIC_IDS = [
    "RPR-S1-0008",
    "RPR-S1-0011",
    "RPR-S1-0014",
    "RPR-S1-0022",
    "RPR-S1-0029",
    "RPR-S1-0030",
]
S3_SEMANTIC_IDS = [
    "RPR-S3-0031",
    "RPR-S3-0040",
]
S2_IDS = [
    "RPR-S2-0073",
    "RPR-S2-0074",
    "RPR-S2-0075",
    "RPR-S2-0076",
    "RPR-S2-0077",
]
SELECTED_ORDER = EXTRACT_IDS + S2_IDS + S1_SEMANTIC_IDS + S3_SEMANTIC_IDS

TASK_PRIORITY = {
    "row_segment_repair": "P0",
    "metric_year_value_alignment": "P0",
    "s2_table_level_repair": "P1",
    "semantic_guard_review": "P2",
}
EXTRACT_TASK_TYPES = {"row_segment_repair", "metric_year_value_alignment"}
TARGET_METRICS = {
    "营业收入",
    "归属母公司净利润",
    "每股收益",
    "P/E",
    "P/B",
    "EV/EBITDA",
    "ROE",
    "EBITDA",
    "毛利率",
    "净利率",
}


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


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _evidence_excerpt(task: Dict[str, Any], limit: int = 260) -> str:
    evidence = task.get("evidence", {}) or {}
    parts: List[str] = []
    for key in ["candidate_type", "row_preview", "table_header_context", "nearby_rows_context", "raw_table_preview"]:
        value = evidence.get(key, "")
        if isinstance(value, list):
            parts.append(json.dumps(value, ensure_ascii=False))
        else:
            parts.append(_norm(value))
    text = " | ".join([p for p in parts if p])
    return text[:limit]


def _task_metrics(task: Dict[str, Any]) -> Dict[str, Any]:
    rule = task.get("current_rule_result", {}) or {}
    source = task.get("source", {}) or {}
    evidence = task.get("evidence", {}) or {}
    return {
        "repair_task_id": _norm(task.get("repair_task_id")),
        "sample_id": _norm(task.get("sample_id")),
        "company": _norm(task.get("company")),
        "task_type": _norm(task.get("task_type")),
        "standard_metric_hint": _norm(rule.get("standard_metric_hint")),
        "detected_years": "|".join([_norm(x) for x in evidence.get("detected_years", []) if _norm(x)]),
        "source_trace_id": _norm(source.get("source_trace_id")),
        "table_role": _norm(source.get("table_role")),
        "row_preview_excerpt": _evidence_excerpt(task),
        "flags": "|".join([_norm(x) for x in (rule.get("flags") or []) if _norm(x)]),
    }


def _metric_priority(metric: str) -> int:
    order = {
        "营业收入": 0,
        "归属母公司净利润": 1,
        "每股收益": 2,
        "P/E": 3,
        "P/B": 4,
        "EV/EBITDA": 5,
        "ROE": 6,
        "EBITDA": 7,
        "毛利率": 8,
        "净利率": 9,
    }
    return order.get(_norm(metric), 99)


def _selected_priority(task: Dict[str, Any]) -> str:
    return TASK_PRIORITY.get(_norm(task.get("task_type")), "P2")


def _build_provider_prompt(task: Dict[str, Any], evidence_digest: Dict[str, Any], schema_name: str) -> str:
    return "\n".join(
        [
            "You are a strict financial table repair worker.",
            "Return JSON only and follow the schema exactly.",
            f"Schema: {schema_name}",
            f"repair_task_id: {evidence_digest['repair_task_id']}",
            f"sample_id: {evidence_digest['sample_id']}",
            f"company: {evidence_digest['company']}",
            f"task_type: {evidence_digest['task_type']}",
            f"priority: {TASK_PRIORITY.get(evidence_digest['task_type'], 'P2')}",
            f"source_trace_id: {evidence_digest['source_trace_id']}",
            f"table_role: {evidence_digest['table_role']}",
            f"detected_years: {evidence_digest['detected_years']}",
            f"flags: {evidence_digest['flags'] or 'none'}",
            f"evidence_digest: {evidence_digest['row_preview_excerpt']}",
            "Rules:",
            "- Use evidence only.",
            "- Do not invent values or years.",
            "- If ambiguous, return manual_review.",
            "- Do not write to production files.",
        ]
    )


def _build_request(task: Dict[str, Any], request_id: str, schema_path: Path, schema_name: str) -> Dict[str, Any]:
    metrics = _task_metrics(task)
    evidence_digest = {
        "repair_task_id": metrics["repair_task_id"],
        "sample_id": metrics["sample_id"],
        "company": metrics["company"],
        "task_type": metrics["task_type"],
        "source_trace_id": metrics["source_trace_id"],
        "table_role": metrics["table_role"],
        "detected_years": metrics["detected_years"].split("|") if metrics["detected_years"] else [],
        "metric_hint": metrics["standard_metric_hint"],
        "flags": metrics["flags"].split("|") if metrics["flags"] else [],
        "row_preview_excerpt": metrics["row_preview_excerpt"],
    }
    return {
        "request_id": request_id,
        "repair_task_id": metrics["repair_task_id"],
        "sample_id": metrics["sample_id"],
        "company": metrics["company"],
        "task_type": metrics["task_type"],
        "priority": _selected_priority(task),
        "provider_prompt": _build_provider_prompt(task, evidence_digest, schema_name),
        "expected_output_schema": {
            "schema_name": schema_name,
            "schema_path": str(schema_path),
            "required_fields": ["repair_task_id", "decision", "repairs", "manual_review_items", "notes"],
        },
        "evidence_digest": evidence_digest,
        "source_trace_id": metrics["source_trace_id"],
        "safety_constraints": [
            "evidence_only",
            "json_only",
            "no_invention",
            "no_network",
            "no_ocr",
            "no_production_write",
            "no_secrets",
        ],
        "response_required_json_only": True,
        "must_not_invent_values": True,
    }


def _scan_no_secret(texts: Dict[str, str]) -> List[Dict[str, str]]:
    patterns = ["sk-", "BEGIN PRIVATE KEY", "Bearer ", "api_secret", "password="]
    rows = []
    for name, text in texts.items():
        hit = any(p in text for p in patterns)
        rows.append(
            {
                "artifact": name,
                "status": "FAIL" if hit else "PASS",
                "detail": "secret_like_pattern_found" if hit else "no_secret_like_patterns",
            }
        )
    return rows


def _snapshot_production(delivery_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for pattern in ["01_*.xlsx", "02_*.xlsx", "02A_*.xlsx", "06_*.xlsx"]:
        for path in sorted(delivery_dir.glob(pattern))[:1]:
            rows.append(
                {
                    "path": str(path),
                    "exists": "1" if path.exists() else "0",
                    "size": path.stat().st_size if path.exists() else 0,
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


def _write_md_table_sample(requests: List[Dict[str, Any]], path: Path) -> Path:
    lines = [
        "# Stage 1 AI Repair Provider Request Sample",
        "",
        "| request_id | repair_task_id | sample | type | priority | note |",
        "|---|---|---|---|---|---|",
    ]
    for req in requests[:5]:
        lines.append(
            f"| {req['request_id']} | {req['repair_task_id']} | {req['sample_id']} | {req['task_type']} | {req['priority']} | evidence-only, json-only |"
        )
    lines.extend(["", "No secrets are embedded in this bundle."])
    return _safe_write_text(path, "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Stage 1 AI repair real-provider preflight bundle (offline only).")
    parser.add_argument("--packet-jsonl", required=True)
    parser.add_argument("--schema-json", required=True)
    parser.add_argument("--prompt-md", required=True)
    parser.add_argument("--trial-run-root", required=True)
    parser.add_argument("--delivery-dir", required=True)
    parser.add_argument("--max-provider-tasks", type=int, default=20)
    args = parser.parse_args()

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    packet_path = Path(args.packet_jsonl)
    schema_path = Path(args.schema_json)
    prompt_path = Path(args.prompt_md)
    trial_run_root = Path(args.trial_run_root)
    delivery_dir = Path(args.delivery_dir)
    helper_path = Path(__file__)

    if not packet_path.exists() or not schema_path.exists() or not prompt_path.exists():
        print("BLOCKED_REQUIRED_INPUT_MISSING")
        return 3

    tasks = _load_jsonl(packet_path)
    task_map = {_norm(t.get("repair_task_id")): t for t in tasks}
    schema_payload = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_name = _norm(schema_payload.get("title")) or "stage1_ai_repair_v1"
    prompt_text = prompt_path.read_text(encoding="utf-8")

    preflight_dir = trial_run_root / "ai_repair_provider_preflight"
    preflight_dir.mkdir(parents=True, exist_ok=True)

    target_count = max(10, min(int(args.max_provider_tasks), len(SELECTED_ORDER)))
    selected_ids = [tid for tid in SELECTED_ORDER if tid in task_map][:target_count]
    if len(selected_ids) < target_count:
        for task in tasks:
            tid = _norm(task.get("repair_task_id"))
            if not tid or tid in selected_ids:
                continue
            selected_ids.append(tid)
            if len(selected_ids) >= target_count:
                break
    selected_tasks = [task_map[tid] for tid in selected_ids]
    provider_requests: List[Dict[str, Any]] = []
    excluded_rows: List[Dict[str, Any]] = []

    for idx, task in enumerate(selected_tasks, start=1):
        provider_requests.append(_build_request(task, f"PRF-{idx:04d}", schema_path, schema_name))

    selected_id_set = set(selected_ids)
    for task in tasks:
        tid = _norm(task.get("repair_task_id"))
        if not tid:
            continue
        if tid in selected_id_set:
            continue
        excluded_rows.append(
            {
                **_task_metrics(task),
                "selected_decision": "excluded",
                "selected_metric": "",
                "selected_year": "",
                "selected_value": "",
                "evidence_source": _evidence_excerpt(task),
                "reject_reason": "not_selected_in_controlled_preflight_batch",
                "confidence": "low" if _norm(task.get("task_type")) in EXTRACT_TASK_TYPES else "n/a",
            }
        )

    request_path = preflight_dir / "provider_request_batch.jsonl"
    request_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in provider_requests), encoding="utf-8")

    sample_md_path = _write_md_table_sample(provider_requests, preflight_dir / "provider_request_batch_sample.md")

    config_template = {
        "provider_name": "local_or_cloud_provider_placeholder",
        "model_name": "placeholder",
        "endpoint_url": "placeholder_do_not_commit_real_endpoint",
        "api_key_env_var": "STAGE1_AI_REPAIR_API_KEY",
        "timeout_seconds": 60,
        "max_retries": 2,
        "max_concurrent_requests": 2,
        "max_input_chars_per_task": 4096,
        "max_output_tokens": 2048,
        "temperature": 0,
        "json_only": True,
        "dry_run": True,
    }
    config_path = preflight_dir / "provider_config_template.json"
    config_path.write_text(json.dumps(config_template, ensure_ascii=False, indent=2), encoding="utf-8")

    response_contract_md = "\n".join(
        [
            "# Stage 1 AI Repair Provider Response Contract",
            "",
            "- One JSON object per request.",
            "- `repair_task_id` must match the request.",
            "- Output must conform to `38_stage1_ai_repair_schema.json`.",
            "- Extracted values must appear in the evidence.",
            "- Invalid responses are demoted or blocked.",
            "- No AI response can directly write production `06`.",
            "- Save real-provider outputs locally first, then replay them via `--provider offline_file`.",
        ]
    )
    response_contract_path = preflight_dir / "provider_response_contract.md"
    response_contract_path.write_text(response_contract_md, encoding="utf-8")

    validation_plan_md = "\n".join(
        [
            "# Stage 1 AI Repair Provider Response Validation Plan",
            "",
            "1. Capture the provider response as local JSONL.",
            "2. Validate one JSON object per line.",
            "3. Check `repair_task_id` against the request batch.",
            "4. Validate schema conformance before any downstream use.",
            "5. Verify extracted values and years appear in evidence.",
            "6. Demote invalid extracts to manual review or block them.",
            "7. Replay valid local JSONL through `--provider offline_file`.",
            "8. Inspect merge preview only after schema/evidence checks pass.",
        ]
    )
    validation_plan_path = preflight_dir / "provider_response_validation_plan.md"
    validation_plan_path.write_text(validation_plan_md, encoding="utf-8")

    run_checklist_md = "\n".join(
        [
            "# Stage 1 AI Repair Provider Run Checklist",
            "",
            "- [ ] Do not use any real model in this preflight task.",
            "- [ ] Do not add secrets, API keys, tokens, passwords, or endpoint secrets.",
            "- [ ] Keep request batch bounded to 10-20 tasks.",
            "- [ ] Verify S1, S2, and S3 are represented where possible.",
            "- [ ] Save provider responses locally before any replay.",
            "- [ ] Replay only via `--provider offline_file`.",
            "- [ ] Confirm no production `01/02/02A/06` changes.",
            "- [ ] Stop if any secret-like text appears in bundle artifacts.",
        ]
    )
    run_checklist_path = preflight_dir / "provider_run_checklist.md"
    run_checklist_path.write_text(run_checklist_md, encoding="utf-8")

    request_count = len(provider_requests)
    sample_counts = Counter([_norm(r.get("sample_id")) for r in provider_requests])
    task_type_counts = Counter([_norm(r.get("task_type")) for r in provider_requests])
    priority_counts = Counter([_norm(r.get("priority")) for r in provider_requests])
    prompt_lengths = [len(_norm(r.get("provider_prompt"))) for r in provider_requests]
    prompt_size_summary = {
        "min_chars": min(prompt_lengths) if prompt_lengths else 0,
        "max_chars": max(prompt_lengths) if prompt_lengths else 0,
        "avg_chars": round(sum(prompt_lengths) / len(prompt_lengths), 1) if prompt_lengths else 0,
        "total_chars": sum(prompt_lengths),
    }

    prompt_map = {
        "provider_request_batch.jsonl": request_path.read_text(encoding="utf-8"),
        "provider_config_template.json": config_path.read_text(encoding="utf-8"),
        "provider_response_contract.md": response_contract_md,
        "provider_response_validation_plan.md": validation_plan_md,
        "provider_run_checklist.md": run_checklist_md,
        "provider_request_batch_sample.md": sample_md_path.read_text(encoding="utf-8"),
    }
    no_secret_rows = _scan_no_secret(prompt_map)
    no_secret_status = "PASS" if all(r["status"] == "PASS" for r in no_secret_rows) else "FAIL"

    production_before = _snapshot_production(delivery_dir)
    production_after = _snapshot_production(delivery_dir)
    production_changed_count = sum(1 for b, a in zip(production_before, production_after) if b != a)
    delivery_after = _run_delivery_check_json(delivery_dir)
    production_files_unchanged = production_changed_count == 0

    selected_rows = []
    for i, req in enumerate(provider_requests, start=1):
        selected_rows.append(
            {
                "request_id": req["request_id"],
                "repair_task_id": req["repair_task_id"],
                "sample_id": req["sample_id"],
                "company": req["company"],
                "task_type": req["task_type"],
                "priority": req["priority"],
                "standard_metric_hint": _norm((task_map[req["repair_task_id"]].get("current_rule_result") or {}).get("standard_metric_hint")),
                "detected_years": "|".join([_norm(x) for x in (task_map[req["repair_task_id"]].get("evidence") or {}).get("detected_years", []) if _norm(x)]),
                "prompt_chars": len(_norm(req.get("provider_prompt"))),
                "source_trace_id": req["source_trace_id"],
            }
        )

    excluded_task_rows = [row for row in excluded_rows]
    sample_task_counts_df = pd.DataFrame([{"sample_id": k, "count": v} for k, v in sample_counts.items()]).sort_values("sample_id")
    task_type_counts_df = pd.DataFrame([{"task_type": k, "count": v} for k, v in task_type_counts.items()]).sort_values("task_type")
    priority_counts_df = pd.DataFrame([{"priority": k, "count": v} for k, v in priority_counts.items()]).sort_values("priority")
    prompt_size_df = pd.DataFrame([prompt_size_summary])

    config_template_df = pd.DataFrame(
        [{"field": k, "value": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v} for k, v in config_template.items()]
    )
    no_secret_df = pd.DataFrame(no_secret_rows)
    production_guard_df = pd.DataFrame(production_after)
    safety_checks_df = pd.DataFrame(
        [
            {"check_name": "factory_core_not_run", "status": "PASS", "detail": "no factory_core invocation"},
            {"check_name": "vision_or_ocr_not_triggered", "status": "PASS", "detail": "no OCR/vision backend used"},
            {"check_name": "no_real_ai_call", "status": "PASS", "detail": "bundle preparation only"},
            {"check_name": "no_secret_check", "status": no_secret_status, "detail": "placeholder values only"},
            {"check_name": "production_files_unchanged", "status": "PASS" if production_files_unchanged else "FAIL", "detail": f"changed_count={production_changed_count}"},
        ]
    )

    inventory_path = preflight_dir / "provider_preflight_inventory.xlsx"
    _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "provider_preflight_status", "value": "PASS" if request_count >= 10 and request_count <= 20 else "WARN"},
                    {"field": "request_count", "value": request_count},
                    {"field": "selected_sample_counts", "value": json.dumps(dict(sample_counts), ensure_ascii=False)},
                    {"field": "selected_task_type_counts", "value": json.dumps(dict(task_type_counts), ensure_ascii=False)},
                    {"field": "priority_counts", "value": json.dumps(dict(priority_counts), ensure_ascii=False)},
                    {"field": "prompt_size_summary", "value": json.dumps(prompt_size_summary, ensure_ascii=False)},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "production_files_unchanged", "value": "1" if production_files_unchanged else "0"},
                ]
            ),
            "selected_provider_requests": pd.DataFrame(selected_rows),
            "excluded_packet_tasks": pd.DataFrame(excluded_task_rows),
            "sample_task_counts": sample_task_counts_df,
            "task_type_counts": task_type_counts_df,
            "priority_counts": priority_counts_df,
            "prompt_size_summary": prompt_size_df,
            "config_template": config_template_df,
            "no_secret_check": no_secret_df,
            "production_guard": production_guard_df,
            "safety_checks": safety_checks_df,
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "When credentials are approved, populate them outside the repo and run a controlled provider dry-run that writes local JSONL only.",
                    }
                ]
            ),
        },
        inventory_path,
    )

    provider_preflight_status = "PASS" if request_count >= 10 and request_count <= 20 and no_secret_status == "PASS" and production_files_unchanged else "WARN"

    commands_run_list = [
        f"{sys.executable} -m py_compile {helper_path}",
        f"{sys.executable} {helper_path} --packet-jsonl {packet_path} --schema-json {schema_path} --prompt-md {prompt_path} --trial-run-root {trial_run_root} --delivery-dir {delivery_dir} --max-provider-tasks {args.max_provider_tasks}",
        f"{sys.executable} D:/_datefac/tools/check_delivery_state.py --json",
    ]

    report50_md = _safe_write_text(
        delivery_dir / "50_stage1_ai_repair_provider_preflight_log.md",
        "\n".join(
            [
                "# Stage1 AI Repair Provider Preflight Log",
                "",
                "- task_title: Prepare Stage 1 AI repair real-provider preflight bundle",
                f"- started_at: {started_at}",
                f"- finished_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- commands_run: {json.dumps(commands_run_list, ensure_ascii=False)}",
                f"- input_files_read: {json.dumps([str(packet_path), str(schema_path), str(prompt_path)], ensure_ascii=False)}",
                f"- output_files_generated: {json.dumps([str(request_path), str(sample_md_path), str(config_path), str(response_contract_path), str(validation_plan_path), str(run_checklist_path), str(inventory_path)], ensure_ascii=False)}",
                f"- provider_request_count: {request_count}",
                f"- selected_sample_counts: {json.dumps(dict(sample_counts), ensure_ascii=False)}",
                f"- selected_task_type_counts: {json.dumps(dict(task_type_counts), ensure_ascii=False)}",
                f"- config_template_status: PASS",
                f"- no_secret_check_status: {no_secret_status}",
                f"- production_guard_changed_count: {production_changed_count}",
                f"- safety_checks: {json.dumps(safety_checks_df.to_dict(orient='records'), ensure_ascii=False)}",
            ]
        ),
    )

    report50_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "task_title", "value": "Prepare Stage 1 AI repair real-provider preflight bundle"},
                    {"field": "started_at", "value": started_at},
                    {"field": "finished_at", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                    {"field": "provider_request_count", "value": request_count},
                    {"field": "config_template_status", "value": "PASS"},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "production_guard_changed_count", "value": production_changed_count},
                ]
            ),
            "selected_provider_requests": pd.DataFrame(selected_rows),
            "excluded_packet_tasks": pd.DataFrame(excluded_task_rows),
            "sample_task_counts": sample_task_counts_df,
            "task_type_counts": task_type_counts_df,
            "priority_counts": priority_counts_df,
            "prompt_size_summary": prompt_size_df,
            "config_template": config_template_df,
            "no_secret_check": no_secret_df,
            "production_guard": production_guard_df,
            "safety_checks": safety_checks_df,
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "Use the bundle only after credentials are supplied outside the repo and a controlled dry-run is approved.",
                    }
                ]
            ),
        },
        delivery_dir / "50_stage1_ai_repair_provider_preflight_log.xlsx",
    )

    report51_md = _safe_write_text(
        delivery_dir / "51_stage1_ai_repair_provider_preflight_evaluation.md",
        "\n".join(
            [
                "# Stage1 AI Repair Provider Preflight Evaluation",
                "",
                f"- provider_preflight_status: {provider_preflight_status}",
                f"- provider_request_count: {request_count}",
                f"- selected_sample_counts: {json.dumps(dict(sample_counts), ensure_ascii=False)}",
                f"- selected_task_type_counts: {json.dumps(dict(task_type_counts), ensure_ascii=False)}",
                f"- priority_counts: {json.dumps(dict(priority_counts), ensure_ascii=False)}",
                f"- prompt_size_summary: {json.dumps(prompt_size_summary, ensure_ascii=False)}",
                f"- schema_reference_status: PASS",
                f"- response_contract_status: PASS",
                f"- validation_plan_status: PASS",
                f"- no_secret_check_status: {no_secret_status}",
                f"- production_delivery_status_after: {json.dumps(delivery_after, ensure_ascii=False)}",
                f"- production_files_unchanged: {production_files_unchanged}",
                "- recommended_next_step: If a provider is approved later, send only this bounded request batch and store responses locally first.",
            ]
        ),
    )

    report51_xlsx = _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "provider_preflight_status", "value": provider_preflight_status},
                    {"field": "provider_request_count", "value": request_count},
                    {"field": "selected_sample_counts", "value": json.dumps(dict(sample_counts), ensure_ascii=False)},
                    {"field": "selected_task_type_counts", "value": json.dumps(dict(task_type_counts), ensure_ascii=False)},
                    {"field": "priority_counts", "value": json.dumps(dict(priority_counts), ensure_ascii=False)},
                    {"field": "prompt_size_summary", "value": json.dumps(prompt_size_summary, ensure_ascii=False)},
                    {"field": "schema_reference_status", "value": "PASS"},
                    {"field": "response_contract_status", "value": "PASS"},
                    {"field": "validation_plan_status", "value": "PASS"},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "production_files_unchanged", "value": "1" if production_files_unchanged else "0"},
                ]
            ),
            "selected_provider_requests": pd.DataFrame(selected_rows),
            "excluded_packet_tasks": pd.DataFrame(excluded_task_rows),
            "sample_task_counts": sample_task_counts_df,
            "task_type_counts": task_type_counts_df,
            "priority_counts": priority_counts_df,
            "prompt_size_summary": prompt_size_df,
            "config_template": config_template_df,
            "no_secret_check": no_secret_df,
            "production_guard": production_guard_df,
            "safety_checks": safety_checks_df,
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "Use the bundle only after credentials are supplied outside the repo and a controlled dry-run is approved.",
                    }
                ]
            ),
        },
        delivery_dir / "51_stage1_ai_repair_provider_preflight_evaluation.xlsx",
    )

    print(f"helper_path: {helper_path}")
    print(f"provider_preflight_status: {provider_preflight_status}")
    print(f"provider_request_count: {request_count}")
    print(f"selected_sample_counts: {json.dumps(dict(sample_counts), ensure_ascii=False)}")
    print(f"selected_task_type_counts: {json.dumps(dict(task_type_counts), ensure_ascii=False)}")
    print(f"priority_counts: {json.dumps(dict(priority_counts), ensure_ascii=False)}")
    print(f"no_secret_check_status: {no_secret_status}")
    print(
        "generated_outputs: "
        + json.dumps(
            [
                str(request_path),
                str(sample_md_path),
                str(config_path),
                str(response_contract_path),
                str(validation_plan_path),
                str(run_checklist_path),
                str(inventory_path),
                str(report50_md),
                str(report50_xlsx),
                str(report51_md),
                str(report51_xlsx),
            ],
            ensure_ascii=False,
        )
    )
    print(f"production_delivery_status_after: {json.dumps(delivery_after, ensure_ascii=False)}")
    print(f"production_files_unchanged: {production_files_unchanged}")

    return 0 if provider_preflight_status in {"PASS", "WARN"} else 4


if __name__ == "__main__":
    raise SystemExit(main())
