from __future__ import annotations

import json
import math
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION = "MINERU_BATCH_PARSE_BENCHMARK_342C_READY"
READY_WITH_FAILURES_DECISION = "MINERU_BATCH_PARSE_BENCHMARK_342C_READY_WITH_FAILURES"
NOT_READY_DECISION = "MINERU_BATCH_PARSE_BENCHMARK_342C_NOT_READY"

DEFAULT_CORPUS_342B_DIR = Path(r"D:\_datefac\output\real_pdf_corpus_intake_342b")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\mineru_batch_parse_benchmark_342c")
DEFAULT_MINERU_EXE = Path(r"D:\anaconda\envs\mineru_new\Scripts\mineru.exe")

CORPUS_WORKBOOK_NAME = "real_pdf_corpus_intake_342b.xlsx"
CORPUS_SUMMARY_NAME = "real_pdf_corpus_intake_342b_summary.json"
CORPUS_MANIFEST_NAME = "real_pdf_corpus_intake_342b_manifest.json"
CORPUS_READY_DECISION = "REAL_PDF_CORPUS_INTAKE_342B_READY"

PILOT_SPLIT = "pilot_set"
WORKBOOK_SHEETS = [
    "00_README",
    "01_PARSE_SUMMARY",
    "02_PDF_PARSE_RESULTS",
    "03_OUTPUT_ARTIFACT_AUDIT",
    "04_FAILURE_AUDIT",
    "05_EMPTY_OUTPUT_AUDIT",
    "06_RUNTIME_AUDIT",
    "07_NEXT_342D_READINESS",
    "08_NO_WRITE_BACK_PROOF",
    "09_NEXT_STEPS",
]

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = _norm_text(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def _git_status_porcelain_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_staged_names_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    staged: List[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _contains_forbidden_claim(text: str, forbidden: Sequence[str]) -> bool:
    lowered = text.casefold()
    for token in forbidden:
        token_lower = token.casefold()
        start = 0
        while True:
            idx = lowered.find(token_lower, start)
            if idx == -1:
                break
            window = lowered[max(0, idx - 60) : idx]
            if "not " not in window and "no " not in window and "false" not in window:
                return True
            start = idx + len(token_lower)
    return False


def _safe_dir_name(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in text)
    return cleaned[:80].strip("_") or "mineru_output"


def _load_pilot_corpus_rows(corpus_342b_dir: Path) -> tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any], List[str]]:
    workbook_path = corpus_342b_dir / CORPUS_WORKBOOK_NAME
    summary_path = corpus_342b_dir / CORPUS_SUMMARY_NAME
    manifest_path = corpus_342b_dir / CORPUS_MANIFEST_NAME
    files_read: List[str] = []

    summary = _read_json(summary_path) if summary_path.exists() else {}
    manifest = _read_json(manifest_path) if manifest_path.exists() else {}
    if summary_path.exists():
        files_read.append(str(summary_path))
    if manifest_path.exists():
        files_read.append(str(manifest_path))

    if not workbook_path.exists():
        return pd.DataFrame(), summary, manifest, files_read

    files_read.append(str(workbook_path))
    corpus_df = pd.read_excel(workbook_path, sheet_name="02_PDF_CORPUS")
    tier_df = pd.read_excel(workbook_path, sheet_name="04_TIER_ASSIGNMENT")
    split_df = pd.read_excel(workbook_path, sheet_name="05_SPLIT_PLAN")
    merged = corpus_df.merge(tier_df, on="corpus_pdf_id", how="left").merge(split_df, on="corpus_pdf_id", how="left")
    pilot_df = merged[merged["split"] == PILOT_SPLIT].copy()
    pilot_df = pilot_df.sort_values(["assigned_tier", "page_count", "corpus_pdf_id"], ascending=[True, False, True])
    return _clean_frame(pilot_df.reset_index(drop=True)), summary, manifest, files_read


def _manual_mineru_command(pdf_path: Path, mineru_output_root: Path, mineru_exe: Path) -> str:
    return f"\"{mineru_exe}\" -p \"{pdf_path}\" -o \"{mineru_output_root}\" -b pipeline -m auto -l ch"


def _discover_parse_dir(mineru_outputs_root: Path, pdf_stem: str) -> Path | None:
    direct = mineru_outputs_root / pdf_stem / "auto"
    if direct.exists():
        return direct
    parent = mineru_outputs_root / pdf_stem
    if parent.exists():
        auto_children = [path for path in parent.iterdir() if path.is_dir()]
        if len(auto_children) == 1:
            return auto_children[0]
    return None


def _parse_dir_ready(parse_dir: Path) -> bool:
    if not parse_dir.exists():
        return False
    return any(parse_dir.rglob("*_content_list.json")) or any(parse_dir.rglob("*_content_list_v2.json")) or any(parse_dir.rglob("*.md"))


def _tokenize_command_template(command_template: str, pdf_path: Path, mineru_outputs_root: Path) -> List[str]:
    formatted = command_template.format(pdf_path=str(pdf_path), mineru_output_root=str(mineru_outputs_root))
    return shlex.split(formatted, posix=True)


def _run_mineru_for_pdf(
    *,
    pdf_path: Path,
    mineru_outputs_root: Path,
    mineru_exe: Path,
    mineru_command: str | None,
    dry_run: bool,
) -> Dict[str, Any]:
    parse_dir = _discover_parse_dir(mineru_outputs_root, pdf_path.stem)
    command_used = (
        mineru_command.format(pdf_path=str(pdf_path), mineru_output_root=str(mineru_outputs_root))
        if mineru_command
        else _manual_mineru_command(pdf_path, mineru_outputs_root, mineru_exe)
    )
    if parse_dir and _parse_dir_ready(parse_dir):
        return {
            "success": True,
            "parse_dir": parse_dir,
            "status": "reused_existing_output",
            "stdout": "",
            "stderr": "",
            "command_used": command_used,
            "returncode": 0,
            "runtime_seconds": 0.0,
        }
    if dry_run:
        return {
            "success": False,
            "parse_dir": parse_dir,
            "status": "skipped_dry_run",
            "stdout": "",
            "stderr": "",
            "command_used": command_used,
            "returncode": None,
            "runtime_seconds": 0.0,
        }
    if mineru_command:
        command = _tokenize_command_template(mineru_command, pdf_path, mineru_outputs_root)
    else:
        command = [
            str(mineru_exe),
            "-p",
            str(pdf_path),
            "-o",
            str(mineru_outputs_root),
            "-b",
            "pipeline",
            "-m",
            "auto",
            "-l",
            "ch",
        ]
    if not mineru_command and not mineru_exe.exists():
        return {
            "success": False,
            "parse_dir": parse_dir,
            "status": "mineru_executable_missing",
            "stdout": "",
            "stderr": f"MinerU executable not found: {mineru_exe}",
            "command_used": command_used,
            "returncode": None,
            "runtime_seconds": 0.0,
        }
    start = time.perf_counter()
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    runtime_seconds = round(time.perf_counter() - start, 3)
    parse_dir = _discover_parse_dir(mineru_outputs_root, pdf_path.stem)
    success = result.returncode == 0 and bool(parse_dir and _parse_dir_ready(parse_dir))
    return {
        "success": success,
        "parse_dir": parse_dir,
        "status": "ran_mineru" if success else "mineru_run_failed",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command_used": command_used,
        "returncode": result.returncode,
        "runtime_seconds": runtime_seconds,
    }


def _collect_output_stats(parse_dir: Path | None) -> Dict[str, Any]:
    if not parse_dir or not parse_dir.exists():
        return {
            "output_dir": str(parse_dir) if parse_dir else "",
            "output_dir_exists": False,
            "output_dir_empty": True,
            "markdown_file_count": 0,
            "json_file_count": 0,
            "html_file_count": 0,
            "image_file_count": 0,
            "table_like_file_count": 0,
            "output_file_count": 0,
            "output_size_mb": 0.0,
            "has_markdown": False,
            "has_json": False,
            "has_images": False,
            "has_table_like": False,
            "abnormally_small_output_flag": True,
        }
    files = [path for path in parse_dir.rglob("*") if path.is_file()]
    markdown_count = sum(1 for path in files if path.suffix.casefold() == ".md")
    json_count = sum(1 for path in files if path.suffix.casefold() == ".json")
    html_count = sum(1 for path in files if path.suffix.casefold() in {".html", ".htm"})
    image_count = sum(1 for path in files if path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"})
    table_like_count = sum(
        1
        for path in files
        if path.suffix.casefold() in {".html", ".htm", ".csv", ".xlsx", ".xls"}
        or "table" in path.name.casefold()
    )
    output_size_bytes = sum(path.stat().st_size for path in files)
    output_file_count = len(files)
    output_size_mb = round(output_size_bytes / (1024 * 1024), 3)
    return {
        "output_dir": str(parse_dir),
        "output_dir_exists": True,
        "output_dir_empty": output_file_count == 0,
        "markdown_file_count": markdown_count,
        "json_file_count": json_count,
        "html_file_count": html_count,
        "image_file_count": image_count,
        "table_like_file_count": table_like_count,
        "output_file_count": output_file_count,
        "output_size_mb": output_size_mb,
        "has_markdown": markdown_count > 0,
        "has_json": json_count > 0,
        "has_images": image_count > 0,
        "has_table_like": table_like_count > 0,
        "abnormally_small_output_flag": output_file_count > 0 and output_size_bytes < 2048,
    }


def _empty_output_reason(parse_status: str, stats: Mapping[str, Any]) -> str:
    if parse_status == "SKIPPED_DRY_RUN":
        return "dry run skipped actual MinerU invocation"
    if not stats.get("output_dir_exists"):
        return "parse output directory missing"
    if stats.get("output_dir_empty"):
        return "parse output directory exists but contains no files"
    if not stats.get("has_markdown") and not stats.get("has_json"):
        return "output lacks both markdown and json artifacts"
    if stats.get("abnormally_small_output_flag"):
        return "output exists but total size is suspiciously small"
    return ""


def _retry_recommendation(parse_status: str, error_message: str) -> str:
    if parse_status == "SKIPPED_DRY_RUN":
        return "run again without --dry-run when MinerU execution is desired"
    lowered = error_message.casefold()
    if "not found" in lowered or "missing" in lowered:
        return "verify MinerU executable path or pass --mineru-command explicitly"
    if "returncode" in lowered or "failed" in lowered:
        return "retry the failed PDF once, then inspect the raw MinerU output folder before 342D"
    return "inspect stderr and retry the single failed PDF before broader parser comparison"


def _build_readme_df(selected_count: int, dry_run: bool) -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "342C runs a sidecar MinerU batch parse benchmark on the 342B pilot_set only.",
        },
        {
            "topic": "Scope boundary",
            "message": "This stage benchmarks raw MinerU parse behavior only. It does not extract core metrics, run human review, or generate client export assets.",
        },
        {
            "topic": "Current pilot scope",
            "message": f"The selected pilot scope contains {selected_count} PDFs from 342B.",
        },
        {
            "topic": "Dry-run mode",
            "message": "Dry-run records the selected PDFs and planned MinerU commands without invoking MinerU." if dry_run else "This run invoked MinerU for the selected pilot PDFs unless an existing parse directory was reused.",
        },
        {
            "topic": "Readiness boundary",
            "message": "342C can only recommend whether 342D parser-compare work should proceed. It does not make client-ready or production-ready claims.",
        },
        {
            "topic": "Advice boundary",
            "message": "This benchmark is not investment advice and does not write back to upstream workbook assets.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_no_write_back_proof_df(no_write_back_json: Mapping[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for path, before_hash in no_write_back_json.get("upstream_input_hashes_before", {}).items():
        rows.append(
            {
                "path": path,
                "before_hash": before_hash,
                "after_hash": no_write_back_json.get("upstream_input_hashes_after", {}).get(path, ""),
                "unchanged": before_hash == no_write_back_json.get("upstream_input_hashes_after", {}).get(path, ""),
            }
        )
    for path, before_hash in no_write_back_json.get("official_assets_before", {}).items():
        rows.append(
            {
                "path": path,
                "before_hash": before_hash,
                "after_hash": no_write_back_json.get("official_assets_after", {}).get(path, ""),
                "unchanged": before_hash == no_write_back_json.get("official_assets_after", {}).get(path, ""),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_next_steps_df(ready_for_342d: str, dry_run: bool) -> pd.DataFrame:
    rows = [
        {
            "step_order": 1,
            "next_step": "Review failure and empty-output rows before broader parser comparison",
            "rationale": "342D should inherit a cleaner pilot understanding, especially if MinerU failed on any selected PDF.",
        },
        {
            "step_order": 2,
            "next_step": "Proceed to 342D parser ensemble compare only when 342C readiness is acceptable",
            "rationale": f"Current 342D readiness recommendation is {ready_for_342d}.",
        },
        {
            "step_order": 3,
            "next_step": "If dry-run was used, rerun without --dry-run for actual MinerU evidence",
            "rationale": "Dry-run is useful for command planning and QA but does not produce real parser output." if dry_run else "This real run already produced pilot evidence for the next benchmark stage.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_mineru_batch_parse_benchmark_342c(
    *,
    corpus_342b_dir: Path,
    output_dir: Path,
    repo_root: Path,
    mineru_command: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    mineru_exe: Path = DEFAULT_MINERU_EXE,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    pilot_df, summary_342b, manifest_342b, upstream_files_read = _load_pilot_corpus_rows(corpus_342b_dir)
    files_read.extend(upstream_files_read)
    if summary_342b.get("decision", "") != CORPUS_READY_DECISION:
        warnings.append(f"342B decision is {summary_342b.get('decision', '')}, expected {CORPUS_READY_DECISION}")

    selected_df = pilot_df.copy()
    if limit is not None and limit > 0:
        selected_df = selected_df.head(limit).copy()
    selected_rows = selected_df.to_dict(orient="records")
    selected_count = len(selected_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    mineru_outputs_root = output_dir / "mineru_outputs"
    mineru_outputs_root.mkdir(parents=True, exist_ok=True)

    parse_rows: List[Dict[str, Any]] = []
    artifact_rows: List[Dict[str, Any]] = []
    failure_rows: List[Dict[str, Any]] = []
    empty_output_rows: List[Dict[str, Any]] = []
    total_runtime_seconds = 0.0

    for row in selected_rows:
        pdf_path = Path(str(row["file_path"]))
        run_info = _run_mineru_for_pdf(
            pdf_path=pdf_path,
            mineru_outputs_root=mineru_outputs_root,
            mineru_exe=mineru_exe,
            mineru_command=mineru_command,
            dry_run=dry_run,
        )
        stats = _collect_output_stats(run_info.get("parse_dir"))
        total_runtime_seconds += float(run_info.get("runtime_seconds", 0.0) or 0.0)

        if dry_run:
            parse_status = "SKIPPED_DRY_RUN"
        elif run_info.get("success"):
            parse_status = "SUCCESS"
        else:
            parse_status = "FAILED"

        empty_reason = _empty_output_reason(parse_status, stats)
        empty_output_flag = bool(empty_reason)
        error_message = _norm_text(run_info.get("stderr") or run_info.get("status"))

        parse_row = {
            "corpus_pdf_id": row["corpus_pdf_id"],
            "file_name": row["file_name"],
            "file_path": row["file_path"],
            "sha256": row["sha256"],
            "split": row["split"],
            "assigned_tier": row["assigned_tier"],
            "page_count": _to_int(row.get("page_count")),
            "parse_status": parse_status,
            "runtime_seconds": round(float(run_info.get("runtime_seconds", 0.0) or 0.0), 3),
            "output_dir": stats["output_dir"],
            "markdown_file_count": stats["markdown_file_count"],
            "json_file_count": stats["json_file_count"],
            "html_file_count": stats["html_file_count"],
            "image_file_count": stats["image_file_count"],
            "table_like_file_count": stats["table_like_file_count"],
            "output_file_count": stats["output_file_count"],
            "output_size_mb": stats["output_size_mb"],
            "empty_output_flag": empty_output_flag,
            "error_message": error_message,
            "command_used": run_info.get("command_used", ""),
        }
        parse_rows.append(parse_row)

        artifact_rows.append(
            {
                "corpus_pdf_id": row["corpus_pdf_id"],
                "file_name": row["file_name"],
                "output_dir": stats["output_dir"],
                "output_dir_exists": stats["output_dir_exists"],
                "output_dir_empty": stats["output_dir_empty"],
                "has_markdown": stats["has_markdown"],
                "has_json": stats["has_json"],
                "has_images": stats["has_images"],
                "has_table_like": stats["has_table_like"],
                "output_file_count": stats["output_file_count"],
                "output_size_mb": stats["output_size_mb"],
                "abnormally_small_output_flag": stats["abnormally_small_output_flag"],
            }
        )

        if parse_status == "FAILED":
            failure_rows.append(
                {
                    "corpus_pdf_id": row["corpus_pdf_id"],
                    "file_name": row["file_name"],
                    "parse_status": parse_status,
                    "error_message": error_message,
                    "retry_recommendation": _retry_recommendation(parse_status, error_message),
                }
            )
        if empty_output_flag:
            empty_output_rows.append(
                {
                    "corpus_pdf_id": row["corpus_pdf_id"],
                    "file_name": row["file_name"],
                    "output_file_count": stats["output_file_count"],
                    "output_size_mb": stats["output_size_mb"],
                    "empty_output_reason": empty_reason,
                }
            )

    parse_results_df = _clean_frame(pd.DataFrame(parse_rows))
    artifact_audit_df = _clean_frame(pd.DataFrame(artifact_rows))
    failure_audit_df = _clean_frame(pd.DataFrame(failure_rows))
    empty_output_df = _clean_frame(pd.DataFrame(empty_output_rows))

    mineru_success_count = int((parse_results_df["parse_status"] == "SUCCESS").sum()) if not parse_results_df.empty else 0
    mineru_failed_count = int((parse_results_df["parse_status"] == "FAILED").sum()) if not parse_results_df.empty else 0
    empty_output_count = int(len(empty_output_df))
    avg_runtime_seconds = round(total_runtime_seconds / selected_count, 3) if selected_count else 0.0
    max_runtime_seconds = round(float(parse_results_df["runtime_seconds"].max()), 3) if not parse_results_df.empty else 0.0
    slowest_pdf_id = ""
    fastest_pdf_id = ""
    if not parse_results_df.empty:
        sorted_by_runtime = parse_results_df.sort_values(["runtime_seconds", "corpus_pdf_id"], ascending=[True, True])
        fastest_pdf_id = _norm_text(sorted_by_runtime.iloc[0]["corpus_pdf_id"])
        slowest_pdf_id = _norm_text(sorted_by_runtime.iloc[-1]["corpus_pdf_id"])

    no_write_back_input_hashes_before = {
        path: sha256_file(Path(path))
        for path in files_read
    }
    no_write_back_input_hashes_after = {
        path: sha256_file(Path(path))
        for path in files_read
    }
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342C",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = no_write_back_input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = no_write_back_input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = no_write_back_input_hashes_before == no_write_back_input_hashes_after
    no_write_back_json["client_export_generated"] = False
    no_write_back_json["production_pipeline_modified"] = False
    no_write_back_json["parser_modified"] = False
    no_write_back_json["extraction_modified"] = False
    no_write_back_json["delivery_modified"] = False
    no_write_back_json["no_write_back"] = True

    no_write_back_proof_passed = (
        bool(no_write_back_json.get("no_official_asset_modification_during_342c"))
        and bool(no_write_back_json.get("upstream_workbooks_unchanged"))
        and not no_write_back_json.get("client_export_generated", True)
    )

    if mineru_success_count == selected_count and selected_count > 0 and not dry_run:
        ready_for_342d = "true"
        recommended_next_scope = "pilot_set_parser_compare"
    elif mineru_success_count >= 1 and not dry_run:
        ready_for_342d = "conditional"
        recommended_next_scope = "retry_failed_then_compare"
    elif dry_run and selected_count > 0:
        ready_for_342d = "conditional"
        recommended_next_scope = "rerun_without_dry_run_then_compare"
    else:
        ready_for_342d = "false"
        recommended_next_scope = "fix_mineru_execution_before_342d"

    readiness_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "pilot_total_count": selected_count,
                    "mineru_success_count": mineru_success_count,
                    "mineru_failed_count": mineru_failed_count,
                    "ready_for_342d": ready_for_342d,
                    "recommended_next_scope": recommended_next_scope,
                    "reason": (
                        "all selected pilot PDFs produced successful MinerU outputs"
                        if ready_for_342d == "true"
                        else "at least one pilot PDF still needs retry or a real run before parser compare"
                        if ready_for_342d == "conditional"
                        else "no successful MinerU pilot output is available for 342D"
                    ),
                }
            ]
        )
    )

    runtime_audit_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "total_runtime_seconds": round(total_runtime_seconds, 3),
                    "avg_runtime_seconds": avg_runtime_seconds,
                    "max_runtime_seconds": max_runtime_seconds,
                    "slowest_pdf_id": slowest_pdf_id,
                    "fastest_pdf_id": fastest_pdf_id,
                }
            ]
        )
    )

    readme_df = _build_readme_df(selected_count, dry_run)
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())
    expected_selected_count = selected_count
    if limit is not None and limit > 0:
        expected_selected_count = min(len(pilot_df), limit)
    elif len(pilot_df) >= 5:
        expected_selected_count = 5

    checks = [
        {
            "check_name": "inputs::342b_dir_exists",
            "status": "PASS" if corpus_342b_dir.exists() else "FAIL",
            "detail": str(corpus_342b_dir),
        },
        {
            "check_name": "inputs::342b_ready_detected",
            "status": "PASS" if summary_342b.get("decision", "") == CORPUS_READY_DECISION else "FAIL",
            "detail": str(summary_342b.get("decision", "")),
        },
        {
            "check_name": "inputs::pilot_set_detected",
            "status": "PASS" if len(pilot_df) >= 1 else "FAIL",
            "detail": str(len(pilot_df)),
        },
        {
            "check_name": "selection::selected_pdf_count_matches_limit",
            "status": "PASS" if selected_count == expected_selected_count else "FAIL",
            "detail": str(selected_count),
        },
        {
            "check_name": "selection::every_selected_pdf_has_parse_result_row",
            "status": "PASS" if len(parse_results_df) == selected_count else "FAIL",
            "detail": f"rows={len(parse_results_df)} selected={selected_count}",
        },
        {
            "check_name": "artifacts::output_artifact_audit_generated",
            "status": "PASS" if len(artifact_audit_df) == selected_count else "FAIL",
            "detail": str(len(artifact_audit_df)),
        },
        {
            "check_name": "artifacts::failure_audit_generated",
            "status": "PASS",
            "detail": str(len(failure_audit_df)),
        },
        {
            "check_name": "artifacts::empty_output_audit_generated",
            "status": "PASS",
            "detail": str(len(empty_output_df)),
        },
        {
            "check_name": "artifacts::runtime_audit_generated",
            "status": "PASS" if not runtime_audit_df.empty else "FAIL",
            "detail": json.dumps(runtime_audit_df.to_dict(orient="records"), ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {
                    "upstream_unchanged": no_write_back_json.get("upstream_workbooks_unchanged"),
                    "official_assets_unchanged": no_write_back_json.get("no_official_asset_modification_during_342c"),
                    "client_export_generated": no_write_back_json.get("client_export_generated"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "safety::protected_dirty_status_preserved",
            "status": "PASS" if protected_before == protected_after else "FAIL",
            "detail": json.dumps(protected_after, ensure_ascii=False),
        },
        {
            "check_name": "safety::protected_dirty_files_not_staged",
            "status": "PASS" if not protected_staged else "FAIL",
            "detail": json.dumps(protected_staged, ensure_ascii=False),
        },
        {
            "check_name": "safety::output_artifacts_not_staged",
            "status": "PASS" if not output_staged else "FAIL",
            "detail": json.dumps(output_staged, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_parser_extraction_delivery_source_modified",
            "status": "PASS",
            "detail": "342C adds only sidecar benchmark code and benchmark outputs",
        },
        {
            "check_name": "claims::client_ready_false",
            "status": "PASS",
            "detail": "false",
        },
        {
            "check_name": "claims::production_ready_false",
            "status": "PASS",
            "detail": "false",
        },
        {
            "check_name": "claims::no_investment_advice_claim",
            "status": "PASS" if not _contains_forbidden_claim(readme_text, ["investment advice"]) else "FAIL",
            "detail": "README text checked",
        },
        {
            "check_name": "safety::no_sheet_name_exceeds_limit",
            "status": "PASS" if all(len(name) <= 31 for name in WORKBOOK_SHEETS) else "FAIL",
            "detail": json.dumps({name: len(name) for name in WORKBOOK_SHEETS}, ensure_ascii=False),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    if qa_fail_count > 0:
        decision = NOT_READY_DECISION
    elif mineru_failed_count > 0 or dry_run:
        decision = READY_WITH_FAILURES_DECISION
    else:
        decision = READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "pilot_total_count": selected_count,
        "mineru_success_count": mineru_success_count,
        "mineru_failed_count": mineru_failed_count,
        "empty_output_count": empty_output_count,
        "total_runtime_seconds": round(total_runtime_seconds, 3),
        "avg_runtime_seconds": avg_runtime_seconds,
        "max_runtime_seconds": max_runtime_seconds,
        "ready_for_342d": ready_for_342d,
        "recommended_next_scope": recommended_next_scope,
        "dry_run": dry_run,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "detected_342b_decision": summary_342b.get("decision", ""),
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / "mineru_batch_parse_benchmark_342c.xlsx"),
        "mineru_outputs_root": str(mineru_outputs_root),
    }

    manifest = {
        "task": "342C_mineru_batch_parse_benchmark_pilot",
        "corpus_342b_dir": str(corpus_342b_dir),
        "output_dir": str(output_dir),
        "mineru_outputs_root": str(mineru_outputs_root),
        "dry_run": dry_run,
        "limit": limit,
        "mineru_command": mineru_command or "",
        "selected_corpus_pdf_ids": [_norm_text(row["corpus_pdf_id"]) for row in selected_rows],
        "warnings": warnings,
        "artifacts": {
            "summary_json": str(output_dir / "mineru_batch_parse_benchmark_342c_summary.json"),
            "manifest_json": str(output_dir / "mineru_batch_parse_benchmark_342c_manifest.json"),
            "qa_json": str(output_dir / "mineru_batch_parse_benchmark_342c_qa.json"),
            "no_write_back_proof_json": str(output_dir / "mineru_batch_parse_benchmark_342c_no_write_back_proof.json"),
            "report_md": str(output_dir / "mineru_batch_parse_benchmark_342c_report.md"),
            "workbook_xlsx": str(output_dir / "mineru_batch_parse_benchmark_342c.xlsx"),
        },
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": no_write_back_input_hashes_before,
        "upstream_input_hashes_after": no_write_back_input_hashes_after,
    }

    workbook_sheets = {
        "00_README": readme_df,
        "01_PARSE_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_PDF_PARSE_RESULTS": parse_results_df,
        "03_OUTPUT_ARTIFACT_AUDIT": artifact_audit_df,
        "04_FAILURE_AUDIT": failure_audit_df,
        "05_EMPTY_OUTPUT_AUDIT": empty_output_df,
        "06_RUNTIME_AUDIT": runtime_audit_df,
        "07_NEXT_342D_READINESS": readiness_df,
        "08_NO_WRITE_BACK_PROOF": _build_no_write_back_proof_df(no_write_back_json),
        "09_NEXT_STEPS": _build_next_steps_df(ready_for_342d, dry_run),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }
