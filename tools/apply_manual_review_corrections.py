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

TRUE_VALUES = {"true", "1", "yes", "y", "是", "对", "使用", "采用", "√"}
FALSE_VALUES = {"false", "0", "no", "n", "否", "不用", "不采用", ""}

STATUS_CORRECTED = {"corrected", "accepted", "修正", "已修正", "已确认", "确认", "通过", "accept", "ok"}
STATUS_REJECTED = {"rejected", "reject", "拒绝", "不采用", "错误"}
STATUS_NOT_APPLICABLE = {"not_applicable", "不适用", "非目标", "无需处理"}

YEAR_FIELDS = ["year", "value_year", "target_year", "source_column", "raw_value_examples"]
YEAR_TOKEN_PATTERN = re.compile(r"(20\d{2}[AE]?)", flags=re.IGNORECASE)


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _to_bool(v) -> bool:
    return _norm(v).lower() in TRUE_VALUES


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


def _safe_write_excel_multi(sheets: Dict[str, pd.DataFrame], path: Path) -> Path:
    final_path = path
    if path.exists():
        try:
            with open(path, "a", encoding="utf-8"):
                pass
        except PermissionError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = path.with_name(f"{path.stem}_copy_{ts}{path.suffix}")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(final_path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
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
    p01_list = sorted(delivery_dir.glob("01_*.xlsx"))
    p02_list = sorted(delivery_dir.glob("02_*.xlsx"))
    if not p01_list:
        raise FileNotFoundError(f"Required file missing: {delivery_dir}\\01_*.xlsx")
    if not p02_list:
        raise FileNotFoundError(f"Required file missing: {delivery_dir}\\02_*.xlsx")
    p01 = p01_list[0]
    p02 = p02_list[0]
    df01 = pd.read_excel(p01, engine="openpyxl").fillna("")
    df02 = pd.read_excel(p02, engine="openpyxl").fillna("")
    return df01, df02, p01, p02


def _normalized_col_key(name: str) -> str:
    s = _norm(name).lower()
    s = s.replace("_", "").replace("-", "").replace(" ", "")
    return s


def _match_candidate_columns(columns: List[str], canonical: str) -> List[str]:
    canon = _normalized_col_key(canonical)
    cands: List[str] = []
    for c in columns:
        key = _normalized_col_key(c)
        if not key:
            continue
        if key == canon:
            cands.append(c)
            continue
        # pandas duplicate columns: corrected_value.1 / .2 ...
        if key.startswith(canon + "."):
            cands.append(c)
            continue
        # loose aliases
        if canonical == "corrected_value":
            if key.startswith("usecorrected"):
                continue
            if key in {"correctedvalue", "correctedval", "corrected"} or ("corrected" in key and "value" in key):
                cands.append(c)
                continue
        if canonical == "corrected_unit":
            if key in {"correctedunit", "unitcorrected"} or ("corrected" in key and "unit" in key):
                cands.append(c)
                continue
        if canonical == "review_status":
            if key in {"reviewstatus", "status", "审核状态"} or ("review" in key and "status" in key):
                cands.append(c)
                continue
        if canonical == "use_corrected_value":
            if key in {"usecorrectedvalue", "usecorrected", "usecorrectedval"} or (
                "use" in key and "corrected" in key
            ):
                cands.append(c)
                continue
        if canonical == "reviewer_note":
            if key in {"reviewernote", "note", "comment"} or ("reviewer" in key and "note" in key):
                cands.append(c)
                continue
        if canonical == "reviewer":
            if key in {"reviewer", "reviewedby", "operator"}:
                cands.append(c)
                continue
        if canonical == "reviewed_at":
            if key in {"reviewedat", "reviewtime", "reviewdate"} or ("reviewed" in key and "at" in key):
                cands.append(c)
                continue
        if canonical == "year":
            if key in {"year", "valueyear", "targetyear"}:
                cands.append(c)
                continue
    # keep order and dedupe
    out: List[str] = []
    seen = set()
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _build_review_field_candidates(df02: pd.DataFrame) -> Dict[str, List[str]]:
    cols = [str(c) for c in df02.columns]
    targets = ["review_status", "corrected_value", "corrected_unit", "use_corrected_value", "reviewer_note", "reviewer", "reviewed_at", "year"]
    cand_map: Dict[str, List[str]] = {}
    for t in targets:
        cand_map[t] = _match_candidate_columns(cols, t)
    return cand_map


def _coalesce_value_from_candidates(row: pd.Series, candidates: List[str]) -> Tuple[str, str, str, str]:
    """
    Returns: (selected_value, selected_column, candidate_values_text, conflict_flags)
    """
    pairs: List[Tuple[str, str]] = []
    for c in candidates:
        v = _norm(row.get(c))
        pairs.append((c, v))
    non_empty = [(c, v) for c, v in pairs if v != ""]
    selected_value = non_empty[0][1] if non_empty else ""
    selected_col = non_empty[0][0] if non_empty else ""
    candidate_values_text = "|".join([f"{c}={v}" for c, v in pairs])
    conflict_flags = ""
    if len(non_empty) > 1:
        uniq_vals = list(dict.fromkeys([v for _, v in non_empty]))
        if len(uniq_vals) > 1:
            conflict_flags = "multi_candidate_conflict"
        else:
            conflict_flags = "multi_candidate_same_value"
    return selected_value, selected_col, candidate_values_text, conflict_flags


def _ensure_review_columns(df02: pd.DataFrame) -> pd.DataFrame:
    out = df02.copy()
    for c in REQUIRED_REVIEW_COLS + ["year", "value_year", "target_year", "source_column", "raw_value_examples"]:
        if c not in out.columns:
            out[c] = ""
    return out


def _normalize_review_status(v) -> Tuple[str, str]:
    s = _norm(v).lower()
    if not s:
        return "pending", "empty_as_pending"
    if s in STATUS_CORRECTED:
        return "corrected", "mapped_corrected"
    if s in STATUS_REJECTED:
        return "rejected", "mapped_rejected"
    if s in STATUS_NOT_APPLICABLE:
        return "not_applicable", "mapped_not_applicable"
    if s == "pending":
        return "pending", "pending"
    return "pending", "unrecognized_as_pending"


def _normalize_use_corrected(v) -> Tuple[bool, str]:
    s = _norm(v).lower()
    if s in TRUE_VALUES:
        return True, "mapped_true"
    if s in FALSE_VALUES:
        return False, "mapped_false"
    return False, "unrecognized_as_false"


def _collect_year_candidates(row: pd.Series) -> Dict[str, object]:
    explicit = _norm(row.get("year"))
    explicit_tokens = [x.upper() for x in YEAR_TOKEN_PATTERN.findall(explicit)]
    if explicit_tokens:
        explicit_tokens = list(dict.fromkeys(explicit_tokens))
    source_column = _norm(row.get("source_column"))
    raw_values = _norm(row.get("raw_value_examples"))
    value_year = _norm(row.get("value_year"))
    target_year = _norm(row.get("target_year"))

    inferred_tokens: List[str] = []
    for c in [value_year, target_year, source_column, raw_values]:
        for t in YEAR_TOKEN_PATTERN.findall(c):
            tu = t.upper()
            if tu not in inferred_tokens:
                inferred_tokens.append(tu)

    all_tokens = explicit_tokens[:] if explicit_tokens else inferred_tokens[:]
    selected = ""
    parse_status = ""
    parse_reason = ""

    if explicit_tokens:
        if len(explicit_tokens) == 1:
            selected = explicit_tokens[0]
            parse_status = "ok"
            parse_reason = "explicit_year_column"
        else:
            parse_status = "multi_year"
            parse_reason = "explicit_year_contains_multiple_tokens"
    else:
        if len(inferred_tokens) == 1:
            selected = inferred_tokens[0]
            parse_status = "ok"
            parse_reason = "inferred_single_year_from_context"
        elif len(inferred_tokens) > 1:
            parse_status = "multi_year"
            parse_reason = "multiple_year_candidates_in_context"
        else:
            parse_status = "missing_year"
            parse_reason = "no_year_token_found"

    return {
        "original_year": explicit,
        "source_column": source_column,
        "raw_value_examples": raw_values,
        "parsed_year_candidates": "|".join(all_tokens),
        "selected_year": selected,
        "parse_status": parse_status,
        "parse_reason": parse_reason,
    }


def _parse_reviewed_at(v) -> pd.Timestamp:
    s = _norm(v)
    if not s:
        return pd.Timestamp.min
    t = pd.to_datetime(s, errors="coerce")
    if pd.isna(t):
        return pd.Timestamp.min
    return t


def _dedupe_manual_candidates(cands: List[Dict[str, object]]) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    grouped: Dict[Tuple[str, str, str], List[Dict[str, object]]] = {}
    for c in cands:
        k = (_norm(c.get("asset_package")), _norm(c.get("standard_metric")), _norm(c.get("parsed_year")))
        grouped.setdefault(k, []).append(c)
    kept: List[Dict[str, object]] = []
    ignored: List[Dict[str, object]] = []
    for _, arr in grouped.items():
        arr_sorted = sorted(
            arr,
            key=lambda x: (
                _parse_reviewed_at(x.get("reviewed_at")),
                1 if _norm(x.get("corrected_value")) else 0,
            ),
            reverse=True,
        )
        kept.append(arr_sorted[0])
        for x in arr_sorted[1:]:
            y = x.copy()
            y["action"] = "conflict_ignored"
            y["action_reason"] = "same_key_multiple_manual_rows_keep_latest_reviewed_at"
            ignored.append(y)
    return kept, ignored


def _build_template_md() -> str:
    return (
        "# 复核模板说明\n\n"
        "## 1. 如何填写 02_人工复核指标队列.xlsx\n"
        "- 在每条需修正记录中填写：`review_status`, `use_corrected_value`, `corrected_value`, `corrected_unit`。\n"
        "- 建议同时填写：`reviewer`, `reviewed_at`, `reviewer_note`。\n"
        "- 强烈建议明确填写 `year` 列（例如 `2026E`），避免多年份歧义。\n\n"
        "## 2. review_status 可选值\n"
        "- corrected / accepted / 修正 / 已修正 / 已确认 / 确认 / 通过 / accept / ok\n"
        "- rejected / reject / 拒绝 / 不采用 / 错误\n"
        "- not_applicable / 不适用 / 非目标 / 无需处理\n"
        "- 空值视为 pending\n\n"
        "## 3. use_corrected_value 如何填写\n"
        "- True: TRUE/true/1/yes/y/是/对/使用/采用/√\n"
        "- False: FALSE/false/0/no/n/否/不用/不采用/空值\n\n"
        "## 4. corrected_value / corrected_unit 示例\n"
        "- corrected_value: 987654.321\n"
        "- corrected_unit: TEST 或 亿元 / % / 元\n\n"
        "## 5. 最终表覆盖规则\n"
        "- 唯一键：asset_package + standard_metric + year。\n"
        "- 命中同键：manual_corrected 覆盖 auto_trusted。\n"
        "- 无同键：manual_added 新增行。\n"
        "- 同键多条人工修正：优先 reviewed_at 最新。\n\n"
        "## 6. 注意\n"
        "- 不要直接改 01_自动可信核心指标.xlsx。\n"
        "- 必须通过 02 回写并运行本工具。\n"
    )


def apply_manual_review(delivery_dir: Path) -> Dict[str, object]:
    df01, df02_raw, p01, p02 = _read_required_inputs(delivery_dir)
    df02 = _ensure_review_columns(df02_raw)
    field_cand_map = _build_review_field_candidates(df02)

    trusted_input_rows = len(df01)
    manual_review_rows = len(df02)
    corrected_value_non_empty_rows = 0
    corrected_candidates = field_cand_map.get("corrected_value", [])
    if corrected_candidates:
        non_empty_mask = pd.Series(False, index=df02.index)
        for c in corrected_candidates:
            non_empty_mask = non_empty_mask | (df02[c].map(_norm) != "")
        corrected_value_non_empty_rows = int(non_empty_mask.sum())

    base = df01.copy()
    base_defaults = {
        "source_pdf": "",
        "report_type": "",
        "data_usability_tier": "",
        "unit": "",
        "value_validation_status": "",
        "value_repair_applied": "",
        "source_row_label": "",
        "source_table_index": "",
        "source_row_index": "",
        "source_column": "",
        "evidence_crop_path": "",
        "trace_note": "",
    }
    for c, d in base_defaults.items():
        if c not in base.columns:
            base[c] = d

    for c in ["asset_package", "standard_metric", "year", "value"]:
        if c not in base.columns:
            raise ValueError(f"trusted table missing required column: {c}")

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
    base["_key"] = base.apply(
        lambda r: f"{_norm(r['asset_package'])}|{_norm(r['standard_metric'])}|{_norm(r['year'])}",
        axis=1,
    )

    diagnosis_rows: List[Dict[str, object]] = []
    app_rows: List[Dict[str, object]] = []
    unresolved_rows: List[Dict[str, object]] = []
    key_parse_rows: List[Dict[str, object]] = []
    manual_candidates: List[Dict[str, object]] = []

    invalid_missing_key_count = 0
    invalid_missing_year_count = 0
    invalid_multi_year_count = 0

    for _, r in df02.iterrows():
        ap = _norm(r.get("asset_package"))
        sm = _norm(r.get("standard_metric"))
        corrected_value, corrected_value_col, corrected_value_candidate_values, corrected_value_conflict = _coalesce_value_from_candidates(
            r, field_cand_map.get("corrected_value", [])
        )
        corrected_unit, corrected_unit_col, _, corrected_unit_conflict = _coalesce_value_from_candidates(
            r, field_cand_map.get("corrected_unit", [])
        )
        raw_use, use_col, _, use_conflict = _coalesce_value_from_candidates(
            r, field_cand_map.get("use_corrected_value", [])
        )
        raw_status, status_col, _, status_conflict = _coalesce_value_from_candidates(
            r, field_cand_map.get("review_status", [])
        )
        reviewer, reviewer_col, _, reviewer_conflict = _coalesce_value_from_candidates(
            r, field_cand_map.get("reviewer", [])
        )
        reviewed_at, reviewed_at_col, _, reviewed_at_conflict = _coalesce_value_from_candidates(
            r, field_cand_map.get("reviewed_at", [])
        )
        reviewer_note, reviewer_note_col, _, reviewer_note_conflict = _coalesce_value_from_candidates(
            r, field_cand_map.get("reviewer_note", [])
        )
        year_val, year_col, _, year_conflict = _coalesce_value_from_candidates(r, field_cand_map.get("year", []))
        field_conflicts = [
            x
            for x in [
                corrected_value_conflict,
                corrected_unit_conflict,
                use_conflict,
                status_conflict,
                reviewer_conflict,
                reviewed_at_conflict,
                reviewer_note_conflict,
                year_conflict,
            ]
            if x
        ]
        field_conflict_flags = "|".join(dict.fromkeys(field_conflicts))
        source_row_label = _norm(r.get("source_row_label"))
        source_table_index = _norm(r.get("source_table_index"))
        source_row_index = _norm(r.get("source_row_index"))
        evidence_crop_path = _norm(r.get("evidence_crop_path"))
        issue_flags = _norm(r.get("value_issue_flags"))
        raw_value_examples = _norm(r.get("raw_value_examples"))
        recommendation = _norm(r.get("recommendation"))

        status_norm, status_reason = _normalize_review_status(raw_status)
        use_norm, use_reason = _normalize_use_corrected(raw_use)

        row_for_year = r.copy()
        row_for_year["year"] = year_val
        yinfo = _collect_year_candidates(row_for_year)
        parsed_year = _norm(yinfo["selected_year"])
        parse_status = _norm(yinfo["parse_status"])
        correction_key = f"{ap}|{sm}|{parsed_year}" if ap and sm and parsed_year else ""

        missing_fields = []
        if not ap:
            missing_fields.append("asset_package")
        if not sm:
            missing_fields.append("standard_metric")
        if not parsed_year:
            missing_fields.append("year")
        key_complete = len(missing_fields) == 0

        action = ""
        action_reason = ""
        how_to_fix = ""

        if status_norm == "pending":
            action = "ignored_pending"
            action_reason = "review_status_pending_or_empty"
            how_to_fix = "将 review_status 设为 corrected/accepted，并填写 corrected_value、year。"
        elif status_norm in {"rejected", "not_applicable"}:
            action = "rejected_or_not_applicable"
            action_reason = f"review_status_{status_norm}"
            how_to_fix = "如需写入最终表，请改为 corrected 并设置 use_corrected_value=True。"
        else:
            # corrected path
            if parse_status == "multi_year":
                action = "invalid_multi_year"
                action_reason = "multiple_year_candidates"
                invalid_multi_year_count += 1
                how_to_fix = "该复核行包含多个年份，请在 year 列明确填写目标年份，例如 2026E。"
            elif parse_status == "missing_year":
                action = "invalid_missing_year"
                action_reason = "cannot_parse_year"
                invalid_missing_year_count += 1
                how_to_fix = "缺少 year，无法构造唯一键 asset_package + standard_metric + year。"
            elif not ap or not sm:
                action = "invalid_missing_key"
                action_reason = "asset_or_metric_missing"
                invalid_missing_key_count += 1
                how_to_fix = "请补齐 asset_package 与 standard_metric。"
            elif not use_norm:
                action = "invalid_missing_corrected_value"
                action_reason = f"use_corrected_value_not_true({use_reason})"
                how_to_fix = "将 use_corrected_value 设置为 TRUE/是/1/√。"
            elif not corrected_value:
                action = "invalid_missing_corrected_value"
                action_reason = "corrected_value_empty"
                how_to_fix = "请填写 corrected_value。"
            else:
                action = "candidate_effective"
                action_reason = "ready_for_apply"
                how_to_fix = "无"
                manual_candidates.append(
                    {
                        "asset_package": ap,
                        "standard_metric": sm,
                        "parsed_year": parsed_year,
                        "review_status": status_norm,
                        "use_corrected_value": raw_use,
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

        key_parse_rows.append(yinfo)

        diagnosis_rows.append(
            {
                "asset_package": ap,
                "standard_metric": sm,
                "year": _norm(r.get("year")),
                "parsed_year": parsed_year,
                "correction_key": correction_key,
                "corrected_value": corrected_value,
                "corrected_unit": corrected_unit,
                "review_status": raw_status,
                "review_status_normalized": status_norm,
                "use_corrected_value": raw_use,
                "use_corrected_value_normalized": str(use_norm),
                "key_complete": key_complete,
                "missing_key_fields": "|".join(missing_fields),
                "action": action,
                "action_reason": action_reason,
                "enters_final_06": False,
                "how_to_fix": how_to_fix,
                "corrected_value_candidate_columns": "|".join(field_cand_map.get("corrected_value", [])),
                "corrected_value_candidate_values": corrected_value_candidate_values,
                "selected_corrected_value_column": corrected_value_col,
                "selected_corrected_value": corrected_value,
                "field_conflict_flags": field_conflict_flags,
            }
        )

        if action in {
            "ignored_pending",
            "rejected_or_not_applicable",
            "invalid_missing_key",
            "invalid_missing_year",
            "invalid_multi_year",
            "invalid_missing_corrected_value",
        }:
            app_rows.append(
                {
                    "asset_package": ap,
                    "standard_metric": sm,
                    "year": parsed_year,
                    "review_status": raw_status,
                    "use_corrected_value": raw_use,
                    "corrected_value": corrected_value,
                    "corrected_unit": corrected_unit,
                    "action": action,
                    "action_reason": action_reason,
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
                    "standard_metric": sm,
                    "year": parsed_year,
                    "problem_type": action,
                    "value_issue_flags": issue_flags,
                    "raw_value_examples": raw_value_examples,
                    "recommendation": recommendation or how_to_fix,
                    "source_row_label": source_row_label,
                    "source_table_index": source_table_index,
                    "source_row_index": source_row_index,
                    "evidence_crop_path": evidence_crop_path,
                }
            )

    kept_manual, ignored_conflicts = _dedupe_manual_candidates(manual_candidates)
    for x in ignored_conflicts:
        app_rows.append(
            {
                "asset_package": _norm(x.get("asset_package")),
                "standard_metric": _norm(x.get("standard_metric")),
                "year": _norm(x.get("parsed_year")),
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
        key = f"{_norm(m['asset_package'])}|{_norm(m['standard_metric'])}|{_norm(m['parsed_year'])}"
        if key in idx_map:
            i = idx_map[key]
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
            action = "applied_override"
            action_reason = "matched_existing_auto_key"
        else:
            new_row = {
                "source_pdf": "",
                "asset_package": _norm(m["asset_package"]),
                "report_type": "",
                "data_usability_tier": "",
                "standard_metric": _norm(m["standard_metric"]),
                "year": _norm(m["parsed_year"]),
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
            idx_map[key] = len(base) - 1
            applied_new_manual_count += 1
            original_auto = ""
            action = "applied_new_manual"
            action_reason = "manual_key_not_in_auto_table"

        app_rows.append(
            {
                "asset_package": _norm(m["asset_package"]),
                "standard_metric": _norm(m["standard_metric"]),
                "year": _norm(m["parsed_year"]),
                "review_status": _norm(m["review_status"]),
                "use_corrected_value": _norm(m["use_corrected_value"]),
                "corrected_value": _norm(m["corrected_value"]),
                "corrected_unit": _norm(m["corrected_unit"]),
                "action": action,
                "action_reason": action_reason,
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

    # Final de-dup safety
    base["_key"] = base.apply(
        lambda r: f"{_norm(r['asset_package'])}|{_norm(r['standard_metric'])}|{_norm(r['year'])}",
        axis=1,
    )
    base["_pri_source"] = base["final_value_source"].map(
        lambda s: 3 if _norm(s) == "manual_corrected" else (2 if _norm(s) == "manual_added" else 1)
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
    duplicate_key_count_final = int(
        base.groupby(["asset_package", "standard_metric", "year"], dropna=False).size().gt(1).sum()
    )
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

    # Update diagnosis with final enter status
    enter_map = set(
        final_df.apply(
            lambda r: f"{_norm(r['asset_package'])}|{_norm(r['standard_metric'])}|{_norm(r['year'])}",
            axis=1,
        ).tolist()
    )
    for r in diagnosis_rows:
        k = _norm(r.get("correction_key"))
        r["enters_final_06"] = bool(k and k in enter_map and _norm(r.get("action")) in {"candidate_effective"})
        if _norm(r.get("action")) == "candidate_effective":
            r["action"] = "applied_override_or_new_manual"
            r["action_reason"] = "applied_after_key_match_or_add"

    diagnosis_df = pd.DataFrame(diagnosis_rows)
    parse_df = pd.DataFrame(key_parse_rows)
    non_applied_df = diagnosis_df[~diagnosis_df["enters_final_06"]].copy() if not diagnosis_df.empty else pd.DataFrame()
    if not non_applied_df.empty:
        grouped = (
            non_applied_df.groupby("action_reason", dropna=False)
            .agg(
                count=("action_reason", "size"),
                example_asset_package=("asset_package", "first"),
                example_standard_metric=("standard_metric", "first"),
                example_corrected_value=("corrected_value", "first"),
                how_to_fix=("how_to_fix", "first"),
            )
            .reset_index()
            .rename(columns={"action_reason": "reason"})
        )
    else:
        grouped = pd.DataFrame(
            columns=[
                "reason",
                "count",
                "example_asset_package",
                "example_standard_metric",
                "example_corrected_value",
                "how_to_fix",
            ]
        )

    fill_examples_df = pd.DataFrame(
        [
            {
                "field_name": "review_status",
                "accepted_values": "corrected/accepted/修正/已修正/已确认/确认/通过/accept/ok; rejected/reject/拒绝/不采用/错误; not_applicable/不适用/非目标/无需处理; empty->pending",
                "bad_examples": "done, pass1, ???",
                "good_examples": "corrected, 已修正, accepted",
            },
            {
                "field_name": "use_corrected_value",
                "accepted_values": "TRUE/true/1/yes/y/是/对/使用/采用/√; FALSE/false/0/no/n/否/不用/不采用/empty",
                "bad_examples": "apply, maybe",
                "good_examples": "TRUE, 是, 1, √",
            },
            {
                "field_name": "year",
                "accepted_values": "2024, 2024A, 2025A, 2026E, 2027E, 2028E (single year only)",
                "bad_examples": "2025A/2026E (multi-year), empty",
                "good_examples": "2026E",
            },
            {
                "field_name": "corrected_value",
                "accepted_values": "non-empty numeric/text agreed by reviewer",
                "bad_examples": "empty while use_corrected_value=TRUE",
                "good_examples": "987654.321",
            },
        ]
    )

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
    p06d = _safe_write_excel_multi(
        {
            "corrected_rows_diagnosis": diagnosis_df,
            "non_applied_reasons": grouped,
            "key_parse_details": parse_df,
            "fill_examples": fill_examples_df,
        },
        delivery_dir / "06D_人工复核回写诊断.xlsx",
    )

    return {
        "trusted_input_rows": trusted_input_rows,
        "manual_review_rows": manual_review_rows,
        "corrected_value_non_empty_rows": corrected_value_non_empty_rows,
        "effective_correction_rows": len(kept_manual),
        "applied_override_count": applied_override_count,
        "applied_new_manual_count": applied_new_manual_count,
        "ignored_pending_count": ignored_pending_count,
        "rejected_or_not_applicable_count": rejected_or_not_applicable_count,
        "invalid_missing_key_count": invalid_missing_key_count,
        "invalid_missing_year_count": invalid_missing_year_count,
        "invalid_multi_year_count": invalid_multi_year_count,
        "unresolved_count": unresolved_count,
        "final_rows": final_rows,
        "duplicate_key_count_final": duplicate_key_count_final,
        "diagnosis_report_path": str(p06d),
        "output_paths": {
            "06": str(p06),
            "06A": str(p06a),
            "06B": str(p06b),
            "06C": str(p06c),
            "06D": str(p06d),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply manual review corrections to final delivery financial metrics.")
    parser.add_argument("--delivery-dir", default=str(DEFAULT_DELIVERY_DIR))
    args = parser.parse_args()

    result = apply_manual_review(Path(args.delivery_dir))
    print(f"trusted_input_rows: {result['trusted_input_rows']}")
    print(f"manual_review_rows: {result['manual_review_rows']}")
    print(f"corrected_value_non_empty_rows: {result['corrected_value_non_empty_rows']}")
    print(f"effective_correction_rows: {result['effective_correction_rows']}")
    print(f"applied_override_count: {result['applied_override_count']}")
    print(f"applied_new_manual_count: {result['applied_new_manual_count']}")
    print(f"ignored_pending_count: {result['ignored_pending_count']}")
    print(f"rejected_or_not_applicable_count: {result['rejected_or_not_applicable_count']}")
    print(f"invalid_missing_key_count: {result['invalid_missing_key_count']}")
    print(f"invalid_missing_year_count: {result['invalid_missing_year_count']}")
    print(f"invalid_multi_year_count: {result['invalid_multi_year_count']}")
    print(f"unresolved_count: {result['unresolved_count']}")
    print(f"final_rows: {result['final_rows']}")
    print(f"duplicate_key_count_final: {result['duplicate_key_count_final']}")
    print(f"diagnosis_report_path: {result['diagnosis_report_path']}")
    print("output_paths:")
    for k, v in result["output_paths"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
