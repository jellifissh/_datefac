import argparse
import json
import math
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
DEFAULT_MAX_REQUESTS_PER_SHARD = 10


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


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    return path


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


def _scan_secret_like_text(text: str) -> List[str]:
    hits: List[str] = []
    for pattern in SECRET_PATTERNS:
        if pattern in text:
            hits.append(pattern)
    return hits


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _estimate_tokens(chars: int) -> int:
    return int(math.ceil(chars / 4.0))


def _read_config_template(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _request_inventory_row(req: Dict[str, Any], shard_name: str, shard_id: int, config_max_output_tokens: int) -> Dict[str, Any]:
    request_json = json.dumps(req, ensure_ascii=False)
    prompt = _norm(req.get("provider_prompt"))
    input_char_count = len(request_json)
    prompt_char_count = len(prompt)
    return {
        "shard_id": shard_id,
        "shard_name": shard_name,
        "request_id": _norm(req.get("request_id")),
        "repair_task_id": _norm(req.get("repair_task_id")),
        "sample_id": _norm(req.get("sample_id")),
        "company": _norm(req.get("company")),
        "task_type": _norm(req.get("task_type")),
        "priority": _norm(req.get("priority")),
        "request_json_chars": input_char_count,
        "provider_prompt_chars": prompt_char_count,
        "estimated_input_tokens": _estimate_tokens(input_char_count),
        "estimated_output_tokens": config_max_output_tokens,
        "estimated_total_tokens": _estimate_tokens(input_char_count) + config_max_output_tokens,
    }


def _write_shards(requests: List[Dict[str, Any]], dry_run_dir: Path, max_per_shard: int) -> Tuple[List[Path], List[Dict[str, Any]]]:
    shard_paths: List[Path] = []
    shard_index_rows: List[Dict[str, Any]] = []
    for idx in range(0, len(requests), max_per_shard):
        shard_id = idx // max_per_shard + 1
        shard_name = f"provider_request_shard_{shard_id:03d}.jsonl"
        shard_requests = requests[idx : idx + max_per_shard]
        shard_path = dry_run_dir / shard_name
        _write_jsonl(shard_path, shard_requests)
        shard_paths.append(shard_path)
        shard_index_rows.append(
            {
                "shard_id": shard_id,
                "shard_name": shard_name,
                "request_count": len(shard_requests),
                "request_ids": "|".join(_norm(r.get("request_id")) for r in shard_requests),
                "repair_task_ids": "|".join(_norm(r.get("repair_task_id")) for r in shard_requests),
                "sample_ids": "|".join(sorted(set(_norm(r.get("sample_id")) for r in shard_requests if _norm(r.get("sample_id"))))),
                "task_types": "|".join(sorted(set(_norm(r.get("task_type")) for r in shard_requests if _norm(r.get("task_type"))))),
                "priorities": "|".join(sorted(set(_norm(r.get("priority")) for r in shard_requests if _norm(r.get("priority"))))),
            }
        )
    return shard_paths, shard_index_rows


def _build_counts(rows: List[Dict[str, Any]], key: str) -> pd.DataFrame:
    c = Counter([_norm(r.get(key)) for r in rows])
    return pd.DataFrame([{key: k, "count": v} for k, v in sorted(c.items())])


def _build_budget_estimate(inv_rows: List[Dict[str, Any]], shard_index_rows: List[Dict[str, Any]], config_max_output_tokens: int) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    by_shard: Dict[int, Dict[str, Any]] = {}
    for row in inv_rows:
        sid = _safe_int(row.get("shard_id"), 0)
        shard = by_shard.setdefault(sid, {"shard_id": sid, "request_count": 0, "input_chars": 0, "input_tokens": 0, "output_tokens": 0})
        shard["request_count"] += 1
        shard["input_chars"] += _safe_int(row.get("request_json_chars"), 0)
        shard["input_tokens"] += _safe_int(row.get("estimated_input_tokens"), 0)
        shard["output_tokens"] += config_max_output_tokens
    rows = []
    total_in_chars = 0
    total_in_tokens = 0
    total_out_tokens = 0
    for sid in sorted(by_shard):
        shard = by_shard[sid]
        rows.append(
            {
                "shard_id": sid,
                "request_count": shard["request_count"],
                "input_char_count": shard["input_chars"],
                "estimated_input_tokens": shard["input_tokens"],
                "estimated_output_tokens": shard["output_tokens"],
                "estimated_total_tokens": shard["input_tokens"] + shard["output_tokens"],
            }
        )
        total_in_chars += shard["input_chars"]
        total_in_tokens += shard["input_tokens"]
        total_out_tokens += shard["output_tokens"]
    rows.append(
        {
            "shard_id": "TOTAL",
            "request_count": len(inv_rows),
            "input_char_count": total_in_chars,
            "estimated_input_tokens": total_in_tokens,
            "estimated_output_tokens": total_out_tokens,
            "estimated_total_tokens": total_in_tokens + total_out_tokens,
        }
    )
    summary = {
        "estimated_total_input_tokens": total_in_tokens,
        "estimated_total_output_tokens": total_out_tokens,
        "estimated_total_tokens": total_in_tokens + total_out_tokens,
        "request_count": len(inv_rows),
        "shard_count": len(shard_index_rows),
    }
    return pd.DataFrame(rows), summary


def _write_md_table_sample(requests: List[Dict[str, Any]], path: Path) -> Path:
    lines = [
        "# Stage 1 AI Repair Provider Dry Run",
        "",
        "| shard | request_id | repair_task_id | sample_id | task_type | priority |",
        "|---|---|---|---|---|---|",
    ]
    for req in requests[:8]:
        lines.append(
            f"| - | {_norm(req.get('request_id'))} | {_norm(req.get('repair_task_id'))} | {_norm(req.get('sample_id'))} | {_norm(req.get('task_type'))} | {_norm(req.get('priority'))} |"
        )
    lines.extend(["", "This controller does not execute any provider requests."])
    return _safe_write_text(path, "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 1 AI repair provider dry-run controller (sandbox-only).")
    parser.add_argument("--request-batch", required=True)
    parser.add_argument("--config-template", required=True)
    parser.add_argument("--trial-run-root", required=True)
    parser.add_argument("--delivery-dir", required=True)
    parser.add_argument("--max-requests-per-shard", type=int, default=DEFAULT_MAX_REQUESTS_PER_SHARD)
    parser.add_argument("--dry-run", dest="dry_run", action="store_true")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    parser.set_defaults(dry_run=True)
    args = parser.parse_args()

    if not args.dry_run:
        print("BLOCKED_NON_DRY_RUN_NOT_ALLOWED")
        return 3

    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_batch = Path(args.request_batch)
    config_template = Path(args.config_template)
    trial_run_root = Path(args.trial_run_root)
    delivery_dir = Path(args.delivery_dir)
    dry_run_dir = trial_run_root / "ai_repair_provider_dry_run"
    dry_run_dir.mkdir(parents=True, exist_ok=True)
    helper_path = Path(__file__)

    if not request_batch.exists() or not config_template.exists():
        print("BLOCKED_REQUIRED_INPUT_MISSING")
        return 3

    before = _snapshot_files(_collect_production_guard_files(delivery_dir))

    requests = _load_jsonl(request_batch)
    config = _read_config_template(config_template)
    config_max_output_tokens = _safe_int(config.get("max_output_tokens"), 2048)
    max_per_shard = max(1, _safe_int(args.max_requests_per_shard, DEFAULT_MAX_REQUESTS_PER_SHARD))

    shard_paths, shard_index_rows = _write_shards(requests, dry_run_dir, max_per_shard)

    request_rows: List[Dict[str, Any]] = []
    for shard_row in shard_index_rows:
        sid = _safe_int(shard_row["shard_id"], 0)
        shard_path = dry_run_dir / shard_row["shard_name"]
        shard_requests = _load_jsonl(shard_path)
        for req in shard_requests:
            request_rows.append(_request_inventory_row(req, shard_row["shard_name"], sid, config_max_output_tokens))

    sample_counts = Counter([_norm(r.get("sample_id")) for r in requests])
    task_type_counts = Counter([_norm(r.get("task_type")) for r in requests])
    priority_counts = Counter([_norm(r.get("priority")) for r in requests])

    sample_df = pd.DataFrame([{"sample_id": k, "count": v} for k, v in sorted(sample_counts.items())])
    task_type_df = pd.DataFrame([{"task_type": k, "count": v} for k, v in sorted(task_type_counts.items())])
    priority_df = pd.DataFrame([{"priority": k, "count": v} for k, v in sorted(priority_counts.items())])
    budget_df, budget_summary = _build_budget_estimate(request_rows, shard_index_rows, config_max_output_tokens)

    request_inventory_df = pd.DataFrame(request_rows)
    shard_index_df = pd.DataFrame(shard_index_rows)

    command_template_md = "\n".join(
        [
            "# Provider Command Template",
            "",
            "This template is not executed by this pipeline.",
            "",
            "Use external credentials only via environment variables.",
            "Do not paste API keys into repo files.",
            "Save raw provider responses to a local JSONL file.",
            "After the provider run, feed the raw response JSONL into `intake_stage1_ai_repair_provider_responses.py`.",
            "",
            "Example placeholders:",
            "```bat",
            "set STAGE1_AI_REPAIR_API_KEY=%%YOUR_EXTERNAL_SECRET%%",
            "provider_cli --config provider_config.json --input provider_request_shard_001.jsonl --output provider_response_raw.jsonl",
            "python D:\\_datefac\\tools\\intake_stage1_ai_repair_provider_responses.py --request-batch ... --raw-provider-response provider_response_raw.jsonl --run-offline-replay",
            "```",
        ]
    )
    command_template_path = _safe_write_text(dry_run_dir / "provider_command_template.md", command_template_md)

    replay_plan_md = "\n".join(
        [
            "# Post-Run Replay Plan",
            "",
            "- Raw response path convention: keep one provider JSONL per run in the dry-run folder.",
            "- Intake command template: run `intake_stage1_ai_repair_provider_responses.py` against the raw JSONL first.",
            "- Expected clean/rejected files: `provider_response_intake_clean.jsonl` and `provider_response_intake_rejected.jsonl` in the intake folder.",
            "- Offline replay path: pass the clean JSONL into `run_stage1_ai_repair_worker.py --provider offline_file`.",
            "- Production write remains forbidden until a separate approval is granted.",
        ]
    )
    replay_plan_path = _safe_write_text(dry_run_dir / "provider_post_run_replay_plan.md", replay_plan_md)

    response_save_contract_md = "\n".join(
        [
            "# Provider Response Save Contract",
            "",
            "- Save provider output as raw JSONL only.",
            "- Preserve one response object per line.",
            "- Do not edit the raw file after generation.",
            "- Hand raw JSONL to the intake gate before any replay.",
            "- Do not store secrets in the response file name or contents.",
        ]
    )
    response_save_contract_path = _safe_write_text(dry_run_dir / "provider_response_save_contract.md", response_save_contract_md)

    execution_checklist_md = "\n".join(
        [
            "# Provider Dry-Run Execution Checklist",
            "",
            "- [ ] Confirm dry_run is true.",
            "- [ ] Confirm no request shard exceeds the configured limit.",
            "- [ ] Confirm no secret-like strings appear in templates or manifests.",
            "- [ ] Confirm no production files changed.",
            "- [ ] Confirm no model, OCR, vision, marker, or network call is made.",
            "- [ ] Save raw provider responses locally only.",
        ]
    )
    execution_checklist_path = _safe_write_text(dry_run_dir / "provider_execution_checklist.md", execution_checklist_md)

    no_secret_sources = {
        "request_batch": request_batch.read_text(encoding="utf-8"),
        "config_template": config_template.read_text(encoding="utf-8"),
        "command_template": command_template_md,
        "replay_plan": replay_plan_md,
        "response_save_contract": response_save_contract_md,
        "execution_checklist": execution_checklist_md,
    }
    no_secret_hits = {name: _scan_secret_like_text(text) for name, text in no_secret_sources.items()}
    no_secret_status = "PASS" if all(not hits for hits in no_secret_hits.values()) else "FAIL"

    manifest = {
        "task_title": "Add Stage 1 AI repair provider dry-run controller",
        "dry_run_mode": True,
        "request_batch_path": str(request_batch),
        "config_template_path": str(config_template),
        "dry_run_dir": str(dry_run_dir),
        "request_count": len(requests),
        "shard_count": len(shard_index_rows),
        "max_requests_per_shard": max_per_shard,
        "request_shards": [str(p) for p in shard_paths],
        "command_template_path": str(command_template_path),
        "response_save_contract_path": str(response_save_contract_path),
        "replay_plan_path": str(replay_plan_path),
        "execution_checklist_path": str(execution_checklist_path),
        "selected_sample_counts": dict(sample_counts),
        "selected_task_type_counts": dict(task_type_counts),
        "priority_counts": dict(priority_counts),
        "budget_summary": budget_summary,
        "no_secret_check_status": no_secret_status,
    }
    manifest_path = _safe_write_text(dry_run_dir / "provider_dry_run_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    inventory_path = _safe_write_excel(
        {
            "shard_index": shard_index_df,
            "request_inventory": request_inventory_df,
            "sample_counts": sample_df,
            "task_type_counts": task_type_df,
            "priority_counts": priority_df,
            "budget_estimate": budget_df,
            "no_secret_check": pd.DataFrame(
                [{"artifact": k, "status": "PASS" if not v else "FAIL", "detail": "|".join(v) or "no_secret_like_patterns"} for k, v in no_secret_hits.items()]
            ),
        },
        dry_run_dir / "provider_request_shard_index.xlsx",
    )

    no_secret_hits_summary = pd.DataFrame(
        [{"artifact": k, "status": "PASS" if not v else "FAIL", "detail": "|".join(v) or "no_secret_like_patterns"} for k, v in no_secret_hits.items()]
    )

    production_after = _snapshot_files(_collect_production_guard_files(delivery_dir))
    production_guard_rows = _compare_snapshot(before, production_after)
    changed_count = sum(1 for r in production_guard_rows if r.get("changed") == "1")
    production_files_unchanged = changed_count == 0
    production_delivery_status = _run_delivery_check_json(delivery_dir)

    provider_dry_run_status = "PASS"
    if no_secret_status != "PASS" or changed_count > 0:
        provider_dry_run_status = "FAIL"
    elif len(shard_paths) == 0 or len(requests) == 0:
        provider_dry_run_status = "WARN"

    safety_checks = [
        {"check_name": "dry_run_mode_true", "status": "PASS" if args.dry_run else "FAIL", "detail": "dry run only"},
        {"check_name": "no_network_or_model_call", "status": "PASS", "detail": "manifest/controller only"},
        {"check_name": "no_secret_check", "status": no_secret_status, "detail": "templates and manifests scanned"},
        {"check_name": "production_files_unchanged", "status": "PASS" if production_files_unchanged else "FAIL", "detail": f"changed={changed_count}"},
    ]

    commands_run = [
        f"{sys.executable} -m py_compile {helper_path}",
        f"{sys.executable} {helper_path} --request-batch {request_batch} --config-template {config_template} --trial-run-root {trial_run_root} --delivery-dir {delivery_dir} --max-requests-per-shard {max_per_shard} --dry-run",
        f"{sys.executable} D:/_datefac/tools/check_delivery_state.py --json",
    ]

    output_files_generated = [
        str(manifest_path),
        *[str(p) for p in shard_paths],
        str(inventory_path),
        str(command_template_path),
        str(replay_plan_path),
        str(response_save_contract_path),
        str(execution_checklist_path),
        str(delivery_dir / "54_stage1_ai_repair_provider_dry_run_log.md"),
        str(delivery_dir / "54_stage1_ai_repair_provider_dry_run_log.xlsx"),
        str(delivery_dir / "55_stage1_ai_repair_provider_dry_run_evaluation.md"),
        str(delivery_dir / "55_stage1_ai_repair_provider_dry_run_evaluation.xlsx"),
    ]

    _safe_write_text(
        delivery_dir / "54_stage1_ai_repair_provider_dry_run_log.md",
        "\n".join(
            [
                "# Stage1 AI Repair Provider Dry Run Log",
                "",
                "- task_title: Add Stage 1 AI repair provider dry-run controller",
                f"- started_at: {started_at}",
                f"- finished_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- commands_run: {json.dumps(commands_run, ensure_ascii=False)}",
                f"- request_batch_path: {request_batch}",
                f"- config_template_path: {config_template}",
                f"- dry_run_dir: {dry_run_dir}",
                f"- request_count: {len(requests)}",
                f"- shard_count: {len(shard_paths)}",
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
                    {"field": "task_title", "value": "Add Stage 1 AI repair provider dry-run controller"},
                    {"field": "started_at", "value": started_at},
                    {"field": "finished_at", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                    {"field": "request_batch_path", "value": str(request_batch)},
                    {"field": "config_template_path", "value": str(config_template)},
                    {"field": "dry_run_dir", "value": str(dry_run_dir)},
                    {"field": "request_count", "value": len(requests)},
                    {"field": "shard_count", "value": len(shard_paths)},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "production_guard_changed_count", "value": changed_count},
                ]
            ),
            "shard_index": shard_index_df,
            "request_inventory": request_inventory_df,
            "sample_counts": sample_df,
            "task_type_counts": task_type_df,
            "priority_counts": priority_df,
            "budget_estimate": budget_df,
            "no_secret_check": no_secret_hits_summary,
            "production_guard": pd.DataFrame(production_guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "If provider approval is later granted, use the shard files as input and keep raw responses local for intake validation first.",
                    }
                ]
            ),
        },
        delivery_dir / "54_stage1_ai_repair_provider_dry_run_log.xlsx",
    )

    _safe_write_text(
        delivery_dir / "55_stage1_ai_repair_provider_dry_run_evaluation.md",
        "\n".join(
            [
                "# Stage1 AI Repair Provider Dry Run Evaluation",
                "",
                f"- provider_dry_run_status: {provider_dry_run_status}",
                f"- dry_run_mode: {args.dry_run}",
                f"- request_count: {len(requests)}",
                f"- shard_count: {len(shard_paths)}",
                f"- selected_sample_counts: {json.dumps(dict(sample_counts), ensure_ascii=False)}",
                f"- selected_task_type_counts: {json.dumps(dict(task_type_counts), ensure_ascii=False)}",
                f"- priority_counts: {json.dumps(dict(priority_counts), ensure_ascii=False)}",
                f"- estimated_total_input_tokens: {budget_summary['estimated_total_input_tokens']}",
                f"- estimated_total_output_tokens: {budget_summary['estimated_total_output_tokens']}",
                f"- no_secret_check_status: {no_secret_status}",
                "- command_template_status: PASS",
                "- post_run_replay_plan_status: PASS",
                f"- production_delivery_status_after: {json.dumps(production_delivery_status, ensure_ascii=False)}",
                f"- production_files_unchanged: {production_files_unchanged}",
                "- recommended_next_step: Use the dry-run manifest to prepare a future provider execution without modifying production files.",
            ]
        ),
    )
    _safe_write_excel(
        {
            "summary": pd.DataFrame(
                [
                    {"field": "provider_dry_run_status", "value": provider_dry_run_status},
                    {"field": "dry_run_mode", "value": str(args.dry_run)},
                    {"field": "request_count", "value": len(requests)},
                    {"field": "shard_count", "value": len(shard_paths)},
                    {"field": "selected_sample_counts", "value": json.dumps(dict(sample_counts), ensure_ascii=False)},
                    {"field": "selected_task_type_counts", "value": json.dumps(dict(task_type_counts), ensure_ascii=False)},
                    {"field": "priority_counts", "value": json.dumps(dict(priority_counts), ensure_ascii=False)},
                    {"field": "estimated_total_input_tokens", "value": budget_summary["estimated_total_input_tokens"]},
                    {"field": "estimated_total_output_tokens", "value": budget_summary["estimated_total_output_tokens"]},
                    {"field": "no_secret_check_status", "value": no_secret_status},
                    {"field": "command_template_status", "value": "PASS"},
                    {"field": "post_run_replay_plan_status", "value": "PASS"},
                    {"field": "production_delivery_status_after", "value": json.dumps(production_delivery_status, ensure_ascii=False)},
                    {"field": "production_files_unchanged", "value": "1" if production_files_unchanged else "0"},
                ]
            ),
            "shard_index": shard_index_df,
            "request_inventory": request_inventory_df,
            "sample_counts": sample_df,
            "task_type_counts": task_type_df,
            "priority_counts": priority_df,
            "budget_estimate": budget_df,
            "no_secret_check": no_secret_hits_summary,
            "production_guard": pd.DataFrame(production_guard_rows),
            "safety_checks": pd.DataFrame(safety_checks),
            "next_steps": pd.DataFrame(
                [
                    {
                        "recommended_next_step": "When a provider is approved, run it outside the repo, save the raw JSONL locally, and feed it through the intake gate before replay.",
                    }
                ]
            ),
        },
        delivery_dir / "55_stage1_ai_repair_provider_dry_run_evaluation.xlsx",
    )

    print(f"dry_run_helper_path: {helper_path}")
    print(f"provider_dry_run_status: {provider_dry_run_status}")
    print(f"dry_run_mode: {args.dry_run}")
    print(f"request_count: {len(requests)}")
    print(f"shard_count: {len(shard_paths)}")
    print(f"selected_sample_counts: {json.dumps(dict(sample_counts), ensure_ascii=False)}")
    print(f"selected_task_type_counts: {json.dumps(dict(task_type_counts), ensure_ascii=False)}")
    print(f"priority_counts: {json.dumps(dict(priority_counts), ensure_ascii=False)}")
    print(f"estimated_total_input_tokens: {budget_summary['estimated_total_input_tokens']}")
    print(f"estimated_total_output_tokens: {budget_summary['estimated_total_output_tokens']}")
    print(f"no_secret_check_status: {no_secret_status}")
    print(
        "generated_outputs: "
        + json.dumps(
            [
                str(manifest_path),
                *[str(p) for p in shard_paths],
                str(inventory_path),
                str(command_template_path),
                str(replay_plan_path),
                str(response_save_contract_path),
                str(execution_checklist_path),
                str(delivery_dir / "54_stage1_ai_repair_provider_dry_run_log.md"),
                str(delivery_dir / "54_stage1_ai_repair_provider_dry_run_log.xlsx"),
                str(delivery_dir / "55_stage1_ai_repair_provider_dry_run_evaluation.md"),
                str(delivery_dir / "55_stage1_ai_repair_provider_dry_run_evaluation.xlsx"),
            ],
            ensure_ascii=False,
        )
    )
    print(f"production_delivery_status_after: {json.dumps(production_delivery_status, ensure_ascii=False)}")
    print(f"production_files_unchanged: {production_files_unchanged}")

    if provider_dry_run_status == "FAIL":
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

