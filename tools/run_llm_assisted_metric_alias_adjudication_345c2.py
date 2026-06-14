from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.llm_assisted_metric_alias_adjudication_345c2 import (  # noqa: E402
    ARTIFACT_INDEX_MD_FILE_NAME,
    DEFAULT_345C_DIR,
    DEFAULT_MAX_ALIAS_CANDIDATES,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_TIMEOUT_SECONDS,
    EXECUTIVE_SUMMARY_MD_FILE_NAME,
    MANIFEST_FILE_NAME,
    NEXT_PLAN_MD_FILE_NAME,
    PROMPT_AUDIT_MD_FILE_NAME,
    REQUEST_PACKAGE_CSV_FILE_NAME,
    REQUEST_PACKAGE_JSON_FILE_NAME,
    RESPONSE_AUDIT_JSON_FILE_NAME,
    REVIEW_REQUIRED_CSV_FILE_NAME,
    REVIEW_REQUIRED_JSON_FILE_NAME,
    SUGGESTION_FIELDS,
    SUGGESTIONS_CSV_FILE_NAME,
    SUGGESTIONS_JSON_FILE_NAME,
    REQUEST_ROW_FIELDS,
    build_llm_assisted_metric_alias_adjudication_345c2,
)
from datefac.benchmark.llm_assisted_metric_alias_adjudication_345c2_report import (  # noqa: E402
    artifact_index_markdown,
    executive_summary_markdown,
    next_plan_markdown,
    prompt_audit_markdown,
    write_csv,
    write_json,
)


def _parse_bool(value: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 345C2 LLM-assisted metric alias adjudication sidecar."
    )
    parser.add_argument(
        "--metric-candidate-normalization-coverage-345c-dir",
        default=str(DEFAULT_345C_DIR),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--max-alias-candidates",
        type=int,
        default=DEFAULT_MAX_ALIAS_CANDIDATES,
    )
    parser.add_argument(
        "--include-medium-priority",
        type=_parse_bool,
        default=False,
    )
    parser.add_argument(
        "--llm-mode",
        default="auto",
        choices=["auto", "live", "request_only", "fixture"],
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts = build_llm_assisted_metric_alias_adjudication_345c2(
        metric_candidate_normalization_coverage_345c_dir=Path(
            args.metric_candidate_normalization_coverage_345c_dir
        ),
        output_dir=output_dir,
        max_alias_candidates=args.max_alias_candidates,
        include_medium_priority=bool(args.include_medium_priority),
        llm_mode=args.llm_mode,
        timeout_seconds=args.timeout_seconds,
        repo_root=PROJECT_ROOT,
    )

    write_json(output_dir / MANIFEST_FILE_NAME, artifacts["manifest"])
    write_json(
        output_dir / REQUEST_PACKAGE_JSON_FILE_NAME,
        artifacts["alias_request_package_rows"],
    )
    write_csv(
        output_dir / REQUEST_PACKAGE_CSV_FILE_NAME,
        artifacts["alias_request_package_rows"],
        REQUEST_ROW_FIELDS,
    )
    write_json(
        output_dir / SUGGESTIONS_JSON_FILE_NAME,
        artifacts["alias_suggestion_rows"],
    )
    write_csv(
        output_dir / SUGGESTIONS_CSV_FILE_NAME,
        artifacts["alias_suggestion_rows"],
        SUGGESTION_FIELDS,
    )
    write_json(
        output_dir / REVIEW_REQUIRED_JSON_FILE_NAME,
        artifacts["review_required_rows"],
    )
    write_csv(
        output_dir / REVIEW_REQUIRED_CSV_FILE_NAME,
        artifacts["review_required_rows"],
        SUGGESTION_FIELDS,
    )
    write_json(output_dir / RESPONSE_AUDIT_JSON_FILE_NAME, artifacts["response_audit"])
    (output_dir / PROMPT_AUDIT_MD_FILE_NAME).write_text(
        prompt_audit_markdown(
            artifacts["manifest"],
            artifacts["alias_request_package_rows"],
        ),
        encoding="utf-8",
    )
    (output_dir / EXECUTIVE_SUMMARY_MD_FILE_NAME).write_text(
        executive_summary_markdown(
            artifacts["manifest"],
            artifacts["alias_suggestion_rows"],
        ),
        encoding="utf-8",
    )
    (output_dir / ARTIFACT_INDEX_MD_FILE_NAME).write_text(
        artifact_index_markdown(artifacts["artifact_index_rows"]),
        encoding="utf-8",
    )
    (output_dir / NEXT_PLAN_MD_FILE_NAME).write_text(
        next_plan_markdown(artifacts["manifest"]),
        encoding="utf-8",
    )

    manifest = artifacts["manifest"]
    print(f"manifest_json: {output_dir / MANIFEST_FILE_NAME}")
    print(f"decision: {manifest.get('decision', '')}")
    print(f"qa_fail_count: {manifest.get('qa_fail_count', '')}")
    print(f"llm_mode: {manifest.get('llm_mode', '')}")
    print(f"runtime_config_available: {manifest.get('runtime_config_available', '')}")
    print(f"selected_alias_candidate_count: {manifest.get('selected_alias_candidate_count', '')}")
    print(f"suggestion_row_count: {manifest.get('suggestion_row_count', '')}")
    print(f"needs_human_review_count: {manifest.get('needs_human_review_count', '')}")
    print(f"formal_client_export_allowed: {manifest.get('formal_client_export_allowed', '')}")
    print(f"client_ready: {manifest.get('client_ready', '')}")
    print(f"production_ready: {manifest.get('production_ready', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
