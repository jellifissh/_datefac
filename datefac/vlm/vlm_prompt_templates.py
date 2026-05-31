from __future__ import annotations

from typing import Any, Dict, List


def build_vlm_rerun_prompt_321a(summary: Dict[str, Any], rerun_worklist: List[Dict[str, Any]]) -> str:
    decision = summary.get("global_vlm_quality_decision", "")
    table_count = summary.get("table_output_count", 0)
    corrupted_rate = summary.get("corrupted_label_rate", 0.0)
    numeric_rate = summary.get("numeric_parse_success_rate", 0.0)

    lines: List[str] = [
        "# 321A VLM Re-run Prompt",
        "",
        "Please re-recognize the provided financial table image and output strict JSON only.",
        "",
        "## Why Re-run",
        f"- Current 321A quality decision: `{decision}`",
        f"- Table outputs reviewed: `{table_count}`",
        f"- Corrupted label rate: `{corrupted_rate:.4f}`",
        f"- Numeric parse success rate: `{numeric_rate:.4f}`",
        "",
        "## Hard Requirements",
        "- Preserve all Chinese text exactly as seen in the image.",
        "- Never replace Chinese with `?`, repeated question marks, pinyin, or English translation.",
        "- If a Chinese label cannot be read, output `null` and add warning `UNREADABLE_LABEL`.",
        "- Output strict JSON only. No Markdown fences. No explanation.",
        "- Preserve year suffixes exactly, including `A` and `E` such as `2024A`, `2025A`, `2026E`.",
        "- Do not guess missing cells. Use `null` when uncertain.",
        "- Keep negative numbers correct. Parentheses negatives must become negative `normalized_value`.",
        "- Preserve units and currency exactly when visible.",
        "",
        "## Required JSON Fields",
        "- `is_table`",
        "- `table_title`",
        "- `unit`",
        "- `currency`",
        "- `columns`",
        "- `warnings`",
        "- `rows`",
        "",
        "Each row must contain:",
        "- `row_index`",
        "- `metric_name_raw`",
        "- `metric_name_cn`",
        "- `values`",
        "",
        "Each value object must contain:",
        "- `column`",
        "- `raw_value`",
        "- `normalized_value`",
        "",
        "## Output Schema Example",
        "```json",
        "{",
        '  "is_table": true,',
        '  "table_title": "现金流量表",',
        '  "unit": "百万元",',
        '  "currency": null,',
        '  "columns": ["2024A", "2025A", "2026E", "2027E", "2028E"],',
        '  "warnings": [],',
        '  "rows": [',
        "    {",
        '      "row_index": 0,',
        '      "metric_name_raw": "经营活动现金流",',
        '      "metric_name_cn": "经营活动现金流",',
        '      "values": [',
        '        {"column": "2024A", "raw_value": "92464", "normalized_value": 92464},',
        '        {"column": "2025A", "raw_value": "61522", "normalized_value": 61522},',
        '        {"column": "2026E", "raw_value": "87447", "normalized_value": 87447},',
        '        {"column": "2027E", "raw_value": "89923", "normalized_value": 89923},',
        '        {"column": "2028E", "raw_value": "87288", "normalized_value": 87288}',
        "      ]",
        "    }",
        "  ]",
        "}",
        "```",
        "",
        "## Tables To Re-run",
    ]

    if rerun_worklist:
        for item in rerun_worklist[:20]:
            lines.append(
                f"- `{item.get('table_folder', '')}` | issue: `{item.get('main_issue', '')}` | action: `{item.get('recommended_action', '')}`"
            )
    else:
        lines.append("- No current rerun items. Keep this template for future VLM runs.")

    lines.extend(
        [
            "",
            "## Final Reminder",
            "- Return JSON only.",
            "- If any label is unreadable, use `null` plus `UNREADABLE_LABEL` warning instead of question marks.",
        ]
    )
    return "\n".join(lines) + "\n"
