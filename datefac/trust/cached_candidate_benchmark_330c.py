from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import pandas as pd

from datefac.trust.confidence_scoring import score_trust_record


READY_330B_DECISION = "TRUST_ENGINE_SCORING_330B_READY_FOR_330C_CACHED_CANDIDATE_TRUST_SCORING_BENCHMARK"
READY_DECISION = "TRUST_ENGINE_CACHED_CANDIDATE_BENCHMARK_330C_READY_FOR_330D_ROUTING_POLICY_CALIBRATION"
READY_WITH_WARNINGS_DECISION = "TRUST_ENGINE_CACHED_CANDIDATE_BENCHMARK_330C_READY_WITH_WARNINGS"
NOT_READY_DECISION = "TRUST_ENGINE_CACHED_CANDIDATE_BENCHMARK_330C_NOT_READY"

DEFAULT_TRUST_SCORING_DIR = Path(r"D:\_datefac\output\trust_engine_scoring_330b")
DEFAULT_CANDIDATE_SOURCE_DIRS = [
    Path(r"D:\_datefac\output\router_mineru_trust_split_322b2"),
    Path(r"D:\_datefac\output\alias_human_confirmed_sandbox_replay_325i"),
    Path(r"D:\_datefac\output\scope_noise_human_confirmed_sandbox_replay_324g"),
    Path(r"D:\_datefac\output\post_patch_regression_validation_325o"),
]
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\cached_candidate_trust_scoring_330c")

PREFERRED_ARTIFACTS = {
    "selected_candidate_reclassified_322b2.jsonl": {"kind": "jsonl"},
    "alias_human_confirmed_sandbox_replay_325i_affected_candidates.jsonl": {"kind": "jsonl"},
    "alias_human_confirmed_sandbox_replay_325i_affected_candidates.xlsx": {
        "kind": "xlsx",
        "sheet_names": ["affected_candidates"],
    },
    "scope_noise_human_confirmed_sandbox_replay_324g_affected_candidates.xlsx": {
        "kind": "xlsx",
        "sheet_names": ["candidate_before_after_diff"],
    },
    "router_mineru_trust_split_322b2.xlsx": {
        "kind": "xlsx",
        "sheet_names": ["selected_candidate_reclassified"],
    },
}

GENERIC_PATTERNS = [
    ("*_affected_candidates.jsonl", "jsonl", None),
    ("*_affected_candidates.xlsx", "xlsx", ["affected_candidates", "candidate_before_after_diff"]),
    ("*_before_after*.xlsx", "xlsx", ["affected_candidates", "candidate_before_after_diff", "selected_candidate_reclassified"]),
]

STATUS_MAP = {
    "TRUSTED": "TRUSTED",
    "TRUSTED_PREVIEW": "TRUSTED",
    "REVIEW_REQUIRED": "REVIEW_REQUIRED",
    "REVIEW_REQUIRED_PREVIEW": "REVIEW_REQUIRED",
    "REJECTED": "REJECTED",
    "REJECTED_PREVIEW": "REJECTED",
    "OUT_OF_SCOPE": "OUT_OF_SCOPE",
    "OUT_OF_SCOPE_PREVIEW": "OUT_OF_SCOPE",
    "NEEDS_MORE_INFO": "NEEDS_MORE_INFO",
}


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _norm_text(value).lower() in {"1", "true", "yes", "y", "pass", "passed"}


def _safe_json_loads(text: Any) -> Dict[str, Any]:
    raw = _norm_text(text)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _safe_float(value: Any) -> Any:
    if value in ("", None):
        return None
    try:
        return float(value)
    except Exception:
        return value


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _split_tokens(value: Any) -> List[str]:
    tokens: List[str] = []
    if value in ("", None):
        return tokens
    if isinstance(value, list):
        items = value
    else:
        text = _norm_text(value)
        if not text:
            return tokens
        for delimiter in ["|", ";", ",", "/", "\\", "\n", "\t"]:
            text = text.replace(delimiter, "||")
        items = text.split("||")
    seen = set()
    for item in items:
        token = _norm_text(item)
        if token and token not in seen:
            tokens.append(token)
            seen.add(token)
    return tokens


def normalize_existing_status(value: Any) -> str:
    text = _norm_text(value).upper()
    return STATUS_MAP.get(text, "")


def map_raw_risk_tokens(values: Iterable[Any]) -> List[str]:
    mapped: List[str] = []
    seen = set()
    for raw in values or []:
        token = _norm_text(raw)
        if not token:
            continue
        upper = token.upper()
        candidate = ""
        if upper in {
            "UNIT_UNKNOWN",
            "UNIT_CONFLICT",
            "YEAR_MISSING",
            "YEAR_MISMATCH",
            "VALUE_PARSE_FAILED",
            "PARSER_CONFLICT",
            "LOW_EVIDENCE_STRENGTH",
            "LABEL_AMBIGUOUS",
            "TARGET_METRIC_AMBIGUOUS",
            "SCOPE_NOISE_RISK",
            "ALIAS_MAPPING_RISK",
            "ADJUSTED_METRIC_RISK",
            "DILUTED_EPS_RISK",
            "LONG_NARRATIVE_LABEL",
            "TABLE_STRUCTURE_UNSTABLE",
            "OFFICIAL_RULE_CONFLICT",
            "HISTORICAL_DUPLICATE_WARNING",
            "MOJIBAKE_ENCODING_ARTIFACT",
        }:
            candidate = upper
        elif "UNKNOWN_METRIC" in upper:
            candidate = "TARGET_METRIC_AMBIGUOUS"
        elif "MAPPING" in upper:
            candidate = "ALIAS_MAPPING_RISK"
        elif "INVALID_OR_MISSING_YEAR" in upper or ("YEAR" in upper and "MISSING" in upper):
            candidate = "YEAR_MISSING"
        elif "YEAR" in upper and "MISMATCH" in upper:
            candidate = "YEAR_MISMATCH"
        elif "VALUE_PARSE" in upper or "SCHEMA_UNCERTAIN" in upper:
            candidate = "VALUE_PARSE_FAILED"
        elif "UNIT" in upper and "CONFLICT" in upper:
            candidate = "UNIT_CONFLICT"
        elif "UNIT" in upper and ("UNKNOWN" in upper or "MISSING" in upper):
            candidate = "UNIT_UNKNOWN"
        elif "DILUTED" in upper and "EPS" in upper:
            candidate = "DILUTED_EPS_RISK"
        elif "ADJUSTED" in upper:
            candidate = "ADJUSTED_METRIC_RISK"
        elif "DUPLICATE" in upper:
            candidate = "HISTORICAL_DUPLICATE_WARNING"
        elif "MOJIBAKE" in upper or "ENCODING" in upper or "涔辩爜" in token:
            candidate = "MOJIBAKE_ENCODING_ARTIFACT"
        elif "DISCLOSURE" in upper or "SCOPE" in upper:
            candidate = "SCOPE_NOISE_RISK"
        elif "LABEL" in upper:
            candidate = "LABEL_AMBIGUOUS"
        elif len(token) >= 80:
            candidate = "LONG_NARRATIVE_LABEL"
        if candidate and candidate not in seen:
            mapped.append(candidate)
            seen.add(candidate)
    return mapped


def score_bucket_label(score: Any) -> str:
    try:
        numeric = float(score)
    except Exception:
        numeric = 0.0
    if numeric <= 0:
        return "0"
    if numeric < 25:
        return "1-24"
    if numeric < 60:
        return "25-59"
    if numeric < 85:
        return "60-84"
    return "85-100"


def _stable_candidate_id(row: Mapping[str, Any], artifact_name: str, sheet_name: str, row_index: int) -> str:
    for key in ["candidate_id", "row_id", "source_candidate_id"]:
        value = _norm_text(row.get(key))
        if value:
            return value
    digest = hashlib.sha1(
        json.dumps(
            {
                "artifact_name": artifact_name,
                "sheet_name": sheet_name,
                "row_index": row_index,
                "row": dict(row),
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    return f"330c::{digest[:16]}"


def _collect_evidence_refs(row: Mapping[str, Any], provenance: Mapping[str, Any]) -> List[str]:
    refs: List[str] = []
    for key in [
        "source_page",
        "page",
        "page_ref",
        "source_table",
        "table_id",
        "table_asset_id",
        "source_row_text",
        "row_text",
        "row_label",
        "source_report_name",
        "source_doc_name",
        "table_title",
    ]:
        value = _norm_text(row.get(key) or provenance.get(key))
        if value:
            refs.append(value)
    explicit = row.get("evidence_refs")
    for item in _as_list(explicit):
        value = _norm_text(item)
        if value:
            refs.append(value)
    ordered: List[str] = []
    seen = set()
    for item in refs:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def convert_candidate_row_to_trust_input(
    row: Mapping[str, Any],
    *,
    artifact_path: Path,
    source_dir: Path,
    sheet_name: str,
    row_index: int,
) -> Dict[str, Any]:
    provenance_payload = _safe_json_loads(row.get("provenance_json")) or _safe_json_loads(row.get("provenance"))
    candidate_id = _stable_candidate_id(row, artifact_path.name, sheet_name, row_index)
    metric_label_raw = (
        _norm_text(row.get("metric_label_raw"))
        or _norm_text(row.get("raw_metric_name"))
        or _norm_text(row.get("label"))
        or _norm_text(row.get("alias_label"))
        or _norm_text(row.get("row_label"))
        or _norm_text(row.get("source_row_text"))
        or _norm_text(row.get("row_text"))
    )
    normalized_metric = (
        _norm_text(row.get("normalized_metric"))
        or _norm_text(row.get("target_metric"))
        or _norm_text(row.get("metric_code_after"))
        or _norm_text(row.get("metric_code"))
        or _norm_text(row.get("metric_code_before"))
    )
    parser_sources = []
    for key in ["parser_sources", "source_parser", "parser_source", "selected_output_source", "source_stage"]:
        for item in _as_list(row.get(key)):
            value = _norm_text(item)
            if value and value not in parser_sources:
                parser_sources.append(value)
    raw_risk_tokens: List[str] = []
    for key in ["risk_flags", "warnings", "validation_flags", "error_codes", "risk_tags_after", "risk_tags_before", "risk_tags"]:
        raw_risk_tokens.extend(_split_tokens(row.get(key)))
    risk_flags = map_raw_risk_tokens(raw_risk_tokens)
    existing_status = (
        normalize_existing_status(row.get("existing_status"))
        or normalize_existing_status(row.get("decision_after"))
        or normalize_existing_status(row.get("split_decision"))
        or normalize_existing_status(row.get("decision_before"))
    )
    semantic_target_unambiguous = bool(normalized_metric) and normalized_metric.lower() not in {"unknown_metric", "unknown"}
    unit = (
        _norm_text(row.get("unit"))
        or _norm_text(row.get("unit_after"))
        or _norm_text(row.get("normalized_unit"))
        or _norm_text(row.get("unit_raw"))
        or _norm_text(row.get("unit_before"))
        or _norm_text(provenance_payload.get("table_unit"))
    )
    year = _norm_text(row.get("year")) or _norm_text(row.get("fiscal_year")) or _norm_text(row.get("column_year"))
    value = row.get("normalized_value")
    if value in ("", None):
        value = row.get("value")
    if value in ("", None):
        value = row.get("numeric_value")
    if value in ("", None):
        value = row.get("extracted_value")
    if value in ("", None):
        value = row.get("raw_value")
    evidence_refs = _collect_evidence_refs(row, provenance_payload)
    proposal_id = _norm_text(row.get("proposal_id"))
    patch_reason = _norm_text(row.get("patch_reason"))
    return {
        "candidate_id": candidate_id,
        "metric_label_raw": metric_label_raw,
        "normalized_metric": normalized_metric,
        "value": _safe_float(value),
        "unit": unit,
        "year": year,
        "parser_sources": parser_sources,
        "evidence_refs": evidence_refs,
        "risk_flags": risk_flags,
        "existing_status": existing_status,
        "existing_status_raw": _norm_text(row.get("decision_after") or row.get("split_decision") or row.get("decision_before")),
        "official_alias_match_signal": proposal_id.startswith("325i::sandbox_alias_rule") or "ACCEPT_ALIAS" in patch_reason,
        "semantic_target_unambiguous": semantic_target_unambiguous,
        "value_parse_success": row.get("normalized_value") not in ("", None) or _safe_bool(row.get("value_parse_success")),
        "source_page": _norm_text(row.get("source_page") or provenance_payload.get("source_page")),
        "source_table": _norm_text(row.get("source_table_id") or row.get("table_asset_id") or provenance_payload.get("table_asset_id")),
        "source_row": _norm_text(row.get("source_row_index") or row.get("row_index") or row.get("row_label")),
        "source_artifact": artifact_path.name,
        "source_sheet": sheet_name,
        "source_dir_name": source_dir.name,
        "provenance": {
            "source_artifact_path": str(artifact_path),
            "source_dir": str(source_dir),
            "source_sheet": sheet_name,
            "source_row_index": row_index,
            "artifact_type": artifact_path.suffix.lower(),
            "raw_existing_status": _norm_text(row.get("decision_after") or row.get("split_decision") or row.get("decision_before")),
            "raw_risk_tokens": raw_risk_tokens,
            "upstream_provenance": provenance_payload,
        },
    }


def _read_jsonl_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
            except Exception:
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
    return rows


def _read_xlsx_rows(path: Path, sheet_names: Sequence[str]) -> List[Tuple[str, Dict[str, Any]]]:
    rows: List[Tuple[str, Dict[str, Any]]] = []
    excel = pd.ExcelFile(path)
    for sheet_name in sheet_names:
        if sheet_name not in excel.sheet_names:
            continue
        frame = excel.parse(sheet_name)
        if frame.empty:
            continue
        frame = frame.where(pd.notna(frame), None)
        for row in frame.to_dict(orient="records"):
            if isinstance(row, dict):
                rows.append((sheet_name, row))
    return rows


def discover_candidate_artifacts(source_dirs: Sequence[Path]) -> List[Dict[str, Any]]:
    discovered: List[Dict[str, Any]] = []
    seen = set()
    for source_dir in source_dirs:
        if not source_dir.exists() or not source_dir.is_dir():
            continue
        for file_name, metadata in PREFERRED_ARTIFACTS.items():
            path = source_dir / file_name
            if path.exists() and str(path.resolve()) not in seen:
                discovered.append(
                    {
                        "path": path,
                        "kind": metadata["kind"],
                        "sheet_names": metadata.get("sheet_names") or [],
                        "source_dir": source_dir,
                        "discovery_reason": "preferred_filename",
                    }
                )
                seen.add(str(path.resolve()))
        for pattern, kind, sheet_names in GENERIC_PATTERNS:
            for path in source_dir.glob(pattern):
                if str(path.resolve()) in seen:
                    continue
                discovered.append(
                    {
                        "path": path,
                        "kind": kind,
                        "sheet_names": sheet_names or [],
                        "source_dir": source_dir,
                        "discovery_reason": f"pattern:{pattern}",
                    }
                )
                seen.add(str(path.resolve()))
    discovered.sort(key=lambda row: (str(row["source_dir"]), row["path"].name))
    return discovered


def load_cached_candidate_like_rows(source_dirs: Sequence[Path]) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
    artifacts = discover_candidate_artifacts(source_dirs)
    converted_rows: List[Dict[str, Any]] = []
    artifact_inventory_rows: List[Dict[str, Any]] = []
    for artifact in artifacts:
        path = artifact["path"]
        source_dir = artifact["source_dir"]
        kind = artifact["kind"]
        row_count_before = len(converted_rows)
        if kind == "jsonl":
            rows = [(path.stem, row) for row in _read_jsonl_rows(path)]
        else:
            rows = _read_xlsx_rows(path, artifact["sheet_names"])
        for row_index, (sheet_name, row) in enumerate(rows, start=1):
            converted_rows.append(
                convert_candidate_row_to_trust_input(
                    row,
                    artifact_path=path,
                    source_dir=source_dir,
                    sheet_name=sheet_name,
                    row_index=row_index,
                )
            )
        artifact_inventory_rows.append(
            {
                "source_dir_name": source_dir.name,
                "artifact_name": path.name,
                "artifact_kind": kind,
                "discovery_reason": artifact["discovery_reason"],
                "sheet_names": " | ".join(artifact["sheet_names"]) if artifact["sheet_names"] else "",
                "loaded_record_count": len(converted_rows) - row_count_before,
            }
        )
    inventory_df = pd.DataFrame(artifact_inventory_rows).fillna("")
    return converted_rows, inventory_df


def build_fallback_fixture_rows() -> List[Dict[str, Any]]:
    return [
        {
            "candidate_id": "330c_fixture_001",
            "metric_label_raw": "Revenue",
            "normalized_metric": "revenue",
            "value": 6742,
            "unit": "CNY_million",
            "year": "2024A",
            "parser_sources": ["pdfplumber"],
            "evidence_refs": ["fixture://page=1", "fixture://row=1"],
            "risk_flags": [],
            "existing_status": "TRUSTED",
            "semantic_target_unambiguous": True,
            "value_parse_success": True,
            "source_artifact": "fallback_fixture",
            "source_sheet": "fallback_fixture",
            "source_dir_name": "fallback_fixture",
            "provenance": {"fixture": True, "stage": "330C"},
        },
        {
            "candidate_id": "330c_fixture_002",
            "metric_label_raw": "Adjusted EPS",
            "normalized_metric": "adjusted_eps",
            "value": 1.25,
            "unit": "CNY",
            "year": "2025E",
            "parser_sources": ["pdfplumber"],
            "evidence_refs": ["fixture://page=2"],
            "risk_flags": ["ADJUSTED_METRIC_RISK", "LOW_EVIDENCE_STRENGTH"],
            "existing_status": "REVIEW_REQUIRED",
            "semantic_target_unambiguous": True,
            "value_parse_success": True,
            "source_artifact": "fallback_fixture",
            "source_sheet": "fallback_fixture",
            "source_dir_name": "fallback_fixture",
            "provenance": {"fixture": True, "stage": "330C"},
        },
        {
            "candidate_id": "330c_fixture_003",
            "metric_label_raw": "P/E?",
            "normalized_metric": "price_earnings_ratio",
            "value": None,
            "unit": "x",
            "year": "",
            "parser_sources": ["pdfplumber"],
            "evidence_refs": ["fixture://row=3"],
            "risk_flags": ["VALUE_PARSE_FAILED", "TARGET_METRIC_AMBIGUOUS"],
            "existing_status": "REJECTED",
            "semantic_target_unambiguous": False,
            "value_parse_success": False,
            "source_artifact": "fallback_fixture",
            "source_sheet": "fallback_fixture",
            "source_dir_name": "fallback_fixture",
            "provenance": {"fixture": True, "stage": "330C"},
        },
    ]


def _distribution_from_series(series: pd.Series) -> Dict[str, int]:
    if series.empty:
        return {}
    counts = series.fillna("").astype(str).value_counts()
    return {str(index): int(value) for index, value in counts.items() if str(index).strip()}


def build_cached_candidate_benchmark_330c(
    *,
    trust_scoring_summary: Dict[str, Any],
    trust_scoring_qa: Dict[str, Any],
    trust_scoring_no_apply: Dict[str, Any],
    candidate_source_dirs: Sequence[Path],
    output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add_qa(
        "readiness::330b_decision",
        _norm_text(trust_scoring_summary.get("decision")) == READY_330B_DECISION,
        _norm_text(trust_scoring_summary.get("decision")),
    )
    add_qa(
        "readiness::330b_qa_fail_count_summary",
        int(trust_scoring_summary.get("qa_fail_count", 1)) == 0,
        str(trust_scoring_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::330b_qa_fail_count_qa_json",
        int(trust_scoring_qa.get("qa_fail_count", 1)) == 0,
        str(trust_scoring_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "readiness::330b_routing_policy_smoke_test_passed",
        bool(trust_scoring_summary.get("routing_policy_smoke_test_passed")) is True,
        str(trust_scoring_summary.get("routing_policy_smoke_test_passed", "")),
    )
    add_qa(
        "readiness::330b_scored_example_count",
        int(trust_scoring_summary.get("scored_example_count", 0)) >= 5,
        str(trust_scoring_summary.get("scored_example_count", "")),
    )
    add_qa(
        "readiness::330b_no_apply_proof",
        bool(trust_scoring_no_apply.get("no_official_asset_modification_during_330b")) is True,
        str(trust_scoring_no_apply.get("no_official_asset_modification_during_330b", "")),
    )

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }

    cached_candidate_rows, artifact_inventory_df = load_cached_candidate_like_rows(candidate_source_dirs)
    fallback_fixture_count = 0
    candidate_source_status = "cached_candidates_loaded"
    if not cached_candidate_rows:
        cached_candidate_rows = build_fallback_fixture_rows()
        fallback_fixture_count = len(cached_candidate_rows)
        candidate_source_status = "fallback_fixtures_only"

    scored_records = [score_trust_record(row) for row in cached_candidate_rows]
    scored_df = pd.DataFrame(scored_records).fillna("")
    if not scored_df.empty:
        scored_df["score_bucket"] = scored_df["confidence_score"].apply(score_bucket_label)

    candidate_source_dir_record_counts = (
        scored_df["source_dir_name"].value_counts().to_dict() if "source_dir_name" in scored_df.columns else {}
    )
    source_artifact_distribution = (
        scored_df["source_artifact"].value_counts().to_dict() if "source_artifact" in scored_df.columns else {}
    )
    confidence_level_distribution = (
        _distribution_from_series(scored_df["confidence_level"]) if "confidence_level" in scored_df.columns else {}
    )
    routing_decision_distribution = (
        _distribution_from_series(scored_df["routing_decision"]) if "routing_decision" in scored_df.columns else {}
    )
    score_bucket_distribution = (
        _distribution_from_series(scored_df["score_bucket"]) if "score_bucket" in scored_df.columns else {}
    )
    risk_counter: Dict[str, int] = {}
    for row in scored_records:
        for risk_code in row.get("risk_flags", []) or []:
            risk_counter[risk_code] = risk_counter.get(risk_code, 0) + 1
    risk_flag_distribution = dict(sorted(risk_counter.items(), key=lambda item: (-item[1], item[0])))

    existing_status_distribution: Dict[str, int] = {}
    sidecar_vs_existing_rows: List[Dict[str, Any]] = []
    if "existing_status" in scored_df.columns:
        existing_status_distribution = _distribution_from_series(scored_df["existing_status"])
        if existing_status_distribution:
            pair_counts = (
                scored_df.groupby(["existing_status", "routing_decision"]).size().reset_index(name="count")
            )
            sidecar_vs_existing_rows = pair_counts.to_dict(orient="records")

    potential_false_trusted_mask = (
        (scored_df["routing_decision"] == "TRUSTED")
        & (scored_df["existing_status"].astype(str).str.strip() != "")
        & (scored_df["existing_status"] != "TRUSTED")
    ) if not scored_df.empty else pd.Series(dtype=bool)
    trusted_with_warning_mask = (
        (scored_df["routing_decision"] == "TRUSTED")
        & (scored_df["warning_risks"].astype(str).str.strip() != "[]")
    ) if not scored_df.empty else pd.Series(dtype=bool)
    trusted_with_low_evidence_mask = (
        (scored_df["routing_decision"] == "TRUSTED")
        & (
            scored_df["risk_flags"].astype(str).str.contains("LOW_EVIDENCE_STRENGTH", regex=False)
            | (pd.to_numeric(scored_df["evidence_score"], errors="coerce").fillna(0) < 20)
        )
    ) if not scored_df.empty else pd.Series(dtype=bool)
    review_required_high_score_mask = (
        (scored_df["routing_decision"] == "REVIEW_REQUIRED")
        & (pd.to_numeric(scored_df["confidence_score"], errors="coerce").fillna(0) >= 85)
    ) if not scored_df.empty else pd.Series(dtype=bool)
    rejected_or_needs_more_info_high_score_mask = (
        scored_df["routing_decision"].isin(["REJECTED", "NEEDS_MORE_INFO"])
        & (pd.to_numeric(scored_df["confidence_score"], errors="coerce").fillna(0) >= 85)
    ) if not scored_df.empty else pd.Series(dtype=bool)
    missing_evidence_mask = (
        (pd.to_numeric(scored_df["evidence_score"], errors="coerce").fillna(0) == 0)
        | (scored_df["evidence_refs"].astype(str).str.strip() == "[]")
    ) if not scored_df.empty else pd.Series(dtype=bool)

    calibration_sets = {
        "potential_false_trusted": scored_df.loc[potential_false_trusted_mask].copy() if not scored_df.empty else pd.DataFrame(),
        "trusted_with_warning_risk": scored_df.loc[trusted_with_warning_mask].copy() if not scored_df.empty else pd.DataFrame(),
        "trusted_with_low_evidence": scored_df.loc[trusted_with_low_evidence_mask].copy() if not scored_df.empty else pd.DataFrame(),
        "review_required_high_score": scored_df.loc[review_required_high_score_mask].copy() if not scored_df.empty else pd.DataFrame(),
        "rejected_or_needs_more_info_high_score": scored_df.loc[rejected_or_needs_more_info_high_score_mask].copy() if not scored_df.empty else pd.DataFrame(),
        "missing_evidence": scored_df.loc[missing_evidence_mask].copy() if not scored_df.empty else pd.DataFrame(),
    }
    calibration_samples = pd.concat(
        [frame for frame in calibration_sets.values() if not frame.empty],
        ignore_index=True,
    ) if any(not frame.empty for frame in calibration_sets.values()) else pd.DataFrame(columns=scored_df.columns if not scored_df.empty else [])
    calibration_sample_count = int(calibration_samples["candidate_id"].nunique()) if "candidate_id" in calibration_samples.columns else 0

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    no_official_asset_modification_during_330c = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330c",
        no_official_asset_modification_during_330c,
        json.dumps(
            {
                "before": official_assets_before,
                "after": official_assets_after,
            },
            ensure_ascii=False,
        ),
    )
    add_qa(
        "records::scored_record_count",
        len(scored_records) > 0,
        f"actual={len(scored_records)}",
    )

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    decision = READY_DECISION
    if candidate_source_status == "fallback_fixtures_only":
        decision = READY_WITH_WARNINGS_DECISION
    if qa_fail_count > 0:
        decision = NOT_READY_DECISION

    summary = {
        "stage": "330C",
        "output_dir": str(output_dir),
        "validated_330b_scoring": _norm_text(trust_scoring_summary.get("decision")) == READY_330B_DECISION and qa_fail_count == 0,
        "candidate_source_dir_count": len(candidate_source_dirs),
        "cached_candidate_count": len(cached_candidate_rows) - fallback_fixture_count,
        "fallback_fixture_count": fallback_fixture_count,
        "candidate_source_status": candidate_source_status,
        "scored_record_count": len(scored_records),
        "confidence_level_distribution": confidence_level_distribution,
        "routing_decision_distribution": routing_decision_distribution,
        "risk_flag_distribution": risk_flag_distribution,
        "score_bucket_distribution": score_bucket_distribution,
        "source_artifact_distribution": {str(k): int(v) for k, v in source_artifact_distribution.items()},
        "candidate_source_dir_record_counts": {str(k): int(v) for k, v in candidate_source_dir_record_counts.items()},
        "existing_status_distribution": existing_status_distribution,
        "sidecar_vs_existing_status_comparison": sidecar_vs_existing_rows,
        "calibration_sample_count": calibration_sample_count,
        "potential_false_trusted_count": int(potential_false_trusted_mask.sum()) if not scored_df.empty else 0,
        "trusted_with_warning_risk_count": int(trusted_with_warning_mask.sum()) if not scored_df.empty else 0,
        "trusted_with_low_evidence_count": int(trusted_with_low_evidence_mask.sum()) if not scored_df.empty else 0,
        "review_required_high_score_count": int(review_required_high_score_mask.sum()) if not scored_df.empty else 0,
        "rejected_or_needs_more_info_high_score_count": int(rejected_or_needs_more_info_high_score_mask.sum()) if not scored_df.empty else 0,
        "missing_evidence_count": int(missing_evidence_mask.sum()) if not scored_df.empty else 0,
        "no_official_asset_modification_during_330c": no_official_asset_modification_during_330c,
        "official_assets_written": [],
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": decision,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    no_apply_proof_json = {
        "stage": "330C",
        "files_read": [str(path) for path in [alias_asset_path, scope_asset_path]],
        "official_assets_before": official_assets_before,
        "official_assets_after": official_assets_after,
        "official_assets_written": [],
        "no_official_asset_modification_during_330c": no_official_asset_modification_during_330c,
    }
    benchmark_json = {
        "candidate_source_status": candidate_source_status,
        "artifact_inventory": artifact_inventory_df.to_dict(orient="records"),
        "scored_record_count": len(scored_records),
        "confidence_level_distribution": confidence_level_distribution,
        "routing_decision_distribution": routing_decision_distribution,
        "risk_flag_distribution": risk_flag_distribution,
        "score_bucket_distribution": score_bucket_distribution,
        "existing_status_distribution": existing_status_distribution,
        "sidecar_vs_existing_status_comparison": sidecar_vs_existing_rows,
    }
    official_asset_proof_df = pd.DataFrame(
        [
            {
                "asset_path": asset_path,
                "hash_before": before_hash,
                "hash_after": official_assets_after.get(asset_path, ""),
                "modified_during_330c": before_hash != official_assets_after.get(asset_path, ""),
            }
            for asset_path, before_hash in official_assets_before.items()
        ]
    ).fillna("")
    calibration_summary_df = pd.DataFrame(
        [
            {"issue": "potential_false_trusted_count", "count": summary["potential_false_trusted_count"]},
            {"issue": "trusted_with_warning_risk_count", "count": summary["trusted_with_warning_risk_count"]},
            {"issue": "trusted_with_low_evidence_count", "count": summary["trusted_with_low_evidence_count"]},
            {"issue": "review_required_high_score_count", "count": summary["review_required_high_score_count"]},
            {"issue": "rejected_or_needs_more_info_high_score_count", "count": summary["rejected_or_needs_more_info_high_score_count"]},
            {"issue": "missing_evidence_count", "count": summary["missing_evidence_count"]},
            {"issue": "calibration_sample_count", "count": summary["calibration_sample_count"]},
        ]
    ).fillna("")
    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "sidecar_only",
                "detail": "330C scores cached candidates in a sidecar benchmark only and does not override production routing.",
            },
            {
                "limitation": "best_effort_field_mapping",
                "detail": "Candidate field mapping is best-effort across heterogeneous cached artifacts and may miss dataset-specific nuance.",
            },
            {
                "limitation": "cached_artifact_scope",
                "detail": "Only curated candidate-like cached artifacts are loaded; summary-only outputs are intentionally skipped.",
            },
        ]
    ).fillna("")

    return {
        "summary": summary,
        "qa_json": qa_json,
        "benchmark_json": benchmark_json,
        "no_apply_proof_json": no_apply_proof_json,
        "artifact_inventory_df": artifact_inventory_df,
        "scored_records_df": scored_df,
        "confidence_distribution_df": pd.DataFrame(
            [{"confidence_level": key, "count": value} for key, value in confidence_level_distribution.items()]
        ).fillna(""),
        "routing_distribution_df": pd.DataFrame(
            [{"routing_decision": key, "count": value} for key, value in routing_decision_distribution.items()]
        ).fillna(""),
        "risk_distribution_df": pd.DataFrame(
            [{"risk_flag": key, "count": value} for key, value in risk_flag_distribution.items()]
        ).fillna(""),
        "score_bucket_distribution_df": pd.DataFrame(
            [{"score_bucket": key, "count": value} for key, value in score_bucket_distribution.items()]
        ).fillna(""),
        "existing_status_distribution_df": pd.DataFrame(
            [{"existing_status": key, "count": value} for key, value in existing_status_distribution.items()]
        ).fillna(""),
        "sidecar_vs_existing_df": pd.DataFrame(sidecar_vs_existing_rows).fillna(""),
        "calibration_summary_df": calibration_summary_df,
        "calibration_sets": calibration_sets,
        "official_asset_proof_df": official_asset_proof_df,
        "qa_summary_df": pd.DataFrame(
            [
                {
                    "qa_pass_count": qa_pass_count,
                    "qa_warn_count": qa_warn_count,
                    "qa_fail_count": qa_fail_count,
                    "blocking_reasons": " | ".join(blocking_reasons),
                    "decision": decision,
                }
            ]
        ).fillna(""),
        "qa_checks_df": qa_df,
        "known_limitations_df": known_limitations_df,
    }
