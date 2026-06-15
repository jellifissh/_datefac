from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.controlled_expansion_replay_with_patched_rules_346b4r import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    DEFAULT_CONTROLLED_QUALITY_LIMITED_RECOVERY_EXPANSION_346B4_DIR,
    DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR,
    DEFAULT_LEDGER_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RECOVERY_RULE_REFINEMENT_PATCH_346B3R_DIR,
    DELTA_CSV_FILE_NAME,
    DELTA_JSON_FILE_NAME,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    GUARD_CSV_FILE_NAME,
    GUARD_JSON_FILE_NAME,
    LINEAGE_CSV_FILE_NAME,
    LINEAGE_JSON_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    PATCHED_CSV_FILE_NAME,
    PATCHED_JSON_FILE_NAME,
    READINESS_JSON_FILE_NAME,
    REPLAY_RESULTS_CSV_FILE_NAME,
    REPLAY_RESULTS_JSON_FILE_NAME,
    SAFE_CSV_FILE_NAME,
    SAFE_JSON_FILE_NAME,
    SEMANTIC_CSV_FILE_NAME,
    SEMANTIC_JSON_FILE_NAME,
    UNIT_CSV_FILE_NAME,
    UNIT_JSON_FILE_NAME,
    UNKNOWN_CSV_FILE_NAME,
    UNKNOWN_JSON_FILE_NAME,
    build_controlled_expansion_replay_with_patched_rules_346b4r,
)
from datefac.benchmark.controlled_expansion_replay_with_patched_rules_346b4r_report import (  # noqa: E402
    write_csv,
    write_json,
)


def _truthy(value: str) -> bool:
    return str(value).strip().lower() not in {"0", "false", "no"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 346B4R Controlled Expansion Replay With Patched Rules.")
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
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ledger-path", default=str(DEFAULT_LEDGER_PATH))
    parser.add_argument("--replay-same-row-set", default="true")
    parser.add_argument("--strict-guardrails", default="true")
    parser.add_argument("--require-346b3r-safe-to-replay", default="true")
    parser.add_argument("--max-context-chars", type=int, default=4000)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_controlled_expansion_replay_with_patched_rules_346b4r(
        full_structured_demo_export_package_345d_dir=Path(args.full_structured_demo_export_package_345d_dir),
        controlled_quality_limited_recovery_expansion_346b4_dir=Path(
            args.controlled_quality_limited_recovery_expansion_346b4_dir
        ),
        recovery_rule_refinement_patch_346b3r_dir=Path(args.recovery_rule_refinement_patch_346b3r_dir),
        output_dir=output_dir,
        repo_root=PROJECT_ROOT,
        ledger_path=Path(args.ledger_path),
        replay_same_row_set=_truthy(args.replay_same_row_set),
        strict_guardrails=_truthy(args.strict_guardrails),
        require_346b3r_safe_to_replay=_truthy(args.require_346b3r_safe_to_replay),
        max_context_chars=args.max_context_chars,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(output_dir / REPLAY_RESULTS_JSON_FILE_NAME, artifacts["replay_results_rows"])
    write_csv(output_dir / REPLAY_RESULTS_CSV_FILE_NAME, artifacts["replay_results_rows"])
    write_json(output_dir / SAFE_JSON_FILE_NAME, artifacts["safe_recovered_candidate_rows"])
    write_csv(output_dir / SAFE_CSV_FILE_NAME, artifacts["safe_recovered_candidate_rows"])
    write_json(output_dir / PATCHED_JSON_FILE_NAME, artifacts["patched_rows"])
    write_csv(output_dir / PATCHED_CSV_FILE_NAME, artifacts["patched_rows"])
    write_json(output_dir / UNKNOWN_JSON_FILE_NAME, artifacts["remaining_unknown_rows"])
    write_csv(output_dir / UNKNOWN_CSV_FILE_NAME, artifacts["remaining_unknown_rows"])
    write_json(output_dir / GUARD_JSON_FILE_NAME, artifacts["guardrail_rows"])
    write_csv(output_dir / GUARD_CSV_FILE_NAME, artifacts["guardrail_rows"])
    write_json(output_dir / DELTA_JSON_FILE_NAME, artifacts["delta_rows"])
    write_csv(output_dir / DELTA_CSV_FILE_NAME, artifacts["delta_rows"])
    write_json(output_dir / SEMANTIC_JSON_FILE_NAME, artifacts["semantic_class_distribution_rows"])
    write_csv(output_dir / SEMANTIC_CSV_FILE_NAME, artifacts["semantic_class_distribution_rows"])
    write_json(output_dir / UNIT_JSON_FILE_NAME, artifacts["unit_action_distribution_rows"])
    write_csv(output_dir / UNIT_CSV_FILE_NAME, artifacts["unit_action_distribution_rows"])
    write_json(output_dir / LINEAGE_JSON_FILE_NAME, artifacts["lineage_evidence_audit_rows"])
    write_csv(output_dir / LINEAGE_CSV_FILE_NAME, artifacts["lineage_evidence_audit_rows"])
    write_json(output_dir / READINESS_JSON_FILE_NAME, artifacts["expansion_readiness_report"])
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(artifacts["executive_summary_md"], encoding="utf-8")
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(artifacts["artifact_index_md"], encoding="utf-8")
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(artifacts["next_plan_md"], encoding="utf-8")

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"replay_input_row_count: {manifest.get('replay_input_row_count', '')}")
    print(f"same_row_set_replay: {manifest.get('same_row_set_replay', '')}")
    print(f"replay_safe_recovered_candidate_count: {manifest.get('replay_safe_recovered_candidate_count', '')}")
    print(f"replay_semantic_class_unknown_count: {manifest.get('replay_semantic_class_unknown_count', '')}")
    print(f"patch_applied_row_count: {manifest.get('patch_applied_row_count', '')}")
    print(f"safe_to_continue_expansion: {manifest.get('safe_to_continue_expansion', '')}")
    print(f"recommended_next_step: {manifest.get('recommended_next_step', '')}")
    return 0 if manifest.get("decision") == "CONTROLLED_EXPANSION_REPLAY_WITH_PATCHED_RULES_346B4R_READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
