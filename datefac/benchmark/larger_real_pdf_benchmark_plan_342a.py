from __future__ import annotations

import json
import subprocess
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


READY_DECISION = "LARGER_REAL_PDF_BENCHMARK_PLAN_342A_READY"
NOT_READY_DECISION = "LARGER_REAL_PDF_BENCHMARK_PLAN_342A_NOT_READY"

BENCHMARK_STATUS_NEEDS_MORE = "NEEDS_MORE_PDFS"
BENCHMARK_STATUS_READY_SMALL_SCALE = "READY_FOR_SMALL_SCALE_BENCHMARK"

DEFAULT_INPUT_DIR = Path(r"D:\_datefac\input")
DEFAULT_FUTURE_BENCHMARK_DIR = Path(r"D:\_datefac\input\real_pdf_benchmark_342a")
DEFAULT_MILESTONE_341A_DIR = Path(r"D:\_datefac\output\human_reviewed_client_preview_milestone_341a")
DEFAULT_CLIENT_PREVIEW_AUDIT_340G_DIR = Path(r"D:\_datefac\output\client_preview_export_audit_340g")
DEFAULT_CLIENT_PREVIEW_340F_DIR = Path(r"D:\_datefac\output\client_preview_after_human_review_340f")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\larger_real_pdf_benchmark_plan_342a")

TARGET_PDF_COUNT_MIN = 10
TARGET_PDF_COUNT_RECOMMENDED = 30
TARGET_PDF_COUNT_STRETCH = 50

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
    "01_BENCHMARK_SUMMARY",
    "02_PDF_INVENTORY",
    "03_SAMPLE_TIERS",
    "04_TARGET_METRICS",
    "05_RUN_PLAN",
    "06_REVIEW_BUDGET",
    "07_SUCCESS_CRITERIA",
    "08_RISK_REGISTER",
    "09_NEXT_STEPS",
    "10_NO_WRITE_BACK_PROOF",
]

SUMMARY_FILE_SPECS = [
    {
        "name": "341A",
        "path_name": "human_reviewed_client_preview_milestone_341a_summary.json",
        "decision_key": "decision",
        "required_decision": "HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_READY",
    },
    {
        "name": "340G",
        "path_name": "client_preview_export_audit_340g_summary.json",
        "decision_key": "decision",
        "required_decision": "CLIENT_PREVIEW_EXPORT_AUDIT_340G_READY",
    },
    {
        "name": "340F",
        "path_name": "client_preview_after_human_review_340f_summary.json",
        "decision_key": "decision",
        "required_decision": "CLIENT_PREVIEW_AFTER_HUMAN_REVIEW_340F_READY",
    },
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
    seen: set[str] = set()
    pdfs: List[Path] = []
    for root in [input_dir, future_dir]:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.pdf")):
            resolved = str(path.resolve())
            if resolved not in seen:
                seen.add(resolved)
                pdfs.append(path)
    return pdfs


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


def _planned_benchmark_status(source_bucket: str, detected_in_current_sample: bool) -> str:
    if detected_in_current_sample:
        return "CURRENT_SAMPLE_BASELINE"
    if source_bucket == "real_pdf_benchmark_342a":
        return "FUTURE_BENCHMARK_POOL"
    return "DISCOVERY_CANDIDATE"


def _scan_pdf_inventory(input_dir: Path, future_dir: Path) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for idx, path in enumerate(_all_pdf_files(input_dir, future_dir), start=1):
        stat = path.stat()
        detected_in_current_sample = "real_test" in {part.casefold() for part in path.parts}
        source_bucket = _source_bucket(path, input_dir, future_dir)
        rows.append(
            {
                "pdf_id": f"342a_pdf_{idx:03d}",
                "file_name": path.name,
                "file_path": str(path),
                "file_size_mb": round(stat.st_size / (1024 * 1024), 3),
                "modified_time": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "document_hint": path.stem,
                "source_bucket": source_bucket,
                "detected_in_current_sample": detected_in_current_sample,
                "planned_benchmark_status": _planned_benchmark_status(source_bucket, detected_in_current_sample),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _benchmark_status(current_pdf_count: int) -> str:
    return BENCHMARK_STATUS_READY_SMALL_SCALE if current_pdf_count >= TARGET_PDF_COUNT_MIN else BENCHMARK_STATUS_NEEDS_MORE


def _load_optional_summary(directory: Path, summary_file_name: str) -> tuple[Dict[str, Any], str | None]:
    summary_path = directory / summary_file_name
    if summary_path.exists():
        return _read_json(summary_path), None
    return {}, f"missing summary: {summary_path}"


def _build_readme_df(current_pdf_count: int, benchmark_status: str) -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "342A creates a larger real-PDF benchmark planning package without running a new large-scale parsing benchmark.",
        },
        {
            "topic": "Scope boundary",
            "message": "This stage is planning, inventory, runbook, and budgeting only. It does not modify production pipeline, parser, extraction, delivery, or official assets.",
        },
        {
            "topic": "Current benchmark state",
            "message": f"The current inventory includes {current_pdf_count} PDFs and the benchmark status is {benchmark_status}.",
        },
        {
            "topic": "Readiness boundary",
            "message": "The project remains demo-ready and client-preview-ready only. It is not client-ready for formal delivery and not production-ready.",
        },
        {
            "topic": "Advice boundary",
            "message": "This benchmark plan is not investment advice and does not generate a client export.",
        },
        {
            "topic": "Benchmark limitation",
            "message": "341A is still a small-sample milestone. A larger benchmark is needed before making stronger stability claims.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_sample_tiers_df() -> pd.DataFrame:
    rows = [
        {
            "tier_name": "Tier A",
            "description": "clean financial forecast table",
            "expected_parser_risk": "low",
            "expected_review_burden": "low",
            "recommended_pdf_count": 6,
            "main_failure_modes": "minor unit normalization and label alias drift",
        },
        {
            "tier_name": "Tier B",
            "description": "multi-panel financial statements",
            "expected_parser_risk": "medium",
            "expected_review_burden": "medium",
            "recommended_pdf_count": 6,
            "main_failure_modes": "panel boundary confusion and cross-table row attribution",
        },
        {
            "tier_name": "Tier C",
            "description": "multi-page tables / cross-page tables",
            "expected_parser_risk": "high",
            "expected_review_burden": "high",
            "recommended_pdf_count": 5,
            "main_failure_modes": "page breaks, repeated headers, missing carry-over rows",
        },
        {
            "tier_name": "Tier D",
            "description": "scanned or OCR-heavy PDF",
            "expected_parser_risk": "high",
            "expected_review_burden": "high",
            "recommended_pdf_count": 4,
            "main_failure_modes": "OCR noise, broken numeric spans, and lost unit symbols",
        },
        {
            "tier_name": "Tier E",
            "description": "mixed industry/comparable-company tables",
            "expected_parser_risk": "medium",
            "expected_review_burden": "medium-high",
            "recommended_pdf_count": 5,
            "main_failure_modes": "peer-table rows confused with core issuer metrics",
        },
        {
            "tier_name": "Tier F",
            "description": "severe layout / table-header confusion",
            "expected_parser_risk": "very high",
            "expected_review_burden": "very high",
            "recommended_pdf_count": 4,
            "main_failure_modes": "header repair failure, year misalignment, and merged-cell ambiguity",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_target_metrics_df() -> pd.DataFrame:
    rows = [
        {
            "metric": "revenue",
            "display_name_zh": "营业收入",
            "expected_unit": "amount unit from source, never %",
            "high_risk_unit_confusion": "percent sign or missing amount scale",
            "benchmark_priority": "P0",
            "validation_notes": "must preserve source trace and amount unit context",
        },
        {
            "metric": "net_profit",
            "display_name_zh": "归母净利润",
            "expected_unit": "amount unit from source, never %",
            "high_risk_unit_confusion": "percent sign,扣非 alias, or wrong scale",
            "benchmark_priority": "P0",
            "validation_notes": "must exclude yoy-only rows and non-parent-profit aliases",
        },
        {
            "metric": "EPS",
            "display_name_zh": "每股收益",
            "expected_unit": "元",
            "high_risk_unit_confusion": "元 vs % vs missing unit",
            "benchmark_priority": "P0",
            "validation_notes": "unit must remain 元 after normalization",
        },
        {
            "metric": "PE",
            "display_name_zh": "市盈率",
            "expected_unit": "倍",
            "high_risk_unit_confusion": "倍 vs % or unlabeled valuation rows",
            "benchmark_priority": "P0",
            "validation_notes": "must not be treated as amount or percent metric",
        },
        {
            "metric": "PB",
            "display_name_zh": "市净率",
            "expected_unit": "倍",
            "high_risk_unit_confusion": "倍 vs unlabeled comparable valuation",
            "benchmark_priority": "P1",
            "validation_notes": "peer-comparison tables need stronger routing guards",
        },
        {
            "metric": "ROE",
            "display_name_zh": "净资产收益率",
            "expected_unit": "%",
            "high_risk_unit_confusion": "ratio vs amount confusion",
            "benchmark_priority": "P1",
            "validation_notes": "must keep ratio semantics and year alignment",
        },
        {
            "metric": "revenue_yoy",
            "display_name_zh": "营业收入同比",
            "expected_unit": "%",
            "high_risk_unit_confusion": "mistakenly mapped into revenue amount",
            "benchmark_priority": "P1",
            "validation_notes": "must stay separate from revenue amount rows",
        },
        {
            "metric": "net_profit_yoy",
            "display_name_zh": "归母净利润同比",
            "expected_unit": "%",
            "high_risk_unit_confusion": "mistakenly mapped into net profit amount",
            "benchmark_priority": "P1",
            "validation_notes": "must stay separate from net profit amount rows",
        },
        {
            "metric": "gross_margin",
            "display_name_zh": "毛利率",
            "expected_unit": "%",
            "high_risk_unit_confusion": "ratio vs absolute margin wording",
            "benchmark_priority": "P2",
            "validation_notes": "watch for table header carry-over and OCR-lost percent symbols",
        },
        {
            "metric": "net_margin",
            "display_name_zh": "净利率",
            "expected_unit": "%",
            "high_risk_unit_confusion": "ratio vs profit amount confusion",
            "benchmark_priority": "P2",
            "validation_notes": "validate ratio semantics and source trace coverage",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_run_plan_df() -> pd.DataFrame:
    rows = [
        {
            "stage_id": "342B",
            "stage_name": "Real PDF Corpus Intake And Metadata Audit",
            "goal": "Expand and normalize benchmark corpus inventory with stronger metadata coverage.",
            "input": "input PDFs and benchmark inventory manifest",
            "output": "corpus manifest and metadata audit",
            "success_criteria": "all benchmark PDFs cataloged with source bucket and metadata sanity checks",
            "should_modify_pipeline": False,
        },
        {
            "stage_id": "342C",
            "stage_name": "MinerU Batch Parse Benchmark",
            "goal": "Measure MinerU-first parsing success across the larger corpus.",
            "input": "342B corpus manifest",
            "output": "batch parse benchmark package",
            "success_criteria": "parser success rate and failure taxonomy recorded for all benchmark PDFs",
            "should_modify_pipeline": False,
        },
        {
            "stage_id": "342D",
            "stage_name": "Parser Ensemble Compare Benchmark",
            "goal": "Compare primary parser output with fallback or probe parser baselines.",
            "input": "342C parser outputs",
            "output": "parser compare benchmark",
            "success_criteria": "delta in table recovery and candidate quality quantified by tier",
            "should_modify_pipeline": False,
        },
        {
            "stage_id": "342E",
            "stage_name": "Core Metric Candidate Quality Audit",
            "goal": "Audit candidate quality for the top-priority financial metrics.",
            "input": "342C/342D parse outputs",
            "output": "core metric candidate audit",
            "success_criteria": "metric-level quality counts available for benchmark tiers and documents",
            "should_modify_pipeline": False,
        },
        {
            "stage_id": "342F",
            "stage_name": "AI Review Scaling Simulation",
            "goal": "Estimate how AI dry-run behavior scales on a broader real-PDF pool.",
            "input": "342E audited candidate set",
            "output": "AI review scaling simulation",
            "success_criteria": "hold, confirm, reject, and invalid-response ratios estimated by tier",
            "should_modify_pipeline": False,
        },
        {
            "stage_id": "342G",
            "stage_name": "Human Review Burden Estimate",
            "goal": "Quantify workbook-based human review load under larger benchmark sizes.",
            "input": "342E and 342F outputs",
            "output": "review burden estimate",
            "success_criteria": "review queue and human-minute ranges estimated for 10/30/50 PDFs",
            "should_modify_pipeline": False,
        },
        {
            "stage_id": "342H",
            "stage_name": "Client Preview Benchmark Rollup",
            "goal": "Roll benchmark evidence into a preview-safe benchmark summary without formal delivery claims.",
            "input": "342C through 342G results",
            "output": "benchmark rollup package",
            "success_criteria": "preview-safe benchmark summary with audit boundaries and no production claims",
            "should_modify_pipeline": False,
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_review_budget_df() -> pd.DataFrame:
    candidate_rows_per_pdf = 116
    review_required_rows_per_pdf = 26
    minutes_low_per_review_row = 1.5
    minutes_high_per_review_row = 4.0
    rows = []
    for pdf_count in [10, 30, 50]:
        expected_review_required_rows = int(round(pdf_count * review_required_rows_per_pdf))
        rows.append(
            {
                "pdf_count_scenario": pdf_count,
                "expected_candidate_rows": int(round(pdf_count * candidate_rows_per_pdf)),
                "expected_review_required_rows": expected_review_required_rows,
                "expected_human_minutes_low": int(round(expected_review_required_rows * minutes_low_per_review_row)),
                "expected_human_minutes_high": int(round(expected_review_required_rows * minutes_high_per_review_row)),
                "main_cost_driver": "cross-page tables, OCR noise, and unit/year ambiguity drive manual review time",
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _build_success_criteria_df() -> pd.DataFrame:
    rows = [
        {
            "criterion": "parser_success_rate",
            "target": ">= 0.90 on Tier A/B and >= 0.75 overall before claiming small-scale benchmark stability",
            "why_it_matters": "a larger corpus is only useful if parser failures are visible and bounded",
        },
        {
            "criterion": "core_metric_candidate_count",
            "target": "sufficient candidate density for the 10 target metrics across all major tiers",
            "why_it_matters": "benchmark coverage is not credible if high-priority metrics are absent",
        },
        {
            "criterion": "trusted_or_confirmed_ratio",
            "target": "track by tier and compare against current small-sample milestone before expansion claims",
            "why_it_matters": "the larger benchmark should show whether confirmed preview quality degrades materially",
        },
        {
            "criterion": "review_required_ratio",
            "target": "keep visible by tier and document type rather than forcing one global threshold",
            "why_it_matters": "review burden is a first-class scaling bottleneck",
        },
        {
            "criterion": "unit_issue_rate",
            "target": "trend downward after deterministic repair and preview audit stages",
            "why_it_matters": "unit confusion is one of the most dangerous financial preview errors",
        },
        {
            "criterion": "duplicate_issue_rate",
            "target": "remain near zero in preview-safe rollups after reviewed strictness and audit layers",
            "why_it_matters": "duplicate metrics distort client preview trust",
        },
        {
            "criterion": "source_trace_coverage",
            "target": "approach complete coverage for all promoted client-preview rows",
            "why_it_matters": "traceability is required for demo-safe and review-safe claims",
        },
        {
            "criterion": "client_preview_audit_pass_rate",
            "target": "only claim preview safety when audit gates pass without overclaim risk",
            "why_it_matters": "341A is a small-sample milestone, not evidence of production stability",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_risk_register_df() -> pd.DataFrame:
    rows = [
        {
            "risk_area": "parser robustness",
            "risk_description": "layout diversity may break MinerU-first parsing assumptions outside the current milestone sample",
            "impact": "high",
            "mitigation_direction": "expand benchmark tiers and capture parser failure taxonomy early",
        },
        {
            "risk_area": "OCR-heavy PDFs",
            "risk_description": "OCR noise can destroy numbers, units, and row labels before trust routing begins",
            "impact": "high",
            "mitigation_direction": "treat OCR-heavy PDFs as a dedicated benchmark tier with separate quality thresholds",
        },
        {
            "risk_area": "unit ambiguity",
            "risk_description": "amount, percent, and valuation units may collapse into the wrong normalized form",
            "impact": "high",
            "mitigation_direction": "track unit issue rate explicitly and preserve source trace for promoted rows",
        },
        {
            "risk_area": "year alignment",
            "risk_description": "forecast and actual years may shift under complex headers or cross-page carries",
            "impact": "high",
            "mitigation_direction": "keep year-alignment QA as a benchmarked gate, not an implicit assumption",
        },
        {
            "risk_area": "duplicate rows",
            "risk_description": "multi-panel and comparable-company tables can surface duplicate metric candidates",
            "impact": "medium-high",
            "mitigation_direction": "measure duplicate issue rate by tier before any broader preview rollup",
        },
        {
            "risk_area": "non-core industry tables",
            "risk_description": "peer and industry tables can pollute issuer-core metric routing",
            "impact": "medium-high",
            "mitigation_direction": "isolate Tier E coverage and validate source routing assumptions",
        },
        {
            "risk_area": "metadata confusion",
            "risk_description": "missing company, report date, or source bucket metadata weakens corpus-level auditability",
            "impact": "medium",
            "mitigation_direction": "run a dedicated metadata audit before large-scale benchmark comparisons",
        },
        {
            "risk_area": "review burden explosion",
            "risk_description": "larger corpora may produce manual-review queues that outgrow workbook-only workflows",
            "impact": "high",
            "mitigation_direction": "estimate human review minutes early and prioritize a UI review workflow",
        },
        {
            "risk_area": "client overclaim risk",
            "risk_description": "benchmark growth may tempt stronger delivery claims before stability is proven",
            "impact": "high",
            "mitigation_direction": "keep client_ready false, production_ready false, and not-investment-advice wording explicit",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_next_steps_df(current_pdf_count: int, benchmark_status: str) -> pd.DataFrame:
    rows = [
        {
            "step_order": 1,
            "next_step": "Acquire or stage more benchmark PDFs into input/real_pdf_benchmark_342a as needed",
            "rationale": f"Current inventory count is {current_pdf_count}, benchmark status is {benchmark_status}.",
        },
        {
            "step_order": 2,
            "next_step": "Run 342B corpus intake and metadata audit",
            "rationale": "Metadata completeness should be audited before parser-scale comparisons.",
        },
        {
            "step_order": 3,
            "next_step": "Run 342C MinerU batch parse benchmark",
            "rationale": "The next hard question is parser success and failure behavior on a broader corpus.",
        },
        {
            "step_order": 4,
            "next_step": "Prioritize Tier C/D/F documents early",
            "rationale": "Cross-page, OCR-heavy, and severe-layout PDFs will likely expose the biggest scaling risks first.",
        },
        {
            "step_order": 5,
            "next_step": "Use 342G review burden estimates to scope a UI review workflow",
            "rationale": "Workbook-only review will not scale gracefully if review-required ratios stay high.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_no_write_back_proof_df(no_apply_proof_json: Mapping[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for path, before_hash in no_apply_proof_json.get("upstream_input_hashes_before", {}).items():
        rows.append(
            {
                "path": path,
                "before_hash": before_hash,
                "after_hash": no_apply_proof_json.get("upstream_input_hashes_after", {}).get(path, ""),
                "unchanged": before_hash == no_apply_proof_json.get("upstream_input_hashes_after", {}).get(path, ""),
            }
        )
    for path, before_hash in no_apply_proof_json.get("official_assets_before", {}).items():
        rows.append(
            {
                "path": path,
                "before_hash": before_hash,
                "after_hash": no_apply_proof_json.get("official_assets_after", {}).get(path, ""),
                "unchanged": before_hash == no_apply_proof_json.get("official_assets_after", {}).get(path, ""),
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def build_larger_real_pdf_benchmark_plan_342a(
    *,
    input_dir: Path,
    milestone_341a_dir: Path,
    client_preview_audit_340g_dir: Path,
    client_preview_340f_dir: Path,
    output_dir: Path,
    repo_root: Path,
    future_benchmark_dir: Path = DEFAULT_FUTURE_BENCHMARK_DIR,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    files_read: List[str] = []
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    inventory_df = _scan_pdf_inventory(input_dir, future_benchmark_dir)
    current_pdf_count = int(len(inventory_df))
    benchmark_status = _benchmark_status(current_pdf_count)

    summary_341a, warning_341a = _load_optional_summary(
        milestone_341a_dir,
        "human_reviewed_client_preview_milestone_341a_summary.json",
    )
    summary_340g, warning_340g = _load_optional_summary(
        client_preview_audit_340g_dir,
        "client_preview_export_audit_340g_summary.json",
    )
    summary_340f, warning_340f = _load_optional_summary(
        client_preview_340f_dir,
        "client_preview_after_human_review_340f_summary.json",
    )
    warnings = [warning for warning in [warning_341a, warning_340g, warning_340f] if warning]

    for directory, file_name in [
        (milestone_341a_dir, "human_reviewed_client_preview_milestone_341a_summary.json"),
        (client_preview_audit_340g_dir, "client_preview_export_audit_340g_summary.json"),
        (client_preview_340f_dir, "client_preview_after_human_review_340f_summary.json"),
    ]:
        path = directory / file_name
        if path.exists():
            files_read.append(str(path))

    official_assets_after_read = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    input_hashes_before = {path: sha256_file(Path(path)) for path in files_read}

    output_dir.mkdir(parents=True, exist_ok=True)

    input_hashes_after = {path: sha256_file(Path(path)) for path in files_read}
    upstream_unchanged = input_hashes_before == input_hashes_after
    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_apply_proof_json = build_no_apply_proof(
        stage="342A",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof_json["upstream_input_hashes_before"] = input_hashes_before
    no_apply_proof_json["upstream_input_hashes_after"] = input_hashes_after
    no_apply_proof_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_apply_proof_json["client_export_generated"] = False
    no_apply_proof_json["production_pipeline_modified"] = False
    no_apply_proof_json["parser_modified"] = False
    no_apply_proof_json["extraction_modified"] = False
    no_apply_proof_json["delivery_modified"] = False
    no_apply_proof_json["no_write_back"] = True

    no_write_back_proof_passed = (
        bool(no_apply_proof_json.get("no_official_asset_modification_during_342a"))
        and upstream_unchanged
        and not no_apply_proof_json.get("client_export_generated", True)
    )

    demo_ready = bool(summary_341a.get("demo_ready", True))
    client_preview_ready = bool(summary_341a.get("client_preview_ready", True))
    client_ready = False
    production_ready = False

    readme_df = _build_readme_df(current_pdf_count, benchmark_status)
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())
    sample_tiers_df = _build_sample_tiers_df()
    target_metrics_df = _build_target_metrics_df()
    run_plan_df = _build_run_plan_df()
    review_budget_df = _build_review_budget_df()
    success_criteria_df = _build_success_criteria_df()
    risk_register_df = _build_risk_register_df()
    next_steps_df = _build_next_steps_df(current_pdf_count, benchmark_status)

    checks = [
        {
            "check_name": "inputs::input_dir_checked",
            "status": "PASS" if input_dir.exists() else "FAIL",
            "detail": str(input_dir),
        },
        {
            "check_name": "inputs::future_benchmark_dir_checked",
            "status": "PASS",
            "detail": f"{future_benchmark_dir} exists={future_benchmark_dir.exists()}",
        },
        {
            "check_name": "inventory::pdf_inventory_generated",
            "status": "PASS" if current_pdf_count >= 0 else "FAIL",
            "detail": str(current_pdf_count),
        },
        {
            "check_name": "summary::341a_detected_if_available",
            "status": "PASS" if summary_341a else "WARN",
            "detail": warning_341a or summary_341a.get("decision", ""),
        },
        {
            "check_name": "summary::340g_detected_if_available",
            "status": "PASS" if summary_340g else "WARN",
            "detail": warning_340g or summary_340g.get("decision", ""),
        },
        {
            "check_name": "summary::340f_detected_if_available",
            "status": "PASS" if summary_340f else "WARN",
            "detail": warning_340f or summary_340f.get("decision", ""),
        },
        {
            "check_name": "planning::sample_tiers_generated",
            "status": "PASS" if len(sample_tiers_df) == 6 else "FAIL",
            "detail": str(len(sample_tiers_df)),
        },
        {
            "check_name": "planning::target_metrics_generated",
            "status": "PASS" if len(target_metrics_df) == 10 else "FAIL",
            "detail": str(len(target_metrics_df)),
        },
        {
            "check_name": "planning::run_plan_generated",
            "status": "PASS" if len(run_plan_df) == 7 else "FAIL",
            "detail": str(len(run_plan_df)),
        },
        {
            "check_name": "planning::review_budget_generated",
            "status": "PASS" if len(review_budget_df) == 3 else "FAIL",
            "detail": str(len(review_budget_df)),
        },
        {
            "check_name": "planning::success_criteria_generated",
            "status": "PASS" if len(success_criteria_df) >= 8 else "FAIL",
            "detail": str(len(success_criteria_df)),
        },
        {
            "check_name": "planning::risk_register_generated",
            "status": "PASS" if len(risk_register_df) >= 9 else "FAIL",
            "detail": str(len(risk_register_df)),
        },
        {
            "check_name": "safety::no_write_back_proof_generated",
            "status": "PASS" if no_write_back_proof_passed else "FAIL",
            "detail": json.dumps(
                {
                    "upstream_unchanged": upstream_unchanged,
                    "official_assets_unchanged": bool(no_apply_proof_json.get("no_official_asset_modification_during_342a")),
                    "client_export_generated": no_apply_proof_json.get("client_export_generated"),
                },
                ensure_ascii=False,
            ),
        },
        {
            "check_name": "safety::no_sheet_name_exceeds_limit",
            "status": "PASS" if all(len(name) <= 31 for name in WORKBOOK_SHEETS) else "FAIL",
            "detail": json.dumps({name: len(name) for name in WORKBOOK_SHEETS}, ensure_ascii=False),
        },
        {
            "check_name": "claims::client_ready_false",
            "status": "PASS" if not client_ready else "FAIL",
            "detail": str(client_ready).lower(),
        },
        {
            "check_name": "claims::production_ready_false",
            "status": "PASS" if not production_ready else "FAIL",
            "detail": str(production_ready).lower(),
        },
        {
            "check_name": "claims::no_investment_advice_claim",
            "status": "PASS" if not _contains_forbidden_claim(readme_text, ["investment advice"]) else "FAIL",
            "detail": "README text checked",
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
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    warning_count = sum(1 for check in checks if check["status"] == "WARN")
    decision = READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "current_pdf_count": current_pdf_count,
        "target_pdf_count_min": TARGET_PDF_COUNT_MIN,
        "target_pdf_count_recommended": TARGET_PDF_COUNT_RECOMMENDED,
        "target_pdf_count_stretch": TARGET_PDF_COUNT_STRETCH,
        "benchmark_status": benchmark_status,
        "demo_ready": demo_ready,
        "client_preview_ready": client_preview_ready,
        "client_ready": client_ready,
        "production_ready": production_ready,
        "warning_count": warning_count,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "detected_341a_decision": summary_341a.get("decision", ""),
        "detected_340g_decision": summary_340g.get("decision", ""),
        "detected_340f_decision": summary_340f.get("decision", ""),
        "detected_340g_audit_passed": summary_340g.get("client_preview_audit_passed", ""),
        "detected_340f_client_preview_core_metric_count": summary_340f.get("client_preview_core_metric_count", ""),
        "detected_340g_duplicate_issue_count": summary_340g.get("duplicate_issue_count", ""),
        "detected_340g_unit_issue_count": summary_340g.get("unit_issue_count", ""),
        "detected_340g_missing_source_trace_count": summary_340g.get("missing_source_trace_count", ""),
        "detected_340g_unsafe_claim_count": summary_340g.get("unsafe_claim_count", ""),
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "output_workbook_path": str(output_dir / "larger_real_pdf_benchmark_plan_342a.xlsx"),
    }

    manifest = {
        "task": "342A_larger_real_pdf_benchmark_plan",
        "input_dir": str(input_dir),
        "future_benchmark_dir": str(future_benchmark_dir),
        "milestone_341a_dir": str(milestone_341a_dir),
        "client_preview_audit_340g_dir": str(client_preview_audit_340g_dir),
        "client_preview_340f_dir": str(client_preview_340f_dir),
        "output_dir": str(output_dir),
        "warnings": warnings,
        "artifacts": {
            "summary_json": str(output_dir / "larger_real_pdf_benchmark_plan_342a_summary.json"),
            "manifest_json": str(output_dir / "larger_real_pdf_benchmark_plan_342a_manifest.json"),
            "qa_json": str(output_dir / "larger_real_pdf_benchmark_plan_342a_qa.json"),
            "report_md": str(output_dir / "larger_real_pdf_benchmark_plan_342a_report.md"),
            "workbook_xlsx": str(output_dir / "larger_real_pdf_benchmark_plan_342a.xlsx"),
        },
        "files_read": files_read,
        "source_summary_detection": {
            "341A": bool(summary_341a),
            "340G": bool(summary_340g),
            "340F": bool(summary_340f),
        },
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "warning_count": warning_count,
        "checks": checks,
        "warnings": warnings,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": readme_df,
        "01_BENCHMARK_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_PDF_INVENTORY": inventory_df,
        "03_SAMPLE_TIERS": sample_tiers_df,
        "04_TARGET_METRICS": target_metrics_df,
        "05_RUN_PLAN": run_plan_df,
        "06_REVIEW_BUDGET": review_budget_df,
        "07_SUCCESS_CRITERIA": success_criteria_df,
        "08_RISK_REGISTER": risk_register_df,
        "09_NEXT_STEPS": next_steps_df,
        "10_NO_WRITE_BACK_PROOF": _build_no_write_back_proof_df(no_apply_proof_json),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_apply_proof_json,
        "workbook_sheets": workbook_sheets,
    }
