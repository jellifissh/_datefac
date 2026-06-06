from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.end_to_end_delivery_quality_report_330g import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PREPARED_UNFAMILIAR_DIR,
    DEFAULT_UNFAMILIAR_EXPORT_SMOKE_DIR,
    DEFAULT_UNFAMILIAR_TRUST_BENCHMARK_DIR,
    build_end_to_end_delivery_quality_report_330g,
)
from datefac.trust.end_to_end_delivery_quality_report_330g_report import (  # noqa: E402
    SUMMARY_SHEET_ORDER,
    end_to_end_delivery_quality_report_330g_markdown,
    write_excel,
    write_json,
)
from datefac.trust.no_apply_proof import FORMAL_SCOPE_RULES_PATH, SEMANTIC_ALIAS_ASSET_PATH  # noqa: E402


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 330G end-to-end delivery quality report.")
    parser.add_argument("--unfamiliar-export-smoke-dir", default=str(DEFAULT_UNFAMILIAR_EXPORT_SMOKE_DIR))
    parser.add_argument("--unfamiliar-trust-benchmark-dir", default=str(DEFAULT_UNFAMILIAR_TRUST_BENCHMARK_DIR))
    parser.add_argument("--prepared-unfamiliar-dir", default=str(DEFAULT_PREPARED_UNFAMILIAR_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    export_smoke_dir = Path(args.unfamiliar_export_smoke_dir)
    trust_benchmark_dir = Path(args.unfamiliar_trust_benchmark_dir)
    prepared_unfamiliar_dir = Path(args.prepared_unfamiliar_dir)
    output_dir = Path(args.output_dir)

    export_summary_path = export_smoke_dir / "unfamiliar_candidate_export_smoke_330f4_summary.json"
    trust_benchmark_summary_path = trust_benchmark_dir / "unfamiliar_pdf_trust_benchmark_330f_summary.json"

    artifacts = build_end_to_end_delivery_quality_report_330g(
        export_summary=_read_json(export_summary_path),
        benchmark_summary=_read_json(trust_benchmark_summary_path),
        prepared_unfamiliar_dir=prepared_unfamiliar_dir,
        output_dir=output_dir,
        alias_asset_path=SEMANTIC_ALIAS_ASSET_PATH,
        scope_asset_path=FORMAL_SCOPE_RULES_PATH,
        files_read=[
            str(export_summary_path),
            str(trust_benchmark_summary_path),
            str(prepared_unfamiliar_dir / "unfamiliar_candidate_manifest.json"),
            str(prepared_unfamiliar_dir / "unfamiliar_candidate_rows.jsonl"),
            str(SEMANTIC_ALIAS_ASSET_PATH),
            str(FORMAL_SCOPE_RULES_PATH),
        ],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "end_to_end_delivery_quality_report_330g_summary.json"
    qa_json = output_dir / "end_to_end_delivery_quality_report_330g_qa.json"
    no_apply_json = output_dir / "end_to_end_delivery_quality_report_330g_no_apply_proof.json"
    summary_xlsx = output_dir / "end_to_end_delivery_quality_report_330g_summary.xlsx"
    report_md = output_dir / "end_to_end_delivery_quality_report_330g_report.md"

    write_json(summary_json, artifacts["summary"])
    write_json(qa_json, artifacts["qa_json"])
    write_json(no_apply_json, artifacts["no_apply_proof_json"])
    write_excel(
        summary_xlsx,
        {
            "summary": artifacts["summary_df"],
            "qa_summary": artifacts["qa_summary_df"],
            "qa_checks": artifacts["qa_checks_df"],
            "delivery_metrics": artifacts["delivery_metrics_df"],
            "distribution": artifacts["distribution_df"],
            "limitations": artifacts["limitations_df"],
            "prepared_manifest": artifacts["prepared_manifest_df"],
            "prepared_candidate_rows": artifacts["prepared_candidate_rows_df"],
            "official_asset_proof": artifacts["official_asset_proof_df"],
        },
        SUMMARY_SHEET_ORDER,
    )
    report_md.write_text(end_to_end_delivery_quality_report_330g_markdown(artifacts["summary"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"end_to_end_delivery_quality_report_330g_summary_json: {summary_json}")
    print(f"end_to_end_delivery_quality_report_330g_qa_json: {qa_json}")
    print(f"end_to_end_delivery_quality_report_330g_no_apply_proof_json: {no_apply_json}")
    print(f"end_to_end_delivery_quality_report_330g_summary_xlsx: {summary_xlsx}")
    print(f"end_to_end_delivery_quality_report_330g_report_md: {report_md}")
    for key in [
        "validated_330f4_smoke_export",
        "validated_330f_unfamiliar_benchmark",
        "processed_pdf_count",
        "prepared_candidate_row_count",
        "artifact_row_count",
        "strict_deduped_candidate_count",
        "sidecar_trusted_suggestion_count",
        "sidecar_review_required_suggestion_count",
        "unit_missing_count",
        "source_page_missing_count",
        "delivery_readiness_judgment",
        "recommended_next_step",
        "no_official_asset_modification_during_330g",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
