from __future__ import annotations

import re
from typing import Any, Dict, List


NUM_RULE = re.compile(r"\(?-?[0-9][0-9,]*(?:\.[0-9]+)?%?\)?")
CASHFLOW_HINT_RULE = re.compile(r"(现金流|经营活动|投资活动|融资活动|自由现金流|净变动)")
LABEL_TAIL_RULE = re.compile(r"[\u4e00-\u9fffA-Za-z_、，,()（）/\-]+$")


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _is_numeric_only_row(label: str, nums: List[str]) -> bool:
    return (not label) and bool(nums)


def _is_table_noise_row(text: str) -> bool:
    t = _norm(text).lower()
    if not t:
        return True
    if t in {"table", "nan", "none"}:
        return True
    if "现金流量表" in t and len(NUM_RULE.findall(t)) >= 5:
        return True
    return False


def _label_and_nums(text: str) -> Dict[str, Any]:
    nums = [x for x in NUM_RULE.findall(text)]
    label = NUM_RULE.sub(" ", text)
    label = re.sub(r"\s+", " ", label).strip(" |")
    return {"label": label, "nums": nums}


def _split_leading_nums_and_rest(text: str) -> Dict[str, Any]:
    nums: List[str] = []
    idx = 0
    ln = len(text)
    while idx < ln:
        m = NUM_RULE.match(text, idx)
        if not m:
            break
        nums.append(m.group(0))
        idx = m.end()
        while idx < ln and text[idx].isspace():
            idx += 1
    rest_text = text[idx:].strip()
    return {"leading_nums": nums, "rest_text": rest_text}


def _flush_pending(
    pending: Dict[str, Any] | None,
    out_rows: List[Dict[str, Any]],
    trace_rows: List[Dict[str, Any]],
    source_row_index: int,
    action: str,
    reason: str,
) -> None:
    if pending is None:
        return
    row = dict(pending["meta"])
    row["row_text_repaired"] = f"{pending['label']} {' '.join(pending['nums'])}".strip()
    row["repaired_label"] = pending["label"]
    row["repaired_values"] = pending["nums"][:]
    row["repair_tags"] = pending.get("tags", "")
    out_rows.append(row)
    trace_rows.append(
        {
            "trace_step": pending["trace_step"],
            "action": action,
            "source_row_index": source_row_index,
            "reason": reason,
            "pending_label": pending["label"],
            "pending_nums": " | ".join(pending["nums"]),
            "result_row_text_repaired": row["row_text_repaired"],
            "repair_tags": row["repair_tags"],
        }
    )


def repair_row_fragments(
    cleaned_rows: List[Dict[str, Any]],
    expected_year_count: int = 5,
) -> Dict[str, Any]:
    repaired_rows: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    trace_rows: List[Dict[str, Any]] = []

    pending: Dict[str, Any] | None = None
    pending_label_waiting_values = False
    trace_step = 0

    for r in cleaned_rows:
        row_text = _norm(r.get("row_text_cleaned") or r.get("row_text") or "")
        row_index = int(r.get("row_index", -1))
        if _is_table_noise_row(row_text):
            warnings.append(
                {
                    "source_file": _norm(r.get("source_file")),
                    "extracted_table_id": _norm(r.get("extracted_table_id")),
                    "warning_code": "ROW_REPAIR_AMBIGUOUS",
                    "warning_message": f"skip table/noise row: {row_text[:120]}",
                }
            )
            continue

        parsed = _label_and_nums(row_text)
        label = parsed["label"]
        nums = parsed["nums"]
        is_cashflow_ctx = bool(CASHFLOW_HINT_RULE.search(row_text))

        trace_rows.append(
            {
                "trace_step": trace_step,
                "action": "READ_ROW",
                "source_row_index": row_index,
                "reason": "",
                "pending_label": pending["label"] if pending else "",
                "pending_nums": " | ".join(pending["nums"]) if pending else "",
                "result_row_text_repaired": "",
                "repair_tags": "",
                "row_text_raw": row_text,
                "parsed_label": label,
                "parsed_nums": " | ".join(nums),
            }
        )
        trace_step += 1

        # Pattern 2 + 3: leading nums then next label in same row.
        if label and nums and pending is not None:
            mix = _split_leading_nums_and_rest(row_text)
            leading_nums = mix["leading_nums"]
            rest_text = mix["rest_text"]
            rest = _label_and_nums(rest_text) if rest_text else {"label": "", "nums": []}
            rest_label = rest["label"]
            rest_nums = rest["nums"]
            if leading_nums and rest_label:
                need = max(expected_year_count - len(pending["nums"]), 0)
                take = leading_nums[:need]
                pending["nums"].extend(take)
                pending["tags"] = "ROW_REPAIRED_VALUES_BEFORE_LABEL"
                trace_rows.append(
                    {
                        "trace_step": trace_step,
                        "action": "APPLY_VALUES_BEFORE_LABEL",
                        "source_row_index": row_index,
                        "reason": "leading numbers used to complete previous pending label",
                        "pending_label": pending["label"],
                        "pending_nums": " | ".join(pending["nums"]),
                        "result_row_text_repaired": "",
                        "repair_tags": pending["tags"],
                    }
                )
                trace_step += 1
                if len(pending["nums"]) >= expected_year_count:
                    _flush_pending(
                        pending=pending,
                        out_rows=repaired_rows,
                        trace_rows=trace_rows,
                        source_row_index=row_index,
                        action="FLUSH_PENDING_COMPLETED",
                        reason="completed by leading values before next label",
                    )
                    pending = None
                if rest_nums and len(rest_nums) >= expected_year_count:
                    row2 = dict(r)
                    row2["row_text_repaired"] = f"{rest_label} {' '.join(rest_nums[:expected_year_count])}".strip()
                    row2["repaired_label"] = rest_label
                    row2["repaired_values"] = rest_nums[:expected_year_count]
                    row2["repair_tags"] = "ROW_REPAIRED_VALUES_BEFORE_LABEL"
                    repaired_rows.append(row2)
                    trace_rows.append(
                        {
                            "trace_step": trace_step,
                            "action": "DIRECT_KEEP_AFTER_VALUES_BEFORE_LABEL",
                            "source_row_index": row_index,
                            "reason": "remaining row parsed as direct label+values",
                            "pending_label": rest_label,
                            "pending_nums": " | ".join(rest_nums[:expected_year_count]),
                            "result_row_text_repaired": row2["row_text_repaired"],
                            "repair_tags": row2["repair_tags"],
                        }
                    )
                    trace_step += 1
                else:
                    pending = {
                        "label": rest_label,
                        "nums": rest_nums[:],
                        "meta": dict(r),
                        "tags": "ROW_REPAIRED_VALUES_BEFORE_LABEL",
                        "trace_step": trace_step,
                    }
                    pending_label_waiting_values = True
                trace_step += 1
                continue

        # Normal label + values row
        if label and nums:
            if pending is not None:
                _flush_pending(
                    pending=pending,
                    out_rows=repaired_rows,
                    trace_rows=trace_rows,
                    source_row_index=row_index,
                    action="FLUSH_PENDING_AMBIGUOUS",
                    reason="encounter new label+values before pending completed",
                )
                pending = None

            if len(nums) >= expected_year_count:
                row = dict(r)
                row["row_text_repaired"] = f"{label} {' '.join(nums[:expected_year_count])}".strip()
                row["repaired_label"] = label
                row["repaired_values"] = nums[:expected_year_count]
                row["repair_tags"] = ""
                repaired_rows.append(row)
                trace_rows.append(
                    {
                        "trace_step": trace_step,
                        "action": "DIRECT_KEEP_ROW",
                        "source_row_index": row_index,
                        "reason": "label+enough values",
                        "pending_label": label,
                        "pending_nums": " | ".join(nums[:expected_year_count]),
                        "result_row_text_repaired": row["row_text_repaired"],
                        "repair_tags": "",
                    }
                )
                trace_step += 1
                if len(nums) > expected_year_count:
                    warnings.append(
                        {
                            "source_file": _norm(r.get("source_file")),
                            "extracted_table_id": _norm(r.get("extracted_table_id")),
                            "warning_code": "ROW_REPAIR_AMBIGUOUS",
                            "warning_message": f"trailing tokens dropped: {nums[expected_year_count:]}",
                        }
                    )
                continue

            pending = {
                "label": label,
                "nums": nums[:],
                "meta": dict(r),
                "tags": "ROW_REPAIRED_CONTINUATION",
                "trace_step": trace_step,
            }
            pending_label_waiting_values = True
            trace_step += 1
            continue

        # Numeric-only continuation row
        if _is_numeric_only_row(label, nums):
            if pending is not None:
                need = max(expected_year_count - len(pending["nums"]), 0)
                take = nums[:need]
                pending["nums"].extend(take)
                pending["tags"] = "ROW_REPAIRED_CONTINUATION"
                trace_rows.append(
                    {
                        "trace_step": trace_step,
                        "action": "APPLY_NUMERIC_CONTINUATION",
                        "source_row_index": row_index,
                        "reason": "numeric-only row extends pending label",
                        "pending_label": pending["label"],
                        "pending_nums": " | ".join(pending["nums"]),
                        "result_row_text_repaired": "",
                        "repair_tags": pending["tags"],
                    }
                )
                trace_step += 1
                if len(pending["nums"]) >= expected_year_count:
                    _flush_pending(
                        pending=pending,
                        out_rows=repaired_rows,
                        trace_rows=trace_rows,
                        source_row_index=row_index,
                        action="FLUSH_PENDING_COMPLETED",
                        reason="completed by numeric continuation row",
                    )
                    pending = None
                    pending_label_waiting_values = False
                if len(nums) > need:
                    warnings.append(
                        {
                            "source_file": _norm(r.get("source_file")),
                            "extracted_table_id": _norm(r.get("extracted_table_id")),
                            "warning_code": "ROW_REPAIR_AMBIGUOUS",
                            "warning_message": f"unused continuation values: {nums[need:]}",
                        }
                    )
                continue

            warnings.append(
                {
                    "source_file": _norm(r.get("source_file")),
                    "extracted_table_id": _norm(r.get("extracted_table_id")),
                    "warning_code": "ROW_REPAIR_AMBIGUOUS",
                    "warning_message": f"numeric row without pending label: {row_text}",
                }
            )
            continue

        # label only row
        if label and not nums:
            if pending is not None:
                _flush_pending(
                    pending=pending,
                    out_rows=repaired_rows,
                    trace_rows=trace_rows,
                    source_row_index=row_index,
                    action="FLUSH_PENDING_AMBIGUOUS",
                    reason="label-only row interrupts pending",
                )
            pending = {
                "label": label,
                "nums": [],
                "meta": dict(r),
                "tags": "ROW_REPAIR_AMBIGUOUS",
                "trace_step": trace_step,
            }
            pending_label_waiting_values = True
            trace_step += 1
            continue

        # unmatched/noise
        if pending is not None and pending_label_waiting_values:
            _flush_pending(
                pending=pending,
                out_rows=repaired_rows,
                trace_rows=trace_rows,
                source_row_index=row_index,
                action="FLUSH_PENDING_AMBIGUOUS",
                reason="noise row interrupts pending",
            )
            pending = None
            pending_label_waiting_values = False

    if pending is not None:
        _flush_pending(
            pending=pending,
            out_rows=repaired_rows,
            trace_rows=trace_rows,
            source_row_index=-1,
            action="FLUSH_PENDING_EOF",
            reason="end of rows",
        )

    repaired_row_count = len([x for x in repaired_rows if _norm(x.get("repair_tags"))])
    return {
        "repaired_rows": repaired_rows,
        "warnings": warnings,
        "repaired_row_count": repaired_row_count,
        "row_repair_trace": trace_rows,
    }
