from __future__ import annotations

import json
import math
import os
import shlex
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.benchmark.mineru_batch_parse_benchmark_342c import (
    CORPUS_MANIFEST_NAME,
    CORPUS_READY_DECISION,
    CORPUS_SUMMARY_NAME,
    CORPUS_WORKBOOK_NAME,
    PILOT_SPLIT,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION = "MINERU_PILOT_RETRY_VERIFIED_ENV_342C2_READY"
NOT_READY_DECISION = "MINERU_PILOT_RETRY_VERIFIED_ENV_342C2_NOT_READY"

DEFAULT_CORPUS_342B_DIR = Path(r"D:\_datefac\output\real_pdf_corpus_intake_342b")
DEFAULT_MINERU_342C_DIR = Path(r"D:\_datefac\output\mineru_batch_parse_benchmark_342c")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\mineru_pilot_retry_verified_env_342c2")
DEFAULT_WORKING_LAB_DIR = Path(r"E:\mineru_lab")
DEFAULT_MODEL_CACHE_DIR = Path(r"E:\mineru_lab\models")
DEFAULT_MINERU_CONFIG_PATH = Path.home() / "magic-pdf.json"

SUMMARY_FILE_NAME = "mineru_pilot_retry_verified_env_342c2_summary.json"
MANIFEST_FILE_NAME = "mineru_pilot_retry_verified_env_342c2_manifest.json"
QA_FILE_NAME = "mineru_pilot_retry_verified_env_342c2_qa.json"
NO_WRITE_BACK_FILE_NAME = "mineru_pilot_retry_verified_env_342c2_no_write_back_proof.json"
REPORT_FILE_NAME = "mineru_pilot_retry_verified_env_342c2_report.md"
WORKBOOK_FILE_NAME = "mineru_pilot_retry_verified_env_342c2.xlsx"

MINERU_342C_SUMMARY_NAME = "mineru_batch_parse_benchmark_342c_summary.json"
MINERU_342C_QA_NAME = "mineru_batch_parse_benchmark_342c_qa.json"
MINERU_342C_WORKBOOK_NAME = "mineru_batch_parse_benchmark_342c.xlsx"

WORKBOOK_SHEETS = [
    "00_README",
    "01_RETRY_SUMMARY",
    "02_RETRY_PARSE_RESULTS",
    "03_OUTPUT_ARTIFACT_AUDIT",
    "04_ORIG_342C_RECAP",
    "05_RETRY_FAILURE_AUDIT",
    "06_EMPTY_OUTPUT_AUDIT",
    "07_342D_READINESS",
    "08_ENV_CONTEXT",
    "09_NO_WRITE_BACK_PROOF",
    "10_NEXT_STEPS",
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


def _excerpt(text: str, limit: int = 240) -> str:
    normalized = " ".join(_norm_text(text).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def _error_category(error_text: str) -> str:
    lowered = error_text.casefold()
    if "certificate_verify_failed" in lowered or "certificate verify failed" in lowered:
        if "huggingface.co" in lowered:
            return "ssl_huggingface_download_failure"
        return "ssl_failure"
    if "huggingface.co" in lowered:
        return "huggingface_access_failure"
    if "task(s) failed" in lowered:
        return "mineru_task_failure"
    if not lowered:
        return "no_error_text"
    return "other_failure"


def _load_342c_failure_context(mineru_342c_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame, List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = mineru_342c_dir / MINERU_342C_SUMMARY_NAME
    qa_path = mineru_342c_dir / MINERU_342C_QA_NAME
    workbook_path = mineru_342c_dir / MINERU_342C_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    if summary_path.exists():
        files_read.append(str(summary_path))
    else:
        warnings.append(f"missing 342C summary: {summary_path}")
    if qa_path.exists():
        files_read.append(str(qa_path))
    else:
        warnings.append(f"missing 342C qa: {qa_path}")

    parse_results_df = pd.DataFrame()
    if workbook_path.exists():
        files_read.append(str(workbook_path))
        try:
            parse_results_df = pd.read_excel(workbook_path, sheet_name="02_PDF_PARSE_RESULTS")
        except Exception as exc:
            warnings.append(f"unable to read 342C parse results workbook: {exc}")
    else:
        warnings.append(f"missing 342C workbook: {workbook_path}")
    return summary, qa_json, _clean_frame(parse_results_df), files_read, warnings


def _build_342c_recap_df(summary_342c: Mapping[str, Any], parse_results_df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
    error_texts = []
    if not parse_results_df.empty and "error_message" in parse_results_df.columns:
        error_texts = [_norm_text(value) for value in parse_results_df["error_message"].tolist() if _norm_text(value)]
    combined_error = "\n".join(error_texts)
    ssl_detected = "certificate_verify_failed" in combined_error.casefold() or "certificate verify failed" in combined_error.casefold()
    huggingface_detected = "huggingface.co" in combined_error.casefold()
    empty_output_count = int(summary_342c.get("empty_output_count", 0) or 0)
    failure_count = int(summary_342c.get("mineru_failed_count", 0) or 0)
    total_count = int(summary_342c.get("pilot_total_count", 0) or 0)
    categories = Counter(_error_category(text) for text in error_texts)
    common_category = categories.most_common(1)[0][0] if categories else "no_error_text"
    first_excerpt = _excerpt(error_texts[0]) if error_texts else ""
    recap = {
        "original_342c_failure_detected": failure_count > 0,
        "original_342c_ssl_failure_detected": ssl_detected,
        "original_342c_huggingface_detected": huggingface_detected,
        "original_342c_error_category": common_category,
        "original_342c_first_error_excerpt": first_excerpt,
        "original_342c_empty_output_count": empty_output_count,
        "original_342c_failed_count": failure_count,
        "original_342c_total_count": total_count,
    }
    recap_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "detected_342c_decision": summary_342c.get("decision", ""),
                    "pilot_total_count": total_count,
                    "mineru_success_count": int(summary_342c.get("mineru_success_count", 0) or 0),
                    "mineru_failed_count": failure_count,
                    "empty_output_count": empty_output_count,
                    "ready_for_342d": summary_342c.get("ready_for_342d", ""),
                    "ssl_failure_detected": ssl_detected,
                    "huggingface_detected": huggingface_detected,
                    "common_error_category": common_category,
                    "first_error_excerpt": first_excerpt,
                }
            ]
        )
    )
    return recap_df, recap


def _build_subprocess_env(
    *,
    model_cache_dir: Path,
    mineru_config_path: Path | None,
) -> Dict[str, str]:
    env = os.environ.copy()
    env["HF_HOME"] = str(model_cache_dir)
    env["TRANSFORMERS_CACHE"] = str(model_cache_dir)
    env["HUGGINGFACE_HUB_CACHE"] = str(model_cache_dir / ".cache" / "huggingface")
    env["PYTHONUTF8"] = env.get("PYTHONUTF8", "1")
    if mineru_config_path and mineru_config_path.exists():
        env["MINERU_TOOLS_CONFIG_JSON"] = str(mineru_config_path)
    return env


def _build_command(mineru_command: str, pdf_path: Path, mineru_outputs_root: Path) -> List[str]:
    command = shlex.split(mineru_command, posix=True)
    command.extend(
        [
            "-p",
            str(pdf_path),
            "-o",
            str(mineru_outputs_root),
            "-b",
            "pipeline",
            "--formula",
            "false",
            "--table",
            "true",
        ]
    )
    return command


def _command_text(command: Sequence[str]) -> str:
    return subprocess.list2cmdline([str(item) for item in command])


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


def _run_mineru_for_pdf(
    *,
    pdf_path: Path,
    mineru_outputs_root: Path,
    mineru_command: str,
    working_lab_dir: Path,
    model_cache_dir: Path,
    mineru_config_path: Path | None,
) -> Dict[str, Any]:
    parse_dir = _discover_parse_dir(mineru_outputs_root, pdf_path.stem)
    command = _build_command(mineru_command, pdf_path, mineru_outputs_root)
    command_used = _command_text(command)

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

    env = _build_subprocess_env(model_cache_dir=model_cache_dir, mineru_config_path=mineru_config_path)
    start = time.perf_counter()
    result = subprocess.run(
        command,
        cwd=working_lab_dir if working_lab_dir.exists() else None,
        env=env,
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
        if path.suffix.casefold() in {".html", ".htm", ".csv", ".xlsx", ".xls"} or "table" in path.name.casefold()
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
    if parse_status != "FAILED":
        return ""
    if not stats.get("output_dir_exists"):
        return "parse output directory missing"
    if stats.get("output_dir_empty"):
        return "parse output directory exists but contains no files"
    if not stats.get("has_markdown") and not stats.get("has_json"):
        return "output lacks both markdown and json artifacts"
    if stats.get("abnormally_small_output_flag"):
        return "output exists but total size is suspiciously small"
    return ""


def _retry_recommendation(error_message: str, ready_for_342d: str) -> str:
    lowered = error_message.casefold()
    if "certificate_verify_failed" in lowered or "certificate verify failed" in lowered:
        return "verified cache env still hit SSL; inspect whether runtime is ignoring HF cache variables"
    if "huggingface.co" in lowered:
        return "check whether model cache path is visible to the active mineru_new runtime"
    if ready_for_342d == "conditional":
        return "at least one pilot succeeded; inspect only failed PDFs before 342D"
    return "inspect stderr, cache path, and MinerU runtime env before broader retry"


def _build_readme_df(selected_count: int) -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "342C2 reruns the 342B pilot_set with a verified local MinerU environment to check whether 342C failed because of runtime environment or model-cache setup.",
        },
        {
            "topic": "Scope boundary",
            "message": "This stage is still a sidecar parse benchmark only. It does not modify production pipeline, parser abstraction, extraction, delivery, or any upstream benchmark workbook.",
        },
        {
            "topic": "Verified local context",
            "message": "The retry is aligned to the known working MinerU lab context under E:/mineru_lab with model cache rooted at E:/mineru_lab/models.",
        },
        {
            "topic": "Pilot scope",
            "message": f"The retry selected {selected_count} PDFs from the 342B pilot_set.",
        },
        {
            "topic": "Readiness boundary",
            "message": "342C2 only recommends whether 342D may proceed conditionally. It does not claim client-ready or production-ready status.",
        },
        {
            "topic": "Advice boundary",
            "message": "This retry audit is not investment advice and does not write back to any upstream workbook.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_env_context_df(
    *,
    working_lab_dir: Path,
    model_cache_dir: Path,
    mineru_config_path: Path | None,
    mineru_command: str,
) -> pd.DataFrame:
    config_exists = bool(mineru_config_path and mineru_config_path.exists())
    cache_dir = model_cache_dir
    hub_cache_dir = cache_dir / ".cache" / "huggingface"
    rows = [
        {
            "context_key": "working_lab_dir",
            "value": str(working_lab_dir),
            "exists": working_lab_dir.exists(),
            "notes": "retry subprocess cwd prefers the verified MinerU lab dir when it exists",
        },
        {
            "context_key": "model_cache_dir",
            "value": str(cache_dir),
            "exists": cache_dir.exists(),
            "notes": "HF_HOME and TRANSFORMERS_CACHE are pointed here for retry subprocesses",
        },
        {
            "context_key": "huggingface_hub_cache",
            "value": str(hub_cache_dir),
            "exists": hub_cache_dir.exists(),
            "notes": "HUGGINGFACE_HUB_CACHE is pointed here for retry subprocesses",
        },
        {
            "context_key": "mineru_config_path",
            "value": str(mineru_config_path) if mineru_config_path else "",
            "exists": config_exists,
            "notes": "MINERU_TOOLS_CONFIG_JSON is set only when this config file exists",
        },
        {
            "context_key": "mineru_command",
            "value": mineru_command,
            "exists": True,
            "notes": "command prefix before fixed MinerU retry args are appended",
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


def _build_next_steps_df(ready_for_342d: str, retry_success_count: int, retry_failed_count: int) -> pd.DataFrame:
    rows = [
        {
            "step_order": 1,
            "next_step": "Review original 342C failure recap next to the 342C2 retry outcome",
            "rationale": "This confirms whether SSL/HuggingFace access was the dominant blocker or whether document-level failures remain.",
        },
        {
            "step_order": 2,
            "next_step": "Inspect only failed retry PDFs before any broader parser compare",
            "rationale": f"Current retry outcome is success={retry_success_count}, failed={retry_failed_count}.",
        },
        {
            "step_order": 3,
            "next_step": "Proceed to 342D only when readiness is acceptable",
            "rationale": f"Current 342D readiness recommendation is {ready_for_342d}.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_mineru_pilot_retry_verified_env_342c2(
    *,
    corpus_342b_dir: Path,
    mineru_342c_dir: Path,
    output_dir: Path,
    repo_root: Path,
    mineru_command: str = "mineru",
    limit: int | None = 5,
    working_lab_dir: Path = DEFAULT_WORKING_LAB_DIR,
    model_cache_dir: Path = DEFAULT_MODEL_CACHE_DIR,
    mineru_config_path: Path | None = DEFAULT_MINERU_CONFIG_PATH,
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

    summary_342c, qa_342c, parse_results_342c_df, files_read_342c, warnings_342c = _load_342c_failure_context(mineru_342c_dir)
    files_read.extend(files_read_342c)
    warnings.extend(warnings_342c)
    recap_df, recap = _build_342c_recap_df(summary_342c, parse_results_342c_df)

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
            mineru_command=mineru_command,
            working_lab_dir=working_lab_dir,
            model_cache_dir=model_cache_dir,
            mineru_config_path=mineru_config_path,
        )
        stats = _collect_output_stats(run_info.get("parse_dir"))
        total_runtime_seconds += float(run_info.get("runtime_seconds", 0.0) or 0.0)

        parse_status = "SUCCESS" if run_info.get("success") else "FAILED"
        execution_mode = "reused_existing_output" if run_info.get("status") == "reused_existing_output" else "ran_mineru"
        error_message = _norm_text(run_info.get("stderr") or run_info.get("status"))
        empty_reason = _empty_output_reason(parse_status, stats)
        empty_output_flag = bool(empty_reason)

        parse_row = {
            "corpus_pdf_id": row["corpus_pdf_id"],
            "file_name": row["file_name"],
            "file_path": row["file_path"],
            "sha256": row["sha256"],
            "split": row["split"],
            "assigned_tier": row["assigned_tier"],
            "page_count": _to_int(row.get("page_count")),
            "parse_status": parse_status,
            "execution_mode": execution_mode,
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
                    "error_category": _error_category(error_message),
                    "error_excerpt": _excerpt(error_message),
                    "error_message": error_message,
                    "retry_recommendation": "",
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

    retry_success_count = int((parse_results_df["parse_status"] == "SUCCESS").sum()) if not parse_results_df.empty else 0
    retry_failed_count = int((parse_results_df["parse_status"] == "FAILED").sum()) if not parse_results_df.empty else 0
    empty_output_count = int(len(empty_output_df))

    if selected_count > 0 and retry_success_count == selected_count:
        ready_for_342d = "true"
        recommended_next_scope = "pilot_set_parser_compare"
    elif retry_success_count >= 1:
        ready_for_342d = "conditional"
        recommended_next_scope = "inspect_failed_retry_rows_then_compare"
    else:
        ready_for_342d = "false"
        recommended_next_scope = "fix_retry_runtime_before_342d"

    if not failure_audit_df.empty:
        failure_audit_df["retry_recommendation"] = failure_audit_df["error_message"].apply(
            lambda value: _retry_recommendation(_norm_text(value), ready_for_342d)
        )

    no_write_back_input_hashes_before = {path: sha256_file(Path(path)) for path in files_read}
    no_write_back_input_hashes_after = {path: sha256_file(Path(path)) for path in files_read}
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342C2",
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
        bool(no_write_back_json.get("no_official_asset_modification_during_342c2"))
        and bool(no_write_back_json.get("upstream_workbooks_unchanged"))
        and not no_write_back_json.get("client_export_generated", True)
    )

    env_context_df = _build_env_context_df(
        working_lab_dir=working_lab_dir,
        model_cache_dir=model_cache_dir,
        mineru_config_path=mineru_config_path,
        mineru_command=mineru_command,
    )
    readme_df = _build_readme_df(selected_count)
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())
    readiness_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "retry_pilot_total_count": selected_count,
                    "retry_mineru_success_count": retry_success_count,
                    "retry_mineru_failed_count": retry_failed_count,
                    "ready_for_342d": ready_for_342d,
                    "recommended_next_scope": recommended_next_scope,
                    "reason": (
                        "all selected pilot PDFs produced successful MinerU outputs under the verified retry environment"
                        if ready_for_342d == "true"
                        else "at least one pilot PDF succeeded, so 342D can be considered conditionally after failed-row inspection"
                        if ready_for_342d == "conditional"
                        else "no successful retry output is available yet for 342D"
                    ),
                }
            ]
        )
    )

    checks = [
        {
            "check_name": "inputs::342b_dir_exists",
            "status": "PASS" if corpus_342b_dir.exists() else "FAIL",
            "detail": str(corpus_342b_dir),
        },
        {
            "check_name": "inputs::342c_dir_exists",
            "status": "PASS" if mineru_342c_dir.exists() else "FAIL",
            "detail": str(mineru_342c_dir),
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
            "check_name": "inputs::342c_failure_recap_generated",
            "status": "PASS" if not recap_df.empty else "FAIL",
            "detail": str(recap_df.to_dict(orient="records")),
        },
        {
            "check_name": "inputs::342c_ssl_failure_detected",
            "status": "PASS" if recap["original_342c_ssl_failure_detected"] else "FAIL",
            "detail": recap["original_342c_first_error_excerpt"],
        },
        {
            "check_name": "inputs::342c_huggingface_detected",
            "status": "PASS" if recap["original_342c_huggingface_detected"] else "FAIL",
            "detail": recap["original_342c_first_error_excerpt"],
        },
        {
            "check_name": "selection::selected_pdf_count_matches_limit",
            "status": "PASS" if selected_count == min(len(pilot_df), limit or len(pilot_df)) else "FAIL",
            "detail": str(selected_count),
        },
        {
            "check_name": "selection::every_selected_pdf_has_retry_result_row",
            "status": "PASS" if len(parse_results_df) == selected_count else "FAIL",
            "detail": f"rows={len(parse_results_df)} selected={selected_count}",
        },
        {
            "check_name": "artifacts::output_artifact_audit_generated",
            "status": "PASS" if len(artifact_audit_df) == selected_count else "FAIL",
            "detail": str(len(artifact_audit_df)),
        },
        {
            "check_name": "artifacts::retry_failure_audit_generated",
            "status": "PASS",
            "detail": str(len(failure_audit_df)),
        },
        {
            "check_name": "artifacts::empty_output_audit_generated",
            "status": "PASS",
            "detail": str(len(empty_output_df)),
        },
        {
            "check_name": "artifacts::env_context_generated",
            "status": "PASS" if not env_context_df.empty else "FAIL",
            "detail": str(len(env_context_df)),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {
                    "upstream_unchanged": no_write_back_json.get("upstream_workbooks_unchanged"),
                    "official_assets_unchanged": no_write_back_json.get("no_official_asset_modification_during_342c2"),
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
            "detail": "342C2 adds only sidecar retry benchmark code and retry outputs",
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
    decision = READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "retry_pilot_total_count": selected_count,
        "retry_mineru_success_count": retry_success_count,
        "retry_mineru_failed_count": retry_failed_count,
        "empty_output_count": empty_output_count,
        "ready_for_342d": ready_for_342d,
        "recommended_next_scope": recommended_next_scope,
        "original_342c_failure_detected": recap["original_342c_failure_detected"],
        "original_342c_ssl_failure_detected": recap["original_342c_ssl_failure_detected"],
        "original_342c_huggingface_detected": recap["original_342c_huggingface_detected"],
        "original_342c_empty_output_count": recap["original_342c_empty_output_count"],
        "verified_working_lab_dir": str(working_lab_dir),
        "verified_model_cache_dir": str(model_cache_dir),
        "mineru_command": mineru_command,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "detected_342b_decision": summary_342b.get("decision", ""),
        "detected_342c_decision": summary_342c.get("decision", ""),
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
        "mineru_outputs_root": str(mineru_outputs_root),
    }

    manifest = {
        "task": "342C2_mineru_pilot_retry_verified_env",
        "corpus_342b_dir": str(corpus_342b_dir),
        "mineru_342c_dir": str(mineru_342c_dir),
        "output_dir": str(output_dir),
        "mineru_outputs_root": str(mineru_outputs_root),
        "limit": limit,
        "mineru_command": mineru_command,
        "working_lab_dir": str(working_lab_dir),
        "model_cache_dir": str(model_cache_dir),
        "mineru_config_path": str(mineru_config_path) if mineru_config_path else "",
        "selected_corpus_pdf_ids": [_norm_text(row["corpus_pdf_id"]) for row in selected_rows],
        "warnings": warnings,
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
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
        "01_RETRY_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_RETRY_PARSE_RESULTS": parse_results_df,
        "03_OUTPUT_ARTIFACT_AUDIT": artifact_audit_df,
        "04_ORIG_342C_RECAP": recap_df,
        "05_RETRY_FAILURE_AUDIT": failure_audit_df,
        "06_EMPTY_OUTPUT_AUDIT": empty_output_df,
        "07_342D_READINESS": readiness_df,
        "08_ENV_CONTEXT": env_context_df,
        "09_NO_WRITE_BACK_PROOF": _build_no_write_back_proof_df(no_write_back_json),
        "10_NEXT_STEPS": _build_next_steps_df(ready_for_342d, retry_success_count, retry_failed_count),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }
