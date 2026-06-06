from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import pandas as pd

from datefac.trust.no_apply_proof import build_no_apply_proof


READY_DECISION = "UNFAMILIAR_OUTPUT_PREPARATION_330F2_READY_FOR_330F_RERUN"
WAITING_DECISION = "UNFAMILIAR_OUTPUT_PREPARATION_330F2_WAITING"
NOT_READY_DECISION = "UNFAMILIAR_OUTPUT_PREPARATION_330F2_NOT_READY"

WAITING_FOR_UNFAMILIAR_INPUTS = "WAITING_FOR_UNFAMILIAR_INPUTS"
WAITING_FOR_PARSER_OUTPUTS = "WAITING_FOR_PARSER_OUTPUTS"
READY_FOR_330F_RERUN = "READY_FOR_330F_RERUN"

DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\unfamiliar_output_preparation_330f2")
DEFAULT_PREPARED_OUTPUT_DIR = Path(r"D:\_datefac\output\unfamiliar_trust_split")
ALTERNATIVE_PREPARED_OUTPUT_DIR = Path(r"D:\_datefac\output\delivery_benchmark_unfamiliar")

DISCOVERY_INPUT_DIRS = [
    Path(r"D:\_datefac\input"),
    Path(r"D:\_datefac\input\unfamiliar"),
]
DISCOVERY_OUTPUT_DIRS = [
    Path(r"D:\_datefac\output"),
    Path(r"D:\_datefac\output\router_mineru_trust_split_322b2"),
    Path(r"D:\_datefac\output\delivery"),
    Path(r"D:\_datefac\output\batch_outputs"),
    Path(r"D:\_datefac\output\mineru_outputs"),
]

PREPARED_COLUMNS = [
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
]


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _frame_for_output(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    return frame.astype(object).where(pd.notna(frame), "")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _listify(value: Any) -> List[str]:
    if value in ("", None):
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    else:
        items = [value]
    ordered: List[str] = []
    seen = set()
    for item in items:
        token = _norm_text(item)
        if token and token not in seen:
            ordered.append(token)
            seen.add(token)
    return ordered


def discover_unfamiliar_inputs(unfamiliar_input_dir: Path) -> pd.DataFrame:
    if not unfamiliar_input_dir.exists() or not unfamiliar_input_dir.is_dir():
        return pd.DataFrame(columns=["pdf_name", "pdf_stem", "full_path", "size_bytes"])

    rows = []
    for path in sorted(unfamiliar_input_dir.glob("*.pdf")):
        rows.append(
            {
                "pdf_name": path.name,
                "pdf_stem": path.stem,
                "full_path": str(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return _frame_for_output(pd.DataFrame(rows))


def discover_matching_cached_outputs(
    unfamiliar_inputs_df: pd.DataFrame,
    output_root: Path,
    *,
    excluded_training_dirs: Iterable[str] | None = None,
) -> pd.DataFrame:
    if unfamiliar_inputs_df.empty or not output_root.exists() or not output_root.is_dir():
        return pd.DataFrame(
            columns=[
                "pdf_name",
                "pdf_stem",
                "match_count",
                "matched_path",
                "matched_parent",
            ]
        )

    excluded = {item.lower() for item in (excluded_training_dirs or [])}
    rows: List[Dict[str, Any]] = []
    for pdf_row in unfamiliar_inputs_df.to_dict(orient="records"):
        stem = _norm_text(pdf_row.get("pdf_stem"))
        if not stem:
            continue
        for path in output_root.rglob("*"):
            try:
                parent_str = str(path.parent)
                name = path.name
            except Exception:
                continue
            if any(token in parent_str.lower() for token in excluded):
                continue
            if stem in name or stem in parent_str:
                rows.append(
                    {
                        "pdf_name": pdf_row.get("pdf_name", ""),
                        "pdf_stem": stem,
                        "match_count": 1,
                        "matched_path": str(path),
                        "matched_parent": parent_str,
                    }
                )
    return _frame_for_output(pd.DataFrame(rows))


def build_unfamiliar_output_preparation_330f2(
    *,
    output_dir: Path,
    prepared_output_dir: Path,
    alias_asset_path: Path,
    scope_asset_path: Path,
    files_read: Sequence[str],
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(check_name: str, passed: bool, detail: str) -> None:
        qa_rows.append(
            {
                "check_name": check_name,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    unfamiliar_input_dir = Path(r"D:\_datefac\input\unfamiliar")
    unfamiliar_inputs_df = discover_unfamiliar_inputs(unfamiliar_input_dir)
    cached_matches_df = discover_matching_cached_outputs(
        unfamiliar_inputs_df,
        Path(r"D:\_datefac\output"),
        excluded_training_dirs={
            "router_mineru_trust_split_322b2",
            "cached_candidate_trust_scoring_330c",
            "routing_policy_calibration_330d",
            "deduped_candidate_trust_benchmark_330e",
            "unfamiliar_pdf_trust_benchmark_330f",
        },
    )

    official_assets_before = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    official_assets_after = {
        str(alias_asset_path): hashlib.sha256(alias_asset_path.read_bytes()).hexdigest() if alias_asset_path.exists() else "__MISSING__",
        str(scope_asset_path): hashlib.sha256(scope_asset_path.read_bytes()).hexdigest() if scope_asset_path.exists() else "__MISSING__",
    }
    no_official_asset_modification_during_330f2 = official_assets_before == official_assets_after
    add_qa(
        "safety::no_official_asset_modification_during_330f2",
        no_official_asset_modification_during_330f2,
        json.dumps({"before": official_assets_before, "after": official_assets_after}, ensure_ascii=False),
    )

    input_pdf_count = len(unfamiliar_inputs_df)
    matched_cached_output_count = len(cached_matches_df)

    if input_pdf_count == 0:
        status = WAITING_FOR_UNFAMILIAR_INPUTS
        recommendation = "Add unfamiliar PDFs under D:\\_datefac\\input\\unfamiliar before rerunning 330F2."
    elif matched_cached_output_count == 0:
        status = WAITING_FOR_PARSER_OUTPUTS
        recommendation = (
            "Generate lightweight cached candidate outputs for D:\\_datefac\\input\\unfamiliar using an existing sidecar export path, "
            "then rerun 330F2 and 330F."
        )
    else:
        status = READY_FOR_330F_RERUN
        recommendation = "Rerun 330F against prepared unfamiliar candidate rows."

    prepared_candidate_rows_df = pd.DataFrame(columns=PREPARED_COLUMNS)
    prepared_candidate_row_count = 0

    qa_df = _frame_for_output(pd.DataFrame(qa_rows))
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    decision = READY_DECISION if status == READY_FOR_330F_RERUN and qa_fail_count == 0 else WAITING_DECISION
    if qa_fail_count > 0:
        decision = NOT_READY_DECISION

    summary = {
        "stage": "330F2",
        "output_dir": str(output_dir),
        "prepared_output_dir": str(prepared_output_dir),
        "alternative_prepared_output_dir": str(ALTERNATIVE_PREPARED_OUTPUT_DIR),
        "unfamiliar_output_preparation_status": status,
        "discovered_unfamiliar_input_pdf_count": input_pdf_count,
        "matched_cached_output_count": matched_cached_output_count,
        "prepared_candidate_row_count": prepared_candidate_row_count,
        "can_rerun_330f": status == READY_FOR_330F_RERUN and qa_fail_count == 0,
        "recommended_next_action": recommendation,
        "production_routing_modified": False,
        "official_assets_modified": False,
        "no_official_asset_modification_during_330f2": no_official_asset_modification_during_330f2,
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
        stage="330F2",
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
    recommendation_df = _frame_for_output(
        pd.DataFrame(
            [
                {"recommendation_type": "status", "value": status},
                {"recommendation_type": "next_action", "value": recommendation},
                {
                    "recommendation_type": "recommended_command",
                    "value": (
                        "Use an existing lightweight cached candidate export path for D:\\_datefac\\input\\unfamiliar, "
                        "then run: python tools\\run_unfamiliar_pdf_trust_benchmark_330f.py --deduped-candidate-benchmark-dir "
                        "D:\\_datefac\\output\\deduped_candidate_trust_benchmark_330e --trust-scoring-dir "
                        "D:\\_datefac\\output\\trust_engine_scoring_330b --unfamiliar-source-dir D:\\_datefac\\output\\unfamiliar_trust_split "
                        "--output-dir D:\\_datefac\\output\\unfamiliar_pdf_trust_benchmark_330f"
                    ),
                },
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
                    "modified_during_330f2": before_hash != official_assets_after.get(asset_path, ""),
                }
                for asset_path, before_hash in official_assets_before.items()
            ]
        )
    )
    known_limitations_df = _frame_for_output(
        pd.DataFrame(
            [
                {
                    "limitation": "no_cached_unfamiliar_candidate_rows",
                    "detail": "There are unfamiliar PDFs, but no matching cached parser outputs or candidate-row artifacts were found under output/.",
                },
                {
                    "limitation": "sidecar_preparation_only",
                    "detail": "330F2 does not run heavy parsers and does not modify production routing or official assets.",
                },
            ]
        )
    )

    return {
        "summary": summary,
        "qa_json": qa_json,
        "no_apply_proof_json": no_apply_proof_json,
        "summary_df": summary_df,
        "qa_summary_df": qa_summary_df,
        "qa_checks_df": qa_df,
        "unfamiliar_inputs_df": _frame_for_output(unfamiliar_inputs_df),
        "cached_matches_df": _frame_for_output(cached_matches_df),
        "prepared_candidate_rows_df": _frame_for_output(prepared_candidate_rows_df),
        "recommendation_df": recommendation_df,
        "official_asset_proof_df": official_asset_proof_df,
        "known_limitations_df": known_limitations_df,
    }
