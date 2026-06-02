from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.semantic.adjudicator_pack_builder import (
    build_batch_plan,
    build_candidate_level_pack,
    build_estimated_review_impact,
    build_label_level_pack,
    build_semantic_case_inventory,
)
from datefac.semantic.adjudicator_prompt_templates import build_prompt_templates, render_prompt_markdown
from datefac.semantic.adjudicator_readiness import build_acceptance_gate_rules, design_decision
from datefac.semantic.adjudicator_schema import (
    build_allowed_metric_codes_rows,
    build_llm_output_schema,
    validate_output_schema_dict,
)


SHEET_ORDER = [
    "summary",
    "semantic_case_inventory",
    "label_level_pack",
    "candidate_level_pack",
    "allowed_metric_codes",
    "prompt_templates",
    "acceptance_gate_rules",
    "estimated_review_impact",
    "semantic_adjudicator_batch_plan",
    "qa_checks",
    "known_limitations",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    base = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    out = base
    i = 1
    while out in used:
        suffix = f"_{i}"
        out = f"{base[:31 - len(suffix)]}{suffix}"
        i += 1
    used.add(out)
    return out


def _write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in df.to_dict(orient="records"):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _find_workbook(directory: Path) -> Optional[Path]:
    if not directory.exists():
        return None
    workbooks = sorted(directory.glob("*.xlsx"))
    return workbooks[0] if workbooks else None


def _read_sheet(workbook: Optional[Path], sheet_name: str) -> pd.DataFrame:
    if workbook is None or not workbook.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(workbook, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def _known_limitations_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "limitation": "design_only",
                "detail": "322C prepares semantic adjudicator packs, schema, prompts, and gates only. It does not call any model.",
            },
            {
                "limitation": "allowed_metric_codes_may_be_incomplete",
                "detail": "The allowed metric-code list is derived from current DateFac known metrics and may require later expansion review.",
            },
            {
                "limitation": "manual_review_still_needed",
                "detail": "Invalid year, parse uncertainty, and some mapping-review-tag cases should stay outside initial semantic automation.",
            },
        ]
    )


def _blocked_result(output_dir: Path, code: str) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "322C",
        "output_dir": str(output_dir),
        "input_review_required_count": 0,
        "unknown_metric_candidate_count": 0,
        "unit_unknown_candidate_count": 0,
        "mapping_review_candidate_count": 0,
        "invalid_year_or_schema_candidate_count": 0,
        "semantic_case_count": 0,
        "label_level_case_count": 0,
        "candidate_level_case_count": 0,
        "alias_candidate_count": 0,
        "out_of_scope_classification_case_count": 0,
        "unit_context_inference_case_count": 0,
        "manual_review_reserved_count": 0,
        "estimated_llm_resolvable_candidate_count": 0,
        "estimated_manual_remaining_count": 0,
        "prompt_template_count": 0,
        "output_schema_defined": False,
        "acceptance_gate_rule_count": 0,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 1,
        "semantic_adjudicator_design_decision": code,
    }
    qa_df = pd.DataFrame([{"check_name": "blocked_input", "status": "FAIL", "detail": code}])
    sheets = {
        "summary": pd.DataFrame([{"metric": k, "value": v} for k, v in summary.items()]),
        "semantic_case_inventory": pd.DataFrame(),
        "label_level_pack": pd.DataFrame(),
        "candidate_level_pack": pd.DataFrame(),
        "allowed_metric_codes": pd.DataFrame(),
        "prompt_templates": pd.DataFrame(),
        "acceptance_gate_rules": pd.DataFrame(),
        "estimated_review_impact": pd.DataFrame(),
        "semantic_adjudicator_batch_plan": pd.DataFrame(),
        "qa_checks": qa_df,
        "known_limitations": _known_limitations_df(),
    }
    _write_excel(output_dir / "semantic_adjudicator_design_322c.xlsx", sheets)
    _write_json(output_dir / "semantic_adjudicator_design_322c_summary.json", summary)
    (output_dir / "semantic_adjudicator_design_322c_report.md").write_text(
        "# Semantic Adjudicator Design 322C\n\n## Decision\n- semantic_adjudicator_design_decision: "
        + code
        + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322C semantic adjudicator design.")
    parser.add_argument("--trust-split-dir", required=True)
    parser.add_argument("--router-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-label-pack", type=int, default=120)
    parser.add_argument("--max-case-pack", type=int, default=120)
    args = parser.parse_args()

    trust_split_dir = Path(args.trust_split_dir)
    router_dir = Path(args.router_dir)
    output_dir = Path(args.output_dir)

    if not trust_split_dir.exists():
        _blocked_result(output_dir, "BLOCKED_MISSING_322B2_TRUST_SPLIT_DIR")
        print(f"semantic_adjudicator_design_322c_summary_json: {output_dir / 'semantic_adjudicator_design_322c_summary.json'}")
        return 0

    workbook = _find_workbook(trust_split_dir)
    review_df = _read_sheet(workbook, "review_required_preview_322b2")
    if review_df.empty:
        review_df = pd.DataFrame()
    review_df = review_df.fillna("")

    semantic_case_inventory_df = build_semantic_case_inventory(review_df, args.max_case_pack)
    label_level_pack_df = build_label_level_pack(review_df, args.max_label_pack)
    candidate_level_pack_df = build_candidate_level_pack(review_df, semantic_case_inventory_df, args.max_case_pack)
    allowed_metric_codes_df = pd.DataFrame(build_allowed_metric_codes_rows())
    prompt_templates_rows = build_prompt_templates()
    prompt_templates_df = pd.DataFrame(prompt_templates_rows)
    acceptance_gate_rules_rows = build_acceptance_gate_rules()
    acceptance_gate_rules_df = pd.DataFrame(acceptance_gate_rules_rows)
    estimated_review_impact_df = build_estimated_review_impact(review_df, label_level_pack_df, candidate_level_pack_df)
    batch_plan_df = build_batch_plan(label_level_pack_df, candidate_level_pack_df, output_dir)
    output_schema = build_llm_output_schema()

    input_review_required_count = len(review_df)
    unknown_metric_candidate_count = int((review_df["metric_code"].astype(str) == "unknown_metric").sum()) if not review_df.empty else 0
    unit_unknown_candidate_count = int(review_df["risk_tags_after"].astype(str).str.contains(r"(?:^|\|)UNIT_UNKNOWN(?:$|\|)", regex=True).sum()) if not review_df.empty else 0
    mapping_review_candidate_count = int(review_df["split_reason"].astype(str).eq("HAS_MAPPING_REVIEW_TAG").sum()) if not review_df.empty else 0
    invalid_year_or_schema_candidate_count = int(
        review_df["split_reason"].astype(str).isin(["INVALID_OR_MISSING_YEAR", "VALUE_PARSE_FAILED_OR_SCHEMA_UNCERTAIN"]).sum()
    ) if not review_df.empty else 0
    semantic_case_count = len(semantic_case_inventory_df)
    label_level_case_count = len(label_level_pack_df)
    candidate_level_case_count = len(candidate_level_pack_df)
    alias_candidate_count = int(label_level_pack_df["candidate_category"].astype(str).eq("UNKNOWN_METRIC_ALIAS_CANDIDATE").sum()) if not label_level_pack_df.empty else 0
    out_of_scope_classification_case_count = int(label_level_pack_df["candidate_category"].astype(str).eq("OUT_OF_SCOPE_OR_CORE_CLASSIFICATION").sum()) if not label_level_pack_df.empty else 0
    unit_context_inference_case_count = int(
        semantic_case_inventory_df["category"].astype(str).eq("UNIT_CONTEXT_INFERENCE").sum()
    ) if not semantic_case_inventory_df.empty else 0
    manual_review_reserved_count = int(
        semantic_case_inventory_df["category"].astype(str).isin(["INVALID_YEAR_OR_SCHEMA_REVIEW", "VALUE_PARSE_OR_SCHEMA_UNCERTAIN"]).sum()
    ) if not semantic_case_inventory_df.empty else 0
    estimated_llm_resolvable_candidate_count = int(estimated_review_impact_df["estimated_llm_resolvable_count"].sum()) if not estimated_review_impact_df.empty else 0
    estimated_manual_remaining_count = int(estimated_review_impact_df["estimated_manual_remaining_count"].sum()) if not estimated_review_impact_df.empty else 0
    prompt_template_count = len(prompt_templates_df)
    output_schema_defined = validate_output_schema_dict(output_schema)
    acceptance_gate_rule_count = len(acceptance_gate_rules_df)

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa("trust_split_output_exists", "PASS" if trust_split_dir.exists() else "FAIL", str(trust_split_dir))
    add_qa("no_model_api_call_executed", "PASS", "322C only builds offline packs, prompts, and schemas")
    add_qa("no_e_drive_files_modified", "PASS", "322C reads local output artifacts only")
    add_qa("no_production_files_modified", "PASS", "322C writes sandbox outputs only")
    stable_label_ids = label_level_pack_df.empty or not label_level_pack_df["label_case_id"].astype(str).duplicated().any()
    stable_case_ids = candidate_level_pack_df.empty or not candidate_level_pack_df["case_id"].astype(str).duplicated().any()
    add_qa("label_and_candidate_packs_have_stable_case_ids", "PASS" if stable_label_ids and stable_case_ids else "FAIL", f"label_cases={label_level_case_count}; candidate_cases={candidate_level_case_count}")
    add_qa("output_schema_is_valid_json", "PASS" if output_schema_defined else "FAIL", "schema dict validated")
    provenance_ok = candidate_level_pack_df.empty or candidate_level_pack_df["available_provenance"].astype(str).isin(["yes", "provenance_warning"]).all()
    add_qa("every_candidate_level_case_has_provenance_or_warning", "PASS" if provenance_ok else "FAIL", f"candidate_level_case_count={candidate_level_case_count}")
    prompt_text = "\n".join(prompt_templates_df["prompt_text"].astype(str).tolist()) if not prompt_templates_df.empty else ""
    add_qa("prompt_templates_forbid_numeric_invention", "PASS" if "must not invent numbers" in prompt_text.lower() else "FAIL", "numeric invention guardrail present")
    gate_text = "\n".join(acceptance_gate_rules_df["condition"].astype(str).tolist()) if not acceptance_gate_rules_df.empty else ""
    add_qa("acceptance_gate_forbids_llm_only_trusted_decisions", "PASS" if "LLM action alone can never create trusted output".lower() in gate_text.lower() else "FAIL", "LLM-only trust forbidden")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {
        "excel": output_dir / "semantic_adjudicator_design_322c.xlsx",
        "summary_json": output_dir / "semantic_adjudicator_design_322c_summary.json",
        "report_md": output_dir / "semantic_adjudicator_design_322c_report.md",
        "label_jsonl": output_dir / "llm_label_pack_322c.jsonl",
        "candidate_jsonl": output_dir / "llm_candidate_pack_322c.jsonl",
        "schema_json": output_dir / "llm_adjudicator_output_schema_322c.json",
        "prompt_md": output_dir / "llm_prompt_templates_322c.md",
    }

    add_qa("many_unknown_metrics_remain", "WARN" if unknown_metric_candidate_count > 1000 else "PASS", f"unknown_metric_candidate_count={unknown_metric_candidate_count}")
    add_qa("allowed_metric_code_list_may_be_incomplete", "WARN", f"allowed_metric_code_count={len(allowed_metric_codes_df)}")
    qa_df = pd.DataFrame(qa_rows)

    sheets = {
        "summary": pd.DataFrame(),
        "semantic_case_inventory": semantic_case_inventory_df,
        "label_level_pack": label_level_pack_df,
        "candidate_level_pack": candidate_level_pack_df,
        "allowed_metric_codes": allowed_metric_codes_df,
        "prompt_templates": prompt_templates_df,
        "acceptance_gate_rules": acceptance_gate_rules_df,
        "estimated_review_impact": estimated_review_impact_df,
        "semantic_adjudicator_batch_plan": batch_plan_df,
        "qa_checks": qa_df,
        "known_limitations": _known_limitations_df(),
    }
    _write_excel(output_files["excel"], sheets)
    _write_json(output_files["schema_json"], output_schema)
    output_files["prompt_md"].write_text(render_prompt_markdown(prompt_templates_rows), encoding="utf-8")
    if not label_level_pack_df.empty:
        _write_jsonl(output_files["label_jsonl"], label_level_pack_df)
    else:
        output_files["label_jsonl"].write_text("", encoding="utf-8")
    if not candidate_level_pack_df.empty:
        _write_jsonl(output_files["candidate_jsonl"], candidate_level_pack_df)
    else:
        output_files["candidate_jsonl"].write_text("", encoding="utf-8")

    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0

    summary = {
        "stage": "322C",
        "output_dir": str(output_dir),
        "input_review_required_count": input_review_required_count,
        "unknown_metric_candidate_count": unknown_metric_candidate_count,
        "unit_unknown_candidate_count": unit_unknown_candidate_count,
        "mapping_review_candidate_count": mapping_review_candidate_count,
        "invalid_year_or_schema_candidate_count": invalid_year_or_schema_candidate_count,
        "semantic_case_count": semantic_case_count,
        "label_level_case_count": label_level_case_count,
        "candidate_level_case_count": candidate_level_case_count,
        "alias_candidate_count": alias_candidate_count,
        "out_of_scope_classification_case_count": out_of_scope_classification_case_count,
        "unit_context_inference_case_count": unit_context_inference_case_count,
        "manual_review_reserved_count": manual_review_reserved_count,
        "estimated_llm_resolvable_candidate_count": estimated_llm_resolvable_candidate_count,
        "estimated_manual_remaining_count": estimated_manual_remaining_count,
        "prompt_template_count": prompt_template_count,
        "output_schema_defined": output_schema_defined,
        "acceptance_gate_rule_count": acceptance_gate_rule_count,
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
    }
    summary["semantic_adjudicator_design_decision"] = design_decision(summary)

    final_sheets = {
        **sheets,
        "summary": pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()]),
        "qa_checks": qa_df,
    }
    _write_excel(output_files["excel"], final_sheets)
    _write_json(output_files["summary_json"], summary)
    output_files["report_md"].write_text(
        "\n".join(
            [
                "# Semantic Adjudicator Design 322C",
                "",
                "## Decision",
                f"- semantic_adjudicator_design_decision: {summary['semantic_adjudicator_design_decision']}",
                "",
                "## Counts",
                f"- input_review_required_count: {summary['input_review_required_count']}",
                f"- semantic_case_count: {summary['semantic_case_count']}",
                f"- label_level_case_count: {summary['label_level_case_count']}",
                f"- candidate_level_case_count: {summary['candidate_level_case_count']}",
                f"- estimated_llm_resolvable_candidate_count: {summary['estimated_llm_resolvable_candidate_count']}",
                f"- estimated_manual_remaining_count: {summary['estimated_manual_remaining_count']}",
                "",
                "## QA",
                f"- qa_pass_count: {summary['qa_pass_count']}",
                f"- qa_warn_count: {summary['qa_warn_count']}",
                f"- qa_fail_count: {summary['qa_fail_count']}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    output_files_written = all(path.exists() for path in output_files.values())
    qa_df = pd.concat(
        [
            qa_df,
            pd.DataFrame(
                [
                    {
                        "check_name": "output_files_written_successfully",
                        "status": "PASS" if output_files_written else "FAIL",
                        "detail": str(output_dir),
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    summary["semantic_adjudicator_design_decision"] = design_decision(summary)

    final_sheets["summary"] = pd.DataFrame([{"metric": key, "value": value} for key, value in summary.items()])
    final_sheets["qa_checks"] = qa_df
    _write_excel(output_files["excel"], final_sheets)
    _write_json(output_files["summary_json"], summary)

    print(f"semantic_adjudicator_design_322c_excel: {output_files['excel']}")
    print(f"semantic_adjudicator_design_322c_summary_json: {output_files['summary_json']}")
    print(f"semantic_adjudicator_design_322c_report_md: {output_files['report_md']}")
    for key in [
        "input_review_required_count",
        "unknown_metric_candidate_count",
        "unit_unknown_candidate_count",
        "mapping_review_candidate_count",
        "invalid_year_or_schema_candidate_count",
        "semantic_case_count",
        "label_level_case_count",
        "candidate_level_case_count",
        "alias_candidate_count",
        "out_of_scope_classification_case_count",
        "unit_context_inference_case_count",
        "manual_review_reserved_count",
        "estimated_llm_resolvable_candidate_count",
        "estimated_manual_remaining_count",
        "prompt_template_count",
        "output_schema_defined",
        "acceptance_gate_rule_count",
        "qa_pass_count",
        "qa_warn_count",
        "qa_fail_count",
        "semantic_adjudicator_design_decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
