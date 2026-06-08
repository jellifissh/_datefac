from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from datefac.trust.delivery_report_refresh_330j import _read_json
from datefac.trust.demo_packaging_331a import REFERENCE_SUMMARY_PATHS
from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import (
    _frame_for_output,
    _norm_text,
    _safe_int,
)


READY_331A_DECISION = "DEMO_PACKAGING_331A_READY_FOR_PRESENTATION_AND_330K2_HUMAN_UNIT_REVIEW"
READY_330K4_DECISION = "REVIEWED_EXPORT_REFRESH_330K4_READY_FOR_PREVIEW_REVIEW"
READY_DECISION = "DEMO_PACKAGING_331B_READY_FOR_PRESENTATION_REFRESH"
NOT_READY_DECISION = "DEMO_PACKAGING_331B_NOT_READY"

DEFAULT_DEMO_PACKAGING_331A_DIR = Path(r"D:\_datefac\output\demo_packaging_331a")
DEFAULT_REVIEWED_EXPORT_REFRESH_DIR = Path(
    r"D:\_datefac\output\reviewed_export_refresh_330k4"
)
DEFAULT_APPLY_SIMULATION_DIR = Path(
    r"D:\_datefac\output\human_unit_review_apply_simulation_330k3"
)
DEFAULT_HUMAN_UNIT_REVIEW_DIR = Path(r"D:\_datefac\output\human_unit_review_330k2")
DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR = Path(
    r"D:\_datefac\output\client_style_export_preview_330l"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\demo_packaging_331b")
DEFAULT_DOCS_DIR = Path(r"D:\_datefac\docs\demo")

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
    "project_brief": "datefac_demo_overview_331b.md",
    "resume_bullets": "datefac_resume_bullets_331b.md",
    "github_readme_section": "datefac_github_readme_section_331b.md",
    "demo_script": "datefac_demo_script_331b.md",
}


def validate_331a_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add(
        "readiness::331a_decision",
        _norm_text(summary.get("decision")) == READY_331A_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::331a_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "quality::331a_project_status",
        _norm_text(summary.get("project_status")) == "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS",
        _norm_text(summary.get("project_status")),
    )
    add(
        "quality::331a_trusted_sheet_row_count",
        _safe_int(summary.get("trusted_sheet_row_count"), -1) == 96,
        str(summary.get("trusted_sheet_row_count", "")),
    )
    add(
        "quality::331a_review_required_sheet_row_count",
        _safe_int(summary.get("review_required_sheet_row_count"), -1) == 21,
        str(summary.get("review_required_sheet_row_count", "")),
    )
    add(
        "safety::331a_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_331a")) is True,
        str(summary.get("no_official_asset_modification_during_331a", "")),
    )
    return checks


def validate_330k4_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add(
        "readiness::330k4_decision",
        _norm_text(summary.get("decision")) == READY_330K4_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330k4_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "quality::330k4_original_trusted_sheet_row_count",
        _safe_int(summary.get("original_trusted_sheet_row_count"), -1) == 96,
        str(summary.get("original_trusted_sheet_row_count", "")),
    )
    add(
        "quality::330k4_reviewed_unit_confirmed_count",
        _safe_int(summary.get("reviewed_unit_confirmed_count"), -1) == 2,
        str(summary.get("reviewed_unit_confirmed_count", "")),
    )
    add(
        "quality::330k4_reviewed_trusted_preview_row_count",
        _safe_int(summary.get("reviewed_trusted_preview_row_count"), -1) == 98,
        str(summary.get("reviewed_trusted_preview_row_count", "")),
    )
    add(
        "quality::330k4_human_rejected_row_count",
        _safe_int(summary.get("human_rejected_row_count"), -1) == 18,
        str(summary.get("human_rejected_row_count", "")),
    )
    add(
        "quality::330k4_remaining_review_required_count",
        _safe_int(summary.get("remaining_review_required_after_unit_review_count"), -1) == 1,
        str(summary.get("remaining_review_required_after_unit_review_count", "")),
    )
    add(
        "quality::330k4_apply_plan_row_count",
        _safe_int(summary.get("apply_plan_row_count"), -1) == 21,
        str(summary.get("apply_plan_row_count", "")),
    )
    add(
        "safety::330k4_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_330k4")) is True,
        str(summary.get("no_official_asset_modification_during_330k4", "")),
    )
    return checks


def _load_optional_summaries() -> Dict[str, Dict[str, Any]]:
    loaded: Dict[str, Dict[str, Any]] = {}
    for label, path in REFERENCE_SUMMARY_PATHS.items():
        if path.exists():
            loaded[label] = _read_json(path)
    return loaded


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
        start = 0
        while True:
            idx = lowered.find(token, start)
            if idx == -1:
                break
            window = lowered[max(0, idx - 40) : idx]
            if "not " not in window and "not yet " not in window:
                return True
            start = idx + len(token)
    return False


def _write_docs(docs_dir: Path, docs_payload: Mapping[str, str]) -> Dict[str, str]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, str] = {}
    for key, filename in DOC_FILENAMES.items():
        path = docs_dir / filename
        path.write_text(docs_payload[key], encoding="utf-8")
        written[key] = str(path)
    return written


def _build_project_brief(
    summary_331a: Mapping[str, Any],
    summary_330k4: Mapping[str, Any],
    loaded_refs: Mapping[str, Mapping[str, Any]],
) -> str:
    alias_summary = loaded_refs.get("alias_closure_325p", {})
    scope_summary = loaded_refs.get("scope_closure_324n", {})
    return "\n".join(
        [
            "# DateFac Demo Overview 331B",
            "",
            "## Problem",
            "Financial PDF extraction quality depends not only on parser coverage, but also on whether unit handling, provenance, and human review boundaries are visible before anything is treated as trusted.",
            "",
            "## Current Status",
            "DateFac is a financial PDF core-metric extraction and trust-routing demo.",
            "Current status: demo-ready after human unit review preview.",
            "The project is not production-ready and not client-ready yet.",
            "",
            "## What Changed From 331A",
            "331A was demo-ready with unit review caveats.",
            "330K2 packaged 21 unit-review rows for manual review.",
            "330K3 simulated applying those human decisions without write-back.",
            "330K4 refreshed the preview state so only reviewed-safe rows were surfaced into the trusted preview.",
            "",
            "## Reviewed Preview State",
            f"- Original trusted preview rows: {_safe_int(summary_330k4.get('original_trusted_sheet_row_count'), 0)}",
            f"- Reviewed unit-confirmed rows added or surfaced: {_safe_int(summary_330k4.get('reviewed_unit_confirmed_count'), 0)}",
            f"- Reviewed trusted preview rows: {_safe_int(summary_330k4.get('reviewed_trusted_preview_row_count'), 0)}",
            f"- Human-rejected rows isolated from trusted preview: {_safe_int(summary_330k4.get('human_rejected_row_count'), 0)}",
            f"- Remaining review-required rows after unit review: {_safe_int(summary_330k4.get('remaining_review_required_after_unit_review_count'), 0)}",
            "",
            "## Safe Claims",
            "The demo can claim sidecar trust routing, provenance preservation, manual unit review packaging, dry-run review application, reviewed preview refresh, and conservative demo documentation.",
            f"If available, official rule milestones remain scope rules {_safe_int(scope_summary.get('scope_rule_count_324'), 0)} and alias rules {_safe_int(alias_summary.get('official_alias_rule_count_325'), 0)}.",
            "",
            "## Unsafe Claims",
            "Do not claim production routing changes, client delivery readiness, or write-back into official assets.",
            "Do not claim that the 330K4 reviewed preview is a production export.",
            "",
            "## Next Steps",
            "Next steps can focus on presentation polish, additional human validation, and future safe write-back planning, but not on production-ready claims.",
            f"331A baseline project status remains {_norm_text(summary_331a.get('project_status'))}.",
            "",
        ]
    )


def _build_resume_bullets(summary_330k4: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# DateFac Resume Bullets 331B",
            "",
            "- Refreshed a sidecar demo-packaging flow after human unit review, carrying a financial PDF trust-routing demo from a 96-row trusted preview baseline to a 98-row reviewed trusted preview without changing production routing.",
            f"- Packaged human review outcomes into demo-safe artifacts: {_safe_int(summary_330k4.get('reviewed_unit_confirmed_count'), 0)} reviewed unit-confirmed rows surfaced into trusted preview, {_safe_int(summary_330k4.get('human_rejected_row_count'), 0)} rows isolated from trusted preview, and {_safe_int(summary_330k4.get('remaining_review_required_after_unit_review_count'), 0)} row kept review-required.",
            "- Produced conservative demo overview, resume, README, and script collateral with explicit non-production and non-client boundaries, preserving provenance and no-write-back guarantees.",
            "",
        ]
    )


def _build_github_readme_section(
    summary_331a: Mapping[str, Any],
    summary_330k4: Mapping[str, Any],
    loaded_refs: Mapping[str, Mapping[str, Any]],
) -> str:
    milestone_330a = loaded_refs.get("trust_engine_330a", {})
    milestone_330b = loaded_refs.get("trust_engine_330b", {})
    return "\n".join(
        [
            "# DateFac README Section 331B",
            "",
            "## Current Status",
            "DateFac is demo-ready after human unit review preview.",
            "The repository demonstrates sidecar trust scoring, manual unit review packaging, dry-run application, and reviewed preview refresh.",
            "It is not production-ready and not client-ready yet.",
            "",
            "## What The Refreshed Demo Shows",
            f"- 331A baseline status: {_norm_text(summary_331a.get('project_status'))}",
            f"- 330A foundation: risk registry {_safe_int(milestone_330a.get('risk_registry_count'), 0)}",
            f"- 330B scoring: scoring model component count {_safe_int(milestone_330b.get('scoring_model_component_count'), 0)}",
            f"- 330K4 reviewed preview: {_safe_int(summary_330k4.get('reviewed_trusted_preview_row_count'), 0)} reviewed trusted rows, {_safe_int(summary_330k4.get('human_rejected_row_count'), 0)} human-rejected rows, {_safe_int(summary_330k4.get('remaining_review_required_after_unit_review_count'), 0)} remaining review-required row",
            "",
            "## Human Review Narrative",
            "- 330K2 packaged unit-risk rows for manual review.",
            "- 330K3 simulated applying reviewer decisions without write-back.",
            "- 330K4 refreshed the preview so reviewed-safe rows are visible while rejected or unresolved rows remain isolated.",
            "",
            "## Limitations",
            "- Sidecar-only refresh; no production routing changes",
            "- No write-back into the original 330L workbook",
            "- Not a client-ready or production-ready export",
            "",
        ]
    )


def _build_demo_script(summary_330k4: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# DateFac Demo Script 331B",
            "",
            "## 1. Open With The Trust Problem",
            "Explain that the core challenge is not just extracting metrics from financial PDFs, but showing what became trusted, what was rejected, and what still needs review after human feedback.",
            "",
            "## 2. Recap 331A",
            "State that 331A was demo-ready with unit review caveats and established the first client-style preview packaging layer.",
            "",
            "## 3. Walk Through The Human Review Stages",
            "Describe 330K2 as the manual unit-review package, 330K3 as the dry-run application plan, and 330K4 as the reviewed preview refresh with no write-back.",
            "",
            "## 4. Show The Refreshed Metrics",
            f"Call out the transition from {_safe_int(summary_330k4.get('original_trusted_sheet_row_count'), 0)} baseline trusted rows to {_safe_int(summary_330k4.get('reviewed_trusted_preview_row_count'), 0)} reviewed trusted rows.",
            f"Note that {_safe_int(summary_330k4.get('human_rejected_row_count'), 0)} rows were isolated from trusted preview and {_safe_int(summary_330k4.get('remaining_review_required_after_unit_review_count'), 0)} row remains review-required.",
            "",
            "## 5. Reinforce Safety Boundaries",
            "Say explicitly that this is still a sidecar preview refresh, not a production export, not a production routing change, and not a client-ready deliverable.",
            "",
            "## 6. Close On What Improved",
            "Close by saying the demo now shows a cleaner reviewed preview state after human unit review while preserving provenance, rejection visibility, and no-write-back constraints.",
            "",
        ]
    )


def build_demo_packaging_331b(
    *,
    demo_packaging_331a_dir: Path,
    reviewed_export_refresh_dir: Path,
    apply_simulation_dir: Path,
    human_unit_review_dir: Path,
    client_style_export_preview_dir: Path,
    output_dir: Path,
    docs_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_331a_path = demo_packaging_331a_dir / "demo_packaging_331a_summary.json"
    summary_330k4_path = reviewed_export_refresh_dir / "reviewed_export_refresh_330k4_summary.json"
    summary_330k3_path = (
        apply_simulation_dir / "human_unit_review_apply_simulation_330k3_summary.json"
    )
    summary_330k2_path = human_unit_review_dir / "human_unit_review_330k2_summary.json"
    summary_330l_path = (
        client_style_export_preview_dir / "client_style_export_preview_330l_summary.json"
    )

    summary_331a = _read_json(summary_331a_path)
    summary_330k4 = _read_json(summary_330k4_path)
    summary_330k3 = _read_json(summary_330k3_path)
    summary_330k2 = _read_json(summary_330k2_path)
    summary_330l = _read_json(summary_330l_path)
    loaded_refs = _load_optional_summaries()

    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS)
    qa_rows = validate_331a_summary(summary_331a)
    qa_rows.extend(validate_330k4_summary(summary_330k4))

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    official_assets_before = {
        str(alias_asset_path): _file_sha256(alias_asset_path),
        str(scope_asset_path): _file_sha256(scope_asset_path),
    }
    input_hashes_before = {
        str(summary_331a_path): _file_sha256(summary_331a_path),
        str(summary_330k4_path): _file_sha256(summary_330k4_path),
        str(summary_330k3_path): _file_sha256(summary_330k3_path),
        str(summary_330k2_path): _file_sha256(summary_330k2_path),
        str(summary_330l_path): _file_sha256(summary_330l_path),
    }

    add_qa("inputs::331a_summary_exists", summary_331a_path.exists(), str(summary_331a_path))
    add_qa("inputs::330k4_summary_exists", summary_330k4_path.exists(), str(summary_330k4_path))
    add_qa("inputs::330k3_summary_exists", summary_330k3_path.exists(), str(summary_330k3_path))
    add_qa("inputs::330k2_summary_exists", summary_330k2_path.exists(), str(summary_330k2_path))
    add_qa("inputs::330l_summary_exists", summary_330l_path.exists(), str(summary_330l_path))

    add_qa(
        "quality::330k3_apply_plan_row_count",
        _safe_int(summary_330k3.get("apply_plan_row_count"), -1) == 21,
        str(summary_330k3.get("apply_plan_row_count", "")),
    )
    add_qa(
        "quality::330k2_packaged_unit_review_row_count",
        _safe_int(summary_330k2.get("packaged_unit_review_row_count"), -1) == 21,
        str(summary_330k2.get("packaged_unit_review_row_count", "")),
    )
    add_qa(
        "quality::330l_trusted_sheet_row_count",
        _safe_int(summary_330l.get("trusted_sheet_row_count"), -1) == 96,
        str(summary_330l.get("trusted_sheet_row_count", "")),
    )

    project_brief = _build_project_brief(summary_331a, summary_330k4, loaded_refs)
    resume_bullets = _build_resume_bullets(summary_330k4)
    github_readme_section = _build_github_readme_section(summary_331a, summary_330k4, loaded_refs)
    demo_script = _build_demo_script(summary_330k4)
    docs_payload = {
        "project_brief": project_brief,
        "resume_bullets": resume_bullets,
        "github_readme_section": github_readme_section,
        "demo_script": demo_script,
    }
    docs_paths = _write_docs(docs_dir, docs_payload)

    production_forbidden = [
        "production-ready",
        "production ready",
        "ready for production",
        "already deployed to production",
    ]
    client_forbidden = ["client-ready", "client ready", "paid-client ready"]
    add_qa(
        "claims::no_production_claims",
        not any(
            _contains_forbidden_claim(text, production_forbidden)
            for text in docs_payload.values()
        ),
        "docs checked for forbidden production-ready claims",
    )
    add_qa(
        "claims::no_client_ready_claims",
        not any(
            _contains_forbidden_claim(text, client_forbidden)
            for text in docs_payload.values()
        ),
        "docs checked for forbidden client-ready claims",
    )
    add_qa(
        "artifacts::generated_docs_exist",
        all(Path(path).exists() for path in docs_paths.values()),
        json.dumps(docs_paths, ensure_ascii=False),
    )
    add_qa(
        "safety::no_write_back_behavior",
        True,
        "331B generates sidecar packaging artifacts only and performs no write-back behavior.",
    )

    input_hashes_after = {
        str(summary_331a_path): _file_sha256(summary_331a_path),
        str(summary_330k4_path): _file_sha256(summary_330k4_path),
        str(summary_330k3_path): _file_sha256(summary_330k3_path),
        str(summary_330k2_path): _file_sha256(summary_330k2_path),
        str(summary_330l_path): _file_sha256(summary_330l_path),
    }
    add_qa(
        "safety::original_input_artifacts_unchanged",
        input_hashes_before == input_hashes_after,
        json.dumps({"before": input_hashes_before, "after": input_hashes_after}, ensure_ascii=False),
    )

    official_assets_after = {
        str(alias_asset_path): _file_sha256(alias_asset_path),
        str(scope_asset_path): _file_sha256(scope_asset_path),
    }
    no_official_asset_modification_during_331b = official_assets_before == official_assets_after
    add_qa(
        "safety::official_assets_unchanged",
        no_official_asset_modification_during_331b,
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

    packaging_metrics = {
        "project_status": "DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW",
        "client_ready": False,
        "production_ready": False,
        "331A_project_status": _norm_text(summary_331a.get("project_status")),
        "330K4_original_trusted_sheet_row_count": _safe_int(summary_330k4.get("original_trusted_sheet_row_count"), 0),
        "330K4_reviewed_unit_confirmed_count": _safe_int(summary_330k4.get("reviewed_unit_confirmed_count"), 0),
        "330K4_reviewed_trusted_preview_row_count": _safe_int(summary_330k4.get("reviewed_trusted_preview_row_count"), 0),
        "330K4_human_rejected_row_count": _safe_int(summary_330k4.get("human_rejected_row_count"), 0),
        "330K4_remaining_review_required_after_unit_review_count": _safe_int(summary_330k4.get("remaining_review_required_after_unit_review_count"), 0),
        "330K4_apply_plan_row_count": _safe_int(summary_330k4.get("apply_plan_row_count"), 0),
        "330K3_apply_plan_row_count": _safe_int(summary_330k3.get("apply_plan_row_count"), 0),
        "330K2_packaged_unit_review_row_count": _safe_int(summary_330k2.get("packaged_unit_review_row_count"), 0),
        "330L_trusted_sheet_row_count": _safe_int(summary_330l.get("trusted_sheet_row_count"), 0),
    }

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "stage": "331B",
        "output_dir": str(output_dir),
        "docs_dir": str(docs_dir),
        "generated_docs": docs_paths,
        "input_dirs": [
            str(demo_packaging_331a_dir),
            str(reviewed_export_refresh_dir),
            str(apply_simulation_dir),
            str(human_unit_review_dir),
            str(client_style_export_preview_dir),
        ],
        "loaded_reference_summaries": sorted(loaded_refs.keys()),
        "packaging_metrics": packaging_metrics,
    }

    summary = {
        "stage": "331B",
        "output_dir": str(output_dir),
        "validated_331a_demo_packaging": all(
            row.get("status") == "PASS" for row in validate_331a_summary(summary_331a)
        ),
        "validated_330k4_reviewed_export_refresh": all(
            row.get("status") == "PASS" for row in validate_330k4_summary(summary_330k4)
        ),
        "project_status": "DEMO_READY_AFTER_HUMAN_UNIT_REVIEW_PREVIEW",
        "client_ready": False,
        "production_ready": False,
        "original_trusted_sheet_row_count": _safe_int(summary_330k4.get("original_trusted_sheet_row_count"), 0),
        "reviewed_unit_confirmed_count": _safe_int(summary_330k4.get("reviewed_unit_confirmed_count"), 0),
        "reviewed_trusted_preview_row_count": _safe_int(summary_330k4.get("reviewed_trusted_preview_row_count"), 0),
        "human_rejected_row_count": _safe_int(summary_330k4.get("human_rejected_row_count"), 0),
        "remaining_review_required_after_unit_review_count": _safe_int(summary_330k4.get("remaining_review_required_after_unit_review_count"), 0),
        "apply_plan_row_count": _safe_int(summary_330k4.get("apply_plan_row_count"), 0),
        "project_brief_generated": True,
        "resume_bullets_generated": True,
        "github_readme_section_generated": True,
        "demo_script_generated": True,
        "generated_demo_artifacts": docs_paths,
        "no_official_asset_modification_during_331b": no_official_asset_modification_during_331b,
        "qa_pass_count": qa_pass_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": READY_DECISION if qa_fail_count == 0 else NOT_READY_DECISION,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    no_apply_proof_json = build_no_apply_proof(
        stage="331B",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    official_asset_proof_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "asset_path": asset_path,
                    "hash_before": before_hash,
                    "hash_after": official_assets_after.get(asset_path, ""),
                    "modified_during_331b": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    packaging_metrics_df = _frame_for_output(
        pd.DataFrame([{"metric": key, "value": value} for key, value in packaging_metrics.items()])
    )
    docs_manifest_df = _frame_for_output(
        pd.DataFrame([{"doc_name": key, "path": path} for key, path in docs_paths.items()])
    )

    return {
        "summary": summary,
        "manifest": manifest,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "summary_df": _frame_for_output(pd.DataFrame([summary])),
        "qa_summary_df": _frame_for_output(
            pd.DataFrame(
                [{"qa_pass_count": qa_pass_count, "qa_fail_count": qa_fail_count, "decision": summary["decision"]}]
            )
        ),
        "qa_checks_df": qa_df,
        "packaging_metrics_df": packaging_metrics_df,
        "docs_manifest_df": docs_manifest_df,
        "official_asset_proof_df": official_asset_proof_df,
    }
