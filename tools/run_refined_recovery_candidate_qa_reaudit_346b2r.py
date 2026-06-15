from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.refined_recovery_candidate_qa_reaudit_346b2r import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    CANDIDATE_REAUDIT_CSV_FILE_NAME,
    CANDIDATE_REAUDIT_JSON_FILE_NAME,
    DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_MINERU_IMAGE_PATH_BINDING_FIX_346A2_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_DIR,
    DEFAULT_RECOVERY_CANDIDATE_QA_AUDIT_346B2_DIR,
    DEFAULT_RECOVERY_RULE_REFINEMENT_346B3_DIR,
    DEFAULT_VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_DIR,
    EVIDENCE_LINEAGE_CSV_FILE_NAME,
    EVIDENCE_LINEAGE_JSON_FILE_NAME,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    EXPANSION_READINESS_JSON_FILE_NAME,
    FALSE_POSITIVE_CSV_FILE_NAME,
    FALSE_POSITIVE_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    REAUDIT_SUMMARY_JSON_FILE_NAME,
    REGRESSION_CSV_FILE_NAME,
    REGRESSION_JSON_FILE_NAME,
    RISKY_CSV_FILE_NAME,
    RISKY_JSON_FILE_NAME,
    SAFE_CSV_FILE_NAME,
    SAFE_JSON_FILE_NAME,
    SEMANTIC_REAUDIT_CSV_FILE_NAME,
    SEMANTIC_REAUDIT_JSON_FILE_NAME,
    UNIT_REAUDIT_CSV_FILE_NAME,
    UNIT_REAUDIT_JSON_FILE_NAME,
    build_refined_recovery_candidate_qa_reaudit_346b2r,
)
from datefac.benchmark.refined_recovery_candidate_qa_reaudit_346b2r_report import (  # noqa: E402
    write_csv,
    write_json,
)


def _truthy(value: str) -> bool:
    return str(value).strip().lower() not in {"0", "false", "no"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 346B2R Refined Recovery Candidate QA Reaudit.")
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
    parser.add_argument(
        "--recovery-rule-refinement-346b3-dir",
        default=str(DEFAULT_RECOVERY_RULE_REFINEMENT_346B3_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--strict-reaudit", default="true")
    parser.add_argument("--require-lineage-preservation", default="true")
    parser.add_argument("--require-evidence-or-deterministic-proof", default="true")
    parser.add_argument("--safe-to-expand-risk-threshold", type=int, default=0)
    parser.add_argument("--max-context-chars", type=int, default=4000)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_refined_recovery_candidate_qa_reaudit_346b2r(
        full_structured_demo_export_package_345d_dir=Path(args.full_structured_demo_export_package_345d_dir),
        vision_assisted_table_evidence_pilot_346a_dir=Path(args.vision_assisted_table_evidence_pilot_346a_dir),
        mineru_image_path_binding_fix_346a2_dir=Path(args.mineru_image_path_binding_fix_346a2_dir),
        quality_limited_row_recovery_pilot_346b_dir=Path(args.quality_limited_row_recovery_pilot_346b_dir),
        recovery_candidate_qa_audit_346b2_dir=Path(args.recovery_candidate_qa_audit_346b2_dir),
        recovery_rule_refinement_346b3_dir=Path(args.recovery_rule_refinement_346b3_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        strict_reaudit=_truthy(args.strict_reaudit),
        require_lineage_preservation=_truthy(args.require_lineage_preservation),
        require_evidence_or_deterministic_proof=_truthy(args.require_evidence_or_deterministic_proof),
        safe_to_expand_risk_threshold=args.safe_to_expand_risk_threshold,
        max_context_chars=args.max_context_chars,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / CANDIDATE_REAUDIT_JSON_FILE_NAME, artifacts["candidate_reaudit_rows"])
    write_csv(output_dir / CANDIDATE_REAUDIT_CSV_FILE_NAME, artifacts["candidate_reaudit_rows"])
    write_json(output_dir / SAFE_JSON_FILE_NAME, artifacts["safe_candidate_rows"])
    write_csv(output_dir / SAFE_CSV_FILE_NAME, artifacts["safe_candidate_rows"])
    write_json(output_dir / RISKY_JSON_FILE_NAME, artifacts["risky_candidate_rows"])
    write_csv(output_dir / RISKY_CSV_FILE_NAME, artifacts["risky_candidate_rows"])
    write_json(output_dir / FALSE_POSITIVE_JSON_FILE_NAME, artifacts["false_positive_candidate_rows"])
    write_csv(output_dir / FALSE_POSITIVE_CSV_FILE_NAME, artifacts["false_positive_candidate_rows"])
    write_json(output_dir / SEMANTIC_REAUDIT_JSON_FILE_NAME, artifacts["semantic_class_reaudit_rows"])
    write_csv(output_dir / SEMANTIC_REAUDIT_CSV_FILE_NAME, artifacts["semantic_class_reaudit_rows"])
    write_json(output_dir / UNIT_REAUDIT_JSON_FILE_NAME, artifacts["unit_compatibility_reaudit_rows"])
    write_csv(output_dir / UNIT_REAUDIT_CSV_FILE_NAME, artifacts["unit_compatibility_reaudit_rows"])
    write_json(output_dir / REGRESSION_JSON_FILE_NAME, artifacts["false_positive_regression_rows"])
    write_csv(output_dir / REGRESSION_CSV_FILE_NAME, artifacts["false_positive_regression_rows"])
    write_json(output_dir / EVIDENCE_LINEAGE_JSON_FILE_NAME, artifacts["evidence_lineage_audit_rows"])
    write_csv(output_dir / EVIDENCE_LINEAGE_CSV_FILE_NAME, artifacts["evidence_lineage_audit_rows"])
    write_json(output_dir / EXPANSION_READINESS_JSON_FILE_NAME, artifacts["expansion_readiness_report"])
    write_json(output_dir / REAUDIT_SUMMARY_JSON_FILE_NAME, artifacts["reaudit_summary"])
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(artifacts["executive_summary_md"], encoding="utf-8")
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_md"], encoding="utf-8")
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(artifacts["next_plan_md"], encoding="utf-8")

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"input_refined_candidate_count: {manifest.get('input_refined_candidate_count', '')}")
    print(f"reaudit_candidate_count: {manifest.get('reaudit_candidate_count', '')}")
    print(f"reaudit_safe_candidate_count: {manifest.get('reaudit_safe_candidate_count', '')}")
    print(f"reaudit_false_positive_suspect_count: {manifest.get('reaudit_false_positive_suspect_count', '')}")
    print(f"false_positive_regression_fixed_count: {manifest.get('false_positive_regression_fixed_count', '')}")
    print(f"safe_to_expand_recovery: {manifest.get('safe_to_expand_recovery', '')}")
    print(f"recommended_next_step: {manifest.get('recommended_next_step', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
