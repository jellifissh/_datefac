from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.client_preview_export_audit_340g import READY_DECISION as READY_340G_DECISION
from datefac.trust.human_review_apply_simulation_340c import READY_FULL_DECISION as READY_340C_FULL_DECISION
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION = "HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_READY"
NOT_READY_DECISION = "HUMAN_REVIEWED_CLIENT_PREVIEW_MILESTONE_341A_NOT_READY"

DEFAULT_HUMAN_REVIEW_340B_DIR = Path(r"D:\_datefac\output\human_review_after_ai_adoption_340b")
DEFAULT_HUMAN_REVIEW_APPLY_340C_DIR = Path(r"D:\_datefac\output\human_review_apply_simulation_340c")
DEFAULT_FULL_HUMAN_REVIEW_APPLY_340D_DIR = Path(r"D:\_datefac\output\full_human_review_apply_plan_340d")
DEFAULT_POST_HUMAN_REVIEW_340E_DIR = Path(r"D:\_datefac\output\post_human_review_sidecar_result_340e")
DEFAULT_CLIENT_PREVIEW_340F_DIR = Path(r"D:\_datefac\output\client_preview_after_human_review_340f")
DEFAULT_CLIENT_PREVIEW_AUDIT_340G_DIR = Path(r"D:\_datefac\output\client_preview_export_audit_340g")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\human_reviewed_client_preview_milestone_341a")

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
    "01_MILESTONE_SUMMARY",
    "02_PIPELINE_STAGES",
    "03_KEY_COUNTS",
    "04_CLIENT_PREVIEW_AUDIT",
    "05_OUTPUT_ARTIFACTS",
    "06_REMAINING_RISKS",
    "07_DEMO_RUNBOOK",
    "08_NEXT_STEP_ROADMAP",
    "09_NO_WRITE_BACK_PROOF",
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


def _build_readme_df() -> pd.DataFrame:
    rows = [
        {
            "topic": "Purpose",
            "message": "341A packages the human-reviewed client preview milestone across the real PDF to audited preview chain.",
        },
        {
            "topic": "Milestone status",
            "message": "This milestone is demo-ready and client-preview-ready, but it is not client-ready for formal delivery and not production-ready.",
        },
        {
            "topic": "Advice boundary",
            "message": "This package is not investment advice.",
        },
        {
            "topic": "Scale boundary",
            "message": "This milestone still does not represent scalable production operation.",
        },
        {
            "topic": "Benchmark scope",
            "message": "The current benchmark is limited to the current real PDF sample set used in this chain.",
        },
        {
            "topic": "Remaining bottlenecks",
            "message": "Next bottlenecks are parser robustness, larger benchmark coverage, metadata extraction, batch stability, and a UI review workflow.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_no_apply_proof_df(no_apply_proof_json: Mapping[str, Any]) -> pd.DataFrame:
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


def _build_pipeline_stages_df() -> pd.DataFrame:
    rows = [
        {
            "stage_id": "340B",
            "stage_name": "Human Review Package After AI Adoption",
            "purpose": "Package review queue rows for manual validation after AI adoption simulation.",
            "key_output": "review workbook",
            "status_boundary": "manual review package only",
        },
        {
            "stage_id": "340C",
            "stage_name": "Human Review Apply Simulation",
            "purpose": "Validate human review decisions without write-back.",
            "key_output": "apply simulation plan",
            "status_boundary": "dry-run validation only",
        },
        {
            "stage_id": "340D",
            "stage_name": "Full Human Review Apply Plan",
            "purpose": "Consolidate reviewed human actions into a final dry-run plan.",
            "key_output": "final apply plan",
            "status_boundary": "still no write-back",
        },
        {
            "stage_id": "340E",
            "stage_name": "Post Human Review Sidecar Result",
            "purpose": "Produce the reviewed sidecar result after human validation.",
            "key_output": "sidecar reviewed result",
            "status_boundary": "sidecar only",
        },
        {
            "stage_id": "340F",
            "stage_name": "Client Preview Export After Human Review",
            "purpose": "Create a human-reviewed preview workbook for demo or preview discussion.",
            "key_output": "client preview workbook",
            "status_boundary": "preview only",
        },
        {
            "stage_id": "340G",
            "stage_name": "Client Preview Export Audit",
            "purpose": "Audit preview suitability, units, duplicates, traceability, and claim safety.",
            "key_output": "preview audit workbook",
            "status_boundary": "audit only",
        },
        {
            "stage_id": "341A",
            "stage_name": "Human-Reviewed Client Preview Milestone Package",
            "purpose": "Summarize the end-to-end milestone across reviewed preview and audit stages.",
            "key_output": "milestone package",
            "status_boundary": "milestone package only",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_key_counts_df(
    summary_340b: Mapping[str, Any],
    summary_340c: Mapping[str, Any],
    summary_340d: Mapping[str, Any],
    summary_340e: Mapping[str, Any],
    summary_340f: Mapping[str, Any],
    summary_340g: Mapping[str, Any],
) -> pd.DataFrame:
    rows = [
        {"metric": "340B_total_review_queue_count", "value": summary_340b.get("total_review_queue_count", ""), "expected": 77},
        {"metric": "340C_full_validation_passed", "value": summary_340c.get("decision", ""), "expected": READY_340C_FULL_DECISION},
        {"metric": "340D_final_reviewed_after_human_candidate_count", "value": summary_340d.get("final_reviewed_after_human_candidate_count", ""), "expected": 34},
        {"metric": "340E_reviewed_after_human_total_count", "value": summary_340e.get("reviewed_after_human_total_count", ""), "expected": 34},
        {"metric": "340F_client_preview_core_metric_count", "value": summary_340f.get("client_preview_core_metric_count", ""), "expected": 34},
        {"metric": "340G_audited_core_metric_count", "value": summary_340g.get("audited_core_metric_count", ""), "expected": 34},
        {"metric": "340G_duplicate_issue_count", "value": summary_340g.get("duplicate_issue_count", ""), "expected": 0},
        {"metric": "340G_unit_issue_count", "value": summary_340g.get("unit_issue_count", ""), "expected": 0},
        {"metric": "340G_missing_source_trace_count", "value": summary_340g.get("missing_source_trace_count", ""), "expected": 0},
        {"metric": "340G_unsafe_claim_count", "value": summary_340g.get("unsafe_claim_count", ""), "expected": 0},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_client_preview_audit_df(summary_340f: Mapping[str, Any], summary_340g: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {"audit_topic": "client_preview_core_metric_count", "value": summary_340f.get("client_preview_core_metric_count", ""), "status": "PASS" if summary_340f.get("client_preview_core_metric_count") == 34 else "FAIL"},
        {"audit_topic": "audited_core_metric_count", "value": summary_340g.get("audited_core_metric_count", ""), "status": "PASS" if summary_340g.get("audited_core_metric_count") == 34 else "FAIL"},
        {"audit_topic": "duplicate_issue_count", "value": summary_340g.get("duplicate_issue_count", ""), "status": "PASS" if summary_340g.get("duplicate_issue_count") == 0 else "FAIL"},
        {"audit_topic": "unit_issue_count", "value": summary_340g.get("unit_issue_count", ""), "status": "PASS" if summary_340g.get("unit_issue_count") == 0 else "FAIL"},
        {"audit_topic": "missing_source_trace_count", "value": summary_340g.get("missing_source_trace_count", ""), "status": "PASS" if summary_340g.get("missing_source_trace_count") == 0 else "FAIL"},
        {"audit_topic": "unsafe_claim_count", "value": summary_340g.get("unsafe_claim_count", ""), "status": "PASS" if summary_340g.get("unsafe_claim_count") == 0 else "FAIL"},
        {"audit_topic": "client_preview_audit_passed", "value": summary_340g.get("client_preview_audit_passed", ""), "status": "PASS" if summary_340g.get("client_preview_audit_passed") else "FAIL"},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_output_artifacts_df(
    human_review_340b_dir: Path,
    human_review_apply_340c_dir: Path,
    full_human_review_apply_340d_dir: Path,
    post_human_review_340e_dir: Path,
    client_preview_340f_dir: Path,
    client_preview_audit_340g_dir: Path,
) -> pd.DataFrame:
    rows = [
        {"stage": "340B", "artifact_path": str(human_review_340b_dir / "human_review_after_ai_adoption_340b_review_template.xlsx"), "artifact_type": "review workbook"},
        {"stage": "340C", "artifact_path": str(human_review_apply_340c_dir / "human_review_apply_simulation_340c_apply_plan.xlsx"), "artifact_type": "apply simulation workbook"},
        {"stage": "340D", "artifact_path": str(full_human_review_apply_340d_dir / "full_human_review_apply_plan_340d.xlsx"), "artifact_type": "final apply plan workbook"},
        {"stage": "340E", "artifact_path": str(post_human_review_340e_dir / "post_human_review_sidecar_result_340e.xlsx"), "artifact_type": "sidecar result workbook"},
        {"stage": "340F", "artifact_path": str(client_preview_340f_dir / "client_preview_after_human_review_340f.xlsx"), "artifact_type": "client preview workbook"},
        {"stage": "340G", "artifact_path": str(client_preview_audit_340g_dir / "client_preview_export_audit_340g.xlsx"), "artifact_type": "client preview audit workbook"},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_remaining_risks_df() -> pd.DataFrame:
    rows = [
        {
            "risk_area": "Parser robustness",
            "current_state": "Current sample chain passed, but broader parser robustness is still unproven across larger PDF diversity.",
            "next_need": "Expand benchmark coverage and harden parser fallbacks.",
        },
        {
            "risk_area": "Benchmark breadth",
            "current_state": "The benchmark remains limited to the current real PDF sample set.",
            "next_need": "Run a larger multi-document benchmark with broader broker and layout diversity.",
        },
        {
            "risk_area": "Metadata extraction",
            "current_state": "Review and preview stages focus on trusted metric routing, not full metadata completeness.",
            "next_need": "Improve document metadata extraction and normalization.",
        },
        {
            "risk_area": "Batch stability",
            "current_state": "The milestone demonstrates one validated chain, not scaled batch reliability.",
            "next_need": "Harden batch orchestration, retries, logging, and monitoring.",
        },
        {
            "risk_area": "UI review workflow",
            "current_state": "Human review is workbook-driven and deterministic, but not yet a scalable product workflow.",
            "next_need": "Build a structured UI review workflow with audit trails and handoff states.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_demo_runbook_df() -> pd.DataFrame:
    rows = [
        {
            "step_no": 1,
            "step": "Show the audited milestone summary first",
            "why_it_matters": "This frames the work as a validated preview milestone rather than a production claim.",
        },
        {
            "step_no": 2,
            "step": "Walk through the 340B to 340G stage chain",
            "why_it_matters": "This shows that human review and preview audit were isolated before any delivery-facing claim.",
        },
        {
            "step_no": 3,
            "step": "Open the 340F client preview workbook",
            "why_it_matters": "This demonstrates the reviewed preview rows and preserved source traceability.",
        },
        {
            "step_no": 4,
            "step": "Open the 340G audit workbook",
            "why_it_matters": "This proves duplicate, unit, trace, and claim checks passed with qa_fail_count = 0.",
        },
        {
            "step_no": 5,
            "step": "Close by restating remaining risks and next engineering bottlenecks",
            "why_it_matters": "This avoids overclaiming and keeps the milestone grounded.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_next_step_roadmap_df() -> pd.DataFrame:
    rows = [
        {
            "roadmap_order": 1,
            "next_step": "Expand parser robustness benchmark",
            "target_outcome": "Validate more layouts, more brokers, and more document edge cases.",
        },
        {
            "roadmap_order": 2,
            "next_step": "Broaden real PDF benchmark coverage",
            "target_outcome": "Move from the current sample milestone toward a more representative benchmark.",
        },
        {
            "roadmap_order": 3,
            "next_step": "Improve metadata extraction",
            "target_outcome": "Add stronger metadata completeness and provenance consistency.",
        },
        {
            "roadmap_order": 4,
            "next_step": "Harden batch stability",
            "target_outcome": "Improve retry behavior, observability, and batch-scale reliability.",
        },
        {
            "roadmap_order": 5,
            "next_step": "Design a UI review workflow",
            "target_outcome": "Replace workbook-only manual review with a more scalable operator interface.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_human_reviewed_client_preview_milestone_341a(
    *,
    human_review_340b_dir: Path,
    human_review_apply_340c_dir: Path,
    full_human_review_apply_340d_dir: Path,
    post_human_review_340e_dir: Path,
    client_preview_340f_dir: Path,
    client_preview_audit_340g_dir: Path,
    output_dir: Path,
    repo_root: Path,
    alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
    scope_asset_path: Path = FORMAL_SCOPE_RULES_PATH,
) -> Dict[str, Any]:
    summary_340b_path = human_review_340b_dir / "human_review_after_ai_adoption_340b_summary.json"
    summary_340c_path = human_review_apply_340c_dir / "human_review_apply_simulation_340c_summary.json"
    summary_340d_path = full_human_review_apply_340d_dir / "full_human_review_apply_plan_340d_summary.json"
    summary_340e_path = post_human_review_340e_dir / "post_human_review_sidecar_result_340e_summary.json"
    summary_340f_path = client_preview_340f_dir / "client_preview_after_human_review_340f_summary.json"
    summary_340g_path = client_preview_audit_340g_dir / "client_preview_export_audit_340g_summary.json"

    files_read = [
        str(summary_340b_path),
        str(summary_340c_path),
        str(summary_340d_path),
        str(summary_340e_path),
        str(summary_340f_path),
        str(summary_340g_path),
    ]
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    input_hashes_before = {str(path): sha256_file(path) for path in map(Path, files_read)}

    summary_340b = _read_json(summary_340b_path) if summary_340b_path.exists() else {}
    summary_340c = _read_json(summary_340c_path) if summary_340c_path.exists() else {}
    summary_340d = _read_json(summary_340d_path) if summary_340d_path.exists() else {}
    summary_340e = _read_json(summary_340e_path) if summary_340e_path.exists() else {}
    summary_340f = _read_json(summary_340f_path) if summary_340f_path.exists() else {}
    summary_340g = _read_json(summary_340g_path) if summary_340g_path.exists() else {}

    output_dir.mkdir(parents=True, exist_ok=True)

    input_hashes_after = {str(path): sha256_file(path) for path in map(Path, files_read)}
    upstream_unchanged = input_hashes_before == input_hashes_after

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    output_staged = _git_staged_names_for_paths([str(output_dir)], repo_root)

    no_apply_proof_json = build_no_apply_proof(
        stage="341A",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof_json["upstream_input_hashes_before"] = input_hashes_before
    no_apply_proof_json["upstream_input_hashes_after"] = input_hashes_after
    no_apply_proof_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_apply_proof_json["no_write_back"] = True

    no_write_back_proof_passed = (
        bool(no_apply_proof_json.get("no_official_asset_modification_during_341a"))
        and upstream_unchanged
    )

    demo_ready = True
    client_preview_ready = bool(summary_340f.get("client_preview_ready")) and bool(summary_340g.get("client_preview_audit_passed"))
    client_ready = False
    production_ready = False

    key_counts_consistent = (
        summary_340d.get("final_reviewed_after_human_candidate_count") == 34
        and summary_340e.get("reviewed_after_human_total_count") == 34
        and summary_340f.get("client_preview_core_metric_count") == 34
        and summary_340g.get("audited_core_metric_count") == 34
        and summary_340g.get("duplicate_issue_count") == 0
        and summary_340g.get("unit_issue_count") == 0
        and summary_340g.get("missing_source_trace_count") == 0
        and summary_340g.get("unsafe_claim_count") == 0
    )

    readme_df = _build_readme_df()
    readme_text = "\n".join(readme_df["message"].astype(str).tolist())

    checks = [
        {"check_name": "inputs::340b_summary_exists", "status": "PASS" if summary_340b_path.exists() else "FAIL", "detail": str(summary_340b_path)},
        {"check_name": "inputs::340c_summary_exists", "status": "PASS" if summary_340c_path.exists() else "FAIL", "detail": str(summary_340c_path)},
        {"check_name": "inputs::340d_summary_exists", "status": "PASS" if summary_340d_path.exists() else "FAIL", "detail": str(summary_340d_path)},
        {"check_name": "inputs::340e_summary_exists", "status": "PASS" if summary_340e_path.exists() else "FAIL", "detail": str(summary_340e_path)},
        {"check_name": "inputs::340f_summary_exists", "status": "PASS" if summary_340f_path.exists() else "FAIL", "detail": str(summary_340f_path)},
        {"check_name": "inputs::340g_summary_exists", "status": "PASS" if summary_340g_path.exists() else "FAIL", "detail": str(summary_340g_path)},
        {"check_name": "readiness::340g_ready", "status": "PASS" if summary_340g.get("decision") == READY_340G_DECISION and summary_340g.get("qa_fail_count") == 0 else "FAIL", "detail": json.dumps(summary_340g, ensure_ascii=False)},
        {"check_name": "quality::340b_total_review_queue_count", "status": "PASS" if summary_340b.get("total_review_queue_count") == 77 else "FAIL", "detail": str(summary_340b.get("total_review_queue_count", ""))},
        {"check_name": "quality::340c_full_validation_passed", "status": "PASS" if summary_340c.get("decision") == READY_340C_FULL_DECISION and summary_340c.get("qa_fail_count") == 0 else "FAIL", "detail": json.dumps(summary_340c, ensure_ascii=False)},
        {"check_name": "quality::key_counts_consistent", "status": "PASS" if key_counts_consistent else "FAIL", "detail": json.dumps({"340d": summary_340d.get("final_reviewed_after_human_candidate_count"), "340e": summary_340e.get("reviewed_after_human_total_count"), "340f": summary_340f.get("client_preview_core_metric_count"), "340g": summary_340g.get("audited_core_metric_count")}, ensure_ascii=False)},
        {"check_name": "claims::demo_ready_true", "status": "PASS" if demo_ready else "FAIL", "detail": str(demo_ready).lower()},
        {"check_name": "claims::client_preview_ready_true", "status": "PASS" if client_preview_ready else "FAIL", "detail": str(client_preview_ready).lower()},
        {"check_name": "claims::client_ready_false", "status": "PASS" if not client_ready else "FAIL", "detail": str(client_ready).lower()},
        {"check_name": "claims::production_ready_false", "status": "PASS" if not production_ready else "FAIL", "detail": str(production_ready).lower()},
        {"check_name": "claims::no_investment_advice_claim", "status": "PASS" if not _contains_forbidden_claim(readme_text, ["investment advice"]) else "FAIL", "detail": "README text checked"},
        {"check_name": "claims::not_scalable_production_stated", "status": "PASS" if "not scalable production" in readme_text.casefold() or "still does not represent scalable production" in readme_text.casefold() else "FAIL", "detail": "README text checked"},
        {"check_name": "claims::benchmark_scope_stated", "status": "PASS" if "current real pdf sample set" in readme_text.casefold() else "FAIL", "detail": "README text checked"},
        {"check_name": "claims::bottlenecks_stated", "status": "PASS" if "parser robustness" in readme_text.casefold() and "ui review workflow" in readme_text.casefold() else "FAIL", "detail": "README text checked"},
        {"check_name": "safety::no_write_back_to_upstream_workbooks", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"upstream_unchanged": upstream_unchanged, "official_assets_unchanged": bool(no_apply_proof_json.get("no_official_asset_modification_during_341a"))}, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::output_artifacts_not_staged", "status": "PASS" if not output_staged else "FAIL", "detail": json.dumps(output_staged, ensure_ascii=False)},
    ]

    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")
    decision = READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION

    summary = {
        "generated_at_utc": _utc_now(),
        "demo_ready": demo_ready,
        "client_preview_ready": client_preview_ready,
        "client_ready": client_ready,
        "production_ready": production_ready,
        "total_review_queue_count_340b": summary_340b.get("total_review_queue_count", ""),
        "reviewed_after_human_candidate_count_340d": summary_340d.get("final_reviewed_after_human_candidate_count", ""),
        "reviewed_after_human_total_count_340e": summary_340e.get("reviewed_after_human_total_count", ""),
        "client_preview_core_metric_count_340f": summary_340f.get("client_preview_core_metric_count", ""),
        "audited_core_metric_count_340g": summary_340g.get("audited_core_metric_count", ""),
        "duplicate_issue_count_340g": summary_340g.get("duplicate_issue_count", ""),
        "unit_issue_count_340g": summary_340g.get("unit_issue_count", ""),
        "missing_source_trace_count_340g": summary_340g.get("missing_source_trace_count", ""),
        "unsafe_claim_count_340g": summary_340g.get("unsafe_claim_count", ""),
        "no_write_back": True,
        "no_write_back_proof_passed": no_write_back_proof_passed,
        "qa_fail_count": qa_fail_count,
        "decision": decision,
        "output_workbook_path": str(output_dir / "human_reviewed_client_preview_milestone_341a.xlsx"),
    }

    manifest = {
        "task": "341A_human_reviewed_client_preview_milestone_package",
        "human_review_340b_dir": str(human_review_340b_dir),
        "human_review_apply_340c_dir": str(human_review_apply_340c_dir),
        "full_human_review_apply_340d_dir": str(full_human_review_apply_340d_dir),
        "post_human_review_340e_dir": str(post_human_review_340e_dir),
        "client_preview_340f_dir": str(client_preview_340f_dir),
        "client_preview_audit_340g_dir": str(client_preview_audit_340g_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / "human_reviewed_client_preview_milestone_341a_summary.json"),
            "manifest_json": str(output_dir / "human_reviewed_client_preview_milestone_341a_manifest.json"),
            "qa_json": str(output_dir / "human_reviewed_client_preview_milestone_341a_qa.json"),
            "report_md": str(output_dir / "human_reviewed_client_preview_milestone_341a_report.md"),
            "workbook_xlsx": str(output_dir / "human_reviewed_client_preview_milestone_341a.xlsx"),
        },
        "files_read": files_read,
    }

    qa_json = {
        "qa_fail_count": qa_fail_count,
        "checks": checks,
        "upstream_input_hashes_before": input_hashes_before,
        "upstream_input_hashes_after": input_hashes_after,
    }

    workbook_sheets = {
        "00_README": _build_readme_df(),
        "01_MILESTONE_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_PIPELINE_STAGES": _build_pipeline_stages_df(),
        "03_KEY_COUNTS": _build_key_counts_df(summary_340b, summary_340c, summary_340d, summary_340e, summary_340f, summary_340g),
        "04_CLIENT_PREVIEW_AUDIT": _build_client_preview_audit_df(summary_340f, summary_340g),
        "05_OUTPUT_ARTIFACTS": _build_output_artifacts_df(human_review_340b_dir, human_review_apply_340c_dir, full_human_review_apply_340d_dir, post_human_review_340e_dir, client_preview_340f_dir, client_preview_audit_340g_dir),
        "06_REMAINING_RISKS": _build_remaining_risks_df(),
        "07_DEMO_RUNBOOK": _build_demo_runbook_df(),
        "08_NEXT_STEP_ROADMAP": _build_next_step_roadmap_df(),
        "09_NO_WRITE_BACK_PROOF": _build_no_apply_proof_df(no_apply_proof_json),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_apply_proof_json,
        "workbook_sheets": workbook_sheets,
    }
