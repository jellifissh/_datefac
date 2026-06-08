from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.delivery_report_refresh_330j import _read_json
from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import (
    _frame_for_output,
    _norm_text,
    _safe_int,
)


READY_331B_DECISION = "DEMO_PACKAGING_331B_READY_FOR_PRESENTATION_REFRESH"
READY_330K4_DECISION = "REVIEWED_EXPORT_REFRESH_330K4_READY_FOR_PREVIEW_REVIEW"
READY_331A_DECISION = "DEMO_PACKAGING_331A_READY_FOR_PRESENTATION_AND_330K2_HUMAN_UNIT_REVIEW"
READY_DECISION = "DEMO_RELEASE_AUDIT_332A_READY_FOR_FINAL_DEMO_USE"
NOT_READY_DECISION = "DEMO_RELEASE_AUDIT_332A_NOT_READY"

DEFAULT_DEMO_PACKAGING_331B_DIR = Path(r"D:\_datefac\output\demo_packaging_331b")
DEFAULT_REVIEWED_EXPORT_REFRESH_DIR = Path(r"D:\_datefac\output\reviewed_export_refresh_330k4")
DEFAULT_DEMO_PACKAGING_331A_DIR = Path(r"D:\_datefac\output\demo_packaging_331a")
DEFAULT_DOCS_DEMO_DIR = Path(r"D:\_datefac\docs\demo")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\demo_release_audit_332a")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "temp",
]
DOC_FILENAMES = {
    "overview": "datefac_demo_overview_331b.md",
    "resume": "datefac_resume_bullets_331b.md",
    "readme": "datefac_github_readme_section_331b.md",
    "script": "datefac_demo_script_331b.md",
}
OPTIONAL_DOC_FILENAMES = {
    "release_checklist": "datefac_demo_release_checklist_332a.md",
    "interview_talking_points": "datefac_interview_talking_points_332a.md",
}
EXPECTED_METRICS = {
    "original_trusted_sheet_row_count": 96,
    "reviewed_unit_confirmed_count": 2,
    "reviewed_trusted_preview_row_count": 98,
    "human_rejected_row_count": 18,
    "remaining_review_required_after_unit_review_count": 1,
    "apply_plan_row_count": 21,
}
OVERCLAIM_TOKENS = [
    "production deployment",
    "production deployed",
    "client delivery ready",
    "guaranteed extraction accuracy",
    "automatic correctness",
    "commercial readiness",
    "full-scale commercial readiness",
]


def validate_331b_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("readiness::331b_decision", _norm_text(summary.get("decision")) == READY_331B_DECISION, _norm_text(summary.get("decision")))
    add("readiness::331b_qa_fail_count", _safe_int(summary.get("qa_fail_count"), 1) == 0, str(summary.get("qa_fail_count", "")))
    add("quality::331b_project_status", _norm_text(summary.get("project_status")) == "DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW", _norm_text(summary.get("project_status")))
    add("quality::331b_client_ready", bool(summary.get("client_ready")) is False, str(summary.get("client_ready", "")))
    add("quality::331b_production_ready", bool(summary.get("production_ready")) is False, str(summary.get("production_ready", "")))
    for key, expected in EXPECTED_METRICS.items():
        add(f"quality::331b_{key}", _safe_int(summary.get(key), -1) == expected, str(summary.get(key, "")))
    add("safety::331b_no_official_asset_modification", bool(summary.get("no_official_asset_modification_during_331b")) is True, str(summary.get("no_official_asset_modification_during_331b", "")))
    return checks


def validate_330k4_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("readiness::330k4_decision", _norm_text(summary.get("decision")) == READY_330K4_DECISION, _norm_text(summary.get("decision")))
    add("readiness::330k4_qa_fail_count", _safe_int(summary.get("qa_fail_count"), 1) == 0, str(summary.get("qa_fail_count", "")))
    for key, expected in EXPECTED_METRICS.items():
        add(f"quality::330k4_{key}", _safe_int(summary.get(key), -1) == expected, str(summary.get(key, "")))
    return checks


def validate_331a_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("readiness::331a_decision", _norm_text(summary.get("decision")) == READY_331A_DECISION, _norm_text(summary.get("decision")))
    add("readiness::331a_qa_fail_count", _safe_int(summary.get("qa_fail_count"), 1) == 0, str(summary.get("qa_fail_count", "")))
    add("quality::331a_project_status", _norm_text(summary.get("project_status")) == "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS", _norm_text(summary.get("project_status")))
    return checks


def _file_sha256(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_status_porcelain_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_cached_names_for_paths(paths: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _contains_forbidden_claim(text: str, forbidden: Sequence[str]) -> bool:
    lowered = text.casefold()
    for token in forbidden:
        if token.casefold() in lowered:
            return True
    return False


def _load_doc(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _extract_metric_values(text: str) -> Dict[str, int]:
    patterns = {
        "original_trusted_sheet_row_count": [
            r"Original trusted preview rows:\s*(\d+)",
            r"from a\s*(\d+)-row trusted preview baseline",
            r"from\s*(\d+)\s*baseline trusted rows",
        ],
        "reviewed_unit_confirmed_count": [
            r"Reviewed unit-confirmed rows added or surfaced:\s*(\d+)",
            r"(\d+)\s+reviewed unit-confirmed rows",
        ],
        "reviewed_trusted_preview_row_count": [
            r"Reviewed trusted preview rows:\s*(\d+)",
            r"to a\s*(\d+)-row reviewed trusted preview",
            r"(\d+)\s+reviewed trusted rows",
            r"to\s*(\d+)\s*reviewed trusted rows",
        ],
        "human_rejected_row_count": [
            r"Human-rejected rows isolated from trusted preview:\s*(\d+)",
            r"(\d+)\s+human-rejected rows",
            r"(\d+)\s+rows were isolated from trusted preview",
            r"(\d+)\s+rows isolated from trusted preview",
        ],
        "remaining_review_required_after_unit_review_count": [
            r"Remaining review-required rows after unit review:\s*(\d+)",
            r"(\d+)\s+remaining review-required row",
            r"(\d+)\s+row remains review-required",
            r"(\d+)\s+row kept review-required",
        ],
        "apply_plan_row_count": [
            r"apply_plan_row_count\s*=\s*(\d+)",
            r"apply plan.*?(\d+)\s+rows",
        ],
    }
    out: Dict[str, int] = {}
    for key, key_patterns in patterns.items():
        for pattern in key_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                out[key] = int(match.group(1))
                break
    return out


def _doc_has_boundary_terms(text: str) -> Dict[str, bool]:
    lowered = text.casefold()
    return {
        "sidecar": "sidecar" in lowered,
        "demo": "demo" in lowered,
        "preview": "preview" in lowered,
        "no_write_back": "no write-back" in lowered or "no-write-back" in lowered or "without write-back" in lowered,
        "not_client_ready": (
            "not client-ready" in lowered
            or "not client ready" in lowered
            or "non-client" in lowered
            or "not a client-ready" in lowered
        ),
        "not_production_ready": (
            "not production-ready" in lowered
            or "not production ready" in lowered
            or "non-production" in lowered
            or "not a production" in lowered
        ),
    }


def _build_checklist_markdown(summary_331b: Mapping[str, Any], summary_330k4: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Demo Release Checklist 332A",
            "",
            "## 1. Safe To Show On GitHub",
            "- Sidecar trust-routing architecture and preview packaging flow",
            f"- Reviewed preview metrics: { _safe_int(summary_330k4.get('reviewed_trusted_preview_row_count'), 0) } reviewed trusted rows, { _safe_int(summary_330k4.get('human_rejected_row_count'), 0) } human-rejected rows, { _safe_int(summary_330k4.get('remaining_review_required_after_unit_review_count'), 0) } remaining review-required row",
            "- Provenance preservation, manual unit review isolation, and no-write-back boundaries",
            "- Conservative demo docs that explicitly stay below client-ready and production-ready claims",
            "",
            "## 2. Safe To Say In Interview",
            "- Parser quality is necessary but not sufficient because trust depends on units, provenance, and routing decisions",
            "- Human unit review was intentionally isolated before any write-back or official export refresh",
            "- 331A established the demo-ready baseline and 331B shows the reviewed preview state after manual review feedback",
            "- The system prefers conservative review-required routing over false trust promotion",
            "",
            "## 3. Must Not Claim",
            "- Production deployment or production routing changes",
            "- Client delivery readiness or client-ready export quality",
            "- Guaranteed extraction accuracy or automatic correctness",
            "- Full-scale commercial readiness",
            "- Official asset write-back or production workbook refresh",
            "",
            "## 4. Known Limitations",
            f"- Project status remains {_norm_text(summary_331b.get('project_status'))}",
            "- Sidecar preview only; no production pipeline changes",
            "- One row remains review-required after unit review",
            "- Review outcomes are surfaced conservatively rather than auto-applied into official outputs",
            "",
            "## 5. Suggested Next Engineering Milestones",
            "- Add a safe write-back planning stage with explicit human approval gates",
            "- Expand deterministic consistency checks for more doc and metric variants",
            "- Broaden preview audit coverage for additional demo narratives and artifacts",
            "- Keep parser, provenance, and review-layer evidence aligned before any production promotion",
            "",
        ]
    )


def _build_interview_talking_points() -> str:
    return "\n".join(
        [
            "# Interview Talking Points 332A",
            "",
            "## Why Parser Quality Alone Is Not Enough",
            "A parser can recover text and table cells, but downstream trust still depends on whether the metric label, unit, year alignment, and provenance are all coherent. Good raw extraction does not automatically mean a row is safe to trust.",
            "",
            "## Why Unit Review Matters",
            "Unit ambiguity can silently flip the meaning of a value. By forcing a human review stage for unit-risk rows, the system avoids treating weakly supported rows as trusted output.",
            "",
            "## How Trust Routing Works",
            "The system keeps sidecar trust scoring separate from production routing. Rows with strong evidence and clean risk profiles surface into trusted preview, while ambiguous rows stay review-required and risky rows can be isolated.",
            "",
            "## Why Human Review Is Isolated Before Write-Back",
            "Write-back creates a much higher correctness bar. Isolating manual review outcomes in a dry-run and reviewed-preview path preserves traceability and avoids accidentally promoting unresolved rows into official assets.",
            "",
            "## What Changed From 331A To 331B",
            "331A packaged a demo-ready baseline with unit review caveats. 330K2 collected unit-review rows, 330K3 simulated applying decisions without write-back, 330K4 refreshed the reviewed preview, and 331B updated the demo narrative around that safer reviewed state.",
            "",
        ]
    )


def build_demo_release_audit_332a(
    *,
    demo_packaging_331b_dir: Path,
    reviewed_export_refresh_dir: Path,
    demo_packaging_331a_dir: Path,
    docs_demo_dir: Path,
    output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_331b_path = demo_packaging_331b_dir / "demo_packaging_331b_summary.json"
    summary_330k4_path = reviewed_export_refresh_dir / "reviewed_export_refresh_330k4_summary.json"
    summary_331a_path = demo_packaging_331a_dir / "demo_packaging_331a_summary.json"

    summary_331b = _read_json(summary_331b_path)
    summary_330k4 = _read_json(summary_330k4_path)
    summary_331a = _read_json(summary_331a_path)

    doc_paths = {key: docs_demo_dir / filename for key, filename in DOC_FILENAMES.items()}
    docs_payload = {key: _load_doc(path) for key, path in doc_paths.items()}

    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    qa_rows = validate_331b_summary(summary_331b)
    qa_rows.extend(validate_330k4_summary(summary_330k4))
    qa_rows.extend(validate_331a_summary(summary_331a))

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    official_assets_before = {
        str(alias_asset_path): _file_sha256(alias_asset_path),
        str(scope_asset_path): _file_sha256(scope_asset_path),
    }
    input_hashes_before = {
        str(summary_331b_path): _file_sha256(summary_331b_path),
        str(summary_330k4_path): _file_sha256(summary_330k4_path),
        str(summary_331a_path): _file_sha256(summary_331a_path),
        **{str(path): _file_sha256(path) for path in doc_paths.values()},
    }

    for key, path in doc_paths.items():
        add_qa(f"inputs::doc_exists::{key}", path.exists(), str(path))
    add_qa("inputs::331b_summary_exists", summary_331b_path.exists(), str(summary_331b_path))
    add_qa("inputs::330k4_summary_exists", summary_330k4_path.exists(), str(summary_330k4_path))
    add_qa("inputs::331a_summary_exists", summary_331a_path.exists(), str(summary_331a_path))

    doc_metrics = {key: _extract_metric_values(text) for key, text in docs_payload.items()}
    boundary_checks = {key: _doc_has_boundary_terms(text) for key, text in docs_payload.items()}
    overclaim_hits = {
        key: [token for token in OVERCLAIM_TOKENS if token.casefold() in text.casefold()]
        for key, text in docs_payload.items()
    }
    overclaim_hits = {key: hits for key, hits in overclaim_hits.items() if hits}

    for doc_key, checks in boundary_checks.items():
        add_qa(
            f"claims::not_client_ready::{doc_key}",
            checks["not_client_ready"],
            json.dumps(checks, ensure_ascii=False),
        )
        add_qa(
            f"claims::not_production_ready::{doc_key}",
            checks["not_production_ready"],
            json.dumps(checks, ensure_ascii=False),
        )

    combined_text = "\n".join(docs_payload.values())
    combined_boundary = _doc_has_boundary_terms(combined_text)
    add_qa("boundaries::combined_sidecar_mentions", combined_boundary["sidecar"], json.dumps(combined_boundary, ensure_ascii=False))
    add_qa("boundaries::combined_demo_mentions", combined_boundary["demo"], json.dumps(combined_boundary, ensure_ascii=False))
    add_qa("boundaries::combined_preview_mentions", combined_boundary["preview"], json.dumps(combined_boundary, ensure_ascii=False))
    add_qa("boundaries::combined_no_write_back_mentions", combined_boundary["no_write_back"], json.dumps(combined_boundary, ensure_ascii=False))

    add_qa(
        "claims::no_overclaim_tokens",
        len(overclaim_hits) == 0,
        json.dumps(overclaim_hits, ensure_ascii=False),
    )

    # Metric consistency checks for docs that explicitly mention metrics.
    metric_doc_expectations = {
        "overview": [
            "original_trusted_sheet_row_count",
            "reviewed_unit_confirmed_count",
            "reviewed_trusted_preview_row_count",
            "human_rejected_row_count",
            "remaining_review_required_after_unit_review_count",
        ],
        "resume": [
            "original_trusted_sheet_row_count",
            "reviewed_unit_confirmed_count",
            "reviewed_trusted_preview_row_count",
            "human_rejected_row_count",
            "remaining_review_required_after_unit_review_count",
        ],
        "readme": [
            "reviewed_trusted_preview_row_count",
            "human_rejected_row_count",
            "remaining_review_required_after_unit_review_count",
        ],
        "script": [
            "original_trusted_sheet_row_count",
            "reviewed_trusted_preview_row_count",
            "human_rejected_row_count",
            "remaining_review_required_after_unit_review_count",
        ],
    }
    metric_consistency_failures: Dict[str, Dict[str, Any]] = {}
    for doc_key, expected_keys in metric_doc_expectations.items():
        found = doc_metrics.get(doc_key, {})
        failures: Dict[str, Any] = {}
        for metric_key in expected_keys:
            expected = EXPECTED_METRICS[metric_key]
            if found.get(metric_key) != expected:
                failures[metric_key] = {"expected": expected, "found": found.get(metric_key)}
        if failures:
            metric_consistency_failures[doc_key] = failures
        add_qa(
            f"metrics::consistent::{doc_key}",
            len(failures) == 0,
            json.dumps({"found": found, "failures": failures}, ensure_ascii=False),
        )

    checklist_md = _build_checklist_markdown(summary_331b, summary_330k4)
    interview_md = _build_interview_talking_points()

    output_dir.mkdir(parents=True, exist_ok=True)
    checklist_output_path = output_dir / "demo_release_audit_332a_checklist.md"
    report_output_path = output_dir / "demo_release_audit_332a_report.md"
    checklist_output_path.write_text(checklist_md, encoding="utf-8")

    optional_doc_paths = {
        "release_checklist": docs_demo_dir / OPTIONAL_DOC_FILENAMES["release_checklist"],
        "interview_talking_points": docs_demo_dir / OPTIONAL_DOC_FILENAMES["interview_talking_points"],
    }
    optional_doc_paths["release_checklist"].write_text(checklist_md, encoding="utf-8")
    optional_doc_paths["interview_talking_points"].write_text(interview_md, encoding="utf-8")
    optional_docs_written = {key: str(path) for key, path in optional_doc_paths.items()}
    add_qa("outputs::optional_docs_written", all(path.exists() for path in optional_doc_paths.values()), json.dumps(optional_docs_written, ensure_ascii=False))

    input_hashes_after = {
        str(summary_331b_path): _file_sha256(summary_331b_path),
        str(summary_330k4_path): _file_sha256(summary_330k4_path),
        str(summary_331a_path): _file_sha256(summary_331a_path),
        **{str(path): _file_sha256(path) for path in doc_paths.values()},
    }
    add_qa(
        "safety::input_artifacts_unchanged",
        input_hashes_before == input_hashes_after,
        json.dumps({"before": input_hashes_before, "after": input_hashes_after}, ensure_ascii=False),
    )

    official_assets_after = {
        str(alias_asset_path): _file_sha256(alias_asset_path),
        str(scope_asset_path): _file_sha256(scope_asset_path),
    }
    no_official_asset_modification_during_332a = official_assets_before == official_assets_after
    add_qa(
        "safety::official_assets_unchanged",
        no_official_asset_modification_during_332a,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    protected_staged = _git_cached_names_for_paths(PROTECTED_DIRTY_PATHS)
    add_qa(
        "safety::protected_dirty_files_state_unchanged",
        protected_before == protected_after,
        json.dumps({"before": protected_before, "after": protected_after}, ensure_ascii=False),
    )
    add_qa(
        "safety::protected_dirty_files_not_staged",
        len(protected_staged) == 0,
        json.dumps(protected_staged, ensure_ascii=False),
    )

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    doc_consistency_passed = len(metric_consistency_failures) == 0
    summary = {
        "stage": "332A",
        "output_dir": str(output_dir),
        "validated_331b_demo_packaging": all(row.get("status") == "PASS" for row in validate_331b_summary(summary_331b)),
        "validated_330k4_reviewed_export_refresh": all(row.get("status") == "PASS" for row in validate_330k4_summary(summary_330k4)),
        "validated_331a_demo_packaging": all(row.get("status") == "PASS" for row in validate_331a_summary(summary_331a)),
        "project_status": _norm_text(summary_331b.get("project_status")),
        "client_ready": False,
        "production_ready": False,
        "reviewed_trusted_preview_row_count": _safe_int(summary_330k4.get("reviewed_trusted_preview_row_count"), 0),
        "human_rejected_row_count": _safe_int(summary_330k4.get("human_rejected_row_count"), 0),
        "remaining_review_required_after_unit_review_count": _safe_int(summary_330k4.get("remaining_review_required_after_unit_review_count"), 0),
        "apply_plan_row_count": _safe_int(summary_330k4.get("apply_plan_row_count"), 0),
        "doc_consistency_passed": doc_consistency_passed,
        "overclaim_risk_count": sum(len(v) for v in overclaim_hits.values()),
        "optional_docs_written": optional_docs_written,
        "no_official_asset_modification_during_332a": no_official_asset_modification_during_332a,
        "qa_pass_count": qa_pass_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    report_md = "\n".join(
        [
            "# Demo Release Audit 332A",
            "",
            "## Decision",
            f"- decision: {summary['decision']}",
            "",
            "## Audit State",
            f"- project_status: {summary['project_status']}",
            f"- client_ready: {summary['client_ready']}",
            f"- production_ready: {summary['production_ready']}",
            "",
            "## Metrics",
            f"- reviewed_trusted_preview_row_count: {summary['reviewed_trusted_preview_row_count']}",
            f"- human_rejected_row_count: {summary['human_rejected_row_count']}",
            f"- remaining_review_required_after_unit_review_count: {summary['remaining_review_required_after_unit_review_count']}",
            f"- apply_plan_row_count: {summary['apply_plan_row_count']}",
            "",
            "## Audit Results",
            f"- doc_consistency_passed: {summary['doc_consistency_passed']}",
            f"- overclaim_risk_count: {summary['overclaim_risk_count']}",
            f"- no_official_asset_modification_during_332a: {summary['no_official_asset_modification_during_332a']}",
            f"- qa_fail_count: {summary['qa_fail_count']}",
            "",
        ]
    )
    report_output_path.write_text(report_md, encoding="utf-8")

    manifest = {
        "stage": "332A",
        "input_files": [
            str(summary_331b_path),
            str(summary_330k4_path),
            str(summary_331a_path),
            *[str(path) for path in doc_paths.values()],
        ],
        "output_dir": str(output_dir),
        "checklist_output_path": str(checklist_output_path),
        "report_output_path": str(report_output_path),
        "optional_docs_written": optional_docs_written,
        "doc_metric_extracts": doc_metrics,
        "boundary_checks": boundary_checks,
        "overclaim_hits": overclaim_hits,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    no_apply_proof_json = build_no_apply_proof(
        stage="332A",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "checklist_md": checklist_md,
        "report_md": report_md,
        "summary_df": _frame_for_output(pd.DataFrame([summary])),
        "qa_summary_df": _frame_for_output(pd.DataFrame([{"qa_pass_count": qa_pass_count, "qa_fail_count": qa_fail_count, "decision": summary["decision"]}])),
        "qa_checks_df": qa_df,
        "doc_audit_df": _frame_for_output(
            pd.DataFrame(
                [
                    {
                        "doc_name": key,
                        "path": str(doc_paths[key]),
                        "metrics_found": json.dumps(doc_metrics.get(key, {}), ensure_ascii=False),
                        "boundary_checks": json.dumps(boundary_checks.get(key, {}), ensure_ascii=False),
                        "overclaim_hits": json.dumps(overclaim_hits.get(key, []), ensure_ascii=False),
                    }
                    for key in doc_paths
                ]
            )
        ),
    }
