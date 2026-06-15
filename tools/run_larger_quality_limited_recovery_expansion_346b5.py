from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.larger_quality_limited_recovery_expansion_346b5 import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    DEFAULT_CONTROLLED_EXPANSION_QA_AUDIT_346B4Q_DIR,
    DEFAULT_CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_DIR,
    DEFAULT_CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_DIR,
    DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RECOVERY_RULE_REFINEMENT_PATCH_346B3R_DIR,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    EXPANSION_READINESS_JSON_FILE_NAME,
    GUARDRAIL_SUMMARY_JSON_FILE_NAME,
    GUARD_CSV_FILE_NAME,
    GUARD_JSON_FILE_NAME,
    HUMAN_CSV_FILE_NAME,
    HUMAN_JSON_FILE_NAME,
    LINEAGE_AUDIT_CSV_FILE_NAME,
    LINEAGE_AUDIT_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    RECOVERED_CSV_FILE_NAME,
    RECOVERED_JSON_FILE_NAME,
    RECOVERY_RESULTS_CSV_FILE_NAME,
    RECOVERY_RESULTS_JSON_FILE_NAME,
    RULE_CSV_FILE_NAME,
    RULE_JSON_FILE_NAME,
    SAFE_CSV_FILE_NAME,
    SAFE_JSON_FILE_NAME,
    SELECTED_ROWS_CSV_FILE_NAME,
    SELECTED_ROWS_JSON_FILE_NAME,
    SEMANTIC_DIST_CSV_FILE_NAME,
    SEMANTIC_DIST_JSON_FILE_NAME,
    STILL_CSV_FILE_NAME,
    STILL_JSON_FILE_NAME,
    UNIT_ACTION_CSV_FILE_NAME,
    UNIT_ACTION_JSON_FILE_NAME,
    VLM_CSV_FILE_NAME,
    VLM_JSON_FILE_NAME,
    build_larger_quality_limited_recovery_expansion_346b5,
)
from datefac.benchmark.larger_quality_limited_recovery_expansion_346b5_report import (  # noqa: E402
    write_csv,
    write_json,
)


def _truthy(value: str) -> bool:
    return str(value).strip().lower() not in {"0", "false", "no"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 346B5 Larger Quality-Limited Recovery Expansion.")
    parser.add_argument(
        "--full-structured-demo-export-package-345d-dir",
        default=str(DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR),
    )
    parser.add_argument(
        "--controlled-quality-limited-recovery-expansion-346b4-dir",
        default=str(DEFAULT_CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_DIR),
    )
    parser.add_argument(
        "--recovery-rule-refinement-patch-346b3r-dir",
        default=str(DEFAULT_RECOVERY_RULE_REFINEMENT_PATCH_346B3R_DIR),
    )
    parser.add_argument(
        "--controlled-expansion-replay-with-patched-rules-346b4r-dir",
        default=str(DEFAULT_CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_DIR),
    )
    parser.add_argument(
        "--controlled-expansion-qa-audit-346b4q-dir",
        default=str(DEFAULT_CONTROLLED_EXPANSION_QA_AUDIT_346B4Q_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--max-expansion-rows", type=int, default=1500)
    parser.add_argument("--selection-mode", default="priority_then_coverage")
    parser.add_argument("--require-346b4q-safe-to-larger-expansion", default="true")
    parser.add_argument("--strict-guardrails", default="true")
    parser.add_argument("--exclude-previous-controlled-batch", default="true")
    parser.add_argument("--include-image-bound-first", default="true")
    parser.add_argument("--include-json-md-context-bound", default="true")
    parser.add_argument("--max-context-chars", type=int, default=4000)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_larger_quality_limited_recovery_expansion_346b5(
        full_structured_demo_export_package_345d_dir=Path(args.full_structured_demo_export_package_345d_dir),
        controlled_quality_limited_recovery_expansion_346b4_dir=Path(args.controlled_quality_limited_recovery_expansion_346b4_dir),
        recovery_rule_refinement_patch_346b3r_dir=Path(args.recovery_rule_refinement_patch_346b3r_dir),
        controlled_expansion_replay_with_patched_rules_346b4r_dir=Path(args.controlled_expansion_replay_with_patched_rules_346b4r_dir),
        controlled_expansion_qa_audit_346b4q_dir=Path(args.controlled_expansion_qa_audit_346b4q_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        max_expansion_rows=args.max_expansion_rows,
        selection_mode=args.selection_mode,
        require_346b4q_safe_to_larger_expansion=_truthy(args.require_346b4q_safe_to_larger_expansion),
        strict_guardrails=_truthy(args.strict_guardrails),
        exclude_previous_controlled_batch=_truthy(args.exclude_previous_controlled_batch),
        include_image_bound_first=_truthy(args.include_image_bound_first),
        include_json_md_context_bound=_truthy(args.include_json_md_context_bound),
        max_context_chars=args.max_context_chars,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / SELECTED_ROWS_JSON_FILE_NAME, artifacts["selected_rows"])
    write_csv(output_dir / SELECTED_ROWS_CSV_FILE_NAME, artifacts["selected_rows"])
    write_json(output_dir / RECOVERY_RESULTS_JSON_FILE_NAME, artifacts["recovery_results_rows"])
    write_csv(output_dir / RECOVERY_RESULTS_CSV_FILE_NAME, artifacts["recovery_results_rows"])
    write_json(output_dir / RECOVERED_JSON_FILE_NAME, artifacts["recovered_candidate_rows"])
    write_csv(output_dir / RECOVERED_CSV_FILE_NAME, artifacts["recovered_candidate_rows"])
    write_json(output_dir / SAFE_JSON_FILE_NAME, artifacts["safe_recovered_candidate_rows"])
    write_csv(output_dir / SAFE_CSV_FILE_NAME, artifacts["safe_recovered_candidate_rows"])
    write_json(output_dir / STILL_JSON_FILE_NAME, artifacts["still_limited_rows"])
    write_csv(output_dir / STILL_CSV_FILE_NAME, artifacts["still_limited_rows"])
    write_json(output_dir / HUMAN_JSON_FILE_NAME, artifacts["needs_human_review_rows"])
    write_csv(output_dir / HUMAN_CSV_FILE_NAME, artifacts["needs_human_review_rows"])
    write_json(output_dir / RULE_JSON_FILE_NAME, artifacts["needs_rule_refinement_rows"])
    write_csv(output_dir / RULE_CSV_FILE_NAME, artifacts["needs_rule_refinement_rows"])
    write_json(output_dir / VLM_JSON_FILE_NAME, artifacts["needs_vlm_rows"])
    write_csv(output_dir / VLM_CSV_FILE_NAME, artifacts["needs_vlm_rows"])
    write_json(output_dir / GUARD_JSON_FILE_NAME, artifacts["false_positive_guardrail_rows"])
    write_csv(output_dir / GUARD_CSV_FILE_NAME, artifacts["false_positive_guardrail_rows"])
    write_json(output_dir / SEMANTIC_DIST_JSON_FILE_NAME, artifacts["semantic_class_distribution_rows"])
    write_csv(output_dir / SEMANTIC_DIST_CSV_FILE_NAME, artifacts["semantic_class_distribution_rows"])
    write_json(output_dir / UNIT_ACTION_JSON_FILE_NAME, artifacts["unit_action_distribution_rows"])
    write_csv(output_dir / UNIT_ACTION_CSV_FILE_NAME, artifacts["unit_action_distribution_rows"])
    write_json(output_dir / LINEAGE_AUDIT_JSON_FILE_NAME, artifacts["lineage_evidence_audit_rows"])
    write_csv(output_dir / LINEAGE_AUDIT_CSV_FILE_NAME, artifacts["lineage_evidence_audit_rows"])
    write_json(output_dir / GUARDRAIL_SUMMARY_JSON_FILE_NAME, artifacts["guardrail_summary"])
    write_json(output_dir / EXPANSION_READINESS_JSON_FILE_NAME, artifacts["expansion_readiness_report"])
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(artifacts["executive_summary_md"], encoding="utf-8")
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_md"], encoding="utf-8")
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(artifacts["next_plan_md"], encoding="utf-8")

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"larger_expansion_input_row_count: {manifest.get('larger_expansion_input_row_count', '')}")
    print(f"safe_recovered_candidate_count: {manifest.get('safe_recovered_candidate_count', '')}")
    print(f"false_positive_guardrail_hit_count: {manifest.get('false_positive_guardrail_hit_count', '')}")
    print(f"safe_to_qa_larger_expansion: {manifest.get('safe_to_qa_larger_expansion', '')}")
    print(f"recommended_next_step: {manifest.get('recommended_next_step', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
