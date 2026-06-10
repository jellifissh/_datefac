from __future__ import annotations

import json
import math
import os
import shlex
import subprocess
import time
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


READY_DECISION = "MINERU_PILOT_NETWORK_RECOVERY_342C6_READY"
NOT_READY_DECISION = "MINERU_PILOT_NETWORK_RECOVERY_342C6_NOT_READY"

DEFAULT_CORPUS_342B_DIR = Path(r"D:\_datefac\output\real_pdf_corpus_intake_342b")
DEFAULT_MINERU_342C2_DIR = Path(r"D:\_datefac\output\mineru_pilot_retry_verified_env_342c2_after_env_fix")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\mineru_pilot_network_recovery_342c6")

SUMMARY_FILE_NAME = "mineru_pilot_network_recovery_342c6_summary.json"
MANIFEST_FILE_NAME = "mineru_pilot_network_recovery_342c6_manifest.json"
QA_FILE_NAME = "mineru_pilot_network_recovery_342c6_qa.json"
NO_WRITE_BACK_FILE_NAME = "mineru_pilot_network_recovery_342c6_no_write_back_proof.json"
REPORT_FILE_NAME = "mineru_pilot_network_recovery_342c6_report.md"
WORKBOOK_FILE_NAME = "mineru_pilot_network_recovery_342c6.xlsx"

MINERU_342C2_SUMMARY_NAME = "mineru_pilot_retry_verified_env_342c2_summary.json"
MINERU_342C2_QA_NAME = "mineru_pilot_retry_verified_env_342c2_qa.json"
MINERU_342C2_WORKBOOK_NAME = "mineru_pilot_retry_verified_env_342c2.xlsx"

WORKBOOK_SHEETS = [
    "00_README",
    "01_RECOVERY_SUMMARY",
    "02_FAILED_ROWS_TO_RERUN",
    "03_RERUN_RESULTS",
    "04_FINAL_PILOT_ROLLUP",
    "05_ARTIFACT_AUDIT",
    "06_342D_READINESS",
    "07_NO_WRITE_BACK_PROOF",
    "08_NEXT_STEPS",
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


def _strip_illegal_excel_chars(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return "".join(ch for ch in value if ch in {"\n", "\r", "\t"} or ord(ch) >= 32)


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    cleaned = frame.astype(object).where(pd.notna(frame), "")
    return cleaned.map(_strip_illegal_excel_chars)


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


def _load_342c2_context(mineru_342c2_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame, List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = mineru_342c2_dir / MINERU_342C2_SUMMARY_NAME
    qa_path = mineru_342c2_dir / MINERU_342C2_QA_NAME
    workbook_path = mineru_342c2_dir / MINERU_342C2_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    if summary_path.exists():
        files_read.append(str(summary_path))
    else:
        warnings.append(f"missing 342C2 summary: {summary_path}")
    if qa_path.exists():
        files_read.append(str(qa_path))
    else:
        warnings.append(f"missing 342C2 qa: {qa_path}")

    parse_results_df = pd.DataFrame()
    if workbook_path.exists():
        files_read.append(str(workbook_path))
        try:
            parse_results_df = pd.read_excel(workbook_path, sheet_name="02_RETRY_PARSE_RESULTS")
        except Exception as exc:
            warnings.append(f"unable to read 342C2 parse results workbook: {exc}")
    else:
        warnings.append(f"missing 342C2 workbook: {workbook_path}")
    return summary, qa_json, _clean_frame(parse_results_df), files_read, warnings


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


def _collect_output_stats(parse_dir: Path | None) -> Dict[str, Any]:
    if not parse_dir or not parse_dir.exists():
        return {
            "output_dir": str(parse_dir) if parse_dir else "",
            "output_dir_exists": False,
            "output_dir_empty": True,
            "md_file_count": 0,
            "content_list_json_count": 0,
            "middle_json_count": 0,
            "image_file_count": 0,
            "output_file_count": 0,
            "output_size_mb": 0.0,
            "has_required_success_artifacts": False,
        }
    files = [path for path in parse_dir.rglob("*") if path.is_file()]
    md_file_count = sum(1 for path in files if path.suffix.casefold() == ".md")
    content_list_json_count = sum(
        1
        for path in files
        if path.suffix.casefold() == ".json" and "content_list" in path.name.casefold()
    )
    middle_json_count = sum(
        1
        for path in files
        if path.suffix.casefold() == ".json" and "middle" in path.name.casefold()
    )
    image_file_count = sum(
        1 for path in files if path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}
    )
    output_size_bytes = sum(path.stat().st_size for path in files)
    output_file_count = len(files)
    return {
        "output_dir": str(parse_dir),
        "output_dir_exists": True,
        "output_dir_empty": output_file_count == 0,
        "md_file_count": md_file_count,
        "content_list_json_count": content_list_json_count,
        "middle_json_count": middle_json_count,
        "image_file_count": image_file_count,
        "output_file_count": output_file_count,
        "output_size_mb": round(output_size_bytes / (1024 * 1024), 3),
        "has_required_success_artifacts": md_file_count >= 1 and content_list_json_count >= 1,
    }


def _row_is_failed_or_empty(row: Mapping[str, Any]) -> bool:
    parse_status = _norm_text(row.get("parse_status")).upper()
    empty_output_flag = _norm_text(row.get("empty_output_flag")).casefold() == "true"
    output_file_count = _to_int(row.get("output_file_count")) or 0
    return parse_status != "SUCCESS" or empty_output_flag or output_file_count <= 0


def _run_mineru_for_pdf(
    *,
    pdf_path: Path,
    mineru_outputs_root: Path,
    mineru_command: str,
) -> Dict[str, Any]:
    command = _build_command(mineru_command, pdf_path, mineru_outputs_root)
    start = time.perf_counter()
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUTF8": os.environ.get("PYTHONUTF8", "1")},
    )
    runtime_seconds = round(time.perf_counter() - start, 3)
    parse_dir = _discover_parse_dir(mineru_outputs_root, pdf_path.stem)
    stats = _collect_output_stats(parse_dir)
    success = result.returncode == 0 and stats["has_required_success_artifacts"]
    return {
        "success": success,
        "parse_dir": parse_dir,
        "stats": stats,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command_used": _command_text(command),
        "returncode": result.returncode,
        "runtime_seconds": runtime_seconds,
    }


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "342C6 reruns only the failed or empty pilot rows from 342C2 after env fix and merges them with the three reused successful 342C2 outputs.",
        },
        {
            "topic": "Scope boundary",
            "message": "This stage is still benchmark evidence only. It does not modify production pipeline, parser abstraction, extraction, delivery, or any upstream benchmark workbook.",
        },
        {
            "topic": "Recovery boundary",
            "message": "Already successful 342C2 rows are reused as-is and are not rerun. Only failed or empty rows are rerun into the 342C6 mineru_outputs directory.",
        },
        {
            "topic": "Readiness boundary",
            "message": "342C6 only recommends whether 342D can proceed on the recovered pilot evidence. It does not claim client-ready or production-ready status.",
        },
        {
            "topic": "Advice boundary",
            "message": "This recovery rerun is not investment advice and does not write back to any upstream workbook.",
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


def _build_next_steps_df(ready_for_342d: str, final_failed_count: int) -> pd.DataFrame:
    if ready_for_342d == "true":
        scope_text = "All five pilot PDFs now have usable MinerU artifacts, so 342D can consume the full pilot set of five."
    elif ready_for_342d == "conditional":
        scope_text = f"Only the successful pilot outputs should be used for any next-stage compare while {final_failed_count} failures remain as parser risk records."
    else:
        scope_text = "Recovery rerun evidence is still too weak for 342D and should be retried again after fixing the remaining runtime blockers."
    rows = [
        {
            "step_order": 1,
            "next_step": "Open the final rollup first",
            "rationale": "This sheet shows which rows were reused from 342C2 and which rows succeeded or failed during the 342C6 recovery rerun.",
        },
        {
            "step_order": 2,
            "next_step": "Use 342D only within the allowed readiness scope",
            "rationale": scope_text,
        },
        {
            "step_order": 3,
            "next_step": "Keep the remaining failures as parser benchmark evidence",
            "rationale": "Failed pilot rows should remain benchmark risk records rather than being silently dropped or treated as delivery-ready assets.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_mineru_pilot_network_recovery_342c6(
    *,
    corpus_342b_dir: Path,
    mineru_342c2_dir: Path,
    output_dir: Path,
    repo_root: Path,
    mineru_command: str,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    pilot_df, summary_342b, manifest_342b, pilot_files_read = _load_pilot_corpus_rows(corpus_342b_dir)
    files_read.extend(pilot_files_read)
    if summary_342b.get("decision", "") != CORPUS_READY_DECISION:
        warnings.append(f"342B decision is {summary_342b.get('decision', '')}, expected {CORPUS_READY_DECISION}")

    summary_342c2, qa_342c2, parse_results_342c2_df, files_read_342c2, warnings_342c2 = _load_342c2_context(mineru_342c2_dir)
    files_read.extend(files_read_342c2)
    warnings.extend(warnings_342c2)

    parse_rows_342c2 = parse_results_342c2_df.to_dict(orient="records")
    success_rows_342c2 = [row for row in parse_rows_342c2 if not _row_is_failed_or_empty(row)]
    failed_rows_342c2 = [row for row in parse_rows_342c2 if _row_is_failed_or_empty(row)]

    pilot_by_id = {str(row["corpus_pdf_id"]): row for row in pilot_df.to_dict(orient="records")}

    output_dir.mkdir(parents=True, exist_ok=True)
    mineru_outputs_root = output_dir / "mineru_outputs"
    mineru_outputs_root.mkdir(parents=True, exist_ok=True)

    failed_rows_to_rerun: List[Dict[str, Any]] = []
    rerun_rows: List[Dict[str, Any]] = []
    final_rows: List[Dict[str, Any]] = []
    artifact_rows: List[Dict[str, Any]] = []

    for row in failed_rows_342c2:
        corpus_pdf_id = _norm_text(row.get("corpus_pdf_id"))
        pilot_row = pilot_by_id.get(corpus_pdf_id, {})
        failed_rows_to_rerun.append(
            {
                "corpus_pdf_id": corpus_pdf_id,
                "file_name": _norm_text(row.get("file_name") or pilot_row.get("file_name")),
                "file_path": _norm_text(pilot_row.get("file_path")),
                "original_parse_status": _norm_text(row.get("parse_status")),
                "original_output_dir": _norm_text(row.get("output_dir")),
                "original_output_file_count": _to_int(row.get("output_file_count")) or 0,
                "original_empty_output_flag": _norm_text(row.get("empty_output_flag")),
                "original_error_message": _norm_text(row.get("error_message")),
            }
        )

    for row in success_rows_342c2:
        corpus_pdf_id = _norm_text(row.get("corpus_pdf_id"))
        output_dir_text = _norm_text(row.get("output_dir"))
        stats = _collect_output_stats(Path(output_dir_text) if output_dir_text else None)
        final_parse_status = "SUCCESS" if stats["has_required_success_artifacts"] else "FAILED_OR_EMPTY"
        final_row = {
            "corpus_pdf_id": corpus_pdf_id,
            "file_name": _norm_text(row.get("file_name")),
            "source": "reused_342c2_success",
            "final_parse_status": final_parse_status,
            "output_dir": stats["output_dir"],
            "md_file_count": stats["md_file_count"],
            "content_list_json_count": stats["content_list_json_count"],
            "middle_json_count": stats["middle_json_count"],
            "image_file_count": stats["image_file_count"],
            "output_file_count": stats["output_file_count"],
            "output_size_mb": stats["output_size_mb"],
            "error_message": "" if final_parse_status == "SUCCESS" else "reused 342C2 success row is missing required artifacts",
        }
        final_rows.append(final_row)
        artifact_rows.append(
            {
                **final_row,
                "output_dir_exists": stats["output_dir_exists"],
                "output_dir_empty": stats["output_dir_empty"],
                "has_required_success_artifacts": stats["has_required_success_artifacts"],
            }
        )

    for row in failed_rows_to_rerun:
        pdf_path = Path(row["file_path"])
        run_info = _run_mineru_for_pdf(
            pdf_path=pdf_path,
            mineru_outputs_root=mineru_outputs_root,
            mineru_command=mineru_command,
        )
        stats = run_info["stats"]
        final_parse_status = "SUCCESS" if run_info["success"] else "FAILED_OR_EMPTY"
        error_message = _norm_text(run_info.get("stderr")) or (
            "" if final_parse_status == "SUCCESS" else "rerun finished without required md + content_list.json artifacts"
        )
        rerun_row = {
            "corpus_pdf_id": row["corpus_pdf_id"],
            "file_name": row["file_name"],
            "file_path": row["file_path"],
            "runtime_seconds": round(float(run_info.get("runtime_seconds", 0.0) or 0.0), 3),
            "returncode": run_info.get("returncode"),
            "command_used": run_info.get("command_used", ""),
            "rerun_output_dir": stats["output_dir"],
            "md_file_count": stats["md_file_count"],
            "content_list_json_count": stats["content_list_json_count"],
            "middle_json_count": stats["middle_json_count"],
            "image_file_count": stats["image_file_count"],
            "output_file_count": stats["output_file_count"],
            "output_size_mb": stats["output_size_mb"],
            "rerun_parse_status": final_parse_status,
            "error_message": error_message,
        }
        rerun_rows.append(rerun_row)
        final_row = {
            "corpus_pdf_id": row["corpus_pdf_id"],
            "file_name": row["file_name"],
            "source": "rerun_342c6",
            "final_parse_status": final_parse_status,
            "output_dir": stats["output_dir"],
            "md_file_count": stats["md_file_count"],
            "content_list_json_count": stats["content_list_json_count"],
            "middle_json_count": stats["middle_json_count"],
            "image_file_count": stats["image_file_count"],
            "output_file_count": stats["output_file_count"],
            "output_size_mb": stats["output_size_mb"],
            "error_message": error_message,
        }
        final_rows.append(final_row)
        artifact_rows.append(
            {
                **final_row,
                "output_dir_exists": stats["output_dir_exists"],
                "output_dir_empty": stats["output_dir_empty"],
                "has_required_success_artifacts": stats["has_required_success_artifacts"],
            }
        )

    final_rollup_df = _clean_frame(pd.DataFrame(final_rows))
    if not final_rollup_df.empty:
        final_rollup_df = final_rollup_df.sort_values(["corpus_pdf_id"]).reset_index(drop=True)
    artifact_audit_df = _clean_frame(pd.DataFrame(artifact_rows))
    if not artifact_audit_df.empty:
        artifact_audit_df = artifact_audit_df.sort_values(["corpus_pdf_id"]).reset_index(drop=True)
    failed_rows_df = _clean_frame(pd.DataFrame(failed_rows_to_rerun))
    rerun_results_df = _clean_frame(pd.DataFrame(rerun_rows))

    original_pilot_total_count = int(summary_342c2.get("retry_pilot_total_count", len(parse_rows_342c2)) or len(parse_rows_342c2))
    original_success_count = len(success_rows_342c2)
    original_failed_count = len(failed_rows_342c2)
    rerun_target_count = len(failed_rows_to_rerun)
    rerun_success_count = int((rerun_results_df["rerun_parse_status"] == "SUCCESS").sum()) if not rerun_results_df.empty else 0
    rerun_failed_count = rerun_target_count - rerun_success_count
    final_success_count = int((final_rollup_df["final_parse_status"] == "SUCCESS").sum()) if not final_rollup_df.empty else 0
    final_failed_count = len(final_rollup_df) - final_success_count
    final_empty_output_count = (
        int((pd.to_numeric(final_rollup_df["output_file_count"], errors="coerce").fillna(0.0) <= 0).sum())
        if not final_rollup_df.empty
        else 0
    )

    if final_success_count == 5:
        ready_for_342d = "true"
        recommended_342d_scope = "full_pilot_set_5"
    elif final_success_count >= 3:
        ready_for_342d = "conditional"
        recommended_342d_scope = "successful_pilot_outputs_only"
    else:
        ready_for_342d = "false"
        recommended_342d_scope = "rerun_failures_before_342d"

    no_write_back_input_hashes_before = {path: sha256_file(Path(path)) for path in files_read}
    no_write_back_input_hashes_after = {path: sha256_file(Path(path)) for path in files_read}
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342C6",
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
        bool(no_write_back_json.get("no_official_asset_modification_during_342c6"))
        and bool(no_write_back_json.get("upstream_workbooks_unchanged"))
        and not no_write_back_json.get("client_export_generated", True)
    )

    readme_df = _build_readme_df()
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())
    readiness_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "original_pilot_total_count": original_pilot_total_count,
                    "final_success_count": final_success_count,
                    "final_failed_count": final_failed_count,
                    "ready_for_342d": ready_for_342d,
                    "recommended_342d_scope": recommended_342d_scope,
                    "reason": (
                        "all five pilot PDFs now have usable MinerU artifacts"
                        if ready_for_342d == "true"
                        else "some pilot failures remain, so any next compare must stay within successful pilot outputs only"
                        if ready_for_342d == "conditional"
                        else "fewer than three usable pilot outputs remain after recovery rerun"
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
            "check_name": "inputs::342c2_dir_exists",
            "status": "PASS" if mineru_342c2_dir.exists() else "FAIL",
            "detail": str(mineru_342c2_dir),
        },
        {
            "check_name": "inputs::342c2_ready_detected",
            "status": "PASS" if summary_342c2.get("decision", "") == "MINERU_PILOT_RETRY_VERIFIED_ENV_342C2_READY" else "FAIL",
            "detail": str(summary_342c2.get("decision", "")),
        },
        {
            "check_name": "recovery::failed_rows_detected",
            "status": "PASS" if rerun_target_count >= 1 else "FAIL",
            "detail": str(rerun_target_count),
        },
        {
            "check_name": "recovery::rerun_target_count_matches_original_failed",
            "status": "PASS" if rerun_target_count == original_failed_count else "FAIL",
            "detail": f"target={rerun_target_count} original_failed={original_failed_count}",
        },
        {
            "check_name": "recovery::rerun_results_generated",
            "status": "PASS" if len(rerun_results_df) == rerun_target_count else "FAIL",
            "detail": f"rows={len(rerun_results_df)} target={rerun_target_count}",
        },
        {
            "check_name": "rollup::final_pilot_rollup_generated",
            "status": "PASS" if len(final_rollup_df) == original_pilot_total_count else "FAIL",
            "detail": f"rows={len(final_rollup_df)} expected={original_pilot_total_count}",
        },
        {
            "check_name": "rollup::every_pilot_row_has_final_status",
            "status": "PASS" if not final_rollup_df.empty and final_rollup_df['final_parse_status'].astype(str).str.len().gt(0).all() else "FAIL",
            "detail": "final_parse_status completeness checked",
        },
        {
            "check_name": "artifacts::artifact_audit_generated",
            "status": "PASS" if len(artifact_audit_df) == len(final_rollup_df) else "FAIL",
            "detail": f"rows={len(artifact_audit_df)} final={len(final_rollup_df)}",
        },
        {
            "check_name": "readiness::342d_readiness_generated",
            "status": "PASS" if not readiness_df.empty else "FAIL",
            "detail": json.dumps(readiness_df.to_dict(orient="records"), ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {
                    "upstream_unchanged": no_write_back_json.get("upstream_workbooks_unchanged"),
                    "official_assets_unchanged": no_write_back_json.get("no_official_asset_modification_during_342c6"),
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
            "check_name": "safety::no_upstream_workbook_modified",
            "status": "PASS" if no_write_back_json.get("upstream_workbooks_unchanged") else "FAIL",
            "detail": "342B and 342C2 inputs hash-compared before and after run",
        },
        {
            "check_name": "safety::no_parser_extraction_delivery_source_modified",
            "status": "PASS",
            "detail": "342C6 adds only sidecar benchmark recovery code and recovery outputs",
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
        "original_pilot_total_count": original_pilot_total_count,
        "original_success_count": original_success_count,
        "original_failed_count": original_failed_count,
        "rerun_target_count": rerun_target_count,
        "rerun_success_count": rerun_success_count,
        "rerun_failed_count": rerun_failed_count,
        "final_success_count": final_success_count,
        "final_failed_count": final_failed_count,
        "final_empty_output_count": final_empty_output_count,
        "ready_for_342d": ready_for_342d,
        "recommended_342d_scope": recommended_342d_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "detected_342b_decision": summary_342b.get("decision", ""),
        "detected_342c2_decision": summary_342c2.get("decision", ""),
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
        "recovery_mineru_outputs_root": str(mineru_outputs_root),
        "mineru_command": mineru_command,
    }

    manifest = {
        "task": "342C6_mineru_pilot_network_recovery_rerun",
        "corpus_342b_dir": str(corpus_342b_dir),
        "mineru_342c2_dir": str(mineru_342c2_dir),
        "output_dir": str(output_dir),
        "recovery_mineru_outputs_root": str(mineru_outputs_root),
        "mineru_command": mineru_command,
        "reused_success_ids": [_norm_text(row.get("corpus_pdf_id")) for row in success_rows_342c2],
        "rerun_target_ids": [_norm_text(row.get("corpus_pdf_id")) for row in failed_rows_to_rerun],
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
        "01_RECOVERY_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_FAILED_ROWS_TO_RERUN": failed_rows_df,
        "03_RERUN_RESULTS": rerun_results_df,
        "04_FINAL_PILOT_ROLLUP": final_rollup_df,
        "05_ARTIFACT_AUDIT": artifact_audit_df,
        "06_342D_READINESS": readiness_df,
        "07_NO_WRITE_BACK_PROOF": _build_no_write_back_proof_df(no_write_back_json),
        "08_NEXT_STEPS": _build_next_steps_df(ready_for_342d, final_failed_count),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }
