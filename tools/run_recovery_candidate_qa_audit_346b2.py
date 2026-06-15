from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.recovery_candidate_qa_audit_346b2 import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_MINERU_IMAGE_PATH_BINDING_FIX_346A2_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_QUALITY_LIMITED_ROW_RECOVERY_PILOT_346B_DIR,
    DEFAULT_VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_DIR,
    EVIDENCE_STRENGTH_DIST_CSV_FILE_NAME,
    EVIDENCE_STRENGTH_DIST_JSON_FILE_NAME,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    EXPANSION_READINESS_JSON_FILE_NAME,
    FALSE_POSITIVE_CSV_FILE_NAME,
    FALSE_POSITIVE_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEEDS_HUMAN_TRIAGE_CSV_FILE_NAME,
    NEEDS_HUMAN_TRIAGE_JSON_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    REAUDIT_SUMMARY_JSON_FILE_NAME,
    RECOVERED_CANDIDATE_AUDIT_CSV_FILE_NAME,
    RECOVERED_CANDIDATE_AUDIT_JSON_FILE_NAME,
    RISKY_RECOVERED_CSV_FILE_NAME,
    RISKY_RECOVERED_JSON_FILE_NAME,
    RULE_REFINEMENT_CSV_FILE_NAME,
    RULE_REFINEMENT_JSON_FILE_NAME,
    SAFE_RECOVERED_CSV_FILE_NAME,
    SAFE_RECOVERED_JSON_FILE_NAME,
    SEMANTIC_CLASS_DIST_CSV_FILE_NAME,
    SEMANTIC_CLASS_DIST_JSON_FILE_NAME,
    STILL_LIMITED_TRIAGE_CSV_FILE_NAME,
    STILL_LIMITED_TRIAGE_JSON_FILE_NAME,
    UNIT_REPAIR_AUDIT_CSV_FILE_NAME,
    UNIT_REPAIR_AUDIT_JSON_FILE_NAME,
    build_recovery_candidate_qa_audit_346b2,
)
from datefac.benchmark.recovery_candidate_qa_audit_346b2_report import (  # noqa: E402
    write_csv,
    write_json,
)


def _truthy(value: str) -> bool:
    return str(value).strip().lower() not in {"0", "false", "no"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 346B2 Recovery Candidate QA Audit.")
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
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--strict-audit", default="true")
    parser.add_argument("--sample-needs-human-review", default="true")
    parser.add_argument("--sample-still-limited", default="true")
    parser.add_argument("--max-context-chars", type=int, default=4000)
    parser.add_argument("--safe-to-expand-risk-threshold", type=int, default=0)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_recovery_candidate_qa_audit_346b2(
        full_structured_demo_export_package_345d_dir=Path(args.full_structured_demo_export_package_345d_dir),
        vision_assisted_table_evidence_pilot_346a_dir=Path(args.vision_assisted_table_evidence_pilot_346a_dir),
        mineru_image_path_binding_fix_346a2_dir=Path(args.mineru_image_path_binding_fix_346a2_dir),
        quality_limited_row_recovery_pilot_346b_dir=Path(args.quality_limited_row_recovery_pilot_346b_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        strict_audit=_truthy(args.strict_audit),
        sample_needs_human_review=_truthy(args.sample_needs_human_review),
        sample_still_limited=_truthy(args.sample_still_limited),
        max_context_chars=args.max_context_chars,
        safe_to_expand_risk_threshold=args.safe_to_expand_risk_threshold,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / RECOVERED_CANDIDATE_AUDIT_JSON_FILE_NAME, artifacts["recovered_candidate_audit_rows"])
    write_csv(output_dir / RECOVERED_CANDIDATE_AUDIT_CSV_FILE_NAME, artifacts["recovered_candidate_audit_rows"])
    write_json(output_dir / SAFE_RECOVERED_JSON_FILE_NAME, artifacts["safe_recovered_candidate_rows"])
    write_csv(output_dir / SAFE_RECOVERED_CSV_FILE_NAME, artifacts["safe_recovered_candidate_rows"])
    write_json(output_dir / RISKY_RECOVERED_JSON_FILE_NAME, artifacts["risky_recovered_candidate_rows"])
    write_csv(output_dir / RISKY_RECOVERED_CSV_FILE_NAME, artifacts["risky_recovered_candidate_rows"])
    write_json(output_dir / FALSE_POSITIVE_JSON_FILE_NAME, artifacts["false_positive_suspect_rows"])
    write_csv(output_dir / FALSE_POSITIVE_CSV_FILE_NAME, artifacts["false_positive_suspect_rows"])
    write_json(output_dir / UNIT_REPAIR_AUDIT_JSON_FILE_NAME, artifacts["unit_repair_audit_rows"])
    write_csv(output_dir / UNIT_REPAIR_AUDIT_CSV_FILE_NAME, artifacts["unit_repair_audit_rows"])
    write_json(output_dir / SEMANTIC_CLASS_DIST_JSON_FILE_NAME, artifacts["metric_semantic_class_distribution_rows"])
    write_csv(output_dir / SEMANTIC_CLASS_DIST_CSV_FILE_NAME, artifacts["metric_semantic_class_distribution_rows"])
    write_json(output_dir / EVIDENCE_STRENGTH_DIST_JSON_FILE_NAME, artifacts["evidence_strength_distribution_rows"])
    write_csv(output_dir / EVIDENCE_STRENGTH_DIST_CSV_FILE_NAME, artifacts["evidence_strength_distribution_rows"])
    write_json(output_dir / NEEDS_HUMAN_TRIAGE_JSON_FILE_NAME, artifacts["needs_human_review_triage_rows"])
    write_csv(output_dir / NEEDS_HUMAN_TRIAGE_CSV_FILE_NAME, artifacts["needs_human_review_triage_rows"])
    write_json(output_dir / STILL_LIMITED_TRIAGE_JSON_FILE_NAME, artifacts["still_limited_triage_rows"])
    write_csv(output_dir / STILL_LIMITED_TRIAGE_CSV_FILE_NAME, artifacts["still_limited_triage_rows"])
    write_json(output_dir / RULE_REFINEMENT_JSON_FILE_NAME, artifacts["rule_refinement_candidate_rows"])
    write_csv(output_dir / RULE_REFINEMENT_CSV_FILE_NAME, artifacts["rule_refinement_candidate_rows"])
    write_json(output_dir / EXPANSION_READINESS_JSON_FILE_NAME, artifacts["expansion_readiness_report"])
    write_json(output_dir / REAUDIT_SUMMARY_JSON_FILE_NAME, artifacts["reaudit_summary"])
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(artifacts["executive_summary_md"], encoding="utf-8")
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_md"], encoding="utf-8")
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(artifacts["next_plan_md"], encoding="utf-8")

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"audited_recovered_candidate_count: {manifest.get('audited_recovered_candidate_count', '')}")
    print(f"safe_recovered_candidate_count: {manifest.get('safe_recovered_candidate_count', '')}")
    print(f"risky_recovered_candidate_count: {manifest.get('risky_recovered_candidate_count', '')}")
    print(f"false_positive_suspect_count: {manifest.get('false_positive_suspect_count', '')}")
    print(f"safe_to_expand_recovery: {manifest.get('safe_to_expand_recovery', '')}")
    print(f"recommended_next_step: {manifest.get('recommended_next_step', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
