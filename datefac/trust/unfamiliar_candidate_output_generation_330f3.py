from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.cached_candidate_benchmark_330c import load_cached_candidate_like_rows
from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.unfamiliar_output_preparation_330f2 import (
    WAITING_DECISION as PREVIOUS_WAITING_DECISION,
    WAITING_FOR_PARSER_OUTPUTS,
    discover_matching_cached_outputs,
    discover_unfamiliar_inputs,
)


READY_DECISION = "UNFAMILIAR_CANDIDATE_OUTPUT_GENERATION_330F3_READY_FOR_330F_RERUN"
WAITING_DECISION = "UNFAMILIAR_CANDIDATE_OUTPUT_GENERATION_330F3_WAITING_FOR_SAFE_EXPORT_PATH"
NOT_READY_DECISION = "UNFAMILIAR_CANDIDATE_OUTPUT_GENERATION_330F3_NOT_READY"

DEFAULT_UNFAMILIAR_INPUT_DIR = Path(r"D:\_datefac\input\unfamiliar")
DEFAULT_PREVIOUS_PREPARATION_DIR = Path(r"D:\_datefac\output\unfamiliar_output_preparation_330f2")
DEFAULT_PREPARED_OUTPUT_DIR = Path(r"D:\_datefac\output\unfamiliar_trust_split")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\unfamiliar_candidate_output_generation_330f3")
DEFAULT_OUTPUT_DISCOVERY_ROOT = Path(r"D:\_datefac\output")

REQUIRED_FIELDS = [
    "candidate_id",
    "metric_label_raw",
    "normalized_metric",
    "value",
    "unit",
    "year",
    "parser_sources",
    "evidence_refs",
    "risk_flags",
    "existing_status",
    "source_pdf",
    "source_artifact",
    "source_page",
    "row_text",
    "table_id",
]

SAFE_EXPORT_PATH_NOTES = [
    {
        "candidate_path": "A",
        "status": "preferred_cached_output_reuse",
        "detail": "Reuse exact unfamiliar-PDF cached candidate artifacts if they already exist under output/.",
    },
    {
        "candidate_path": "B",
        "status": "existing_lightweight_export_path_not_auto_run",
        "detail": (
            "Repository contains export/ingestion helpers, but no exact unfamiliar-PDF cached outputs were discovered "
            "and no generic no-risk exporter was confirmed for auto-execution here."
        ),
    },
    {
        "candidate_path": "C",
        "status": "waiting_without_fabrication",
        "detail": "If no exact cached outputs exist and no approved safe exporter is available, emit a waiting report only.",
    },
]


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_json_loads(value: Any) -> Dict[str, Any]:
    text = _norm_text(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


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
    ordered: List[str] = []
    seen = set()
    for item in items:
        token = _norm_text(item)
        if token and token not in seen:
            ordered.append(token)
            seen.add(token)
    return ordered


def _frame_for_output(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _source_pdf_name(row: Mapping[str, Any]) -> str:
    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        upstream = provenance.get("upstream_provenance")
        if isinstance(upstream, dict):
            for key in ["source_report_name", "source_doc_name", "content_source_file"]:
                value = _norm_text(upstream.get(key))
                if value:
                    return Path(value).name
        source_artifact_path = _norm_text(provenance.get("source_artifact_path"))
        if source_artifact_path:
            return Path(source_artifact_path).stem
    for key in ["source_pdf", "source_pdf_name", "source_report_name", "source_doc_name"]:
        value = _norm_text(row.get(key))
        if value:
            return Path(value).name
    return ""


def _row_text_from_row(row: Mapping[str, Any]) -> str:
    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        upstream = provenance.get("upstream_provenance")
        if isinstance(upstream, dict):
            for key in ["source_row_text", "row_text", "row_label"]:
                value = _norm_text(upstream.get(key))
                if value:
                    return value
    for key in ["source_row_text", "row_text", "metric_label_raw"]:
        value = _norm_text(row.get(key))
        if value:
            return value
    return ""


def _prepared_candidate_id(row: Mapping[str, Any]) -> str:
    digest = hashlib.sha1(
        json.dumps(
            {
                "source_pdf": _norm_text(row.get("source_pdf")),
                "source_artifact": _norm_text(row.get("source_artifact")),
                "source_page": _norm_text(row.get("source_page")),
                "table_id": _norm_text(row.get("table_id")),
                "metric_label_raw": _norm_text(row.get("metric_label_raw")),
                "normalized_metric": _norm_text(row.get("normalized_metric")),
                "value": row.get("value"),
                "unit": _norm_text(row.get("unit")),
                "year": _norm_text(row.get("year")),
                "row_text": _norm_text(row.get("row_text")),
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    return f"330f3::{digest[:20]}"


def validate_previous_preparation_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add(
        "readiness::330f2_decision",
        _norm_text(summary.get("decision")) == PREVIOUS_WAITING_DECISION,
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330f2_status",
        _norm_text(summary.get("unfamiliar_output_preparation_status")) == WAITING_FOR_PARSER_OUTPUTS,
        _norm_text(summary.get("unfamiliar_output_preparation_status")),
    )
    add(
        "readiness::330f2_discovered_unfamiliar_input_pdf_count",
        _safe_int(summary.get("discovered_unfamiliar_input_pdf_count"), -1) == 13,
        str(summary.get("discovered_unfamiliar_input_pdf_count", "")),
    )
    add(
        "readiness::330f2_matched_cached_output_count",
        _safe_int(summary.get("matched_cached_output_count"), -1) == 0,
        str(summary.get("matched_cached_output_count", "")),
    )
    add(
        "readiness::330f2_prepared_candidate_row_count",
        _safe_int(summary.get("prepared_candidate_row_count"), -1) == 0,
        str(summary.get("prepared_candidate_row_count", "")),
    )
    add(
        "readiness::330f2_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    return checks


def discover_exact_candidate_source_dirs(
    unfamiliar_inputs_df: pd.DataFrame,
    output_root: Path,
) -> tuple[pd.DataFrame, List[Path]]:
    output_matches_df = discover_matching_cached_outputs(unfamiliar_inputs_df, output_root)
    if output_matches_df.empty:
        return _frame_for_output(output_matches_df), []

    candidate_dirs: List[Path] = []
    seen = set()
    for row in output_matches_df.to_dict(orient="records"):
        raw_path = _norm_text(row.get("matched_path"))
        if not raw_path:
            continue
        path = Path(raw_path)
        candidate_dir = path if path.is_dir() else path.parent
        resolved = str(candidate_dir.resolve())
        if resolved not in seen:
            candidate_dirs.append(candidate_dir)
            seen.add(resolved)
    return _frame_for_output(output_matches_df), candidate_dirs


def filter_rows_for_unfamiliar_pdfs(
    rows: Sequence[Mapping[str, Any]],
    unfamiliar_pdf_names: Iterable[str],
) -> List[Dict[str, Any]]:
    allowed = {name.lower() for name in unfamiliar_pdf_names}
    filtered: List[Dict[str, Any]] = []
    for row in rows:
        source_pdf = _source_pdf_name(row)
        if source_pdf.lower() in allowed:
            filtered.append(dict(row))
    return filtered


def convert_to_prepared_rows(rows: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    prepared_rows: List[Dict[str, Any]] = []
    for row in rows:
        parser_sources = _listify_tokens(row.get("parser_sources"))
        evidence_refs = _listify_tokens(row.get("evidence_refs"))
        risk_flags = _listify_tokens(row.get("risk_flags"))
        prepared = {
            "candidate_id": "",
            "metric_label_raw": _norm_text(row.get("metric_label_raw")),
            "normalized_metric": _norm_text(row.get("normalized_metric")),
            "value": row.get("value"),
            "unit": _norm_text(row.get("unit")),
            "year": _norm_text(row.get("year")),
            "parser_sources": parser_sources,
            "evidence_refs": evidence_refs,
            "risk_flags": risk_flags,
            "existing_status": _norm_text(row.get("existing_status")),
            "source_pdf": _source_pdf_name(row),
            "source_artifact": _norm_text(row.get("source_artifact")),
            "source_page": _norm_text(row.get("source_page")),
            "row_text": _row_text_from_row(row),
            "table_id": _norm_text(row.get("source_table")),
        }
        prepared["candidate_id"] = _prepared_candidate_id(prepared)
        prepared_rows.append(prepared)
    frame = pd.DataFrame(prepared_rows, columns=REQUIRED_FIELDS)
    return _frame_for_output(frame)


def missing_field_counts(frame: pd.DataFrame) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    if frame.empty:
        return {field: 0 for field in REQUIRED_FIELDS}
    for field in REQUIRED_FIELDS:
        missing = 0
        for value in frame[field].tolist():
            if isinstance(value, list):
                if len(value) == 0:
                    missing += 1
            elif value in ("", None):
                missing += 1
            elif isinstance(value, float) and pd.isna(value):
                missing += 1
        counts[field] = int(missing)
    return counts


def build_prepared_manifest(
    *,
    prepared_output_dir: Path,
    prepared_rows_df: pd.DataFrame,
    processed_pdf_count: int,
    unfamiliar_pdf_count: int,
    output_matches_df: pd.DataFrame,
) -> Dict[str, Any]:
    return {
        "stage": "330F3",
        "prepared_output_dir": str(prepared_output_dir),
        "prepared_candidate_row_count": int(len(prepared_rows_df)),
        "processed_pdf_count": int(processed_pdf_count),
        "unfamiliar_pdf_count": int(unfamiliar_pdf_count),
        "source_match_count": int(len(output_matches_df)),
        "required_fields": list(REQUIRED_FIELDS),
        "missing_field_counts": missing_field_counts(prepared_rows_df),
        "prepared_jsonl": str(prepared_output_dir / "unfamiliar_candidate_rows.jsonl"),
        "prepared_xlsx": str(prepared_output_dir / "unfamiliar_candidate_rows.xlsx"),
        "prepared_manifest_json": str(prepared_output_dir / "unfamiliar_candidate_manifest.json"),
    }


def _write_prepared_outputs(
    prepared_output_dir: Path,
    prepared_rows_df: pd.DataFrame,
    manifest: Mapping[str, Any],
) -> None:
    prepared_output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = prepared_output_dir / "unfamiliar_candidate_rows.jsonl"
    xlsx_path = prepared_output_dir / "unfamiliar_candidate_rows.xlsx"
    manifest_path = prepared_output_dir / "unfamiliar_candidate_manifest.json"

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in prepared_rows_df.to_dict(orient="records"):
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        prepared_rows_df.to_excel(writer, sheet_name="unfamiliar_candidate_rows", index=False)
        pd.DataFrame(
            [{"field_name": key, "missing_count": value} for key, value in missing_field_counts(prepared_rows_df).items()]
        ).to_excel(writer, sheet_name="missing_field_counts", index=False)

    manifest_path.write_text(json.dumps(dict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")


def build_unfamiliar_candidate_output_generation_330f3(
    *,
    previous_preparation_summary: Mapping[str, Any],
    unfamiliar_input_dir: Path,
    output_discovery_root: Path,
    prepared_output_dir: Path,
    output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    qa_rows = validate_previous_preparation_summary(previous_preparation_summary)

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    unfamiliar_inputs_df = discover_unfamiliar_inputs(unfamiliar_input_dir)
    unfamiliar_pdf_names = unfamiliar_inputs_df["pdf_name"].astype(str).tolist() if not unfamiliar_inputs_df.empty else []
    output_matches_df, candidate_source_dirs = discover_exact_candidate_source_dirs(
        unfamiliar_inputs_df,
        output_discovery_root,
    )

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }

    matched_candidate_artifacts_df = pd.DataFrame(
        columns=["source_dir_name", "artifact_name", "artifact_kind", "discovery_reason", "sheet_names", "loaded_record_count"]
    )
    filtered_rows: List[Dict[str, Any]] = []
    prepared_rows_df = pd.DataFrame(columns=REQUIRED_FIELDS)
    processed_pdf_count = 0
    generation_export_approach_used = "C"

    if candidate_source_dirs:
        loaded_rows, matched_candidate_artifacts_df = load_cached_candidate_like_rows(candidate_source_dirs)
        filtered_rows = filter_rows_for_unfamiliar_pdfs(loaded_rows, unfamiliar_pdf_names)
        prepared_rows_df = convert_to_prepared_rows(filtered_rows)
        processed_pdf_count = int(prepared_rows_df["source_pdf"].astype(str).nunique()) if not prepared_rows_df.empty else 0
        if not prepared_rows_df.empty:
            generation_export_approach_used = "A"

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    no_official_asset_modification_during_330f3 = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330f3",
        no_official_asset_modification_during_330f3,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )
    add_qa(
        "inputs::unfamiliar_pdf_count",
        len(unfamiliar_inputs_df) == 13,
        str(len(unfamiliar_inputs_df)),
    )

    if generation_export_approach_used == "A":
        manifest = build_prepared_manifest(
            prepared_output_dir=prepared_output_dir,
            prepared_rows_df=prepared_rows_df,
            processed_pdf_count=processed_pdf_count,
            unfamiliar_pdf_count=len(unfamiliar_inputs_df),
            output_matches_df=output_matches_df,
        )
        _write_prepared_outputs(prepared_output_dir, prepared_rows_df, manifest)
    else:
        manifest = {
            "stage": "330F3",
            "prepared_output_dir": str(prepared_output_dir),
            "prepared_candidate_row_count": 0,
            "processed_pdf_count": 0,
            "unfamiliar_pdf_count": int(len(unfamiliar_inputs_df)),
            "source_match_count": int(len(output_matches_df)),
            "required_fields": list(REQUIRED_FIELDS),
            "missing_field_counts": {field: 0 for field in REQUIRED_FIELDS},
        }

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    can_rerun_330f = generation_export_approach_used == "A" and not prepared_rows_df.empty and qa_fail_count == 0
    decision = READY_DECISION if can_rerun_330f else WAITING_DECISION
    if qa_fail_count > 0:
        decision = NOT_READY_DECISION

    summary = {
        "stage": "330F3",
        "output_dir": str(output_dir),
        "prepared_output_dir": str(prepared_output_dir),
        "validated_330f2_waiting_for_parser_outputs": qa_fail_count == 0 and all(
            row.get("status") == "PASS" for row in qa_rows if _norm_text(row.get("check_name")).startswith("readiness::330f2_")
        ),
        "unfamiliar_pdf_count": int(len(unfamiliar_inputs_df)),
        "processed_pdf_count": int(processed_pdf_count),
        "prepared_candidate_row_count": int(len(prepared_rows_df)),
        "existing_output_match_count": int(len(output_matches_df)),
        "matched_candidate_artifact_count": int(len(matched_candidate_artifacts_df)),
        "generation_export_approach_used": generation_export_approach_used,
        "can_rerun_330f": can_rerun_330f,
        "output_dir_for_330f": str(prepared_output_dir),
        "recommended_330f_rerun_command": (
            "python tools\\run_unfamiliar_pdf_trust_benchmark_330f.py --deduped-candidate-benchmark-dir "
            "D:\\_datefac\\output\\deduped_candidate_trust_benchmark_330e --trust-scoring-dir "
            "D:\\_datefac\\output\\trust_engine_scoring_330b --unfamiliar-source-dir "
            "D:\\_datefac\\output\\unfamiliar_trust_split --output-dir "
            "D:\\_datefac\\output\\unfamiliar_pdf_trust_benchmark_330f"
        ),
        "missing_field_counts": manifest.get("missing_field_counts", {}),
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330f3": no_official_asset_modification_during_330f3,
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
        stage="330F3",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    summary_df = _frame_for_output(pd.DataFrame([summary]))
    qa_summary_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "qa_pass_count": qa_pass_count,
                    "qa_fail_count": qa_fail_count,
                    "blocking_reasons": " | ".join(blocking_reasons),
                    "decision": decision,
                }
            ]
        )
    )
    missing_field_counts_df = _frame_for_output(
        pd.DataFrame(
            [{"field_name": key, "missing_count": value} for key, value in summary["missing_field_counts"].items()]
        )
    )
    official_asset_proof_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "asset_path": asset_path,
                    "hash_before": before_hash,
                    "hash_after": official_assets_after.get(asset_path, ""),
                    "modified_during_330f3": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    known_limitations_df = _frame_for_output(pd.DataFrame(SAFE_EXPORT_PATH_NOTES))

    return {
        "summary": summary,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "prepared_manifest_json": manifest,
        "summary_df": summary_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "unfamiliar_inputs_df": _frame_for_output(unfamiliar_inputs_df),
        "output_matches_df": _frame_for_output(output_matches_df),
        "matched_candidate_artifacts_df": _frame_for_output(matched_candidate_artifacts_df),
        "prepared_candidate_rows_df": _frame_for_output(prepared_rows_df),
        "missing_field_counts_df": missing_field_counts_df,
        "official_asset_proof_df": official_asset_proof_df,
        "known_limitations_df": known_limitations_df,
    }
