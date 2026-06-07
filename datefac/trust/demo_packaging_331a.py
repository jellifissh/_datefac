from __future__ import annotations

import hashlib
import json
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


READY_330L_DECISION = (
    "CLIENT_STYLE_EXPORT_PREVIEW_330L_READY_FOR_330K2_HUMAN_UNIT_REVIEW_OR_331A_DEMO_PACKAGING"
)
READY_DECISION = "DEMO_PACKAGING_331A_READY_FOR_PRESENTATION_AND_330K2_HUMAN_UNIT_REVIEW"
NOT_READY_DECISION = "DEMO_PACKAGING_331A_NOT_READY"

DEFAULT_CLIENT_STYLE_EXPORT_PREVIEW_DIR = Path(
    r"D:\_datefac\output\client_style_export_preview_330l"
)
DEFAULT_DELIVERY_REPORT_REFRESH_DIR = Path(
    r"D:\_datefac\output\delivery_report_refresh_after_330k_330j2"
)
DEFAULT_UNIT_SIGNAL_REVIEW_DIR = Path(r"D:\_datefac\output\unit_signal_review_330k")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\demo_packaging_331a")
DEFAULT_DOCS_DIR = Path(r"D:\_datefac\docs\demo")

REFERENCE_SUMMARY_PATHS = {
    "scope_closure_324n": Path(
        r"D:\_datefac\output\official_scope_patch_cycle_closure_324n\official_scope_patch_cycle_closure_324n_summary.json"
    ),
    "alias_closure_325p": Path(
        r"D:\_datefac\output\alias_patch_cycle_closure_325p\alias_patch_cycle_closure_325p_summary.json"
    ),
    "trust_engine_330a": Path(
        r"D:\_datefac\output\trust_engine_foundation_330a\trust_engine_foundation_330a_summary.json"
    ),
    "trust_engine_330b": Path(
        r"D:\_datefac\output\trust_engine_scoring_330b\trust_engine_scoring_330b_summary.json"
    ),
    "trust_engine_330c": Path(
        r"D:\_datefac\output\cached_candidate_trust_scoring_330c\cached_candidate_trust_scoring_330c_summary.json"
    ),
    "source_attribution_330i": Path(
        r"D:\_datefac\output\source_attribution_unit_signal_fix_330i\source_attribution_unit_signal_fix_330i_summary.json"
    ),
    "delivery_refresh_330j": Path(
        r"D:\_datefac\output\delivery_report_refresh_330j\delivery_report_refresh_330j_summary.json"
    ),
    "full_unfamiliar_330h": Path(
        r"D:\_datefac\output\full_unfamiliar_export_benchmark_330h\full_unfamiliar_export_benchmark_330h_summary.json"
    ),
}

DOC_FILENAMES = {
    "project_brief": "datefac_demo_overview_331a.md",
    "resume_bullets": "datefac_resume_bullets_331a.md",
    "github_readme_section": "datefac_github_readme_section_331a.md",
    "demo_script": "datefac_demo_script_331a.md",
}


def validate_330l_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append(
            {
                "check_name": name,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    add(
        "readiness::330l_decision",
        _norm_text(summary.get("decision")) == READY_330L_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330l_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "records::330l_preview_workbook_generated",
        bool(summary.get("preview_workbook_generated")) is True,
        str(summary.get("preview_workbook_generated", "")),
    )
    add(
        "records::330l_prepared_candidate_row_count",
        _safe_int(summary.get("prepared_candidate_row_count"), -1) == 117,
        str(summary.get("prepared_candidate_row_count", "")),
    )
    add(
        "records::330l_strict_deduped_candidate_count",
        _safe_int(summary.get("strict_deduped_candidate_count"), -1) == 117,
        str(summary.get("strict_deduped_candidate_count", "")),
    )
    add(
        "quality::330l_unit_missing_count",
        _safe_int(summary.get("unit_missing_count"), -1) == 18,
        str(summary.get("unit_missing_count", "")),
    )
    add(
        "quality::330l_unit_conflict_risk_count",
        _safe_int(summary.get("unit_conflict_risk_count"), -1) == 12,
        str(summary.get("unit_conflict_risk_count", "")),
    )
    add(
        "quality::330l_delivery_readiness_judgment",
        _norm_text(summary.get("delivery_readiness_judgment"))
        == "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS",
        _norm_text(summary.get("delivery_readiness_judgment")),
    )
    add(
        "safety::330l_no_official_asset_modification",
        bool(summary.get("no_official_asset_modification_during_330l")) is True,
        str(summary.get("no_official_asset_modification_during_330l", "")),
    )
    return checks


def _load_optional_summaries() -> Dict[str, Dict[str, Any]]:
    loaded: Dict[str, Dict[str, Any]] = {}
    for label, path in REFERENCE_SUMMARY_PATHS.items():
        if path.exists():
            loaded[label] = _read_json(path)
    return loaded


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


def _build_project_brief(
    summary_330l: Mapping[str, Any],
    loaded_refs: Mapping[str, Mapping[str, Any]],
) -> str:
    alias_summary = loaded_refs.get("alias_closure_325p", {})
    scope_summary = loaded_refs.get("scope_closure_324n", {})
    return "\n".join(
        [
            "# DateFac Demo Overview 331A",
            "",
            "## Problem",
            "Financial PDF core-metric extraction is difficult to trust because parser output, units, semantics, and provenance often drift before anything reaches downstream review.",
            "",
            "## System Capability",
            "DateFac is a financial PDF core-metric extraction and trust-routing demo.",
            "Current status: demo-ready with manual review caveats.",
            "The system demonstrates parser-output normalization, semantic rule curation, sidecar trust scoring, risk flagging, provenance preservation, and client-style Excel preview generation.",
            "It is not production-ready or client-ready yet.",
            "",
            "## Architecture Summary",
            "The demo uses cached parser outputs and sidecar trust artifacts rather than changing production routing.",
            "Key layers are parser-output normalization, candidate shaping, semantic-rule curation, trust scoring, risk routing, and Excel/report packaging.",
            "",
            "## Trust Engine Workflow",
            "1. Load prepared candidate rows with provenance preserved.",
            "2. Apply sidecar trust scoring and route rows into trusted vs review-required buckets.",
            "3. Surface unit-risk and conflict rows for human review instead of auto-promoting them.",
            "4. Package results into client-style preview outputs and demo-facing summaries.",
            "",
            "## Demo Output Artifacts",
            f"- 330L preview workbook: {summary_330l.get('preview_workbook_path', '')}",
            f"- Prepared candidate rows: {_safe_int(summary_330l.get('prepared_candidate_row_count'), 0)}",
            f"- Trusted preview rows: {_safe_int(summary_330l.get('trusted_sheet_row_count'), 0)}",
            f"- Review-required rows: {_safe_int(summary_330l.get('review_required_sheet_row_count'), 0)}",
            f"- Unit review sample rows: {_safe_int(summary_330l.get('unit_review_sheet_row_count'), 0)}",
            "",
            "## What Is Safe To Claim",
            "The demo can truthfully claim parser-output normalization, provenance-preserving sidecar trust scoring, curated semantic patch history, and conservative preview packaging.",
            f"If available, official rule milestones include scope rules {_safe_int(scope_summary.get('scope_rule_count_324'), 0)} and alias rules {_safe_int(alias_summary.get('official_alias_rule_count_325'), 0)}.",
            "",
            "## What Is Not Safe To Claim",
            "Do not claim production routing changes, client-ready deployment, or zero-manual-review operation.",
            "Do not claim that the preview workbook is a production export.",
            "",
            "## Next Steps",
            "Immediate next step remains 330K2 human unit review to reduce residual unit-risk rows.",
            "After that, demo packaging can extend into a clearer presentation flow without changing production behavior.",
            "",
        ]
    )


def _build_resume_bullets(
    summary_330l: Mapping[str, Any],
    loaded_refs: Mapping[str, Mapping[str, Any]],
) -> str:
    alias_summary = loaded_refs.get("alias_closure_325p", {})
    scope_summary = loaded_refs.get("scope_closure_324n", {})
    return "\n".join(
        [
            "# DateFac Resume Bullets 331A",
            "",
            "## 中文",
            f"- 负责 DateFac 券商研报 PDF 结构化 demo 的 sidecar 信任路由与演示包装，基于 13 份 unfamiliar PDF 的缓存产物生成 117 条候选指标行，并输出保守措辞的客户端风格 Excel 预览。",
            f"- 参与语义规则整理与回归闭环，累计沉淀 scope 规则 {_safe_int(scope_summary.get('scope_rule_count_324'), 0)} 条、alias 规则 {_safe_int(alias_summary.get('official_alias_rule_count_325'), 0)} 条；若按阶段汇总可引用累计 trusted gain {_safe_int(alias_summary.get('cumulative_trusted_gain_after_325'), 0)}、review reduction {_safe_int(alias_summary.get('cumulative_review_reduction_after_325'), 0)}。",
            "- 设计并实现 provenance 保留、风险标记、人工复核分流和 demo 文档生成流程，明确区分演示可展示状态与正式生产、正式客户交付状态的边界。",
            "",
            "## English",
            f"- Built sidecar trust-routing and demo-packaging workflows for a financial PDF extraction demo, packaging 117 prepared candidate rows from 13 unfamiliar PDFs into a conservative client-style Excel preview.",
            f"- Contributed to semantic-rule curation and closure reporting across scope and alias patch cycles, with milestone summaries tracking { _safe_int(alias_summary.get('cumulative_trusted_gain_after_325'), 0) } trusted-gain and { _safe_int(alias_summary.get('cumulative_review_reduction_after_325'), 0) } review-reduction impacts when available.",
            "- Implemented provenance-preserving risk routing, manual-review surfacing, and demo documentation generation while keeping claims explicitly below formal production and formal client-delivery thresholds.",
            "",
        ]
    )


def _build_github_readme_section(
    summary_330l: Mapping[str, Any],
    loaded_refs: Mapping[str, Mapping[str, Any]],
) -> str:
    milestone_330a = loaded_refs.get("trust_engine_330a", {})
    milestone_330b = loaded_refs.get("trust_engine_330b", {})
    milestone_330c = loaded_refs.get("trust_engine_330c", {})
    return "\n".join(
        [
            "# DateFac README Section 331A",
            "",
            "## Current Status",
            "DateFac is currently demo-ready with manual review caveats.",
            "The repository demonstrates sidecar trust scoring and preview packaging, but it is not production-ready or client-ready yet.",
            "",
            "## Architecture",
            "- Parser-output normalization and candidate shaping",
            "- Semantic rule curation and closure reporting",
            "- Sidecar trust scoring and risk routing",
            "- Provenance preservation and client-style preview packaging",
            "",
            "## What The Demo Shows",
            f"- 330A foundation: risk registry {_safe_int(milestone_330a.get('risk_registry_count'), 0)} and routing-policy smoke tests",
            f"- 330B scoring: scoring model component count {_safe_int(milestone_330b.get('scoring_model_component_count'), 0)}",
            f"- 330C cached benchmark: {_safe_int(milestone_330c.get('cached_candidate_count'), 0)} cached candidates when available",
            f"- 330L preview: {_safe_int(summary_330l.get('trusted_sheet_row_count'), 0)} trusted preview rows and {_safe_int(summary_330l.get('review_required_sheet_row_count'), 0)} review-required rows",
            "",
            "## How To Run Key Sidecar Reports",
            "```powershell",
            "python tools\\run_delivery_report_refresh_after_330k_330j2.py --unit-signal-review-dir D:\\_datefac\\output\\unit_signal_review_330k --fixed-prepared-dir D:\\_datefac\\output\\unfamiliar_trust_split_330k --previous-delivery-report-dir D:\\_datefac\\output\\delivery_report_refresh_330j --deduped-candidate-benchmark-dir D:\\_datefac\\output\\deduped_candidate_trust_benchmark_330e --trust-scoring-dir D:\\_datefac\\output\\trust_engine_scoring_330b --rerun-330f --output-dir D:\\_datefac\\output\\delivery_report_refresh_after_330k_330j2",
            "python tools\\run_client_style_export_preview_330l.py --delivery-report-refresh-dir D:\\_datefac\\output\\delivery_report_refresh_after_330k_330j2 --fixed-prepared-dir D:\\_datefac\\output\\unfamiliar_trust_split_330k --unit-signal-review-dir D:\\_datefac\\output\\unit_signal_review_330k --output-dir D:\\_datefac\\output\\client_style_export_preview_330l",
            "```",
            "",
            "## Known Limitations",
            "- Sidecar-only trust scoring; no production routing changes",
            "- Residual unit review remains",
            "- Cached unfamiliar PDF evidence only; no fresh PDF reopen in this demo path",
            "",
        ]
    )


def _build_demo_script(summary_330l: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# DateFac Demo Script 331A",
            "",
            "## 1. Open Problem Statement",
            "Financial PDFs contain useful metrics, but the challenge is not only extraction. The harder problem is whether a downstream user can trust what was extracted and know what still needs review.",
            "",
            "## 2. Show Pipeline Concept",
            "Walk through the demo as parser-output normalization -> candidate shaping -> semantic curation -> sidecar trust scoring -> provenance-preserving preview packaging.",
            "",
            "## 3. Show 330L Excel Preview",
            f"Open the 330L workbook at `{summary_330l.get('preview_workbook_path', '')}` and show the README, executive summary, trusted suggestions, review-required rows, and unit review sample.",
            "",
            "## 4. Explain Trusted vs Review-Required",
            f"Point out that the current demo preview contains {_safe_int(summary_330l.get('trusted_sheet_row_count'), 0)} trusted preview rows and {_safe_int(summary_330l.get('review_required_sheet_row_count'), 0)} review-required rows, based on sidecar trust scoring rather than production routing.",
            "",
            "## 5. Explain Unit Caveats",
            f"Call out that {_safe_int(summary_330l.get('unit_review_sheet_row_count'), 0)} unit-risk rows remain in the human review sample and the project status is demo-ready with manual review caveats.",
            "",
            "## 6. Explain Next Steps",
            "Close by saying the immediate next step is 330K2 human unit review, followed by cleaner presentation packaging once residual unit-risk rows are reduced.",
            "",
        ]
    )


def _write_docs(docs_dir: Path, docs_payload: Mapping[str, str]) -> Dict[str, str]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, str] = {}
    for key, filename in DOC_FILENAMES.items():
        path = docs_dir / filename
        path.write_text(docs_payload[key], encoding="utf-8")
        written[key] = str(path)
    return written


def build_demo_packaging_331a(
    *,
    client_style_export_preview_dir: Path,
    delivery_report_refresh_dir: Path,
    unit_signal_review_dir: Path,
    output_dir: Path,
    docs_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_330l_path = (
        client_style_export_preview_dir / "client_style_export_preview_330l_summary.json"
    )
    preview_workbook_path = (
        client_style_export_preview_dir / "client_style_export_preview_330l_preview.xlsx"
    )
    summary_330l = _read_json(summary_330l_path)
    loaded_refs = _load_optional_summaries()

    qa_rows = validate_330l_summary(summary_330l)

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append(
            {
                "check_name": name,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest()
        if alias_asset_path.exists()
        else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest()
        if scope_asset_path.exists()
        else "__MISSING__",
    }

    add_qa("artifacts::preview_workbook_exists", preview_workbook_path.exists(), str(preview_workbook_path))
    add_qa(
        "artifacts::delivery_refresh_summary_exists",
        delivery_report_refresh_dir.joinpath("delivery_report_refresh_after_330k_330j2_summary.json").exists(),
        str(delivery_report_refresh_dir / "delivery_report_refresh_after_330k_330j2_summary.json"),
    )
    add_qa(
        "artifacts::unit_signal_review_summary_exists",
        unit_signal_review_dir.joinpath("unit_signal_review_330k_summary.json").exists(),
        str(unit_signal_review_dir / "unit_signal_review_330k_summary.json"),
    )

    project_brief = _build_project_brief(summary_330l, loaded_refs)
    resume_bullets = _build_resume_bullets(summary_330l, loaded_refs)
    github_readme_section = _build_github_readme_section(summary_330l, loaded_refs)
    demo_script = _build_demo_script(summary_330l)
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
    client_forbidden = [
        "client-ready",
        "client ready",
        "paid-client ready",
    ]
    add_qa(
        "claims::no_production_claims",
        not any(_contains_forbidden_claim(text, production_forbidden) for text in docs_payload.values()),
        "docs checked for forbidden ready-state claims",
    )
    add_qa(
        "claims::no_client_ready_claims",
        not any(_contains_forbidden_claim(text, client_forbidden) for text in docs_payload.values()),
        "docs checked for forbidden client-ready claims",
    )
    add_qa(
        "claims::resume_bullets_not_overclaiming",
        "production-ready" not in resume_bullets.casefold()
        and "client-ready" not in resume_bullets.casefold(),
        "resume bullets checked",
    )
    add_qa(
        "artifacts::generated_docs_exist",
        all(Path(path).exists() for path in docs_paths.values()),
        json.dumps(docs_paths, ensure_ascii=False),
    )

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest()
        if alias_asset_path.exists()
        else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest()
        if scope_asset_path.exists()
        else "__MISSING__",
    }
    no_official_asset_modification_during_331a = official_assets_before == official_assets_after
    add_qa(
        "safety::official_assets_unchanged",
        no_official_asset_modification_during_331a,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    milestone_summary = {
        "scope_rule_count_324": _safe_int(loaded_refs.get("scope_closure_324n", {}).get("scope_rule_count_324"), 0),
        "alias_rule_count_325": _safe_int(loaded_refs.get("alias_closure_325p", {}).get("official_alias_rule_count_325"), 0),
        "cumulative_official_rule_count_after_325": _safe_int(
            loaded_refs.get("alias_closure_325p", {}).get("cumulative_official_rule_count_after_325"),
            0,
        ),
        "cumulative_trusted_gain_after_325": _safe_int(
            loaded_refs.get("alias_closure_325p", {}).get("cumulative_trusted_gain_after_325"),
            0,
        ),
        "cumulative_review_reduction_after_325": _safe_int(
            loaded_refs.get("alias_closure_325p", {}).get("cumulative_review_reduction_after_325"),
            0,
        ),
        "330L_prepared_candidate_row_count": _safe_int(summary_330l.get("prepared_candidate_row_count"), 0),
        "330L_trusted_sheet_row_count": _safe_int(summary_330l.get("trusted_sheet_row_count"), 0),
        "330L_review_required_sheet_row_count": _safe_int(summary_330l.get("review_required_sheet_row_count"), 0),
        "330L_unit_review_sheet_row_count": _safe_int(summary_330l.get("unit_review_sheet_row_count"), 0),
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
        "stage": "331A",
        "output_dir": str(output_dir),
        "docs_dir": str(docs_dir),
        "preview_workbook_path": str(preview_workbook_path),
        "generated_docs": docs_paths,
        "loaded_reference_summaries": sorted(loaded_refs.keys()),
        "milestone_summary": milestone_summary,
    }

    summary = {
        "stage": "331A",
        "output_dir": str(output_dir),
        "validated_330l_export_preview": all(
            row.get("status") == "PASS" for row in validate_330l_summary(summary_330l)
        ),
        "project_status": "DEMO_READY_WITH_UNIT_REVIEW_CAVEATS",
        "client_ready": False,
        "production_ready": False,
        "preview_workbook_path": str(preview_workbook_path),
        "prepared_candidate_row_count": _safe_int(summary_330l.get("prepared_candidate_row_count"), 0),
        "trusted_sheet_row_count": _safe_int(summary_330l.get("trusted_sheet_row_count"), 0),
        "review_required_sheet_row_count": _safe_int(summary_330l.get("review_required_sheet_row_count"), 0),
        "unit_review_sheet_row_count": _safe_int(summary_330l.get("unit_review_sheet_row_count"), 0),
        "project_brief_generated": True,
        "resume_bullets_generated": True,
        "github_readme_section_generated": True,
        "demo_script_generated": True,
        "generated_demo_artifacts": docs_paths,
        **milestone_summary,
        "no_official_asset_modification_during_331a": no_official_asset_modification_during_331a,
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
        stage="331A",
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
                    "modified_during_331a": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    milestone_df = _frame_for_output(
        pd.DataFrame([{"metric": key, "value": value} for key, value in milestone_summary.items()])
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
            pd.DataFrame([{"qa_pass_count": qa_pass_count, "qa_fail_count": qa_fail_count, "decision": summary["decision"]}])
        ),
        "qa_checks_df": qa_df,
        "milestone_df": milestone_df,
        "docs_manifest_df": docs_manifest_df,
        "official_asset_proof_df": official_asset_proof_df,
    }
