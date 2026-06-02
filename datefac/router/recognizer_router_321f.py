from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd


MINERU_TABLE_BODY_321D = "MINERU_TABLE_BODY_321D"
STRUCTTABLE_INTERVL2 = "STRUCTTABLE_INTERVL2"
DOCLING_TABLE_GRID_321E2 = "DOCLING_TABLE_GRID_321E2"
PPSTRUCTURE_320G = "PPSTRUCTURE_320G"
PURE_VLM_ADJUDICATOR = "PURE_VLM_SEMANTIC_ADJUDICATOR"
MANUAL_REVIEW = "MANUAL_REVIEW"

CORE_ROLE_SET = {
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW_STATEMENT",
    "CORE_METRIC_TABLE",
    "FINANCIAL_FORECAST_VALUATION",
}
NON_CORE_ROLE_SET = {
    "RATING_STANDARD",
    "DISCLAIMER_OR_LEGAL",
    "CHART_OR_MARKET_TREND",
}
SHEET_ORDER = [
    "summary",
    "router_policy",
    "route_preview",
    "route_counts",
    "adjudicator_worklist",
    "manual_review_worklist",
    "qa_checks",
    "known_limitations",
]


@dataclass
class RecognizerRouter321FConfig:
    bakeoff_dir: Path
    router_revision_dir: Path
    output_dir: Path


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _norm(value).lower() in {"1", "true", "yes", "y"}


def _to_int(value: Any) -> int:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0
        return int(float(value))
    except Exception:
        return 0


def _to_float(value: Any) -> float:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    base = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    out = base
    i = 1
    while out in used:
        suffix = f"_{i}"
        out = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(out)
    return out


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def _load_route_rankings(bakeoff_dir: Path) -> pd.DataFrame:
    workbook = bakeoff_dir / "table_extraction_full_bakeoff_321e5.xlsx"
    return _read_sheet(workbook, "route_rankings").fillna("")


def _load_route_preview(router_revision_dir: Path) -> pd.DataFrame:
    workbook = router_revision_dir / "source_aware_router_revision_321c2.xlsx"
    return _read_sheet(workbook, "table_route_preview_revised").fillna("")


def _route_score_lookup(rankings_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    return {str(row["route_name"]): row.to_dict() for _, row in rankings_df.iterrows()}


def _is_core_table(row: Dict[str, Any]) -> bool:
    role = _norm(row.get("effective_role_category") or row.get("table_role_guess"))
    return role in CORE_ROLE_SET


def _is_non_core_table(row: Dict[str, Any]) -> bool:
    role = _norm(row.get("effective_role_category") or row.get("table_role_guess"))
    return role in NON_CORE_ROLE_SET


def _needs_semantic_adjudicator(row: Dict[str, Any]) -> bool:
    pure_trusted = _to_int(row.get("pure_trusted_count"))
    pure_review = _to_int(row.get("pure_review_required_count"))
    if pure_trusted <= 0 and pure_review <= 0:
        return False
    reasons = _norm(row.get("route_reason")) + "|" + _norm(row.get("previous_route_reason"))
    if "conflict" in reasons.lower():
        return True
    if pure_review >= pure_trusted:
        return True
    return _is_core_table(row) and pure_trusted > 0 and _to_bool(row.get("image_exists"))


def _decide_route(row: Dict[str, Any], route_scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    role = _norm(row.get("effective_role_category") or row.get("table_role_guess"))
    mineru_clean = _to_bool(row.get("mineru_table_body_clean"))
    image_exists = _to_bool(row.get("image_exists"))
    pp_available = _to_bool(row.get("ppstructure_output_available"))
    pure_trusted = _to_int(row.get("pure_trusted_count"))
    pure_review = _to_int(row.get("pure_review_required_count"))
    value_score = _to_int(row.get("estimated_value_score"))
    previous_route = _norm(row.get("recommended_route"))

    risk_tags: List[str] = []
    reason_parts: List[str] = []

    if _is_non_core_table(row):
        risk_tags.append("NON_CORE_TABLE")
        return {
            "recommended_recognizer": "",
            "fallback_recognizer": "",
            "semantic_adjudicator_required": False,
            "manual_review_required": False,
            "risk_tags": "|".join(risk_tags),
            "reason": "non-core table outside recognizer budget",
        }

    if not image_exists and not mineru_clean:
        risk_tags.extend(["MISSING_IMAGE", "NO_CLEAN_TABLE_BODY"])
        return {
            "recommended_recognizer": "",
            "fallback_recognizer": "",
            "semantic_adjudicator_required": False,
            "manual_review_required": True,
            "risk_tags": "|".join(risk_tags),
            "reason": "no image and no clean MinerU table_body available",
        }

    semantic_adjudicator_required = False
    manual_review_required = False
    recommended = ""
    fallback = ""

    if mineru_clean:
        recommended = MINERU_TABLE_BODY_321D
        fallback = DOCLING_TABLE_GRID_321E2 if _is_core_table(row) else STRUCTTABLE_INTERVL2
        reason_parts.append("pdf_table_body_default_uses_mineru")
        reason_parts.append("clean_mineru_table_body_available")
    else:
        recommended = STRUCTTABLE_INTERVL2
        fallback = DOCLING_TABLE_GRID_321E2
        reason_parts.append("image_table_default_uses_structtable")
        reason_parts.append("no_clean_mineru_table_body")

    if not _is_core_table(row) and recommended == STRUCTTABLE_INTERVL2:
        fallback = DOCLING_TABLE_GRID_321E2
        reason_parts.append("non-core-image-route-keeps-docling-backup")

    if pp_available:
        risk_tags.append("PPSTRUCTURE_AVAILABLE")
    else:
        risk_tags.append("PPSTRUCTURE_NOT_AVAILABLE")

    if _needs_semantic_adjudicator(row):
        semantic_adjudicator_required = True
        risk_tags.append("PURE_VLM_ADJUDICATOR_CANDIDATE")
        reason_parts.append("pure_vlm_reserved_for_semantic_adjudication")

    if pure_trusted > 0:
        risk_tags.append("PURE_VLM_SIGNAL_PRESENT")
        reason_parts.append("pure_vlm_core_mapping_signal_acknowledged")
    if pure_review > pure_trusted:
        risk_tags.append("PURE_VLM_REVIEW_HEAVY")

    if value_score >= 90 and not mineru_clean and not image_exists:
        manual_review_required = True
        risk_tags.append("HIGH_VALUE_BUT_NO_EXECUTABLE_ROUTE")
        reason_parts.append("high-value-table-without-reliable-recognizer-input")

    if previous_route == "UNSUPPORTED_TABLE_TYPE":
        manual_review_required = True
        risk_tags.append("UNSUPPORTED_LAYOUT")
        reason_parts.append("previous-router-marked-unsupported")

    if previous_route == "MANUAL_REVIEW_REQUIRED":
        manual_review_required = True
        risk_tags.append("PREVIOUS_MANUAL_REVIEW_REQUIRED")
        reason_parts.append("previous-router-already-needed-manual-review")

    if _to_bool(row.get("mineru_assisted_source_risk")):
        risk_tags.append("SOURCE_CONTAMINATION_RISK")
        manual_review_required = True
        reason_parts.append("source-risk-kept-out-of-automatic-recognition")

    if recommended == STRUCTTABLE_INTERVL2:
        struct_score = route_scores.get(STRUCTTABLE_INTERVL2, {})
        pure_score = route_scores.get("PURE_VLM_321B2_CALIBRATED", {})
        if _to_float(pure_score.get("core_candidate_mapping_score")) > _to_float(struct_score.get("core_candidate_mapping_score")):
            risk_tags.append("PURE_VLM_STRONGER_MAPPING_BUT_NOT_DEFAULT")
            reason_parts.append("cost-stability-reproducibility-favor-structtable-default")

    if recommended == MINERU_TABLE_BODY_321D and not _is_core_table(row):
        risk_tags.append("MINERU_COST_EFFICIENT")

    if recommended == STRUCTTABLE_INTERVL2:
        risk_tags.append("STRUCTTABLE_DEFAULT_IMAGE_ROUTE")
    if fallback == DOCLING_TABLE_GRID_321E2:
        risk_tags.append("DOCLING_BACKUP_CANDIDATE")
    if pp_available and recommended not in {PPSTRUCTURE_320G, ""}:
        risk_tags.append("PPSTRUCTURE_WEAK_LEGACY_FALLBACK")

    return {
        "recommended_recognizer": recommended,
        "fallback_recognizer": fallback if fallback else (PPSTRUCTURE_320G if pp_available else ""),
        "semantic_adjudicator_required": semantic_adjudicator_required,
        "manual_review_required": manual_review_required,
        "risk_tags": "|".join(dict.fromkeys(tag for tag in risk_tags if _norm(tag))),
        "reason": "|".join(dict.fromkeys(part for part in reason_parts if _norm(part))),
    }


def _policy_rows() -> List[Dict[str, Any]]:
    return [
        {
            "policy_key": "pdf_table_body_default",
            "recommended_recognizer": MINERU_TABLE_BODY_321D,
            "fallback_recognizer": DOCLING_TABLE_GRID_321E2,
            "semantic_adjudicator": PURE_VLM_ADJUDICATOR,
            "notes": "default route for PDF table_body when clean MinerU HTML table is already available",
        },
        {
            "policy_key": "image_table_default",
            "recommended_recognizer": STRUCTTABLE_INTERVL2,
            "fallback_recognizer": DOCLING_TABLE_GRID_321E2,
            "semantic_adjudicator": PURE_VLM_ADJUDICATOR,
            "notes": "default route for image tables; pure VLM is intentionally not the batch default extractor",
        },
        {
            "policy_key": "docling_backup",
            "recommended_recognizer": DOCLING_TABLE_GRID_321E2,
            "fallback_recognizer": PPSTRUCTURE_320G,
            "semantic_adjudicator": "",
            "notes": "backup candidate when StructTable cannot be used or MinerU table_body is unavailable",
        },
        {
            "policy_key": "ppstructure_legacy_fallback",
            "recommended_recognizer": PPSTRUCTURE_320G,
            "fallback_recognizer": "",
            "semantic_adjudicator": "",
            "notes": "weak legacy fallback only",
        },
    ]


def _known_limitations() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "limitation": "read_only_policy",
                "detail": "321F builds executable routing policy from 321E5 and 321C2 artifacts only; no recognizer reruns occur.",
            },
            {
                "limitation": "semantic_adjudicator_not_extractor",
                "detail": "pure VLM is modeled only as semantic adjudicator demand, not as batch default recognizer.",
            },
            {
                "limitation": "production_not_touched",
                "detail": "router remains sandbox-only and does not alter delivery pipeline, overrides, or Stage7 logic.",
            },
        ]
    )


def _build_qa_checks(config: RecognizerRouter321FConfig, route_preview_df: pd.DataFrame, summary: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("bakeoff_dir_exists", config.bakeoff_dir.exists(), str(config.bakeoff_dir))
    add("router_revision_dir_exists", config.router_revision_dir.exists(), str(config.router_revision_dir))
    add("route_preview_loaded", not route_preview_df.empty, f"route_preview_rows={len(route_preview_df)}")
    add(
        "structtable_default_not_pure_vlm_for_images",
        bool(
            route_preview_df.empty
            or not (
                (route_preview_df["image_exists"].fillna(False).astype(bool))
                & (~route_preview_df["mineru_table_body_clean"].fillna(False).astype(bool))
                & (route_preview_df["recommended_recognizer"].astype(str) != STRUCTTABLE_INTERVL2)
                & (route_preview_df["manual_review_required"].fillna(False).astype(bool) == False)
            ).any()
        ),
        "image tables without clean MinerU body should default to StructTable unless forced manual review",
    )
    add(
        "pure_vlm_not_batch_default",
        bool(route_preview_df.empty or not (route_preview_df["recommended_recognizer"].astype(str) == "PURE_VLM_321B2_CALIBRATED").any()),
        "PURE_VLM should only appear as adjudicator demand, not recommended_recognizer",
    )
    add(
        "summary_counts_reconcile",
        _to_int(summary.get("route_total_count")) == len(route_preview_df),
        f"route_total_count={summary.get('route_total_count')} preview_rows={len(route_preview_df)}",
    )
    return pd.DataFrame(rows)


def _build_report(path: Path, summary: Dict[str, Any], route_counts_df: pd.DataFrame, qa_df: pd.DataFrame) -> None:
    lines = [
        "# Recognizer Router 321F",
        "",
        "## Decision",
        f"- router_decision: {summary.get('router_decision', '')}",
        "",
        "## Snapshot",
        f"- route_total_count: {summary.get('route_total_count', 0)}",
        f"- mineru_default_count: {summary.get('mineru_default_count', 0)}",
        f"- structtable_default_count: {summary.get('structtable_default_count', 0)}",
        f"- pure_vlm_adjudicator_count: {summary.get('pure_vlm_adjudicator_count', 0)}",
        f"- docling_backup_count: {summary.get('docling_backup_count', 0)}",
        f"- ppstructure_fallback_count: {summary.get('ppstructure_fallback_count', 0)}",
        f"- manual_review_count: {summary.get('manual_review_count', 0)}",
        f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
        "",
        "## Route Counts",
    ]
    if route_counts_df.empty:
        lines.append("- none")
    else:
        for _, row in route_counts_df.iterrows():
            lines.append(
                f"- {row.get('route_bucket', '')}: {row.get('count', 0)}"
            )
    lines.extend(["", "## QA Checks"])
    if qa_df.empty:
        lines.append("- none")
    else:
        for _, row in qa_df.iterrows():
            lines.append(f"- {row.get('check_name', '')}: {row.get('status', '')} | {row.get('detail', '')}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_recognizer_router_321f(config: RecognizerRouter321FConfig) -> Dict[str, Any]:
    output_dir = config.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    bakeoff_summary = _read_json(config.bakeoff_dir / "table_extraction_full_bakeoff_321e5_summary.json")
    rankings_df = _load_route_rankings(config.bakeoff_dir)
    base_preview_df = _load_route_preview(config.router_revision_dir)
    route_scores = _route_score_lookup(rankings_df)

    if base_preview_df.empty:
        route_preview_df = pd.DataFrame()
    else:
        decisions_df = base_preview_df.apply(
            lambda row: _decide_route(row.to_dict(), route_scores),
            axis=1,
            result_type="expand",
        )
        route_preview_df = pd.concat([base_preview_df, decisions_df], axis=1)

    adjudicator_df = route_preview_df[route_preview_df["semantic_adjudicator_required"].fillna(False).astype(bool)].copy() if not route_preview_df.empty else pd.DataFrame()
    manual_review_df = route_preview_df[route_preview_df["manual_review_required"].fillna(False).astype(bool)].copy() if not route_preview_df.empty else pd.DataFrame()

    route_total_count = int(len(route_preview_df))
    mineru_default_count = int((route_preview_df["recommended_recognizer"] == MINERU_TABLE_BODY_321D).sum()) if not route_preview_df.empty else 0
    structtable_default_count = int((route_preview_df["recommended_recognizer"] == STRUCTTABLE_INTERVL2).sum()) if not route_preview_df.empty else 0
    pure_vlm_adjudicator_count = int(len(adjudicator_df))
    docling_backup_count = int((route_preview_df["fallback_recognizer"] == DOCLING_TABLE_GRID_321E2).sum()) if not route_preview_df.empty else 0
    ppstructure_fallback_count = int(
        (
            (route_preview_df["fallback_recognizer"] == PPSTRUCTURE_320G)
            | (route_preview_df["recommended_recognizer"] == PPSTRUCTURE_320G)
        ).sum()
    ) if not route_preview_df.empty else 0
    manual_review_count = int(len(manual_review_df))

    route_counts_df = pd.DataFrame(
        [
            {"route_bucket": "recommended_mineru_table_body_321d", "count": mineru_default_count},
            {"route_bucket": "recommended_structtable_intervl2", "count": structtable_default_count},
            {"route_bucket": "pure_vlm_semantic_adjudicator_required", "count": pure_vlm_adjudicator_count},
            {"route_bucket": "docling_backup_candidate", "count": docling_backup_count},
            {"route_bucket": "ppstructure_legacy_fallback", "count": ppstructure_fallback_count},
            {"route_bucket": "manual_review_required", "count": manual_review_count},
        ]
    )

    summary = {
        "stage": "321F",
        "output_dir": str(output_dir),
        "route_total_count": route_total_count,
        "mineru_default_count": mineru_default_count,
        "structtable_default_count": structtable_default_count,
        "pure_vlm_adjudicator_count": pure_vlm_adjudicator_count,
        "docling_backup_count": docling_backup_count,
        "ppstructure_fallback_count": ppstructure_fallback_count,
        "manual_review_count": manual_review_count,
        "router_decision": "RECOGNIZER_ROUTER_321F_READY_FOR_SANDBOX_INTEGRATION",
        "pdf_table_body_default_route": MINERU_TABLE_BODY_321D,
        "image_table_default_route": STRUCTTABLE_INTERVL2,
        "pure_vlm_positioning": "SEMANTIC_ADJUDICATOR_ONLY",
        "bakeoff_top_overall_route": _norm(bakeoff_summary.get("top_overall_route")),
        "bakeoff_pdf_default_route": _norm(bakeoff_summary.get("pdf_table_body_default_route")),
        "bakeoff_image_default_route": _norm(bakeoff_summary.get("image_table_default_route")),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    qa_df = _build_qa_checks(config, route_preview_df, summary)
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    summary["qa_pass_count"] = qa_pass_count
    summary["qa_fail_count"] = qa_fail_count
    if qa_fail_count > 0:
        summary["router_decision"] = "RECOGNIZER_ROUTER_321F_BLOCKED_BY_QA"

    router_policy_json = {
        "stage": "321F",
        "defaults": {
            "pdf_table_body": MINERU_TABLE_BODY_321D,
            "image_table": STRUCTTABLE_INTERVL2,
        },
        "fallbacks": {
            "image_table_backup": DOCLING_TABLE_GRID_321E2,
            "legacy_weak_fallback": PPSTRUCTURE_320G,
        },
        "semantic_adjudicator": {
            "recognizer": PURE_VLM_ADJUDICATOR,
            "positioning": "not batch default extractor",
        },
        "route_counts": route_counts_df.to_dict(orient="records"),
    }

    excel_path = output_dir / "recognizer_router_321f.xlsx"
    summary_json_path = output_dir / "recognizer_router_321f_summary.json"
    report_md_path = output_dir / "recognizer_router_321f_report.md"
    router_json_path = output_dir / "router_plan_321f.json"

    _write_excel(
        excel_path,
        {
            "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
            "router_policy": pd.DataFrame(_policy_rows()),
            "route_preview": route_preview_df,
            "route_counts": route_counts_df,
            "adjudicator_worklist": adjudicator_df,
            "manual_review_worklist": manual_review_df,
            "qa_checks": qa_df,
            "known_limitations": _known_limitations(),
        },
    )
    _write_json(summary_json_path, summary)
    _write_json(router_json_path, router_policy_json)
    _build_report(report_md_path, summary, route_counts_df, qa_df)

    return {
        "summary": summary,
        "excel_path": str(excel_path),
        "summary_json_path": str(summary_json_path),
        "report_md_path": str(report_md_path),
        "router_json_path": str(router_json_path),
    }
