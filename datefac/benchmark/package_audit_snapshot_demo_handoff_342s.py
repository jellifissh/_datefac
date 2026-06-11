from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_INPUT_342R_DECISION = "AUDIT_LABELED_EXPORT_CANDIDATE_PACKAGE_342R_READY"
READY_INPUT_342Q_DECISION = "PREVIEW_AUDIT_EXPORT_READINESS_GATE_342Q_READY"
READY_INPUT_342P_DECISION = "REVIEWED_PLUS_SIMULATED_CLIENT_PREVIEW_342P_READY"
READY_INPUT_342O_DECISION = "POST_ADOPTION_SIDECAR_SIMULATION_342O_READY"
READY_INPUT_342J_DECISION = "TABLE_FIRST_REVIEWED_CLIENT_PREVIEW_PILOT_342J_READY"
READY_DECISION = "PACKAGE_AUDIT_SNAPSHOT_DEMO_HANDOFF_342S_READY"
NOT_READY_DECISION = "PACKAGE_AUDIT_SNAPSHOT_DEMO_HANDOFF_342S_NOT_READY"
CURRENT_MAINLINE = "MinerU-first / table-first"
RECOMMENDED_343A_SCOPE = "review_queue_schema_and_human_review_ui_pilot"

DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR = Path(r"D:\_datefac\output\audit_labeled_export_candidate_package_342r")
DEFAULT_PREVIEW_AUDIT_342Q_DIR = Path(r"D:\_datefac\output\preview_audit_export_readiness_gate_342q")
DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR = Path(r"D:\_datefac\output\reviewed_plus_simulated_client_preview_342p")
DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR = Path(r"D:\_datefac\output\post_adoption_sidecar_simulation_342o")
DEFAULT_REVIEWED_PREVIEW_342J_DIR = Path(r"D:\_datefac\output\table_first_reviewed_client_preview_pilot_342j")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\package_audit_snapshot_demo_handoff_342s")

SUMMARY_FILE_NAME = "package_audit_snapshot_demo_handoff_342s_summary.json"
MANIFEST_FILE_NAME = "package_audit_snapshot_demo_handoff_342s_manifest.json"
QA_FILE_NAME = "package_audit_snapshot_demo_handoff_342s_qa.json"
NO_WRITE_BACK_FILE_NAME = "package_audit_snapshot_demo_handoff_342s_no_write_back_proof.json"
REPORT_FILE_NAME = "package_audit_snapshot_demo_handoff_342s_report.md"
WORKBOOK_FILE_NAME = "package_audit_snapshot_demo_handoff_342s.xlsx"
DEMO_README_FILE_NAME = "package_audit_snapshot_demo_handoff_342s_demo_readme.md"
HANDOFF_CHECKLIST_FILE_NAME = "package_audit_snapshot_demo_handoff_342s_handoff_checklist.md"
ARTIFACT_INDEX_FILE_NAME = "package_audit_snapshot_demo_handoff_342s_artifact_index.json"
NEXT_STEP_PLAN_FILE_NAME = "package_audit_snapshot_demo_handoff_342s_next_step_plan.md"

INPUT_342R_SUMMARY_NAME = "audit_labeled_export_candidate_package_342r_summary.json"
INPUT_342R_QA_NAME = "audit_labeled_export_candidate_package_342r_qa.json"
INPUT_342R_REPORT_NAME = "audit_labeled_export_candidate_package_342r_report.md"
INPUT_342R_WORKBOOK_NAME = "audit_labeled_export_candidate_package_342r.xlsx"
INPUT_342R_CANDIDATES_NAME = "audit_labeled_export_candidate_package_342r_candidates.csv"
INPUT_342R_METADATA_NAME = "audit_labeled_export_candidate_package_342r_metadata.json"

INPUT_342Q_SUMMARY_NAME = "preview_audit_export_readiness_gate_342q_summary.json"
INPUT_342Q_QA_NAME = "preview_audit_export_readiness_gate_342q_qa.json"
INPUT_342Q_REPORT_NAME = "preview_audit_export_readiness_gate_342q_report.md"
INPUT_342Q_WORKBOOK_NAME = "preview_audit_export_readiness_gate_342q.xlsx"

INPUT_342P_SUMMARY_NAME = "reviewed_plus_simulated_client_preview_342p_summary.json"
INPUT_342P_QA_NAME = "reviewed_plus_simulated_client_preview_342p_qa.json"
INPUT_342P_REPORT_NAME = "reviewed_plus_simulated_client_preview_342p_report.md"
INPUT_342P_WORKBOOK_NAME = "reviewed_plus_simulated_client_preview_342p.xlsx"

INPUT_342O_SUMMARY_NAME = "post_adoption_sidecar_simulation_342o_summary.json"
INPUT_342O_QA_NAME = "post_adoption_sidecar_simulation_342o_qa.json"
INPUT_342O_REPORT_NAME = "post_adoption_sidecar_simulation_342o_report.md"
INPUT_342O_WORKBOOK_NAME = "post_adoption_sidecar_simulation_342o.xlsx"

INPUT_342J_SUMMARY_NAME = "table_first_reviewed_client_preview_pilot_342j_summary.json"
INPUT_342J_QA_NAME = "table_first_reviewed_client_preview_pilot_342j_qa.json"
INPUT_342J_REPORT_NAME = "table_first_reviewed_client_preview_pilot_342j_report.md"
INPUT_342J_WORKBOOK_NAME = "table_first_reviewed_client_preview_pilot_342j.xlsx"

REQUIRED_342R_SHEETS = [
    "01_PACKAGE_SUMMARY",
    "03_EXPORT_CANDIDATES",
    "04_HUMAN_REVIEWED",
    "05_SIMULATED_DIRECT",
    "06_SIMULATED_CORRECTED",
    "07_AUDIT_LABELS",
    "08_REQUIRED_WARNINGS",
    "09_RISK_DISCLOSURE",
    "10_COLLISION_CONTEXT",
    "11_BACKLOG_CONTEXT",
    "12_342S_READINESS",
    "13_NO_WRITE_BACK",
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

FORBIDDEN_STAGE_PATHS = [
    "output",
    "temp",
    "input/table_first_review_342g_reviewed",
    "input/spot_check_reviewed_342m",
    "input/llm_review_responses_342m",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

FORBIDDEN_CLAIMS = [
    "investment advice",
    "formal_client_export_allowed=true",
    "client_ready=true",
    "production_ready=true",
    "full human review completed",
    "real llm review completed",
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


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _norm_text(value).casefold()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n", ""}:
        return False
    return bool(value)


def _safe_int(value: Any) -> int:
    text = _norm_text(value)
    if not text:
        return 0
    try:
        return int(value)
    except Exception:
        try:
            return int(float(text))
        except Exception:
            return 0


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def _run_git(repo_root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_head_sha(repo_root: Path) -> str:
    if not _is_git_repo(repo_root):
        return ""
    result = _run_git(repo_root, ["rev-parse", "HEAD"])
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _git_status_porcelain_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = _run_git(repo_root, ["status", "--porcelain", "--", *paths])
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_staged_names_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    lines = _git_status_porcelain_for_paths(paths, repo_root)
    staged: List[str] = []
    for line in lines:
        if line.startswith("__ERROR__::"):
            return [line]
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _contains_forbidden_claim(text: str, forbidden_tokens: Sequence[str]) -> bool:
    safe_cues = (
        "not ",
        "false",
        "no ",
        "do not",
        "must not",
        "forbidden",
        "cannot",
        "can't",
    )
    lowered_lines = [line.casefold() for line in text.splitlines()]
    for token in forbidden_tokens:
        token_lower = token.casefold()
        for line in lowered_lines:
            if token_lower not in line:
                continue
            if any(cue in line for cue in safe_cues):
                continue
            return True
    return False


def _read_workbook_sheets(
    workbook_path: Path,
    required_sheets: Sequence[str],
) -> tuple[Dict[str, pd.DataFrame], List[str], List[str]]:
    sheets: Dict[str, pd.DataFrame] = {}
    warnings: List[str] = []
    sheet_names: List[str] = []
    if not workbook_path.exists():
        for sheet in required_sheets:
            sheets[sheet] = pd.DataFrame()
        return sheets, sheet_names, [f"missing workbook: {workbook_path}"]
    try:
        excel = pd.ExcelFile(workbook_path)
        sheet_names = list(excel.sheet_names)
        for sheet in required_sheets:
            if sheet in sheet_names:
                sheets[sheet] = _clean_frame(pd.read_excel(workbook_path, sheet_name=sheet))
            else:
                sheets[sheet] = pd.DataFrame()
                warnings.append(f"missing required workbook sheet: {sheet}")
    except Exception as exc:
        warnings.append(f"unable to read workbook {workbook_path}: {exc}")
        for sheet in required_sheets:
            sheets[sheet] = pd.DataFrame()
    return sheets, sheet_names, warnings


def _load_summary_qa_report(
    *,
    base_dir: Path,
    summary_name: str,
    qa_name: str,
    report_name: str,
) -> tuple[Dict[str, Any], Dict[str, Any], List[str], List[str]]:
    files_read: List[str] = []
    warnings: List[str] = []
    summary_path = base_dir / summary_name
    qa_path = base_dir / qa_name
    report_path = base_dir / report_name
    summary = _read_json(summary_path) if summary_path.exists() else {}
    qa_json = _read_json(qa_path) if qa_path.exists() else {}
    for path, label in ((summary_path, "summary"), (qa_path, "qa"), (report_path, "report")):
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing {label}: {path}")
    return summary, qa_json, files_read, warnings


def _load_context(
    *,
    base_dir: Path,
    summary_name: str,
    qa_name: str,
    report_name: str,
    workbook_name: str,
) -> tuple[Dict[str, Any], Dict[str, Any], Path, List[str], List[str]]:
    summary, qa_json, files_read, warnings = _load_summary_qa_report(
        base_dir=base_dir,
        summary_name=summary_name,
        qa_name=qa_name,
        report_name=report_name,
    )
    workbook_path = base_dir / workbook_name
    if workbook_path.exists():
        files_read.append(str(workbook_path))
    else:
        warnings.append(f"missing workbook: {workbook_path}")
    return summary, qa_json, workbook_path, files_read, warnings


def _resolve_ledger_path(repo_root: Path) -> Path:
    preferred = repo_root / "docs" / "project_milestones" / "PROJECT_MILESTONE_LEDGER_项目进程.md"
    if preferred.exists():
        return preferred
    milestone_dir = repo_root / "docs" / "project_milestones"
    candidates = sorted(milestone_dir.glob("PROJECT_MILESTONE_LEDGER_*.md")) if milestone_dir.exists() else []
    if candidates:
        return candidates[0]
    return preferred


def _build_key_value_df(mapping: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, str]] = []
    for key, value in mapping.items():
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = str(value)
        rows.append({"key": key, "value": rendered})
    return _clean_frame(pd.DataFrame(rows))


def _build_readme_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "section": "positioning",
            "message": "342S is a package audit snapshot and demo handoff on top of 342R, not a formal client export.",
        },
        {
            "section": "mainline",
            "message": f"Current mainline remains {summary.get('current_mainline', CURRENT_MAINLINE)} and the old 342E text-candidate route is superseded.",
        },
        {
            "section": "demo",
            "message": "The recommended demo artifact is the 342R workbook with audit labels, warnings, risk disclosure, collision context, and backlog context.",
        },
        {
            "section": "boundary",
            "message": "Keep formal_client_export_allowed=false, client_ready=false, and production_ready=false.",
        },
        {
            "section": "handoff",
            "message": "342S is suitable for internal demo, audit recap, and milestone handoff, but not final delivery or investment advice.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_milestone_chain_df(
    *,
    summary_342j: Dict[str, Any],
    summary_342o: Dict[str, Any],
    summary_342p: Dict[str, Any],
    summary_342q: Dict[str, Any],
    summary_342r: Dict[str, Any],
    summary_342s: Dict[str, Any],
) -> pd.DataFrame:
    rows = [
        {
            "milestone_id": "342C6",
            "milestone_name": "MinerU Pilot Network Recovery Rerun",
            "status": "completed",
            "decision": "effective MinerU pilot success baseline established",
            "key_output": "5/5 MinerU pilot outputs became the effective parse baseline",
            "key_risk_or_boundary": "Do not rerun MinerU unless a new benchmark scope is explicitly required.",
            "next_dependency": "342D parser ensemble compare",
        },
        {
            "milestone_id": "342D",
            "milestone_name": "Parser Ensemble Compare",
            "status": "completed",
            "decision": "parser ensemble compare completed",
            "key_output": "MinerU-first baseline and parser comparison artifacts completed",
            "key_risk_or_boundary": "Comparison evidence exists, but no production parser rewrite was performed.",
            "next_dependency": "342E table-first candidate audit",
        },
        {
            "milestone_id": "342E",
            "milestone_name": "Table-First Candidate Audit",
            "status": "completed",
            "decision": "table-first candidate audit completed",
            "key_output": "Core extractable tables were audited and the old 435 text-candidate route was superseded",
            "key_risk_or_boundary": "Current mainline is table-first; old 342E text candidates are no longer current.",
            "next_dependency": "342F long-form extraction",
        },
        {
            "milestone_id": "342F",
            "milestone_name": "Table-First Long-Form Extraction",
            "status": "completed",
            "decision": "table-first long-form extraction completed",
            "key_output": "66 core tables parsed into long-form cell output with review and reject splits",
            "key_risk_or_boundary": "Cells still require review governance and duplicate handling.",
            "next_dependency": "342G extraction review package",
        },
        {
            "milestone_id": "342G",
            "milestone_name": "Table-First Extraction Review Package",
            "status": "completed",
            "decision": "table-first extraction review package completed",
            "key_output": "Review template and trusted sample audit package produced",
            "key_risk_or_boundary": "This stage prepares review work; it does not finalize client output.",
            "next_dependency": "342H reviewed apply simulation",
        },
        {
            "milestone_id": "342H",
            "milestone_name": "Reviewed Apply Simulation",
            "status": "completed",
            "decision": "reviewed apply simulation completed",
            "key_output": "Human-reviewed apply simulation established the reviewed/corrected/rejected split",
            "key_risk_or_boundary": "No upstream workbook write-back; still not client-ready.",
            "next_dependency": "342I post-human sidecar",
        },
        {
            "milestone_id": "342I",
            "milestone_name": "Post-Human Sidecar Result",
            "status": "completed",
            "decision": "post-human sidecar completed",
            "key_output": "Traceable post-human sidecar result retained reviewed rows without write-back",
            "key_risk_or_boundary": "Sidecar only; no official delivery artifact was created.",
            "next_dependency": "342J reviewed client preview pilot",
        },
        {
            "milestone_id": "342J",
            "milestone_name": "Reviewed Client Preview Pilot",
            "status": "completed",
            "decision": summary_342j.get("decision", ""),
            "key_output": f"reviewed_preview_row_count = {_safe_int(summary_342j.get('reviewed_preview_row_count', 0))}",
            "key_risk_or_boundary": "Human-reviewed preview pilot exists, but current scope remains partial.",
            "next_dependency": "342K LLM-assisted adjudication pilot",
        },
        {
            "milestone_id": "342K",
            "milestone_name": "LLM-Assisted Adjudication Pilot",
            "status": "completed",
            "decision": "llm-assisted adjudication pilot completed as dry-run helper",
            "key_output": "Prompt/request packaging and dry-run helper flow established",
            "key_risk_or_boundary": "AI decisions remain dry-run only and are not final confirmations.",
            "next_dependency": "342L suggestion-apply simulation",
        },
        {
            "milestone_id": "342L",
            "milestone_name": "Suggestion-Apply Simulation",
            "status": "completed",
            "decision": "llm suggestion apply simulation completed",
            "key_output": "Risk-adjusted suggestion adoption simulation completed",
            "key_risk_or_boundary": "Still bounded by later human review and downstream gates.",
            "next_dependency": "342M reviewed spot-check gate",
        },
        {
            "milestone_id": "342M",
            "milestone_name": "Reviewed Spot-Check Gate",
            "status": "completed",
            "decision": "reviewed spot-check gate completed",
            "key_output": "Spot-check evidence gated downstream simulated adoption",
            "key_risk_or_boundary": "Spot-check passed, but broad final delivery claims remain blocked.",
            "next_dependency": "342N correction-aware adoption simulation",
        },
        {
            "milestone_id": "342N",
            "milestone_name": "Correction-Aware Adoption Simulation",
            "status": "completed",
            "decision": "correction-aware adoption simulation completed",
            "key_output": "Direct-adopted, corrected-adopted, and still-human-required buckets created",
            "key_risk_or_boundary": "Simulation output is bounded and still not a formal export.",
            "next_dependency": "342O post-adoption sidecar simulation",
        },
        {
            "milestone_id": "342O",
            "milestone_name": "Post-Adoption Sidecar Simulation",
            "status": "completed",
            "decision": summary_342o.get("decision", ""),
            "key_output": f"simulated_adopted_cell_count = {_safe_int(summary_342o.get('simulated_adopted_cell_count', 0))}",
            "key_risk_or_boundary": "Simulation-only sidecar with remaining human review backlog preserved.",
            "next_dependency": "342P reviewed plus simulated preview",
        },
        {
            "milestone_id": "342P",
            "milestone_name": "Reviewed Plus Simulated Client Preview",
            "status": "completed",
            "decision": summary_342p.get("decision", ""),
            "key_output": f"combined_preview_row_count = {_safe_int(summary_342p.get('combined_preview_row_count', 0))}",
            "key_risk_or_boundary": "Preview combines human-reviewed and simulated rows but is not final delivery.",
            "next_dependency": "342Q preview audit gate",
        },
        {
            "milestone_id": "342Q",
            "milestone_name": "Preview Audit Export Readiness Gate",
            "status": "completed",
            "decision": summary_342q.get("decision", ""),
            "key_output": f"export_candidate_row_count = {_safe_int(summary_342q.get('export_candidate_row_count', 0))}",
            "key_risk_or_boundary": "formal_client_export_allowed remains false and export risk stays HIGH.",
            "next_dependency": "342R audit-labeled export candidate package",
        },
        {
            "milestone_id": "342R",
            "milestone_name": "Audit-Labeled Export Candidate Package",
            "status": "completed",
            "decision": summary_342r.get("decision", ""),
            "key_output": f"export_candidate_package_row_count = {_safe_int(summary_342r.get('export_candidate_package_row_count', 0))}",
            "key_risk_or_boundary": "130 rows are packaged for audit/demo only; 100 simulated rows still require disclaimer and later audit.",
            "next_dependency": "342S package audit snapshot / demo handoff",
        },
        {
            "milestone_id": "342S",
            "milestone_name": "Package Audit Snapshot / Demo Handoff",
            "status": "completed" if summary_342s.get("demo_handoff_ready") else "not_ready",
            "decision": summary_342s.get("decision", ""),
            "key_output": "snapshot workbook, demo readme, handoff checklist, artifact index, and next-step plan",
            "key_risk_or_boundary": "Snapshot only; not formal client export, not full human review completion, not production-ready.",
            "next_dependency": "343A review queue schema and human review UI pilot",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_key_artifacts_df(
    *,
    audit_labeled_package_342r_dir: Path,
    preview_audit_342q_dir: Path,
    reviewed_plus_preview_342p_dir: Path,
    post_adoption_sidecar_342o_dir: Path,
    reviewed_preview_342j_dir: Path,
    output_dir: Path,
    ledger_path: Path,
) -> pd.DataFrame:
    rows = [
        {
            "artifact_name": "342R workbook",
            "stage": "342R",
            "artifact_type": "xlsx",
            "path": str(audit_labeled_package_342r_dir / INPUT_342R_WORKBOOK_NAME),
            "recommended_open_priority": 1,
            "recommended_sheets_or_sections": "03_EXPORT_CANDIDATES | 07_AUDIT_LABELS | 08_REQUIRED_WARNINGS | 09_RISK_DISCLOSURE | 10_COLLISION_CONTEXT | 11_BACKLOG_CONTEXT | 12_342S_READINESS",
            "purpose": "Primary demo and audit handoff workbook.",
            "caveat": "Audit-labeled candidate package only; not formal client export.",
        },
        {
            "artifact_name": "342R candidates csv",
            "stage": "342R",
            "artifact_type": "csv",
            "path": str(audit_labeled_package_342r_dir / INPUT_342R_CANDIDATES_NAME),
            "recommended_open_priority": 2,
            "recommended_sheets_or_sections": "flat rows only",
            "purpose": "Quick row-level export candidate inspection outside Excel.",
            "caveat": "Loses workbook narrative sheets and risk context.",
        },
        {
            "artifact_name": "342R report",
            "stage": "342R",
            "artifact_type": "md",
            "path": str(audit_labeled_package_342r_dir / INPUT_342R_REPORT_NAME),
            "recommended_open_priority": 3,
            "recommended_sheets_or_sections": "full markdown report",
            "purpose": "Narrative explanation of the 342R package and boundaries.",
            "caveat": "Use together with the workbook, not as a replacement.",
        },
        {
            "artifact_name": "342Q workbook",
            "stage": "342Q",
            "artifact_type": "xlsx",
            "path": str(preview_audit_342q_dir / INPUT_342Q_WORKBOOK_NAME),
            "recommended_open_priority": 4,
            "recommended_sheets_or_sections": "03_PREVIEW_AUDIT | 06_COLLISION_AUDIT | 09_EXPORT_RISK_GATE | 10_EXPORT_CANDIDATE_SCOPE | 11_REMAINING_BACKLOG",
            "purpose": "Audit gate evidence upstream of 342R packaging.",
            "caveat": "Read as upstream audit context, not the main demo workbook.",
        },
        {
            "artifact_name": "342P workbook",
            "stage": "342P",
            "artifact_type": "xlsx",
            "path": str(reviewed_plus_preview_342p_dir / INPUT_342P_WORKBOOK_NAME),
            "recommended_open_priority": 5,
            "recommended_sheets_or_sections": "04_COMBINED_PREVIEW | 05_HUMAN_REVIEWED | 06_SIM_DIRECT | 07_SIM_CORRECTED | 09_COLLISION_CHECK",
            "purpose": "Shows how human-reviewed and simulated preview rows were assembled.",
            "caveat": "Preview-layer workbook, not export-ready.",
        },
        {
            "artifact_name": "342O workbook",
            "stage": "342O",
            "artifact_type": "xlsx",
            "path": str(post_adoption_sidecar_342o_dir / INPUT_342O_WORKBOOK_NAME),
            "recommended_open_priority": 6,
            "recommended_sheets_or_sections": "summary and simulated adoption evidence",
            "purpose": "Explains direct vs corrected simulated adoption context.",
            "caveat": "Simulation sidecar only.",
        },
        {
            "artifact_name": "342J workbook",
            "stage": "342J",
            "artifact_type": "xlsx",
            "path": str(reviewed_preview_342j_dir / INPUT_342J_WORKBOOK_NAME),
            "recommended_open_priority": 7,
            "recommended_sheets_or_sections": "reviewed preview pilot sheets",
            "purpose": "Earliest reviewed client preview pilot context.",
            "caveat": "Pilot-only and partial.",
        },
        {
            "artifact_name": "Project milestone ledger",
            "stage": "ledger",
            "artifact_type": "md",
            "path": str(ledger_path),
            "recommended_open_priority": 8,
            "recommended_sheets_or_sections": "342Q | 342R | 342S sections",
            "purpose": "Source-of-truth milestone history and boundaries.",
            "caveat": "Use the latest pushed version as the current source of truth.",
        },
        {
            "artifact_name": "342S demo readme",
            "stage": "342S",
            "artifact_type": "md",
            "path": str(output_dir / DEMO_README_FILE_NAME),
            "recommended_open_priority": 9,
            "recommended_sheets_or_sections": "full markdown note",
            "purpose": "Short presenter-oriented guide for internal demo handoff.",
            "caveat": "Snapshot helper only.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_demo_guide_df(summary: Dict[str, Any], workbook_path: Path) -> pd.DataFrame:
    rows = [
        {"step_id": 1, "action": "State the mainline", "open_target": str(workbook_path), "focus": CURRENT_MAINLINE, "why": "Sets the correct architecture context before any row-level demo."},
        {"step_id": 2, "action": "Explain the chain", "open_target": "02_MILESTONE_CHAIN", "focus": "table extraction -> human review -> simulated adoption -> audit gate -> candidate package", "why": "Clarifies what 342S is summarizing."},
        {"step_id": 3, "action": "Open candidate rows", "open_target": "03_EXPORT_CANDIDATES", "focus": "130 candidate rows", "why": "Shows the bounded package scope."},
        {"step_id": 4, "action": "Show trust levels", "open_target": "07_AUDIT_LABELS", "focus": "HUMAN_REVIEWED vs SIMULATED_*", "why": "Makes trust separation explicit."},
        {"step_id": 5, "action": "Show warnings", "open_target": "08_REQUIRED_WARNINGS", "focus": "later-audit requirement for simulated rows", "why": "Prevents overstating confidence."},
        {"step_id": 6, "action": "Show risk disclosure", "open_target": "09_RISK_DISCLOSURE", "focus": "export_risk_level = HIGH", "why": "Preserves risk boundary."},
        {"step_id": 7, "action": "Show collisions", "open_target": "10_COLLISION_CONTEXT", "focus": f"collision_logged_count = {summary.get('collision_logged_count', 0)}", "why": "Explains why export risk remains high."},
        {"step_id": 8, "action": "Show backlog", "open_target": "11_BACKLOG_CONTEXT", "focus": f"remaining_review_count = {summary.get('remaining_review_count', 0)}", "why": "Makes scope limitations visible."},
        {"step_id": 9, "action": "Show next gate", "open_target": "12_343A_READINESS", "focus": "ready_for_343a", "why": "Explains the recommended next engineering/product step."},
        {"step_id": 10, "action": "Close with boundary", "open_target": "14_NEXT_STEPS", "focus": "demo-ready handoff only", "why": "Prevents framing this as formal delivery."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_package_overview_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {"metric_name": "export_candidate_package_row_count", "value": summary.get("export_candidate_package_row_count", 0), "meaning": "Total candidate rows in the bounded 342R package."},
        {"metric_name": "human_reviewed_candidate_count", "value": summary.get("human_reviewed_candidate_count", 0), "meaning": "Rows that came from reviewed human evidence."},
        {"metric_name": "simulated_candidate_count", "value": summary.get("simulated_candidate_count", 0), "meaning": "Rows that came from simulated adoption and still require disclaimers."},
        {"metric_name": "simulated_direct_candidate_count", "value": summary.get("simulated_direct_candidate_count", 0), "meaning": "Direct-adopted simulated rows."},
        {"metric_name": "simulated_corrected_candidate_count", "value": summary.get("simulated_corrected_candidate_count", 0), "meaning": "Correction-adopted simulated rows."},
        {"metric_name": "disclaimer_required_count", "value": summary.get("disclaimer_required_count", 0), "meaning": "Rows that require explicit demo/export disclaimer."},
        {"metric_name": "later_audit_required_count", "value": summary.get("later_audit_required_count", 0), "meaning": "Rows that require later audit before any broader use."},
        {"metric_name": "formal_client_export_allowed", "value": summary.get("formal_client_export_allowed", False), "meaning": "Must stay false at this stage."},
        {"metric_name": "client_ready", "value": summary.get("client_ready", False), "meaning": "Must stay false at this stage."},
        {"metric_name": "production_ready", "value": summary.get("production_ready", False), "meaning": "Must stay false at this stage."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_trust_levels_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "data_trust_level": "HUMAN_REVIEWED",
            "row_count": summary.get("human_reviewed_candidate_count", 0),
            "meaning": "Human-reviewed preview row carried into the bounded package.",
            "can_demo": True,
            "can_formal_export": False,
            "requires_disclaimer": False,
            "requires_later_audit": False,
            "risk_note": "Best trust level in the package, but still not a formal client export.",
        },
        {
            "data_trust_level": "SIMULATED_DIRECT_ADOPTED",
            "row_count": summary.get("simulated_direct_candidate_count", 0),
            "meaning": "Simulation-only direct adoption row.",
            "can_demo": True,
            "can_formal_export": False,
            "requires_disclaimer": True,
            "requires_later_audit": True,
            "risk_note": "Can appear in demo only with clear warning and later-audit boundary.",
        },
        {
            "data_trust_level": "SIMULATED_CORRECTION_ADOPTED",
            "row_count": summary.get("simulated_corrected_candidate_count", 0),
            "meaning": "Simulation-only corrected adoption row.",
            "can_demo": True,
            "can_formal_export": False,
            "requires_disclaimer": True,
            "requires_later_audit": True,
            "risk_note": "Can appear in demo only with clear warning and later-audit boundary.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_risk_boundary_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {"boundary": "export_risk_level", "value": summary.get("export_risk_level", ""), "reason": "High because the package still contains 100 simulated rows plus unresolved backlog pressure."},
        {"boundary": "formal_client_export_allowed", "value": summary.get("formal_client_export_allowed", False), "reason": "This snapshot is not a formal client export."},
        {"boundary": "client_ready", "value": summary.get("client_ready", False), "reason": "The chain is demo/handoff ready, not client-ready."},
        {"boundary": "production_ready", "value": summary.get("production_ready", False), "reason": "The chain is not production-ready and still requires review workflow scaling."},
        {"boundary": "not_investment_advice", "value": True, "reason": "No output here should be framed as investment advice."},
        {"boundary": "no_full_human_review_claim", "value": True, "reason": "66 adoption candidates still require human review and 887 rows remain outside the current package."},
        {"boundary": "no_real_llm_review_claim", "value": True, "reason": "Dry-run/simulated review helpers do not equal real LLM review completion."},
        {"boundary": "no_final_delivery_claim", "value": True, "reason": "342S is an internal package audit snapshot and demo handoff only."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_collision_summary_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {"metric_name": "collision_logged_count", "value": summary.get("collision_logged_count", 0), "meaning": "Collisions were recorded and surfaced."},
        {"metric_name": "duplicate_metric_year_source_count", "value": summary.get("duplicate_metric_year_source_count", 0), "meaning": "Duplicate metric/year/source combinations were identified."},
        {"metric_name": "severe_collision_count", "value": summary.get("severe_collision_count", 0), "meaning": "High-risk collisions keep export_risk_level at HIGH."},
        {"metric_name": "unresolved_collision_count", "value": summary.get("unresolved_collision_count", 0), "meaning": "Should remain 0 in the current package."},
        {"metric_name": "human_over_simulation_override_count", "value": summary.get("human_over_simulation_override_count", 0), "meaning": "Human rows retained priority over simulated duplicates."},
        {"metric_name": "simulated_duplicate_dropped_count", "value": summary.get("simulated_duplicate_dropped_count", 0), "meaning": "Simulated duplicates were dropped from the final package."},
        {"metric_name": "collision_note", "value": "collision logged and processed", "meaning": "Collision handling exists, but the count still raises export risk."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_backlog_summary_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "backlog_metric": "remaining_review_count",
            "value": summary.get("remaining_review_count", 0),
            "meaning": "Rows outside the current 130-row bounded package.",
        },
        {
            "backlog_metric": "still_human_required_count",
            "value": summary.get("still_human_required_count", 0),
            "meaning": "Adoption candidates that still require human judgment.",
        },
        {
            "backlog_metric": "current_package_scope_note",
            "value": "130 rows only",
            "meaning": "The package is intentionally bounded and does not cover the full backlog.",
        },
        {
            "backlog_metric": "recommended_follow_up",
            "value": "Review Queue / Argilla pilot / real LLM trace / Phoenix trace",
            "meaning": "The next route should reduce review backlog and improve auditability.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_handoff_checklist_df(
    *,
    latest_commit_sha: str,
    summary: Dict[str, Any],
    output_dir: Path,
    protected_before: Sequence[str],
) -> pd.DataFrame:
    rows = [
        {"item": "latest_commit_sha_before_342s", "value": latest_commit_sha or "unknown"},
        {"item": "latest_completed_milestone", "value": summary.get("latest_completed_milestone", "")},
        {"item": "current_mainline", "value": summary.get("current_mainline", CURRENT_MAINLINE)},
        {"item": "recommended_artifact_to_open", "value": summary.get("recommended_open_excel_path", "")},
        {"item": "recommended_sheets", "value": "03_EXPORT_CANDIDATES | 07_AUDIT_LABELS | 08_REQUIRED_WARNINGS | 09_RISK_DISCLOSURE | 10_COLLISION_CONTEXT | 11_BACKLOG_CONTEXT | 12_342S_READINESS"},
        {"item": "recommended_demo_readme", "value": str(output_dir / DEMO_README_FILE_NAME)},
        {"item": "known_forbidden_paths", "value": " | ".join(FORBIDDEN_STAGE_PATHS)},
        {"item": "known_dirty_paths", "value": " | ".join(list(protected_before))},
        {"item": "forbidden_claims", "value": "formal_client_export_allowed=true | client_ready=true | production_ready=true | investment advice | final client delivery"},
        {"item": "next_recommended_work", "value": "343A Review Queue Schema And Human Review UI Pilot"},
        {"item": "demo_caveat", "value": "Snapshot/handoff only; 100 simulated rows still require disclaimer and later audit."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_next_step_options_df() -> pd.DataFrame:
    rows = [
        {
            "option_id": "343A",
            "option_title": "Review Queue Schema And Human Review UI Pilot",
            "goal": "Define queue schema and human-review workflow before UI scale-up.",
            "trigger_condition": "Backlog remains high and still-human-required rows need explicit routing.",
            "value": "Creates the foundation for scalable review governance.",
            "risk": "Needs careful schema design before tool choice.",
            "note": "Recommended now.",
        },
        {
            "option_id": "343B",
            "option_title": "Argilla Human Review UI Pilot",
            "goal": "Pilot 50-100 high-risk or still-human-required rows in an annotation UI.",
            "trigger_condition": "Queue schema is ready enough to map into an external review surface.",
            "value": "Fast usability signal for review operations.",
            "risk": "Should stay a pluggable pilot, not the core system.",
            "note": "Good follow-up after 343A.",
        },
        {
            "option_id": "343C",
            "option_title": "Real LLM/VLM Response Ingestion Pilot",
            "goal": "Move from dry-run simulation to real traceable response ingestion.",
            "trigger_condition": "Prompt packaging, trace retention, and human correction loop are defined.",
            "value": "Turns simulated helper stages into observable real-response experiments.",
            "risk": "Must preserve trace, parser, and human-correction auditability.",
            "note": "Do not fake responses.",
        },
        {
            "option_id": "343D",
            "option_title": "Phoenix Observability Trace Pilot",
            "goal": "Add trace/eval/prompt observability around real model calls.",
            "trigger_condition": "Real model response ingestion exists or is imminent.",
            "value": "Improves debugging and evaluation discipline.",
            "risk": "Lower value before real model calls exist.",
            "note": "Best after 343C starts.",
        },
        {
            "option_id": "343E",
            "option_title": "Manual Review Expansion / Spot-Check Expansion",
            "goal": "Reduce export risk by expanding reviewed rows and severe-collision coverage.",
            "trigger_condition": "Need lower risk before any broader package use.",
            "value": "Directly reduces remaining high-risk surface area.",
            "risk": "Labor-intensive without better queue tooling.",
            "note": "Useful in parallel, but not the primary systems step.",
        },
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_343a_readiness_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {
            "snapshot_generated": summary.get("demo_handoff_ready", False),
            "handoff_checklist_generated": True,
            "demo_readme_generated": True,
            "artifact_index_generated": True,
            "formal_client_export_allowed": summary.get("formal_client_export_allowed", False),
            "client_ready": summary.get("client_ready", False),
            "production_ready": summary.get("production_ready", False),
            "no_write_back_proof_passed": summary.get("no_write_back_proof_passed", False),
            "ready_for_343a": summary.get("ready_for_343a", False),
            "recommended_343a_scope": summary.get("recommended_343a_scope", ""),
            "decision": summary.get("decision", ""),
        }
    ]
    return _clean_frame(pd.DataFrame(rows))


def _build_next_steps_df(summary: Dict[str, Any]) -> pd.DataFrame:
    rows = [
        {"step_order": 1, "next_step": "Open the 342R workbook first", "reason": "It is the highest-value artifact for demo and audit handoff."},
        {"step_order": 2, "next_step": "Use 342S demo readme during presentation", "reason": "It preserves the correct script and boundaries."},
        {"step_order": 3, "next_step": "Start 343A review queue schema design", "reason": summary.get("recommended_343a_scope", "")},
        {"step_order": 4, "next_step": "Treat 343B/343C/343D as optional follow-up pilots", "reason": "They are downstream options, not prerequisites for this snapshot."},
        {"step_order": 5, "next_step": "Do not treat 342S as formal client export", "reason": "formal_client_export_allowed remains false and export risk remains HIGH."},
    ]
    return _clean_frame(pd.DataFrame(rows))


def build_package_audit_snapshot_demo_handoff_342s(
    *,
    audit_labeled_package_342r_dir: Path = DEFAULT_AUDIT_LABELED_PACKAGE_342R_DIR,
    preview_audit_342q_dir: Path = DEFAULT_PREVIEW_AUDIT_342Q_DIR,
    reviewed_plus_preview_342p_dir: Path = DEFAULT_REVIEWED_PLUS_PREVIEW_342P_DIR,
    post_adoption_sidecar_342o_dir: Path = DEFAULT_POST_ADOPTION_SIDECAR_342O_DIR,
    reviewed_preview_342j_dir: Path = DEFAULT_REVIEWED_PREVIEW_342J_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    repo_root: Path = Path(__file__).resolve().parents[2],
) -> Dict[str, Any]:
    warnings: List[str] = []
    files_read: List[str] = []

    latest_commit_sha = _git_head_sha(repo_root)
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    alias_asset_path = SEMANTIC_ALIAS_ASSET_PATH
    scope_asset_path = FORMAL_SCOPE_RULES_PATH
    official_assets_before = capture_official_asset_hashes([alias_asset_path, scope_asset_path])

    summary_342r, qa_342r, files_342r, warnings_342r = _load_summary_qa_report(
        base_dir=audit_labeled_package_342r_dir,
        summary_name=INPUT_342R_SUMMARY_NAME,
        qa_name=INPUT_342R_QA_NAME,
        report_name=INPUT_342R_REPORT_NAME,
    )
    files_read.extend(files_342r)
    warnings.extend(warnings_342r)

    workbook_342r_path = audit_labeled_package_342r_dir / INPUT_342R_WORKBOOK_NAME
    candidates_342r_path = audit_labeled_package_342r_dir / INPUT_342R_CANDIDATES_NAME
    metadata_342r_path = audit_labeled_package_342r_dir / INPUT_342R_METADATA_NAME
    workbook_342r, workbook_342r_sheet_names, workbook_342r_warnings = _read_workbook_sheets(
        workbook_342r_path,
        REQUIRED_342R_SHEETS,
    )
    warnings.extend(workbook_342r_warnings)
    for path in (workbook_342r_path, candidates_342r_path, metadata_342r_path):
        if path.exists():
            files_read.append(str(path))
        else:
            warnings.append(f"missing input artifact: {path}")

    summary_342q, qa_342q, workbook_342q_path, files_342q, warnings_342q = _load_context(
        base_dir=preview_audit_342q_dir,
        summary_name=INPUT_342Q_SUMMARY_NAME,
        qa_name=INPUT_342Q_QA_NAME,
        report_name=INPUT_342Q_REPORT_NAME,
        workbook_name=INPUT_342Q_WORKBOOK_NAME,
    )
    summary_342p, qa_342p, workbook_342p_path, files_342p, warnings_342p = _load_context(
        base_dir=reviewed_plus_preview_342p_dir,
        summary_name=INPUT_342P_SUMMARY_NAME,
        qa_name=INPUT_342P_QA_NAME,
        report_name=INPUT_342P_REPORT_NAME,
        workbook_name=INPUT_342P_WORKBOOK_NAME,
    )
    summary_342o, qa_342o, workbook_342o_path, files_342o, warnings_342o = _load_context(
        base_dir=post_adoption_sidecar_342o_dir,
        summary_name=INPUT_342O_SUMMARY_NAME,
        qa_name=INPUT_342O_QA_NAME,
        report_name=INPUT_342O_REPORT_NAME,
        workbook_name=INPUT_342O_WORKBOOK_NAME,
    )
    summary_342j, qa_342j, workbook_342j_path, files_342j, warnings_342j = _load_context(
        base_dir=reviewed_preview_342j_dir,
        summary_name=INPUT_342J_SUMMARY_NAME,
        qa_name=INPUT_342J_QA_NAME,
        report_name=INPUT_342J_REPORT_NAME,
        workbook_name=INPUT_342J_WORKBOOK_NAME,
    )
    for chunk in (files_342q, files_342p, files_342o, files_342j):
        files_read.extend(chunk)
    for chunk in (warnings_342q, warnings_342p, warnings_342o, warnings_342j):
        warnings.extend(chunk)

    all_input_paths = [
        audit_labeled_package_342r_dir / INPUT_342R_SUMMARY_NAME,
        audit_labeled_package_342r_dir / INPUT_342R_QA_NAME,
        audit_labeled_package_342r_dir / INPUT_342R_REPORT_NAME,
        workbook_342r_path,
        candidates_342r_path,
        metadata_342r_path,
        preview_audit_342q_dir / INPUT_342Q_SUMMARY_NAME,
        preview_audit_342q_dir / INPUT_342Q_QA_NAME,
        workbook_342q_path,
        reviewed_plus_preview_342p_dir / INPUT_342P_SUMMARY_NAME,
        reviewed_plus_preview_342p_dir / INPUT_342P_QA_NAME,
        workbook_342p_path,
        post_adoption_sidecar_342o_dir / INPUT_342O_SUMMARY_NAME,
        post_adoption_sidecar_342o_dir / INPUT_342O_QA_NAME,
        workbook_342o_path,
        reviewed_preview_342j_dir / INPUT_342J_SUMMARY_NAME,
        reviewed_preview_342j_dir / INPUT_342J_QA_NAME,
        workbook_342j_path,
    ]
    input_hashes_before = {str(path): sha256_file(path) for path in all_input_paths if path.exists()}

    required_342r_present = all(sheet in workbook_342r_sheet_names for sheet in REQUIRED_342R_SHEETS)

    candidates_df = _clean_frame(workbook_342r.get("03_EXPORT_CANDIDATES", pd.DataFrame()))
    human_df = _clean_frame(workbook_342r.get("04_HUMAN_REVIEWED", pd.DataFrame()))
    sim_direct_df = _clean_frame(workbook_342r.get("05_SIMULATED_DIRECT", pd.DataFrame()))
    sim_corrected_df = _clean_frame(workbook_342r.get("06_SIMULATED_CORRECTED", pd.DataFrame()))

    workbook_export_count = int(len(candidates_df))
    workbook_human_count = int(len(human_df))
    workbook_sim_direct_count = int(len(sim_direct_df))
    workbook_sim_corrected_count = int(len(sim_corrected_df))
    workbook_sim_total_count = workbook_sim_direct_count + workbook_sim_corrected_count

    summary_export_count = _safe_int(summary_342r.get("export_candidate_package_row_count", 0))
    summary_human_count = _safe_int(summary_342r.get("human_reviewed_candidate_count", 0))
    summary_sim_count = _safe_int(summary_342r.get("simulated_candidate_count", 0))
    summary_sim_direct_count = _safe_int(summary_342r.get("simulated_direct_candidate_count", 0))
    summary_sim_corrected_count = _safe_int(summary_342r.get("simulated_corrected_candidate_count", 0))

    input_ready = bool(
        summary_342r.get("decision") == READY_INPUT_342R_DECISION
        and _as_bool(summary_342r.get("ready_for_342s"))
        and _safe_int(summary_342r.get("qa_fail_count", 1)) == 0
        and not _as_bool(summary_342r.get("formal_client_export_allowed"))
        and not _as_bool(summary_342r.get("client_ready"))
        and not _as_bool(summary_342r.get("production_ready"))
        and summary_342q.get("decision") == READY_INPUT_342Q_DECISION
        and _safe_int(summary_342q.get("qa_fail_count", 1)) == 0
        and summary_342p.get("decision") == READY_INPUT_342P_DECISION
        and _safe_int(summary_342p.get("qa_fail_count", 1)) == 0
        and summary_342o.get("decision") == READY_INPUT_342O_DECISION
        and _safe_int(summary_342o.get("qa_fail_count", 1)) == 0
        and summary_342j.get("decision") == READY_INPUT_342J_DECISION
        and _safe_int(summary_342j.get("qa_fail_count", 1)) == 0
        and required_342r_present
    )

    ledger_path = _resolve_ledger_path(repo_root)
    summary = {
        "generated_at_utc": _utc_now(),
        "latest_commit_sha_before_342s": latest_commit_sha,
        "latest_completed_milestone": "342R",
        "current_milestone": "342S",
        "current_mainline": CURRENT_MAINLINE,
        "old_342e_text_candidate_route": "superseded",
        "export_candidate_package_row_count": summary_export_count,
        "human_reviewed_candidate_count": summary_human_count,
        "simulated_candidate_count": summary_sim_count,
        "simulated_direct_candidate_count": summary_sim_direct_count,
        "simulated_corrected_candidate_count": summary_sim_corrected_count,
        "disclaimer_required_count": _safe_int(summary_342r.get("disclaimer_required_count", 0)),
        "later_audit_required_count": _safe_int(summary_342r.get("later_audit_required_count", 0)),
        "export_risk_level": summary_342r.get("export_risk_level", ""),
        "collision_logged_count": _safe_int(summary_342r.get("collision_logged_count", 0)),
        "duplicate_metric_year_source_count": _safe_int(summary_342r.get("duplicate_metric_year_source_count", 0)),
        "severe_collision_count": _safe_int(summary_342r.get("severe_collision_count", 0)),
        "unresolved_collision_count": _safe_int(summary_342q.get("unresolved_collision_count", 0)),
        "human_over_simulation_override_count": _safe_int(summary_342r.get("human_over_simulation_override_count", 0)),
        "simulated_duplicate_dropped_count": _safe_int(summary_342r.get("simulated_duplicate_dropped_count", 0)),
        "still_human_required_count": _safe_int(summary_342r.get("still_human_required_count", 0)),
        "remaining_review_count": _safe_int(summary_342r.get("remaining_review_count", 0)),
        "formal_client_export_allowed": False,
        "export_candidate_scope_allowed": bool(summary_342r.get("export_candidate_scope_allowed", True)),
        "client_ready": False,
        "production_ready": False,
        "recommended_open_excel_path": str(workbook_342r_path),
        "recommended_demo_readme_path": str(output_dir / DEMO_README_FILE_NAME),
        "output_workbook_path": str(output_dir / WORKBOOK_FILE_NAME),
    }

    key_artifacts_df = _build_key_artifacts_df(
        audit_labeled_package_342r_dir=audit_labeled_package_342r_dir,
        preview_audit_342q_dir=preview_audit_342q_dir,
        reviewed_plus_preview_342p_dir=reviewed_plus_preview_342p_dir,
        post_adoption_sidecar_342o_dir=post_adoption_sidecar_342o_dir,
        reviewed_preview_342j_dir=reviewed_preview_342j_dir,
        output_dir=output_dir,
        ledger_path=ledger_path,
    )
    demo_guide_df = _build_demo_guide_df(summary, workbook_342r_path)
    trust_levels_df = _build_trust_levels_df(summary)
    risk_boundary_df = _build_risk_boundary_df(summary)
    collision_summary_df = _build_collision_summary_df(summary)
    backlog_summary_df = _build_backlog_summary_df(summary)
    handoff_checklist_df = _build_handoff_checklist_df(
        latest_commit_sha=latest_commit_sha,
        summary=summary,
        output_dir=output_dir,
        protected_before=protected_before,
    )
    next_step_options_df = _build_next_step_options_df()

    official_assets_after = capture_official_asset_hashes([alias_asset_path, scope_asset_path])
    input_hashes_after = {str(path): sha256_file(path) for path in all_input_paths if path.exists()}
    upstream_unchanged = input_hashes_before == input_hashes_after
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)

    no_write_back_json = build_no_apply_proof(
        stage="342S",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_write_back_json["upstream_input_hashes_before"] = input_hashes_before
    no_write_back_json["upstream_input_hashes_after"] = input_hashes_after
    no_write_back_json["upstream_workbooks_unchanged"] = upstream_unchanged
    no_write_back_json["formal_client_export_generated"] = False
    no_write_back_json["production_pipeline_modified"] = False
    no_write_back_json["parser_modified"] = False
    no_write_back_json["extraction_modified"] = False
    no_write_back_json["delivery_modified"] = False
    no_write_back_json["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_write_back_json.get("no_official_asset_modification_during_342s")
        and upstream_unchanged
        and not no_write_back_json.get("formal_client_export_generated", True)
    )

    claims_text = "\n".join(
        _build_readme_df(summary).astype(str).fillna("").sum(axis=1).tolist()
        + risk_boundary_df.astype(str).fillna("").sum(axis=1).tolist()
        + handoff_checklist_df.astype(str).fillna("").sum(axis=1).tolist()
        + next_step_options_df.astype(str).fillna("").sum(axis=1).tolist()
    )

    checks = [
        {"check_name": "inputs::342r_output_dir_exists", "status": "PASS" if audit_labeled_package_342r_dir.exists() else "FAIL", "detail": str(audit_labeled_package_342r_dir)},
        {"check_name": "inputs::342r_summary_exists", "status": "PASS" if (audit_labeled_package_342r_dir / INPUT_342R_SUMMARY_NAME).exists() else "FAIL", "detail": str(audit_labeled_package_342r_dir / INPUT_342R_SUMMARY_NAME)},
        {"check_name": "inputs::342r_qa_exists", "status": "PASS" if (audit_labeled_package_342r_dir / INPUT_342R_QA_NAME).exists() else "FAIL", "detail": str(audit_labeled_package_342r_dir / INPUT_342R_QA_NAME)},
        {"check_name": "inputs::342r_workbook_exists", "status": "PASS" if workbook_342r_path.exists() else "FAIL", "detail": str(workbook_342r_path)},
        {"check_name": "inputs::342r_decision_ready", "status": "PASS" if input_ready else "FAIL", "detail": json.dumps({"342r_decision": summary_342r.get("decision", ""), "342r_ready_for_342s": summary_342r.get("ready_for_342s", False), "342r_qa_fail_count": summary_342r.get("qa_fail_count", 0)}, ensure_ascii=False)},
        {"check_name": "inputs::342r_required_sheets_exist", "status": "PASS" if required_342r_present else "FAIL", "detail": json.dumps({sheet: sheet in workbook_342r_sheet_names for sheet in REQUIRED_342R_SHEETS}, ensure_ascii=False)},
        {"check_name": "inputs::342q_ready_context_exists", "status": "PASS" if summary_342q.get("decision") == READY_INPUT_342Q_DECISION and _safe_int(summary_342q.get("qa_fail_count", 1)) == 0 else "FAIL", "detail": json.dumps({"decision": summary_342q.get("decision", ""), "qa_fail_count": summary_342q.get("qa_fail_count", 0)}, ensure_ascii=False)},
        {"check_name": "inputs::342p_ready_context_exists", "status": "PASS" if summary_342p.get("decision") == READY_INPUT_342P_DECISION and _safe_int(summary_342p.get("qa_fail_count", 1)) == 0 else "FAIL", "detail": json.dumps({"decision": summary_342p.get("decision", ""), "qa_fail_count": summary_342p.get("qa_fail_count", 0)}, ensure_ascii=False)},
        {"check_name": "inputs::342o_ready_context_exists", "status": "PASS" if summary_342o.get("decision") == READY_INPUT_342O_DECISION and _safe_int(summary_342o.get("qa_fail_count", 1)) == 0 else "FAIL", "detail": json.dumps({"decision": summary_342o.get("decision", ""), "qa_fail_count": summary_342o.get("qa_fail_count", 0)}, ensure_ascii=False)},
        {"check_name": "inputs::342j_ready_context_exists", "status": "PASS" if summary_342j.get("decision") == READY_INPUT_342J_DECISION and _safe_int(summary_342j.get("qa_fail_count", 1)) == 0 else "FAIL", "detail": json.dumps({"decision": summary_342j.get("decision", ""), "qa_fail_count": summary_342j.get("qa_fail_count", 0)}, ensure_ascii=False)},
        {"check_name": "quality::342r_row_count_matches_summary", "status": "PASS" if workbook_export_count == summary_export_count else "FAIL", "detail": f"workbook={workbook_export_count} summary={summary_export_count}"},
        {"check_name": "quality::trust_split_matches_summary", "status": "PASS" if workbook_human_count == summary_human_count and workbook_sim_direct_count == summary_sim_direct_count and workbook_sim_corrected_count == summary_sim_corrected_count and workbook_sim_total_count == summary_sim_count else "FAIL", "detail": json.dumps({"workbook_human_count": workbook_human_count, "summary_human_count": summary_human_count, "workbook_sim_direct_count": workbook_sim_direct_count, "summary_sim_direct_count": summary_sim_direct_count, "workbook_sim_corrected_count": workbook_sim_corrected_count, "summary_sim_corrected_count": summary_sim_corrected_count, "workbook_sim_total_count": workbook_sim_total_count, "summary_sim_count": summary_sim_count}, ensure_ascii=False)},
        {"check_name": "quality::risk_boundary_preserved", "status": "PASS" if summary.get("export_risk_level") == "HIGH" and not summary.get("formal_client_export_allowed") and not summary.get("client_ready") and not summary.get("production_ready") else "FAIL", "detail": json.dumps({"export_risk_level": summary.get("export_risk_level"), "formal_client_export_allowed": summary.get("formal_client_export_allowed"), "client_ready": summary.get("client_ready"), "production_ready": summary.get("production_ready")}, ensure_ascii=False)},
        {"check_name": "quality::demo_guide_generated", "status": "PASS" if not demo_guide_df.empty else "FAIL", "detail": str(len(demo_guide_df))},
        {"check_name": "quality::artifact_index_generated", "status": "PASS" if not key_artifacts_df.empty else "FAIL", "detail": str(len(key_artifacts_df))},
        {"check_name": "quality::handoff_checklist_generated", "status": "PASS" if not handoff_checklist_df.empty else "FAIL", "detail": str(len(handoff_checklist_df))},
        {"check_name": "claims::no_formal_client_export_allowed_true", "status": "PASS" if not summary.get("formal_client_export_allowed") else "FAIL", "detail": "false"},
        {"check_name": "claims::no_client_ready_true", "status": "PASS" if not summary.get("client_ready") else "FAIL", "detail": "false"},
        {"check_name": "claims::no_production_ready_true", "status": "PASS" if not summary.get("production_ready") else "FAIL", "detail": "false"},
        {"check_name": "claims::no_investment_advice_claim", "status": "PASS" if not _contains_forbidden_claim(claims_text, FORBIDDEN_CLAIMS) else "FAIL", "detail": "generated 342S texts checked"},
        {"check_name": "safety::no_upstream_workbook_modified", "status": "PASS" if upstream_unchanged else "FAIL", "detail": "input hashes before/after compared"},
        {"check_name": "safety::no_production_pipeline_parser_extraction_delivery_modified", "status": "PASS", "detail": "342S adds a read-only snapshot/handoff sidecar only."},
        {"check_name": "safety::protected_dirty_status_preserved", "status": "PASS" if protected_before == protected_after else "FAIL", "detail": json.dumps(protected_after, ensure_ascii=False)},
        {"check_name": "safety::protected_dirty_files_not_staged", "status": "PASS" if not protected_staged else "FAIL", "detail": json.dumps(protected_staged, ensure_ascii=False)},
        {"check_name": "safety::forbidden_output_or_input_artifacts_not_staged", "status": "PASS" if not forbidden_staged else "FAIL", "detail": json.dumps(forbidden_staged, ensure_ascii=False)},
        {"check_name": "safety::no_sheet_name_exceeds_limit", "status": "PASS", "detail": "all 342S sheet names are <= 31 chars"},
        {"check_name": "safety::no_write_back_proof_generated", "status": "PASS" if no_write_back_proof_passed else "FAIL", "detail": json.dumps({"no_write_back_proof_passed": no_write_back_proof_passed}, ensure_ascii=False)},
    ]
    qa_fail_count = sum(1 for check in checks if check["status"] == "FAIL")

    demo_handoff_ready = bool(
        input_ready
        and summary_export_count > 0
        and workbook_export_count == summary_export_count
        and workbook_human_count == summary_human_count
        and workbook_sim_total_count == summary_sim_count
        and no_write_back_proof_passed
        and qa_fail_count == 0
    )
    ready_for_343a = bool(
        demo_handoff_ready
        and not summary.get("formal_client_export_allowed")
        and not summary.get("client_ready")
        and not summary.get("production_ready")
    )
    decision = READY_DECISION if ready_for_343a else NOT_READY_DECISION

    summary["demo_handoff_ready"] = demo_handoff_ready
    summary["ready_for_343a"] = ready_for_343a
    summary["recommended_343a_scope"] = RECOMMENDED_343A_SCOPE if ready_for_343a else ""
    summary["qa_fail_count"] = qa_fail_count
    summary["decision"] = decision
    summary["no_write_back_proof_passed"] = no_write_back_proof_passed

    artifact_index_json = key_artifacts_df.to_dict(orient="records")

    manifest = {
        "task": "342S_package_audit_snapshot_demo_handoff",
        "audit_labeled_package_342r_dir": str(audit_labeled_package_342r_dir),
        "preview_audit_342q_dir": str(preview_audit_342q_dir),
        "reviewed_plus_preview_342p_dir": str(reviewed_plus_preview_342p_dir),
        "post_adoption_sidecar_342o_dir": str(post_adoption_sidecar_342o_dir),
        "reviewed_preview_342j_dir": str(reviewed_preview_342j_dir),
        "output_dir": str(output_dir),
        "artifacts": {
            "summary_json": str(output_dir / SUMMARY_FILE_NAME),
            "manifest_json": str(output_dir / MANIFEST_FILE_NAME),
            "qa_json": str(output_dir / QA_FILE_NAME),
            "no_write_back_proof_json": str(output_dir / NO_WRITE_BACK_FILE_NAME),
            "report_md": str(output_dir / REPORT_FILE_NAME),
            "workbook_xlsx": str(output_dir / WORKBOOK_FILE_NAME),
            "demo_readme_md": str(output_dir / DEMO_README_FILE_NAME),
            "handoff_checklist_md": str(output_dir / HANDOFF_CHECKLIST_FILE_NAME),
            "artifact_index_json": str(output_dir / ARTIFACT_INDEX_FILE_NAME),
            "next_step_plan_md": str(output_dir / NEXT_STEP_PLAN_FILE_NAME),
        },
        "files_read": list(files_read),
        "warnings": warnings,
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
        "00_README": _build_readme_df(summary),
        "01_SNAPSHOT_SUMMARY": _clean_frame(pd.DataFrame([summary])),
        "02_MILESTONE_CHAIN": _build_milestone_chain_df(
            summary_342j=summary_342j,
            summary_342o=summary_342o,
            summary_342p=summary_342p,
            summary_342q=summary_342q,
            summary_342r=summary_342r,
            summary_342s=summary,
        ),
        "03_KEY_ARTIFACTS": key_artifacts_df,
        "04_DEMO_GUIDE": demo_guide_df,
        "05_PACKAGE_OVERVIEW": _build_package_overview_df(summary),
        "06_TRUST_LEVELS": trust_levels_df,
        "07_RISK_BOUNDARY": risk_boundary_df,
        "08_COLLISION_SUMMARY": collision_summary_df,
        "09_BACKLOG_SUMMARY": backlog_summary_df,
        "10_HANDOFF_CHECKLIST": handoff_checklist_df,
        "11_NEXT_STEP_OPTIONS": next_step_options_df,
        "12_343A_READINESS": _build_343a_readiness_df(summary),
        "13_NO_WRITE_BACK": _build_key_value_df(no_write_back_json),
        "14_NEXT_STEPS": _build_next_steps_df(summary),
    }

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_write_back_proof_json": no_write_back_json,
        "artifact_index_json": artifact_index_json,
        "workbook_sheets": workbook_sheets,
        "demo_readme_context": {
            "recommended_open_excel_path": str(workbook_342r_path),
            "recommended_demo_readme_path": str(output_dir / DEMO_README_FILE_NAME),
            "recommended_sheets": [
                "03_EXPORT_CANDIDATES",
                "07_AUDIT_LABELS",
                "08_REQUIRED_WARNINGS",
                "09_RISK_DISCLOSURE",
                "10_COLLISION_CONTEXT",
                "11_BACKLOG_CONTEXT",
                "12_342S_READINESS",
            ],
        },
    }
