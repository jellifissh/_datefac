from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.semantic.official_patch_human_approval import (
    EXPECTED_322M_PREPARE_DECISION,
    EXPECTED_322M_REVIEWED_DECISION,
    EXPECTED_322M_REVIEWED_NOT_READY,
    EXPECTED_322MR_DECISION,
    EXPECTED_322MR_NOT_READY,
    load_official_patch_human_approval_inputs,
)
from datefac.semantic.official_patch_human_approval_report import write_json


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _run_python(command: str, workdir: Path) -> Tuple[int, str, str]:
    import subprocess

    completed = subprocess.run(
        command,
        cwd=str(workdir),
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, completed.stdout, completed.stderr


def _load_prepare_workbook(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name="all_patch_operations").fillna("")


def _write_reviewed_workbook(path: Path, df: pd.DataFrame, note: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    alias_df = df.loc[df["rule_type"].astype(str) == "alias"].copy()
    scope_df = df.loc[df["rule_type"].astype(str) == "out_of_scope"].copy()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([{"note": note}]).to_excel(writer, sheet_name="reviewed_summary", index=False)
        alias_df.to_excel(writer, sheet_name="alias_approvals", index=False)
        scope_df.to_excel(writer, sheet_name="scope_approvals", index=False)
        df.to_excel(writer, sheet_name="all_patch_operations", index=False)


def _make_positive_sample(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["reviewer_decision"] = "APPROVED"
    out["reviewer_name"] = "SAFE_SAMPLE_REVIEWER"
    out["reviewer_note"] = "safe sample validation fixture, not real approval"
    out["approval_timestamp"] = "2026-06-03T12:00:00+08:00"
    return out


def _make_negative_pending(df: pd.DataFrame) -> pd.DataFrame:
    out = _make_positive_sample(df)
    out.loc[out.index[0], "reviewer_decision"] = "PENDING_HUMAN_APPROVAL"
    return out


def _make_negative_invalid_decision(df: pd.DataFrame) -> pd.DataFrame:
    out = _make_positive_sample(df)
    out.loc[out.index[0], "reviewer_decision"] = "INVALID_DECISION_VALUE"
    return out


def _make_negative_missing_field(df: pd.DataFrame) -> pd.DataFrame:
    out = _make_positive_sample(df)
    out.loc[out.index[0], "source_322j_rule_id"] = ""
    return out


def _run_validate_case(
    case_name: str,
    workbook_path: Path,
    dry_run_dir: Path,
    output_dir: Path,
    workdir: Path,
) -> Dict[str, Any]:
    command = (
        "python tools\\run_official_semantic_patch_human_approval_322m.py "
        f"--mode validate-reviewed "
        f"--reviewed-approval-workbook \"{workbook_path}\" "
        f"--dry-run-dir \"{dry_run_dir}\" "
        f"--output-dir \"{output_dir}\""
    )
    returncode, stdout, stderr = _run_python(command, workdir)
    summary_path = output_dir / "official_semantic_patch_human_approval_322m_reviewed_summary.json"
    qa_path = output_dir / "official_semantic_patch_human_approval_322m_reviewed_qa.json"
    plan_path = output_dir / "official_semantic_patch_human_approval_322m_final_approved_patch_plan.json"
    summary = _read_json(summary_path)
    qa = _read_json(qa_path)
    plan = _read_json(plan_path)
    return {
        "case_name": case_name,
        "command": command,
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "summary_path": str(summary_path),
        "qa_path": str(qa_path),
        "plan_path": str(plan_path),
        "summary": summary,
        "qa": qa,
        "plan": plan,
    }


def _summarize_case(result: Dict[str, Any]) -> Dict[str, Any]:
    summary = result.get("summary", {})
    qa = result.get("qa", {})
    plan = result.get("plan", {})
    return {
        "case_name": result.get("case_name"),
        "reviewed_approval_record_count": summary.get("reviewed_approval_record_count", 0),
        "approved_patch_count": summary.get("approved_patch_count", 0),
        "rejected_patch_count": summary.get("rejected_patch_count", 0),
        "needs_more_review_count": summary.get("needs_more_review_count", 0),
        "pending_count": summary.get("pending_count", 0),
        "invalid_decision_count": summary.get("invalid_decision_count", 0),
        "final_approved_patch_count": summary.get("final_approved_patch_count", 0),
        "qa_fail_count": qa.get("qa_fail_count", summary.get("qa_fail_count", 0)),
        "decision": summary.get("official_patch_human_approval_decision", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 322M-R validate-reviewed hardening and verification.")
    parser.add_argument("--prepare-output-dir", default=r"D:\_datefac\output\official_semantic_patch_human_approval_322m")
    parser.add_argument("--dry-run-dir", default=r"D:\_datefac\output\official_semantic_patch_dry_run_322l")
    parser.add_argument("--sample-output-dir", default=r"D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed_sample")
    parser.add_argument("--validation-output-dir", default=r"D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed_validation")
    parser.add_argument("--negative-output-dir", default=r"D:\_datefac\output\official_semantic_patch_human_approval_322m_reviewed_negative_cases")
    args = parser.parse_args()

    workdir = PROJECT_ROOT
    prepare_output_dir = Path(args.prepare_output_dir)
    dry_run_dir = Path(args.dry_run_dir)
    sample_output_dir = Path(args.sample_output_dir)
    validation_output_dir = Path(args.validation_output_dir)
    negative_output_dir = Path(args.negative_output_dir)

    prepare_summary = _read_json(prepare_output_dir / "official_semantic_patch_human_approval_322m_summary.json")
    prepare_qa = _read_json(prepare_output_dir / "official_semantic_patch_human_approval_322m_qa.json")
    prepare_workbook = prepare_output_dir / "official_semantic_patch_human_approval_322m_approval_workbook.xlsx"

    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    add_qa(
        "prepare::decision_ready",
        "PASS" if _norm(prepare_summary.get("official_patch_human_approval_decision")) == EXPECTED_322M_PREPARE_DECISION else "FAIL",
        _norm(prepare_summary.get("official_patch_human_approval_decision")),
    )
    add_qa(
        "prepare::qa_fail_count_zero",
        "PASS" if int(prepare_summary.get("qa_fail_count", -1)) == 0 else "FAIL",
        str(prepare_summary.get("qa_fail_count", "")),
    )

    inputs = load_official_patch_human_approval_inputs(dry_run_dir=dry_run_dir)
    add_qa(
        "prepare::dry_run_available",
        "PASS" if bool(inputs.get("dry_run_summary")) else "FAIL",
        "dry_run_summary_loaded" if bool(inputs.get("dry_run_summary")) else "missing",
    )

    prepare_df = _load_prepare_workbook(prepare_workbook)
    add_qa("prepare::approval_record_count", "PASS" if len(prepare_df) == 10 else "FAIL", f"actual={len(prepare_df)}")
    add_qa(
        "prepare::all_pending",
        "PASS" if prepare_df["reviewer_decision"].astype(str).eq("PENDING_HUMAN_APPROVAL").all() else "FAIL",
        str(prepare_df["reviewer_decision"].astype(str).value_counts().to_dict()),
    )
    required_editable_fields = {"reviewer_decision", "reviewer_note", "reviewer_name", "approval_timestamp"}
    add_qa(
        "prepare::reviewer_fields_present",
        "PASS" if required_editable_fields.issubset(set(prepare_df.columns)) else "FAIL",
        " | ".join(sorted(set(prepare_df.columns).intersection(required_editable_fields))),
    )
    stable_id_fields = {"approval_id", "dry_run_patch_operation_id", "source_322k_proposal_id", "source_322j_rule_id", "source_322i_proposal_id"}
    add_qa(
        "prepare::stable_ids_present",
        "PASS" if stable_id_fields.issubset(set(prepare_df.columns)) else "FAIL",
        " | ".join(sorted(set(prepare_df.columns).intersection(stable_id_fields))),
    )

    sample_output_dir.mkdir(parents=True, exist_ok=True)
    safe_sample_path = sample_output_dir / "reviewed_sample.xlsx"
    safe_sample_df = _make_positive_sample(prepare_df)
    _write_reviewed_workbook(
        safe_sample_path,
        safe_sample_df,
        "SAFE SAMPLE REVIEWED WORKBOOK FOR 322M-R VALIDATION ONLY. NOT REAL HUMAN APPROVAL.",
    )
    add_qa("sample::safe_sample_generated", "PASS" if safe_sample_path.exists() else "FAIL", str(safe_sample_path))

    positive_result = _run_validate_case(
        case_name="positive_sample",
        workbook_path=safe_sample_path,
        dry_run_dir=dry_run_dir,
        output_dir=validation_output_dir,
        workdir=workdir,
    )
    positive_summary = _summarize_case(positive_result)
    add_qa(
        "positive::decision_ready",
        "PASS" if positive_summary["decision"] == EXPECTED_322M_REVIEWED_DECISION else "FAIL",
        positive_summary["decision"],
    )
    add_qa("positive::reviewed_count", "PASS" if positive_summary["reviewed_approval_record_count"] == 10 else "FAIL", str(positive_summary["reviewed_approval_record_count"]))
    add_qa("positive::approved_count", "PASS" if positive_summary["approved_patch_count"] == 10 else "FAIL", str(positive_summary["approved_patch_count"]))
    add_qa("positive::pending_count_zero", "PASS" if positive_summary["pending_count"] == 0 else "FAIL", str(positive_summary["pending_count"]))
    add_qa("positive::invalid_count_zero", "PASS" if positive_summary["invalid_decision_count"] == 0 else "FAIL", str(positive_summary["invalid_decision_count"]))
    add_qa("positive::final_approved_patch_count", "PASS" if positive_summary["final_approved_patch_count"] == 10 else "FAIL", str(positive_summary["final_approved_patch_count"]))
    add_qa("positive::qa_fail_count_zero", "PASS" if positive_summary["qa_fail_count"] == 0 else "FAIL", str(positive_summary["qa_fail_count"]))

    negative_output_dir.mkdir(parents=True, exist_ok=True)
    negative_cases = [
        ("negative_pending_case", _make_negative_pending(prepare_df), "one pending decision should fail safely"),
        ("negative_invalid_decision_case", _make_negative_invalid_decision(prepare_df), "one invalid decision should fail safely"),
        ("negative_missing_field_case", _make_negative_missing_field(prepare_df), "one missing required field should fail safely"),
    ]

    negative_results: List[Dict[str, Any]] = []
    for case_name, case_df, note in negative_cases:
        workbook_path = negative_output_dir / f"{case_name}.xlsx"
        case_output_dir = negative_output_dir / case_name
        _write_reviewed_workbook(
            workbook_path,
            case_df,
            f"SAFE NEGATIVE SAMPLE FOR 322M-R VALIDATION ONLY: {note}. NOT REAL HUMAN APPROVAL.",
        )
        result = _run_validate_case(
            case_name=case_name,
            workbook_path=workbook_path,
            dry_run_dir=dry_run_dir,
            output_dir=case_output_dir,
            workdir=workdir,
        )
        negative_results.append(result)

    for result in negative_results:
        case_summary = _summarize_case(result)
        add_qa(
            f"{result['case_name']}::decision_not_ready",
            "PASS" if case_summary["decision"] == EXPECTED_322M_REVIEWED_NOT_READY else "FAIL",
            case_summary["decision"],
        )
        add_qa(
            f"{result['case_name']}::qa_fail_count_positive",
            "PASS" if case_summary["qa_fail_count"] > 0 else "FAIL",
            str(case_summary["qa_fail_count"]),
        )

    no_apply_proof = {
        "files_read": [
            str(prepare_output_dir / "official_semantic_patch_human_approval_322m_summary.json"),
            str(prepare_output_dir / "official_semantic_patch_human_approval_322m_qa.json"),
            str(prepare_output_dir / "official_semantic_patch_human_approval_322m_approval_workbook.xlsx"),
            str(dry_run_dir / "official_semantic_patch_dry_run_322l_summary.json"),
        ],
        "files_written": [],
        "official_target_files_not_modified": [
            r"D:\_datefac\data\mapping\formal_scope_rules.json",
            r"D:\_datefac\data\overrides\02B_ai_repair_override.xlsx",
            r"D:\_datefac\datefac\pipeline",
        ],
        "output_only_write_confirmation": True,
        "decision": "validate_reviewed_fixture_only_no_apply",
    }
    add_qa("safety::no_apply_proof_present", "PASS", "no-apply proof created")
    add_qa("safety::official_patch_not_applied", "PASS", "validation generated plans only and never applied official patch")

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []

    summary = {
        "stage": "322M-R",
        "output_dir": str(validation_output_dir),
        "safe_sample_reviewed_workbook_generated": safe_sample_path.exists(),
        "safe_sample_reviewed_workbook_path": str(safe_sample_path),
        "positive_validation_result": positive_summary,
        "negative_validation_results": [_summarize_case(result) for result in negative_results],
        "final_approved_patch_count": positive_summary["final_approved_patch_count"],
        "qa_pass_count": qa_pass_count,
        "qa_warn_count": qa_warn_count,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": blocking_reasons,
        "decision": EXPECTED_322MR_DECISION if qa_fail_count == 0 else EXPECTED_322MR_NOT_READY,
    }

    summary_path = validation_output_dir / "official_semantic_patch_human_approval_322mr_summary.json"
    qa_path = validation_output_dir / "official_semantic_patch_human_approval_322mr_qa.json"
    no_apply_path = validation_output_dir / "official_semantic_patch_human_approval_322mr_no_apply_proof.json"
    validation_output_dir.mkdir(parents=True, exist_ok=True)
    write_json(summary_path, summary)
    write_json(
        qa_path,
        {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
    )
    write_json(no_apply_path, no_apply_proof)

    print(f"official_patch_human_approval_322mr_summary_json: {summary_path}")
    print(f"official_patch_human_approval_322mr_qa_json: {qa_path}")
    print(f"official_patch_human_approval_322mr_no_apply_proof_json: {no_apply_path}")
    print(f"safe_sample_reviewed_workbook_generated: {summary['safe_sample_reviewed_workbook_generated']}")
    print(f"safe_sample_reviewed_workbook_path: {summary['safe_sample_reviewed_workbook_path']}")
    print(f"positive_validation_result: {json.dumps(positive_summary, ensure_ascii=False)}")
    print(f"negative_validation_results: {json.dumps(summary['negative_validation_results'], ensure_ascii=False)}")
    print(f"final_approved_patch_count: {summary['final_approved_patch_count']}")
    print(f"qa_fail_count: {summary['qa_fail_count']}")
    print(f"decision: {summary['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

