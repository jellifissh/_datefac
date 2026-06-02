from __future__ import annotations

from typing import Any, Dict, List


NUMERIC_GUARDRAIL = (
    "You must not invent numbers, years, or provenance. "
    "You may only classify labels, units, and scope using the provided context."
)
TRUST_GUARDRAIL = (
    "Your output is semantic advice only. "
    "A later deterministic gate decides whether anything can become trusted."
)


def build_prompt_templates() -> List[Dict[str, Any]]:
    return [
        {
            "template_name": "label_level_alias_or_scope",
            "purpose": "Resolve deduplicated unknown labels into existing metric codes, out-of-scope, or context-needed buckets.",
            "prompt_text": (
                "You are assisting a financial table mapping benchmark.\n"
                "Decide only among the allowed actions and allowed metric codes.\n"
                f"{NUMERIC_GUARDRAIL}\n"
                f"{TRUST_GUARDRAIL}\n"
                "When evidence is insufficient, choose requires_table_context or requires_manual_review."
            ),
            "output_schema_name": "DateFacSemanticAdjudicatorOutput",
        },
        {
            "template_name": "candidate_level_context_review",
            "purpose": "Review table-context-heavy cases where row label, year columns, or unit context affect interpretation.",
            "prompt_text": (
                "Review the provided table context, row label, year columns, and unit context.\n"
                "Do not repair extraction or invent schema.\n"
                f"{NUMERIC_GUARDRAIL}\n"
                "Prefer requires_manual_review for invalid year or parse failures."
            ),
            "output_schema_name": "DateFacSemanticAdjudicatorOutput",
        },
        {
            "template_name": "unit_context_inference",
            "purpose": "Infer unit only when the evidence from table title, header, or row label is explicit and high-confidence.",
            "prompt_text": (
                "Focus on unit inference only.\n"
                "If explicit evidence is missing, set unit to null and source to unavailable.\n"
                f"{NUMERIC_GUARDRAIL}\n"
                "Do not infer metric code unless the label is also clearly identifiable."
            ),
            "output_schema_name": "DateFacSemanticAdjudicatorOutput",
        },
    ]


def render_prompt_markdown(templates: List[Dict[str, Any]]) -> str:
    lines = ["# LLM Prompt Templates 322C", ""]
    for item in templates:
        lines.extend(
            [
                f"## {item['template_name']}",
                "",
                f"Purpose: {item['purpose']}",
                "",
                item["prompt_text"],
                "",
                f"Output schema: {item['output_schema_name']}",
                "",
            ]
        )
    return "\n".join(lines)

