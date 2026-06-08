from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.core_financial_context_repair_337c import (  # noqa: E402
    DEFAULT_MINERU_REAL_TEST_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PRECISION_337B_DIR,
    build_core_financial_context_repair_337c,
)
from datefac.trust.core_financial_context_repair_337c_report import (  # noqa: E402
    BEFORE_AFTER_SHEETS,
    CUSTOMER_WORKBOOK_SHEETS,
    report_markdown,
    write_excel,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 337C core financial table context repair.")
    parser.add_argument("--precision-337b-dir", default=str(DEFAULT_PRECISION_337B_DIR))
    parser.add_argument("--mineru-real-test-dir", default=str(DEFAULT_MINERU_REAL_TEST_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    precision_337b_dir = Path(args.precision_337b_dir)
    mineru_real_test_dir = Path(args.mineru_real_test_dir)
    output_dir = Path(args.output_dir)

    artifacts = build_core_financial_context_repair_337c(
        precision_337b_dir=precision_337b_dir,
        mineru_real_test_dir=mineru_real_test_dir,
        output_dir=output_dir,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "core_financial_context_repair_337c_summary.json"
    manifest_json = output_dir / "core_financial_context_repair_337c_manifest.json"
    qa_json = output_dir / "core_financial_context_repair_337c_qa.json"
    report_md = output_dir / "core_financial_context_repair_337c_report.md"
    before_after_xlsx = output_dir / "core_financial_context_repair_337c_before_after.xlsx"
    customer_workbook_xlsx = output_dir / "real_test_mineru_client_export_337c.xlsx"

    write_json(summary_json, artifacts["summary"])
    write_json(manifest_json, artifacts["manifest"])
    write_json(qa_json, artifacts["qa_json"])
    write_excel(before_after_xlsx, artifacts["before_after_sheets"], BEFORE_AFTER_SHEETS)
    write_excel(customer_workbook_xlsx, artifacts["customer_workbook_sheets"], CUSTOMER_WORKBOOK_SHEETS)
    report_md.write_text(report_markdown(artifacts["summary"], artifacts["qa_json"]), encoding="utf-8")

    summary = artifacts["summary"]
    print(f"core_financial_context_repair_337c_summary_json: {summary_json}")
    print(f"core_financial_context_repair_337c_manifest_json: {manifest_json}")
    print(f"core_financial_context_repair_337c_qa_json: {qa_json}")
    print(f"core_financial_context_repair_337c_report_md: {report_md}")
    print(f"core_financial_context_repair_337c_before_after_xlsx: {before_after_xlsx}")
    print(f"real_test_mineru_client_export_337c_xlsx: {customer_workbook_xlsx}")
    for key in [
        "reviewed_before_count",
        "reviewed_after_count",
        "table_role_repair_count",
        "unit_filled_count",
        "yoy_parent_repaired_count",
        "reviewed_356439_before_count",
        "reviewed_356439_after_count",
        "qa_fail_count",
        "decision",
    ]:
        print(f"{key}: {summary.get(key, '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
