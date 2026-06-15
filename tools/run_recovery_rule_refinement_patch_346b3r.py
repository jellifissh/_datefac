from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.recovery_rule_refinement_patch_346b3r import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    DEFAULT_CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_DIR,
    DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RECOVERY_RULE_REFINEMENT_346B3_DIR,
    DEFAULT_REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_DIR,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    NON_PATCHABLE_CSV_FILE_NAME,
    NON_PATCHABLE_JSON_FILE_NAME,
    PATCHED_POLICY_PREVIEW_JSON_FILE_NAME,
    PATCHED_POLICY_PREVIEW_MD_FILE_NAME,
    PATCHABLE_CSV_FILE_NAME,
    PATCHABLE_JSON_FILE_NAME,
    PATCH_SAFETY_CSV_FILE_NAME,
    PATCH_SAFETY_JSON_FILE_NAME,
    READY_DECISION_346B3R,
    REPLAY_READINESS_JSON_FILE_NAME,
    SEMANTIC_PATCHES_CSV_FILE_NAME,
    SEMANTIC_PATCHES_JSON_FILE_NAME,
    UNIT_PATCHES_CSV_FILE_NAME,
    UNIT_PATCHES_JSON_FILE_NAME,
    UNKNOWN_AUDIT_CSV_FILE_NAME,
    UNKNOWN_AUDIT_JSON_FILE_NAME,
    build_recovery_rule_refinement_patch_346b3r,
)
from datefac.benchmark.recovery_rule_refinement_patch_346b3r_report import (  # noqa: E402
    write_csv,
    write_json,
)


def _truthy(value: str) -> bool:
    return str(value).strip().lower() not in {"0", "false", "no"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 346B3R Recovery Rule Refinement Patch.")
    parser.add_argument(
        "--full-structured-demo-export-package-345d-dir",
        default=str(DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR),
    )
    parser.add_argument(
        "--recovery-rule-refinement-346b3-dir",
        default=str(DEFAULT_RECOVERY_RULE_REFINEMENT_346B3_DIR),
    )
    parser.add_argument(
        "--refined-recovery-candidate-qa-reaudit-346b2r-dir",
        default=str(DEFAULT_REFINED_RECOVERY_CANDIDATE_QA_REAUDIT_346B2R_DIR),
    )
    parser.add_argument(
        "--controlled-quality-limited-recovery-expansion-346b4-dir",
        default=str(DEFAULT_CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--strict-patch", default="true")
    parser.add_argument("--max-patch-rows", type=int, default=22)
    parser.add_argument("--include-human-review-triage", default="true")
    parser.add_argument("--include-still-limited-triage", default="true")
    parser.add_argument("--max-context-chars", type=int, default=4000)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_recovery_rule_refinement_patch_346b3r(
        full_structured_demo_export_package_345d_dir=Path(args.full_structured_demo_export_package_345d_dir),
        recovery_rule_refinement_346b3_dir=Path(args.recovery_rule_refinement_346b3_dir),
        refined_recovery_candidate_qa_reaudit_346b2r_dir=Path(args.refined_recovery_candidate_qa_reaudit_346b2r_dir),
        controlled_quality_limited_recovery_expansion_346b4_dir=Path(
            args.controlled_quality_limited_recovery_expansion_346b4_dir
        ),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        strict_patch=_truthy(args.strict_patch),
        max_patch_rows=args.max_patch_rows,
        include_human_review_triage=_truthy(args.include_human_review_triage),
        include_still_limited_triage=_truthy(args.include_still_limited_triage),
        max_context_chars=args.max_context_chars,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / UNKNOWN_AUDIT_JSON_FILE_NAME, artifacts["unknown_row_audit_rows"])
    write_csv(output_dir / UNKNOWN_AUDIT_CSV_FILE_NAME, artifacts["unknown_row_audit_rows"])
    write_json(output_dir / PATCHABLE_JSON_FILE_NAME, artifacts["patchable_rows"])
    write_csv(output_dir / PATCHABLE_CSV_FILE_NAME, artifacts["patchable_rows"])
    write_json(output_dir / NON_PATCHABLE_JSON_FILE_NAME, artifacts["non_patchable_rows"])
    write_csv(output_dir / NON_PATCHABLE_CSV_FILE_NAME, artifacts["non_patchable_rows"])
    write_json(
        output_dir / SEMANTIC_PATCHES_JSON_FILE_NAME,
        artifacts["proposed_semantic_classifier_patch_rows"],
    )
    write_csv(
        output_dir / SEMANTIC_PATCHES_CSV_FILE_NAME,
        artifacts["proposed_semantic_classifier_patch_rows"],
    )
    write_json(
        output_dir / UNIT_PATCHES_JSON_FILE_NAME,
        artifacts["proposed_unit_policy_patch_rows"],
    )
    write_csv(
        output_dir / UNIT_PATCHES_CSV_FILE_NAME,
        artifacts["proposed_unit_policy_patch_rows"],
    )
    write_json(output_dir / PATCHED_POLICY_PREVIEW_JSON_FILE_NAME, artifacts["patched_unit_policy_preview"])
    (output_dir / PATCHED_POLICY_PREVIEW_MD_FILE_NAME).write_text(
        artifacts["patched_unit_policy_preview_md"], encoding="utf-8"
    )
    write_json(output_dir / PATCH_SAFETY_JSON_FILE_NAME, artifacts["patch_safety_review_rows"])
    write_csv(output_dir / PATCH_SAFETY_CSV_FILE_NAME, artifacts["patch_safety_review_rows"])
    write_json(output_dir / REPLAY_READINESS_JSON_FILE_NAME, artifacts["replay_readiness_report"])
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(artifacts["executive_summary_md"], encoding="utf-8")
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_md"], encoding="utf-8")
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(artifacts["next_plan_md"], encoding="utf-8")

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"audited_unknown_row_count: {manifest.get('audited_unknown_row_count', '')}")
    print(f"patchable_rule_gap_count: {manifest.get('patchable_rule_gap_count', '')}")
    print(f"proposed_semantic_classifier_patch_count: {manifest.get('proposed_semantic_classifier_patch_count', '')}")
    print(f"proposed_unit_policy_patch_count: {manifest.get('proposed_unit_policy_patch_count', '')}")
    print(f"safe_to_replay_346b4: {manifest.get('safe_to_replay_346b4', '')}")
    print(f"safe_to_continue_expansion: {manifest.get('safe_to_continue_expansion', '')}")
    print(f"recommended_next_step: {manifest.get('recommended_next_step', '')}")
    return 0 if manifest.get("decision") == READY_DECISION_346B3R else 1


if __name__ == "__main__":
    raise SystemExit(main())
