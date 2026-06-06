from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.trust.unfamiliar_pdf_trust_benchmark_330f import (  # noqa: E402
    _delivery_summary,
    _source_pdf_name,
    _waiting_summary,
)


def test_source_pdf_name_prefers_upstream_report_name() -> None:
    row = {
        "provenance": {
            "upstream_provenance": {
                "source_report_name": "demo_report.pdf",
            }
        }
    }
    assert _source_pdf_name(row) == "demo_report.pdf"


def test_delivery_summary_computes_review_burden_and_ratio() -> None:
    metrics = {
        "record_count": 10,
        "routing_decision_distribution": {
            "TRUSTED": 4,
            "REVIEW_REQUIRED": 5,
            "REJECTED": 1,
        },
    }
    result = _delivery_summary(metrics)
    assert result["sidecar_trusted_suggestion_count"] == 4
    assert result["estimated_human_review_burden_count"] == 6
    assert result["estimated_auto_trusted_ratio"] == 0.4


def test_waiting_summary_is_non_blocking() -> None:
    summary = _waiting_summary(
        output_dir=Path(r"D:\_datefac\output\unfamiliar_pdf_trust_benchmark_330f"),
        unfamiliar_source_dirs=[Path(r"D:\_datefac\output\unfamiliar_pdf_outputs")],
        no_official_asset_modification_during_330f=True,
    )
    assert summary["unfamiliar_source_status"] == "missing_or_empty"
    assert summary["scored_unfamiliar_record_count"] == 0
