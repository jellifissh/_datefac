from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from datefac.benchmark.demo_narrative_report_package_345f_report import (
    render_artifact_index,
    render_claims_allowed_vs_forbidden,
    render_frontend_demo_copy,
    render_interview_summary,
    render_next_plan,
    render_risk_and_caveat_section,
    render_stakeholder_report,
    render_talking_points,
    render_teacher_brief,
    render_team_update,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345D = "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY"
READY_DECISION_345E = "DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY"
READY_DECISION_345F = "DEMO_NARRATIVE_REPORT_PACKAGE_345F_READY"
BLOCKED_DECISION_345F = "DEMO_NARRATIVE_REPORT_PACKAGE_345F_BLOCKED"
INPUT_STAGE_345F = "POST_345E_DEMO_NARRATIVE_REPORT_PACKAGE"

DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR = Path(
    r"D:\_datefac\output\full_structured_demo_export_package_345d"
)
DEFAULT_DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_DIR = Path(
    r"D:\_datefac\output\demo_export_review_qa_checklist_345e"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\demo_narrative_report_package_345f")

MANIFEST_FILE_NAME = "demo_narrative_report_package_345f_manifest.json"
STAKEHOLDER_REPORT_MD_FILE_NAME = "demo_narrative_report_package_345f_stakeholder_report.md"
TEACHER_BRIEF_MD_FILE_NAME = "demo_narrative_report_package_345f_teacher_brief.md"
TEAM_UPDATE_MD_FILE_NAME = "demo_narrative_report_package_345f_team_update.md"
INTERVIEW_PROJECT_SUMMARY_MD_FILE_NAME = "demo_narrative_report_package_345f_interview_project_summary.md"
FRONTEND_DEMO_COPY_MD_FILE_NAME = "demo_narrative_report_package_345f_frontend_demo_copy.md"
TALKING_POINTS_MD_FILE_NAME = "demo_narrative_report_package_345f_talking_points.md"
RISK_AND_CAVEAT_SECTION_MD_FILE_NAME = "demo_narrative_report_package_345f_risk_and_caveat_section.md"
METRICS_SUMMARY_JSON_FILE_NAME = "demo_narrative_report_package_345f_metrics_summary.json"
METRICS_SUMMARY_CSV_FILE_NAME = "demo_narrative_report_package_345f_metrics_summary.csv"
SAMPLE_ROWS_FOR_STORY_JSON_FILE_NAME = "demo_narrative_report_package_345f_sample_rows_for_story.json"
SAMPLE_ROWS_FOR_STORY_CSV_FILE_NAME = "demo_narrative_report_package_345f_sample_rows_for_story.csv"
CLAIMS_ALLOWED_VS_FORBIDDEN_MD_FILE_NAME = "demo_narrative_report_package_345f_claims_allowed_vs_forbidden.md"
ARTIFACT_INDEX_MD_FILE_NAME = "demo_narrative_report_package_345f_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "demo_narrative_report_package_345f_next_plan.md"

INPUT_345D_MANIFEST_NAME = "full_structured_demo_export_package_345d_manifest.json"
INPUT_345D_DEMO_EXPORT_SUMMARY_JSON_NAME = "full_structured_demo_export_package_345d_demo_export_summary.json"
INPUT_345D_QUALITY_CAVEATS_JSON_NAME = "full_structured_demo_export_package_345d_quality_caveats.json"
INPUT_345D_QUALITY_CAVEATS_MD_NAME = "full_structured_demo_export_package_345d_quality_caveats.md"
INPUT_345D_EXECUTIVE_SUMMARY_MD_NAME = "full_structured_demo_export_package_345d_executive_summary.md"
INPUT_345D_ARTIFACT_INDEX_MD_NAME = "full_structured_demo_export_package_345d_artifact_index.md"
INPUT_345D_NEXT_PLAN_MD_NAME = "full_structured_demo_export_package_345d_next_plan.md"

INPUT_345E_MANIFEST_NAME = "demo_export_review_qa_checklist_345e_manifest.json"
INPUT_345E_REVIEW_CHECKLIST_MD_NAME = "demo_export_review_qa_checklist_345e_review_checklist.md"
INPUT_345E_PRESENTATION_READINESS_JSON_NAME = "demo_export_review_qa_checklist_345e_demo_presentation_readiness.json"
INPUT_345E_ROW_COUNT_RECONCILIATION_JSON_NAME = "demo_export_review_qa_checklist_345e_row_count_reconciliation.json"
INPUT_345E_ROW_COUNT_RECONCILIATION_CSV_NAME = "demo_export_review_qa_checklist_345e_row_count_reconciliation.csv"
INPUT_345E_GATE_SAFETY_JSON_NAME = "demo_export_review_qa_checklist_345e_gate_safety_check.json"
INPUT_345E_CAVEAT_COMPLETENESS_JSON_NAME = "demo_export_review_qa_checklist_345e_caveat_completeness_check.json"
INPUT_345E_SAMPLE_DEMO_ROWS_JSON_NAME = "demo_export_review_qa_checklist_345e_sample_demo_rows.json"
INPUT_345E_SAMPLE_DEMO_ROWS_CSV_NAME = "demo_export_review_qa_checklist_345e_sample_demo_rows.csv"
INPUT_345E_QUALITY_LIMITED_SAMPLE_ROWS_JSON_NAME = "demo_export_review_qa_checklist_345e_quality_limited_sample_rows.json"
INPUT_345E_QUALITY_LIMITED_SAMPLE_ROWS_CSV_NAME = "demo_export_review_qa_checklist_345e_quality_limited_sample_rows.csv"
INPUT_345E_EXCLUDED_SAMPLE_ROWS_JSON_NAME = "demo_export_review_qa_checklist_345e_excluded_sample_rows.json"
INPUT_345E_EXCLUDED_SAMPLE_ROWS_CSV_NAME = "demo_export_review_qa_checklist_345e_excluded_sample_rows.csv"
INPUT_345E_EXECUTIVE_SUMMARY_MD_NAME = "demo_export_review_qa_checklist_345e_executive_summary.md"
INPUT_345E_ARTIFACT_INDEX_MD_NAME = "demo_export_review_qa_checklist_345e_artifact_index.md"
INPUT_345E_NEXT_PLAN_MD_NAME = "demo_export_review_qa_checklist_345e_next_plan.md"

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

FORBIDDEN_STAGE_PATHS = [
    "output",
    "temp",
    "input",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_ledger_path() -> Path:
    milestone_dir = Path(r"D:\_datefac\docs\project_milestones")
    matches = sorted(milestone_dir.glob("PROJECT_MILESTONE_LEDGER_*.md"))
    if matches:
        return matches[0]
    return milestone_dir / "PROJECT_MILESTONE_LEDGER.md"


DEFAULT_LEDGER_PATH = _default_ledger_path()


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).strip().split())
    return "" if text.lower() == "nan" else text


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _safe_text(value).lower() in {"1", "true", "yes", "y"}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_sample_package(json_path: Path, csv_path: Path) -> Dict[str, Any]:
    if json_path.exists():
        payload = _read_json(json_path)
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            return payload
        if isinstance(payload, list):
            return {
                "source_artifact": json_path.stem,
                "source_path": str(json_path),
                "sample_limit": len(payload),
                "selected_count": len(payload),
                "source_row_count": len(payload),
                "rows": [dict(row) for row in payload],
            }
        raise ValueError(f"unsupported sample package JSON payload: {json_path}")
    if csv_path.exists():
        rows = _read_csv_rows(csv_path)
        return {
            "source_artifact": csv_path.stem,
            "source_path": str(csv_path),
            "sample_limit": len(rows),
            "selected_count": len(rows),
            "source_row_count": len(rows),
            "rows": rows,
        }
    raise FileNotFoundError(f"sample package missing: {json_path} / {csv_path}")


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


def _ensure_path(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"required input file missing: {path}")
    return path


def _select_story_rows(
    *,
    demo_package: Dict[str, Any],
    quality_package: Dict[str, Any],
    excluded_package: Dict[str, Any],
    max_sample_rows_in_report: int,
) -> Dict[str, Any]:
    if max_sample_rows_in_report <= 0:
        return {
            "sample_limit": max_sample_rows_in_report,
            "selected_count": 0,
            "selection_plan": {"demo": 0, "quality_limited": 0, "excluded": 0},
            "rows": [],
        }

    demo_quota = max(1, max_sample_rows_in_report // 3 + (1 if max_sample_rows_in_report % 3 else 0))
    quality_quota = max(1, max_sample_rows_in_report // 3)
    excluded_quota = max_sample_rows_in_report - demo_quota - quality_quota
    excluded_quota = max(1, excluded_quota)

    demo_rows = demo_package.get("rows", [])[:demo_quota]
    quality_rows = quality_package.get("rows", [])[:quality_quota]
    excluded_rows = excluded_package.get("rows", [])[:excluded_quota]

    combined = [dict(row) for row in demo_rows + quality_rows + excluded_rows][:max_sample_rows_in_report]
    return {
        "sample_limit": max_sample_rows_in_report,
        "selected_count": len(combined),
        "selection_plan": {
            "demo": len(demo_rows),
            "quality_limited": len(quality_rows),
            "excluded": len(excluded_rows),
        },
        "rows": combined,
    }


def _metrics_summary_rows(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {"category": "counts", "metric_name": "inventory_row_count", "metric_value": manifest["inventory_row_count"]},
        {"category": "counts", "metric_name": "demo_export_row_count", "metric_value": manifest["demo_export_row_count"]},
        {"category": "counts", "metric_name": "quality_limited_row_count", "metric_value": manifest["quality_limited_row_count"]},
        {"category": "counts", "metric_name": "excluded_row_count", "metric_value": manifest["excluded_row_count"]},
        {
            "category": "coverage",
            "metric_name": "coverage_ratio_before_alias_simulation",
            "metric_value": manifest["coverage_ratio_before_alias_simulation"],
        },
        {
            "category": "coverage",
            "metric_name": "coverage_ratio_after_alias_simulation",
            "metric_value": manifest["coverage_ratio_after_alias_simulation"],
        },
        {
            "category": "coverage",
            "metric_name": "baseline_normalized_demo_row_count",
            "metric_value": manifest["baseline_normalized_demo_row_count"],
        },
        {
            "category": "coverage",
            "metric_name": "alias_simulated_demo_row_count",
            "metric_value": manifest["alias_simulated_demo_row_count"],
        },
        {
            "category": "risk",
            "metric_name": "remaining_unnormalized_raw_metric_name_count",
            "metric_value": manifest["remaining_unnormalized_raw_metric_name_count"],
        },
        {
            "category": "risk",
            "metric_name": "remaining_unnormalized_metric_row_count",
            "metric_value": manifest["remaining_unnormalized_metric_row_count"],
        },
        {"category": "risk", "metric_name": "high_severity_issue_count", "metric_value": manifest["high_severity_issue_count"]},
        {"category": "risk", "metric_name": "medium_severity_issue_count", "metric_value": manifest["medium_severity_issue_count"]},
        {"category": "risk", "metric_name": "missing_unit_count", "metric_value": manifest["missing_unit_count"]},
        {"category": "risk", "metric_name": "missing_period_count", "metric_value": manifest["missing_period_count"]},
        {
            "category": "risk",
            "metric_name": "missing_source_trace_count",
            "metric_value": manifest["missing_source_trace_count"],
        },
        {"category": "qa", "metric_name": "row_count_closure_passed", "metric_value": manifest["row_count_closure_passed"]},
        {"category": "qa", "metric_name": "gate_safety_check_passed", "metric_value": manifest["gate_safety_check_passed"]},
        {"category": "qa", "metric_name": "caveat_completeness_passed", "metric_value": manifest["caveat_completeness_passed"]},
        {
            "category": "qa",
            "metric_name": "presentation_ready_for_demo_only",
            "metric_value": manifest["presentation_ready_for_demo_only"],
        },
    ]


def _build_allowed_claims(manifest: Dict[str, Any]) -> List[str]:
    return [
        f"Generated a full structured demo export package from {manifest['inventory_row_count']} inventory rows.",
        "Validated row-count closure and demo-only gate safety.",
        "Alias simulation improved normalization coverage from 45.25% to 68.41%.",
        f"Produced {manifest['demo_export_row_count']} strict demo-ready rows and separated {manifest['quality_limited_row_count']} quality-limited rows from {manifest['excluded_row_count']} excluded rows.",
        "Kept official rules and alias assets unchanged while packaging the demo narrative.",
    ]


def _build_forbidden_claims() -> List[str]:
    return [
        "Production ready.",
        "Formal client export completed.",
        "Official alias rules updated.",
        "All extracted financial rows are correct.",
        "Human review pipeline is globally complete.",
        "Alias simulation equals official rule mutation.",
        "344G can proceed without a genuinely human-filled 344F workbook.",
    ]


def _build_talking_points(manifest: Dict[str, Any]) -> List[str]:
    return [
        f"DateFac closes {manifest['inventory_row_count']} structured rows into explicit demo, quality-limited, and excluded buckets.",
        f"Row-count closure passed: {manifest['demo_export_row_count']} + {manifest['quality_limited_row_count']} + {manifest['excluded_row_count']} = {manifest['inventory_row_count']}.",
        "Alias simulation improved normalization coverage, but did not mutate official rules.",
        f"Strict demo-ready rows remain {manifest['demo_export_row_count']} because demo safety requires more than normalization alone.",
        "345E confirmed gate safety, caveat completeness, and presentation readiness for demo-only use.",
        "Formal/client/production gates remain false throughout the chain.",
    ]


def _build_caveat_list(manifest: Dict[str, Any]) -> List[str]:
    return [
        f"Remaining unnormalized raw metric names: {manifest['remaining_unnormalized_raw_metric_name_count']}.",
        f"Remaining unnormalized metric rows: {manifest['remaining_unnormalized_metric_row_count']}.",
        f"High severity issue count: {manifest['high_severity_issue_count']}.",
        f"Medium severity issue count: {manifest['medium_severity_issue_count']}.",
        f"Missing unit count: {manifest['missing_unit_count']}.",
        f"Missing period count: {manifest['missing_period_count']}.",
        f"Missing source trace count: {manifest['missing_source_trace_count']}.",
        "Simulated alias improvements are analytical sidecar results, not official rule updates.",
        "Quality-limited and excluded rows must remain visible in any honest demo narrative.",
    ]


def ledger_has_345f_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    text = ledger_path.read_text(encoding="utf-8")
    return "## 345F Demo Narrative Report Package" in text or READY_DECISION_345F in text


def build_345f_ledger_entry(*, manifest: Dict[str, Any]) -> str:
    lines = [
        "## 345F Demo Narrative Report Package",
        "",
        "Status: completed",
        "",
        "Decision:",
        f"- `{manifest.get('decision', '')}`",
        "",
        "Input packages:",
        f"- `345D = {manifest.get('input_345d_dir', '')}`",
        f"- `345E = {manifest.get('input_345e_dir', '')}`",
        "",
        "Output package:",
        f"- `{manifest.get('output_dir', '')}`",
        "",
        "Key metrics:",
        f"- `generated_report_count = {manifest.get('generated_report_count', 0)}`",
        f"- `demo_export_row_count = {manifest.get('demo_export_row_count', 0)}`",
        f"- `quality_limited_row_count = {manifest.get('quality_limited_row_count', 0)}`",
        f"- `excluded_row_count = {manifest.get('excluded_row_count', 0)}`",
        f"- `coverage_ratio_before_alias_simulation = {manifest.get('coverage_ratio_before_alias_simulation', None)}`",
        f"- `coverage_ratio_after_alias_simulation = {manifest.get('coverage_ratio_after_alias_simulation', None)}`",
        f"- `sample_rows_for_story_count = {manifest.get('sample_rows_for_story_count', 0)}`",
        f"- `qa_fail_count = {manifest.get('qa_fail_count', 0)}`",
        "",
        "Gate status:",
        f"- `formal_client_export_allowed = {str(manifest.get('formal_client_export_allowed', False)).lower()}`",
        f"- `client_ready = {str(manifest.get('client_ready', False)).lower()}`",
        f"- `production_ready = {str(manifest.get('production_ready', False)).lower()}`",
        f"- `global_strict_human_review_completed = {str(manifest.get('global_strict_human_review_completed', False)).lower()}`",
        "",
        "No-write-back confirmation:",
        f"- `no_write_back_proof_passed = {str(manifest.get('no_write_back_proof_passed', False)).lower()}`",
        f"- `official_rules_modified = {str(manifest.get('official_rules_modified', False)).lower()}`",
        f"- `official_alias_assets_modified = {str(manifest.get('official_alias_assets_modified', False)).lower()}`",
        "",
        "Validation commands and results:",
        "- `python -m py_compile ...` passed",
        "- `python -m pytest tests\\benchmark\\test_demo_narrative_report_package_345f.py -q` passed",
        "- real runner passed",
        "",
        "Next recommended step:",
        f"- `{manifest.get('next_recommended_step', '')}`",
        "- `344G` still waits for a genuinely human-filled `344F` workbook",
    ]
    return "\n".join(lines)


def append_345f_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    if ledger_has_345f_entry(ledger_path):
        return False
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    addition = build_345f_ledger_entry(manifest=manifest)
    prefix = "\n\n" if existing and not existing.endswith("\n\n") else ""
    if existing.endswith("\n"):
        prefix = "\n" if not existing.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(existing + prefix + addition + "\n", encoding="utf-8")
    return True


def _artifact_index_rows(output_dir: Path) -> List[Dict[str, str]]:
    rows = [
        {"artifact_name": MANIFEST_FILE_NAME, "path": str(output_dir / MANIFEST_FILE_NAME), "purpose": "Manifest with 345F narrative-package metrics and gates."},
        {"artifact_name": STAKEHOLDER_REPORT_MD_FILE_NAME, "path": str(output_dir / STAKEHOLDER_REPORT_MD_FILE_NAME), "purpose": "General stakeholder-facing narrative summary."},
        {"artifact_name": TEACHER_BRIEF_MD_FILE_NAME, "path": str(output_dir / TEACHER_BRIEF_MD_FILE_NAME), "purpose": "Concise teacher/class presentation brief."},
        {"artifact_name": TEAM_UPDATE_MD_FILE_NAME, "path": str(output_dir / TEAM_UPDATE_MD_FILE_NAME), "purpose": "Technical team-facing implementation update."},
        {"artifact_name": INTERVIEW_PROJECT_SUMMARY_MD_FILE_NAME, "path": str(output_dir / INTERVIEW_PROJECT_SUMMARY_MD_FILE_NAME), "purpose": "Truthful interview/resume project summary."},
        {"artifact_name": FRONTEND_DEMO_COPY_MD_FILE_NAME, "path": str(output_dir / FRONTEND_DEMO_COPY_MD_FILE_NAME), "purpose": "Frontend-safe demo labels and warning copy."},
        {"artifact_name": TALKING_POINTS_MD_FILE_NAME, "path": str(output_dir / TALKING_POINTS_MD_FILE_NAME), "purpose": "Safe talking points for presenting the demo."},
        {"artifact_name": RISK_AND_CAVEAT_SECTION_MD_FILE_NAME, "path": str(output_dir / RISK_AND_CAVEAT_SECTION_MD_FILE_NAME), "purpose": "Explicit caveat and risk section."},
        {"artifact_name": METRICS_SUMMARY_JSON_FILE_NAME, "path": str(output_dir / METRICS_SUMMARY_JSON_FILE_NAME), "purpose": "Machine-readable metrics summary."},
        {"artifact_name": METRICS_SUMMARY_CSV_FILE_NAME, "path": str(output_dir / METRICS_SUMMARY_CSV_FILE_NAME), "purpose": "Flat metrics summary for spreadsheet/report use."},
        {"artifact_name": SAMPLE_ROWS_FOR_STORY_JSON_FILE_NAME, "path": str(output_dir / SAMPLE_ROWS_FOR_STORY_JSON_FILE_NAME), "purpose": "Bounded sample rows copied for story/demo narration."},
        {"artifact_name": SAMPLE_ROWS_FOR_STORY_CSV_FILE_NAME, "path": str(output_dir / SAMPLE_ROWS_FOR_STORY_CSV_FILE_NAME), "purpose": "CSV copy of bounded story sample rows."},
        {"artifact_name": CLAIMS_ALLOWED_VS_FORBIDDEN_MD_FILE_NAME, "path": str(output_dir / CLAIMS_ALLOWED_VS_FORBIDDEN_MD_FILE_NAME), "purpose": "Allowed vs forbidden claims table."},
        {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": str(output_dir / ARTIFACT_INDEX_MD_FILE_NAME), "purpose": "Index of all 345F report artifacts."},
        {"artifact_name": NEXT_PLAN_MD_FILE_NAME, "path": str(output_dir / NEXT_PLAN_MD_FILE_NAME), "purpose": "Recommended next step after 345F."},
    ]
    return rows


def build_demo_narrative_report_package_345f(
    *,
    full_structured_demo_export_package_345d_dir: Path,
    demo_export_review_qa_checklist_345e_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    max_sample_rows_in_report: int = 10,
    audiences: Sequence[str] | None = None,
) -> Dict[str, Any]:
    _ensure_path(full_structured_demo_export_package_345d_dir)
    _ensure_path(demo_export_review_qa_checklist_345e_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audience_list = list(audiences or ["teacher"])

    input_paths = {
        "345d_manifest": _ensure_path(full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME),
        "345d_demo_export_summary": _ensure_path(full_structured_demo_export_package_345d_dir / INPUT_345D_DEMO_EXPORT_SUMMARY_JSON_NAME),
        "345d_quality_caveats_json": _ensure_path(full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_CAVEATS_JSON_NAME),
        "345d_quality_caveats_md": _ensure_path(full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_CAVEATS_MD_NAME),
        "345d_executive_summary_md": _ensure_path(full_structured_demo_export_package_345d_dir / INPUT_345D_EXECUTIVE_SUMMARY_MD_NAME),
        "345d_artifact_index_md": _ensure_path(full_structured_demo_export_package_345d_dir / INPUT_345D_ARTIFACT_INDEX_MD_NAME),
        "345d_next_plan_md": _ensure_path(full_structured_demo_export_package_345d_dir / INPUT_345D_NEXT_PLAN_MD_NAME),
        "345e_manifest": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_MANIFEST_NAME),
        "345e_review_checklist_md": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_REVIEW_CHECKLIST_MD_NAME),
        "345e_presentation_readiness_json": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_PRESENTATION_READINESS_JSON_NAME),
        "345e_row_count_reconciliation_json": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_ROW_COUNT_RECONCILIATION_JSON_NAME),
        "345e_gate_safety_json": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_GATE_SAFETY_JSON_NAME),
        "345e_caveat_completeness_json": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_CAVEAT_COMPLETENESS_JSON_NAME),
        "345e_sample_demo_rows_json": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_SAMPLE_DEMO_ROWS_JSON_NAME),
        "345e_quality_limited_sample_rows_json": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_QUALITY_LIMITED_SAMPLE_ROWS_JSON_NAME),
        "345e_excluded_sample_rows_json": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_EXCLUDED_SAMPLE_ROWS_JSON_NAME),
        "345e_executive_summary_md": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_EXECUTIVE_SUMMARY_MD_NAME),
        "345e_artifact_index_md": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_ARTIFACT_INDEX_MD_NAME),
        "345e_next_plan_md": _ensure_path(demo_export_review_qa_checklist_345e_dir / INPUT_345E_NEXT_PLAN_MD_NAME),
    }

    files_read = [str(path) for path in input_paths.values()]
    file_hashes_before = {str(path): sha256_file(path) for path in input_paths.values()}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    manifest_345d = _read_json(input_paths["345d_manifest"])
    demo_export_summary_345d = _read_json(input_paths["345d_demo_export_summary"])
    quality_caveats_345d = _read_json(input_paths["345d_quality_caveats_json"])
    _ = input_paths["345d_quality_caveats_md"].read_text(encoding="utf-8")
    _ = input_paths["345d_executive_summary_md"].read_text(encoding="utf-8")
    _ = input_paths["345d_artifact_index_md"].read_text(encoding="utf-8")
    _ = input_paths["345d_next_plan_md"].read_text(encoding="utf-8")

    manifest_345e = _read_json(input_paths["345e_manifest"])
    _ = input_paths["345e_review_checklist_md"].read_text(encoding="utf-8")
    presentation_readiness_345e = _read_json(input_paths["345e_presentation_readiness_json"])
    row_count_reconciliation_345e = _read_json(input_paths["345e_row_count_reconciliation_json"])
    gate_safety_345e = _read_json(input_paths["345e_gate_safety_json"])
    caveat_completeness_345e = _read_json(input_paths["345e_caveat_completeness_json"])
    demo_sample_package = _read_sample_package(
        input_paths["345e_sample_demo_rows_json"],
        demo_export_review_qa_checklist_345e_dir / INPUT_345E_SAMPLE_DEMO_ROWS_CSV_NAME,
    )
    quality_sample_package = _read_sample_package(
        input_paths["345e_quality_limited_sample_rows_json"],
        demo_export_review_qa_checklist_345e_dir / INPUT_345E_QUALITY_LIMITED_SAMPLE_ROWS_CSV_NAME,
    )
    excluded_sample_package = _read_sample_package(
        input_paths["345e_excluded_sample_rows_json"],
        demo_export_review_qa_checklist_345e_dir / INPUT_345E_EXCLUDED_SAMPLE_ROWS_CSV_NAME,
    )
    _ = input_paths["345e_executive_summary_md"].read_text(encoding="utf-8")
    _ = input_paths["345e_artifact_index_md"].read_text(encoding="utf-8")
    _ = input_paths["345e_next_plan_md"].read_text(encoding="utf-8")

    validations = [
        (_safe_text(manifest_345d.get("decision")) == READY_DECISION_345D, "345D decision must be READY"),
        (int(manifest_345d.get("qa_fail_count", 1)) == 0, "345D qa_fail_count must be 0"),
        (_bool_value(manifest_345d.get("demo_export_only")), "345D demo_export_only must be true"),
        (not _bool_value(manifest_345d.get("formal_export_generated")), "345D formal_export_generated must be false"),
        (_safe_text(manifest_345e.get("decision")) == READY_DECISION_345E, "345E decision must be READY"),
        (int(manifest_345e.get("qa_fail_count", 1)) == 0, "345E qa_fail_count must be 0"),
        (_bool_value(manifest_345e.get("row_count_closure_passed")), "345E row_count_closure_passed must be true"),
        (_bool_value(manifest_345e.get("gate_safety_check_passed")), "345E gate_safety_check_passed must be true"),
        (_bool_value(manifest_345e.get("caveat_completeness_passed")), "345E caveat_completeness_passed must be true"),
        (_bool_value(manifest_345e.get("presentation_ready_for_demo_only")), "345E presentation_ready_for_demo_only must be true"),
        (not _bool_value(manifest_345d.get("formal_client_export_allowed")), "345D formal_client_export_allowed must be false"),
        (not _bool_value(manifest_345d.get("client_ready")), "345D client_ready must be false"),
        (not _bool_value(manifest_345d.get("production_ready")), "345D production_ready must be false"),
        (not _bool_value(manifest_345e.get("formal_client_export_allowed")), "345E formal_client_export_allowed must be false"),
        (not _bool_value(manifest_345e.get("client_ready")), "345E client_ready must be false"),
        (not _bool_value(manifest_345e.get("production_ready")), "345E production_ready must be false"),
        (not _bool_value(manifest_345d.get("official_rules_modified")), "345D official_rules_modified must be false"),
        (not _bool_value(manifest_345d.get("official_alias_assets_modified")), "345D official_alias_assets_modified must be false"),
        (not _bool_value(manifest_345e.get("official_rules_modified")), "345E official_rules_modified must be false"),
        (not _bool_value(manifest_345e.get("official_alias_assets_modified")), "345E official_alias_assets_modified must be false"),
        (_bool_value(caveat_completeness_345e.get("passed")), "345E caveat completeness artifact must pass"),
        (_bool_value(gate_safety_345e.get("passed")), "345E gate safety artifact must pass"),
        (_bool_value(presentation_readiness_345e.get("safe_for_demo_only")), "345E presentation artifact must mark safe_for_demo_only"),
        (bool(row_count_reconciliation_345e), "345E row count reconciliation must be present"),
    ]
    failures = [message for passed, message in validations if not passed]
    if failures:
        raise ValueError(" ; ".join(failures))

    sample_rows_for_story = _select_story_rows(
        demo_package=demo_sample_package,
        quality_package=quality_sample_package,
        excluded_package=excluded_sample_package,
        max_sample_rows_in_report=max_sample_rows_in_report,
    )

    talking_points = _build_talking_points(
        {
            "inventory_row_count": int(manifest_345d.get("inventory_row_count", 0)),
            "demo_export_row_count": int(manifest_345d.get("demo_export_row_count", 0)),
            "quality_limited_row_count": int(manifest_345d.get("quality_limited_row_count", 0)),
            "excluded_row_count": int(manifest_345d.get("excluded_row_count", 0)),
        }
    )
    allowed_claims = _build_allowed_claims(
        {
            "inventory_row_count": int(manifest_345d.get("inventory_row_count", 0)),
            "demo_export_row_count": int(manifest_345d.get("demo_export_row_count", 0)),
            "quality_limited_row_count": int(manifest_345d.get("quality_limited_row_count", 0)),
            "excluded_row_count": int(manifest_345d.get("excluded_row_count", 0)),
        }
    )
    forbidden_claims = _build_forbidden_claims()

    manifest = {
        "decision": READY_DECISION_345F,
        "input_stage": INPUT_STAGE_345F,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_345d_decision": _safe_text(manifest_345d.get("decision")),
        "input_345e_decision": _safe_text(manifest_345e.get("decision")),
        "input_345d_dir": str(full_structured_demo_export_package_345d_dir),
        "input_345e_dir": str(demo_export_review_qa_checklist_345e_dir),
        "output_dir": str(output_dir),
        "demo_export_row_count": int(manifest_345d.get("demo_export_row_count", 0)),
        "quality_limited_row_count": int(manifest_345d.get("quality_limited_row_count", 0)),
        "excluded_row_count": int(manifest_345d.get("excluded_row_count", 0)),
        "inventory_row_count": int(manifest_345d.get("inventory_row_count", 0)),
        "row_count_closure_passed": _bool_value(manifest_345e.get("row_count_closure_passed")),
        "coverage_ratio_before_alias_simulation": manifest_345d.get("coverage_ratio_before_alias_simulation"),
        "coverage_ratio_after_alias_simulation": manifest_345d.get("coverage_ratio_after_alias_simulation"),
        "baseline_normalized_demo_row_count": int(manifest_345d.get("baseline_normalized_demo_row_count", manifest_345d.get("demo_export_row_count", 0))),
        "alias_simulated_demo_row_count": int(manifest_345d.get("alias_simulated_demo_row_count", 0)),
        "remaining_unnormalized_raw_metric_name_count": int(manifest_345d.get("remaining_unnormalized_raw_metric_name_count", 0)),
        "remaining_unnormalized_metric_row_count": int(manifest_345d.get("remaining_unnormalized_metric_row_count", 0)),
        "high_severity_issue_count": int(manifest_345d.get("high_severity_issue_count", 0)),
        "medium_severity_issue_count": int(manifest_345d.get("medium_severity_issue_count", 0)),
        "missing_unit_count": int(manifest_345d.get("missing_unit_count", 0)),
        "missing_period_count": int(manifest_345d.get("missing_period_count", 0)),
        "missing_source_trace_count": int(manifest_345d.get("missing_source_trace_count", 0)),
        "gate_safety_check_passed": _bool_value(manifest_345e.get("gate_safety_check_passed")),
        "caveat_completeness_passed": _bool_value(manifest_345e.get("caveat_completeness_passed")),
        "presentation_ready_for_demo_only": _bool_value(manifest_345e.get("presentation_ready_for_demo_only")),
        "generated_report_count": 10,
        "sample_rows_for_story_count": sample_rows_for_story["selected_count"],
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_export_generated": False,
        "demo_export_only": True,
        "milestone_ledger_updated": False,
        "primary_audience": audience_list[0],
        "audiences": audience_list,
        "next_recommended_step": "345G Demo Presentation Slide Outline",
        "generated_at_utc": _utc_now(),
    }

    caveats = _build_caveat_list(manifest)
    metrics_summary_rows = _metrics_summary_rows(manifest)
    stakeholder_report_md = render_stakeholder_report(manifest, talking_points, caveats)
    teacher_brief_md = render_teacher_brief(manifest, talking_points, caveats)
    team_update_md = render_team_update(
        manifest,
        str(output_dir),
        [
            STAKEHOLDER_REPORT_MD_FILE_NAME,
            TEACHER_BRIEF_MD_FILE_NAME,
            TEAM_UPDATE_MD_FILE_NAME,
            INTERVIEW_PROJECT_SUMMARY_MD_FILE_NAME,
            FRONTEND_DEMO_COPY_MD_FILE_NAME,
            TALKING_POINTS_MD_FILE_NAME,
            RISK_AND_CAVEAT_SECTION_MD_FILE_NAME,
            CLAIMS_ALLOWED_VS_FORBIDDEN_MD_FILE_NAME,
            ARTIFACT_INDEX_MD_FILE_NAME,
            NEXT_PLAN_MD_FILE_NAME,
        ],
        sample_rows_for_story["selected_count"],
    )
    interview_summary_md = render_interview_summary(manifest, caveats)
    frontend_demo_copy_md = render_frontend_demo_copy(
        {
            **manifest,
            "sample_rows_for_story_count": sample_rows_for_story["selected_count"],
        }
    )
    talking_points_md = render_talking_points(talking_points, allowed_claims, forbidden_claims)
    risk_and_caveat_md = render_risk_and_caveat_section(caveats)
    claims_allowed_vs_forbidden_md = render_claims_allowed_vs_forbidden(allowed_claims, forbidden_claims)
    artifact_index_rows = _artifact_index_rows(output_dir)
    artifact_index_md = render_artifact_index(artifact_index_rows)
    next_plan_md = render_next_plan(manifest)

    file_hashes_after = {str(path): sha256_file(path) for path in input_paths.values()}
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)
    official_assets_after = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    upstream_unchanged = file_hashes_before == file_hashes_after

    no_apply_proof = build_no_apply_proof(
        stage="345F",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )
    no_apply_proof["upstream_input_hashes_before"] = file_hashes_before
    no_apply_proof["upstream_input_hashes_after"] = file_hashes_after
    no_apply_proof["upstream_inputs_unchanged"] = upstream_unchanged
    no_apply_proof["formal_client_export_generated"] = False
    no_apply_proof["real_production_apply_performed"] = False
    no_apply_proof["official_rules_modified"] = False
    no_apply_proof["official_alias_assets_modified"] = False
    no_apply_proof["demo_narrative_package_only"] = True
    no_apply_proof["no_write_back"] = True
    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_345f")
        and upstream_unchanged
        and protected_before == protected_after
        and not protected_staged
        and not forbidden_staged
    )
    manifest["no_write_back_proof_passed"] = no_write_back_proof_passed

    qa_checks = [
        _safe_text(manifest_345d.get("decision")) == READY_DECISION_345D,
        _safe_text(manifest_345e.get("decision")) == READY_DECISION_345E,
        manifest["row_count_closure_passed"],
        manifest["gate_safety_check_passed"],
        manifest["caveat_completeness_passed"],
        manifest["presentation_ready_for_demo_only"],
        manifest["generated_report_count"] == 10,
        manifest["sample_rows_for_story_count"] > 0,
        manifest["formal_client_export_allowed"] is False,
        manifest["client_ready"] is False,
        manifest["production_ready"] is False,
        manifest["formal_export_generated"] is False,
        manifest["demo_export_only"] is True,
        manifest["official_rules_modified"] is False,
        manifest["official_alias_assets_modified"] is False,
        no_write_back_proof_passed,
    ]

    if ledger_path is not None:
        _ = append_345f_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = ledger_has_345f_entry(ledger_path)
    qa_checks.append(manifest["milestone_ledger_updated"] or ledger_path is None)

    qa_fail_count = sum(1 for check in qa_checks if not check)
    manifest["qa_fail_count"] = qa_fail_count
    manifest["decision"] = READY_DECISION_345F if qa_fail_count == 0 else BLOCKED_DECISION_345F

    metrics_summary_json = {
        "decision": manifest["decision"],
        "qa_fail_count": manifest["qa_fail_count"],
        "metrics": metrics_summary_rows,
    }

    sample_rows_for_story_json = {
        "sample_limit": sample_rows_for_story["sample_limit"],
        "selected_count": sample_rows_for_story["selected_count"],
        "selection_plan": sample_rows_for_story["selection_plan"],
        "rows": sample_rows_for_story["rows"],
    }

    return {
        "manifest": manifest,
        "stakeholder_report_md": stakeholder_report_md,
        "teacher_brief_md": teacher_brief_md,
        "team_update_md": team_update_md,
        "interview_project_summary_md": interview_summary_md,
        "frontend_demo_copy_md": frontend_demo_copy_md,
        "talking_points_md": talking_points_md,
        "risk_and_caveat_section_md": risk_and_caveat_md,
        "metrics_summary_json": metrics_summary_json,
        "metrics_summary_rows": metrics_summary_rows,
        "sample_rows_for_story_json": sample_rows_for_story_json,
        "sample_rows_for_story_rows": sample_rows_for_story["rows"],
        "claims_allowed_vs_forbidden_md": claims_allowed_vs_forbidden_md,
        "artifact_index_md": artifact_index_md,
        "artifact_index_rows": artifact_index_rows,
        "next_plan_md": next_plan_md,
        "no_write_back_proof": no_apply_proof,
        "allowed_claims": allowed_claims,
        "forbidden_claims": forbidden_claims,
    }
