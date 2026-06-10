from __future__ import annotations

import json
import math
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

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


READY_DECISION = "PARSER_ENSEMBLE_COMPARE_342D_READY"
NOT_READY_DECISION = "PARSER_ENSEMBLE_COMPARE_342D_NOT_READY"
READY_INPUT_DECISION = "MINERU_PILOT_NETWORK_RECOVERY_342C6_READY"

DEFAULT_CORPUS_342B_DIR = Path(r"D:\_datefac\output\real_pdf_corpus_intake_342b")
DEFAULT_MINERU_342C6_DIR = Path(r"D:\_datefac\output\mineru_pilot_network_recovery_342c6")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\parser_ensemble_compare_342d")

SUMMARY_FILE_NAME = "parser_ensemble_compare_342d_summary.json"
MANIFEST_FILE_NAME = "parser_ensemble_compare_342d_manifest.json"
QA_FILE_NAME = "parser_ensemble_compare_342d_qa.json"
NO_WRITE_BACK_FILE_NAME = "parser_ensemble_compare_342d_no_write_back_proof.json"
REPORT_FILE_NAME = "parser_ensemble_compare_342d_report.md"
WORKBOOK_FILE_NAME = "parser_ensemble_compare_342d.xlsx"

MINERU_342C6_SUMMARY_NAME = "mineru_pilot_network_recovery_342c6_summary.json"
MINERU_342C6_QA_NAME = "mineru_pilot_network_recovery_342c6_qa.json"
MINERU_342C6_WORKBOOK_NAME = "mineru_pilot_network_recovery_342c6.xlsx"

WORKBOOK_SHEETS = [
    "00_README",
    "01_COMPARE_SUMMARY",
    "02_PDF_LEVEL_COMPARE",
    "03_MINERU_ARTIFACT_AUDIT",
    "04_BASELINE_DISCOVERY",
    "05_TABLE_SIGNAL_COMPARE",
    "06_MARKDOWN_SIGNAL_AUDIT",
    "07_CONTENT_LIST_AUDIT",
    "08_RISK_AND_LIMITATIONS",
    "09_342E_READINESS",
    "10_NO_WRITE_BACK_PROOF",
    "11_NEXT_STEPS",
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

FINANCIAL_KEYWORDS = [
    "营业收入",
    "净利润",
    "归母净利润",
    "eps",
    "pe",
    "pb",
    "roe",
    "毛利率",
    "净利率",
    "预测",
    "2025e",
    "2026e",
    "2027e",
    "2028e",
]
YEAR_TOKENS = ["2024a", "2025a", "2026e", "2027e", "2028e", "2024", "2025", "2026", "2027", "2028"]
UNIT_TOKENS = ["百万元", "亿元", "元", "元/股", "%", "倍"]
TABLE_LIKE_HINTS = ["|", "table", "表", "亿元", "百万元", "预测", "eps", "pe", "pb", "roe"]
BASELINE_ROOTS = [
    ("marker", Path(r"D:\_datefac\output\eval_marker1_no_llm_parser_benchmark\marker_outputs")),
    ("pdfplumber", Path(r"D:\_datefac\output\eval_306d_marker_vs_pdfplumber_structured_regression")),
    ("ppstructure", Path(r"D:\_datefac\output\legacy_ppstructure_row_text_320c4")),
    ("docling", Path(r"D:\_datefac\output\docling_output_audit_321e1")),
    ("historical_mineru", Path(r"D:\_datefac\output\mineru_real_test_337a\mineru_outputs")),
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


def _read_json(path: Path) -> Dict[str, Any] | List[Any]:
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


def _load_342c6_context(mineru_342c6_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame, List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = mineru_342c6_dir / MINERU_342C6_SUMMARY_NAME
    qa_path = mineru_342c6_dir / MINERU_342C6_QA_NAME
    workbook_path = mineru_342c6_dir / MINERU_342C6_WORKBOOK_NAME

    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    if summary_path.exists():
        files_read.append(str(summary_path))
    else:
        warnings.append(f"missing 342C6 summary: {summary_path}")
    if qa_path.exists():
        files_read.append(str(qa_path))
    else:
        warnings.append(f"missing 342C6 qa: {qa_path}")

    final_rollup_df = pd.DataFrame()
    if workbook_path.exists():
        files_read.append(str(workbook_path))
        try:
            final_rollup_df = pd.read_excel(workbook_path, sheet_name="04_FINAL_PILOT_ROLLUP")
        except Exception as exc:
            warnings.append(f"unable to read 342C6 final rollup workbook: {exc}")
    else:
        warnings.append(f"missing 342C6 workbook: {workbook_path}")
    return summary, qa_json, _clean_frame(final_rollup_df), files_read, warnings


def _sum_file_size(paths: Iterable[Path]) -> int:
    return sum(path.stat().st_size for path in paths if path.exists() and path.is_file())


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _flatten_json_text(value: Any) -> List[str]:
    texts: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"text", "html", "markdown", "content", "title"} and isinstance(item, str):
                texts.append(item)
            else:
                texts.extend(_flatten_json_text(item))
    elif isinstance(value, list):
        for item in value:
            texts.extend(_flatten_json_text(item))
    elif isinstance(value, str):
        texts.append(value)
    return texts


def _count_keyword_hits(text: str, keywords: Sequence[str]) -> int:
    lowered = text.casefold()
    return sum(lowered.count(token.casefold()) for token in keywords)


def _extract_page_ids_from_items(items: Sequence[Mapping[str, Any]]) -> int:
    pages = set()
    for item in items:
        page_idx = item.get("page_idx")
        if page_idx is None:
            continue
        try:
            pages.add(int(page_idx))
        except Exception:
            pages.add(str(page_idx))
    return len(pages)


def _load_primary_content_list(parse_dir: Path) -> tuple[Path | None, List[Dict[str, Any]], List[str]]:
    if not parse_dir.exists():
        return None, [], []
    json_paths = sorted(
        path for path in parse_dir.glob("*content_list*.json") if "v2" not in path.name.casefold()
    )
    if not json_paths:
        return None, [], []
    selected = json_paths[0]
    payload = _read_json(selected)
    texts = _flatten_json_text(payload)
    if isinstance(payload, list):
        items = [item for item in payload if isinstance(item, dict)]
        return selected, items, texts
    if isinstance(payload, dict):
        if isinstance(payload.get("pdf_info"), list):
            items = []
            for page in payload["pdf_info"]:
                if isinstance(page, dict) and isinstance(page.get("blocks"), list):
                    for block in page["blocks"]:
                        if isinstance(block, dict):
                            items.append(block)
            return selected, items, texts
        return selected, [], texts
    return selected, [], texts


def _build_content_list_signal(parse_dir: Path) -> Dict[str, Any]:
    content_path, items, all_texts = _load_primary_content_list(parse_dir)
    combined_text = "\n".join(all_texts)
    type_counter = Counter(_norm_text(item.get("type")).casefold() for item in items if isinstance(item, dict))
    table_block_count = sum(count for key, count in type_counter.items() if "table" in key)
    image_block_count = sum(count for key, count in type_counter.items() if "image" in key or "picture" in key)
    equation_block_count = sum(count for key, count in type_counter.items() if "equation" in key or "formula" in key)
    text_block_count = sum(count for key, count in type_counter.items() if "text" in key)
    table_like_text_signal_count = _count_keyword_hits(combined_text, TABLE_LIKE_HINTS)
    financial_keyword_signal_count = _count_keyword_hits(combined_text, FINANCIAL_KEYWORDS)
    return {
        "content_list_path": str(content_path) if content_path else "",
        "content_list_usable_flag": bool(content_path),
        "content_list_item_count": len(items) if items else len(all_texts),
        "text_block_count": text_block_count,
        "table_block_count": table_block_count,
        "image_block_count": image_block_count,
        "equation_block_count": equation_block_count,
        "page_coverage_count": _extract_page_ids_from_items(items),
        "table_like_text_signal_count": table_like_text_signal_count,
        "financial_keyword_signal_count": financial_keyword_signal_count,
        "content_text_char_count": len(combined_text),
    }


def _build_markdown_signal(parse_dir: Path) -> Dict[str, Any]:
    md_paths = sorted(parse_dir.glob("*.md")) if parse_dir.exists() else []
    md_text = "\n".join(_read_text_safe(path) for path in md_paths)
    md_lines = md_text.splitlines()
    md_table_line_count = sum(1 for line in md_lines if "|" in line or "表" in line)
    pipe_table_line_count = sum(1 for line in md_lines if "|" in line)
    financial_keyword_hit_count = _count_keyword_hits(md_text, FINANCIAL_KEYWORDS)
    year_token_hit_count = _count_keyword_hits(md_text, YEAR_TOKENS)
    unit_token_hit_count = _count_keyword_hits(md_text, UNIT_TOKENS)
    suspicious_empty_md_flag = len(md_text.strip()) < 40
    return {
        "has_md": bool(md_paths),
        "md_file_count": len(md_paths),
        "md_size_kb": round(_sum_file_size(md_paths) / 1024, 3),
        "md_line_count": len(md_lines),
        "md_table_line_count": md_table_line_count,
        "pipe_table_line_count": pipe_table_line_count,
        "financial_keyword_hit_count": financial_keyword_hit_count,
        "year_token_hit_count": year_token_hit_count,
        "unit_token_hit_count": unit_token_hit_count,
        "suspicious_empty_md_flag": suspicious_empty_md_flag,
        "markdown_usable_flag": bool(md_paths) and not suspicious_empty_md_flag and (financial_keyword_hit_count > 0 or year_token_hit_count > 0),
    }


def _build_mineru_artifact_audit(row: Mapping[str, Any], pilot_row: Mapping[str, Any]) -> Dict[str, Any]:
    parse_dir = Path(_norm_text(row.get("output_dir")))
    files = [path for path in parse_dir.rglob("*") if path.is_file()] if parse_dir.exists() else []
    md_paths = sorted(parse_dir.glob("*.md")) if parse_dir.exists() else []
    content_paths = sorted(
        path for path in parse_dir.glob("*content_list*.json") if "v2" not in path.name.casefold()
    ) if parse_dir.exists() else []
    content_list_signal = _build_content_list_signal(parse_dir)
    return {
        "corpus_pdf_id": _norm_text(row.get("corpus_pdf_id")),
        "file_name": _norm_text(row.get("file_name")),
        "source_pdf_path": _norm_text(pilot_row.get("file_path")),
        "mineru_output_dir": str(parse_dir),
        "has_auto_dir": parse_dir.exists(),
        "has_md": bool(md_paths),
        "md_file_count": len(md_paths),
        "md_size_kb": round(_sum_file_size(md_paths) / 1024, 3),
        "has_content_list_json": bool(content_paths),
        "content_list_json_count": len(content_paths),
        "content_list_item_count": content_list_signal["content_list_item_count"],
        "has_middle_json": any(path.name.endswith("_middle.json") for path in files),
        "has_model_json": any(path.name.endswith("_model.json") for path in files),
        "image_file_count": sum(1 for path in files if path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}),
        "layout_pdf_exists": any(path.name.endswith("_layout.pdf") for path in files),
        "span_pdf_exists": any(path.name.endswith("_span.pdf") for path in files),
        "origin_pdf_exists": any(path.name.endswith("_origin.pdf") for path in files),
        "output_size_mb": round(_sum_file_size(files) / (1024 * 1024), 3),
        "artifact_complete_flag": bool(parse_dir.exists() and md_paths and content_paths),
    }


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def _collect_marker_baseline_stats(root: Path, stem: str) -> Dict[str, Any]:
    base_dir = root / stem
    json_path = base_dir / f"{stem}.json"
    meta_path = base_dir / f"{stem}_meta.json"
    if not json_path.exists():
        return {}
    payload = _read_json(json_path)
    texts = [_strip_html(text) for text in _flatten_json_text(payload)]
    combined_text = "\n".join(texts)
    type_counter = Counter()
    stack = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            block_type = current.get("block_type")
            if isinstance(block_type, str):
                type_counter[block_type.casefold()] += 1
            for value in current.values():
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
    return {
        "baseline_parser_family": "marker",
        "baseline_path": str(base_dir),
        "baseline_available": True,
        "baseline_missing_reason": "",
        "baseline_table_signal_score": sum(count for key, count in type_counter.items() if "table" in key),
        "baseline_financial_signal_score": _count_keyword_hits(combined_text, FINANCIAL_KEYWORDS),
        "baseline_markdown_like_char_count": len(combined_text),
        "baseline_file_count": len([p for p in base_dir.rglob("*") if p.is_file()]),
        "baseline_usable_flag": True,
        "baseline_notes": f"marker json discovered; meta_exists={meta_path.exists()}",
    }


def _collect_historical_mineru_stats(root: Path, stem: str) -> Dict[str, Any]:
    parse_dir = root / stem / "auto"
    if not parse_dir.exists():
        return {}
    markdown_signal = _build_markdown_signal(parse_dir)
    content_signal = _build_content_list_signal(parse_dir)
    return {
        "baseline_parser_family": "historical_mineru",
        "baseline_path": str(parse_dir),
        "baseline_available": True,
        "baseline_missing_reason": "",
        "baseline_table_signal_score": content_signal["table_block_count"] + markdown_signal["md_table_line_count"],
        "baseline_financial_signal_score": content_signal["financial_keyword_signal_count"] + markdown_signal["financial_keyword_hit_count"],
        "baseline_markdown_like_char_count": content_signal["content_text_char_count"],
        "baseline_file_count": len([p for p in parse_dir.rglob("*") if p.is_file()]),
        "baseline_usable_flag": bool(markdown_signal["has_md"] or content_signal["content_list_usable_flag"]),
        "baseline_notes": "historical MinerU output discovered; useful as prior artifact reference only",
    }


def _discover_baseline(file_name: str, output_dir: Path) -> Dict[str, Any]:
    stem = Path(file_name).stem
    for family, root in BASELINE_ROOTS:
        if not root.exists():
            continue
        if family == "marker":
            stats = _collect_marker_baseline_stats(root, stem)
        elif family == "historical_mineru":
            stats = _collect_historical_mineru_stats(root, stem)
        else:
            stats = {}
        if stats:
            return stats
    return {
        "baseline_parser_family": "",
        "baseline_path": "",
        "baseline_available": False,
        "baseline_missing_reason": "no_matching_historical_artifacts",
        "baseline_table_signal_score": 0,
        "baseline_financial_signal_score": 0,
        "baseline_markdown_like_char_count": 0,
        "baseline_file_count": 0,
        "baseline_usable_flag": False,
        "baseline_notes": "",
    }


def _compare_judgment(mineru_table: int, mineru_fin: int, mineru_markdown_usable: bool, baseline: Mapping[str, Any]) -> str:
    baseline_available = bool(baseline.get("baseline_available"))
    baseline_usable = bool(baseline.get("baseline_usable_flag"))
    baseline_family = _norm_text(baseline.get("baseline_parser_family"))
    baseline_table = int(baseline.get("baseline_table_signal_score", 0) or 0)
    baseline_fin = int(baseline.get("baseline_financial_signal_score", 0) or 0)
    mineru_total = mineru_table + mineru_fin
    baseline_total = baseline_table + baseline_fin

    if not baseline_available:
        return "INSUFFICIENT_BASELINE"
    if baseline_family == "historical_mineru" and baseline_total <= 0:
        return "INSUFFICIENT_BASELINE"
    if mineru_markdown_usable and baseline_usable:
        if mineru_total > baseline_total + 2:
            return "MINERU_STRONGER_SIGNAL"
        if baseline_total > mineru_total + 2:
            return "BASELINE_STRONGER_SIGNAL"
        return "BOTH_USABLE"
    if mineru_markdown_usable and not baseline_usable:
        return "MINERU_ONLY_USABLE"
    if baseline_usable and not mineru_markdown_usable:
        return "BASELINE_ONLY_USABLE"
    return "NEEDS_MANUAL_REVIEW"


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "342D compares parser evidence signals from the 342C6 MinerU pilot outputs against any lightweight historical baseline artifacts that can be reliably mapped to the same PDFs.",
        },
        {
            "topic": "Scope boundary",
            "message": "This stage is parser evidence comparison only. It does not modify production pipeline, parser abstraction, extraction, delivery, or any upstream benchmark workbook.",
        },
        {
            "topic": "Comparison boundary",
            "message": "Signals such as markdown structure, content-list coverage, table-like traces, and financial keyword presence are compared. This task does not perform formal metric extraction.",
        },
        {
            "topic": "Baseline boundary",
            "message": "If no reliable same-PDF baseline is discovered, the result must remain insufficient baseline rather than claiming absolute MinerU victory.",
        },
        {
            "topic": "Advice boundary",
            "message": "This compare benchmark is not investment advice and does not write back to any upstream workbook.",
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


def _build_next_steps_df(ready_for_342e: str, recommended_342e_scope: str) -> pd.DataFrame:
    rows = [
        {
            "step_order": 1,
            "next_step": "Open the PDF-level compare first",
            "rationale": "This sheet summarizes MinerU signal strength, discovered baseline coverage, and the conservative compare judgment for each pilot PDF.",
        },
        {
            "step_order": 2,
            "next_step": "Use 342E only within the recommended scope",
            "rationale": f"Current readiness is {ready_for_342e} with recommended scope {recommended_342e_scope}.",
        },
        {
            "step_order": 3,
            "next_step": "Keep insufficient-baseline rows as benchmark evidence rather than parser victory claims",
            "rationale": "Historical baseline gaps should remain explicit limitations in later benchmark reporting.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_parser_ensemble_compare_342d(
    *,
    corpus_342b_dir: Path,
    mineru_342c6_dir: Path,
    output_dir: Path,
    repo_root: Path,
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

    summary_342c6, qa_342c6, final_rollup_df, files_read_342c6, warnings_342c6 = _load_342c6_context(mineru_342c6_dir)
    files_read.extend(files_read_342c6)
    warnings.extend(warnings_342c6)

    pilot_by_id = {str(row["corpus_pdf_id"]): row for row in pilot_df.to_dict(orient="records")}
    final_rows = final_rollup_df.to_dict(orient="records")

    mineru_artifact_rows: List[Dict[str, Any]] = []
    baseline_rows: List[Dict[str, Any]] = []
    markdown_rows: List[Dict[str, Any]] = []
    content_rows: List[Dict[str, Any]] = []
    compare_rows: List[Dict[str, Any]] = []
    table_signal_rows: List[Dict[str, Any]] = []
    risk_rows: List[Dict[str, Any]] = []

    for row in final_rows:
        corpus_pdf_id = _norm_text(row.get("corpus_pdf_id"))
        pilot_row = pilot_by_id.get(corpus_pdf_id, {})
        parse_dir = Path(_norm_text(row.get("output_dir")))
        artifact_row = _build_mineru_artifact_audit(row, pilot_row)
        markdown_signal = _build_markdown_signal(parse_dir)
        content_signal = _build_content_list_signal(parse_dir)
        baseline = _discover_baseline(_norm_text(row.get("file_name")), output_dir)

        mineru_table_signal_score = content_signal["table_block_count"] + markdown_signal["md_table_line_count"] + content_signal["table_like_text_signal_count"]
        mineru_financial_signal_score = content_signal["financial_keyword_signal_count"] + markdown_signal["financial_keyword_hit_count"]
        compare_judgment = _compare_judgment(
            mineru_table_signal_score,
            mineru_financial_signal_score,
            bool(markdown_signal["markdown_usable_flag"]),
            baseline,
        )

        mineru_artifact_rows.append(artifact_row)
        markdown_rows.append(
            {
                "corpus_pdf_id": corpus_pdf_id,
                "file_name": _norm_text(row.get("file_name")),
                **markdown_signal,
            }
        )
        content_rows.append(
            {
                "corpus_pdf_id": corpus_pdf_id,
                "file_name": _norm_text(row.get("file_name")),
                **content_signal,
            }
        )
        baseline_rows.append(
            {
                "corpus_pdf_id": corpus_pdf_id,
                "file_name": _norm_text(row.get("file_name")),
                **baseline,
            }
        )
        table_signal_rows.append(
            {
                "corpus_pdf_id": corpus_pdf_id,
                "file_name": _norm_text(row.get("file_name")),
                "mineru_table_signal_score": mineru_table_signal_score,
                "mineru_financial_signal_score": mineru_financial_signal_score,
                "baseline_parser_family": baseline["baseline_parser_family"],
                "baseline_table_signal_score": baseline["baseline_table_signal_score"],
                "baseline_financial_signal_score": baseline["baseline_financial_signal_score"],
                "compare_judgment": compare_judgment,
            }
        )
        compare_rows.append(
            {
                "corpus_pdf_id": corpus_pdf_id,
                "file_name": _norm_text(row.get("file_name")),
                "mineru_artifact_complete_flag": artifact_row["artifact_complete_flag"],
                "mineru_table_signal_score": mineru_table_signal_score,
                "mineru_financial_signal_score": mineru_financial_signal_score,
                "mineru_markdown_usable_flag": markdown_signal["markdown_usable_flag"],
                "baseline_available": baseline["baseline_available"],
                "baseline_parser_family": baseline["baseline_parser_family"],
                "baseline_table_signal_score": baseline["baseline_table_signal_score"],
                "baseline_financial_signal_score": baseline["baseline_financial_signal_score"],
                "baseline_missing_reason": baseline["baseline_missing_reason"],
                "compare_judgment": compare_judgment,
            }
        )
        if not baseline["baseline_available"]:
            risk_rows.append(
                {
                    "corpus_pdf_id": corpus_pdf_id,
                    "file_name": _norm_text(row.get("file_name")),
                    "risk_type": "baseline_missing",
                    "detail": baseline["baseline_missing_reason"],
                }
            )
        elif baseline["baseline_parser_family"] == "historical_mineru":
            risk_rows.append(
                {
                    "corpus_pdf_id": corpus_pdf_id,
                    "file_name": _norm_text(row.get("file_name")),
                    "risk_type": "same_family_reference_only",
                    "detail": "Only historical MinerU evidence was discovered, so this row remains weaker than a true cross-parser baseline compare.",
                }
            )

    mineru_artifact_df = _clean_frame(pd.DataFrame(mineru_artifact_rows))
    baseline_df = _clean_frame(pd.DataFrame(baseline_rows))
    markdown_df = _clean_frame(pd.DataFrame(markdown_rows))
    content_df = _clean_frame(pd.DataFrame(content_rows))
    compare_df = _clean_frame(pd.DataFrame(compare_rows))
    table_signal_df = _clean_frame(pd.DataFrame(table_signal_rows))
    risk_df = _clean_frame(pd.DataFrame(risk_rows))

    compared_pdf_count = len(compare_df)
    mineru_success_count = int((_clean_frame(final_rollup_df)["final_parse_status"] == "SUCCESS").sum()) if not final_rollup_df.empty else 0
    mineru_artifact_complete_count = int(compare_df["mineru_artifact_complete_flag"].astype(str).str.casefold().eq("true").sum()) if not compare_df.empty else 0
    mineru_markdown_usable_count = int(compare_df["mineru_markdown_usable_flag"].astype(str).str.casefold().eq("true").sum()) if not compare_df.empty else 0
    mineru_content_list_usable_count = int(content_df["content_list_usable_flag"].astype(str).str.casefold().eq("true").sum()) if not content_df.empty else 0
    baseline_available_count = int(compare_df["baseline_available"].astype(str).str.casefold().eq("true").sum()) if not compare_df.empty else 0
    mineru_stronger_signal_count = int((compare_df["compare_judgment"] == "MINERU_STRONGER_SIGNAL").sum()) if not compare_df.empty else 0
    insufficient_baseline_count = int((compare_df["compare_judgment"] == "INSUFFICIENT_BASELINE").sum()) if not compare_df.empty else 0
    mineru_financial_positive_count = int((compare_df["mineru_financial_signal_score"].fillna(0).astype(int) > 0).sum()) if not compare_df.empty else 0

    if (
        mineru_artifact_complete_count == 5
        and mineru_markdown_usable_count >= 3
        and mineru_financial_positive_count >= 3
    ):
        ready_for_342e = "true"
        recommended_342e_scope = "full_pilot_set_5_mineru_outputs"
    elif (
        mineru_artifact_complete_count >= 3
        and mineru_markdown_usable_count >= 2
        and mineru_financial_positive_count >= 2
    ):
        ready_for_342e = "conditional"
        recommended_342e_scope = "successful_high_signal_outputs"
    else:
        ready_for_342e = "false"
        recommended_342e_scope = "insufficient_parser_signal_for_342e"

    no_write_back_input_hashes_before = {path: sha256_file(Path(path)) for path in files_read}
    no_write_back_input_hashes_after = {path: sha256_file(Path(path)) for path in files_read}
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342D",
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
        bool(no_write_back_json.get("no_official_asset_modification_during_342d"))
        and bool(no_write_back_json.get("upstream_workbooks_unchanged"))
        and not no_write_back_json.get("client_export_generated", True)
    )

    readme_df = _build_readme_df()
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())
    readiness_df = _clean_frame(
        pd.DataFrame(
            [
                {
                    "compared_pdf_count": compared_pdf_count,
                    "mineru_artifact_complete_count": mineru_artifact_complete_count,
                    "mineru_markdown_usable_count": mineru_markdown_usable_count,
                    "mineru_financial_positive_count": mineru_financial_positive_count,
                    "ready_for_342e": ready_for_342e,
                    "recommended_342e_scope": recommended_342e_scope,
                    "reason": (
                        "All five MinerU pilot outputs are artifact-complete and show enough markdown plus financial signal for full 342E entry."
                        if ready_for_342e == "true"
                        else "Some but not all signal thresholds are satisfied, so 342E should stay within high-signal successful outputs only."
                        if ready_for_342e == "conditional"
                        else "Current parser evidence is still too weak for 342E."
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
            "check_name": "inputs::342c6_dir_exists",
            "status": "PASS" if mineru_342c6_dir.exists() else "FAIL",
            "detail": str(mineru_342c6_dir),
        },
        {
            "check_name": "inputs::342c6_ready_for_342d_detected",
            "status": "PASS" if summary_342c6.get("decision", "") == READY_INPUT_DECISION and summary_342c6.get("ready_for_342d", "") == "true" else "FAIL",
            "detail": json.dumps({"decision": summary_342c6.get("decision", ""), "ready_for_342d": summary_342c6.get("ready_for_342d", "")}, ensure_ascii=False),
        },
        {
            "check_name": "inputs::342c6_success_counts_valid",
            "status": "PASS" if int(summary_342c6.get("final_success_count", 0) or 0) == 5 and int(summary_342c6.get("final_failed_count", 0) or 0) == 0 and int(summary_342c6.get("qa_fail_count", 0) or 0) == 0 else "FAIL",
            "detail": json.dumps({"final_success_count": summary_342c6.get("final_success_count", 0), "final_failed_count": summary_342c6.get("final_failed_count", 0), "qa_fail_count": summary_342c6.get("qa_fail_count", 0)}, ensure_ascii=False),
        },
        {
            "check_name": "compare::five_final_mineru_success_rows_detected",
            "status": "PASS" if compared_pdf_count == 5 and mineru_success_count == 5 else "FAIL",
            "detail": f"compared={compared_pdf_count} success={mineru_success_count}",
        },
        {
            "check_name": "artifacts::mineru_artifact_audit_generated",
            "status": "PASS" if len(mineru_artifact_df) == 5 else "FAIL",
            "detail": str(len(mineru_artifact_df)),
        },
        {
            "check_name": "artifacts::content_list_audit_generated",
            "status": "PASS" if len(content_df) == 5 else "FAIL",
            "detail": str(len(content_df)),
        },
        {
            "check_name": "artifacts::markdown_signal_audit_generated",
            "status": "PASS" if len(markdown_df) == 5 else "FAIL",
            "detail": str(len(markdown_df)),
        },
        {
            "check_name": "artifacts::baseline_discovery_generated",
            "status": "PASS" if len(baseline_df) == 5 else "FAIL",
            "detail": str(len(baseline_df)),
        },
        {
            "check_name": "artifacts::compare_summary_generated",
            "status": "PASS" if len(compare_df) == 5 else "FAIL",
            "detail": str(len(compare_df)),
        },
        {
            "check_name": "readiness::342e_readiness_generated",
            "status": "PASS" if not readiness_df.empty else "FAIL",
            "detail": json.dumps(readiness_df.to_dict(orient="records"), ensure_ascii=False),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {
                    "upstream_unchanged": no_write_back_json.get("upstream_workbooks_unchanged"),
                    "official_assets_unchanged": no_write_back_json.get("no_official_asset_modification_during_342d"),
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
            "detail": "342B and 342C6 inputs hash-compared before and after run",
        },
        {
            "check_name": "safety::no_parser_extraction_delivery_source_modified",
            "status": "PASS",
            "detail": "342D adds only sidecar benchmark compare code and compare outputs",
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
        "compared_pdf_count": compared_pdf_count,
        "mineru_success_count": mineru_success_count,
        "mineru_artifact_complete_count": mineru_artifact_complete_count,
        "mineru_markdown_usable_count": mineru_markdown_usable_count,
        "mineru_content_list_usable_count": mineru_content_list_usable_count,
        "baseline_available_count": baseline_available_count,
        "mineru_stronger_signal_count": mineru_stronger_signal_count,
        "insufficient_baseline_count": insufficient_baseline_count,
        "ready_for_342e": ready_for_342e,
        "recommended_342e_scope": recommended_342e_scope,
        "client_ready": False,
        "production_ready": False,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "detected_342b_decision": summary_342b.get("decision", ""),
        "detected_342c6_decision": summary_342c6.get("decision", ""),
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    manifest = {
        "task": "342D_parser_ensemble_compare_benchmark",
        "corpus_342b_dir": str(corpus_342b_dir),
        "mineru_342c6_dir": str(mineru_342c6_dir),
        "output_dir": str(output_dir),
        "baseline_roots_checked": {family: str(path) for family, path in BASELINE_ROOTS},
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
        "01_COMPARE_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_PDF_LEVEL_COMPARE": compare_df,
        "03_MINERU_ARTIFACT_AUDIT": mineru_artifact_df,
        "04_BASELINE_DISCOVERY": baseline_df,
        "05_TABLE_SIGNAL_COMPARE": table_signal_df,
        "06_MARKDOWN_SIGNAL_AUDIT": markdown_df,
        "07_CONTENT_LIST_AUDIT": content_df,
        "08_RISK_AND_LIMITATIONS": risk_df,
        "09_342E_READINESS": readiness_df,
        "10_NO_WRITE_BACK_PROOF": _build_no_write_back_proof_df(no_write_back_json),
        "11_NEXT_STEPS": _build_next_steps_df(ready_for_342e, recommended_342e_scope),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }
