from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.full_structured_data_inventory_345a import (  # noqa: E402
    NOT_READY_DECISION_345A,
    READY_DECISION_345A,
    build_full_structured_data_inventory_345a,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_excel(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=sheet_name, index=False)


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_full_structured_data_inventory_345a"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345a_inputs(root: Path, *, with_342h: bool = True, with_344f: bool = True) -> tuple[Path, Path, Path, Path]:
    dir_342f = root / "output" / "table_first_core_financial_extraction_342f"
    dir_342g = root / "output" / "table_first_extraction_review_package_342g"
    dir_342h = root / "output" / "table_first_human_review_apply_simulation_342h"
    dir_344f = root / "output" / "review_queue_strict_human_review_package_344f"
    dir_342f.mkdir(parents=True, exist_ok=True)
    dir_342g.mkdir(parents=True, exist_ok=True)
    if with_342h:
        dir_342h.mkdir(parents=True, exist_ok=True)
    if with_344f:
        dir_344f.mkdir(parents=True, exist_ok=True)

    _write_json(
        dir_342f / "table_first_core_financial_extraction_342f_summary.json",
        {
            "long_form_cell_count": 2,
            "trusted_cell_count": 1,
            "review_required_cell_count": 1,
            "rejected_cell_count": 1,
            "decision": "TABLE_FIRST_CORE_FINANCIAL_EXTRACTION_342F_READY",
            "qa_fail_count": 0,
        },
    )
    _write_excel(
        dir_342f / "table_first_core_financial_extraction_342f.xlsx",
        {
            "03_LONG_FORM_CELLS": pd.DataFrame(
                [
                    {
                        "long_cell_id": "c1",
                        "corpus_pdf_id": "pdf_1",
                        "file_name": "file1.pdf",
                        "table_id": "table_1",
                        "row_index": 0,
                        "metric_raw": "Revenue",
                        "metric_standardized": "revenue",
                        "value_raw": "10",
                        "value_numeric": "10",
                        "normalized_unit": "亿元",
                        "year_standardized": "2024A",
                        "source_page": 1,
                        "confidence_signal": "high",
                    },
                    {
                        "long_cell_id": "c2",
                        "corpus_pdf_id": "pdf_1",
                        "file_name": "file1.pdf",
                        "table_id": "table_1",
                        "row_index": 1,
                        "metric_raw": "ROE",
                        "metric_standardized": "ROE",
                        "value_raw": "10%",
                        "value_numeric": "10",
                        "normalized_unit": "%",
                        "year_standardized": "2024A",
                        "source_page": 1,
                        "confidence_signal": "medium",
                    },
                ]
            ),
            "04_TRUSTED_CELLS": pd.DataFrame(
                [
                    {
                        "long_cell_id": "c1",
                        "corpus_pdf_id": "pdf_1",
                        "file_name": "file1.pdf",
                        "table_id": "table_1",
                        "row_index": 0,
                        "metric_raw": "Revenue",
                        "metric_standardized": "revenue",
                        "value_raw": "10",
                        "value_numeric": "10",
                        "normalized_unit": "亿元",
                        "year_standardized": "2024A",
                        "source_page": 1,
                        "confidence_signal": "high",
                    }
                ]
            ),
            "05_REVIEW_REQUIRED": pd.DataFrame(
                [
                    {
                        "long_cell_id": "c2",
                        "corpus_pdf_id": "pdf_1",
                        "file_name": "file1.pdf",
                        "table_id": "table_1",
                        "row_index": 1,
                        "metric_raw": "ROE",
                        "metric_standardized": "ROE",
                        "value_raw": "10%",
                        "value_numeric": "10",
                        "normalized_unit": "%",
                        "year_standardized": "2024A",
                        "source_page": 1,
                        "confidence_signal": "medium",
                    }
                ]
            ),
            "06_REJECTED_CELLS": pd.DataFrame(
                [
                    {
                        "long_cell_id": "c3",
                        "corpus_pdf_id": "pdf_1",
                        "file_name": "file1.pdf",
                        "table_id": "table_1",
                        "row_index": 2,
                        "metric_raw": "",
                        "metric_standardized": "",
                        "value_raw": "n/a",
                        "value_numeric": "",
                        "normalized_unit": "",
                        "year_standardized": "",
                        "source_page": "",
                        "confidence_signal": "low",
                    }
                ]
            ),
        },
    )

    _write_json(
        dir_342g / "table_first_extraction_review_package_342g_summary.json",
        {"decision": "TABLE_FIRST_EXTRACTION_REVIEW_PACKAGE_342G_READY", "qa_fail_count": 0},
    )
    _write_excel(
        dir_342g / "table_first_extraction_review_package_342g.xlsx",
        {
            "03_REVIEW_QUEUE": pd.DataFrame(
                [
                    {
                        "review_item_id": "q1",
                        "corpus_pdf_id": "pdf_1",
                        "file_name": "file1.pdf",
                        "table_id": "table_1",
                        "metric_raw": "ROE",
                        "metric_standardized": "ROE",
                        "value_raw": "10%",
                        "value_numeric": "10",
                        "normalized_unit": "%",
                        "year_standardized": "2024A",
                        "source_page": 1,
                        "confidence_signal": "medium",
                    }
                ]
            ),
            "04_TRUSTED_AUDIT": pd.DataFrame(
                [
                    {
                        "review_item_id": "t1",
                        "corpus_pdf_id": "pdf_1",
                        "file_name": "file1.pdf",
                        "table_id": "table_1",
                        "metric_raw": "Revenue",
                        "metric_standardized": "revenue",
                        "value_raw": "10",
                        "value_numeric": "10",
                        "normalized_unit": "亿元",
                        "year_standardized": "2024A",
                        "source_page": 1,
                        "confidence_signal": "high",
                    }
                ]
            ),
            "10_REVIEW_TEMPLATE": pd.DataFrame(
                [
                    {
                        "review_item_id": "tpl1",
                        "corpus_pdf_id": "pdf_1",
                        "file_name": "file1.pdf",
                        "table_id": "table_1",
                        "metric_raw": "ROE",
                        "metric_standardized": "ROE",
                        "value_raw": "10%",
                        "value_numeric": "10",
                        "normalized_unit": "%",
                        "year_standardized": "2024A",
                        "source_page": 1,
                        "confidence_signal": "medium",
                    }
                ]
            ),
        },
    )

    if with_342h:
        _write_json(
            dir_342h / "table_first_human_review_apply_simulation_342h_summary.json",
            {"reviewed_row_count": 2, "decision": "TABLE_FIRST_HUMAN_REVIEW_APPLY_SIMULATION_342H_READY", "qa_fail_count": 0},
        )
        _write_excel(
            dir_342h / "table_first_human_review_apply_simulation_342h.xlsx",
            {
                "03_VALIDATED_DECISIONS": pd.DataFrame(
                    [
                        {
                            "review_item_id": "h1",
                            "corpus_pdf_id": "pdf_1",
                            "file_name": "file1.pdf",
                            "table_id": "table_1",
                            "metric_raw": "ROE",
                            "metric_standardized": "ROE",
                            "value_raw": "10%",
                            "value_numeric": "10",
                            "normalized_unit": "%",
                            "year_standardized": "2024A",
                            "source_page": 1,
                            "confidence_signal": "medium",
                        }
                    ]
                ),
                "04_CONFIRMED_CELLS": pd.DataFrame(
                    [
                        {
                            "review_item_id": "h1",
                            "corpus_pdf_id": "pdf_1",
                            "file_name": "file1.pdf",
                            "table_id": "table_1",
                            "metric_raw": "ROE",
                            "metric_standardized": "ROE",
                            "value_raw": "10%",
                            "value_numeric": "10",
                            "normalized_unit": "%",
                            "year_standardized": "2024A",
                            "source_page": 1,
                            "confidence_signal": "medium",
                        }
                    ]
                ),
                "05_CORRECTED_CELLS": pd.DataFrame(
                    [
                        {
                            "review_item_id": "h2",
                            "corpus_pdf_id": "pdf_1",
                            "file_name": "file1.pdf",
                            "table_id": "table_1",
                            "metric_raw": "Growth",
                            "reviewer_metric_standardized": "YOY",
                            "value_raw": "20%",
                            "reviewer_value_numeric": "20",
                            "reviewer_normalized_unit": "%",
                            "reviewer_year_standardized": "2025A",
                            "source_page": 2,
                            "confidence_signal": "medium",
                        }
                    ]
                ),
                "06_REJECTED_CELLS": pd.DataFrame(columns=["review_item_id"]),
                "09_PENDING_REVIEW": pd.DataFrame(
                    [
                        {
                            "review_item_id": "h3",
                            "corpus_pdf_id": "pdf_1",
                            "file_name": "file1.pdf",
                            "table_id": "table_1",
                            "metric_raw": "PE",
                            "metric_standardized": "PE",
                            "value_raw": "12",
                            "value_numeric": "12",
                            "normalized_unit": "倍",
                            "year_standardized": "2025A",
                            "source_page": 2,
                            "confidence_signal": "low",
                        }
                    ]
                ),
            },
        )

    if with_344f:
        _write_json(
            dir_344f / "review_queue_strict_human_review_package_344f_manifest.json",
            {
                "strict_review_row_count": 2,
                "decision": "STRICT_HUMAN_REVIEW_PACKAGE_344F_READY",
                "formal_client_export_allowed": False,
                "client_ready": False,
                "production_ready": False,
            },
        )
        _write_json(
            dir_344f / "review_queue_strict_human_review_package_344f_review_rows.json",
            [
                {
                    "source_row_id": "344f1",
                    "source_document": "file1.pdf",
                    "metric_name": "EPS",
                    "normalized_metric_name": "EPS",
                    "reported_value": "1.2",
                    "normalized_value": "1.2",
                    "unit": "元",
                    "period": "2024A",
                    "source_page": "2",
                    "trust_status": "Prior demo trusted arc",
                },
                {
                    "source_row_id": "344f2",
                    "source_document": "file2.pdf",
                    "metric_name": "YOY",
                    "normalized_metric_name": "YOY",
                    "reported_value": "20",
                    "normalized_value": "20",
                    "unit": "%",
                    "period": "2025A",
                    "source_page": "3",
                    "trust_status": "Source-check resolved row",
                },
            ],
        )

    return dir_342f, dir_342g, dir_342h, dir_344f


def test_345a_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_342f, dir_342g, dir_342h, dir_344f = _seed_345a_inputs(case_root)
        artifacts = build_full_structured_data_inventory_345a(
            table_first_core_financial_extraction_342f_dir=dir_342f,
            table_first_extraction_review_package_342g_dir=dir_342g,
            table_first_human_review_apply_simulation_342h_dir=dir_342h,
            review_queue_strict_human_review_package_344f_dir=dir_344f,
            output_dir=case_root / "output" / "full_structured_data_inventory_345a",
            repo_root=case_root,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345A
        assert manifest["qa_fail_count"] == 0
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        assert manifest["global_strict_human_review_completed"] is False
        assert manifest["total_inventory_row_count"] > 0
        assert manifest["strict_human_review_pending_row_count"] == 2
        assert manifest["downstream_ready_candidate_count"] > 0
        assert artifacts["qa_json"]["warning_count"] >= 0
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345a_optional_missing_inputs_become_warnings() -> None:
    case_root = _make_case_root()
    try:
        dir_342f, dir_342g, dir_342h, dir_344f = _seed_345a_inputs(
            case_root,
            with_342h=False,
            with_344f=False,
        )
        artifacts = build_full_structured_data_inventory_345a(
            table_first_core_financial_extraction_342f_dir=dir_342f,
            table_first_extraction_review_package_342g_dir=dir_342g,
            table_first_human_review_apply_simulation_342h_dir=dir_342h,
            review_queue_strict_human_review_package_344f_dir=dir_344f,
            output_dir=case_root / "output" / "full_structured_data_inventory_345a",
            repo_root=case_root,
        )
        assert artifacts["manifest"]["decision"] == READY_DECISION_345A
        assert artifacts["qa_json"]["warning_count"] >= 2
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345a_not_ready_if_both_342f_and_342g_missing() -> None:
    case_root = _make_case_root()
    try:
        missing = case_root / "missing"
        try:
            build_full_structured_data_inventory_345a(
                table_first_core_financial_extraction_342f_dir=missing / "342f",
                table_first_extraction_review_package_342g_dir=missing / "342g",
                table_first_human_review_apply_simulation_342h_dir=missing / "342h",
                review_queue_strict_human_review_package_344f_dir=missing / "344f",
                output_dir=case_root / "output" / "full_structured_data_inventory_345a",
                repo_root=case_root,
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError when both 342F and 342G are missing.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
