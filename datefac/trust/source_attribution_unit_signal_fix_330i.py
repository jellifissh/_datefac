from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.unfamiliar_candidate_export_smoke_330f4 import (
    _compatibility_row_from_prepared,
)
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import (
    REQUIRED_FIELDS,
    _frame_for_output,
    _norm_text,
    _safe_int,
)
from datefac.trust.unfamiliar_pdf_trust_benchmark_330f import (
    READY_DECISION as READY_330F_DECISION,
    build_unfamiliar_pdf_trust_benchmark_330f,
)


READY_330H_DECISION = (
    "FULL_UNFAMILIAR_EXPORT_BENCHMARK_330H_READY_FOR_330I_SOURCE_ATTRIBUTION_UNIT_FIX"
)
READY_DECISION = (
    "SOURCE_ATTRIBUTION_UNIT_SIGNAL_FIX_330I_READY_FOR_330J_DELIVERY_REPORT_REFRESH"
)
READY_WITHOUT_RERUN_DECISION = (
    "SOURCE_ATTRIBUTION_UNIT_SIGNAL_FIX_330I_READY_FOR_330F_RERUN_OR_330J_DELIVERY_REPORT_REFRESH"
)
NOT_READY_DECISION = "SOURCE_ATTRIBUTION_UNIT_SIGNAL_FIX_330I_NOT_READY"

DEFAULT_FULL_UNFAMILIAR_BENCHMARK_DIR = Path(
    r"D:\_datefac\output\full_unfamiliar_export_benchmark_330h"
)
DEFAULT_PREPARED_UNFAMILIAR_DIR = Path(r"D:\_datefac\output\unfamiliar_trust_split_330h")
DEFAULT_FIXED_PREPARED_OUTPUT_DIR = Path(r"D:\_datefac\output\unfamiliar_trust_split_330i")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\source_attribution_unit_signal_fix_330i")
DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR = Path(
    r"D:\_datefac\output\deduped_candidate_trust_benchmark_330e"
)
DEFAULT_TRUST_SCORING_DIR = Path(r"D:\_datefac\output\trust_engine_scoring_330b")

FIX_METADATA_FIELDS = [
    "unit_fix_method",
    "unit_fix_source_text",
    "unit_fix_confidence",
    "unit_fix_notes",
]
OUTPUT_FIELDS = list(REQUIRED_FIELDS) + FIX_METADATA_FIELDS

PAREN_PAIRS = [
    ("\uFF08", "\uFF09"),
    ("(", ")"),
]

UNIT_UNKNOWN_FLAG = "UNIT_UNKNOWN"
UNIT_CONFLICT_FLAG = "UNIT_CONFLICT"


@dataclass(frozen=True)
class UnitHint:
    normalized_unit: str
    source_text: str
    method: str
    confidence: str
    notes: str


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_jsonl_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
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


def _listify_tokens(value: Any) -> List[str]:
    if value in ("", None):
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    else:
        text = _norm_text(value)
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = None
            if isinstance(parsed, list):
                items = parsed
            else:
                items = [text]
        else:
            items = [token for token in text.replace("|", ",").replace(";", ",").split(",")]
    out: List[str] = []
    seen = set()
    for item in items:
        token = _norm_text(item)
        if token and token not in seen:
            out.append(token)
            seen.add(token)
    return out


def _ordered_unique(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        token = _norm_text(item)
        if token and token not in seen:
            out.append(token)
            seen.add(token)
    return out


def _normalize_unit_text(text: str) -> str:
    raw = _norm_text(text)
    if not raw:
        return ""
    normalized = raw.casefold().replace(" ", "")
    mapping = {
        "\u767e\u4e07\u5143": "RMB_mn",
        "rmbmn": "RMB_mn",
        "rmbmillion": "RMB_mn",
        "cnymillion": "RMB_mn",
        "\u4ebf\u5143": "RMB_100m",
        "\u4eba\u6c11\u5e01\u4ebf\u5143": "RMB_100m",
        "rmbbn": "RMB_100m",
        "\u767e\u4e07\u7f8e\u5143": "USD_mn",
        "usdmillion": "USD_mn",
        "\u4ebf\u7f8e\u5143": "USD_100m",
        "usdbn": "USD_100m",
        "%": "percent",
        "pct": "percent",
        "percentage": "percent",
        "\u5143/\u80a1": "RMB_per_share",
        "rmb/share": "RMB_per_share",
        "rmbpershare": "RMB_per_share",
        "x": "x",
        "\u500d": "x",
    }
    return mapping.get(normalized, "")


def _extract_parenthetical_tokens(text: str) -> List[str]:
    source = _norm_text(text)
    if not source:
        return []
    tokens: List[str] = []
    for left, right in PAREN_PAIRS:
        start = 0
        while True:
            left_index = source.find(left, start)
            if left_index < 0:
                break
            right_index = source.find(right, left_index + 1)
            if right_index < 0:
                break
            token = _norm_text(source[left_index + 1 : right_index])
            if token:
                tokens.append(token)
            start = right_index + 1
    return _ordered_unique(tokens)


def _collect_text_fields(row: Mapping[str, Any]) -> List[tuple[str, str]]:
    values: List[tuple[str, str]] = [
        ("row_text", _norm_text(row.get("row_text"))),
        ("metric_label_raw", _norm_text(row.get("metric_label_raw"))),
        ("table_id", _norm_text(row.get("table_id"))),
        ("source_artifact", _norm_text(row.get("source_artifact"))),
    ]
    for ref in _listify_tokens(row.get("evidence_refs")):
        values.append(("evidence_refs", ref))
    return [(label, text) for label, text in values if text]


def _semantic_allowed_units(metric: str) -> set[str] | None:
    mapping = {
        "eps": {"RMB_per_share"},
        "gross_margin": {"percent"},
        "pe": {"x"},
        "pb": {"x"},
        "ev_ebitda": {"x"},
    }
    return mapping.get(_norm_text(metric).casefold())


def _is_semantic_conflict(metric: str, normalized_unit: str) -> bool:
    allowed = _semantic_allowed_units(metric)
    if not allowed:
        return False
    return normalized_unit not in allowed


def _infer_unit_hints(row: Mapping[str, Any]) -> List[UnitHint]:
    hints: List[UnitHint] = []
    for label, text in _collect_text_fields(row):
        for token in _extract_parenthetical_tokens(text):
            normalized = _normalize_unit_text(token)
            if not normalized:
                continue
            hints.append(
                UnitHint(
                    normalized_unit=normalized,
                    source_text=token,
                    method="INFERRED_FROM_EXPLICIT_PARENTHESES",
                    confidence="HIGH",
                    notes=f"explicit unit token from {label}",
                )
            )

        text_value = _norm_text(text)
        if "%" in text_value:
            hints.append(
                UnitHint(
                    normalized_unit="percent",
                    source_text="%",
                    method="INFERRED_FROM_PERCENT_SYMBOL",
                    confidence="HIGH",
                    notes=f"percent symbol found in {label}",
                )
            )

        normalized_text = text_value.casefold()
        if "pct" in normalized_text or "percentage" in normalized_text:
            hints.append(
                UnitHint(
                    normalized_unit="percent",
                    source_text="pct" if "pct" in normalized_text else "percentage",
                    method="INFERRED_FROM_PERCENT_TOKEN",
                    confidence="MEDIUM",
                    notes=f"percent token found in {label}",
                )
            )

    unique: List[UnitHint] = []
    seen = set()
    for hint in hints:
        key = (
            hint.normalized_unit,
            hint.source_text,
            hint.method,
            hint.confidence,
            hint.notes,
        )
        if key not in seen:
            unique.append(hint)
            seen.add(key)
    return unique


def _missing_field_counts(frame: pd.DataFrame, fields: Sequence[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    if frame.empty:
        return {field: 0 for field in fields}
    for field in fields:
        missing = 0
        for value in frame[field].tolist():
            if isinstance(value, list):
                if not value:
                    missing += 1
            elif value in ("", None):
                missing += 1
            elif isinstance(value, float) and pd.isna(value):
                missing += 1
        counts[field] = int(missing)
    return counts


def validate_330h_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
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
        "readiness::330h_decision",
        _norm_text(summary.get("decision")) == READY_330H_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330h_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    add(
        "inventory::unfamiliar_pdf_count",
        _safe_int(summary.get("unfamiliar_pdf_count"), -1) == 13,
        str(summary.get("unfamiliar_pdf_count", "")),
    )
    add(
        "processing::processed_pdf_count",
        _safe_int(summary.get("processed_pdf_count"), -1) == 13,
        str(summary.get("processed_pdf_count", "")),
    )
    add(
        "processing::failed_pdf_count",
        _safe_int(summary.get("failed_pdf_count"), -1) == 0,
        str(summary.get("failed_pdf_count", "")),
    )
    add(
        "records::prepared_candidate_row_count",
        _safe_int(summary.get("prepared_candidate_row_count"), -1) == 117,
        str(summary.get("prepared_candidate_row_count", "")),
    )
    add(
        "quality::source_pdf_preserved",
        bool(summary.get("source_pdf_preserved")) is True,
        str(summary.get("source_pdf_preserved", "")),
    )
    add(
        "quality::source_page_missing_count",
        _safe_int(summary.get("source_page_missing_count"), -1) == 0,
        str(summary.get("source_page_missing_count", "")),
    )
    add(
        "quality::unit_missing_count",
        _safe_int(summary.get("unit_missing_count"), -1) == 64,
        str(summary.get("unit_missing_count", "")),
    )
    add(
        "safety::no_official_asset_modification_during_330h",
        bool(summary.get("no_official_asset_modification_during_330h")) is True,
        str(summary.get("no_official_asset_modification_during_330h", "")),
    )
    return checks


def _choose_hint_for_metric(metric: str, hints: Sequence[UnitHint]) -> UnitHint | None:
    allowed = _semantic_allowed_units(metric)
    if allowed:
        for hint in hints:
            if hint.normalized_unit in allowed:
                return hint
        return None
    monetary_priority = [
        "RMB_per_share",
        "RMB_mn",
        "RMB_100m",
        "USD_mn",
        "USD_100m",
        "percent",
        "x",
    ]
    for target in monetary_priority:
        for hint in hints:
            if hint.normalized_unit == target:
                return hint
    return hints[0] if hints else None


def _fix_single_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    risk_flags = _ordered_unique(_listify_tokens(out.get("risk_flags")))
    metric = _norm_text(out.get("normalized_metric"))
    original_unit = _norm_text(out.get("unit"))
    normalized_existing_unit = _normalize_unit_text(original_unit)
    hints = _infer_unit_hints(out)
    chosen_hint = _choose_hint_for_metric(metric, hints)

    final_unit = original_unit
    fix_method = "PRESERVED_AS_IS"
    fix_source_text = original_unit
    fix_confidence = ""
    fix_notes = ""

    if original_unit:
        if normalized_existing_unit:
            if _is_semantic_conflict(metric, normalized_existing_unit):
                final_unit = ""
                fix_method = "CLEARED_SEMANTIC_CONFLICT"
                fix_source_text = original_unit
                fix_confidence = "HIGH"
                fix_notes = (
                    f"existing unit {original_unit} conflicts with metric {metric}"
                )
                if UNIT_CONFLICT_FLAG not in risk_flags:
                    risk_flags.append(UNIT_CONFLICT_FLAG)
                if chosen_hint is not None:
                    final_unit = chosen_hint.normalized_unit
                    fix_method = chosen_hint.method
                    fix_source_text = chosen_hint.source_text
                    fix_confidence = chosen_hint.confidence
                    fix_notes = (
                        f"{chosen_hint.notes}; replaced conflicting unit {original_unit}"
                    )
            else:
                final_unit = normalized_existing_unit
                if final_unit == original_unit:
                    fix_method = "PRESERVED_EXISTING_UNIT"
                else:
                    fix_method = "NORMALIZED_EXISTING_UNIT"
                fix_source_text = original_unit
                fix_confidence = "HIGH"
                fix_notes = "existing unit preserved after canonical normalization"
        else:
            fix_method = "PRESERVED_UNRECOGNIZED_UNIT"
            fix_source_text = original_unit
            fix_confidence = ""
            fix_notes = "existing unit preserved because no safe canonical mapping was found"
    else:
        if chosen_hint is not None:
            final_unit = chosen_hint.normalized_unit
            fix_method = chosen_hint.method
            fix_source_text = chosen_hint.source_text
            fix_confidence = chosen_hint.confidence
            fix_notes = chosen_hint.notes
        else:
            final_unit = ""
            fix_method = "LEFT_MISSING"
            fix_source_text = ""
            fix_confidence = ""
            fix_notes = "no safe unit evidence found in existing row context"

    if not _norm_text(final_unit):
        if UNIT_UNKNOWN_FLAG not in risk_flags:
            risk_flags.append(UNIT_UNKNOWN_FLAG)
    out["unit"] = final_unit
    out["risk_flags"] = risk_flags
    out["unit_fix_method"] = fix_method
    out["unit_fix_source_text"] = fix_source_text
    out["unit_fix_confidence"] = fix_confidence
    out["unit_fix_notes"] = fix_notes
    return out


def _write_fixed_prepared_outputs(
    fixed_prepared_output_dir: Path,
    fixed_df: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> Dict[str, str]:
    fixed_prepared_output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = fixed_prepared_output_dir / "unfamiliar_candidate_rows.jsonl"
    xlsx_path = fixed_prepared_output_dir / "unfamiliar_candidate_rows.xlsx"
    manifest_path = fixed_prepared_output_dir / "unfamiliar_candidate_manifest.json"

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in fixed_df.to_dict(orient="records"):
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        fixed_df.to_excel(writer, sheet_name="unfamiliar_candidate_rows", index=False)
        pd.DataFrame(
            [
                {"field_name": key, "missing_count": value}
                for key, value in _missing_field_counts(fixed_df, OUTPUT_FIELDS).items()
            ]
        ).to_excel(writer, sheet_name="missing_field_counts", index=False)

    manifest_path.write_text(json.dumps(dict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "jsonl_path": str(jsonl_path),
        "xlsx_path": str(xlsx_path),
        "manifest_path": str(manifest_path),
    }


def _write_rerun_compatibility_inputs(
    compat_dir: Path,
    fixed_rows: Sequence[Mapping[str, Any]],
) -> Dict[str, str]:
    compat_dir.mkdir(parents=True, exist_ok=True)
    compat_jsonl_path = compat_dir / "unfamiliar_330i_rerun_affected_candidates.jsonl"
    compat_xlsx_path = compat_dir / "unfamiliar_330i_rerun_affected_candidates.xlsx"
    compatibility_rows = [_compatibility_row_from_prepared(row) for row in fixed_rows]

    with compat_jsonl_path.open("w", encoding="utf-8") as handle:
        for row in compatibility_rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    with pd.ExcelWriter(compat_xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame(compatibility_rows).to_excel(
            writer,
            sheet_name="affected_candidates",
            index=False,
        )
    return {
        "compat_jsonl_path": str(compat_jsonl_path),
        "compat_xlsx_path": str(compat_xlsx_path),
    }


def _rerun_330f(
    *,
    compat_dir: Path,
    rerun_output_dir: Path,
    deduped_candidate_benchmark_dir: Path,
    trust_scoring_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
) -> Dict[str, Any]:
    from datefac.trust.unfamiliar_pdf_trust_benchmark_330f_report import (
        SAMPLES_SHEET_ORDER,
        SUMMARY_SHEET_ORDER,
        unfamiliar_pdf_trust_benchmark_330f_markdown,
        write_excel,
        write_json,
    )

    deduped_summary_path = (
        deduped_candidate_benchmark_dir
        / "deduped_candidate_trust_benchmark_330e_summary.json"
    )
    deduped_qa_path = (
        deduped_candidate_benchmark_dir / "deduped_candidate_trust_benchmark_330e_qa.json"
    )
    trust_scoring_summary_path = trust_scoring_dir / "trust_engine_scoring_330b_summary.json"

    artifacts = build_unfamiliar_pdf_trust_benchmark_330f(
        deduped_candidate_summary=_read_json(deduped_summary_path),
        deduped_candidate_qa=_read_json(deduped_qa_path),
        trust_scoring_summary=_read_json(trust_scoring_summary_path),
        unfamiliar_source_dirs=[compat_dir],
        output_dir=rerun_output_dir,
        alias_asset_path=alias_asset_path,
        scope_asset_path=scope_asset_path,
        files_read=[
            str(deduped_summary_path),
            str(deduped_qa_path),
            str(trust_scoring_summary_path),
            str(compat_dir),
            str(alias_asset_path),
            str(scope_asset_path),
        ],
    )

    rerun_output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = rerun_output_dir / "unfamiliar_pdf_trust_benchmark_330f_summary.json"
    qa_json = rerun_output_dir / "unfamiliar_pdf_trust_benchmark_330f_qa.json"
    no_apply_json = rerun_output_dir / "unfamiliar_pdf_trust_benchmark_330f_no_apply_proof.json"
    summary_xlsx = rerun_output_dir / "unfamiliar_pdf_trust_benchmark_330f_summary.xlsx"
    samples_xlsx = rerun_output_dir / "unfamiliar_pdf_trust_benchmark_330f_samples.xlsx"
    report_md = rerun_output_dir / "unfamiliar_pdf_trust_benchmark_330f_report.md"
    scored_jsonl = rerun_output_dir / "unfamiliar_pdf_trust_benchmark_330f_scored_records.jsonl"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "source_inventory": artifacts["source_inventory_df"],
            "coverage": artifacts["coverage_df"],
            "distribution": artifacts["distribution_df"],
            "delivery_summary": artifacts["delivery_summary_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
            "known_limitations": artifacts["known_limitations_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    write_excel(
        samples_xlsx,
        {
            "summary": artifacts["summary_df"],
            "artifact_row_view": artifacts["artifact_row_view_df"],
            "strict_deduped_view": artifacts["strict_deduped_view_df"],
            "cross_artifact_deduped_view": artifacts["cross_artifact_deduped_view_df"],
            "strict_duplicate_rows": artifacts["strict_duplicate_rows_df"],
            "cross_artifact_duplicate_rows": artifacts["cross_artifact_duplicate_rows_df"],
            "qa_checks": artifacts["qa_checks_df"],
        },
        SAMPLES_SHEET_ORDER,
    )
    report_md.write_text(
        unfamiliar_pdf_trust_benchmark_330f_markdown(artifacts["summary"]),
        encoding="utf-8",
    )
    with scored_jsonl.open("w", encoding="utf-8") as handle:
        for row in artifacts["artifact_row_view_df"].to_dict(orient="records"):
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    return artifacts


def build_source_attribution_unit_signal_fix_330i(
    *,
    full_unfamiliar_benchmark_dir: Path,
    prepared_unfamiliar_dir: Path,
    fixed_prepared_output_dir: Path,
    output_dir: Path,
    rerun_330f: bool,
    deduped_candidate_benchmark_dir: Path,
    trust_scoring_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    summary_path = (
        full_unfamiliar_benchmark_dir / "full_unfamiliar_export_benchmark_330h_summary.json"
    )
    manifest_path = prepared_unfamiliar_dir / "unfamiliar_candidate_manifest.json"
    input_jsonl_path = prepared_unfamiliar_dir / "unfamiliar_candidate_rows.jsonl"

    summary_330h = _read_json(summary_path)
    input_manifest = _read_json(manifest_path)
    input_rows = _read_jsonl_rows(input_jsonl_path)

    qa_rows = validate_330h_summary(summary_330h)

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

    fixed_rows = [_fix_single_row(row) for row in input_rows]
    fixed_df = _frame_for_output(pd.DataFrame(fixed_rows, columns=OUTPUT_FIELDS))

    input_candidate_ids = [_norm_text(row.get("candidate_id")) for row in input_rows]
    output_candidate_ids = [_norm_text(row.get("candidate_id")) for row in fixed_rows]
    candidate_id_mismatch_count = int(
        sum(1 for left, right in zip(input_candidate_ids, output_candidate_ids) if left != right)
    )
    candidate_id_stability_check = (
        len(input_candidate_ids) == len(output_candidate_ids) and candidate_id_mismatch_count == 0
    )

    source_pdf_nonempty_count = int(
        sum(1 for row in fixed_rows if _norm_text(row.get("source_pdf")))
    )
    source_pdf_unique_count = int(
        len({_norm_text(row.get("source_pdf")) for row in fixed_rows if _norm_text(row.get("source_pdf"))})
    )
    source_page_nonempty_count = int(
        sum(1 for row in fixed_rows if _norm_text(row.get("source_page")))
    )
    source_page_missing_count_after = int(
        sum(1 for row in fixed_rows if not _norm_text(row.get("source_page")))
    )
    source_artifact_nonempty_count = int(
        sum(1 for row in fixed_rows if _norm_text(row.get("source_artifact")))
    )

    unit_missing_count_before = int(
        sum(1 for row in input_rows if not _norm_text(row.get("unit")))
    )
    unit_missing_count_after = int(
        sum(1 for row in fixed_rows if not _norm_text(row.get("unit")))
    )
    unit_filled_count = int(
        sum(
            1
            for before_row, after_row in zip(input_rows, fixed_rows)
            if (not _norm_text(before_row.get("unit"))) and _norm_text(after_row.get("unit"))
        )
    )
    unit_inference_high_confidence_count = int(
        sum(
            1
            for row in fixed_rows
            if _norm_text(row.get("unit_fix_confidence")) == "HIGH"
            and _norm_text(row.get("unit_fix_method")).startswith("INFERRED_")
        )
    )
    unit_inference_medium_confidence_count = int(
        sum(
            1
            for row in fixed_rows
            if _norm_text(row.get("unit_fix_confidence")) == "MEDIUM"
            and _norm_text(row.get("unit_fix_method")).startswith("INFERRED_")
        )
    )
    unit_inference_low_confidence_count = int(
        sum(
            1
            for row in fixed_rows
            if _norm_text(row.get("unit_fix_confidence")) == "LOW"
            and _norm_text(row.get("unit_fix_method")).startswith("INFERRED_")
        )
    )
    unit_unknown_risk_added_count = int(
        sum(
            1
            for before_row, after_row in zip(input_rows, fixed_rows)
            if UNIT_UNKNOWN_FLAG not in _listify_tokens(before_row.get("risk_flags"))
            and UNIT_UNKNOWN_FLAG in _listify_tokens(after_row.get("risk_flags"))
        )
    )
    unit_conflict_flag_added_count = int(
        sum(
            1
            for before_row, after_row in zip(input_rows, fixed_rows)
            if UNIT_CONFLICT_FLAG not in _listify_tokens(before_row.get("risk_flags"))
            and UNIT_CONFLICT_FLAG in _listify_tokens(after_row.get("risk_flags"))
        )
    )

    input_source_pdf_names = {
        _norm_text(row.get("source_pdf")) for row in input_rows if _norm_text(row.get("source_pdf"))
    }
    output_source_pdf_names = {
        _norm_text(row.get("source_pdf")) for row in fixed_rows if _norm_text(row.get("source_pdf"))
    }
    source_pdf_preserved = input_source_pdf_names == output_source_pdf_names and bool(
        output_source_pdf_names
    )

    add_qa("records::input_candidate_row_count", len(input_rows) == 117, str(len(input_rows)))
    add_qa("records::output_candidate_row_count", len(fixed_rows) == 117, str(len(fixed_rows)))
    add_qa(
        "quality::candidate_id_stability_check",
        candidate_id_stability_check,
        str(candidate_id_mismatch_count),
    )
    add_qa(
        "quality::source_pdf_preserved_after_fix",
        source_pdf_preserved,
        json.dumps(sorted(output_source_pdf_names), ensure_ascii=False),
    )
    add_qa(
        "quality::source_page_missing_count_after",
        source_page_missing_count_after == 0,
        str(source_page_missing_count_after),
    )
    add_qa(
        "quality::unit_missing_count_before",
        unit_missing_count_before == 64,
        str(unit_missing_count_before),
    )
    add_qa(
        "quality::unit_missing_count_after",
        unit_missing_count_after <= unit_missing_count_before,
        str(unit_missing_count_after),
    )

    output_manifest: Dict[str, Any] = {
        "stage": "330I",
        "validated_330h_full_benchmark": all(
            row.get("status") == "PASS" for row in validate_330h_summary(summary_330h)
        ),
        "input_candidate_row_count": int(len(input_rows)),
        "output_candidate_row_count": int(len(fixed_rows)),
        "prepared_output_dir": str(fixed_prepared_output_dir),
        "required_fields": list(REQUIRED_FIELDS),
        "fix_metadata_fields": list(FIX_METADATA_FIELDS),
        "canonical_candidate_source_file": "unfamiliar_candidate_rows.jsonl",
        "inspection_mirror_file": "unfamiliar_candidate_rows.xlsx",
        "inspection_mirror_role": "xlsx_inspection_mirror_only_not_additional_candidate_source",
        "source_pdf_nonempty_count": source_pdf_nonempty_count,
        "source_pdf_unique_count": source_pdf_unique_count,
        "source_page_nonempty_count": source_page_nonempty_count,
        "source_page_missing_count_after": source_page_missing_count_after,
        "source_artifact_nonempty_count": source_artifact_nonempty_count,
        "candidate_id_stability_check": candidate_id_stability_check,
        "candidate_id_mismatch_count": candidate_id_mismatch_count,
        "source_pdf_preserved": source_pdf_preserved,
        "unit_missing_count_before": unit_missing_count_before,
        "unit_missing_count_after": unit_missing_count_after,
        "unit_filled_count": unit_filled_count,
        "unit_inference_high_confidence_count": unit_inference_high_confidence_count,
        "unit_inference_medium_confidence_count": unit_inference_medium_confidence_count,
        "unit_inference_low_confidence_count": unit_inference_low_confidence_count,
        "unit_unknown_risk_added_count": unit_unknown_risk_added_count,
        "unit_conflict_flag_added_count": unit_conflict_flag_added_count,
    }
    output_manifest.update(
        _write_fixed_prepared_outputs(
            fixed_prepared_output_dir=fixed_prepared_output_dir,
            fixed_df=fixed_df,
            manifest=output_manifest,
        )
    )

    rerun_summary: Dict[str, Any] = {}
    rerun_artifacts: Dict[str, Any] | None = None
    rerun_compat_paths: Dict[str, str] = {}
    rerun_output_dir = output_dir / "rerun_330f"
    rerun_compat_dir = output_dir / "rerun_330f_input_compat"
    if rerun_330f:
        rerun_compat_paths = _write_rerun_compatibility_inputs(
            compat_dir=rerun_compat_dir,
            fixed_rows=fixed_rows,
        )
        rerun_artifacts = _rerun_330f(
            compat_dir=rerun_compat_dir,
            rerun_output_dir=rerun_output_dir,
            deduped_candidate_benchmark_dir=deduped_candidate_benchmark_dir,
            trust_scoring_dir=trust_scoring_dir,
            alias_asset_path=alias_asset_path,
            scope_asset_path=scope_asset_path,
        )
        rerun_summary = rerun_artifacts["summary"]
        add_qa(
            "rerun::330f_unfamiliar_source_status",
            _norm_text(rerun_summary.get("unfamiliar_source_status")) == "loaded",
            _norm_text(rerun_summary.get("unfamiliar_source_status")),
        )
        add_qa(
            "rerun::330f_scored_unfamiliar_record_count",
            _safe_int(rerun_summary.get("scored_unfamiliar_record_count"), 0) > 0,
            str(rerun_summary.get("scored_unfamiliar_record_count", "")),
        )
        add_qa(
            "rerun::330f_decision",
            _norm_text(rerun_summary.get("decision")) == READY_330F_DECISION,
            _norm_text(rerun_summary.get("decision")),
        )

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest()
        if alias_asset_path.exists()
        else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest()
        if scope_asset_path.exists()
        else "__MISSING__",
    }
    no_official_asset_modification_during_330i = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330i",
        no_official_asset_modification_during_330i,
        json.dumps(
            {"before": official_assets_before, "after": official_assets_after},
            ensure_ascii=False,
        ),
    )

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = (
        qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else []
    )

    reran_330f_successfully = bool(rerun_summary) and (
        _norm_text(rerun_summary.get("decision")) == READY_330F_DECISION
        and _safe_int(rerun_summary.get("scored_unfamiliar_record_count"), 0) > 0
    )

    if qa_fail_count > 0:
        decision = NOT_READY_DECISION
    elif rerun_330f and reran_330f_successfully:
        decision = READY_DECISION
    else:
        decision = READY_WITHOUT_RERUN_DECISION

    summary = {
        "stage": "330I",
        "output_dir": str(output_dir),
        "prepared_output_dir": str(fixed_prepared_output_dir),
        "validated_330h_full_benchmark": output_manifest["validated_330h_full_benchmark"],
        "input_candidate_row_count": int(len(input_rows)),
        "output_candidate_row_count": int(len(fixed_rows)),
        "source_pdf_nonempty_count": source_pdf_nonempty_count,
        "source_pdf_unique_count": source_pdf_unique_count,
        "source_page_nonempty_count": source_page_nonempty_count,
        "source_page_missing_count_after": source_page_missing_count_after,
        "source_artifact_nonempty_count": source_artifact_nonempty_count,
        "candidate_id_stability_check": candidate_id_stability_check,
        "candidate_id_mismatch_count": candidate_id_mismatch_count,
        "source_pdf_preserved": source_pdf_preserved,
        "unit_missing_count_before": unit_missing_count_before,
        "unit_missing_count_after": unit_missing_count_after,
        "unit_filled_count": unit_filled_count,
        "unit_inference_high_confidence_count": unit_inference_high_confidence_count,
        "unit_inference_medium_confidence_count": unit_inference_medium_confidence_count,
        "unit_inference_low_confidence_count": unit_inference_low_confidence_count,
        "unit_unknown_risk_added_count": unit_unknown_risk_added_count,
        "unit_conflict_flag_added_count": unit_conflict_flag_added_count,
        "prepared_output_dir_for_330f": str(fixed_prepared_output_dir),
        "can_rerun_330f": True,
        "reran_330f": bool(rerun_330f),
        "rerun_330f_output_dir": str(rerun_output_dir) if rerun_330f else "",
        "rerun_330f_input_compat_dir": str(rerun_compat_dir) if rerun_330f else "",
        "330f_unfamiliar_source_status": _norm_text(
            rerun_summary.get("unfamiliar_source_status")
        ),
        "330f_scored_unfamiliar_record_count": _safe_int(
            rerun_summary.get("scored_unfamiliar_record_count"), 0
        ),
        "330f_decision": _norm_text(rerun_summary.get("decision")),
        "recommended_next_step": "330J_DELIVERY_REPORT_REFRESH",
        "official_assets_modified": False,
        "no_official_asset_modification_during_330i": no_official_asset_modification_during_330i,
        "files_written_to_official_assets": [],
        "qa_pass_count": qa_pass_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": decision,
    }

    qa_json = {
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "checks": qa_df.to_dict(orient="records"),
    }
    no_apply_proof_json = build_no_apply_proof(
        stage="330I",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    source_attribution_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "metric": "source_pdf_nonempty_count",
                    "value": source_pdf_nonempty_count,
                },
                {
                    "metric": "source_pdf_unique_count",
                    "value": source_pdf_unique_count,
                },
                {
                    "metric": "source_page_nonempty_count",
                    "value": source_page_nonempty_count,
                },
                {
                    "metric": "source_page_missing_count_after",
                    "value": source_page_missing_count_after,
                },
                {
                    "metric": "source_artifact_nonempty_count",
                    "value": source_artifact_nonempty_count,
                },
                {
                    "metric": "candidate_id_stability_check",
                    "value": candidate_id_stability_check,
                },
                {
                    "metric": "candidate_id_mismatch_count",
                    "value": candidate_id_mismatch_count,
                },
            ]
        )
    )
    unit_fix_summary_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "metric": "unit_missing_count_before",
                    "value": unit_missing_count_before,
                },
                {
                    "metric": "unit_missing_count_after",
                    "value": unit_missing_count_after,
                },
                {
                    "metric": "unit_filled_count",
                    "value": unit_filled_count,
                },
                {
                    "metric": "unit_inference_high_confidence_count",
                    "value": unit_inference_high_confidence_count,
                },
                {
                    "metric": "unit_inference_medium_confidence_count",
                    "value": unit_inference_medium_confidence_count,
                },
                {
                    "metric": "unit_inference_low_confidence_count",
                    "value": unit_inference_low_confidence_count,
                },
                {
                    "metric": "unit_unknown_risk_added_count",
                    "value": unit_unknown_risk_added_count,
                },
                {
                    "metric": "unit_conflict_flag_added_count",
                    "value": unit_conflict_flag_added_count,
                },
            ]
        )
    )
    confidence_distribution_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "unit_fix_confidence": bucket,
                    "count": count,
                }
                for bucket, count in pd.Series(
                    [_norm_text(row.get("unit_fix_confidence")) for row in fixed_rows]
                )
                .value_counts()
                .items()
                if _norm_text(bucket)
            ]
        )
    )
    risk_flag_update_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "risk_flag": bucket,
                    "count": count,
                }
                for bucket, count in pd.Series(
                    [
                        token
                        for row in fixed_rows
                        for token in _listify_tokens(row.get("risk_flags"))
                    ]
                )
                .value_counts()
                .items()
            ]
        )
    )
    official_asset_proof_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "asset_path": asset_path,
                    "hash_before": before_hash,
                    "hash_after": official_assets_after.get(asset_path, ""),
                    "modified_during_330i": before_hash
                    != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    rerun_summary_df = (
        _frame_for_output(pd.DataFrame([rerun_summary])) if rerun_summary else pd.DataFrame()
    )
    known_limitations_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "limitation": "row_context_only",
                    "detail": "330I only infers units from existing cached row context and does not reopen PDFs.",
                },
                {
                    "limitation": "canonical_prepared_output_only",
                    "detail": "The fixed prepared directory contains one canonical JSONL and one XLSX inspection mirror only.",
                },
                {
                    "limitation": "330f_rerun_compat_isolated",
                    "detail": "330F rerun compatibility artifacts are isolated under the 330I report directory and are not part of the canonical prepared output.",
                },
            ]
        )
    )

    return {
        "summary": summary,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "manifest_json": output_manifest,
        "summary_df": _frame_for_output(pd.DataFrame([summary])),
        "qa_summary_df": _frame_for_output(
            pd.DataFrame(
                [
                    {
                        "qa_pass_count": qa_pass_count,
                        "qa_fail_count": qa_fail_count,
                        "decision": decision,
                    }
                ]
            )
        ),
        "qa_checks_df": qa_df,
        "source_attribution_df": source_attribution_df,
        "unit_fix_summary_df": unit_fix_summary_df,
        "confidence_distribution_df": confidence_distribution_df,
        "risk_flag_update_df": risk_flag_update_df,
        "fixed_candidate_rows_df": fixed_df,
        "prepared_manifest_df": _frame_for_output(pd.DataFrame([output_manifest])),
        "official_asset_proof_df": official_asset_proof_df,
        "rerun_330f_summary_df": rerun_summary_df,
        "known_limitations_df": known_limitations_df,
        "input_manifest_json": input_manifest,
        "rerun_compat_paths": rerun_compat_paths,
    }
