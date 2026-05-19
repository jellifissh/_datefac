import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_OUTPUT_ROOT = Path(r"D:\_datefac\output")
DEFAULT_DELIVERY_DIR = Path(r"D:\_datefac\output\delivery_package")
BASELINE_GUARD_PDF = "H3_AP202605091822098939_1.pdf"

PRODUCTION_GUARD_FILES = [
    "01_自动可信核心指标.xlsx",
    "02_人工复核指标队列.xlsx",
    "02A_人工年份修正覆盖表.xlsx",
    "06_最终核心财务指标.xlsx",
]

SAFE_ENTRYPOINT_CANDIDATES = [
    r"D:\_datefac\tools\probe_pdf_tables.py",
    r"D:\_datefac\tools\probe_pdfplumber_profiles.py",
    r"D:\_datefac\tools\probe_extractors.py",
    r"D:\_datefac\tools\build_manual_review_queue.py",
    r"D:\_datefac\tools\validate_financial_metric_values.py",
    r"D:\_datefac\tools\build_delivery_package.py",
    r"D:\_datefac\tools\apply_manual_review_corrections.py",
    r"D:\_datefac\tools\check_delivery_state.py",
]

UNSAFE_ENTRYPOINTS = [
    ("D:\\_datefac\\factory_core.py", "forbidden: factory_core entrypoint"),
    ("D:\\_datefac\\tools\\probe_visual_table_regions.py", "forbidden: vision-related probe"),
    ("D:\\_datefac\\tools\\check_vision_dependencies.py", "forbidden: vision dependency chain"),
    ("D:\\_datefac\\tools\\prewarm_marker_models.py", "forbidden: may trigger model downloads"),
]


@dataclass
class SampleItem:
    pdf_path: Path
    approved_pages: str = ""
    ignored_pages: str = ""
    source: str = ""


def _norm(v) -> str:
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
    with pd.ExcelWriter(final, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return final


def _load_manifest(manifest_path: Path) -> Tuple[List[SampleItem], List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    items = payload.get("samples", payload if isinstance(payload, list) else [])
    samples: List[SampleItem] = []
    for idx, item in enumerate(items):
        if isinstance(item, str):
            pdf = Path(item)
            samples.append(SampleItem(pdf_path=pdf, source="manifest"))
            rows.append({"idx": str(idx), "pdf": str(pdf), "approved_pages": "", "ignored_pages": ""})
            continue
        if isinstance(item, dict):
            pdf = Path(_norm(item.get("pdf") or item.get("pdf_path")))
            approved = _norm(item.get("approved_pages"))
            ignored = _norm(item.get("ignored_pages"))
            samples.append(SampleItem(pdf_path=pdf, approved_pages=approved, ignored_pages=ignored, source="manifest"))
            rows.append({"idx": str(idx), "pdf": str(pdf), "approved_pages": approved, "ignored_pages": ignored})
            continue
    return samples, rows


def _load_samples(manifest: Optional[Path], pdf_args: List[str]) -> Tuple[List[SampleItem], List[Dict[str, str]]]:
    if manifest and pdf_args:
        raise ValueError("Use either --manifest or --pdf, not both.")
    if not manifest and not pdf_args:
        raise ValueError("Must provide --manifest or at least one --pdf.")

    source_rows: List[Dict[str, str]] = []
    if manifest:
        return _load_manifest(manifest)

    samples = [SampleItem(pdf_path=Path(p), source="cli_pdf") for p in pdf_args]
    for i, s in enumerate(samples):
        source_rows.append({"idx": str(i), "pdf": str(s.pdf_path), "approved_pages": "", "ignored_pages": ""})
    return samples, source_rows


def _discover_safe_entrypoints() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    safe_rows: List[Dict[str, str]] = []
    for p in SAFE_ENTRYPOINT_CANDIDATES:
        pp = Path(p)
        safe_rows.append(
            {
                "entrypoint": p,
                "exists": "1" if pp.exists() else "0",
                "safety_level": "safe_probe_or_downstream",
                "notes": "non-vision script candidate",
            }
        )

    unsafe_rows = []
    for p, reason in UNSAFE_ENTRYPOINTS:
        unsafe_rows.append({"entrypoint": p, "blocked_reason": reason, "exists": "1" if Path(p).exists() else "0"})
    return safe_rows, unsafe_rows


def _validate_samples(
    samples: List[SampleItem],
    strict_scope: bool,
    allow_baseline: bool,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    details: List[Dict[str, str]] = []
    errors: List[Dict[str, str]] = []
    seen = set()
    for s in samples:
        abs_path = s.pdf_path if s.pdf_path.is_absolute() else Path(r"D:\_datefac\input") / s.pdf_path
        key = str(abs_path).lower()
        duplicate = key in seen
        seen.add(key)
        exists = abs_path.exists()
        is_pdf = abs_path.suffix.lower() == ".pdf"
        baseline_hit = abs_path.name == BASELINE_GUARD_PDF
        in_scope = str(abs_path).lower().startswith(str(Path(r"D:\_datefac\input")).lower())
        details.append(
            {
                "pdf_path": str(abs_path),
                "exists": "1" if exists else "0",
                "is_pdf": "1" if is_pdf else "0",
                "duplicate": "1" if duplicate else "0",
                "strict_scope_pass": "1" if (not strict_scope or in_scope) else "0",
                "baseline_guard_hit": "1" if baseline_hit else "0",
                "approved_pages": s.approved_pages,
                "ignored_pages": s.ignored_pages,
                "source": s.source,
            }
        )
        if not exists:
            errors.append({"error_code": "MISSING_PDF", "detail": str(abs_path)})
        if not is_pdf:
            errors.append({"error_code": "NOT_PDF", "detail": str(abs_path)})
        if duplicate:
            errors.append({"error_code": "DUPLICATE_PDF", "detail": str(abs_path)})
        if strict_scope and not in_scope:
            errors.append({"error_code": "STRICT_SCOPE_VIOLATION", "detail": str(abs_path)})
        if baseline_hit and not allow_baseline:
            errors.append({"error_code": "BASELINE_NOT_ALLOWED", "detail": str(abs_path)})
    return details, errors


def _build_dry_run_plan(samples: List[SampleItem], output_root: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for s in samples:
        pdf_abs = s.pdf_path if s.pdf_path.is_absolute() else Path(r"D:\_datefac\input") / s.pdf_path
        asset_name = f"{pdf_abs.stem}_资产包"
        pkg = output_root / asset_name
        rows.append(
            {
                "pdf": str(pdf_abs),
                "asset_package_dir": str(pkg),
                "planned_outputs": "02A/02/05 + downstream delivery refresh (execute mode only)",
                "safe_mode": "dry_run_only_no_write_to_production_delivery",
            }
        )
    return rows


def _write_23_reports(
    delivery_dir: Path,
    summary_rows: List[Dict[str, str]],
    source_rows: List[Dict[str, str]],
    sample_rows: List[Dict[str, str]],
    plan_rows: List[Dict[str, str]],
    safe_rows: List[Dict[str, str]],
    unsafe_rows: List[Dict[str, str]],
    error_rows: List[Dict[str, str]],
) -> Tuple[Path, Path]:
    md_lines = [
        "# Stage1 Safe Runner Dry Run",
        "",
        "## Summary",
    ]
    for row in summary_rows:
        md_lines.append(f"- {row['key']}: {row['value']}")
    md_lines.append("")
    md_lines.append("## Sample Validation")
    for row in sample_rows:
        md_lines.append(
            f"- {row['pdf_path']} | exists={row['exists']} | strict_scope_pass={row['strict_scope_pass']} | baseline_guard_hit={row['baseline_guard_hit']}"
        )
    md_lines.append("")
    md_lines.append("## Safe Entrypoints")
    for row in safe_rows:
        md_lines.append(f"- {row['entrypoint']} | exists={row['exists']}")
    md_lines.append("")
    md_lines.append("## Unsafe Entrypoints")
    for row in unsafe_rows:
        md_lines.append(f"- {row['entrypoint']} | reason={row['blocked_reason']}")
    if error_rows:
        md_lines.append("")
        md_lines.append("## Blocking Errors")
        for row in error_rows:
            md_lines.append(f"- {row['error_code']}: {row['detail']}")

    md_path = _safe_write_text(delivery_dir / "23_stage1_safe_runner_dry_run.md", "\n".join(md_lines))
    xlsx_path = _safe_write_excel(
        {
            "summary": pd.DataFrame(summary_rows),
            "inputs": pd.DataFrame(source_rows),
            "sample_validation": pd.DataFrame(sample_rows),
            "dry_run_plan": pd.DataFrame(plan_rows),
            "safe_entrypoints": pd.DataFrame(safe_rows),
            "unsafe_entrypoints": pd.DataFrame(unsafe_rows),
            "errors": pd.DataFrame(error_rows),
        },
        delivery_dir / "23_stage1_safe_runner_dry_run.xlsx",
    )
    return md_path, xlsx_path


def _write_24_reports(
    delivery_dir: Path,
    runner_path: Path,
    dry_run_status: str,
    dry_run_cmd: str,
    sample_rows: List[Dict[str, str]],
    safe_rows: List[Dict[str, str]],
    unsafe_rows: List[Dict[str, str]],
    delivery_status: Dict[str, str],
    next_step: str,
) -> Tuple[Path, Path]:
    summary = [
        {"field": "implemented_runner_path", "value": str(runner_path)},
        {"field": "dry_run_status", "value": dry_run_status},
        {"field": "why_execute_not_run", "value": "task constraint: dry-run only"},
        {"field": "current_delivery_status", "value": json.dumps(delivery_status, ensure_ascii=False)},
        {"field": "next_recommended_task", "value": next_step},
    ]
    md_lines = [
        "# Stage1 Safe Runner Implementation Report",
        "",
        f"- implemented_runner_path: {runner_path}",
        f"- dry_run_status: {dry_run_status}",
        f"- dry_run_commands: {dry_run_cmd}",
        "- why execute was not run: task constraint dry-run only",
        f"- current_delivery_status: {json.dumps(delivery_status, ensure_ascii=False)}",
        f"- next recommended task: {next_step}",
    ]
    md_path = _safe_write_text(delivery_dir / "24_stage1_safe_runner_implementation_report.md", "\n".join(md_lines))
    xlsx_path = _safe_write_excel(
        {
            "summary": pd.DataFrame(summary),
            "runner_interface": pd.DataFrame(
                [
                    {"arg": "--manifest", "required": "either with --pdf", "note": "manifest json path"},
                    {"arg": "--pdf", "required": "either with --manifest", "note": "repeatable"},
                    {"arg": "--dry-run", "required": "yes in this task", "note": "no execution"},
                    {"arg": "--execute", "required": "not used in this task", "note": "blocked scaffold"},
                    {"arg": "--strict-scope", "required": "recommended", "note": "scope guard"},
                    {"arg": "--no-vision", "required": "default true", "note": "safety guard"},
                ]
            ),
            "safe_entrypoints": pd.DataFrame(safe_rows),
            "unsafe_entrypoints": pd.DataFrame(unsafe_rows),
            "dry_run_plan": pd.DataFrame(sample_rows),
            "dry_run_results": pd.DataFrame([{"dry_run_status": dry_run_status, "generated_report_23": "yes"}]),
            "delivery_status": pd.DataFrame([delivery_status]),
            "next_steps": pd.DataFrame([{"next_step": next_step}]),
        },
        delivery_dir / "24_stage1_safe_runner_implementation_report.xlsx",
    )
    return md_path, xlsx_path


def _run_delivery_check(delivery_dir: Path) -> Dict[str, str]:
    script = Path(r"D:\_datefac\tools\check_delivery_state.py")
    if not script.exists():
        return {"overall_status": "UNKNOWN", "pass_count": "0", "warn_count": "0", "fail_count": "0"}
    import subprocess

    cmd = [sys.executable, str(script), "--delivery-dir", str(delivery_dir), "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
        return {
            "overall_status": _norm(payload.get("overall_status")),
            "pass_count": _norm(payload.get("pass_count")),
            "warn_count": _norm(payload.get("warn_count")),
            "fail_count": _norm(payload.get("fail_count")),
        }
    except Exception:
        return {"overall_status": "UNKNOWN", "pass_count": "0", "warn_count": "0", "fail_count": "0"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scoped safe non-vision Stage 1 runner (dry-run by default).")
    parser.add_argument("--manifest", type=str, default="")
    parser.add_argument("--pdf", action="append", default=[])
    parser.add_argument("--output-root", type=str, default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--delivery-dir", type=str, default=str(DEFAULT_DELIVERY_DIR))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--strict-scope", action="store_true")
    parser.add_argument("--no-vision", action="store_true", default=True)
    parser.add_argument("--skip-apply", action="store_true")
    parser.add_argument("--stop-on-first-error", action="store_true", default=True)
    parser.add_argument("--allow-baseline", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.dry_run and args.execute:
        print("BLOCKED_INVALID_ARGS: --dry-run and --execute cannot be both set.")
        return 2
    if not args.dry_run and not args.execute:
        print("BLOCKED_INVALID_ARGS: one of --dry-run or --execute is required.")
        return 2
    if not args.no_vision:
        print("BLOCKED_UNSAFE_ARGS: --no-vision must stay enabled.")
        return 2

    output_root = Path(args.output_root)
    delivery_dir = Path(args.delivery_dir)
    manifest = Path(args.manifest) if _norm(args.manifest) else None
    runner_path = Path(__file__).resolve()

    try:
        samples, source_rows = _load_samples(manifest, args.pdf)
    except Exception as exc:
        print(f"BLOCKED_INVALID_INPUT: {exc}")
        return 2

    sample_rows, sample_errors = _validate_samples(samples, strict_scope=args.strict_scope, allow_baseline=args.allow_baseline)
    safe_rows, unsafe_rows = _discover_safe_entrypoints()
    safe_exists = [r for r in safe_rows if r["exists"] == "1"]

    plan_rows = _build_dry_run_plan(samples, output_root)
    production_guard_rows = []
    for name in PRODUCTION_GUARD_FILES:
        production_guard_rows.append({"file": str(delivery_dir / name), "will_modify_in_dry_run": "0"})

    # This runner is intentionally dry-run-first; execute path is scaffolded and blocked for now.
    safe_full_pipeline_ready = False
    status = "DRY_RUN_BLOCKED_NO_SAFE_FULL_PIPELINE"
    if sample_errors:
        status = "DRY_RUN_BLOCKED_INPUT_VALIDATION_FAILED"

    summary_rows = [
        {"key": "runner_path", "value": str(runner_path)},
        {"key": "mode", "value": "dry_run" if args.dry_run else "execute"},
        {"key": "sample_count", "value": str(len(samples))},
        {"key": "strict_scope", "value": str(bool(args.strict_scope))},
        {"key": "no_vision", "value": str(bool(args.no_vision))},
        {"key": "safe_entrypoints_found", "value": str(len(safe_exists))},
        {"key": "unsafe_entrypoints_listed", "value": str(len(unsafe_rows))},
        {"key": "plan_executable_in_principle", "value": "1" if safe_full_pipeline_ready else "0"},
        {"key": "dry_run_status", "value": status},
    ]

    md23, xlsx23 = _write_23_reports(
        delivery_dir=delivery_dir,
        summary_rows=summary_rows,
        source_rows=source_rows,
        sample_rows=sample_rows,
        plan_rows=plan_rows + production_guard_rows,
        safe_rows=safe_rows,
        unsafe_rows=unsafe_rows,
        error_rows=sample_errors if sample_errors else [{"error_code": "BLOCKED_NO_SAFE_FULL_PIPELINE", "detail": "execute wiring intentionally blocked in this task"}],
    )

    delivery_status = _run_delivery_check(delivery_dir)
    dry_cmd = (
        f'{sys.executable} {runner_path} --manifest <manifest.json> --output-root "{output_root}" '
        f'--delivery-dir "{delivery_dir}" --dry-run --strict-scope'
    )
    next_step = (
        "Implement safe execute wiring for non-vision extraction + 02/05 generation, then run scoped execute with backups."
    )
    md24, xlsx24 = _write_24_reports(
        delivery_dir=delivery_dir,
        runner_path=runner_path,
        dry_run_status=status,
        dry_run_cmd=dry_cmd,
        sample_rows=sample_rows,
        safe_rows=safe_rows,
        unsafe_rows=unsafe_rows,
        delivery_status=delivery_status,
        next_step=next_step,
    )

    print(f"runner_path: {runner_path}")
    print(f"dry_run_status: {status}")
    print(f"report_23_md: {md23}")
    print(f"report_23_xlsx: {xlsx23}")
    print(f"report_24_md: {md24}")
    print(f"report_24_xlsx: {xlsx24}")
    print(f"delivery_overall_status: {delivery_status.get('overall_status', '')}")
    print(f"delivery_pass_count: {delivery_status.get('pass_count', '')}")
    print(f"delivery_warn_count: {delivery_status.get('warn_count', '')}")
    print(f"delivery_fail_count: {delivery_status.get('fail_count', '')}")

    if args.execute:
        print("BLOCKED_NOT_IMPLEMENTED: execute mode intentionally blocked in this task.")
        return 3
    return 0 if safe_full_pipeline_ready and not sample_errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
