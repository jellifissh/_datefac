from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


NUM_RULE = re.compile(r"\(?-?[0-9][0-9,]*(?:\.[0-9]+)?%?\)?")


def _norm(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _tokenize_row(row_text: str) -> Tuple[str, List[str]]:
    text = _norm(row_text)
    nums = [x for x in NUM_RULE.findall(text)]
    label = NUM_RULE.sub(" ", text)
    label = re.sub(r"\s+", " ", label).strip(" |")
    return label, nums


def repair_row_fragments(
    cleaned_rows: List[Dict[str, Any]],
    expected_year_count: int = 5,
) -> Dict[str, Any]:
    repaired_rows: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    repaired_row_count = 0

    pending_label: str = ""
    pending_nums: List[str] = []
    pending_meta: Dict[str, Any] | None = None

    def flush_pending(reason: str = "") -> None:
        nonlocal pending_label, pending_nums, pending_meta
        if pending_meta is None:
            return
        row = dict(pending_meta)
        row["row_text_repaired"] = f"{pending_label} {' '.join(pending_nums)}".strip()
        row["repaired_label"] = pending_label
        row["repaired_values"] = pending_nums[:]
        row["repair_tags"] = reason
        repaired_rows.append(row)
        pending_label = ""
        pending_nums = []
        pending_meta = None

    for r in cleaned_rows:
        row_text = _norm(r.get("row_text_cleaned") or r.get("row_text") or "")
        label, nums = _tokenize_row(row_text)

        # pattern: label + values
        if label and nums:
            if pending_meta is not None:
                flush_pending("ROW_REPAIR_AMBIGUOUS")
            if len(nums) >= expected_year_count:
                row = dict(r)
                row["row_text_repaired"] = f"{label} {' '.join(nums[:expected_year_count])}".strip()
                row["repaired_label"] = label
                row["repaired_values"] = nums[:expected_year_count]
                row["repair_tags"] = ""
                repaired_rows.append(row)
                # keep trailing tokens as noise
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

            # incomplete -> pending
            pending_label = label
            pending_nums = nums[:]
            pending_meta = dict(r)
            continue

        # numeric-only continuation
        if not label and nums:
            if pending_meta is not None:
                need = max(expected_year_count - len(pending_nums), 0)
                take = nums[:need]
                pending_nums.extend(take)
                tag = "ROW_REPAIRED_CONTINUATION"
                if len(pending_nums) >= expected_year_count:
                    flush_pending(tag)
                    repaired_row_count += 1
                    # left values ignored
                    if len(nums) > need:
                        warnings.append(
                            {
                                "source_file": _norm(r.get("source_file")),
                                "extracted_table_id": _norm(r.get("extracted_table_id")),
                                "warning_code": "ROW_REPAIR_AMBIGUOUS",
                                "warning_message": f"unused continuation values: {nums[need:]}",
                            }
                        )
                else:
                    # still pending
                    continue
            else:
                # no pending label
                warnings.append(
                    {
                        "source_file": _norm(r.get("source_file")),
                        "extracted_table_id": _norm(r.get("extracted_table_id")),
                        "warning_code": "ROW_REPAIR_AMBIGUOUS",
                        "warning_message": f"numeric row without pending label: {row_text}",
                    }
                )
            continue

        # label-only row
        if label and not nums:
            if pending_meta is not None:
                flush_pending("ROW_REPAIR_AMBIGUOUS")
            pending_label = label
            pending_nums = []
            pending_meta = dict(r)
            continue

        # noise
        if pending_meta is not None:
            flush_pending("ROW_REPAIR_AMBIGUOUS")

    if pending_meta is not None:
        flush_pending("ROW_REPAIR_AMBIGUOUS")

    # pass-through rows without row_text_repaired
    for row in repaired_rows:
        vals = row.get("repaired_values", [])
        if isinstance(vals, list) and len(vals) >= expected_year_count:
            repaired_row_count += 0

    return {
        "repaired_rows": repaired_rows,
        "warnings": warnings,
        "repaired_row_count": repaired_row_count,
    }

