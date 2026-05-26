from __future__ import annotations

import importlib.metadata as im
import importlib.util
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "output" / "eval_marker1a_environment_and_history_audit"

MARKER1_SUMMARY = (
    BASE_DIR
    / "output"
    / "eval_marker1_no_llm_parser_benchmark"
    / "304_eval_marker1_no_llm_benchmark_summary.json"
)
MARKER1_AVAIL = (
    BASE_DIR
    / "output"
    / "eval_marker1_no_llm_parser_benchmark"
    / "304_eval_marker1_marker_availability.json"
)
OLD_STAGE5B_SUMMARY = (
    BASE_DIR
    / "output"
    / "stage5b_table_extraction_restore"
    / "129_stage5b_table_extraction_restore_summary.json"
)
BENCH_SCRIPT = BASE_DIR / "tools" / "run_eval_marker1_no_llm_parser_benchmark.py"
EXTRACT_STAGE5B_SCRIPT = BASE_DIR / "tools" / "extract_stage5b_pdf_raw_tables.py"

OUT_SUMMARY = OUT_DIR / "305a_marker_environment_history_audit_summary.json"
OUT_REPORT = OUT_DIR / "305a_marker_environment_history_audit_report.md"
OUT_INV = OUT_DIR / "305a_marker_related_files_inventory.xlsx"
OUT_NO_APPLY = OUT_DIR / "305a_no_apply_proof.json"

INVENTORY_ROOTS = [
    BASE_DIR / "tools",
    BASE_DIR / "docs" / "codex_tasks",
    BASE_DIR / "output" / "eval_marker1_no_llm_parser_benchmark",
    BASE_DIR / "output" / "stage5b_table_extraction_restore",
]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _detect_marker_env() -> Dict[str, Any]:
    marker_importable = importlib.util.find_spec("marker") is not None
    marker_cli_path = shutil.which("marker") or ""
    marker_cli_available = bool(marker_cli_path)

    marker_version = ""
    for pkg_name in ("marker-pdf", "marker"):
        try:
            marker_version = im.version(pkg_name)
            if marker_version:
                break
        except Exception:
            continue

    marker_cli_version_output = ""
    marker_cli_version_ok = False
    if marker_cli_available:
        try:
            run = subprocess.run(
                [marker_cli_path, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
            out = (run.stdout or "").strip()
            err = (run.stderr or "").strip()
            marker_cli_version_output = out or err
            marker_cli_version_ok = run.returncode == 0
        except Exception as exc:
            marker_cli_version_output = f"{type(exc).__name__}: {exc}"

    return {
        "marker_importable": marker_importable,
        "marker_cli_available": marker_cli_available,
        "marker_cli_path": marker_cli_path,
        "marker_version": marker_version,
        "marker_cli_version_ok": marker_cli_version_ok,
        "marker_cli_version_output": marker_cli_version_output,
        "marker_available": bool(marker_importable and marker_cli_available),
    }


def _extract_no_llm_command_template() -> Dict[str, Any]:
    if not BENCH_SCRIPT.exists():
        return {"command_template": "", "command_found": False, "offline_flags_found": False}

    text = BENCH_SCRIPT.read_text(encoding="utf-8")

    cmd_tokens: List[str] = []
    m = re.search(r"marker_cmd\s*=\s*\[(.*?)\]\s*", text, flags=re.S)
    if m:
        body = m.group(1)
        for token in re.findall(r'"([^"]+)"', body):
            cmd_tokens.append(token)

    offline_flags_found = "HF_HUB_OFFLINE" in text and "TRANSFORMERS_OFFLINE" in text
    command_template = ""
    if cmd_tokens:
        command_template = (
            "marker <input_dir> --output_dir <output_dir> --output_format json "
            "--disable_ocr --disable_multiprocessing --skip_existing --max_files <N>"
        )
    return {
        "command_template": command_template,
        "command_found": bool(cmd_tokens),
        "offline_flags_found": offline_flags_found,
    }


def _run_check_delivery_state_status() -> str:
    cmd = ["python", str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"]
    try:
        run = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=120)
        if run.returncode != 0:
            return "ERROR"
        payload = json.loads((run.stdout or "").strip() or "{}")
        return str(payload.get("overall_status", "UNKNOWN"))
    except Exception:
        return "ERROR"


def _inventory_marker_files() -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for root in INVENTORY_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if "marker" not in p.name.lower() and "marker" not in str(p).lower():
                continue
            try:
                stat = p.stat()
                rows.append(
                    {
                        "path": str(p),
                        "relative_path": str(p.relative_to(BASE_DIR)),
                        "size_bytes": int(stat.st_size),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                        "area": str(root.relative_to(BASE_DIR)),
                    }
                )
            except Exception:
                continue
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["area", "relative_path"]).reset_index(drop=True)
    return df


def _collect_historical_failure_evidence() -> Dict[str, Any]:
    evidence_rows: List[Dict[str, str]] = []
    likely_reason = "unknown_no_direct_evidence"

    if OLD_STAGE5B_SUMMARY.exists():
        old = _load_json(OLD_STAGE5B_SUMMARY)
        marker_error_reason = str(old.get("marker_error_reason", "")).strip()
        fallback_extractor = str(old.get("fallback_extractor", "")).strip()
        if marker_error_reason:
            evidence_rows.append(
                {
                    "source": str(OLD_STAGE5B_SUMMARY.relative_to(BASE_DIR)),
                    "evidence": f"marker_error_reason={marker_error_reason}",
                }
            )
        if fallback_extractor:
            evidence_rows.append(
                {
                    "source": str(OLD_STAGE5B_SUMMARY.relative_to(BASE_DIR)),
                    "evidence": f"fallback_extractor={fallback_extractor}",
                }
            )
        if marker_error_reason == "marker_markdown_cache_missing_for_pdf":
            likely_reason = "old_marker_cache_path_depended_on_existing_markdown_cache_but_cache_was_missing"
        elif marker_error_reason == "marker_module_not_installed":
            likely_reason = "marker_module_missing_in_old_runtime"
        elif marker_error_reason:
            likely_reason = f"historical_marker_error:{marker_error_reason}"

    if EXTRACT_STAGE5B_SCRIPT.exists():
        lines = EXTRACT_STAGE5B_SCRIPT.read_text(encoding="utf-8").splitlines()
        probes = [
            "marker_module_not_installed",
            "marker_markdown_cache_missing_for_pdf",
            "stage5a did not have marker cache entrypoint wired",
        ]
        for idx, line in enumerate(lines, start=1):
            for token in probes:
                if token in line:
                    evidence_rows.append(
                        {
                            "source": f"{EXTRACT_STAGE5B_SCRIPT.relative_to(BASE_DIR)}:{idx}",
                            "evidence": line.strip(),
                        }
                    )
                    break

    return {
        "likely_old_marker_failure_reason": likely_reason,
        "evidence_rows": evidence_rows,
        "evidence_found": bool(evidence_rows),
    }


def _policy_notes(command_template: str) -> List[str]:
    return [
        "Preflight both import and CLI: require marker importable and marker CLI path resolvable before run.",
        "Use no-LLM local mode only; never enable any Marker LLM option in this project path.",
        "Use offline guards for reproducibility: HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1.",
        "Stable command template: "
        + (command_template or "marker <input_dir> --output_dir <out_dir> --output_format json --disable_ocr --disable_multiprocessing --skip_existing --max_files <N>"),
        "Do not rely on legacy markdown-cache-only path as primary input; treat cache absence as expected and use direct CLI parse for eval runs.",
        "Keep Marker outputs isolated in eval-specific output folders and avoid committing bulky raw runtime artifacts.",
    ]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    eval_marker1_summary_loaded = MARKER1_SUMMARY.exists()
    eval_marker1_availability_loaded = MARKER1_AVAIL.exists()
    marker1_summary = _load_json(MARKER1_SUMMARY) if eval_marker1_summary_loaded else {}
    marker1_avail = _load_json(MARKER1_AVAIL) if eval_marker1_availability_loaded else {}

    env_info = _detect_marker_env()
    cmd_info = _extract_no_llm_command_template()
    inv_df = _inventory_marker_files()
    history = _collect_historical_failure_evidence()
    policy = _policy_notes(cmd_info.get("command_template", ""))

    evidence_df = pd.DataFrame(history["evidence_rows"])
    if evidence_df.empty:
        evidence_df = pd.DataFrame([{"source": "", "evidence": ""}])

    delivery_status = _run_check_delivery_state_status()

    summary: Dict[str, Any] = {
        "stage": "EVAL-MARKER-1A-ENV",
        "mode": "marker_environment_and_history_audit_only",
        "external_api_called": False,
        "llm_api_called": False,
        "ocr_called": False,
        "marker_rerun_executed": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval_marker1_summary_loaded": eval_marker1_summary_loaded,
        "eval_marker1_availability_loaded": eval_marker1_availability_loaded,
        "marker_available": bool(env_info["marker_available"]),
        "marker_importable": bool(env_info["marker_importable"]),
        "marker_cli_available": bool(env_info["marker_cli_available"]),
        "marker_cli_path": env_info["marker_cli_path"],
        "marker_version": env_info["marker_version"],
        "marker_cli_version_ok": bool(env_info["marker_cli_version_ok"]),
        "command_template_found": bool(cmd_info["command_found"]),
        "offline_flags_found": bool(cmd_info["offline_flags_found"]),
        "current_successful_no_llm_command_template": cmd_info["command_template"],
        "marker_related_file_inventory_generated": True,
        "marker_related_file_count": int(len(inv_df)),
        "likely_old_marker_failure_reason": history["likely_old_marker_failure_reason"],
        "historical_failure_evidence_found": bool(history["evidence_found"]),
        "recommended_stable_marker_invocation_policy_generated": True,
        "production_files_modified": False,
        "official_02b_modified": False,
        "formal_rules_modified": False,
        "standardizer_modified": False,
        "release_package_modified": False,
        "check_delivery_state_overall_status": delivery_status,
        "reference_eval_marker1_marker_available": bool(marker1_summary.get("marker_available", marker1_avail.get("marker_available", False))),
        "reference_eval_marker1_marker_version": str(marker1_summary.get("marker_version", marker1_avail.get("marker_version", ""))),
    }

    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# 305A Marker Environment and History Audit",
        "",
        "## Runtime Audit",
        f"- marker_available: {summary['marker_available']}",
        f"- marker_version: {summary['marker_version']}",
        f"- marker_cli_path: `{summary['marker_cli_path']}`",
        f"- marker_importable: {summary['marker_importable']}",
        f"- marker_cli_available: {summary['marker_cli_available']}",
        f"- marker_cli_version_ok: {summary['marker_cli_version_ok']}",
        f"- marker_cli_version_output: `{env_info['marker_cli_version_output']}`",
        "",
        "## Current Successful No-LLM Command",
        f"- command_template_found: {summary['command_template_found']}",
        f"- offline_flags_found: {summary['offline_flags_found']}",
        f"- command: `{summary['current_successful_no_llm_command_template']}`",
        "",
        "## Historical Evidence",
        f"- likely_old_marker_failure_reason: {summary['likely_old_marker_failure_reason']}",
        f"- historical_failure_evidence_found: {summary['historical_failure_evidence_found']}",
    ]
    for row in history["evidence_rows"]:
        report_lines.append(f"- evidence: `{row['source']}` -> {row['evidence']}")

    report_lines.extend(
        [
            "",
            "## Recommended Stable Marker Invocation Policy",
        ]
    )
    for note in policy:
        report_lines.append(f"- {note}")

    report_lines.extend(
        [
            "",
            "## Safety",
            "- external_api_called: false",
            "- llm_api_called: false",
            "- ocr_called: false",
            "- marker_rerun_executed: false",
            "- real_apply_executed: false",
            "- sandbox_apply_attempt_count: 0",
            "- production_apply_attempt_count: 0",
        ]
    )

    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    with pd.ExcelWriter(OUT_INV, engine="openpyxl") as writer:
        inv_df.to_excel(writer, index=False, sheet_name="marker_related_files")
        evidence_df.to_excel(writer, index=False, sheet_name="history_evidence")
        pd.DataFrame({"policy_note": policy}).to_excel(writer, index=False, sheet_name="stable_policy")

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "ocr_called": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
            "marker_rerun_executed": False,
        },
    )

    print(f"audit_summary_json: {OUT_SUMMARY}")
    print(f"audit_report_md: {OUT_REPORT}")
    print(f"audit_inventory_xlsx: {OUT_INV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
