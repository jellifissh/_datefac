import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


DEFAULT_DELIVERY_DIR = Path(r"D:\_datefac\output\delivery_package")


REQUIRED_REVIEW_COLS = [
    "review_status",
    "corrected_value",
    "corrected_unit",
    "use_corrected_value",
    "reviewer_note",
    "reviewer",
    "reviewed_at",
]


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_int(v, default: int = -1) -> int:
    try:
        return int(float(v))
    except Exception:
        return default


def _to_bool(v) -> bool:
    s = _norm(v).lower()
    return s in {"1", "true", "yes", "y", "是", "t"}


def _safe_write_excel(df: pd.DataFrame, path: Path) -> Path:
    final_path = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(final_path, index=False, engine="openpyxl")
    return final_path


def _safe_write_text(text: str, path: Path) -> Path:
    final_path = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(text, encoding="utf-8")
    return final_path


def _read_required_inputs(delivery_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, Path, Path]:
    p01s = sorted(delivery_dir.glob("01_*.xlsx"))
    p02s = sorted(delivery_dir.glob("02_*.xlsx"))
    if not p01s:
        raise FileNotFoundError(f"Required file missing: {delivery_dir}\\01_*.xlsx")
    if not p02s:
        raise FileNotFoundError(f"Required file missing: {delivery_dir}\\02_*.xlsx")
    p01 = p01s[0]
    p02 = p02s[0]
    df01 = pd.read_excel(p01, engine="openpyxl").fillna("")
    df02 = pd.read_excel(p02, engine="openpyxl").fillna("")
    return df01, df02, p01, p02


def _ensure_review_columns(df02: pd.DataFrame) -> pd.DataFrame:
    out = df02.copy()
    for c in REQUIRED_REVIEW_COLS:
        if c not in out.columns:
            out[c] = ""
    return out


def _parse_year_from_text(text: str) -> str:
    s = _norm(text)
    if not s:
        return ""
    # Prefer full tokens like 2025A / 2026E / 2024
    m = re.findall(r"(20\d{2}[A-Za-z]?)", s)
    if m:
        return m[0]
    return ""


def _resolve_manual_year(row: pd.Series) -> str:
    # 1) explicit year column
    if "year" in row.index:
        y = _norm(row.get("year"))
        if y:
            return y
    # 2) source_column
    y = _parse_year_from_text(_norm(row.get("source_column")))
    if y:
        return y
    # 3) raw_value_examples
    y = _parse_year_from_text(_norm(row.get("raw_value_examples")))
    if y:
        return y
    return ""


def _parse_reviewed_at(v) -> pd.Timestamp:
    s = _norm(v)
    if not s:
        return pd.Timestamp.min
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return pd.Timestamp.min


def _dedupe_manual_candidates(cands: List[Dict[str, object]]) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    if not cands:
        return [], []
    grouped: Dict[Tuple[str, str, str], List[Dict[str, object]]] = {}
    for c in cands:
        key = (str(c.get("asset_package", "")), str(c.get("standard_metric", "")), str(c.get("year", "")))
        grouped.setdefault(key, []).append(c)
    kept: List[Dict[str, object]] = []
    ignored: List[Dict[str, object]] = []
    for _, arr in grouped.items():
        arr2 = sorted(
            arr,
            key=lambda x: (
                _parse_reviewed_at(x.get("reviewed_at")),
                1 if _norm(x.get("corrected_value")) else 0,
            ),
            reverse=True,
        )
        best = arr2[0]
        kept.append(best)
        for other in arr2[1:]:
            x = other.copy()
            x["action"] = "conflict_ignored"
            x["action_reason"] = "same_key_older_or_lower_priority_manual_correction"
            ignored.append(x)
    return kept, ignored


def _build_template_md() -> str:
    return (
        "# 复核模板说明\n\n"
        "## 1. 填写位置\n"
        "- 请在 `02_人工复核指标队列.xlsx` 中填写以下字段：\n"
        "- `review_status`\n"
        "- `use_corrected_value`\n"
        "- `corrected_value`\n"
        "- `corrected_unit`\n"
        "- `reviewer`\n"
        "- `reviewed_at`\n"
        "- `reviewer_note`\n\n"
        "## 2. review_status 可选值\n"
        "- pending\n"
        "- accepted\n"
        "- rejected\n"
        "- corrected\n"
        "- not_applicable\n\n"
        "## 3. use_corrected_value 填写规则\n"
        "- 支持：`TRUE/FALSE`、`是/否`、`1/0`、`yes/no`、`Y/N`。\n"
        "- 仅当 `use_corrected_value=True` 且 `corrected_value` 非空时才会应用覆盖。\n\n"
        "## 4. corrected_value / corrected_unit 示例\n"
        "- corrected_value: `123.45`\n"
        "- corrected_unit: `亿元` / `%` / `元`\n\n"
        "## 5. 最终表覆盖规则\n"
        "- 唯一键：`asset_package + standard_metric + year`\n"
        "- 命中同键：覆盖自动可信值，记录 `original_auto_value`。\n"
        "- 未命中同键：新增 `manual_added` 行。\n"
        "- 同键多条人工修正：优先 `reviewed_at` 最新。\n\n"
        "## 6. 注意事项\n"
        "- 不要直接修改 `01_自动可信核心指标.xlsx`。\n"
        "- 请通过 `02_人工复核指标队列.xlsx` 回写后再运行本工具。\n"
    )


def apply_manual_review(delivery_dir: Path) -> Dict[str, object]:
    df01, df02_raw, p01, p02 = _read_required_inputs(delivery_dir)
    df02 = _ensure_review_columns(df02_raw)

    trusted_input_rows = len(df01)
    manual_review_rows = len(df02)

    base = df01.copy()
    # Ensure required columns for final output.
    if "source_pdf" not in base.columns:
        base["source_pdf"] = ""
    if "report_type" not in base.columns:
        base["report_type"] = ""
    if "data_usability_tier" not in base.columns:
        base["data_usability_tier"] = ""
    if "unit" not in base.columns:
        base["unit"] = ""
    if "value_validation_status" not in base.columns:
        base["value_validation_status"] = ""
    if "value_repair_applied" not in base.columns:
        base["value_repair_applied"] = ""
    if "source_row_label" not in base.columns:
        base["source_row_label"] = ""
    if "source_table_index" not in base.columns:
        base["source_table_index"] = ""
    if "source_row_index" not in base.columns:
        base["source_row_index"] = ""
    if "source_column" not in base.columns:
        base["source_column"] = ""
    if "evidence_crop_path" not in base.columns:
        base["evidence_crop_path"] = ""
    if "trace_note" not in base.columns:
        base["trace_note"] = ""

    base["final_value_source"] = "auto_trusted"
    base["final_review_status"] = "auto"
    base["final_value"] = base["value"].map(_norm)
    base["final_unit"] = base["unit"].map(_norm)
    base["final_note"] = "from auto trusted table"
    base["original_auto_value"] = base["value"].map(_norm)
    base["original_auto_unit"] = base["unit"].map(_norm)
    base["corrected_value"] = ""
    base["corrected_unit"] = ""
    base["reviewer"] = ""
    base["reviewed_at"] = ""
    base["reviewer_note"] = ""

    key_cols = ["asset_package", "standard_metric", "year"]
    for c in key_cols:
        if c not in base.columns:
            raise ValueError(f"trusted table missing required key column: {c}")
    base["_key"] = base.apply(lambda r: f"{_norm(r['asset_package'])}|{_norm(r['standard_metric'])}|{_norm(r['year'])}", axis=1)

    app_rows: List[Dict[str, object]] = []
    unresolved_rows: List[Dict[str, object]] = []
    manual_candidates: List[Dict[str, object]] = []

    for _, r in df02.iterrows():
        ap = _norm(r.get("asset_package"))
        metric = _norm(r.get("standard_metric"))
        year = _resolve_manual_year(r)
        review_status = _norm(r.get("review_status")).lower()
        use_corr = _to_bool(r.get("use_corrected_value"))
        corrected_value = _norm(r.get("corrected_value"))
        corrected_unit = _norm(r.get("corrected_unit"))
        reviewer = _norm(r.get("reviewer"))
        reviewed_at = _norm(r.get("reviewed_at"))
        reviewer_note = _norm(r.get("reviewer_note"))
        source_row_label = _norm(r.get("source_row_label"))
        source_table_index = _norm(r.get("source_table_index"))
        source_row_index = _norm(r.get("source_row_index"))
        evidence_crop_path = _norm(r.get("evidence_crop_path"))
        recommendation = _norm(r.get("recommendation"))
        issue_flags = _norm(r.get("value_issue_flags"))
        raw_value_examples = _norm(r.get("raw_value_examples"))

        key_ok = bool(ap and metric and year)
        status_pending = review_status in {"", "pending"}
        status_rejected = review_status in {"rejected", "not_applicable"}
        status_accept = review_status in {"corrected", "accepted"}

        if status_pending:
            app_rows.append(
                {
                    "asset_package": ap,
                    "standard_metric": metric,
                    "year": year,
                    "review_status": review_status or "pending",
                    "use_corrected_value": _norm(r.get("use_corrected_value")),
                    "corrected_value": corrected_value,
                    "corrected_unit": corrected_unit,
                    "action": "ignored_pending",
                    "action_reason": "review_status_pending_or_empty",
                    "original_auto_value": "",
                    "final_value": "",
                    "reviewer": reviewer,
                    "reviewed_at": reviewed_at,
                    "reviewer_note": reviewer_note,
                    "source_row_label": source_row_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "evidence_crop_path": evidence_crop_path,
                }
            )
            unresolved_rows.append(
                {
                    "asset_package": ap,
                    "standard_metric": metric,
                    "year": year,
                    "problem_type": "pending_review",
                    "value_issue_flags": issue_flags,
                    "raw_value_examples": raw_value_examples,
                    "recommendation": recommendation or "complete manual review fields",
                    "source_row_label": source_row_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "evidence_crop_path": evidence_crop_path,
                }
            )
            continue

        if status_rejected:
            app_rows.append(
                {
                    "asset_package": ap,
                    "standard_metric": metric,
                    "year": year,
                    "review_status": review_status,
                    "use_corrected_value": _norm(r.get("use_corrected_value")),
                    "corrected_value": corrected_value,
                    "corrected_unit": corrected_unit,
                    "action": "rejected_or_not_applicable",
                    "action_reason": "review_status_rejected_or_not_applicable",
                    "original_auto_value": "",
                    "final_value": "",
                    "reviewer": reviewer,
                    "reviewed_at": reviewed_at,
                    "reviewer_note": reviewer_note,
                    "source_row_label": source_row_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "evidence_crop_path": evidence_crop_path,
                }
            )
            unresolved_rows.append(
                {
                    "asset_package": ap,
                    "standard_metric": metric,
                    "year": year,
                    "problem_type": "rejected_or_not_applicable",
                    "value_issue_flags": issue_flags,
                    "raw_value_examples": raw_value_examples,
                    "recommendation": recommendation or "manual decision kept as rejected/not_applicable",
                    "source_row_label": source_row_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "evidence_crop_path": evidence_crop_path,
                }
            )
            continue

        # Effective correction candidate path.
        if not key_ok:
            app_rows.append(
                {
                    "asset_package": ap,
                    "standard_metric": metric,
                    "year": year,
                    "review_status": review_status,
                    "use_corrected_value": _norm(r.get("use_corrected_value")),
                    "corrected_value": corrected_value,
                    "corrected_unit": corrected_unit,
                    "action": "invalid_missing_key",
                    "action_reason": "cannot_resolve_asset_metric_year_key",
                    "original_auto_value": "",
                    "final_value": "",
                    "reviewer": reviewer,
                    "reviewed_at": reviewed_at,
                    "reviewer_note": reviewer_note,
                    "source_row_label": source_row_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "evidence_crop_path": evidence_crop_path,
                }
            )
            unresolved_rows.append(
                {
                    "asset_package": ap,
                    "standard_metric": metric,
                    "year": year,
                    "problem_type": "invalid_missing_key",
                    "value_issue_flags": issue_flags,
                    "raw_value_examples": raw_value_examples,
                    "recommendation": recommendation or "add year or explicit key fields",
                    "source_row_label": source_row_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "evidence_crop_path": evidence_crop_path,
                }
            )
            continue

        if not use_corr or not status_accept:
            app_rows.append(
                {
                    "asset_package": ap,
                    "standard_metric": metric,
                    "year": year,
                    "review_status": review_status,
                    "use_corrected_value": _norm(r.get("use_corrected_value")),
                    "corrected_value": corrected_value,
                    "corrected_unit": corrected_unit,
                    "action": "invalid_missing_corrected_value",
                    "action_reason": "use_corrected_value_false_or_review_status_not_accepted",
                    "original_auto_value": "",
                    "final_value": "",
                    "reviewer": reviewer,
                    "reviewed_at": reviewed_at,
                    "reviewer_note": reviewer_note,
                    "source_row_label": source_row_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "evidence_crop_path": evidence_crop_path,
                }
            )
            unresolved_rows.append(
                {
                    "asset_package": ap,
                    "standard_metric": metric,
                    "year": year,
                    "problem_type": "invalid_missing_corrected_value",
                    "value_issue_flags": issue_flags,
                    "raw_value_examples": raw_value_examples,
                    "recommendation": recommendation or "set use_corrected_value=true and review_status=corrected/accepted",
                    "source_row_label": source_row_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "evidence_crop_path": evidence_crop_path,
                }
            )
            continue

        if not corrected_value:
            app_rows.append(
                {
                    "asset_package": ap,
                    "standard_metric": metric,
                    "year": year,
                    "review_status": review_status,
                    "use_corrected_value": _norm(r.get("use_corrected_value")),
                    "corrected_value": corrected_value,
                    "corrected_unit": corrected_unit,
                    "action": "invalid_missing_corrected_value",
                    "action_reason": "corrected_value_empty",
                    "original_auto_value": "",
                    "final_value": "",
                    "reviewer": reviewer,
                    "reviewed_at": reviewed_at,
                    "reviewer_note": reviewer_note,
                    "source_row_label": source_row_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "evidence_crop_path": evidence_crop_path,
                }
            )
            unresolved_rows.append(
                {
                    "asset_package": ap,
                    "standard_metric": metric,
                    "year": year,
                    "problem_type": "corrected_value_empty",
                    "value_issue_flags": issue_flags,
                    "raw_value_examples": raw_value_examples,
                    "recommendation": recommendation or "fill corrected_value",
                    "source_row_label": source_row_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "evidence_crop_path": evidence_crop_path,
                }
            )
            continue

        manual_candidates.append(
            {
                "asset_package": ap,
                "standard_metric": metric,
                "year": year,
                "review_status": review_status,
                "use_corrected_value": _norm(r.get("use_corrected_value")),
                "corrected_value": corrected_value,
                "corrected_unit": corrected_unit,
                "reviewer": reviewer,
                "reviewed_at": reviewed_at,
                "reviewer_note": reviewer_note,
                "source_row_label": source_row_label,
                "source_table_index": source_table_index,
                "source_row_index": source_row_index,
                "evidence_crop_path": evidence_crop_path,
                "raw_value_examples": raw_value_examples,
                "value_issue_flags": issue_flags,
                "recommendation": recommendation,
            }
        )

    kept_manual, ignored_conflicts = _dedupe_manual_candidates(manual_candidates)
    for x in ignored_conflicts:
        app_rows.append(
            {
                "asset_package": _norm(x.get("asset_package")),
                "standard_metric": _norm(x.get("standard_metric")),
                "year": _norm(x.get("year")),
                "review_status": _norm(x.get("review_status")),
                "use_corrected_value": _norm(x.get("use_corrected_value")),
                "corrected_value": _norm(x.get("corrected_value")),
                "corrected_unit": _norm(x.get("corrected_unit")),
                "action": "conflict_ignored",
                "action_reason": _norm(x.get("action_reason")),
                "original_auto_value": "",
                "final_value": "",
                "reviewer": _norm(x.get("reviewer")),
                "reviewed_at": _norm(x.get("reviewed_at")),
                "reviewer_note": _norm(x.get("reviewer_note")),
                "source_row_label": _norm(x.get("source_row_label")),
                "source_table_index": _norm(x.get("source_table_index")),
                "source_row_index": _norm(x.get("source_row_index")),
                "evidence_crop_path": _norm(x.get("evidence_crop_path")),
            }
        )

    effective_correction_rows = len(kept_manual)
    applied_override_count = 0
    applied_new_manual_count = 0

    idx_map = {k: i for i, k in enumerate(base["_key"].tolist())}
    for m in kept_manual:
        k = f"{_norm(m['asset_package'])}|{_norm(m['standard_metric'])}|{_norm(m['year'])}"
        if k in idx_map:
            i = idx_map[k]
            original_auto = _norm(base.at[i, "value"])
            base.at[i, "final_value_source"] = "manual_corrected"
            base.at[i, "final_review_status"] = "corrected"
            base.at[i, "final_value"] = _norm(m["corrected_value"])
            base.at[i, "final_unit"] = _norm(m["corrected_unit"]) or _norm(base.at[i, "unit"])
            base.at[i, "final_note"] = "manual override applied"
            base.at[i, "corrected_value"] = _norm(m["corrected_value"])
            base.at[i, "corrected_unit"] = _norm(m["corrected_unit"])
            base.at[i, "reviewer"] = _norm(m["reviewer"])
            base.at[i, "reviewed_at"] = _norm(m["reviewed_at"])
            base.at[i, "reviewer_note"] = _norm(m["reviewer_note"])
            applied_override_count += 1
            app_rows.append(
                {
                    "asset_package": _norm(m["asset_package"]),
                    "standard_metric": _norm(m["standard_metric"]),
                    "year": _norm(m["year"]),
                    "review_status": _norm(m["review_status"]),
                    "use_corrected_value": _norm(m["use_corrected_value"]),
                    "corrected_value": _norm(m["corrected_value"]),
                    "corrected_unit": _norm(m["corrected_unit"]),
                    "action": "applied_override",
                    "action_reason": "matched_existing_auto_key",
                    "original_auto_value": original_auto,
                    "final_value": _norm(m["corrected_value"]),
                    "reviewer": _norm(m["reviewer"]),
                    "reviewed_at": _norm(m["reviewed_at"]),
                    "reviewer_note": _norm(m["reviewer_note"]),
                    "source_row_label": _norm(m["source_row_label"]),
                    "source_table_index": _norm(m["source_table_index"]),
                    "source_row_index": _norm(m["source_row_index"]),
                    "evidence_crop_path": _norm(m["evidence_crop_path"]),
                }
            )
        else:
            new_row = {
                "source_pdf": "",
                "asset_package": _norm(m["asset_package"]),
                "report_type": "",
                "data_usability_tier": "",
                "standard_metric": _norm(m["standard_metric"]),
                "year": _norm(m["year"]),
                "value": "",
                "unit": _norm(m["corrected_unit"]),
                "value_validation_status": "",
                "value_repair_applied": "",
                "source_row_label": _norm(m["source_row_label"]),
                "source_table_index": _norm(m["source_table_index"]),
                "source_row_index": _norm(m["source_row_index"]),
                "source_column": "",
                "evidence_crop_path": _norm(m["evidence_crop_path"]),
                "trace_note": "manual addition from review queue",
                "final_value_source": "manual_added",
                "final_review_status": "corrected",
                "final_value": _norm(m["corrected_value"]),
                "final_unit": _norm(m["corrected_unit"]),
                "final_note": "manual added new key",
                "original_auto_value": "",
                "original_auto_unit": "",
                "corrected_value": _norm(m["corrected_value"]),
                "corrected_unit": _norm(m["corrected_unit"]),
                "reviewer": _norm(m["reviewer"]),
                "reviewed_at": _norm(m["reviewed_at"]),
                "reviewer_note": _norm(m["reviewer_note"]),
            }
            base = pd.concat([base, pd.DataFrame([new_row])], ignore_index=True)
            idx_map[k] = len(base) - 1
            applied_new_manual_count += 1
            app_rows.append(
                {
                    "asset_package": _norm(m["asset_package"]),
                    "standard_metric": _norm(m["standard_metric"]),
                    "year": _norm(m["year"]),
                    "review_status": _norm(m["review_status"]),
                    "use_corrected_value": _norm(m["use_corrected_value"]),
                    "corrected_value": _norm(m["corrected_value"]),
                    "corrected_unit": _norm(m["corrected_unit"]),
                    "action": "applied_new_manual",
                    "action_reason": "manual_key_not_in_auto_table",
                    "original_auto_value": "",
                    "final_value": _norm(m["corrected_value"]),
                    "reviewer": _norm(m["reviewer"]),
                    "reviewed_at": _norm(m["reviewed_at"]),
                    "reviewer_note": _norm(m["reviewer_note"]),
                    "source_row_label": _norm(m["source_row_label"]),
                    "source_table_index": _norm(m["source_table_index"]),
                    "source_row_index": _norm(m["source_row_index"]),
                    "evidence_crop_path": _norm(m["evidence_crop_path"]),
                }
            )

    # Final de-dup safety, prioritize manual corrected/added then latest reviewed_at.
    base["_key"] = base.apply(lambda r: f"{_norm(r['asset_package'])}|{_norm(r['standard_metric'])}|{_norm(r['year'])}", axis=1)
    base["_pri_source"] = base["final_value_source"].map(
        lambda s: 3
        if _norm(s) == "manual_corrected"
        else (2 if _norm(s) == "manual_added" else 1)
    )
    base["_pri_reviewed_at"] = base["reviewed_at"].map(_parse_reviewed_at)
    base = (
        base.sort_values(
            by=["_key", "_pri_source", "_pri_reviewed_at"],
            ascending=[True, False, False],
            kind="mergesort",
        )
        .drop_duplicates(subset=["_key"], keep="first")
        .copy()
    )
    duplicate_key_count_final = int(base.groupby(["asset_package", "standard_metric", "year"], dropna=False).size().gt(1).sum())

    base = base.sort_values(by=["asset_package", "standard_metric", "year"], kind="mergesort").reset_index(drop=True)

    final_cols = [
        "source_pdf",
        "asset_package",
        "report_type",
        "data_usability_tier",
        "standard_metric",
        "year",
        "final_value",
        "final_unit",
        "final_value_source",
        "final_review_status",
        "original_auto_value",
        "original_auto_unit",
        "corrected_value",
        "corrected_unit",
        "value_validation_status",
        "value_repair_applied",
        "source_row_label",
        "source_table_index",
        "source_row_index",
        "source_column",
        "evidence_crop_path",
        "trace_note",
        "reviewer",
        "reviewed_at",
        "reviewer_note",
    ]
    for c in final_cols:
        if c not in base.columns:
            base[c] = ""
    final_df = base[final_cols].copy()

    app_cols = [
        "asset_package",
        "standard_metric",
        "year",
        "review_status",
        "use_corrected_value",
        "corrected_value",
        "corrected_unit",
        "action",
        "action_reason",
        "original_auto_value",
        "final_value",
        "reviewer",
        "reviewed_at",
        "reviewer_note",
        "source_row_label",
        "source_table_index",
        "source_row_index",
        "evidence_crop_path",
    ]
    app_df = pd.DataFrame(app_rows)
    for c in app_cols:
        if c not in app_df.columns:
            app_df[c] = ""
    app_df = app_df[app_cols].copy()

    unresolved_cols = [
        "asset_package",
        "standard_metric",
        "year",
        "problem_type",
        "value_issue_flags",
        "raw_value_examples",
        "recommendation",
        "source_row_label",
        "source_table_index",
        "source_row_index",
        "evidence_crop_path",
    ]
    unresolved_df = pd.DataFrame(unresolved_rows)
    for c in unresolved_cols:
        if c not in unresolved_df.columns:
            unresolved_df[c] = ""
    unresolved_df = unresolved_df[unresolved_cols].copy()

    ignored_pending_count = int((app_df["action"] == "ignored_pending").sum()) if not app_df.empty else 0
    rejected_or_not_applicable_count = (
        int((app_df["action"] == "rejected_or_not_applicable").sum()) if not app_df.empty else 0
    )
    unresolved_count = len(unresolved_df)
    final_rows = len(final_df)

    p06 = _safe_write_excel(final_df, delivery_dir / "06_最终核心财务指标.xlsx")
    p06a = _safe_write_excel(app_df, delivery_dir / "06A_人工修正应用明细.xlsx")
    p06b = _safe_write_excel(unresolved_df, delivery_dir / "06B_未解决问题清单.xlsx")
    p06c = _safe_write_text(_build_template_md(), delivery_dir / "06C_复核模板说明.md")

    return {
        "trusted_input_rows": trusted_input_rows,
        "manual_review_rows": manual_review_rows,
        "effective_correction_rows": effective_correction_rows,
        "applied_override_count": applied_override_count,
        "applied_new_manual_count": applied_new_manual_count,
        "ignored_pending_count": ignored_pending_count,
        "rejected_or_not_applicable_count": rejected_or_not_applicable_count,
        "unresolved_count": unresolved_count,
        "final_rows": final_rows,
        "duplicate_key_count_final": duplicate_key_count_final,
        "output_paths": {
            "06": str(p06),
            "06A": str(p06a),
            "06B": str(p06b),
            "06C": str(p06c),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply manual review corrections to build final delivery financial metrics.")
    parser.add_argument("--delivery-dir", default=str(DEFAULT_DELIVERY_DIR))
    args = parser.parse_args()

    result = apply_manual_review(Path(args.delivery_dir))
    print(f"trusted_input_rows: {result['trusted_input_rows']}")
    print(f"manual_review_rows: {result['manual_review_rows']}")
    print(f"effective_correction_rows: {result['effective_correction_rows']}")
    print(f"applied_override_count: {result['applied_override_count']}")
    print(f"applied_new_manual_count: {result['applied_new_manual_count']}")
    print(f"ignored_pending_count: {result['ignored_pending_count']}")
    print(f"rejected_or_not_applicable_count: {result['rejected_or_not_applicable_count']}")
    print(f"unresolved_count: {result['unresolved_count']}")
    print(f"final_rows: {result['final_rows']}")
    print(f"duplicate_key_count_final: {result['duplicate_key_count_final']}")
    print("output_paths:")
    for k, v in result["output_paths"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
