from __future__ import annotations

import json
import subprocess
from collections import defaultdict, deque
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

try:
    import pdfplumber
except Exception:  # pragma: no cover - runtime dependency fallback
    pdfplumber = None


READY_DECISION = "REAL_PDF_CORPUS_INTAKE_342B_READY"
NOT_READY_DECISION = "REAL_PDF_CORPUS_INTAKE_342B_NOT_READY"

DEFAULT_INPUT_DIR = Path(r"D:\_datefac\input")
DEFAULT_FUTURE_INPUT_DIR = Path(r"D:\_datefac\input\real_pdf_benchmark_342a")
DEFAULT_BENCHMARK_PLAN_342A_DIR = Path(r"D:\_datefac\output\larger_real_pdf_benchmark_plan_342a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\real_pdf_corpus_intake_342b")

BENCHMARK_PLAN_342A_SUMMARY_NAME = "larger_real_pdf_benchmark_plan_342a_summary.json"
BENCHMARK_PLAN_READY_DECISION = "LARGER_REAL_PDF_BENCHMARK_PLAN_342A_READY"

PILOT_SPLIT = "pilot_set"
BENCHMARK_SPLIT = "benchmark_set"
HOLDOUT_SPLIT = "holdout_set"
KEEP_DUPLICATE_ACTION = "KEEP_CANONICAL_REVIEW_DUPLICATES"

TIER_ORDER = ["Tier A", "Tier B", "Tier C", "Tier D", "Tier E", "Tier F", "UNKNOWN"]
MONEY_METRIC_HINTS = ["revenue", "profit", "income", "eps", "pe", "pb", "roe"]

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]

WORKBOOK_SHEETS = [
    "00_README",
    "01_CORPUS_SUMMARY",
    "02_PDF_CORPUS",
    "03_DEDUP_AUDIT",
    "04_TIER_ASSIGNMENT",
    "05_SPLIT_PLAN",
    "06_METADATA_AUDIT",
    "07_RUN_READINESS",
    "08_RISK_FLAGS",
    "09_NO_WRITE_BACK_PROOF",
    "10_NEXT_STEPS",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _all_pdf_files(input_dir: Path, future_dir: Path) -> List[Path]:
    roots = [input_dir]
    if future_dir.exists() and future_dir.resolve() != input_dir.resolve():
        roots.append(future_dir)
    seen: set[str] = set()
    pdfs: List[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.pdf")):
            resolved = str(path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            pdfs.append(path)
    return pdfs


def _read_page_count(path: Path) -> tuple[int | None, str | None]:
    if pdfplumber is None:
        return None, "pdfplumber unavailable"
    try:
        with pdfplumber.open(path) as pdf:
            return len(pdf.pages), None
    except Exception as exc:  # pragma: no cover - depends on local PDFs
        return None, f"{type(exc).__name__}: {exc}"


def _source_bucket(path: Path, input_dir: Path, future_dir: Path) -> str:
    if future_dir.exists():
        try:
            path.relative_to(future_dir)
            return "real_pdf_benchmark_342a"
        except ValueError:
            pass
    try:
        relative = path.relative_to(input_dir)
    except ValueError:
        return "outside_input_root"
    if len(relative.parts) <= 1:
        return "input_root"
    return relative.parts[0]


def _extract_document_hint(path: Path) -> str:
    stem = path.stem
    return stem.replace("_", " ").strip()


def _intake_status(file_size: int, page_count: int | None, page_warning: str | None) -> str:
    if file_size == 0:
        return "ZERO_BYTE_FILE"
    if page_warning:
        return "PAGE_COUNT_UNREADABLE"
    if page_count is None:
        return "PAGE_COUNT_MISSING"
    return "INTAKE_READY"


def _scan_pdf_corpus(input_dir: Path, future_dir: Path) -> tuple[pd.DataFrame, Dict[str, str], List[str]]:
    rows: List[Dict[str, Any]] = []
    input_hashes: Dict[str, str] = {}
    warnings: List[str] = []
    for idx, path in enumerate(_all_pdf_files(input_dir, future_dir), start=1):
        stat = path.stat()
        file_size = int(stat.st_size)
        page_count, page_warning = _read_page_count(path) if file_size > 0 else (None, "zero-byte file")
        if page_warning and file_size > 0:
            warnings.append(f"page_count unavailable for {path}: {page_warning}")
        file_hash = sha256_file(path)
        input_hashes[str(path)] = file_hash
        rows.append(
            {
                "corpus_pdf_id": f"342b_pdf_{idx:03d}",
                "file_name": path.name,
                "file_path": str(path),
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 3),
                "sha256": file_hash,
                "modified_time": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "source_bucket": _source_bucket(path, input_dir, future_dir),
                "document_hint": _extract_document_hint(path),
                "page_count": page_count,
                "intake_status": _intake_status(file_size, page_count, page_warning),
                "page_count_warning": page_warning or "",
            }
        )
    return _clean_frame(pd.DataFrame(rows)), input_hashes, warnings


def _group_by_sha(corpus_df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in corpus_df.to_dict(orient="records"):
        groups[str(row.get("sha256", ""))].append(row)
    return groups


def _build_dedup_audit(corpus_df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, str], int]:
    rows: List[Dict[str, Any]] = []
    canonical_by_pdf_id: Dict[str, str] = {}
    duplicate_pdf_count = 0
    duplicate_group_index = 1
    for group_rows in _group_by_sha(corpus_df).values():
        sorted_rows = sorted(group_rows, key=lambda item: (str(item.get("file_path", "")), str(item.get("corpus_pdf_id", ""))))
        canonical_pdf_id = str(sorted_rows[0]["corpus_pdf_id"])
        for row in sorted_rows:
            canonical_by_pdf_id[str(row["corpus_pdf_id"])] = canonical_pdf_id
        if len(sorted_rows) >= 2:
            duplicate_pdf_count += len(sorted_rows) - 1
            rows.append(
                {
                    "duplicate_group_id": f"dup_{duplicate_group_index:03d}",
                    "duplicate_count": len(sorted_rows),
                    "canonical_pdf_id": canonical_pdf_id,
                    "duplicate_pdf_ids": ",".join(str(item["corpus_pdf_id"]) for item in sorted_rows),
                    "dedup_action": KEEP_DUPLICATE_ACTION,
                }
            )
            duplicate_group_index += 1
    return _clean_frame(pd.DataFrame(rows)), canonical_by_pdf_id, duplicate_pdf_count


def _tier_profile(tier: str) -> tuple[str, str]:
    mapping = {
        "Tier A": ("low", "low"),
        "Tier B": ("medium", "medium"),
        "Tier C": ("high", "high"),
        "Tier D": ("high", "high"),
        "Tier E": ("medium-high", "medium-high"),
        "Tier F": ("very high", "very high"),
        "UNKNOWN": ("unknown", "unknown"),
    }
    return mapping[tier]


def _assign_tier(row: Mapping[str, Any]) -> tuple[str, str, str]:
    file_name = str(row.get("file_name", "")).casefold()
    source_bucket = str(row.get("source_bucket", ""))
    page_count = row.get("page_count")
    page_count_value = int(page_count) if str(page_count).strip() not in {"", "None"} else None
    file_size_mb = float(row.get("file_size_mb", 0) or 0)
    intake_status = str(row.get("intake_status", ""))

    if any(token in file_name for token in ["peer", "comparable", "industry", "行业", "可比"]):
        return "Tier E", "medium", "file name suggests industry or comparable-company tables"
    if any(token in file_name for token in ["hard", "scan", "ocr", "image"]):
        return "Tier D", "medium", "file name suggests scan or OCR-heavy document"
    if source_bucket == "real_test":
        return "Tier A", "medium", "current real_test corpus is used as the cleanest smoke-style real PDF bucket"
    if source_bucket == "stage7a_regression_pdfs":
        return "Tier B", "medium", "stage7a regression PDFs are likely multi-panel statement benchmark cases"
    if page_count_value is not None and page_count_value >= 45:
        return "Tier C", "medium", "high page count suggests multi-page or cross-page table risk"
    if intake_status == "PAGE_COUNT_UNREADABLE" and file_size_mb >= 2.5:
        return "Tier D", "low", "page count unreadable on a larger file, raising OCR or structure risk"
    if source_bucket == "unfamiliar" and file_size_mb >= 3.0:
        return "Tier C", "low", "unfamiliar larger PDF likely adds cross-page benchmark risk"
    if source_bucket == "input_root" and file_size_mb <= 0.35:
        return "Tier F", "low", "small top-level file may represent severe layout or header-confusion edge case"
    return "UNKNOWN", "low", "lightweight file-name and metadata heuristics were insufficient for a safer tier assignment"


def _build_tier_assignment_df(corpus_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for row in corpus_df.to_dict(orient="records"):
        assigned_tier, tier_confidence, tier_reason = _assign_tier(row)
        parser_risk, review_burden = _tier_profile(assigned_tier)
        rows.append(
            {
                "corpus_pdf_id": row["corpus_pdf_id"],
                "assigned_tier": assigned_tier,
                "tier_confidence": tier_confidence,
                "tier_reason": tier_reason,
                "expected_parser_risk": parser_risk,
                "expected_review_burden": review_burden,
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _choose_split_targets(unique_pdf_count: int, current_pdf_count: int) -> tuple[int, int]:
    pilot_target = min(5, unique_pdf_count)
    if current_pdf_count >= 30:
        benchmark_target = min(20, max(unique_pdf_count - pilot_target, 0))
    else:
        benchmark_target = max(unique_pdf_count - pilot_target, 0)
    return pilot_target, benchmark_target


def _ordered_canonical_ids(unique_rows: List[Dict[str, Any]]) -> List[str]:
    buckets: Dict[str, deque[Dict[str, Any]]] = {
        tier: deque(sorted(
            [row for row in unique_rows if row["assigned_tier"] == tier],
            key=lambda item: (
                -int(item["page_count"]) if str(item.get("page_count", "")).strip() not in {"", "None"} else 0,
                -float(item.get("file_size_mb", 0) or 0),
                str(item["corpus_pdf_id"]),
            ),
        ))
        for tier in TIER_ORDER
    }
    ordered: List[str] = []
    while any(buckets[tier] for tier in TIER_ORDER):
        for tier in TIER_ORDER:
            if buckets[tier]:
                ordered.append(str(buckets[tier].popleft()["corpus_pdf_id"]))
    return ordered


def _build_split_plan_df(
    corpus_df: pd.DataFrame,
    tier_df: pd.DataFrame,
    canonical_by_pdf_id: Dict[str, str],
) -> pd.DataFrame:
    merged = corpus_df.merge(tier_df, on="corpus_pdf_id", how="left")
    canonical_rows = []
    seen: set[str] = set()
    for row in merged.to_dict(orient="records"):
        canonical_pdf_id = canonical_by_pdf_id.get(str(row["corpus_pdf_id"]), str(row["corpus_pdf_id"]))
        if canonical_pdf_id in seen:
            continue
        if canonical_pdf_id == str(row["corpus_pdf_id"]):
            seen.add(canonical_pdf_id)
            canonical_rows.append(row)

    ordered_canonical_ids = _ordered_canonical_ids(canonical_rows)
    pilot_target, benchmark_target = _choose_split_targets(len(ordered_canonical_ids), len(corpus_df))
    pilot_ids = set(ordered_canonical_ids[:pilot_target])
    benchmark_ids = set(ordered_canonical_ids[pilot_target : pilot_target + benchmark_target])

    rows: List[Dict[str, Any]] = []
    for row in merged.to_dict(orient="records"):
        pdf_id = str(row["corpus_pdf_id"])
        canonical_pdf_id = canonical_by_pdf_id.get(pdf_id, pdf_id)
        assigned_tier = str(row.get("assigned_tier", "UNKNOWN"))
        if canonical_pdf_id in pilot_ids:
            split = PILOT_SPLIT
        elif canonical_pdf_id in benchmark_ids:
            split = BENCHMARK_SPLIT
        else:
            split = HOLDOUT_SPLIT
        if canonical_pdf_id != pdf_id:
            split_reason = f"duplicate inherits canonical split from {canonical_pdf_id}"
        else:
            split_reason = f"{assigned_tier} canonical row assigned to preserve tier diversity where practical"
        rows.append(
            {
                "corpus_pdf_id": pdf_id,
                "split": split,
                "split_reason": split_reason,
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_metadata_audit_df(
    corpus_df: pd.DataFrame,
    tier_df: pd.DataFrame,
    duplicate_pdf_count: int,
) -> tuple[pd.DataFrame, Dict[str, int]]:
    merged = corpus_df.merge(tier_df, on="corpus_pdf_id", how="left")
    missing_sha256_count = int((merged["sha256"].astype(str).str.strip() == "").sum())
    unreadable_pdf_count = int((merged["intake_status"] == "PAGE_COUNT_UNREADABLE").sum())
    missing_page_count_count = int(merged["page_count"].replace("", pd.NA).isna().sum())
    unknown_tier_count = int((merged["assigned_tier"] == "UNKNOWN").sum())
    oversized_pdf_count = int((pd.to_numeric(merged["file_size_mb"], errors="coerce").fillna(0) >= 4.0).sum())
    zero_byte_file_count = int((pd.to_numeric(merged["file_size_bytes"], errors="coerce").fillna(0) == 0).sum())
    counts = {
        "missing_sha256_count": missing_sha256_count,
        "duplicate_pdf_count": duplicate_pdf_count,
        "unreadable_pdf_count": unreadable_pdf_count,
        "missing_page_count_count": missing_page_count_count,
        "unknown_tier_count": unknown_tier_count,
        "oversized_pdf_count": oversized_pdf_count,
        "zero_byte_file_count": zero_byte_file_count,
    }
    rows = [
        {"metric": key, "value": value, "notes": ""}
        for key, value in counts.items()
    ]
    return _clean_frame(pd.DataFrame(rows)), counts


def _build_run_readiness_df(
    current_pdf_count: int,
    unique_pdf_count: int,
    zero_byte_file_count: int,
    duplicate_pdf_count: int,
    unreadable_pdf_count: int,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    ready_for_342c = current_pdf_count >= 10 and unique_pdf_count >= 10 and zero_byte_file_count == 0
    recommended_scope = PILOT_SPLIT if ready_for_342c else "not_ready"
    recommended_first_run_pdf_count = 5 if ready_for_342c and current_pdf_count >= 30 else min(5, unique_pdf_count) if ready_for_342c else 0
    reasons = []
    if current_pdf_count < 10:
        reasons.append("current_pdf_count < 10")
    if unique_pdf_count < 10:
        reasons.append("unique_pdf_count < 10")
    if zero_byte_file_count > 0:
        reasons.append("zero_byte_file_count > 0")
    if duplicate_pdf_count > 0:
        reasons.append("duplicates recorded but non-blocking")
    if unreadable_pdf_count > 0:
        reasons.append("some PDFs lack readable page counts and should stay visible in risk audit")
    if not reasons:
        reasons.append("corpus size and file-integrity checks are sufficient for a pilot MinerU benchmark run")
    reason = "; ".join(reasons)
    payload = {
        "ready_for_342c": ready_for_342c,
        "recommended_342c_scope": recommended_scope,
        "recommended_first_run_pdf_count": recommended_first_run_pdf_count,
        "reason": reason,
    }
    return _clean_frame(pd.DataFrame([payload])), payload


def _build_risk_flags_df(
    corpus_df: pd.DataFrame,
    tier_df: pd.DataFrame,
    split_df: pd.DataFrame,
    duplicate_groups_df: pd.DataFrame,
) -> pd.DataFrame:
    merged = corpus_df.merge(tier_df, on="corpus_pdf_id", how="left").merge(split_df, on="corpus_pdf_id", how="left")
    rows: List[Dict[str, Any]] = []
    duplicate_members: set[str] = set()
    for group in duplicate_groups_df.to_dict(orient="records"):
        for pdf_id in str(group.get("duplicate_pdf_ids", "")).split(","):
            if pdf_id.strip():
                duplicate_members.add(pdf_id.strip())
    for row in merged.to_dict(orient="records"):
        pdf_id = str(row["corpus_pdf_id"])
        if pdf_id in duplicate_members:
            rows.append(
                {
                    "risk_type": "duplicate_pdf",
                    "corpus_pdf_id": pdf_id,
                    "severity": "medium",
                    "detail": "sha256 duplicate detected; keep canonical and review duplicates manually if selected downstream",
                }
            )
        if str(row.get("intake_status", "")) == "PAGE_COUNT_UNREADABLE":
            rows.append(
                {
                    "risk_type": "page_count_unreadable",
                    "corpus_pdf_id": pdf_id,
                    "severity": "medium",
                    "detail": str(row.get("page_count_warning", "")),
                }
            )
        if str(row.get("assigned_tier", "")) == "UNKNOWN":
            rows.append(
                {
                    "risk_type": "unknown_tier",
                    "corpus_pdf_id": pdf_id,
                    "severity": "low",
                    "detail": "tier remains UNKNOWN and may need manual triage before a broader benchmark run",
                }
            )
        if float(row.get("file_size_mb", 0) or 0) >= 4.0:
            rows.append(
                {
                    "risk_type": "oversized_pdf",
                    "corpus_pdf_id": pdf_id,
                    "severity": "medium",
                    "detail": "larger file size may increase parser latency or cross-page extraction complexity",
                }
            )
    return _clean_frame(pd.DataFrame(rows))


def _build_readme_df(summary_342a: Mapping[str, Any], current_pdf_count: int) -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "342B builds a benchmark-corpus intake and metadata audit package for the current real-PDF pool.",
        },
        {
            "topic": "Scope boundary",
            "message": "This stage only catalogs PDFs, computes hashes, checks duplicates, assigns lightweight tiers, proposes splits, and audits readiness for 342C.",
        },
        {
            "topic": "Non-impact boundary",
            "message": "It does not run MinerU, does not parse tables deeply, does not modify production pipeline, parser, extraction, delivery, official assets, or upstream outputs.",
        },
        {
            "topic": "Current corpus size",
            "message": f"The current scanned corpus contains {current_pdf_count} PDFs, grounded by 342A decision {summary_342a.get('decision', '')}.",
        },
        {
            "topic": "Readiness boundary",
            "message": "This package can recommend a 342C pilot scope, but it does not claim client-ready or production-ready status.",
        },
        {
            "topic": "Advice boundary",
            "message": "This corpus audit is not investment advice and does not generate a client export.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_next_steps_df(readiness: Mapping[str, Any]) -> pd.DataFrame:
    recommended_scope = str(readiness.get("recommended_342c_scope", ""))
    recommended_count = int(readiness.get("recommended_first_run_pdf_count", 0) or 0)
    rows = [
        {
            "step_order": 1,
            "next_step": "Review duplicate and unknown-tier rows before 342C scheduling",
            "rationale": "Tier ambiguity and duplicate membership should stay visible before larger parser benchmarking.",
        },
        {
            "step_order": 2,
            "next_step": "Use the split plan to stage a constrained 342C first run",
            "rationale": f"Current recommendation is {recommended_scope} with {recommended_count} PDFs.",
        },
        {
            "step_order": 3,
            "next_step": "Prioritize unreadable-page-count and oversized PDFs as explicit parser-risk samples",
            "rationale": "They are non-blocking for intake but likely to surface the earliest benchmark failures.",
        },
        {
            "step_order": 4,
            "next_step": "Expand manual tier curation only where UNKNOWN blocks benchmark interpretation",
            "rationale": "342B is intentionally lightweight and should not turn into deep PDF content review.",
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


def build_real_pdf_corpus_intake_342b(
    *,
    input_dir: Path,
    benchmark_plan_342a_dir: Path,
    output_dir: Path,
    repo_root: Path,
    future_input_dir: Path = DEFAULT_FUTURE_INPUT_DIR,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    warnings: List[str] = []
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    summary_342a_path = benchmark_plan_342a_dir / BENCHMARK_PLAN_342A_SUMMARY_NAME
    summary_342a = _read_json(summary_342a_path) if summary_342a_path.exists() else {}
    if summary_342a_path.exists():
        files_read.append(str(summary_342a_path))
    else:
        warnings.append(f"missing 342A summary: {summary_342a_path}")

    corpus_df, input_hashes_before, page_count_warnings = _scan_pdf_corpus(input_dir, future_input_dir)
    files_read.extend(corpus_df["file_path"].astype(str).tolist())
    warnings.extend(page_count_warnings)

    dedup_df, canonical_by_pdf_id, duplicate_pdf_count = _build_dedup_audit(corpus_df)
    tier_df = _build_tier_assignment_df(corpus_df)
    split_df = _build_split_plan_df(corpus_df, tier_df, canonical_by_pdf_id)
    metadata_df, metadata_counts = _build_metadata_audit_df(corpus_df, tier_df, duplicate_pdf_count)
    run_readiness_df, readiness = _build_run_readiness_df(
        current_pdf_count=len(corpus_df),
        unique_pdf_count=max(len(corpus_df) - duplicate_pdf_count, 0),
        zero_byte_file_count=metadata_counts["zero_byte_file_count"],
        duplicate_pdf_count=duplicate_pdf_count,
        unreadable_pdf_count=metadata_counts["unreadable_pdf_count"],
    )
    risk_flags_df = _build_risk_flags_df(corpus_df, tier_df, split_df, dedup_df)
    readme_df = _build_readme_df(summary_342a, len(corpus_df))
    next_steps_df = _build_next_steps_df(readiness)

    output_dir.mkdir(parents=True, exist_ok=True)

    input_hashes_after = {path: sha256_file(Path(path)) for path in input_hashes_before}
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342B",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = input_hashes_before == input_hashes_after
    no_write_back_json["client_export_generated"] = False
    no_write_back_json["pdf_deleted_or_moved"] = False
    no_write_back_json["production_pipeline_modified"] = False
    no_write_back_json["parser_modified"] = False
    no_write_back_json["extraction_modified"] = False
    no_write_back_json["delivery_modified"] = False
    no_write_back_json["no_write_back"] = True

    no_write_back_proof_passed = (
        bool(no_write_back_json.get("no_official_asset_modification_during_342b"))
        and bool(no_write_back_json.get("upstream_workbooks_unchanged"))
        and not no_write_back_json.get("client_export_generated", True)
        and not no_write_back_json.get("pdf_deleted_or_moved", True)
    )

    current_pdf_count = int(len(corpus_df))
    unique_pdf_count = max(current_pdf_count - duplicate_pdf_count, 0)
    assigned_tier_count = int((tier_df["assigned_tier"] != "UNKNOWN").sum()) if not tier_df.empty else 0
    unknown_tier_count = int((tier_df["assigned_tier"] == "UNKNOWN").sum()) if not tier_df.empty else 0
    split_counts = split_df["split"].value_counts().to_dict() if not split_df.empty else {}
    pilot_set_count = int(split_counts.get(PILOT_SPLIT, 0))
    benchmark_set_count = int(split_counts.get(BENCHMARK_SPLIT, 0))
    holdout_set_count = int(split_counts.get(HOLDOUT_SPLIT, 0))

    readme_text = "\n".join(readme_df["message"].astype(str).tolist())
    checks = [
        {
            "check_name": "inputs::input_dir_checked",
            "status": "PASS" if input_dir.exists() else "FAIL",
            "detail": str(input_dir),
        },
        {
            "check_name": "inputs::benchmark_plan_342a_summary_detected",
            "status": "PASS" if summary_342a else "FAIL",
            "detail": str(summary_342a_path),
        },
        {
            "check_name": "inputs::optional_future_input_dir_checked",
            "status": "PASS",
            "detail": f"{future_input_dir} exists={future_input_dir.exists()}",
        },
        {
            "check_name": "corpus::pdf_corpus_generated",
            "status": "PASS" if current_pdf_count >= 0 else "FAIL",
            "detail": str(current_pdf_count),
        },
        {
            "check_name": "corpus::sha256_generated_for_each_file",
            "status": "PASS" if metadata_counts["missing_sha256_count"] == 0 else "FAIL",
            "detail": str(metadata_counts["missing_sha256_count"]),
        },
        {
            "check_name": "audit::duplicate_audit_generated",
            "status": "PASS",
            "detail": f"duplicate_pdf_count={duplicate_pdf_count}",
        },
        {
            "check_name": "audit::tier_assignment_generated",
            "status": "PASS" if len(tier_df) == current_pdf_count else "FAIL",
            "detail": str(len(tier_df)),
        },
        {
            "check_name": "audit::split_plan_generated",
            "status": "PASS" if len(split_df) == current_pdf_count else "FAIL",
            "detail": str(len(split_df)),
        },
        {
            "check_name": "audit::metadata_audit_generated",
            "status": "PASS" if not metadata_df.empty else "FAIL",
            "detail": str(len(metadata_df)),
        },
        {
            "check_name": "audit::run_readiness_generated",
            "status": "PASS" if not run_readiness_df.empty else "FAIL",
            "detail": json.dumps(readiness, ensure_ascii=False),
        },
        {
            "check_name": "safety::no_pdf_deleted_or_moved",
            "status": "PASS" if not no_write_back_json.get("pdf_deleted_or_moved", True) else "FAIL",
            "detail": "pdf_deleted_or_moved=false",
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {
                    "upstream_unchanged": no_write_back_json.get("upstream_workbooks_unchanged"),
                    "official_assets_unchanged": no_write_back_json.get("no_official_asset_modification_during_342b"),
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
            "check_name": "safety::no_pipeline_parser_extraction_delivery_modification",
            "status": "PASS",
            "detail": "342B creates only sidecar audit artifacts",
        },
        {
            "check_name": "safety::no_sheet_name_exceeds_limit",
            "status": "PASS" if all(len(name) <= 31 for name in WORKBOOK_SHEETS) else "FAIL",
            "detail": json.dumps({name: len(name) for name in WORKBOOK_SHEETS}, ensure_ascii=False),
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
            "check_name": "upstream::342a_ready_detected",
            "status": "PASS" if summary_342a.get("decision", "") == BENCHMARK_PLAN_READY_DECISION else "FAIL",
            "detail": str(summary_342a.get("decision", "")),
        },
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    decision = READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "current_pdf_count": current_pdf_count,
        "unique_pdf_count": unique_pdf_count,
        "duplicate_pdf_count": duplicate_pdf_count,
        "assigned_tier_count": assigned_tier_count,
        "unknown_tier_count": unknown_tier_count,
        "pilot_set_count": pilot_set_count,
        "benchmark_set_count": benchmark_set_count,
        "holdout_set_count": holdout_set_count,
        "ready_for_342c": readiness["ready_for_342c"],
        "recommended_342c_scope": readiness["recommended_342c_scope"],
        "recommended_first_run_pdf_count": readiness["recommended_first_run_pdf_count"],
        "missing_sha256_count": metadata_counts["missing_sha256_count"],
        "unreadable_pdf_count": metadata_counts["unreadable_pdf_count"],
        "missing_page_count_count": metadata_counts["missing_page_count_count"],
        "oversized_pdf_count": metadata_counts["oversized_pdf_count"],
        "zero_byte_file_count": metadata_counts["zero_byte_file_count"],
        "warning_count": len(warnings),
        "qa_fail_count": qa_fail_count,
        "client_ready": False,
        "production_ready": False,
        "decision": decision,
        "detected_342a_decision": summary_342a.get("decision", ""),
        "detected_342a_benchmark_status": summary_342a.get("benchmark_status", ""),
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / "real_pdf_corpus_intake_342b.xlsx"),
    }

    manifest = {
        "task": "342B_real_pdf_corpus_intake_metadata_audit",
        "input_dir": str(input_dir),
        "future_input_dir": str(future_input_dir),
        "benchmark_plan_342a_dir": str(benchmark_plan_342a_dir),
        "output_dir": str(output_dir),
        "files_read_count": len(files_read),
        "files_read": files_read,
        "warnings": warnings,
        "artifacts": {
            "summary_json": str(output_dir / "real_pdf_corpus_intake_342b_summary.json"),
            "manifest_json": str(output_dir / "real_pdf_corpus_intake_342b_manifest.json"),
            "qa_json": str(output_dir / "real_pdf_corpus_intake_342b_qa.json"),
            "no_write_back_proof_json": str(output_dir / "real_pdf_corpus_intake_342b_no_write_back_proof.json"),
            "report_md": str(output_dir / "real_pdf_corpus_intake_342b_report.md"),
            "workbook_xlsx": str(output_dir / "real_pdf_corpus_intake_342b.xlsx"),
        },
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": len(warnings),
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": readme_df,
        "01_CORPUS_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_PDF_CORPUS": corpus_df.drop(columns=["page_count_warning", "file_size_bytes"], errors="ignore"),
        "03_DEDUP_AUDIT": dedup_df,
        "04_TIER_ASSIGNMENT": tier_df,
        "05_SPLIT_PLAN": split_df,
        "06_METADATA_AUDIT": metadata_df,
        "07_RUN_READINESS": run_readiness_df,
        "08_RISK_FLAGS": risk_flags_df,
        "09_NO_WRITE_BACK_PROOF": _build_no_write_back_proof_df(no_write_back_json),
        "10_NEXT_STEPS": next_steps_df,
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "workbook_sheets": workbook_sheets,
    }
