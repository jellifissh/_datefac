from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.controlled_expansion_qa_audit_346b4q import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    CANDIDATE_QA_CSV_FILE_NAME,
    CANDIDATE_QA_JSON_FILE_NAME,
    DEFAULT_CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_DIR,
    DEFAULT_CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_DIR,
    DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RECOVERY_RULE_REFINEMENT_PATCH_346B3R_DIR,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    FALSE_POSITIVE_CSV_FILE_NAME,
    FALSE_POSITIVE_JSON_FILE_NAME,
    LINEAGE_CSV_FILE_NAME,
    LINEAGE_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    PATCH_QA_CSV_FILE_NAME,
    PATCH_QA_JSON_FILE_NAME,
    READINESS_JSON_FILE_NAME,
    RISKY_CSV_FILE_NAME,
    RISKY_JSON_FILE_NAME,
    SAFE_CSV_FILE_NAME,
    SAFE_JSON_FILE_NAME,
    SEMANTIC_UNIT_CSV_FILE_NAME,
    SEMANTIC_UNIT_JSON_FILE_NAME,
    SUMMARY_JSON_FILE_NAME,
    build_controlled_expansion_qa_audit_346b4q,
)
from datefac.benchmark.controlled_expansion_qa_audit_346b4q_report import (  # noqa: E402
    write_csv,
    write_json,
)


def _truthy(value: str) -> bool:
    return str(value).strip().lower() not in {"0", "false", "no"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 346B4Q Controlled Expansion QA Audit.")
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
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--strict-qa", default="true")
    parser.add_argument("--audit-patch-applied-rows", default="true")
    parser.add_argument("--require-same-row-set-proof", default="true")
    parser.add_argument("--require-lineage-preservation", default="true")
    parser.add_argument("--require-evidence-or-deterministic-proof", default="true")
    parser.add_argument("--safe-to-larger-expansion-risk-threshold", type=int, default=0)
    parser.add_argument("--max-context-chars", type=int, default=4000)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_controlled_expansion_qa_audit_346b4q(
        full_structured_demo_export_package_345d_dir=Path(args.full_structured_demo_export_package_345d_dir),
        controlled_quality_limited_recovery_expansion_346b4_dir=Path(args.controlled_quality_limited_recovery_expansion_346b4_dir),
        recovery_rule_refinement_patch_346b3r_dir=Path(args.recovery_rule_refinement_patch_346b3r_dir),
        controlled_expansion_replay_with_patched_rules_346b4r_dir=Path(args.controlled_expansion_replay_with_patched_rules_346b4r_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        strict_qa=_truthy(args.strict_qa),
        audit_patch_applied_rows=_truthy(args.audit_patch_applied_rows),
        require_same_row_set_proof=_truthy(args.require_same_row_set_proof),
        require_lineage_preservation=_truthy(args.require_lineage_preservation),
        require_evidence_or_deterministic_proof=_truthy(args.require_evidence_or_deterministic_proof),
        safe_to_larger_expansion_risk_threshold=args.safe_to_larger_expansion_risk_threshold,
        max_context_chars=args.max_context_chars,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / CANDIDATE_QA_JSON_FILE_NAME, artifacts["candidate_qa_rows"])
    write_csv(output_dir / CANDIDATE_QA_CSV_FILE_NAME, artifacts["candidate_qa_rows"])
    write_json(output_dir / SAFE_JSON_FILE_NAME, artifacts["qa_safe_candidate_rows"])
    write_csv(output_dir / SAFE_CSV_FILE_NAME, artifacts["qa_safe_candidate_rows"])
    write_json(output_dir / RISKY_JSON_FILE_NAME, artifacts["qa_risky_candidate_rows"])
    write_csv(output_dir / RISKY_CSV_FILE_NAME, artifacts["qa_risky_candidate_rows"])
    write_json(output_dir / FALSE_POSITIVE_JSON_FILE_NAME, artifacts["false_positive_candidate_rows"])
    write_csv(output_dir / FALSE_POSITIVE_CSV_FILE_NAME, artifacts["false_positive_candidate_rows"])
    write_json(output_dir / PATCH_QA_JSON_FILE_NAME, artifacts["patch_applied_row_qa_rows"])
    write_csv(output_dir / PATCH_QA_CSV_FILE_NAME, artifacts["patch_applied_row_qa_rows"])
    write_json(output_dir / SEMANTIC_UNIT_JSON_FILE_NAME, artifacts["semantic_unit_recheck_rows"])
    write_csv(output_dir / SEMANTIC_UNIT_CSV_FILE_NAME, artifacts["semantic_unit_recheck_rows"])
    write_json(output_dir / LINEAGE_JSON_FILE_NAME, artifacts["lineage_evidence_audit_rows"])
    write_csv(output_dir / LINEAGE_CSV_FILE_NAME, artifacts["lineage_evidence_audit_rows"])
    write_json(output_dir / READINESS_JSON_FILE_NAME, artifacts["larger_expansion_readiness_report"])
    write_json(output_dir / SUMMARY_JSON_FILE_NAME, artifacts["reaudit_summary"])
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(artifacts["executive_summary_md"], encoding="utf-8")
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_md"], encoding="utf-8")
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(artifacts["next_plan_md"], encoding="utf-8")

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"replay_input_row_count: {manifest.get('replay_input_row_count', '')}")
    print(f"qa_audited_candidate_count: {manifest.get('qa_audited_candidate_count', '')}")
    print(f"qa_safe_candidate_count: {manifest.get('qa_safe_candidate_count', '')}")
    print(f"qa_false_positive_suspect_count: {manifest.get('qa_false_positive_suspect_count', '')}")
    print(f"patch_applied_qa_pass_count: {manifest.get('patch_applied_qa_pass_count', '')}")
    print(f"qa_safe_to_larger_expansion: {manifest.get('qa_safe_to_larger_expansion', '')}")
    print(f"recommended_next_step: {manifest.get('recommended_next_step', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
