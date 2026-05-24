import argparse
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
from pdfplumber_profile_extractor import extract_tables_with_pdfplumber_profiles
from table_block import TableBlock

import build_stage7b_full_structured_sandbox as s7b
import build_stage7c_statement_classification_sandbox as s7c
import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k


BASE_DIR = Path(r"D:\_datefac")
DEFAULT_INPUT = BASE_DIR / "input" / "stage7a_regression_pdfs"
DEFAULT_OUTPUT = BASE_DIR / "output" / "stage7d_pipeline_sandbox"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
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


def _run_delivery_check() -> Dict[str, Any]:
    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    if not txt:
        return {"overall_status": "UNKNOWN"}
    return json.loads(txt)


def _snapshot_guard() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_scope_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP) if RELEASE_ZIP.exists() else "MISSING"
    return snap


def _extract_tables(pdf_path: Path) -> Tuple[List[TableBlock], str, pd.DataFrame]:
    cm = ConfigManager(config_path="config.yaml")
    config = cm.load()
    extraction_cfg = (config.get("table_extraction", {}) or {})

    selected: List[TableBlock] = []
    selected_by = "pdfplumber_fallback"
    profile_diag = pd.DataFrame()

    blocks, profile_diag = extract_tables_with_pdfplumber_profiles(str(pdf_path), config, logger=None)
    if blocks:
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
        if converted:
            selected = converted
            selected_by = "pdfplumber_profiles"
    if not selected:
        selected = extract_pdfplumber_table_blocks(str(pdf_path), extraction_cfg, logger=None)
        selected_by = "pdfplumber_fallback"
    return selected, selected_by, profile_diag


def _build_sandbox_06_preview(classified: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    if classified.empty:
        return pd.DataFrame(), {
            "duplicate_key_count": 0,
            "value_mismatch_count": 0,
            "unit_conflict_count": 0,
            "year_conflict_count": 0,
        }

    core = classified[classified["usability_layer"].map(_norm) == "candidate_for_core_metrics"].copy()
    rows: List[Dict[str, Any]] = []
    for _, r in core.iterrows():
        metric = _norm(r.get("standard_metric"))
        unit = _norm(r.get("inferred_unit"))
        if metric == "每股收益":
            unit = "元/股"
        rows.append(
            {
                "source_pdf": _norm(r.get("source_pdf")),
                "asset_package": _norm(r.get("source_pdf_name")).replace(".pdf", "_stage7d_sandbox"),
                "report_type": "sandbox",
                "data_usability_tier": "sandbox",
                "standard_metric": metric,
                "year": _norm(r.get("year")),
                "final_value": _norm(r.get("value")),
                "final_unit": unit,
                "final_value_source": "STAGE7D_SANDBOX_PREVIEW",
                "final_review_status": "CANDIDATE",
                "trace_note": _norm(r.get("classification_reason")),
                "source_row_label": _norm(r.get("raw_metric_name")),
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
    parser = argparse.ArgumentParser(description="Stage7D unified sandbox pipeline entrypoint.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Input PDF directory")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output sandbox directory")
    parser.add_argument("--mode", default="sandbox", help="Mode, only sandbox is allowed")
    args = parser.parse_args()

    input_dir = Path(args.input)
    out_dir = Path(args.output)
    mode = _norm(args.mode).lower()
    if mode != "sandbox":
        raise RuntimeError("Only sandbox mode is allowed in Stage7D.")
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    pdfs = sorted(input_dir.glob("*.pdf"))
    if len(pdfs) < 5:
        raise RuntimeError(f"Input PDF count is {len(pdfs)}; requires at least 5 under {input_dir}")

    before = _snapshot_guard()

    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = out_dir / "sandbox_raw_tables"
    blocks_dir = out_dir / "sandbox_table_blocks"
    debug_dir = out_dir / "sandbox_debug"
    raw_dir.mkdir(parents=True, exist_ok=True)
    blocks_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)

    full_rows: List[Dict[str, Any]] = []
    all_blocks: List[Dict[str, Any]] = []
    all_debug: List[Dict[str, Any]] = []
    per_pdf_rows: List[Dict[str, Any]] = []

    parse_success_count = 0
    raw_extract_success_count = 0

    for pdf in pdfs[:5]:
        pdf_name = pdf.name
        selected_by = ""
        parse_ok = False
        raw_df = pd.DataFrame()
        idx_df = pd.DataFrame()
        prof_df = pd.DataFrame()
        one_blocks: List[Dict[str, Any]] = []
        one_debug: List[Dict[str, Any]] = []
        one_full: List[Dict[str, Any]] = []
        try:
            blocks, selected_by, prof_df = _extract_tables(pdf)
            parse_ok = True
            parse_success_count += 1

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
            if not raw_df.empty:
                raw_extract_success_count += 1

            table_ids = raw_df["table_id"].map(_norm).dropna().unique().tolist() if not raw_df.empty else []
            for table_id in table_ids:
                m = re.search(r"\|p(\d+)\|t(\d+)\|", table_id)
                page_num = int(m.group(1)) if m else 0
                rows, blks, dbg = s7b._build_rows_from_table(
                    raw_df=raw_df,
                    pdf_name=pdf_name,
                    page_number=page_num,
                    table_id=table_id,
                    block_prefix=pdf.stem,
                )
                one_full.extend(rows)
                one_blocks.extend(blks)
                one_debug.extend(dbg)
        except Exception as exc:
            one_debug.append(
                {
                    "source_pdf_name": pdf_name,
                    "reason": "pipeline_exception",
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            )

        one_full_df = pd.DataFrame(one_full).fillna("")
        one_block_df = pd.DataFrame(one_blocks).fillna("")
        one_debug_df = pd.DataFrame(one_debug).fillna("")
        _write_excel(raw_dir / f"{pdf.stem}_raw_tables.xlsx", {"raw_tables": raw_df, "table_index": idx_df, "profile_diag": prof_df})
        _write_excel(blocks_dir / f"{pdf.stem}_table_blocks.xlsx", {"table_blocks": one_block_df, "full_structured_rows": one_full_df})
        _write_excel(debug_dir / f"{pdf.stem}_debug.xlsx", {"debug": one_debug_df})

        full_rows.extend(one_full)
        all_blocks.extend(one_blocks)
        all_debug.extend(one_debug)
        detected_types = sorted(set([_norm(x.get("statement_type")) for x in one_blocks if _norm(x.get("statement_type"))]))
        per_pdf_rows.append(
            {
                "source_pdf": pdf_name,
                "parse_ok": parse_ok,
                "selected_extractor": selected_by,
                "raw_table_count": int(raw_df["table_id"].nunique()) if not raw_df.empty else 0,
                "full_structured_rows": int(len(one_full_df)),
                "detected_block_count": int(len(one_block_df)),
                "detected_statement_types": ",".join(detected_types),
                "status": "OK" if parse_ok else "FAILED",
            }
        )

    full_df = pd.DataFrame(full_rows).fillna("")
    blocks_df = pd.DataFrame(all_blocks).fillna("")
    debug_df = pd.DataFrame(all_debug).fillna("")
    if full_df.empty:
        raise RuntimeError("Stage7D produced empty full_structured_table.")

    # Stage7C classification logic
    classified = full_df.copy()
    normalized_types: List[str] = []
    reasons: List[str] = []
    confs: List[float] = []
    for _, row in classified.iterrows():
        nst, rsn, conf = s7c._normalize_statement(row)
        metric = _norm(row.get("normalized_metric_name")) or _norm(row.get("raw_metric_name"))
        if ("EPS" in s7c._compact(metric) or "每股收益" in metric) and nst == "financial_ratios":
            nst, rsn, conf = "per_share_metrics", "eps_force_not_ratio_guard", 0.99
        normalized_types.append(nst)
        reasons.append(rsn)
        confs.append(round(float(conf), 4))
    classified["normalized_statement_type"] = normalized_types
    classified["classification_reason"] = reasons
    classified["classification_confidence"] = confs
    classified["usability_layer"] = [s7c._usability_layer(r) for _, r in classified.iterrows()]

    standardized = classified.copy()
    standardized["standardized_status"] = standardized["mapping_status"].map(
        lambda x: "STANDARDIZED_CANDIDATE" if _norm(x) == "MAPPED" else "UNMAPPED_RETAINED"
    )

    core_preview = classified[
        classified["usability_layer"].map(_norm).isin({"candidate_for_core_metrics", "manual_review_required"})
    ].copy()

    sandbox06, conflict = _build_sandbox_06_preview(classified)

    eps_scope = classified[
        classified["normalized_metric_name"].map(lambda x: "EPS" in s7c._compact(x) or "每股收益" in _norm(x))
    ].copy()
    bad_eps_ratio_count = int((eps_scope["normalized_statement_type"].map(_norm) == "financial_ratios").sum()) if not eps_scope.empty else 0

    stmt_counts = classified["normalized_statement_type"].map(_norm).value_counts().to_dict()
    per_pdf_df = pd.DataFrame(per_pdf_rows).fillna("")

    # write outputs
    _write_excel(out_dir / "183_stage7d_full_structured_table.xlsx", {"full_structured_table": full_df, "table_blocks": blocks_df, "debug": debug_df})
    _write_excel(out_dir / "183_stage7d_classified_structured_table.xlsx", {"classified_structured_table": classified, "standardized_structured_table": standardized})
    _write_excel(out_dir / "183_stage7d_core_metrics_candidate_preview.xlsx", {"core_metrics_candidate_preview": core_preview, "eps_rows": eps_scope})
    _write_excel(out_dir / "183_stage7d_sandbox_06_preview.xlsx", {"sandbox_06_preview": sandbox06})
    _write_excel(out_dir / "183_stage7d_conflict_report.xlsx", {"conflict_summary": pd.DataFrame([conflict]), "sandbox_06_preview": sandbox06})
    _write_excel(out_dir / "183_stage7d_per_pdf_inventory.xlsx", {"per_pdf_inventory": per_pdf_df})

    after = _snapshot_guard()
    production_files_modified = not (
        before["01"] == after["01"]
        and before["02"] == after["02"]
        and before["02A"] == after["02A"]
        and before["05"] == after["05"]
        and before["06"] == after["06"]
    )
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_scope_rules"] != after["formal_scope_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()
    overall_status = _norm(delivery.get("overall_status"))

    summary = {
        "stage": "stage7d_unified_sandbox_pipeline",
        "mode": "sandbox_only",
        "based_on_stage7c_commit": "939f4eff2415c4fc330006a4bb149ae37f3d07a6",
        "input_pdf_count": 5,
        "pipeline_entrypoint": "tools/run_stage7d_sandbox_pipeline.py",
        "raw_tables_generated": True,
        "full_structured_table_generated": bool(not full_df.empty),
        "classified_structured_table_generated": bool(not classified.empty),
        "core_metrics_candidate_preview_generated": bool(core_preview is not None),
        "sandbox_06_preview_generated": bool(sandbox06 is not None),
        "full_structured_rows": int(len(full_df)),
        "classified_rows": int(len(classified)),
        "core_metrics_candidate_rows": int(len(core_preview)),
        "sandbox_06_preview_rows": int(len(sandbox06)),
        "statement_type_counts": stmt_counts,
        "duplicate_key_count": int(conflict["duplicate_key_count"]),
        "value_mismatch_count": int(conflict["value_mismatch_count"]),
        "unit_conflict_count": int(conflict["unit_conflict_count"]),
        "year_conflict_count": int(conflict["year_conflict_count"]),
        "eps_detected_count": int(len(eps_scope)),
        "bad_eps_ratio_count": int(bad_eps_ratio_count),
        "production_files_modified": bool(production_files_modified),
        "official_02b_modified": bool(official_02b_modified),
        "formal_rules_modified": bool(formal_rules_modified),
        "standardizer_modified": bool(standardizer_modified),
        "release_package_modified": bool(release_package_modified),
        "check_delivery_state_overall_status": overall_status,
        "ready_for_stage7e_ai_runtime_design": False,
    }

    summary["ready_for_stage7e_ai_runtime_design"] = bool(
        summary["raw_tables_generated"]
        and summary["full_structured_table_generated"]
        and summary["classified_structured_table_generated"]
        and summary["core_metrics_candidate_preview_generated"]
        and summary["sandbox_06_preview_generated"]
        and summary["classified_rows"] == summary["full_structured_rows"]
        and summary["bad_eps_ratio_count"] == 0
        and not summary["production_files_modified"]
        and not summary["official_02b_modified"]
        and not summary["formal_rules_modified"]
        and not summary["standardizer_modified"]
        and not summary["release_package_modified"]
        and summary["check_delivery_state_overall_status"] == "PASS"
    )

    (out_dir / "183_stage7d_pipeline_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report_lines = [
        "# Stage 7D Unified Sandbox Pipeline",
        "",
        "## Run",
        f"- entrypoint: {summary['pipeline_entrypoint']}",
        f"- input_pdf_count: {summary['input_pdf_count']}",
        f"- parse_success_count: {parse_success_count}",
        f"- raw_extract_success_count: {raw_extract_success_count}",
        "",
        "## Output Rows",
        f"- full_structured_rows: {summary['full_structured_rows']}",
        f"- classified_rows: {summary['classified_rows']}",
        f"- core_metrics_candidate_rows: {summary['core_metrics_candidate_rows']}",
        f"- sandbox_06_preview_rows: {summary['sandbox_06_preview_rows']}",
        "",
        "## Statement Type Counts",
    ]
    for k, v in stmt_counts.items():
        report_lines.append(f"- {k}: {v}")
    report_lines.extend(
        [
            "",
            "## EPS & Conflicts",
            f"- eps_detected_count: {summary['eps_detected_count']}",
            f"- bad_eps_ratio_count: {summary['bad_eps_ratio_count']}",
            f"- duplicate_key_count: {summary['duplicate_key_count']}",
            f"- value_mismatch_count: {summary['value_mismatch_count']}",
            f"- unit_conflict_count: {summary['unit_conflict_count']}",
            f"- year_conflict_count: {summary['year_conflict_count']}",
            "",
            "## Safety",
            f"- production_files_modified: {summary['production_files_modified']}",
            f"- official_02b_modified: {summary['official_02b_modified']}",
            f"- formal_rules_modified: {summary['formal_rules_modified']}",
            f"- standardizer_modified: {summary['standardizer_modified']}",
            f"- release_package_modified: {summary['release_package_modified']}",
            f"- check_delivery_state_overall_status: {summary['check_delivery_state_overall_status']}",
            "",
            "## Decision",
            f"- ready_for_stage7e_ai_runtime_design: {summary['ready_for_stage7e_ai_runtime_design']}",
        ]
    )
    (out_dir / "183_stage7d_pipeline_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    print(f"stage7d_summary_json: {out_dir / '183_stage7d_pipeline_summary.json'}")
    print(f"stage7d_report_md: {out_dir / '183_stage7d_pipeline_report.md'}")
    print(f"stage7d_ready_for_stage7e_ai_runtime_design: {summary['ready_for_stage7e_ai_runtime_design']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
