from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.cached_candidate_benchmark_330c import (  # noqa: E402
    build_fallback_fixture_rows,
    convert_candidate_row_to_trust_input,
    map_raw_risk_tokens,
    normalize_existing_status,
    score_bucket_label,
)
from datefac.trust.confidence_scoring import score_trust_record  # noqa: E402


def test_normalize_existing_status() -> None:
    assert normalize_existing_status("trusted_preview") == "TRUSTED"
    assert normalize_existing_status("review_required_preview") == "REVIEW_REQUIRED"
    assert normalize_existing_status("rejected") == "REJECTED"
    assert normalize_existing_status("out_of_scope_preview") == "OUT_OF_SCOPE"


def test_map_raw_risk_tokens_best_effort() -> None:
    assert map_raw_risk_tokens(
        ["UNKNOWN_METRIC_CODE", "INVALID_OR_MISSING_YEAR", "VALUE_PARSE_FAILED_OR_SCHEMA_UNCERTAIN"]
    ) == ["TARGET_METRIC_AMBIGUOUS", "YEAR_MISSING", "VALUE_PARSE_FAILED"]


def test_convert_candidate_row_to_trust_input_router_style() -> None:
    row = {
        "candidate_id": "abc123",
        "raw_metric_name": "Revenue",
        "metric_code_after": "revenue",
        "normalized_value": 6742.0,
        "unit": "CNY_million",
        "year": "2024A",
        "source_stage": "mineru_table_body_321d",
        "source_row_text": "Revenue | 6742",
        "source_table_id": "table_001",
        "source_row_index": 1,
        "source_report_name": "doc_001",
        "split_decision": "trusted_preview",
        "risk_tags_after": "",
        "provenance_json": "{\"table_title\":\"Forecast Table\"}",
    }
    converted = convert_candidate_row_to_trust_input(
        row,
        artifact_path=Path("selected_candidate_reclassified_322b2.jsonl"),
        source_dir=Path(r"D:\_datefac\output\router_mineru_trust_split_322b2"),
        sheet_name="selected_candidate_reclassified_322b2",
        row_index=1,
    )
    assert converted["candidate_id"] == "abc123"
    assert converted["normalized_metric"] == "revenue"
    assert converted["existing_status"] == "TRUSTED"
    assert converted["parser_sources"] == ["mineru_table_body_321d"]


def test_fallback_fixtures_can_be_scored() -> None:
    fixtures = build_fallback_fixture_rows()
    assert len(fixtures) > 0
    scored = [score_trust_record(row) for row in fixtures]
    assert len(scored) == len(fixtures)
    assert all(score_bucket_label(row["confidence_score"]) for row in scored)
