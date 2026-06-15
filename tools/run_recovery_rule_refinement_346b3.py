from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.recovery_rule_refinement_346b3 import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    CORRECTED_PER_SHARE_CSV_FILE_NAME,
    CORRECTED_PER_SHARE_JSON_FILE_NAME,
    CORRECTED_RATIO_CSV_FILE_NAME,
    CORRECTED_RATIO_JSON_FILE_NAME,
    DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_MINERU_IMAGE_PATH_BINDING_FIX_346A2_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_DIR,
    DEFAULT_RECOVERY_CANDIDATE_QA_AUDIT_346B2_DIR,
    DEFAULT_VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_DIR,
    DEMOTED_ROWS_CSV_FILE_NAME,
    DEMOTED_ROWS_JSON_FILE_NAME,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    EXPANSION_READINESS_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    PRESERVED_PERCENTAGE_CSV_FILE_NAME,
    PRESERVED_PERCENTAGE_JSON_FILE_NAME,
    REAUDIT_PREVIEW_CSV_FILE_NAME,
    REAUDIT_PREVIEW_JSON_FILE_NAME,
    REFINED_CANDIDATES_CSV_FILE_NAME,
    REFINED_CANDIDATES_JSON_FILE_NAME,
    REFINED_POLICY_JSON_FILE_NAME,
    REFINED_POLICY_MD_FILE_NAME,
    REFINED_SAFE_CSV_FILE_NAME,
    REFINED_SAFE_JSON_FILE_NAME,
    RULE_CHANGE_LOG_JSON_FILE_NAME,
    RULE_CHANGE_LOG_MD_FILE_NAME,
    build_recovery_rule_refinement_346b3,
)
from datefac.benchmark.recovery_rule_refinement_346b3_report import (  # noqa: E402
    write_csv,
    write_json,
)


def _truthy(value: str) -> bool:
    return str(value).strip().lower() not in {"0", "false", "no"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 346B3 Recovery Rule Refinement.")
    parser.add_argument(
        "--full-structured-demo-export-package-345d-dir",
        default=str(DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR),
    )
    parser.add_argument(
        "--vision-assisted-table-evidence-pilot-346a-dir",
        default=str(DEFAULT_VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_DIR),
    )
    parser.add_argument(
        "--mineru-image-path-binding-fix-346a2-dir",
        default=str(DEFAULT_MINERU_IMAGE_PATH_BINDING_FIX_346A2_DIR),
    )
    parser.add_argument(
        "--quality-limited-row-recovery-pilot-346b-dir",
        default=str(DEFAULT_QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_DIR),
    )
    parser.add_argument(
        "--recovery-candidate-qa-audit-346b2-dir",
        default=str(DEFAULT_RECOVERY_CANDIDATE_QA_AUDIT_346B2_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--strict-refinement", default="true")
    parser.add_argument("--preserve-safe-346b2-candidates", default="true")
    parser.add_argument("--demote-unresolved-risk", default="true")
    parser.add_argument("--max-context-chars", type=int, default=4000)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_recovery_rule_refinement_346b3(
        full_structured_demo_export_package_345d_dir=Path(args.full_structured_demo_export_package_345d_dir),
        vision_assisted_table_evidence_pilot_346a_dir=Path(args.vision_assisted_table_evidence_pilot_346a_dir),
        mineru_image_path_binding_fix_346a2_dir=Path(args.mineru_image_path_binding_fix_346a2_dir),
        quality_limited_row_recovery_pilot_346b_dir=Path(args.quality_limited_row_recovery_pilot_346b_dir),
        recovery_candidate_qa_audit_346b2_dir=Path(args.recovery_candidate_qa_audit_346b2_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        strict_refinement=_truthy(args.strict_refinement),
        preserve_safe_346b2_candidates=_truthy(args.preserve_safe_346b2_candidates),
        demote_unresolved_risk=_truthy(args.demote_unresolved_risk),
        max_context_chars=args.max_context_chars,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / REFINED_CANDIDATES_JSON_FILE_NAME, artifacts["refined_candidate_rows"])
    write_csv(output_dir / REFINED_CANDIDATES_CSV_FILE_NAME, artifacts["refined_candidate_rows"])
    write_json(output_dir / REFINED_SAFE_JSON_FILE_NAME, artifacts["refined_safe_candidate_rows"])
    write_csv(output_dir / REFINED_SAFE_CSV_FILE_NAME, artifacts["refined_safe_candidate_rows"])
    write_json(output_dir / CORRECTED_RATIO_JSON_FILE_NAME, artifacts["corrected_ratio_multiple_rows"])
    write_csv(output_dir / CORRECTED_RATIO_CSV_FILE_NAME, artifacts["corrected_ratio_multiple_rows"])
    write_json(output_dir / CORRECTED_PER_SHARE_JSON_FILE_NAME, artifacts["corrected_per_share_rows"])
    write_csv(output_dir / CORRECTED_PER_SHARE_CSV_FILE_NAME, artifacts["corrected_per_share_rows"])
    write_json(output_dir / PRESERVED_PERCENTAGE_JSON_FILE_NAME, artifacts["preserved_percentage_margin_rows"])
    write_csv(output_dir / PRESERVED_PERCENTAGE_CSV_FILE_NAME, artifacts["preserved_percentage_margin_rows"])
    write_json(output_dir / DEMOTED_ROWS_JSON_FILE_NAME, artifacts["demoted_rows"])
    write_csv(output_dir / DEMOTED_ROWS_CSV_FILE_NAME, artifacts["demoted_rows"])
    write_json(output_dir / REFINED_POLICY_JSON_FILE_NAME, artifacts["refined_unit_policy"])
    (output_dir / REFINED_POLICY_MD_FILE_NAME).write_text(artifacts["refined_unit_policy_md"], encoding="utf-8")
    write_json(output_dir / RULE_CHANGE_LOG_JSON_FILE_NAME, artifacts["rule_change_log_rows"])
    (output_dir / RULE_CHANGE_LOG_MD_FILE_NAME).write_text(artifacts["rule_change_log_md"], encoding="utf-8")
    write_json(output_dir / REAUDIT_PREVIEW_JSON_FILE_NAME, artifacts["reaudit_preview_rows"])
    write_csv(output_dir / REAUDIT_PREVIEW_CSV_FILE_NAME, artifacts["reaudit_preview_rows"])
    write_json(output_dir / EXPANSION_READINESS_JSON_FILE_NAME, artifacts["expansion_readiness_report"])
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(artifacts["executive_summary_md"], encoding="utf-8")
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_md"], encoding="utf-8")
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(artifacts["next_plan_md"], encoding="utf-8")

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"input_recovered_candidate_count: {manifest.get('input_recovered_candidate_count', '')}")
    print(f"refined_candidate_count: {manifest.get('refined_candidate_count', '')}")
    print(f"refined_safe_candidate_count: {manifest.get('refined_safe_candidate_count', '')}")
    print(f"remaining_false_positive_suspect_count: {manifest.get('remaining_false_positive_suspect_count', '')}")
    print(f"corrected_ratio_multiple_unit_count: {manifest.get('corrected_ratio_multiple_unit_count', '')}")
    print(f"corrected_per_share_unit_count: {manifest.get('corrected_per_share_unit_count', '')}")
    print(f"preserved_percentage_margin_unit_count: {manifest.get('preserved_percentage_margin_unit_count', '')}")
    print(f"safe_to_reaudit: {manifest.get('safe_to_reaudit', '')}")
    print(f"safe_to_expand_recovery: {manifest.get('safe_to_expand_recovery', '')}")
    print(f"recommended_next_step: {manifest.get('recommended_next_step', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
