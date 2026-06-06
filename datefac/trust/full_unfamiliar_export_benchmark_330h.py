from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from extractor_adapter import extract_pdfplumber_table_blocks
from datefac.extraction.row_text_cleaner import clean_row_texts
from datefac.extraction.row_text_metric_extractor import extract_metric_candidates_from_repaired_rows
from datefac.extraction.row_text_repair import repair_row_fragments
from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.unfamiliar_candidate_export_smoke_330f4 import (
    REQUIRED_FIELDS,
    _compatibility_row_from_prepared,
    _frame_for_output,
    _missing_field_counts,
    _norm_text,
    _row_text_rows_from_blocks,
)
from datefac.trust.unfamiliar_pdf_trust_benchmark_330f import (
    READY_DECISION as READY_330F_DECISION,
    build_unfamiliar_pdf_trust_benchmark_330f,
)


READY_330G_DECISION = "END_TO_END_DELIVERY_QUALITY_REPORT_330G_READY_FOR_330H_FULL_UNFAMILIAR_BENCHMARK"
READY_DECISION = "FULL_UNFAMILIAR_EXPORT_BENCHMARK_330H_READY_FOR_330I_SOURCE_ATTRIBUTION_UNIT_FIX"
NOT_READY_DECISION = "FULL_UNFAMILIAR_EXPORT_BENCHMARK_330H_NOT_READY"

DEFAULT_UNFAMILIAR_INPUT_DIR = Path(r"D:\_datefac\input\unfamiliar")
DEFAULT_PREVIOUS_DELIVERY_REPORT_DIR = Path(r"D:\_datefac\output\end_to_end_delivery_quality_report_330g")
DEFAULT_PREPARED_OUTPUT_DIR = Path(r"D:\_datefac\output\unfamiliar_trust_split_330h")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\full_unfamiliar_export_benchmark_330h")
DEFAULT_DEDUPED_CANDIDATE_BENCHMARK_DIR = Path(r"D:\_datefac\output\deduped_candidate_trust_benchmark_330e")
DEFAULT_TRUST_SCORING_DIR = Path(r"D:\_datefac\output\trust_engine_scoring_330b")
COMPATIBILITY_ARTIFACT_STEM = "unfamiliar_full_330h_affected_candidates"

PAREN_UNIT_RULE = re.compile(r"[（(]([^()（）]{1,16})[)）]")
UNIT_HINTS = [
    "%",
    "倍",
    "x",
    "元/股",
    "元/支",
    "元/吨",
    "万元",
    "百万元",
    "千万元",
    "亿元",
    "亿美元",
    "万支",
    "亿支",
    "万台",
    "万吨",
    "万平",
    "万平方米",
]


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _stable_candidate_id(payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha1(
        json.dumps(
            {
                "source_pdf": _norm_text(payload.get("source_pdf")),
                "source_page": _norm_text(payload.get("source_page")),
                "table_id": _norm_text(payload.get("table_id")),
                "row_text": _norm_text(payload.get("row_text")),
                "normalized_metric": _norm_text(payload.get("normalized_metric")),
                "year": _norm_text(payload.get("year")),
                "value": _norm_text(payload.get("value")),
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return f"330h::{digest[:20]}"


def _normalize_unit_token(token: str) -> str:
    cleaned = _norm_text(token).replace("／", "/")
    cleaned = cleaned.replace(" ", "")
    if cleaned.lower() == "x":
        return "x"
    return cleaned


def _extract_units_from_text(text: str) -> List[str]:
    found: List[str] = []
    if not text:
        return found
    for token in PAREN_UNIT_RULE.findall(text):
        normalized = _normalize_unit_token(token)
        if normalized in UNIT_HINTS and normalized not in found:
            found.append(normalized)
    for hint in UNIT_HINTS:
        if hint == "%":
            continue
        if hint in text and hint not in found:
            found.append(hint)
    return found


def _infer_unit_from_context(candidate: Mapping[str, Any], row_context: Mapping[str, Any], table_context_rows: Sequence[str]) -> str:
    explicit = _norm_text(candidate.get("raw_unit"))
    if explicit:
        return explicit

    raw_value = _norm_text(candidate.get("raw_value") or candidate.get("normalized_value"))
    if raw_value.endswith("%"):
        return "%"

    row_units = _extract_units_from_text(_norm_text(row_context.get("row_text")))
    if len(row_units) == 1:
        return row_units[0]
    if len(row_units) > 1:
        return ""

    found: List[str] = []
    for text in [_norm_text(text) for text in table_context_rows]:
        for unit in _extract_units_from_text(text):
            if unit not in found:
                found.append(unit)
    if len(found) == 1:
        return found[0]
    return ""


def validate_330g_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add("readiness::330g_decision", _norm_text(summary.get("decision")) == READY_330G_DECISION, _norm_text(summary.get("decision")))
    add("readiness::330g_qa_fail_count", _safe_int(summary.get("qa_fail_count"), 1) == 0, str(summary.get("qa_fail_count", "")))
    add("records::330g_processed_pdf_count", _safe_int(summary.get("processed_pdf_count"), -1) == 3, str(summary.get("processed_pdf_count", "")))
    add(
        "records::330g_prepared_candidate_row_count",
        _safe_int(summary.get("prepared_candidate_row_count"), -1) == 83,
        str(summary.get("prepared_candidate_row_count", "")),
    )
    add(
        "records::330g_strict_deduped_candidate_count",
        _safe_int(summary.get("strict_deduped_candidate_count"), -1) == 83,
        str(summary.get("strict_deduped_candidate_count", "")),
    )
    add(
        "judgment::330g_delivery_readiness_judgment",
        _norm_text(summary.get("delivery_readiness_judgment")) == "SMOKE_DEMO_READY_INTERNAL_ONLY",
        _norm_text(summary.get("delivery_readiness_judgment")),
    )
    add(
        "recommendation::330g_next_step",
        _norm_text(summary.get("recommended_next_step")) == "330H_FULL_13_PDF_UNFAMILIAR_EXPORT_AND_BENCHMARK",
        _norm_text(summary.get("recommended_next_step")),
    )
    return checks


def _table_context_rows(row_text_rows: Sequence[Mapping[str, Any]]) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {}
    for row in row_text_rows:
        table_id = _norm_text(row.get("extracted_table_id"))
        if not table_id:
            continue
        grouped.setdefault(table_id, [])
        if len(grouped[table_id]) < 3:
            grouped[table_id].append(_norm_text(row.get("row_text")))
    return grouped


def _candidate_context_map(repaired_rows: Sequence[Mapping[str, Any]]) -> Dict[tuple[str, str], Dict[str, Any]]:
    out: Dict[tuple[str, str], Dict[str, Any]] = {}
    for row in repaired_rows:
        key = (_norm_text(row.get("extracted_table_id")), _norm_text(row.get("row_index")))
        out[key] = {
            "source_page": _norm_text(row.get("source_page")),
            "row_text": _norm_text(row.get("row_text_repaired") or row.get("row_text_cleaned") or row.get("row_text")),
            "source_file": _norm_text(row.get("source_file")),
        }
    return out


def _prepared_row_from_candidate_330h(
    candidate: Mapping[str, Any],
    *,
    row_context: Mapping[str, Any],
    table_context_rows: Sequence[str],
) -> Dict[str, Any]:
    risk_tokens = [token for token in _norm_text(candidate.get("risk_tags")).replace("|", ",").split(",") if _norm_text(token)]
    payload = {
        "candidate_id": "",
        "metric_label_raw": _norm_text(candidate.get("raw_metric_name")),
        "normalized_metric": _norm_text(candidate.get("metric_code")),
        "value": _norm_text(candidate.get("normalized_value") or candidate.get("raw_value")),
        "unit": _infer_unit_from_context(candidate, row_context, table_context_rows),
        "year": _norm_text(candidate.get("year")),
        "parser_sources": ["pdfplumber", "row_text_full_330h"],
        "evidence_refs": [
            f"table_id={_norm_text(candidate.get('extracted_table_id'))}",
            f"row_index={_norm_text(candidate.get('row_index'))}",
        ],
        "risk_flags": risk_tokens,
        "existing_status": "REVIEW_REQUIRED",
        "source_pdf": _norm_text(row_context.get("source_file") or candidate.get("source_file")),
        "source_artifact": "full_unfamiliar_export_benchmark_330h",
        "source_page": _norm_text(row_context.get("source_page")),
        "row_text": _norm_text(row_context.get("row_text") or candidate.get("row_text")),
        "table_id": _norm_text(candidate.get("extracted_table_id")),
    }
    payload["candidate_id"] = _stable_candidate_id(payload)
    return payload


def inspect_full_unfamiliar_candidate_export(unfamiliar_input_dir: Path) -> Dict[str, Any]:
    pdf_paths = sorted(unfamiliar_input_dir.glob("*.pdf"))
    per_pdf_rows: List[Dict[str, Any]] = []
    prepared_rows: List[Dict[str, Any]] = []

    for pdf in pdf_paths:
        try:
            blocks = extract_pdfplumber_table_blocks(str(pdf), {}, logger=None)
            row_text_rows = _row_text_rows_from_blocks(pdf, blocks)
            cleaned = clean_row_texts(row_text_rows)
            repaired = repair_row_fragments(cleaned["cleaned_rows"], expected_year_count=5)
            extracted = extract_metric_candidates_from_repaired_rows(repaired["repaired_rows"], expected_year_count=5)
            context_map = _candidate_context_map(repaired["repaired_rows"])
            table_context_map = _table_context_rows(row_text_rows)

            pdf_prepared_rows: List[Dict[str, Any]] = []
            for candidate in extracted.get("metric_candidate_preview", []):
                key = (_norm_text(candidate.get("extracted_table_id")), _norm_text(candidate.get("row_index")))
                row_context = context_map.get(
                    key,
                    {
                        "source_page": "",
                        "row_text": _norm_text(candidate.get("row_text")),
                        "source_file": _norm_text(candidate.get("source_file")),
                    },
                )
                pdf_prepared_rows.append(
                    _prepared_row_from_candidate_330h(
                        candidate,
                        row_context=row_context,
                        table_context_rows=table_context_map.get(_norm_text(candidate.get("extracted_table_id")), []),
                    )
                )

            prepared_rows.extend(pdf_prepared_rows)
            status = "processed" if pdf_prepared_rows else "no_candidates"
            per_pdf_rows.append(
                {
                    "source_pdf": pdf.name,
                    "processing_status": status,
                    "block_count": int(len(blocks)),
                    "row_text_row_count": int(len(row_text_rows)),
                    "cleaned_row_count": int(len(cleaned["cleaned_rows"])),
                    "repaired_row_count": int(len(repaired["repaired_rows"])),
                    "matched_metric_row_count": int(extracted.get("matched_metric_row_count", 0)),
                    "candidate_row_count": int(len(pdf_prepared_rows)),
                    "error_message": "",
                }
            )
        except Exception as exc:
            per_pdf_rows.append(
                {
                    "source_pdf": pdf.name,
                    "processing_status": "failed",
                    "block_count": -1,
                    "row_text_row_count": 0,
                    "cleaned_row_count": 0,
                    "repaired_row_count": 0,
                    "matched_metric_row_count": 0,
                    "candidate_row_count": 0,
                    "error_message": f"{type(exc).__name__}: {exc}",
                }
            )

    prepared_df = _frame_for_output(pd.DataFrame(prepared_rows, columns=REQUIRED_FIELDS))
    per_pdf_df = _frame_for_output(pd.DataFrame(per_pdf_rows))
    return {
        "pdf_paths": pdf_paths,
        "per_pdf_df": per_pdf_df,
        "prepared_df": prepared_df,
    }


def _write_prepared_outputs(prepared_output_dir: Path, prepared_df: pd.DataFrame, per_pdf_df: pd.DataFrame) -> Dict[str, str]:
    prepared_output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = prepared_output_dir / "unfamiliar_candidate_rows.jsonl"
    xlsx_path = prepared_output_dir / "unfamiliar_candidate_rows.xlsx"
    manifest_path = prepared_output_dir / "unfamiliar_candidate_manifest.json"
    compat_jsonl_path = prepared_output_dir / f"{COMPATIBILITY_ARTIFACT_STEM}.jsonl"
    compat_xlsx_path = prepared_output_dir / f"{COMPATIBILITY_ARTIFACT_STEM}.xlsx"

    prepared_rows = prepared_df.to_dict(orient="records")
    compatibility_rows = [_compatibility_row_from_prepared(row) for row in prepared_rows]

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in prepared_rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    with compat_jsonl_path.open("w", encoding="utf-8") as handle:
        for row in compatibility_rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        prepared_df.to_excel(writer, sheet_name="unfamiliar_candidate_rows", index=False)
        pd.DataFrame(
            [{"field_name": key, "missing_count": value} for key, value in _missing_field_counts(prepared_df).items()]
        ).to_excel(writer, sheet_name="missing_field_counts", index=False)
        per_pdf_df.to_excel(writer, sheet_name="per_pdf_summary", index=False)

    with pd.ExcelWriter(compat_xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame(compatibility_rows).to_excel(writer, sheet_name="affected_candidates", index=False)

    return {
        "jsonl_path": str(jsonl_path),
        "xlsx_path": str(xlsx_path),
        "manifest_path": str(manifest_path),
        "compat_jsonl_path": str(compat_jsonl_path),
        "compat_xlsx_path": str(compat_xlsx_path),
    }


def _rerun_330f(
    *,
    prepared_output_dir: Path,
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

    deduped_summary_path = deduped_candidate_benchmark_dir / "deduped_candidate_trust_benchmark_330e_summary.json"
    deduped_qa_path = deduped_candidate_benchmark_dir / "deduped_candidate_trust_benchmark_330e_qa.json"
    trust_scoring_summary_path = trust_scoring_dir / "trust_engine_scoring_330b_summary.json"

    artifacts = build_unfamiliar_pdf_trust_benchmark_330f(
        deduped_candidate_summary=_read_json(deduped_summary_path),
        deduped_candidate_qa=_read_json(deduped_qa_path),
        trust_scoring_summary=_read_json(trust_scoring_summary_path),
        unfamiliar_source_dirs=[prepared_output_dir],
        output_dir=rerun_output_dir,
        alias_asset_path=alias_asset_path,
        scope_asset_path=scope_asset_path,
        files_read=[
            str(deduped_summary_path),
            str(deduped_qa_path),
            str(trust_scoring_summary_path),
            str(prepared_output_dir),
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
    report_md.write_text(unfamiliar_pdf_trust_benchmark_330f_markdown(artifacts["summary"]), encoding="utf-8")
    with scored_jsonl.open("w", encoding="utf-8") as handle:
        for row in artifacts["artifact_row_view_df"].to_dict(orient="records"):
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    return artifacts


def build_full_unfamiliar_export_benchmark_330h(
    *,
    unfamiliar_input_dir: Path,
    previous_delivery_report_dir: Path,
    prepared_output_dir: Path,
    output_dir: Path,
    deduped_candidate_benchmark_dir: Path,
    trust_scoring_dir: Path,
    rerun_330f: bool,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    previous_summary_path = previous_delivery_report_dir / "end_to_end_delivery_quality_report_330g_summary.json"
    previous_summary = _read_json(previous_summary_path)
    qa_rows = validate_330g_summary(previous_summary)

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }

    inspection = inspect_full_unfamiliar_candidate_export(unfamiliar_input_dir)
    pdf_paths = inspection["pdf_paths"]
    per_pdf_df = inspection["per_pdf_df"]
    prepared_df = inspection["prepared_df"]

    missing_field_counts = _missing_field_counts(prepared_df)
    per_pdf_rows = per_pdf_df.to_dict(orient="records") if not per_pdf_df.empty else []
    pdf_names = [path.name for path in pdf_paths]
    processed_pdf_count = int(sum(1 for row in per_pdf_rows if row.get("processing_status") in {"processed", "no_candidates"}))
    failed_pdf_count = int(sum(1 for row in per_pdf_rows if row.get("processing_status") == "failed"))
    no_candidate_pdf_count = int(sum(1 for row in per_pdf_rows if row.get("processing_status") == "no_candidates"))
    pdf_with_candidate_count = int(sum(1 for row in per_pdf_rows if row.get("processing_status") == "processed"))
    prepared_candidate_row_count = int(len(prepared_df))
    true_source_pdf_names = set(prepared_df["source_pdf"].astype(str).tolist()) if not prepared_df.empty else set()
    source_pdf_preserved = bool(true_source_pdf_names) and all(name in pdf_names for name in true_source_pdf_names) and "" not in true_source_pdf_names

    add_qa("inputs::unfamiliar_pdf_count", len(pdf_paths) == 13, str(len(pdf_paths)))
    add_qa("records::processed_pdf_count", processed_pdf_count >= 3, str(processed_pdf_count))
    add_qa("records::pdf_with_candidate_count", pdf_with_candidate_count >= 1, str(pdf_with_candidate_count))
    add_qa("records::prepared_candidate_row_count", prepared_candidate_row_count > 0, str(prepared_candidate_row_count))
    add_qa("quality::source_pdf_preserved", source_pdf_preserved, json.dumps(sorted(true_source_pdf_names), ensure_ascii=False))

    written_paths: Dict[str, str] = {}
    manifest: Dict[str, Any] = {
        "stage": "330H",
        "unfamiliar_pdf_count": len(pdf_paths),
        "unfamiliar_pdf_list": pdf_names,
        "processed_pdf_count": processed_pdf_count,
        "failed_pdf_count": failed_pdf_count,
        "no_candidate_pdf_count": no_candidate_pdf_count,
        "pdf_with_candidate_count": pdf_with_candidate_count,
        "prepared_candidate_row_count": prepared_candidate_row_count,
        "required_fields": list(REQUIRED_FIELDS),
        "missing_field_count_by_field": missing_field_counts,
        "extraction_export_approach_used": "pdfplumber_table_blocks_plus_existing_row_text_candidate_extractors",
        "source_pdf_preserved": source_pdf_preserved,
    }
    can_rerun_330f = prepared_candidate_row_count > 0
    if prepared_candidate_row_count > 0:
        written_paths = _write_prepared_outputs(prepared_output_dir, prepared_df, per_pdf_df)
        manifest.update(written_paths)
        Path(written_paths["manifest_path"]).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    rerun_artifacts: Dict[str, Any] | None = None
    rerun_summary: Dict[str, Any] = {}
    rerun_output_dir = output_dir / "rerun_330f"
    if rerun_330f and can_rerun_330f:
        rerun_artifacts = _rerun_330f(
            prepared_output_dir=prepared_output_dir,
            rerun_output_dir=rerun_output_dir,
            deduped_candidate_benchmark_dir=deduped_candidate_benchmark_dir,
            trust_scoring_dir=trust_scoring_dir,
            alias_asset_path=alias_asset_path,
            scope_asset_path=scope_asset_path,
        )
        rerun_summary = rerun_artifacts["summary"]
        add_qa("rerun::330f_unfamiliar_source_status", _norm_text(rerun_summary.get("unfamiliar_source_status")) == "loaded", _norm_text(rerun_summary.get("unfamiliar_source_status")))
        add_qa("rerun::330f_scored_unfamiliar_record_count", _safe_int(rerun_summary.get("scored_unfamiliar_record_count"), 0) > 0, str(rerun_summary.get("scored_unfamiliar_record_count", "")))
        add_qa("rerun::330f_decision", _norm_text(rerun_summary.get("decision")) == READY_330F_DECISION, _norm_text(rerun_summary.get("decision")))

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    no_official_asset_modification_during_330h = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330h",
        no_official_asset_modification_during_330h,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    validated_330g_delivery_report = all(row["status"] == "PASS" for row in validate_330g_summary(previous_summary))
    reran_330f_successfully = bool(rerun_summary) and _norm_text(rerun_summary.get("decision")) == READY_330F_DECISION and _safe_int(rerun_summary.get("scored_unfamiliar_record_count"), 0) > 0
    decision = READY_DECISION if prepared_candidate_row_count > 0 and qa_fail_count == 0 and ((not rerun_330f) or reran_330f_successfully) else NOT_READY_DECISION

    summary = {
        "stage": "330H",
        "output_dir": str(output_dir),
        "prepared_output_dir": str(prepared_output_dir),
        "validated_330g_delivery_report": validated_330g_delivery_report,
        "unfamiliar_pdf_count": len(pdf_paths),
        "unfamiliar_pdf_list": pdf_names,
        "processed_pdf_count": processed_pdf_count,
        "failed_pdf_count": failed_pdf_count,
        "no_candidate_pdf_count": no_candidate_pdf_count,
        "pdf_with_candidate_count": pdf_with_candidate_count,
        "prepared_candidate_row_count": prepared_candidate_row_count,
        "missing_required_field_count_by_field": missing_field_counts,
        "extraction_export_approach_used": "pdfplumber_table_blocks_plus_existing_row_text_candidate_extractors",
        "can_rerun_330f": can_rerun_330f,
        "source_pdf_preserved": source_pdf_preserved,
        "unit_missing_count": _safe_int(missing_field_counts.get("unit"), 0),
        "source_page_missing_count": _safe_int(missing_field_counts.get("source_page"), 0),
        "reran_330f": rerun_330f and can_rerun_330f,
        "rerun_330f_output_dir": str(rerun_output_dir) if rerun_330f and can_rerun_330f else "",
        "330f_unfamiliar_source_status": _norm_text(rerun_summary.get("unfamiliar_source_status")),
        "330f_scored_unfamiliar_record_count": _safe_int(rerun_summary.get("scored_unfamiliar_record_count"), 0),
        "330f_decision": _norm_text(rerun_summary.get("decision")),
        "330f_sidecar_trusted_suggestion_count": _safe_int(rerun_summary.get("sidecar_trusted_suggestion_count"), 0),
        "330f_sidecar_review_required_suggestion_count": _safe_int(rerun_summary.get("sidecar_review_required_suggestion_count"), 0),
        "recommended_next_step": "330I_SOURCE_ATTRIBUTION_AND_UNIT_SIGNAL_FIX",
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330h": no_official_asset_modification_during_330h,
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
        stage="330H",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    missing_field_counts_df = _frame_for_output(
        pd.DataFrame([{"field_name": key, "missing_count": value} for key, value in missing_field_counts.items()])
    )
    rerun_summary_df = _frame_for_output(pd.DataFrame([rerun_summary])) if rerun_summary else pd.DataFrame()
    official_asset_proof_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "asset_path": asset_path,
                    "hash_before": before_hash,
                    "hash_after": official_assets_after.get(asset_path, ""),
                    "modified_during_330h": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    pdf_list_df = _frame_for_output(pd.DataFrame([{"source_pdf": name} for name in pdf_names]))
    prepared_manifest_df = _frame_for_output(pd.DataFrame([manifest])) if manifest else pd.DataFrame()

    return {
        "summary": summary,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "manifest_json": manifest,
        "summary_df": _frame_for_output(pd.DataFrame([summary])),
        "qa_summary_df": _frame_for_output(pd.DataFrame([{"qa_pass_count": qa_pass_count, "qa_fail_count": qa_fail_count, "decision": decision}])),
        "qa_checks_df": qa_df,
        "per_pdf_df": per_pdf_df,
        "prepared_df": prepared_df,
        "missing_field_counts_df": missing_field_counts_df,
        "pdf_list_df": pdf_list_df,
        "prepared_manifest_df": prepared_manifest_df,
        "rerun_330f_summary_df": rerun_summary_df,
        "official_asset_proof_df": official_asset_proof_df,
    }
