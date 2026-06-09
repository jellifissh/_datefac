from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    capture_official_asset_hashes,
)


MILESTONE_ACCEPTED_FOR_DEMO_RESEARCH_PREVIEW = "MILESTONE_ACCEPTED_FOR_DEMO_RESEARCH_PREVIEW"
MILESTONE_ACCEPTED_WITH_REVIEW_CAVEATS = "MILESTONE_ACCEPTED_WITH_REVIEW_CAVEATS"
MILESTONE_BLOCKED = "MILESTONE_BLOCKED"

DEFAULT_INPUT_PDF_DIR = Path(r"D:\_datefac\input\real_test")
DEFAULT_OUTPUT_ROOT = Path(r"D:\_datefac\output")
DEFAULT_DOCS_ROOT = Path(r"D:\_datefac\docs")
DEFAULT_REPO_ROOT = Path(r"D:\_datefac")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\milestone_acceptance_audit_340a")

EXPECTED_PDFS = [
    "H3_AP202606081823352620_1.pdf",
    "H3_AP202606081823352906_1.pdf",
    "H3_AP202606081823356439_1.pdf",
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

REQUIRED_OUTPUT_FILES = {
    "337a_client_export": Path("mineru_real_test_337a/real_test_mineru_client_export_337a.xlsx"),
    "337b_client_export": Path("mineru_candidate_precision_337b/real_test_mineru_client_export_337b.xlsx"),
    "337c_client_export": Path("core_financial_context_repair_337c/real_test_mineru_client_export_337c.xlsx"),
    "337d_client_export": Path("reviewed_strictness_year_alignment_337d/real_test_mineru_client_export_337d.xlsx"),
    "338c_plan": Path("grounded_ai_review_338c/grounded_ai_review_338c_plan.xlsx"),
    "338d_plan": Path("ai_review_adoption_simulation_338d/ai_review_adoption_simulation_338d_plan.xlsx"),
}

DOC_FILES = {
    "README": Path("README.md"),
    "runbook_zh": Path("docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_zh.md"),
    "runbook_en": Path("docs/demo/datefac_real_pdf_mineru_ai_review_runbook_339a_en.md"),
    "architecture_zh": Path("docs/demo/datefac_ai_review_architecture_339a_zh.md"),
    "architecture_en": Path("docs/demo/datefac_ai_review_architecture_339a_en.md"),
}

DOC_CONCEPT_RULES = {
    "README": {
        "mineru_first_real_pdf_intake": ["mineru-first", "mineru first"],
        "ai_review_dry_run_no_write_back": ["dry-run", "no-write-back", "dry-run only", "write back"],
        "not_client_ready": ["not client-ready", "client_ready = false", "client ready = false"],
        "not_production_ready": ["not production-ready", "production_ready = false", "production ready = false"],
        "ai_review_model_candidate": ["ai_review_model", "candidate text adjudicator"],
        "deepseek_baseline": ["deepseek flash", "baseline", "fallback"],
        "vision_model_future": ["vision model", "future visual", "layout uncertainty", "future complement", "image-table uncertainty"],
    },
    "runbook_zh": {
        "mineru_first_real_pdf_intake": ["mineru", "pdf"],
        "ai_review_dry_run_no_write_back": ["dry-run", "no-write-back"],
        "not_client_ready": ["client-ready", "not client-ready", "涓嶆槸 client-ready", "褰撳墠涓嶆槸 client-ready"],
        "not_production_ready": ["production-ready", "not production-ready", "涓嶆槸 production-ready", "褰撳墠涓嶆槸 production-ready"],
    },
    "runbook_en": {
        "mineru_first_real_pdf_intake": ["mineru", "real pdf"],
        "ai_review_dry_run_no_write_back": ["dry-run", "no-write-back", "write-back"],
        "not_client_ready": ["not client-ready"],
        "not_production_ready": ["not production-ready"],
    },
    "architecture_zh": {
        "ai_review_dry_run_no_write_back": ["dry-run", "not a write-back path", "涓嶅啓鍥", "涓嶅啓鍥為摼璺"],
        "not_client_ready": ["client-ready", "not client-ready", "涓嶆槸 client-ready", "褰撳墠涓嶆槸 client-ready"],
        "not_production_ready": ["production-ready", "not production-ready", "涓嶆槸 production-ready", "褰撳墠涓嶆槸 production-ready"],
        "ai_review_model_candidate": ["ai_review_model", "candidate text adjudicator", "鍊欓€夋ā鍨"],
        "deepseek_baseline": ["deepseek flash", "baseline", "fallback"],
        "vision_model_future": ["vision model", "future", "layout", "image-table", "鎴浘", "鐗堥潰"],
    },
    "architecture_en": {
        "ai_review_dry_run_no_write_back": ["dry-run", "not a write-back path", "write back"],
        "not_client_ready": ["not client-ready"],
        "not_production_ready": ["not production-ready"],
        "ai_review_model_candidate": ["ai_review_model", "candidate text adjudicator"],
        "deepseek_baseline": ["deepseek flash", "baseline", "fallback"],
        "vision_model_future": ["vision model", "future complement", "layout", "image-table uncertainty"],
    },
}

UNSAFE_PHRASES = [
    "client-ready",
    "production-ready",
    "fully automatic commercial saas",
    "100% accurate",
    "no human review needed",
    "ai decisions are final",
]

SAFE_SECTION_TOKENS = [
    "unsafe claims",
    "must not claim",
    "forbidden",
    "do not claim",
    "must not",
    "still is not",
    "it still is not",
    "is not:",
    "still is not:",
    "\u5f53\u524d\u4ed3\u5e93\u4ecd\u7136\u4e0d\u662f",
    "\u4e0d\u662f",
    "\u5f53\u524d\u4e0d\u662f",
    "\u4e0d\u80fd\u5ba3\u79f0",
    "\u4e0d\u80fd\u8bf4",
    "\u7981\u6b62",
    "\u4e0d\u8be5\u5ba3\u79f0",
]

EXPLICIT_SAFE_PATTERNS = [
    "not client-ready",
    "not production-ready",
    "not 100% accurate",
    "ai decisions are dry-run only",
    "human review remains necessary",
    "\u4e0d\u662f client-ready",
    "\u5f53\u524d\u4e0d\u662f client-ready",
    "\u4e0d\u662f production-ready",
    "\u5f53\u524d\u4e0d\u662f production-ready",
    "\u4e0d\u5199\u56de",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    return _clean_frame(pd.read_excel(path, sheet_name=sheet_name))


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


def _git_cached_names_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
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
    staged = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _matched_line(text: str, patterns: Sequence[str]) -> str:
    for line in text.splitlines():
        line_text = line.strip()
        line_lower = line_text.lower()
        if any(pattern.lower() in line_lower for pattern in patterns):
            return line_text[:240]
    return ""


def _build_doc_consistency_rows(repo_root: Path) -> Tuple[pd.DataFrame, Dict[str, bool], List[str]]:
    rows: List[Dict[str, Any]] = []
    concept_pass: Dict[str, bool] = {}
    missing_docs: List[str] = []
    for doc_key, rel_path in DOC_FILES.items():
        path = repo_root / rel_path
        if not path.exists():
            missing_docs.append(str(path))
            continue
        text = path.read_text(encoding="utf-8")
        rules = DOC_CONCEPT_RULES.get(doc_key, {})
        for concept, patterns in rules.items():
            matched = _matched_line(text, patterns)
            rows.append(
                {
                    "doc_key": doc_key,
                    "path": str(path),
                    "concept": concept,
                    "patterns": " | ".join(patterns),
                    "status": "PASS" if matched else "FAIL",
                    "matched_line_excerpt": matched,
                }
            )
            concept_pass[f"{doc_key}:{concept}"] = bool(matched)
    return _clean_frame(pd.DataFrame(rows)), concept_pass, missing_docs


def _unsafe_context_recent(recent_lines: Sequence[str]) -> bool:
    text = " | ".join(recent_lines).lower()
    return any(token in text for token in SAFE_SECTION_TOKENS)


def _line_is_explicitly_safe(line: str) -> bool:
    lower = line.lower()
    return any(pattern in lower for pattern in EXPLICIT_SAFE_PATTERNS)


def _scan_unsafe_claims(label: str, text: str) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    recent_non_empty: List[str] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        line_lower = line.lower()
        for phrase in UNSAFE_PHRASES:
            if phrase in line_lower:
                safe = _line_is_explicitly_safe(line) or _unsafe_context_recent(recent_non_empty[-10:])
                hits.append(
                    {
                        "source": label,
                        "line_no": line_no,
                        "phrase": phrase,
                        "line_excerpt": line[:240],
                        "status": "SAFE_CONTEXT" if safe else "FAIL",
                    }
                )
        recent_non_empty.append(line)
    return hits


def _reviewed_sample_337d(reviewed_workbook_path: Path) -> pd.DataFrame:
    source_trace_df = _read_excel(reviewed_workbook_path, "04_SOURCE_TRACE")
    if source_trace_df.empty:
        return pd.DataFrame()
    reviewed_df = source_trace_df[source_trace_df["status_after_337d"].astype(str) == "reviewed_preview"].copy()
    if reviewed_df.empty:
        return pd.DataFrame()
    reviewed_df = reviewed_df.sort_values(["document", "source_page", "metric_after_337d", "value"], kind="stable")
    sampled = reviewed_df.groupby("document", group_keys=False).head(10).copy()
    rows = []
    for _, row in sampled.iterrows():
        rows.append(
            {
                "candidate_id": _norm_text(row.get("candidate_id")),
                "document": _norm_text(row.get("document")),
                "metric": _norm_text(row.get("metric_after_337d") or row.get("metric_after")),
                "metric_display_zh": _norm_text(row.get("metric_display_zh_after_337d") or row.get("metric_display_zh_after")),
                "year": _norm_text(row.get("year_after_337d") or row.get("year")),
                "value": _norm_text(row.get("value")),
                "unit": _norm_text(row.get("unit_after_337d") or row.get("unit_after_337c") or row.get("unit")),
                "source_page": _norm_text(row.get("source_page")),
                "source_evidence_excerpt": _norm_text(row.get("source_evidence_excerpt")),
                "table_role_if_available": _norm_text(row.get("table_role_337c") or row.get("table_role_337b")),
                "audit_status_placeholder": "",
                "audit_notes_placeholder": "",
            }
        )
    return _clean_frame(pd.DataFrame(rows))


def _ai_adoption_audit_338d(adoption_plan_path: Path) -> pd.DataFrame:
    adoption_df = _read_excel(adoption_plan_path, "02_ADOPTION_PLAN")
    if adoption_df.empty:
        return adoption_df
    keep_actions = {
        "ACCEPT_MODEL_CONFIRM",
        "ACCEPT_MODEL_REJECT",
        "HOLD_FOR_HUMAN_REVIEW",
        "INVALID_MODEL_RESPONSE",
        "REJECT_BY_DETERMINISTIC_RULE",
    }
    filtered = adoption_df[adoption_df["adoption_action"].astype(str).isin(keep_actions)].copy()
    filtered = filtered.sort_values(["adoption_action", "document", "source_row_no"], kind="stable")
    columns = [
        "adoption_id",
        "adjudication_id",
        "document",
        "metric_before",
        "year_before",
        "value_before",
        "unit_before",
        "model_name",
        "confidence",
        "grounding_source",
        "adoption_action",
        "adoption_reason",
        "recommended_route_after_adoption",
        "human_review_required",
    ]
    existing = [column for column in columns if column in filtered.columns]
    return _clean_frame(filtered[existing])


def _milestone_judgment(qa_fail_count: int) -> str:
    if qa_fail_count > 0:
        return MILESTONE_BLOCKED
    return MILESTONE_ACCEPTED_WITH_REVIEW_CAVEATS


def _next_step_recommendation(summary_338d: Mapping[str, Any]) -> str:
    hold_count = _safe_int(summary_338d.get("hold_for_human_review_count"))
    invalid_count = _safe_int(summary_338d.get("invalid_model_response_count"))
    if hold_count > 0 or invalid_count > 0:
        return "HUMAN_REVIEW_PACKAGE"
    return "FULL_AI_REVIEW"


def build_milestone_acceptance_audit_340a(
    *,
    input_pdf_dir: Path,
    output_root: Path,
    docs_root: Path,
    repo_root: Path,
    output_dir: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    pdf_paths = sorted(path for path in input_pdf_dir.glob("*.pdf") if path.is_file())
    input_pdf_rows = [
        {"pdf_name": path.name, "exists": True, "expected_pdf": path.name in EXPECTED_PDFS}
        for path in pdf_paths
    ]
    expected_presence_rows = []
    for pdf_name in EXPECTED_PDFS:
        path = input_pdf_dir / pdf_name
        expected_presence_rows.append({"pdf_name": pdf_name, "exists": path.exists(), "path": str(path)})

    required_output_rows = []
    for key, rel_path in REQUIRED_OUTPUT_FILES.items():
        full_path = output_root / rel_path
        required_output_rows.append({"artifact_key": key, "path": str(full_path), "exists": full_path.exists()})

    summary_337a = _read_json(output_root / "mineru_real_test_337a" / "00_batch_summary.json")
    summary_337b = _read_json(output_root / "mineru_candidate_precision_337b" / "mineru_candidate_precision_337b_summary.json")
    summary_337c = _read_json(output_root / "core_financial_context_repair_337c" / "core_financial_context_repair_337c_summary.json")
    summary_337d = _read_json(output_root / "reviewed_strictness_year_alignment_337d" / "reviewed_strictness_year_alignment_337d_summary.json")
    summary_338d = _read_json(output_root / "ai_review_adoption_simulation_338d" / "ai_review_adoption_simulation_338d_summary.json")

    per_pdf_candidate_counts: Dict[str, int] = {}
    for pdf_name in EXPECTED_PDFS:
        stem = Path(pdf_name).stem
        path = output_root / "mineru_real_test_337a" / "datefac_debug" / stem / "document_summary.json"
        if path.exists():
            per_pdf_candidate_counts[stem] = _safe_int(_read_json(path).get("metric_candidate_count"))

    metrics_rows = [
        {"metric_name": "337A_pdf_processed_count", "expected_value": 3, "actual_value": _safe_int(summary_337a.get("pdf_processed_count")), "status": "PASS" if _safe_int(summary_337a.get("pdf_processed_count")) == 3 else "FAIL"},
        {"metric_name": "337A_352620_1_candidate_count", "expected_value": 134, "actual_value": per_pdf_candidate_counts.get("H3_AP202606081823352620_1", 0), "status": "PASS" if per_pdf_candidate_counts.get("H3_AP202606081823352620_1", 0) == 134 else "FAIL"},
        {"metric_name": "337A_352906_1_candidate_count", "expected_value": 111, "actual_value": per_pdf_candidate_counts.get("H3_AP202606081823352906_1", 0), "status": "PASS" if per_pdf_candidate_counts.get("H3_AP202606081823352906_1", 0) == 111 else "FAIL"},
        {"metric_name": "337A_356439_1_candidate_count", "expected_value": 102, "actual_value": per_pdf_candidate_counts.get("H3_AP202606081823356439_1", 0), "status": "PASS" if per_pdf_candidate_counts.get("H3_AP202606081823356439_1", 0) == 102 else "FAIL"},
        {"metric_name": "337B_reviewed_after_count", "expected_value": 98, "actual_value": _safe_int(summary_337b.get("reviewed_after_count")), "status": "PASS" if _safe_int(summary_337b.get("reviewed_after_count")) == 98 else "FAIL"},
        {"metric_name": "337C_reviewed_after_count", "expected_value": 148, "actual_value": _safe_int(summary_337c.get("reviewed_after_count")), "status": "PASS" if _safe_int(summary_337c.get("reviewed_after_count")) == 148 else "FAIL"},
        {"metric_name": "337D_reviewed_after_count", "expected_value": 112, "actual_value": _safe_int(summary_337d.get("reviewed_after_count")), "status": "PASS" if _safe_int(summary_337d.get("reviewed_after_count")) == 112 else "FAIL"},
        {"metric_name": "338D_input_row_count", "expected_value": 50, "actual_value": _safe_int(summary_338d.get("input_338c_row_count")), "status": "PASS" if _safe_int(summary_338d.get("input_338c_row_count")) == 50 else "FAIL"},
        {"metric_name": "338D_accept_model_confirm_count", "expected_value": 39, "actual_value": _safe_int(summary_338d.get("accept_model_confirm_count")), "status": "PASS" if _safe_int(summary_338d.get("accept_model_confirm_count")) == 39 else "FAIL"},
        {"metric_name": "338D_accept_model_reject_count", "expected_value": 3, "actual_value": _safe_int(summary_338d.get("accept_model_reject_count")), "status": "PASS" if _safe_int(summary_338d.get("accept_model_reject_count")) == 3 else "FAIL"},
        {"metric_name": "338D_hold_for_human_review_count", "expected_value": 3, "actual_value": _safe_int(summary_338d.get("hold_for_human_review_count")), "status": "PASS" if _safe_int(summary_338d.get("hold_for_human_review_count")) == 3 else "FAIL"},
        {"metric_name": "338D_invalid_model_response_count", "expected_value": 1, "actual_value": _safe_int(summary_338d.get("invalid_model_response_count")), "status": "PASS" if _safe_int(summary_338d.get("invalid_model_response_count")) == 1 else "FAIL"},
        {"metric_name": "338D_deterministic_rule_override_count", "expected_value": 0, "actual_value": _safe_int(summary_338d.get("deterministic_rule_override_count")), "status": "PASS" if _safe_int(summary_338d.get("deterministic_rule_override_count")) == 0 else "FAIL"},
    ]
    key_metric_df = _clean_frame(pd.DataFrame(metrics_rows))

    reviewed_sample_df = _reviewed_sample_337d(output_root / "reviewed_strictness_year_alignment_337d" / "real_test_mineru_client_export_337d.xlsx")
    ai_adoption_audit_df = _ai_adoption_audit_338d(output_root / "ai_review_adoption_simulation_338d" / "ai_review_adoption_simulation_338d_plan.xlsx")

    doc_consistency_df, concept_pass, missing_docs = _build_doc_consistency_rows(repo_root)
    documentation_consistency_passed = (not missing_docs) and all(concept_pass.values())

    unsafe_hits: List[Dict[str, Any]] = []
    for rel_path in DOC_FILES.values():
        path = repo_root / rel_path
        if path.exists():
            unsafe_hits.extend(_scan_unsafe_claims(str(path), path.read_text(encoding="utf-8")))

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_status_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_cached_after = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    qa_checks = [
        {"check_name": "input_pdf_count_is_3", "status": "PASS" if len(pdf_paths) == 3 else "FAIL", "detail": str(len(pdf_paths))},
        {"check_name": "all_expected_pdfs_exist", "status": "PASS" if all(row["exists"] for row in expected_presence_rows) else "FAIL", "detail": json.dumps(expected_presence_rows, ensure_ascii=False)},
        {"check_name": "required_output_files_exist", "status": "PASS" if all(row["exists"] for row in required_output_rows) else "FAIL", "detail": json.dumps(required_output_rows, ensure_ascii=False)},
        {"check_name": "key_metrics_match_expected", "status": "PASS" if (key_metric_df["status"] == "PASS").all() else "FAIL", "detail": json.dumps(metrics_rows, ensure_ascii=False)},
        {"check_name": "reviewed_sample_sheet_has_rows", "status": "PASS" if not reviewed_sample_df.empty else "FAIL", "detail": str(len(reviewed_sample_df))},
        {"check_name": "ai_adoption_audit_sheet_has_rows", "status": "PASS" if not ai_adoption_audit_df.empty else "FAIL", "detail": str(len(ai_adoption_audit_df))},
        {"check_name": "documentation_consistency_passed", "status": "PASS" if documentation_consistency_passed else "FAIL", "detail": json.dumps(missing_docs, ensure_ascii=False)},
        {"check_name": "unsafe_claim_scan_passed", "status": "PASS", "detail": "pre_report_scan_only"},
        {"check_name": "official_assets_unchanged", "status": "PASS" if official_assets_before == official_assets_after else "FAIL", "detail": json.dumps(official_assets_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_status_preserved", "status": "PASS" if protected_status_before == protected_status_after else "FAIL", "detail": json.dumps(protected_status_after, ensure_ascii=False)},
        {"check_name": "protected_dirty_paths_not_staged", "status": "PASS" if not protected_cached_after else "FAIL", "detail": json.dumps(protected_cached_after, ensure_ascii=False)},
    ]

    provisional_qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")
    summary = {
        "generated_at_utc": _utc_now(),
        "repo_root": str(repo_root),
        "docs_root": str(docs_root),
        "output_root": str(output_root),
        "output_dir": str(output_dir),
        "input_pdf_count": len(pdf_paths),
        "expected_pdf_present_count": sum(1 for row in expected_presence_rows if row["exists"]),
        "parsed_pdf_count_337a": _safe_int(summary_337a.get("pdf_processed_count")),
        "candidate_count_352620_1": per_pdf_candidate_counts.get("H3_AP202606081823352620_1", 0),
        "candidate_count_352906_1": per_pdf_candidate_counts.get("H3_AP202606081823352906_1", 0),
        "candidate_count_356439_1": per_pdf_candidate_counts.get("H3_AP202606081823356439_1", 0),
        "reviewed_after_count_337b": _safe_int(summary_337b.get("reviewed_after_count")),
        "reviewed_after_count_337c": _safe_int(summary_337c.get("reviewed_after_count")),
        "reviewed_after_count_337d": _safe_int(summary_337d.get("reviewed_after_count")),
        "input_row_count_338d": _safe_int(summary_338d.get("input_338c_row_count")),
        "accept_model_confirm_count_338d": _safe_int(summary_338d.get("accept_model_confirm_count")),
        "accept_model_reject_count_338d": _safe_int(summary_338d.get("accept_model_reject_count")),
        "hold_for_human_review_count_338d": _safe_int(summary_338d.get("hold_for_human_review_count")),
        "invalid_model_response_count_338d": _safe_int(summary_338d.get("invalid_model_response_count")),
        "deterministic_rule_override_count_338d": _safe_int(summary_338d.get("deterministic_rule_override_count")),
        "required_pipeline_output_file_count": len(required_output_rows),
        "existing_pipeline_output_file_count": sum(1 for row in required_output_rows if row["exists"]),
        "sample_reviewed_row_count_337d": int(len(reviewed_sample_df)),
        "ai_adoption_audit_row_count": int(len(ai_adoption_audit_df)),
        "documentation_consistency_passed": documentation_consistency_passed,
        "unsafe_claim_audit_passed": False,
        "suitable_for_demo_research_preview": provisional_qa_fail_count == 0,
        "client_ready": False,
        "production_ready": False,
        "ai_adoption_is_dry_run_only": True,
        "human_review_remains_necessary": True,
        "next_step_recommendation": _next_step_recommendation(summary_338d),
        "milestone_judgment": _milestone_judgment(provisional_qa_fail_count),
        "qa_fail_count": provisional_qa_fail_count,
        "no_official_asset_modification_during_340a": official_assets_before == official_assets_after,
    }

    from datefac.trust.milestone_acceptance_audit_340a_report import report_markdown

    report_text = report_markdown(summary, {"checks": qa_checks})
    report_hits = _scan_unsafe_claims("generated_report", report_text)
    all_unsafe_hits = unsafe_hits + report_hits
    unsafe_claim_fail_count = sum(1 for row in all_unsafe_hits if row["status"] == "FAIL")
    summary["unsafe_claim_audit_passed"] = unsafe_claim_fail_count == 0

    qa_checks[7] = {
        "check_name": "unsafe_claim_scan_passed",
        "status": "PASS" if unsafe_claim_fail_count == 0 else "FAIL",
        "detail": str(unsafe_claim_fail_count),
    }

    qa_fail_count = sum(1 for check in qa_checks if check["status"] == "FAIL")
    summary["qa_fail_count"] = qa_fail_count
    summary["milestone_judgment"] = _milestone_judgment(qa_fail_count)
    summary["suitable_for_demo_research_preview"] = qa_fail_count == 0

    manifest = {
        "task": "340A_milestone_acceptance_audit_after_mineru_ai_review",
        "input_pdf_dir": str(input_pdf_dir),
        "output_root": str(output_root),
        "docs_root": str(docs_root),
        "repo_root": str(repo_root),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "milestone_acceptance_audit_340a_summary.json"),
            "manifest_json": str(output_dir / "milestone_acceptance_audit_340a_manifest.json"),
            "qa_json": str(output_dir / "milestone_acceptance_audit_340a_qa.json"),
            "report_md": str(output_dir / "milestone_acceptance_audit_340a_report.md"),
            "workbook_xlsx": str(output_dir / "milestone_acceptance_audit_340a.xlsx"),
        },
    }

    qa_json = {
        "milestone_judgment": summary["milestone_judgment"],
        "qa_fail_count": qa_fail_count,
        "checks": qa_checks,
        "unsafe_claim_hits": all_unsafe_hits,
        "missing_docs": missing_docs,
        "official_assets_before": official_assets_before,
        "official_assets_after": official_assets_after,
    }

    workbook_sheets = {
        "00_README": _clean_frame(
            pd.DataFrame(
                [
                    {"topic": "Workbook purpose", "message": "This workbook audits whether the MinerU + AI review milestone is reproducible and explainable for demo / research-preview use."},
                    {"topic": "Boundary", "message": "340A is validation-only. It does not modify production pipeline behavior or official assets."},
                    {"topic": "Current status", "message": "The milestone can be suitable for demo / research-preview while still not being client-ready or production-ready."},
                ]
            )
        ),
        "01_AUDIT_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_INPUT_PDF_AUDIT": _clean_frame(pd.DataFrame(expected_presence_rows + input_pdf_rows)),
        "03_OUTPUT_ARTIFACT_AUDIT": _clean_frame(pd.DataFrame(required_output_rows)),
        "04_KEY_METRIC_AUDIT": key_metric_df,
        "05_337D_REVIEWED_SAMPLE": reviewed_sample_df,
        "06_338D_AI_ADOPTION_AUDIT": ai_adoption_audit_df,
        "07_DOC_CONSISTENCY_AUDIT": doc_consistency_df,
        "08_UNSAFE_CLAIM_AUDIT": _clean_frame(pd.DataFrame(all_unsafe_hits)),
        "09_QA_CHECKS": _clean_frame(pd.DataFrame(qa_checks)),
        "10_NEXT_STEP": _clean_frame(
            pd.DataFrame(
                [
                    {
                        "next_step_recommendation": summary["next_step_recommendation"],
                        "reason": (
                            "Human review package is recommended next because 338D still has held and invalid rows."
                            if summary["next_step_recommendation"] == "HUMAN_REVIEW_PACKAGE"
                            else "Full AI review can be considered next if human-review pressure is low."
                        ),
                    }
                ]
            )
        ),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "workbook_sheets": workbook_sheets,
    }
