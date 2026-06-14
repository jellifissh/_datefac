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

from datefac.benchmark.reviewed_alias_decision_ingestion_345c5 import (  # noqa: E402
    READY_DECISION_345C5,
    build_reviewed_alias_decision_ingestion_345c5,
)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_reviewed_workbook(path: Path, review_rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([{"section": "x"}]).to_excel(writer, sheet_name="00_README", index=False)
        pd.DataFrame([{"key": "x"}]).to_excel(writer, sheet_name="01_REVIEW_SUMMARY", index=False)
        pd.DataFrame(review_rows).to_excel(writer, sheet_name="02_REVIEW_ROWS", index=False)


def _make_case_root() -> Path:
    base_dir = PROJECT_ROOT / "_codex_test_tmp_reviewed_alias_decision_ingestion_345c5"
    base_dir.mkdir(parents=True, exist_ok=True)
    case_root = base_dir / f"case_{uuid4().hex}"
    case_root.mkdir(parents=True, exist_ok=False)
    return case_root


def _seed_345c4_outputs(root: Path) -> tuple[Path, Path]:
    dir_345c4 = root / "output" / "alias_suggestion_human_review_package_345c4"
    dir_345c4.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "ALIAS_SUGGESTION_HUMAN_REVIEW_PACKAGE_345C4_READY",
        "review_row_count": 4,
    }
    review_rows = [
        {
            "alias_review_row_id": "345c4::review::001",
            "alias_adjudication_id": "345c2::alias::001",
            "raw_metric_name": "Alias A",
            "frequency": 10,
            "alias_candidate_priority": "HIGH",
            "llm_suggested_action": "PROPOSE_NEW_STANDARD_METRIC",
            "llm_suggested_standard_metric": "",
            "llm_suggested_new_standard_metric": "metric_a",
            "llm_confidence": "MEDIUM",
            "human_alias_review_decision": "",
            "approved_standard_metric": "",
            "approved_new_standard_metric": "",
            "alias_reviewer": "",
            "alias_reviewed_at": "",
            "alias_review_notes": "",
            "alias_rule_update_allowed": False,
        },
        {
            "alias_review_row_id": "345c4::review::002",
            "alias_adjudication_id": "345c2::alias::002",
            "raw_metric_name": "Alias B",
            "frequency": 8,
            "alias_candidate_priority": "HIGH",
            "llm_suggested_action": "NEEDS_HUMAN_REVIEW",
            "llm_suggested_standard_metric": "",
            "llm_suggested_new_standard_metric": "",
            "llm_confidence": "LOW",
            "human_alias_review_decision": "",
            "approved_standard_metric": "",
            "approved_new_standard_metric": "",
            "alias_reviewer": "",
            "alias_reviewed_at": "",
            "alias_review_notes": "",
            "alias_rule_update_allowed": False,
        },
        {
            "alias_review_row_id": "345c4::review::003",
            "alias_adjudication_id": "345c2::alias::003",
            "raw_metric_name": "Alias C",
            "frequency": 7,
            "alias_candidate_priority": "LOW",
            "llm_suggested_action": "REJECT_ALIAS",
            "llm_suggested_standard_metric": "",
            "llm_suggested_new_standard_metric": "",
            "llm_confidence": "LOW",
            "human_alias_review_decision": "",
            "approved_standard_metric": "",
            "approved_new_standard_metric": "",
            "alias_reviewer": "",
            "alias_reviewed_at": "",
            "alias_review_notes": "",
            "alias_rule_update_allowed": False,
        },
        {
            "alias_review_row_id": "345c4::review::004",
            "alias_adjudication_id": "345c2::alias::004",
            "raw_metric_name": "Alias D",
            "frequency": 5,
            "alias_candidate_priority": "LOW",
            "llm_suggested_action": "MAP_TO_EXISTING_STANDARD_METRIC",
            "llm_suggested_standard_metric": "revenue",
            "llm_suggested_new_standard_metric": "",
            "llm_confidence": "MEDIUM",
            "human_alias_review_decision": "",
            "approved_standard_metric": "",
            "approved_new_standard_metric": "",
            "alias_reviewer": "",
            "alias_reviewed_at": "",
            "alias_review_notes": "",
            "alias_rule_update_allowed": False,
        },
    ]
    reviewed_rows = [
        {
            **review_rows[0],
            "human_alias_review_decision": "APPROVE_NEW_STANDARD",
            "approved_new_standard_metric": "metric_a",
            "alias_reviewer": "Reviewer",
            "alias_reviewed_at": "2026-06-14",
            "alias_review_notes": "Approved new standard.",
        },
        {
            **review_rows[1],
            "human_alias_review_decision": "NEEDS_MORE_CONTEXT",
            "alias_reviewer": "Reviewer",
            "alias_reviewed_at": "2026-06-14",
            "alias_review_notes": "Need more context.",
        },
        {
            **review_rows[2],
            "human_alias_review_decision": "REJECT_ALIAS",
            "alias_reviewer": "Reviewer",
            "alias_reviewed_at": "2026-06-14",
            "alias_review_notes": "Reject this alias.",
        },
        {
            **review_rows[3],
            "human_alias_review_decision": "APPROVE_EXISTING_MAPPING",
            "approved_standard_metric": "revenue",
            "alias_reviewer": "Reviewer",
            "alias_reviewed_at": "2026-06-14",
            "alias_review_notes": "",
        },
    ]
    _write_json(dir_345c4 / "alias_suggestion_human_review_package_345c4_manifest.json", manifest)
    _write_json(dir_345c4 / "alias_suggestion_human_review_package_345c4_review_rows.json", review_rows)
    (dir_345c4 / "alias_suggestion_human_review_package_345c4.xlsx").write_bytes(b"placeholder")
    reviewed_workbook = dir_345c4 / "alias_suggestion_human_review_package_345c4_reviewed.xlsx"
    _write_reviewed_workbook(reviewed_workbook, reviewed_rows)
    return dir_345c4, reviewed_workbook


def test_345c5_ready_path() -> None:
    case_root = _make_case_root()
    try:
        dir_345c4, reviewed_workbook = _seed_345c4_outputs(case_root)
        artifacts = build_reviewed_alias_decision_ingestion_345c5(
            alias_suggestion_human_review_package_345c4_dir=dir_345c4,
            reviewed_alias_workbook=reviewed_workbook,
            output_dir=case_root / "output" / "reviewed_alias_decision_ingestion_345c5",
            repo_root=case_root,
        )
        manifest = artifacts["manifest"]
        assert manifest["decision"] == READY_DECISION_345C5
        assert manifest["qa_fail_count"] == 0
        assert manifest["reviewed_row_count"] == 4
        assert manifest["approved_existing_mapping_count"] == 1
        assert manifest["approved_new_standard_count"] == 1
        assert manifest["rejected_alias_count"] == 1
        assert manifest["needs_more_context_count"] == 1
        assert manifest["validation_issue_count"] == 0
        assert manifest["apply_simulation_eligible_count"] == 2
        assert manifest["alias_rule_update_allowed_count"] == 0
        assert manifest["formal_client_export_allowed"] is False
        assert manifest["client_ready"] is False
        assert manifest["production_ready"] is False
        assert all(row["alias_rule_update_allowed"] is False for row in artifacts["reviewed_decisions"])
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c5_missing_required_inputs_fail() -> None:
    case_root = _make_case_root()
    try:
        missing_dir = case_root / "missing_345c4"
        missing_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_reviewed_alias_decision_ingestion_345c5(
                alias_suggestion_human_review_package_345c4_dir=missing_dir,
                reviewed_alias_workbook=missing_dir / "missing.xlsx",
                output_dir=case_root / "output" / "reviewed_alias_decision_ingestion_345c5",
                repo_root=case_root,
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("Expected FileNotFoundError for missing 345C4 inputs.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)


def test_345c5_duplicate_ids_fail_clearly() -> None:
    case_root = _make_case_root()
    try:
        dir_345c4, reviewed_workbook = _seed_345c4_outputs(case_root)
        reviewed_rows = pd.read_excel(reviewed_workbook, sheet_name="02_REVIEW_ROWS").to_dict(orient="records")
        reviewed_rows[1]["alias_review_row_id"] = reviewed_rows[0]["alias_review_row_id"]
        _write_reviewed_workbook(reviewed_workbook, reviewed_rows)
        try:
            build_reviewed_alias_decision_ingestion_345c5(
                alias_suggestion_human_review_package_345c4_dir=dir_345c4,
                reviewed_alias_workbook=reviewed_workbook,
                output_dir=case_root / "output" / "reviewed_alias_decision_ingestion_345c5",
                repo_root=case_root,
            )
        except ValueError as exc:
            assert "Duplicate reviewed alias_review_row_id" in str(exc)
        else:
            raise AssertionError("Expected duplicate id failure.")
    finally:
        shutil.rmtree(case_root, ignore_errors=True)
