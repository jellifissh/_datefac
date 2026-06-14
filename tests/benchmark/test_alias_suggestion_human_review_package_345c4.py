from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.benchmark.alias_suggestion_human_review_package_345c4 import (  # noqa: E402
    READY_DECISION_345C4,
    build_alias_suggestion_human_review_package_345c4,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_alias_suggestion_human_review_package_345c4"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345c2_live_outputs(root: Path) -> Path:
    live_dir = root / "output" / "llm_assisted_metric_alias_adjudication_345c2_live"
    live_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "LLM_ASSISTED_METRIC_ALIAS_ADJUDICATION_345C2_READY",
        "llm_mode": "live",
        "qa_fail_count": 0,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "suggestion_row_count": 3,
        "selected_alias_candidate_count": 3,
    }
    suggestions = [
        {
            "alias_adjudication_id": "345c2::alias::001",
            "raw_metric_name": "Alias A",
            "frequency": 10,
            "alias_candidate_priority": "HIGH",
            "source_stages": "LONG_FORM_CELL|REVIEW_REQUIRED",
            "pdf_names": "alpha.pdf",
            "sample_row_ids": "345c::metric::00001",
            "suggested_action": "PROPOSE_NEW_STANDARD_METRIC",
            "suggested_standard_metric": "",
            "suggested_new_standard_metric": "capital_expenditure",
            "confidence": "MEDIUM",
            "reason": "Potential new standard.",
            "evidence_excerpt": "Alias A",
            "risk_flags": ["NEW_STANDARD_CANDIDATE"],
            "needs_human_review": True,
            "response_parse_status": "PARSED",
            "response_validation_status": "VALID",
        },
        {
            "alias_adjudication_id": "345c2::alias::002",
            "raw_metric_name": "Alias B",
            "frequency": 8,
            "alias_candidate_priority": "HIGH",
            "source_stages": "LONG_FORM_CELL",
            "pdf_names": "beta.pdf",
            "sample_row_ids": "345c::metric::00002",
            "suggested_action": "INSUFFICIENT_EVIDENCE",
            "suggested_standard_metric": "",
            "suggested_new_standard_metric": "",
            "confidence": "LOW",
            "reason": "Not enough context.",
            "evidence_excerpt": "Alias B",
            "risk_flags": ["INSUFFICIENT_ALIAS_CONTEXT"],
            "needs_human_review": True,
            "response_parse_status": "PARSED",
            "response_validation_status": "VALID",
        },
        {
            "alias_adjudication_id": "345c2::alias::003",
            "raw_metric_name": "Alias C",
            "frequency": 6,
            "alias_candidate_priority": "LOW",
            "source_stages": "REJECTED_OR_EXCLUDED",
            "pdf_names": "gamma.pdf",
            "sample_row_ids": "345c::metric::00003",
            "suggested_action": "NEEDS_HUMAN_REVIEW",
            "suggested_standard_metric": "",
            "suggested_new_standard_metric": "",
            "confidence": "LOW",
            "reason": "Validation issue.",
            "evidence_excerpt": "Alias C",
            "risk_flags": ["VALIDATION_FAILURE"],
            "needs_human_review": True,
            "response_parse_status": "PARSED",
            "response_validation_status": "INVALID_RESPONSE",
        },
    ]
    _write_json(live_dir / "llm_assisted_metric_alias_adjudication_345c2_manifest.json", manifest)
    _write_json(live_dir / "llm_assisted_metric_alias_adjudication_345c2_alias_suggestions.json", suggestions)
    _write_json(live_dir / "llm_assisted_metric_alias_adjudication_345c2_review_required.json", suggestions)
    _write_json(live_dir / "llm_assisted_metric_alias_adjudication_345c2_response_audit.json", {"rows": []})
    (live_dir / "llm_assisted_metric_alias_adjudication_345c2_prompt_audit.md").write_text(
        "# prompt audit",
        encoding="utf-8",
    )
    return live_dir


def test_345c4_ready_path() -> None:
    case_root = _make_case_root()
    try:
        live_dir = _seed_345c2_live_outputs(case_root)
        artifacts = build_alias_suggestion_human_review_package_345c4(
            llm_assisted_metric_alias_adjudication_345c2_live_dir=live_dir,
            output_dir=case_root / "output" / "alias_suggestion_human_review_package_345c4",
            repo_root=case_root,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345C4
        assert manifest["qa_fail_count"] == 0
        assert manifest["review_row_count"] == 3
        assert manifest["llm_propose_new_standard_count"] == 1
        assert manifest["llm_insufficient_evidence_count"] == 1
        assert manifest["validation_failed_count"] == 1
        assert manifest["generated_review_pending_count"] == 3
        assert manifest["generated_approved_count"] == 0
        assert manifest["alias_rule_update_allowed_count"] == 0
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        review_rows = artifacts["review_rows"]
        assert len(review_rows) == 3
        assert all(not row["human_alias_review_decision"] for row in review_rows)
        assert all(row["alias_rule_update_allowed"] is False for row in review_rows)
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c4_missing_required_inputs_fail() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing_live"
        missing_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_alias_suggestion_human_review_package_345c4(
                llm_assisted_metric_alias_adjudication_345c2_live_dir=missing_dir,
                output_dir=case_root / "output" / "alias_suggestion_human_review_package_345c4",
                repo_root=case_root,
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345C2 live inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
