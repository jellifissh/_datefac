import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rebuild_stage5k_full_sandbox_02_05_from_pdf as s5k

BASE_DIR = Path(r"D:\_datefac")
IN_DIR = BASE_DIR / "output" / "stage7z_controlled_sample_exclusion_readiness_gate"

IN_SUMMARY = IN_DIR / "213_stage7z_controlled_sample_exclusion_summary.json"
IN_REPORT = IN_DIR / "213_stage7z_controlled_sample_exclusion_report.md"
IN_CLASSIFICATION = IN_DIR / "213_stage7z_candidate_source_classification.xlsx"
IN_BLOCKER = IN_DIR / "213_stage7z_production_preflight_blocker.json"
IN_CHECKLIST = IN_DIR / "213_stage7z_real_second_review_readiness_checklist.json"
IN_INSTRUCTIONS = IN_DIR / "213_stage7z_real_second_review_intake_instructions.md"
IN_NO_APPLY = IN_DIR / "213_stage7z_no_apply_proof.json"

REAL_INPUT_DIR = BASE_DIR / "input" / "real_second_review"
REAL_INPUT_PATH = REAL_INPUT_DIR / "stage8a_real_second_review_input.xlsx"
README_PATH = REAL_INPUT_DIR / "README_REAL_SECOND_REVIEW_INPUT.md"

OUT_DIR = BASE_DIR / "output" / "stage8a_real_second_review_input_intake_gate"
OUT_SUMMARY = OUT_DIR / "214_stage8a_real_second_review_intake_summary.json"
OUT_REPORT = OUT_DIR / "214_stage8a_real_second_review_intake_report.md"
OUT_MANIFEST = OUT_DIR / "214_stage8a_real_second_review_intake_manifest.json"
OUT_SHALLOW = OUT_DIR / "214_stage8a_real_input_shallow_check.json"
OUT_NO_APPLY = OUT_DIR / "214_stage8a_no_apply_proof.json"

OFFICIAL_02B = BASE_DIR / "data" / "overrides" / "02B_ai_repair_override.xlsx"
FORMAL_SCOPE_RULES = BASE_DIR / "data" / "mapping" / "formal_scope_rules.json"
STANDARDIZER_FILE = BASE_DIR / "financial_standardizer.py"
RELEASE_ZIP = BASE_DIR / "output" / "release_package" / "stage6b_final_release.zip"

EXPECTED_SCHEMA_VERSION = "stage7w_second_review_input_v1"
EXPECTED_SHEET_NAME = "second_review_input_template"
SOURCE_TEMPLATE_PATH = BASE_DIR / "output" / "stage7w_second_review_needs_more_info_package" / "210_stage7w_second_review_input_template.xlsx"

REQUIRED_COLUMNS = [
    "schema_version",
    "queue_item_id",
    "suggestion_id",
    "source_pdf",
    "source_page",
    "source_row_reference",
    "statement_type",
    "fiscal_year",
    "original_metric_name",
    "suggested_metric_name",
    "suggested_value",
    "suggested_unit",
    "existing_metric_name",
    "existing_value",
    "existing_unit",
    "conflict_type",
    "value_mismatch",
    "prior_stage_status",
    "second_reviewer_id",
    "second_reviewer_role",
    "second_review_decision",
    "second_review_reason_code",
    "second_review_notes",
    "source_row_rechecked",
    "fiscal_year_rechecked",
    "unit_rechecked",
    "value_rechecked",
    "original_pdf_evidence_checked",
    "corrected_metric_name",
    "corrected_value",
    "corrected_unit",
    "corrected_fiscal_year",
    "remaining_question",
    "reviewed_at_utc",
]

FORBIDDEN_FIELDS = [
    "safe_to_apply",
    "approve_for_real_apply",
    "real_apply",
    "write_production",
]

ALLOWED_DECISIONS = [
    "CONFIRM_NEEDS_MORE_INFO",
    "CONFIRM_REJECT",
    "APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE",
    "ESCALATE_TO_MANUAL_ACCOUNTING_REVIEW",
]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    if isinstance(v, str) and v.strip().lower() == "nan":
        return ""
    return str(v).strip()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot_hashes() -> Dict[str, str]:
    snap = s5k._snapshot_hashes()
    snap["official_02b"] = _sha256(OFFICIAL_02B)
    snap["formal_rules"] = _sha256(FORMAL_SCOPE_RULES)
    snap["standardizer"] = _sha256(STANDARDIZER_FILE)
    snap["release_zip"] = _sha256(RELEASE_ZIP)
    return snap


def _run_delivery_check() -> Dict[str, Any]:
    import subprocess

    p = subprocess.run(
        [sys.executable, str(BASE_DIR / "tools" / "check_delivery_state.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = (p.stdout or "").strip()
    return json.loads(txt) if txt else {"overall_status": "UNKNOWN"}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    required = [
        IN_SUMMARY,
        IN_REPORT,
        IN_CLASSIFICATION,
        IN_BLOCKER,
        IN_CHECKLIST,
        IN_INSTRUCTIONS,
        IN_NO_APPLY,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        _write_json(
            OUT_SUMMARY,
            {
                "stage": "8A",
                "external_api_called": False,
                "real_apply_executed": False,
                "stage7z_summary_loaded": False,
                "blocked": True,
                "blocked_reason": f"missing_input:{'|'.join(missing)}",
            },
        )
        print("stage8a_status=blocked_missing_input")
        return 0

    before = _snapshot_hashes()

    s7z = _load_json(IN_SUMMARY)
    _ = IN_REPORT.read_text(encoding="utf-8")
    _ = pd.read_excel(IN_CLASSIFICATION)
    blocker = _load_json(IN_BLOCKER)
    _ = _load_json(IN_CHECKLIST)
    _ = IN_INSTRUCTIONS.read_text(encoding="utf-8")
    _ = _load_json(IN_NO_APPLY)

    stage7z_summary_loaded = True
    stage7z_gate_verified = bool(
        s7z.get("external_api_called") is False
        and s7z.get("real_apply_executed") is False
        and int(s7z.get("controlled_sample_candidate_count", -1)) == 1
        and int(s7z.get("production_approval_candidate_count", -1)) == 0
        and int(s7z.get("unknown_source_candidate_count", -1)) == 0
        and s7z.get("controlled_sample_candidate_excluded_from_production") is True
        and s7z.get("production_preflight_allowed") is False
        and _norm(s7z.get("production_preflight_blocked_reason")) == "no_real_second_review_production_candidate"
        and s7z.get("real_second_review_input_required") is True
        and s7z.get("real_second_review_readiness_checklist_generated") is True
        and s7z.get("real_second_review_intake_instructions_generated") is True
        and int(s7z.get("sandbox_apply_attempt_count", -1)) == 0
        and int(s7z.get("sandbox_apply_success_count", -1)) == 0
        and int(s7z.get("production_apply_attempt_count", -1)) == 0
        and int(s7z.get("fabricated_candidate_count", -1)) == 0
        and int(s7z.get("blocked_value_mismatch_auto_apply_count", -1)) == 0
        and int(s7z.get("approve_for_real_apply_detected_count", -1)) == 0
        and int(s7z.get("safe_to_apply_human_field_detected_count", -1)) == 0
        and s7z.get("ready_for_real_second_review_input_collection") is True
        and s7z.get("ready_for_production_preflight") is False
        and _norm(s7z.get("check_delivery_state_overall_status")) == "PASS"
        and blocker.get("production_preflight_allowed") is False
    )

    REAL_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    intake_directory_ready = REAL_INPUT_DIR.exists()

    readme_lines = [
        "# Real Second Review Input (Stage 8A)",
        "",
        "This folder is for **real** second-review human input only.",
        "",
        "## Steps",
        "1. Copy the Stage 7W template:",
        f"   - `{SOURCE_TEMPLATE_PATH}`",
        "2. Fill with real second reviewer information.",
        f"3. Save as: `{REAL_INPUT_PATH}`",
        "",
        "## Mandatory Rules",
        "- Do not edit immutable queue fields.",
        "- Do not add `safe_to_apply`.",
        "- Do not use `APPROVE_FOR_REAL_APPLY`.",
        "- `APPROVE_FOR_SANDBOX_PREVIEW_CANDIDATE` only creates a future sandbox preview candidate; it is not production apply.",
        "",
        "## Rerun Sequence After Real Input",
        "1. `python tools/run_stage7x_second_review_input_validation.py`",
        "2. `python tools/run_stage7y_sandbox_preview_candidate_preflight.py`",
        "3. `python tools/run_stage7z_controlled_sample_exclusion_readiness_gate.py`",
        "4. `python tools/run_stage8b_real_second_review_validation.py` (future stage)",
    ]
    README_PATH.write_text("\n".join(readme_lines), encoding="utf-8")

    manifest = {
        "stage": "8A",
        "expected_real_input_path": str(REAL_INPUT_PATH),
        "expected_schema_version": EXPECTED_SCHEMA_VERSION,
        "required_sheet_name": EXPECTED_SHEET_NAME,
        "required_columns": REQUIRED_COLUMNS,
        "forbidden_fields": FORBIDDEN_FIELDS,
        "allowed_second_review_decisions": ALLOWED_DECISIONS,
        "source_template_path": str(SOURCE_TEMPLATE_PATH),
        "rerun_sequence_after_real_input": [
            "tools/run_stage7x_second_review_input_validation.py",
            "tools/run_stage7y_sandbox_preview_candidate_preflight.py",
            "tools/run_stage7z_controlled_sample_exclusion_readiness_gate.py",
            "tools/run_stage8b_real_second_review_validation.py",
        ],
    }
    _write_json(OUT_MANIFEST, manifest)

    real_second_review_input_present = REAL_INPUT_PATH.exists()
    real_second_review_input_readable = False
    shallow_schema_check_pass = False
    intake_status = "BLOCKED_WAITING_FOR_REAL_INPUT"
    row_count = 0
    missing_required_columns: List[str] = []
    forbidden_columns_present: List[str] = []
    schema_version_values: List[str] = []
    sheet_name_loaded = ""
    shallow_errors: List[str] = []

    if real_second_review_input_present:
        try:
            xl = pd.ExcelFile(REAL_INPUT_PATH)
            target_sheet = EXPECTED_SHEET_NAME if EXPECTED_SHEET_NAME in xl.sheet_names else xl.sheet_names[0]
            sheet_name_loaded = target_sheet
            df = pd.read_excel(REAL_INPUT_PATH, sheet_name=target_sheet)
            real_second_review_input_readable = True
            row_count = len(df)
            cols = list(df.columns)
            missing_required_columns = [c for c in REQUIRED_COLUMNS if c not in cols]
            forbidden_columns_present = [c for c in cols if c.lower() in {f.lower() for f in FORBIDDEN_FIELDS}]

            if "schema_version" in df.columns:
                schema_version_values = sorted({_norm(v) for v in df["schema_version"].tolist() if _norm(v)})
            else:
                schema_version_values = []

            if row_count <= 0:
                shallow_errors.append("row_count_not_positive")
            if missing_required_columns:
                shallow_errors.append("missing_required_columns")
            if forbidden_columns_present:
                shallow_errors.append("forbidden_columns_present")
            if not schema_version_values:
                shallow_errors.append("schema_version_values_missing")
            elif any(v != EXPECTED_SCHEMA_VERSION for v in schema_version_values):
                shallow_errors.append("schema_version_values_invalid")

            shallow_schema_check_pass = len(shallow_errors) == 0
            intake_status = "READY_FOR_STAGE8B_SHALLOW_CHECK_PASS" if shallow_schema_check_pass else "BLOCKED_SHALLOW_CHECK_FAILED"
        except Exception as exc:
            real_second_review_input_readable = False
            shallow_schema_check_pass = False
            intake_status = "BLOCKED_REAL_INPUT_UNREADABLE"
            shallow_errors.append(f"read_exception:{type(exc).__name__}")

    shallow = {
        "real_second_review_input_path": str(REAL_INPUT_PATH),
        "real_second_review_input_present": real_second_review_input_present,
        "real_second_review_input_readable": real_second_review_input_readable,
        "required_sheet_name": EXPECTED_SHEET_NAME,
        "sheet_name_loaded": sheet_name_loaded,
        "row_count": row_count,
        "missing_required_columns": missing_required_columns,
        "forbidden_columns_present": forbidden_columns_present,
        "schema_version_values": schema_version_values,
        "shallow_schema_check_pass": shallow_schema_check_pass,
        "intake_status": intake_status,
        "errors": shallow_errors,
    }
    _write_json(OUT_SHALLOW, shallow)

    _write_json(
        OUT_NO_APPLY,
        {
            "external_api_called": False,
            "real_apply_executed": False,
            "sandbox_apply_attempt_count": 0,
            "sandbox_apply_success_count": 0,
            "production_apply_attempt_count": 0,
            "production_apply_success_count": 0,
            "note": "Stage 8A is intake gate only; no apply actions.",
        },
    )

    after = _snapshot_hashes()
    production_files_modified = any(before[k] != after[k] for k in ["01", "02", "02A", "05", "06"])
    official_02b_modified = before["official_02b"] != after["official_02b"]
    formal_rules_modified = before["formal_rules"] != after["formal_rules"]
    standardizer_modified = before["standardizer"] != after["standardizer"]
    release_package_modified = before["release_zip"] != after["release_zip"]

    delivery = _run_delivery_check()

    ready_for_stage8b_real_second_review_validation = bool(shallow_schema_check_pass)

    summary = {
        "stage": "8A",
        "external_api_called": False,
        "real_apply_executed": False,
        "sandbox_apply_attempt_count": 0,
        "production_apply_attempt_count": 0,
        "stage7z_summary_loaded": stage7z_summary_loaded,
        "stage7z_gate_verified": stage7z_gate_verified,
        "intake_directory_ready": intake_directory_ready,
        "real_second_review_input_path": str(REAL_INPUT_PATH),
        "real_second_review_input_present": real_second_review_input_present,
        "real_second_review_input_readable": real_second_review_input_readable,
        "shallow_schema_check_pass": shallow_schema_check_pass,
        "intake_status": intake_status,
        "intake_manifest_generated": True,
        "human_readme_generated": True,
        "controlled_sample_candidate_count": int(s7z.get("controlled_sample_candidate_count", 0)),
        "production_approval_candidate_count": int(s7z.get("production_approval_candidate_count", 0)),
        "production_preflight_allowed": False,
        "ready_for_stage8b_real_second_review_validation": ready_for_stage8b_real_second_review_validation,
        "ready_for_production_preflight": False,
        "production_files_modified": production_files_modified,
        "official_02b_modified": official_02b_modified,
        "formal_rules_modified": formal_rules_modified,
        "standardizer_modified": standardizer_modified,
        "release_package_modified": release_package_modified,
        "check_delivery_state_overall_status": _norm(delivery.get("overall_status")),
    }
    _write_json(OUT_SUMMARY, summary)

    report_lines = [
        "# Stage 8A Real Second-Review Input Intake Gate",
        "",
        "Mode: no API call, no sandbox apply, no real apply, no production write.",
        "",
        "## Stage7Z Gate",
        f"- stage7z_gate_verified: {stage7z_gate_verified}",
        "",
        "## Intake Status",
        f"- real_second_review_input_path: {REAL_INPUT_PATH}",
        f"- real_second_review_input_present: {real_second_review_input_present}",
        f"- real_second_review_input_readable: {real_second_review_input_readable}",
        f"- shallow_schema_check_pass: {shallow_schema_check_pass}",
        f"- intake_status: {intake_status}",
        "",
        "## Notes",
        "- Controlled sample candidates remain excluded from production path.",
        "- Stage 8A does not create or infer fake real approvals.",
    ]
    OUT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print("stage8a_status=ok")
    print(f"stage8a_summary={OUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
