from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.vlm.vlm_quality_gate import run_vlm_output_quality_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 321A sandbox-only VLM output quality gate.")
    parser.add_argument("--vlm-output-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_vlm_output_quality_gate(
        vlm_output_root=Path(args.vlm_output_root),
        output_dir=Path(args.output_dir),
    )
    print(f"vlm_output_quality_excel: {result.get('excel_path', '')}")
    print(f"vlm_output_quality_summary_json: {result.get('summary_json_path', '')}")
    print(f"vlm_output_quality_report_md: {result.get('report_md_path', '')}")
    print(f"vlm_rerun_prompt_md: {result.get('rerun_prompt_path', '')}")
    print(f"vlm_folder_count: {result.get('vlm_folder_count', 0)}")
    print(f"parsed_json_count: {result.get('parsed_json_count', 0)}")
    print(f"table_output_count: {result.get('table_output_count', 0)}")
    print(f"table_ready_count: {result.get('table_ready_count', 0)}")
    print(f"values_ok_labels_corrupted_count: {result.get('values_ok_labels_corrupted_count', 0)}")
    print(f"corrupted_label_rate: {result.get('corrupted_label_rate', 0.0):.4f}")
    print(f"numeric_parse_success_rate: {result.get('numeric_parse_success_rate', 0.0):.4f}")
    print(f"global_vlm_quality_decision: {result.get('global_vlm_quality_decision', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
