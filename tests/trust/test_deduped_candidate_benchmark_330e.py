from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.deduped_candidate_benchmark_330e import (  # noqa: E402
    content_fingerprint_key,
    cross_artifact_fingerprint_key,
    dedup_reliability_level,
    recommended_next_step,
    strict_candidate_key,
)


def test_strict_candidate_key_prefers_candidate_id() -> None:
    row = {
        "candidate_id": "cand_001",
        "source_candidate_id": "src_001",
        "provenance": {"upstream_provenance": {"source_candidate_id": "up_001"}},
    }
    assert strict_candidate_key(row) == "candidate_id::cand_001"


def test_strict_candidate_key_falls_back_to_artifact_row_identity() -> None:
    row = {
        "candidate_id": "",
        "source_candidate_id": "",
        "source_artifact": "a.jsonl",
        "source_sheet": "sheet1",
        "source_row": "row_1",
        "source_table": "table_1",
        "provenance": {"source_row_index": 2},
    }
    key = strict_candidate_key(row)
    assert key.startswith("artifact_row::")


def test_content_and_cross_artifact_fingerprint_keys_can_collapse_artifact_only_difference() -> None:
    base = {
        "metric_label_raw": "Revenue",
        "normalized_metric": "revenue",
        "value": 10,
        "unit": "CNY",
        "year": "2024A",
        "parser_sources": ["p1"],
        "evidence_refs": ["table_1", "Revenue", "doc_1"],
        "existing_status": "REVIEW_REQUIRED",
        "source_table": "table_1",
        "source_row": "Revenue",
        "provenance": {"upstream_provenance": {"source_report_name": "doc_1"}},
    }
    row_a = dict(base, source_artifact="a.jsonl", source_sheet="sheet_a")
    row_b = dict(base, source_artifact="b.xlsx", source_sheet="sheet_b")

    assert content_fingerprint_key(row_a) == content_fingerprint_key(row_b)
    assert cross_artifact_fingerprint_key(row_a) == cross_artifact_fingerprint_key(row_b)


def test_reliability_and_next_step_logic() -> None:
    assert dedup_reliability_level(
        source_candidate_id_coverage_rate=0.0,
        candidate_id_coverage_rate=1.0,
        strict_duplicate_rate=0.01,
        cross_artifact_duplicate_rate=0.09,
    ) == "MEDIUM"
    assert recommended_next_step(
        reliability_level="MEDIUM",
        policy_calibration_safe_to_continue=True,
    ) == "330F_UNFAMILIAR_PDF_TRUST_BENCHMARK"
    assert recommended_next_step(
        reliability_level="LOW",
        policy_calibration_safe_to_continue=False,
    ) == "330D2_STRONGER_CANDIDATE_ID_EXTRACTION"
