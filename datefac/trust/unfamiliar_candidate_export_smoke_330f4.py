from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import pandas as pd

from extractor_adapter import extract_pdfplumber_table_blocks
from datefac.extraction.row_text_cleaner import clean_row_texts
from datefac.extraction.row_text_metric_extractor import extract_metric_candidates_from_repaired_rows
from datefac.extraction.row_text_repair import repair_row_fragments
from datefac.trust.no_apply_proof import build_no_apply_proof
from datefac.trust.unfamiliar_candidate_output_generation_330f3 import (
    REQUIRED_FIELDS,
    DEFAULT_UNFAMILIAR_INPUT_DIR,
    _frame_for_output,
    _norm_text,
    _safe_int,
)


READY_DECISION = "UNFAMILIAR_CANDIDATE_EXPORT_SMOKE_330F4_READY_FOR_330F_RERUN"
WAITING_DECISION = "UNFAMILIAR_CANDIDATE_EXPORT_SMOKE_330F4_WAITING_FOR_SAFE_LOCAL_PARSER_PATH"
NOT_READY_DECISION = "UNFAMILIAR_CANDIDATE_EXPORT_SMOKE_330F4_NOT_READY"

DEFAULT_PREPARED_OUTPUT_DIR = Path(r"D:\_datefac\output\unfamiliar_trust_split")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\unfamiliar_candidate_export_smoke_330f4")
DEFAULT_PREVIOUS_330F3_DIR = Path(r"D:\_datefac\output\unfamiliar_candidate_output_generation_330f3")
DEFAULT_SELECT_COUNT = 3
COMPATIBILITY_ARTIFACT_STEM = "unfamiliar_smoke_330f4_affected_candidates"


def _listify_tokens(value: Any) -> List[str]:
    if value in ("", None):
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    else:
        items = [token for token in str(value).replace("|", ",").replace(";", ",").split(",")]
    out: List[str] = []
    seen = set()
    for item in items:
        token = _norm_text(item)
        if token and token not in seen:
            out.append(token)
            seen.add(token)
    return out


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


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
    return f"330f4::{digest[:20]}"


def _row_text_rows_from_blocks(pdf: Path, blocks: Sequence[Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for block in blocks:
        df = block.raw_df if isinstance(getattr(block, "raw_df", None), pd.DataFrame) else pd.DataFrame()
        if df.empty:
            continue
        page = _norm_text(getattr(block, "page", ""))
        table_index = _norm_text(getattr(block, "table_index", ""))
        table_id = f"{pdf.stem}|p{page or 'NA'}|t{table_index or 'NA'}|pdfplumber"
        for row_index in range(df.shape[0]):
            values = [_norm_text(df.iat[row_index, c]) for c in range(df.shape[1])]
            row_text = " | ".join([v for v in values if v])
            if not row_text:
                continue
            rows.append(
                {
                    "source_file": pdf.name,
                    "source_doc_name": pdf.name,
                    "extracted_table_id": table_id,
                    "row_index": row_index + 1,
                    "row_text": row_text,
                    "source_page": page,
                    "source_artifact": "pdfplumber_smoke_330f4",
                }
            )
    return rows


def _prepared_row_from_candidate(candidate: Mapping[str, Any], source_page: str) -> Dict[str, Any]:
    risk_flags = _listify_tokens(candidate.get("risk_tags"))
    payload = {
        "candidate_id": "",
        "metric_label_raw": _norm_text(candidate.get("raw_metric_name")),
        "normalized_metric": _norm_text(candidate.get("metric_code")),
        "value": _norm_text(candidate.get("normalized_value") or candidate.get("raw_value")),
        "unit": _norm_text(candidate.get("raw_unit")),
        "year": _norm_text(candidate.get("year")),
        "parser_sources": ["pdfplumber", "row_text_smoke_330f4"],
        "evidence_refs": [
            f"table_id={_norm_text(candidate.get('extracted_table_id'))}",
            f"row_index={_norm_text(candidate.get('row_index'))}",
        ],
        "risk_flags": risk_flags,
        "existing_status": "REVIEW_REQUIRED",
        "source_pdf": _norm_text(candidate.get("source_file")),
        "source_artifact": "unfamiliar_candidate_export_smoke_330f4",
        "source_page": _norm_text(source_page),
        "row_text": _norm_text(candidate.get("row_text")),
        "table_id": _norm_text(candidate.get("extracted_table_id")),
    }
    payload["candidate_id"] = _stable_candidate_id(payload)
    return payload


def _compatibility_row_from_prepared(prepared: Mapping[str, Any]) -> Dict[str, Any]:
    source_pdf = _norm_text(prepared.get("source_pdf"))
    source_page = _norm_text(prepared.get("source_page"))
    table_id = _norm_text(prepared.get("table_id"))
    row_text = _norm_text(prepared.get("row_text"))
    evidence_refs = prepared.get("evidence_refs", [])
    risk_flags = prepared.get("risk_flags", [])
    parser_sources = prepared.get("parser_sources", [])
    provenance = {
        "source_report_name": source_pdf,
        "source_page": source_page,
        "table_asset_id": table_id,
        "source_row_text": row_text,
    }
    return {
        "candidate_id": _norm_text(prepared.get("candidate_id")),
        "metric_label_raw": _norm_text(prepared.get("metric_label_raw")),
        "normalized_metric": _norm_text(prepared.get("normalized_metric")),
        "value": prepared.get("value"),
        "unit": _norm_text(prepared.get("unit")),
        "year": _norm_text(prepared.get("year")),
        "parser_sources": list(parser_sources) if isinstance(parser_sources, list) else _listify_tokens(parser_sources),
        "evidence_refs": list(evidence_refs) if isinstance(evidence_refs, list) else _listify_tokens(evidence_refs),
        "risk_flags": list(risk_flags) if isinstance(risk_flags, list) else _listify_tokens(risk_flags),
        "existing_status": _norm_text(prepared.get("existing_status")),
        "source_file": source_pdf,
        "source_page": source_page,
        "source_table_id": table_id,
        "source_row_text": row_text,
        "provenance_json": json.dumps(provenance, ensure_ascii=False),
    }


def _missing_field_counts(frame: pd.DataFrame) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    if frame.empty:
        return {field: 0 for field in REQUIRED_FIELDS}
    for field in REQUIRED_FIELDS:
        missing = 0
        for value in frame[field].tolist():
            if isinstance(value, list):
                if not value:
                    missing += 1
            elif value in ("", None):
                missing += 1
        counts[field] = int(missing)
    return counts


def validate_330f3_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    add(
        "readiness::330f3_decision",
        _norm_text(summary.get("decision")) == "UNFAMILIAR_CANDIDATE_OUTPUT_GENERATION_330F3_WAITING_FOR_SAFE_EXPORT_PATH",
        _norm_text(summary.get("decision")),
    )
    add(
        "readiness::330f3_unfamiliar_pdf_count",
        _safe_int(summary.get("unfamiliar_pdf_count"), -1) == 13,
        str(summary.get("unfamiliar_pdf_count", "")),
    )
    add(
        "readiness::330f3_prepared_candidate_row_count",
        _safe_int(summary.get("prepared_candidate_row_count"), -1) == 0,
        str(summary.get("prepared_candidate_row_count", "")),
    )
    add(
        "readiness::330f3_qa_fail_count",
        _safe_int(summary.get("qa_fail_count"), 1) == 0,
        str(summary.get("qa_fail_count", "")),
    )
    return checks


def inspect_smoke_candidate_export(
    unfamiliar_input_dir: Path,
    *,
    select_count: int = DEFAULT_SELECT_COUNT,
) -> Dict[str, Any]:
    scan_rows: List[Dict[str, Any]] = []
    pdf_paths = sorted(unfamiliar_input_dir.glob("*.pdf"))
    for pdf in pdf_paths:
        try:
            blocks = extract_pdfplumber_table_blocks(str(pdf), {}, logger=None)
        except Exception as exc:
            scan_rows.append(
                {
                    "source_pdf": pdf.name,
                    "block_count": -1,
                    "row_text_row_count": 0,
                    "cleaned_row_count": 0,
                    "repaired_row_count": 0,
                    "candidate_count": 0,
                    "matched_metric_row_count": 0,
                    "error": f"{type(exc).__name__}: {exc}",
                    "prepared_rows": [],
                }
            )
            continue

        row_text_rows = _row_text_rows_from_blocks(pdf, blocks)
        cleaned = clean_row_texts(row_text_rows)
        repaired = repair_row_fragments(cleaned["cleaned_rows"], expected_year_count=5)
        extracted = extract_metric_candidates_from_repaired_rows(repaired["repaired_rows"], expected_year_count=5)
        prepared_rows = [
            _prepared_row_from_candidate(candidate, _norm_text(candidate.get("source_page")))
            for candidate in extracted.get("metric_candidate_preview", [])
        ]
        scan_rows.append(
            {
                "source_pdf": pdf.name,
                "block_count": int(len(blocks)),
                "row_text_row_count": int(len(row_text_rows)),
                "cleaned_row_count": int(len(cleaned["cleaned_rows"])),
                "repaired_row_count": int(len(repaired["repaired_rows"])),
                "candidate_count": int(len(prepared_rows)),
                "matched_metric_row_count": int(extracted.get("matched_metric_row_count", 0)),
                "error": "",
                "prepared_rows": prepared_rows,
            }
        )

    ranked = sorted(
        scan_rows,
        key=lambda row: (
            -int(row.get("candidate_count", 0)),
            -int(row.get("matched_metric_row_count", 0)),
            _norm_text(row.get("source_pdf")),
        ),
    )
    selected = [row for row in ranked if int(row.get("candidate_count", 0)) > 0][:select_count]
    selected_pdf_names = [_norm_text(row.get("source_pdf")) for row in selected]
    prepared_rows: List[Dict[str, Any]] = []
    for row in selected:
        prepared_rows.extend(row.get("prepared_rows", []))
    prepared_df = _frame_for_output(pd.DataFrame(prepared_rows, columns=REQUIRED_FIELDS))

    return {
        "scan_df": _frame_for_output(
            pd.DataFrame(
                [
                    {k: v for k, v in row.items() if k != "prepared_rows"}
                    for row in scan_rows
                ]
            )
        ),
        "selected_pdf_names": selected_pdf_names,
        "prepared_df": prepared_df,
    }


def _write_prepared_outputs(prepared_output_dir: Path, prepared_df: pd.DataFrame) -> Dict[str, str]:
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

    with pd.ExcelWriter(compat_xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame(compatibility_rows).to_excel(writer, sheet_name="affected_candidates", index=False)

    return {
        "jsonl_path": str(jsonl_path),
        "xlsx_path": str(xlsx_path),
        "manifest_path": str(manifest_path),
        "compat_jsonl_path": str(compat_jsonl_path),
        "compat_xlsx_path": str(compat_xlsx_path),
    }


def build_unfamiliar_candidate_export_smoke_330f4(
    *,
    unfamiliar_input_dir: Path,
    previous_330f3_dir: Path,
    prepared_output_dir: Path,
    output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    previous_summary_path = previous_330f3_dir / "unfamiliar_candidate_output_generation_330f3_summary.json"
    previous_summary = _read_json(previous_summary_path)
    qa_rows = validate_330f3_summary(previous_summary)

    def add_qa(name: str, passed: bool, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }

    smoke = inspect_smoke_candidate_export(unfamiliar_input_dir)
    scan_df = smoke["scan_df"]
    selected_pdf_names = smoke["selected_pdf_names"]
    prepared_df = smoke["prepared_df"]

    add_qa(
        "selection::selected_pdf_count",
        len(selected_pdf_names) in {2, 3},
        str(len(selected_pdf_names)),
    )
    add_qa(
        "records::prepared_candidate_row_count",
        len(prepared_df) > 0,
        str(len(prepared_df)),
    )

    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    no_official_asset_modification_during_330f4 = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330f4",
        no_official_asset_modification_during_330f4,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    written_paths: Dict[str, str] = {}
    if len(prepared_df) > 0:
        written_paths = _write_prepared_outputs(prepared_output_dir, prepared_df)
        manifest = {
            "stage": "330F4",
            "selected_pdf_count": int(len(selected_pdf_names)),
            "selected_pdfs": list(selected_pdf_names),
            "processed_pdf_count": int(prepared_df["source_pdf"].astype(str).nunique()) if not prepared_df.empty else 0,
            "prepared_candidate_row_count": int(len(prepared_df)),
            "required_fields": list(REQUIRED_FIELDS),
            "missing_field_counts": _missing_field_counts(prepared_df),
            **written_paths,
        }
        Path(written_paths["manifest_path"]).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        manifest = {
            "stage": "330F4",
            "selected_pdf_count": int(len(selected_pdf_names)),
            "selected_pdfs": list(selected_pdf_names),
            "processed_pdf_count": 0,
            "prepared_candidate_row_count": 0,
            "required_fields": list(REQUIRED_FIELDS),
            "missing_field_counts": {field: 0 for field in REQUIRED_FIELDS},
        }

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    processed_pdf_count = int(prepared_df["source_pdf"].astype(str).nunique()) if not prepared_df.empty else 0
    can_rerun_330f = processed_pdf_count > 0 and len(prepared_df) > 0 and qa_fail_count == 0
    decision = READY_DECISION if can_rerun_330f else WAITING_DECISION
    if qa_fail_count > 0:
        decision = NOT_READY_DECISION

    summary = {
        "stage": "330F4",
        "output_dir": str(output_dir),
        "prepared_output_dir": str(prepared_output_dir),
        "validated_330f3_waiting_state": qa_fail_count == 0,
        "selected_pdf_count": int(len(selected_pdf_names)),
        "selected_pdfs": list(selected_pdf_names),
        "processed_pdf_count": int(processed_pdf_count),
        "prepared_candidate_row_count": int(len(prepared_df)),
        "extraction_export_approach_used": "pdfplumber_table_blocks_plus_existing_row_text_candidate_extractors",
        "can_rerun_330f": can_rerun_330f,
        "output_dir_for_330f": str(prepared_output_dir),
        "missing_field_counts": manifest.get("missing_field_counts", {}),
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330f4": no_official_asset_modification_during_330f4,
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
        stage="330F4",
        files_read=list(files_read),
        official_assets_before=official_assets_before,
        official_assets_after=official_assets_after,
        official_assets_written=[],
    )

    return {
        "summary": summary,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "manifest_json": manifest,
        "summary_df": _frame_for_output(pd.DataFrame([summary])),
        "qa_summary_df": _frame_for_output(pd.DataFrame([{"qa_pass_count": qa_pass_count, "qa_fail_count": qa_fail_count, "decision": decision}])),
        "qa_checks_df": qa_df,
        "scan_df": scan_df,
        "prepared_df": prepared_df,
        "missing_field_counts_df": _frame_for_output(
            pd.DataFrame([{"field_name": key, "missing_count": value} for key, value in manifest.get("missing_field_counts", {}).items()])
        ),
        "official_asset_proof_df": _frame_for_output(
            pd.DataFrame(
                [
                    {
                        "asset_path": asset_path,
                        "hash_before": before_hash,
                        "hash_after": official_assets_after.get(asset_path, ""),
                        "modified_during_330f4": before_hash != official_assets_after.get(asset_path, ""),
                    }
                    for asset_path, before_hash in official_assets_before.items()
                ]
            )
        ),
    }
