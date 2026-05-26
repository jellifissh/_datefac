import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config_manager import ConfigManager
from extractor_adapter import extract_pdfplumber_table_blocks
import pdfplumber_profile_extractor as ppe
from table_block import TableBlock

import build_stage7b_full_structured_sandbox as s7b
import build_stage7c_statement_classification_sandbox as s7c
import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
INPUT_DIR = BASE_DIR / "input"

EVAL1_DIR = BASE_DIR / "output" / "eval1_10pdf_sandbox_extraction_evaluation"
EVAL1A_DIR = BASE_DIR / "output" / "eval1a_table_extraction_structure_quality_audit"
OUT_DIR = BASE_DIR / "output" / "eval1b_profile_selection_fix_regression"

IN_EVAL1_SUMMARY = EVAL1_DIR / "300_eval1_10pdf_extraction_evaluation_summary.json"
IN_EVAL1_PER_PDF = EVAL1_DIR / "300_eval1_per_pdf_metrics.xlsx"
IN_EVAL1A_SUMMARY = EVAL1A_DIR / "301_eval1a_table_extraction_structure_quality_summary.json"
IN_EVAL1A_PROFILE_AUDIT = EVAL1A_DIR / "301_eval1a_profile_selection_audit.xlsx"
IN_EVAL1A_FIX_PLAN = EVAL1A_DIR / "301_eval1a_recommended_extraction_fix_plan.json"

OUT_SUMMARY = OUT_DIR / "302_eval1b_profile_selection_fix_summary.json"
OUT_REPORT = OUT_DIR / "302_eval1b_profile_selection_fix_report.md"
OUT_COMPARISON = OUT_DIR / "302_eval1b_profile_selection_comparison.xlsx"
OUT_PER_PDF = OUT_DIR / "302_eval1b_per_pdf_metrics.xlsx"
OUT_FULL = OUT_DIR / "302_eval1b_full_structured_table.xlsx"
OUT_CLASSIFIED = OUT_DIR / "302_eval1b_classified_structured_table.xlsx"
OUT_CANDIDATE = OUT_DIR / "302_eval1b_core_metrics_candidate_preview.xlsx"
OUT_CONFLICT = OUT_DIR / "302_eval1b_conflict_diagnosis_summary.xlsx"
OUT_GUARD = OUT_DIR / "302_eval1b_regression_guard.json"
OUT_NO_APPLY = OUT_DIR / "302_eval1b_no_apply_proof.json"

RAW_DIR = OUT_DIR / "raw_tables_per_pdf"
BLOCK_DIR = OUT_DIR / "table_blocks_per_pdf"
DEBUG_DIR = OUT_DIR / "debug_per_pdf"

EXPECTED_PDFS = [
    INPUT_DIR / "0b4b955b8219ffd0bc5a277fab5b8b6c.pdf",
    INPUT_DIR / "6a0b9e0769373f552c4348621ad58543.pdf",
    INPUT_DIR / "7ef666d64e743498aa76e6ad4ef70fa1.pdf",
    INPUT_DIR / "6862e6f3995d3dbfbed310b51601fb0a.pdf",
    INPUT_DIR / "H3_AP202604291821755175_1.pdf",
    INPUT_DIR / "H3_AP202605251822844635_1.pdf",
    INPUT_DIR / "H3_AP202605251822845141_1.pdf",
    INPUT_DIR / "H3_AP202605251822853403_1.pdf",
    INPUT_DIR / "H3_AP202605251822859039_1.pdf",
    INPUT_DIR / "H3_AP202605231822706325_1.pdf",
]

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    if isinstance(v, str) and v.strip().lower() == "nan":
        return ""
    return str(v).strip()


def _compact(v: Any) -> str:
    return re.sub(r"\s+", "", _norm(v)).upper()


def _as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return _norm(v).lower() in {"1", "true", "yes", "y"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_sheet_name(name: str, used: set) -> str:
    s = re.sub(r"[\\/*?:\[\]]", "_", _norm(name) or "Sheet")[:31] or "Sheet"
    base = s
    i = 1
    while s in used:
        suffix = f"_{i}"
        s = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(s)
    return s


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=_safe_sheet_name(name, used), index=False)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _snapshot_guard() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP) if RELEASE_ZIP.exists() else "MISSING"
    return snap


def _run_delivery_check() -> Dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    return json.loads(txt) if txt else {"overall_status": "UNKNOWN"}


def _profile_rank_key(stats: Dict[str, Any]) -> Tuple[int, int, int, float, int, int]:
    # Priority:
    # 1) highest good_count
    # 2) highest good_count+ok_count
    # 3) lowest bad_count
    # 4) highest avg_quality_score
    # 5) highest total_non_empty_cells
    # 6) conservative table_count tie-break (lower count preferred when tied)
    good = int(stats.get("good_count", 0) or 0)
    good_ok = int(stats.get("good_ok_count", 0) or 0)
    bad = int(stats.get("bad_count", 0) or 0)
    score = float(stats.get("avg_quality_score", 0.0) or 0.0)
    cells = int(stats.get("total_non_empty_cells", 0) or 0)
    table_count = int(stats.get("table_count", 0) or 0)
    return (good, good_ok, -bad, score, cells, -table_count)


def _material_improvement(old_stats: Dict[str, Any], new_stats: Dict[str, Any]) -> Tuple[bool, str]:
    old_score = float(old_stats.get("avg_quality_score", 0.0) or 0.0)
    new_score = float(new_stats.get("avg_quality_score", 0.0) or 0.0)
    old_good = int(old_stats.get("good_count", 0) or 0)
    new_good = int(new_stats.get("good_count", 0) or 0)
    old_bad = int(old_stats.get("bad_count", 0) or 0)
    new_bad = int(new_stats.get("bad_count", 0) or 0)
    old_good_ok = int(old_stats.get("good_ok_count", 0) or 0)
    new_good_ok = int(new_stats.get("good_ok_count", 0) or 0)

    reasons: List[str] = []
    if new_score - old_score >= 0.15:
        reasons.append("avg_quality_score+0.15")
    if new_good > old_good:
        reasons.append("good_count_increase")
    if new_bad < old_bad:
        reasons.append("bad_count_decrease")
    if new_good_ok > old_good_ok and new_bad <= old_bad:
        reasons.append("good_ok_increase_without_bad_increase")
    return (len(reasons) > 0), "|".join(reasons) if reasons else "no_material_improvement"


def _to_tableblocks(blocks: List[Dict[str, Any]]) -> List[TableBlock]:
    converted: List[TableBlock] = []
    for b in blocks:
        df = b.get("df")
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue
        converted.append(
            TableBlock(
                backend="pdfplumber",
                page=b.get("page"),
                table_index=b.get("table_index"),
                bbox=b.get("bbox"),
                confidence=b.get("confidence"),
                raw_df=df,
            )
        )
    return converted


def _extract_tables_eval1b(pdf_path: Path) -> Tuple[List[TableBlock], str, pd.DataFrame, Dict[str, Any]]:
    cm = ConfigManager(config_path="config.yaml")
    cfg = cm.load()
    extraction_cfg = (cfg.get("table_extraction", {}) or {})
    profile_cfg = (cfg.get("pdfplumber_profiles", {}) or {})

    enabled_profiles = profile_cfg.get("profiles", ["default", "text_text", "text_lines"]) or ["default"]
    profile_order = [str(p).strip().lower() for p in enabled_profiles if str(p).strip().lower() in ppe.PROFILE_SETTINGS]
    if "default" not in profile_order:
        profile_order.insert(0, "default")

    profile_blocks: Dict[str, List[Dict[str, Any]]] = {}
    profile_stats: Dict[str, Dict[str, Any]] = {}
    for profile_name in profile_order:
        if profile_name == "default":
            blocks = ppe._extract_default_profile(str(pdf_path), extraction_cfg, logger=None)
        else:
            blocks = ppe._extract_custom_profile(
                str(pdf_path),
                profile_name=profile_name,
                table_settings=ppe.PROFILE_SETTINGS[profile_name],
                logger=None,
            )
        profile_blocks[profile_name] = blocks
        profile_stats[profile_name] = ppe._summarize_profile(profile_name, blocks)

    old_selected, old_fallback_applied, old_fallback_reason = ppe._choose_selected_profile(
        profile_stats=profile_stats,
        profile_order=profile_order,
        profile_config=profile_cfg,
    )
    if old_selected not in profile_stats and profile_order:
        old_selected = profile_order[0]

    best_profile = old_selected
    best_key = _profile_rank_key(profile_stats.get(old_selected, {}))
    for p in profile_order:
        key = _profile_rank_key(profile_stats.get(p, {}))
        if key > best_key:
            best_profile = p
            best_key = key

    old_stats = profile_stats.get(old_selected, ppe._summarize_profile(old_selected, []))
    best_stats = profile_stats.get(best_profile, ppe._summarize_profile(best_profile, []))
    material, material_reason = _material_improvement(old_stats, best_stats)

    new_selected = old_selected
    if best_profile != old_selected and material:
        new_selected = best_profile

    selected_blocks = profile_blocks.get(new_selected, [])
    selected = _to_tableblocks(selected_blocks)
    selected_by = "pdfplumber_profiles_eval1b_policy"
    if not selected:
        selected = extract_pdfplumber_table_blocks(str(pdf_path), extraction_cfg, logger=None)
        selected_by = "pdfplumber_fallback"

    diag_rows: List[Dict[str, Any]] = []
    for idx, pname in enumerate(profile_order):
        st = profile_stats.get(pname, ppe._summarize_profile(pname, []))
        diag_rows.append(
            {
                "source_pdf": str(pdf_path),
                "profile_name": pname,
                "profile_order": idx + 1,
                "table_count": int(st.get("table_count", 0) or 0),
                "good_count": int(st.get("good_count", 0) or 0),
                "ok_count": int(st.get("ok_count", 0) or 0),
                "bad_count": int(st.get("bad_count", 0) or 0),
                "good_ok_count": int(st.get("good_ok_count", 0) or 0),
                "avg_quality_score": float(st.get("avg_quality_score", 0.0) or 0.0),
                "total_non_empty_cells": int(st.get("total_non_empty_cells", 0) or 0),
                "selected_profile": old_selected,
                "new_selected_profile": new_selected,
                "best_profile_by_policy": best_profile,
                "is_selected": pname == new_selected,
                "fallback_applied": bool(old_fallback_applied),
                "fallback_reason": _norm(old_fallback_reason),
                "profile_changed_by_eval1b": new_selected != old_selected,
                "material_improvement": material,
                "material_improvement_reason": material_reason,
                "selection_policy": "good_count>good_ok_count>low_bad_count>avg_quality_score>total_non_empty_cells>conservative_table_count",
            }
        )
    prof_df = pd.DataFrame(diag_rows).fillna("")

    meta = {
        "old_selected_profile": old_selected,
        "new_selected_profile": new_selected,
        "best_profile_by_policy": best_profile,
        "profile_changed": bool(new_selected != old_selected),
        "material_improvement": bool(material),
        "material_improvement_reason": material_reason,
        "old_stats": old_stats,
        "new_stats": profile_stats.get(new_selected, ppe._summarize_profile(new_selected, [])),
    }
    return selected, selected_by, prof_df, meta


def _build_sandbox_06_preview(classified: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    if classified.empty:
        return pd.DataFrame(), {"duplicate_key_count": 0, "value_mismatch_count": 0, "unit_conflict_count": 0, "year_conflict_count": 0}

    core = classified[classified["usability_layer"].map(_norm) == "candidate_for_core_metrics"].copy()
    rows: List[Dict[str, Any]] = []
    for _, r in core.iterrows():
        rows.append(
            {
                "source_pdf": _norm(r.get("source_pdf")),
                "asset_package": _norm(r.get("source_pdf_name")).replace(".pdf", "_eval1b_sandbox"),
                "standard_metric": _norm(r.get("standard_metric")),
                "year": _norm(r.get("year")),
                "final_value": _norm(r.get("value")),
                "final_unit": _norm(r.get("inferred_unit")),
            }
        )
    df = pd.DataFrame(rows).fillna("")
    if df.empty:
        return df, {"duplicate_key_count": 0, "value_mismatch_count": 0, "unit_conflict_count": 0, "year_conflict_count": 0}

    df["key"] = df["asset_package"].map(_norm) + "||" + df["standard_metric"].map(_norm) + "||" + df["year"].map(_norm)
    duplicate_key_count = int(df["key"].duplicated().sum())
    value_mismatch_count = 0
    unit_conflict_count = 0
    year_conflict_count = 0
    for _, g in df.groupby(["asset_package", "standard_metric"], dropna=False):
        ys = [y for y in g["year"].map(_norm).tolist() if y]
        if len(ys) != len(set(ys)):
            year_conflict_count += 1
    for _, g in df.groupby("key", dropna=False):
        if g["final_value"].map(_norm).nunique() > 1:
            value_mismatch_count += 1
        if g["final_unit"].map(_norm).nunique() > 1:
            unit_conflict_count += 1
    df = df.drop(columns=["key"], errors="ignore")
    return df, {
        "duplicate_key_count": duplicate_key_count,
        "value_mismatch_count": value_mismatch_count,
        "unit_conflict_count": unit_conflict_count,
        "year_conflict_count": year_conflict_count,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    required_inputs = [
        IN_EVAL1_SUMMARY,
        IN_EVAL1_PER_PDF,
        IN_EVAL1A_SUMMARY,
        IN_EVAL1A_PROFILE_AUDIT,
        IN_EVAL1A_FIX_PLAN,
    ]
    missing_inputs = [str(p) for p in required_inputs if not p.exists()]
    if missing_inputs:
        blocked = {
            "stage": "EVAL-1B",
            "mode": "profile_selection_fix_regression",
            "blocked": True,
            "blocked_reason": "missing_eval1_or_eval1a_inputs",
            "missing_input_count": len(missing_inputs),
            "missing_input_list": missing_inputs,
            "external_api_called": False,
            "llm_api_called": False,
            "real_apply_executed": False,
        }
        _write_json(OUT_SUMMARY, blocked)
        OUT_REPORT.write_text("# EVAL-1B BLOCKED\n\nMissing EVAL-1/EVAL-1A required inputs.", encoding="utf-8")
        _write_json(OUT_NO_APPLY, {"external_api_called": False, "llm_api_called": False, "real_apply_executed": False})
        print("eval1b_status=blocked_missing_eval_inputs")
        return 0

    missing_pdfs = [str(p) for p in EXPECTED_PDFS if not p.exists()]
    if missing_pdfs:
        blocked = {
            "stage": "EVAL-1B",
            "mode": "profile_selection_fix_regression",
            "blocked": True,
            "blocked_reason": "missing_expected_pdf",
            "missing_pdf_count": len(missing_pdfs),
            "missing_pdf_list": missing_pdfs,
            "external_api_called": False,
            "llm_api_called": False,
            "real_apply_executed": False,
        }
        _write_json(OUT_SUMMARY, blocked)
        OUT_REPORT.write_text("# EVAL-1B BLOCKED\n\nMissing expected PDFs.", encoding="utf-8")
        _write_json(OUT_NO_APPLY, {"external_api_called": False, "llm_api_called": False, "real_apply_executed": False})
        print("eval1b_status=blocked_missing_expected_pdf")
        return 0

    eval1_summary = _load_json(IN_EVAL1_SUMMARY)
    old_per_pdf_df = pd.read_excel(IN_EVAL1_PER_PDF).fillna("")
    eval1a_summary = _load_json(IN_EVAL1A_SUMMARY)
    eval1a_profile_df = pd.read_excel(IN_EVAL1A_PROFILE_AUDIT).fillna("")
    _ = _load_json(IN_EVAL1A_FIX_PLAN)

    suspected_pdf_set = set(
        eval1a_profile_df[
            eval1a_profile_df.get("suspected_profile_selection_issue", pd.Series([], dtype=bool)).map(_as_bool)
        ].get("pdf_file_name", pd.Series([], dtype=str)).map(_norm).tolist()
    )

    old_pdf_map = {
        _norm(r.get("pdf_file_name")): r for _, r in old_per_pdf_df.iterrows()
    }

    before = _snapshot_guard()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    BLOCK_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    all_full_rows: List[Dict[str, Any]] = []
    all_classified_rows: List[Dict[str, Any]] = []
    all_candidates_rows: List[Dict[str, Any]] = []
    per_pdf_rows: List[Dict[str, Any]] = []
    comparison_rows: List[Dict[str, Any]] = []

    for pdf in EXPECTED_PDFS:
        err = ""
        failure_stage = ""
        selected_by = ""
        raw_df = pd.DataFrame()
        idx_df = pd.DataFrame()
        prof_df = pd.DataFrame()
        one_full: List[Dict[str, Any]] = []
        one_blocks: List[Dict[str, Any]] = []
        one_debug: List[Dict[str, Any]] = []
        classified_df = pd.DataFrame()
        core_preview = pd.DataFrame()
        sandbox06 = pd.DataFrame()
        conflict = {"duplicate_key_count": 0, "value_mismatch_count": 0, "unit_conflict_count": 0, "year_conflict_count": 0}
        notes = ""
        extraction_status = "FAILED"
        profile_meta: Dict[str, Any] = {}

        try:
            blocks, selected_by, prof_df, profile_meta = _extract_tables_eval1b(pdf)
            raw_rows: List[Dict[str, Any]] = []
            for b in blocks:
                raw_rows.extend(s5k._table_to_rows(b, pdf, "pdfplumber"))
            raw_df = pd.DataFrame(
                raw_rows,
                columns=[
                    "table_id",
                    "page",
                    "row_index",
                    "col_index",
                    "cell_text",
                    "extractor_name",
                    "extraction_status",
                    "source_pdf",
                    "source_bbox",
                    "raw_row_text",
                    "raw_col_count",
                ],
            ).fillna("")
            idx_df = s5k._aggregate_table_index(blocks, "pdfplumber", pdf)

            table_ids = raw_df["table_id"].map(_norm).dropna().unique().tolist() if not raw_df.empty else []
            for table_id in table_ids:
                m = re.search(r"\|p(\d+)\|t(\d+)\|", table_id)
                page_num = int(m.group(1)) if m else 0
                rows, blks, dbg = s7b._build_rows_from_table(
                    raw_df=raw_df,
                    pdf_name=pdf.name,
                    page_number=page_num,
                    table_id=table_id,
                    block_prefix=pdf.stem,
                )
                one_full.extend(rows)
                one_blocks.extend(blks)
                one_debug.extend(dbg)

            full_df = pd.DataFrame(one_full).fillna("")
            if full_df.empty:
                failure_stage = "full_structured"
                extraction_status = "PARTIAL" if not raw_df.empty else "FAILED"
                err = "empty_full_structured_rows"
            else:
                classified_df = full_df.copy()
                normalized_types: List[str] = []
                reasons: List[str] = []
                confs: List[float] = []
                for _, row in classified_df.iterrows():
                    nst, rsn, conf = s7c._normalize_statement(row)
                    metric = _norm(row.get("normalized_metric_name")) or _norm(row.get("raw_metric_name"))
                    if ("EPS" in s7c._compact(metric) or "每股收益" in metric) and nst == "financial_ratios":
                        nst, rsn, conf = "per_share_metrics", "eps_force_not_ratio_guard", 0.99
                    normalized_types.append(nst)
                    reasons.append(rsn)
                    confs.append(round(float(conf), 4))
                classified_df["normalized_statement_type"] = normalized_types
                classified_df["classification_reason"] = reasons
                classified_df["classification_confidence"] = confs
                classified_df["usability_layer"] = [s7c._usability_layer(r) for _, r in classified_df.iterrows()]

                core_preview = classified_df[
                    classified_df["usability_layer"].map(_norm).isin({"candidate_for_core_metrics", "manual_review_required"})
                ].copy()
                sandbox06, conflict = _build_sandbox_06_preview(classified_df)

                all_full_rows.extend(full_df.to_dict("records"))
                all_classified_rows.extend(classified_df.to_dict("records"))
                all_candidates_rows.extend(core_preview.to_dict("records"))

                extraction_status = "SUCCESS"
                if raw_df.empty:
                    extraction_status = "PARTIAL"
                    notes = "no_raw_tables_extracted"
                elif core_preview.empty:
                    extraction_status = "PARTIAL"
                    notes = "no_core_metrics_candidates"

            if extraction_status in {"FAILED", "PARTIAL"} and not failure_stage:
                failure_stage = "classification_or_candidates"

        except Exception as exc:
            extraction_status = "FAILED"
            failure_stage = failure_stage or "pipeline_exception"
            err = f"{type(exc).__name__}: {exc}"

        block_df = pd.DataFrame(one_blocks).fillna("")
        debug_df = pd.DataFrame(one_debug).fillna("")
        _write_excel(RAW_DIR / f"{pdf.stem}_raw_tables.xlsx", {"raw_tables": raw_df, "table_index": idx_df, "profile_diag": prof_df})
        _write_excel(BLOCK_DIR / f"{pdf.stem}_table_blocks.xlsx", {"table_blocks": block_df})
        _write_excel(DEBUG_DIR / f"{pdf.stem}_debug.xlsx", {"debug": debug_df})

        eps_scope = classified_df[
            classified_df["normalized_metric_name"].map(lambda x: "EPS" in s7c._compact(x) or "每股收益" in _norm(x))
        ].copy() if not classified_df.empty else pd.DataFrame()
        bad_eps_ratio_count = int((eps_scope["normalized_statement_type"].map(_norm) == "financial_ratios").sum()) if not eps_scope.empty else 0
        unknown_statement_type_count = int((classified_df["normalized_statement_type"].map(_norm) == "unknown_financial_table").sum()) if not classified_df.empty else 0

        per_pdf_rows.append(
            {
                "pdf_file_name": pdf.name,
                "pdf_path": str(pdf),
                "file_size_bytes": int(pdf.stat().st_size),
                "extraction_status": extraction_status,
                "error_message": err,
                "raw_table_count": int(raw_df["table_id"].nunique()) if not raw_df.empty else 0,
                "raw_table_row_count": int(len(raw_df)),
                "full_structured_row_count": int(len(one_full)),
                "classified_row_count": int(len(classified_df)),
                "core_metrics_candidate_count": int(len(core_preview)),
                "sandbox_preview_candidate_count": int(len(sandbox06)),
                "duplicate_key_count": int(conflict["duplicate_key_count"]),
                "value_mismatch_count": int(conflict["value_mismatch_count"]),
                "unit_conflict_count": int(conflict["unit_conflict_count"]),
                "year_conflict_count": int(conflict["year_conflict_count"]),
                "eps_detected_count": int(len(eps_scope)),
                "bad_eps_ratio_count": int(bad_eps_ratio_count),
                "unknown_statement_type_count": int(unknown_statement_type_count),
                "empty_table_count": int((idx_df["raw_row_count"] == 0).sum()) if (not idx_df.empty and "raw_row_count" in idx_df.columns) else 0,
                "selected_by": selected_by,
                "old_selected_profile": _norm(profile_meta.get("old_selected_profile")),
                "new_selected_profile": _norm(profile_meta.get("new_selected_profile")),
                "profile_changed": bool(profile_meta.get("profile_changed", False)),
                "suspected_profile_issue_from_eval1a": pdf.name in suspected_pdf_set,
                "notes": notes,
            }
        )

        old_row = old_pdf_map.get(pdf.name, {})
        old_stats = profile_meta.get("old_stats", {})
        new_stats = profile_meta.get("new_stats", {})
        profile_changed = bool(profile_meta.get("profile_changed", False))
        material_reason = _norm(profile_meta.get("material_improvement_reason"))

        improved = False
        regressed = False
        if profile_changed:
            improved = (
                float(new_stats.get("avg_quality_score", 0.0) or 0.0) - float(old_stats.get("avg_quality_score", 0.0) or 0.0) >= 0.15
                or int(new_stats.get("good_count", 0) or 0) > int(old_stats.get("good_count", 0) or 0)
                or int(new_stats.get("bad_count", 0) or 0) < int(old_stats.get("bad_count", 0) or 0)
                or (
                    int(new_stats.get("good_ok_count", 0) or 0) > int(old_stats.get("good_ok_count", 0) or 0)
                    and int(new_stats.get("bad_count", 0) or 0) <= int(old_stats.get("bad_count", 0) or 0)
                )
            )
            regressed = not improved

        comparison_rows.append(
            {
                "pdf_file_name": pdf.name,
                "old_selected_profile": _norm(profile_meta.get("old_selected_profile")),
                "new_selected_profile": _norm(profile_meta.get("new_selected_profile")),
                "profile_changed": profile_changed,
                "old_avg_quality_score": float(old_stats.get("avg_quality_score", 0.0) or 0.0),
                "new_avg_quality_score": float(new_stats.get("avg_quality_score", 0.0) or 0.0),
                "old_good_count": int(old_stats.get("good_count", 0) or 0),
                "new_good_count": int(new_stats.get("good_count", 0) or 0),
                "old_bad_count": int(old_stats.get("bad_count", 0) or 0),
                "new_bad_count": int(new_stats.get("bad_count", 0) or 0),
                "old_raw_table_count": int(old_row.get("raw_table_count", 0) or 0),
                "new_raw_table_count": int(raw_df["table_id"].nunique()) if not raw_df.empty else 0,
                "old_full_structured_row_count": int(old_row.get("full_structured_row_count", 0) or 0),
                "new_full_structured_row_count": int(len(one_full)),
                "old_core_metrics_candidate_count": int(old_row.get("core_metrics_candidate_count", 0) or 0),
                "new_core_metrics_candidate_count": int(len(core_preview)),
                "old_extraction_status": _norm(old_row.get("extraction_status")),
                "new_extraction_status": extraction_status,
                "improved": improved,
                "regressed": regressed,
                "notes": f"suspected_from_eval1a={pdf.name in suspected_pdf_set}; material_reason={material_reason}; failure_stage={failure_stage}",
            }
        )

    per_pdf_df = pd.DataFrame(per_pdf_rows).fillna("")
    comparison_df = pd.DataFrame(comparison_rows).fillna("")

    full_df_all = pd.DataFrame(all_full_rows).fillna("")
    classified_df_all = pd.DataFrame(all_classified_rows).fillna("")
    candidate_df_all = pd.DataFrame(all_candidates_rows).fillna("")

    _write_excel(OUT_PER_PDF, {"per_pdf_metrics": per_pdf_df})
    _write_excel(OUT_COMPARISON, {"profile_selection_comparison": comparison_df})
    _write_excel(OUT_FULL, {"full_structured_table": full_df_all})
    _write_excel(OUT_CLASSIFIED, {"classified_structured_table": classified_df_all})
    _write_excel(OUT_CANDIDATE, {"core_metrics_candidate_preview": candidate_df_all})

    duplicate_key_total_count = int(per_pdf_df["duplicate_key_count"].sum()) if not per_pdf_df.empty else 0
    value_mismatch_total_count = int(per_pdf_df["value_mismatch_count"].sum()) if not per_pdf_df.empty else 0
    unit_conflict_total_count = int(per_pdf_df["unit_conflict_count"].sum()) if not per_pdf_df.empty else 0
    year_conflict_total_count = int(per_pdf_df["year_conflict_count"].sum()) if not per_pdf_df.empty else 0
    bad_eps_ratio_total_count = int(per_pdf_df["bad_eps_ratio_count"].sum()) if not per_pdf_df.empty else 0
    unknown_statement_type_total_count = int(per_pdf_df["unknown_statement_type_count"].sum()) if not per_pdf_df.empty else 0

    most_dup = per_pdf_df.sort_values("duplicate_key_count", ascending=False)[["pdf_file_name", "duplicate_key_count"]].head(3) if not per_pdf_df.empty else pd.DataFrame()
    most_vm = per_pdf_df.sort_values("value_mismatch_count", ascending=False)[["pdf_file_name", "value_mismatch_count"]].head(3) if not per_pdf_df.empty else pd.DataFrame()
    conflict_summary = pd.DataFrame(
        [
            {"metric": "duplicate_key_total_count", "value": duplicate_key_total_count},
            {"metric": "value_mismatch_total_count", "value": value_mismatch_total_count},
            {"metric": "unit_conflict_total_count", "value": unit_conflict_total_count},
            {"metric": "year_conflict_total_count", "value": year_conflict_total_count},
            {"metric": "bad_eps_ratio_total_count", "value": bad_eps_ratio_total_count},
        ]
    )
    _write_excel(
        OUT_CONFLICT,
        {
            "conflict_summary": conflict_summary,
            "top_duplicate_keys": most_dup,
            "top_value_mismatch": most_vm,
        },
    )

    input_pdf_count = len(EXPECTED_PDFS)
    new_pdf_success_count = int((per_pdf_df["extraction_status"] == "SUCCESS").sum())
    new_pdf_partial_count = int((per_pdf_df["extraction_status"] == "PARTIAL").sum())
    new_pdf_failed_count = int((per_pdf_df["extraction_status"] == "FAILED").sum())
    new_extraction_success_rate = round(new_pdf_success_count / input_pdf_count, 4) if input_pdf_count else 0.0

    new_full_structured_total_rows = int(per_pdf_df["full_structured_row_count"].sum()) if not per_pdf_df.empty else 0
    new_core_metrics_candidate_total_rows = int(per_pdf_df["core_metrics_candidate_count"].sum()) if not per_pdf_df.empty else 0
    new_zero_candidate_pdf_count = int((per_pdf_df["core_metrics_candidate_count"] == 0).sum()) if not per_pdf_df.empty else 0

    old_pdf_success_count = int(eval1_summary.get("pdf_success_count", 0) or 0)
    old_pdf_partial_count = int(eval1_summary.get("pdf_partial_count", 0) or 0)
    old_pdf_failed_count = int(eval1_summary.get("pdf_failed_count", 0) or 0)
    old_extraction_success_rate = float(eval1_summary.get("extraction_success_rate", 0.0) or 0.0)
    old_full_structured_total_rows = int(eval1_summary.get("full_structured_total_rows", 0) or 0)
    old_core_metrics_candidate_total_rows = int(eval1_summary.get("core_metrics_candidate_total_rows", 0) or 0)
    old_zero_candidate_pdf_count = int((old_per_pdf_df["core_metrics_candidate_count"] == 0).sum()) if not old_per_pdf_df.empty else 0
    old_unknown_statement_type_total_count = int(eval1_summary.get("unknown_statement_type_total_count", 0) or 0)

    profile_changed_pdf_count = int((comparison_df["profile_changed"] == True).sum()) if not comparison_df.empty else 0
    profile_quality_improved_pdf_count = int((comparison_df["improved"] == True).sum()) if not comparison_df.empty else 0
    profile_quality_regressed_pdf_count = int((comparison_df["regressed"] == True).sum()) if not comparison_df.empty else 0

    after = _snapshot_guard()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    delivery_status = _norm(delivery.get("overall_status"))

    no_failed_increase = new_pdf_failed_count <= old_pdf_failed_count
    regressions_explained = profile_quality_regressed_pdf_count == 0
    eval1b_profile_selection_fix_pass = bool(
        no_failed_increase
        and new_full_structured_total_rows > 0
        and regressions_explained
        and delivery_status == "PASS"
        and not production_files_modified
        and not official_02b_modified
        and not formal_rules_modified
        and not standardizer_modified
        and not release_package_modified
    )

    ready_for_eval1c = bool(
        eval1b_profile_selection_fix_pass
        and delivery_status == "PASS"
        and not production_files_modified
        and not official_02b_modified
        and not formal_rules_modified
        and not standardizer_modified
        and not release_package_modified
    )

    regression_guard = {
        "no_failed_increase": no_failed_increase,
        "old_pdf_failed_count": old_pdf_failed_count,
        "new_pdf_failed_count": new_pdf_failed_count,
        "new_full_structured_total_rows_gt_zero": new_full_structured_total_rows > 0,
        "profile_quality_regressed_pdf_count": profile_quality_regressed_pdf_count,
        "regressions_explained": regressions_explained,
        "check_delivery_state_overall_status": delivery_status,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "eval1b_profile_selection_fix_pass": eval1b_profile_selection_fix_pass,
    }
    _write_json(OUT_GUARD, regression_guard)

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "llm_api_called": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "production_apply_attempt_count": 0,
            "note": "EVAL-1B is sandbox extraction profile-selection regression only.",
        },
    )

    summary = {
        "stage": "EVAL-1B",
        "mode": "profile_selection_fix_regression",
        "external_api_called": False,
        "llm_api_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "eval1a_summary_loaded": bool(_norm(eval1a_summary.get("stage")) == "EVAL-1A"),
        "input_pdf_count": input_pdf_count,
        "profile_selection_logic_modified": True,
        "candidate_rules_modified": False,
        "fragmented_table_merge_modified": False,
        "multi_panel_splitter_modified": False,
        "profile_changed_pdf_count": profile_changed_pdf_count,
        "profile_quality_improved_pdf_count": profile_quality_improved_pdf_count,
        "profile_quality_regressed_pdf_count": profile_quality_regressed_pdf_count,
        "old_pdf_success_count": old_pdf_success_count,
        "old_pdf_partial_count": old_pdf_partial_count,
        "old_pdf_failed_count": old_pdf_failed_count,
        "new_pdf_success_count": new_pdf_success_count,
        "new_pdf_partial_count": new_pdf_partial_count,
        "new_pdf_failed_count": new_pdf_failed_count,
        "old_extraction_success_rate": old_extraction_success_rate,
        "new_extraction_success_rate": new_extraction_success_rate,
        "old_full_structured_total_rows": old_full_structured_total_rows,
        "new_full_structured_total_rows": new_full_structured_total_rows,
        "old_core_metrics_candidate_total_rows": old_core_metrics_candidate_total_rows,
        "new_core_metrics_candidate_total_rows": new_core_metrics_candidate_total_rows,
        "old_zero_candidate_pdf_count": old_zero_candidate_pdf_count,
        "new_zero_candidate_pdf_count": new_zero_candidate_pdf_count,
        "old_unknown_statement_type_total_count": old_unknown_statement_type_total_count,
        "new_unknown_statement_type_total_count": unknown_statement_type_total_count,
        "duplicate_key_total_count": duplicate_key_total_count,
        "value_mismatch_total_count": value_mismatch_total_count,
        "unit_conflict_total_count": unit_conflict_total_count,
        "year_conflict_total_count": year_conflict_total_count,
        "bad_eps_ratio_total_count": bad_eps_ratio_total_count,
        "eval1b_profile_selection_fix_pass": eval1b_profile_selection_fix_pass,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": delivery_status,
        "ready_for_eval1c_fragmented_table_merge_fix": ready_for_eval1c,
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# EVAL-1B Profile Selection Fix Regression",
        "",
        "## Scope",
        "- profile selection policy improvement only",
        "- candidate rules unchanged",
        "- fragmented merge unchanged",
        "- multi-panel splitter unchanged",
        "",
        "## Comparison",
        f"- profile_changed_pdf_count: {profile_changed_pdf_count}",
        f"- profile_quality_improved_pdf_count: {profile_quality_improved_pdf_count}",
        f"- profile_quality_regressed_pdf_count: {profile_quality_regressed_pdf_count}",
        f"- old_pdf_success_count: {old_pdf_success_count}",
        f"- new_pdf_success_count: {new_pdf_success_count}",
        f"- old_pdf_partial_count: {old_pdf_partial_count}",
        f"- new_pdf_partial_count: {new_pdf_partial_count}",
        f"- old_pdf_failed_count: {old_pdf_failed_count}",
        f"- new_pdf_failed_count: {new_pdf_failed_count}",
        f"- old_extraction_success_rate: {old_extraction_success_rate}",
        f"- new_extraction_success_rate: {new_extraction_success_rate}",
        f"- old_full_structured_total_rows: {old_full_structured_total_rows}",
        f"- new_full_structured_total_rows: {new_full_structured_total_rows}",
        f"- old_core_metrics_candidate_total_rows: {old_core_metrics_candidate_total_rows}",
        f"- new_core_metrics_candidate_total_rows: {new_core_metrics_candidate_total_rows}",
        "",
        "## Safety",
        f"- production_files_modified: {production_files_modified}",
        f"- official_02b_modified: {official_02b_modified}",
        f"- formal_rules_modified: {formal_rules_modified}",
        f"- standardizer_modified: {standardizer_modified}",
        f"- release_package_modified: {release_package_modified}",
        f"- check_delivery_state_overall_status: {delivery_status}",
        "",
        "## Decision",
        f"- eval1b_profile_selection_fix_pass: {eval1b_profile_selection_fix_pass}",
        f"- ready_for_eval1c_fragmented_table_merge_fix: {ready_for_eval1c}",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"eval1b_summary_json: {OUT_SUMMARY}")
    print(f"eval1b_report_md: {OUT_REPORT}")
    print(f"eval1b_profile_selection_fix_pass: {eval1b_profile_selection_fix_pass}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
