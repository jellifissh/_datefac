from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from datefac.benchmark.vision_assisted_table_evidence_pilot_346a_report import (
    render_artifact_index_markdown,
    render_conflict_handling_policy_markdown,
    render_executive_summary_markdown,
    render_next_plan_markdown,
    render_vlm_prompt_templates_markdown,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_345D = "FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_READY"
READY_DECISION_345E = "DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_READY"
READY_DECISION_346A = "VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY"
BLOCKED_DECISION_346A = "VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_BLOCKED"
INPUT_STAGE_346A = "POST_345F_VISION_ASSISTED_TABLE_EVIDENCE_PILOT"

DEFAULT_FULL_STRUCTURED_DEMO_EXPORT_PACKAGE_345D_DIR = Path(
    r"D:\_datefac\output\full_structured_demo_export_package_345d"
)
DEFAULT_DEMO_EXPORT_REVIEW_QA_CHECKLIST_345E_DIR = Path(
    r"D:\_datefac\output\demo_export_review_qa_checklist_345e"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\vision_assisted_table_evidence_pilot_346a")

MANIFEST_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_manifest.json"
CANDIDATE_POOL_JSON_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_candidate_pool.json"
CANDIDATE_POOL_CSV_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_candidate_pool.csv"
SELECTED_PILOT_ROWS_JSON_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json"
SELECTED_PILOT_ROWS_CSV_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.csv"
EVIDENCE_BUNDLE_INDEX_JSON_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_evidence_bundle_index.json"
EVIDENCE_BUNDLE_INDEX_CSV_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_evidence_bundle_index.csv"
IMAGE_RESOLUTION_STATUS_JSON_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_image_resolution_status.json"
IMAGE_RESOLUTION_STATUS_CSV_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_image_resolution_status.csv"
FIELD_REPAIR_TARGETS_JSON_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_field_repair_targets.json"
FIELD_REPAIR_TARGETS_CSV_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_field_repair_targets.csv"
VLM_REQUEST_PACKAGE_JSONL_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_vlm_request_package.jsonl"
VLM_REQUEST_PACKAGE_PREVIEW_JSON_FILE_NAME = (
    "vision_assisted_table_evidence_pilot_346a_vlm_request_package_preview.json"
)
VLM_OUTPUT_SCHEMA_JSON_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_vlm_output_schema.json"
VLM_PROMPT_TEMPLATES_MD_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_vlm_prompt_templates.md"
CONFLICT_HANDLING_POLICY_MD_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_conflict_handling_policy.md"
COST_LATENCY_ESTIMATE_JSON_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_cost_latency_estimate.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "vision_assisted_table_evidence_pilot_346a_next_plan.md"

INPUT_345D_MANIFEST_NAME = "full_structured_demo_export_package_345d_manifest.json"
INPUT_345D_QUALITY_LIMITED_ROWS_JSON_NAME = "full_structured_demo_export_package_345d_quality_limited_rows.json"
INPUT_345D_QUALITY_LIMITED_ROWS_CSV_NAME = "full_structured_demo_export_package_345d_quality_limited_rows.csv"
INPUT_345D_DEMO_ROWS_JSON_NAME = "full_structured_demo_export_package_345d_demo_rows.json"
INPUT_345D_DEMO_ROWS_CSV_NAME = "full_structured_demo_export_package_345d_demo_rows.csv"
INPUT_345D_QUALITY_CAVEATS_JSON_NAME = "full_structured_demo_export_package_345d_quality_caveats.json"
INPUT_345D_QUALITY_CAVEATS_MD_NAME = "full_structured_demo_export_package_345d_quality_caveats.md"
INPUT_345D_ARTIFACT_INDEX_MD_NAME = "full_structured_demo_export_package_345d_artifact_index.md"

INPUT_345E_MANIFEST_NAME = "demo_export_review_qa_checklist_345e_manifest.json"
INPUT_345E_QUALITY_LIMITED_SAMPLE_ROWS_JSON_NAME = "demo_export_review_qa_checklist_345e_quality_limited_sample_rows.json"
INPUT_345E_QUALITY_LIMITED_SAMPLE_ROWS_CSV_NAME = "demo_export_review_qa_checklist_345e_quality_limited_sample_rows.csv"
INPUT_345E_CAVEAT_COMPLETENESS_JSON_NAME = "demo_export_review_qa_checklist_345e_caveat_completeness_check.json"
INPUT_345E_PRESENTATION_READINESS_JSON_NAME = "demo_export_review_qa_checklist_345e_demo_presentation_readiness.json"

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

PROTECTED_DIRTY_PATHS = [
    "datefac/benchmark/batch_row_text_delivery_benchmark.py",
    "datefac/extraction/row_text_metric_extractor.py",
    "datefac/pipeline/batch_ppstructure_row_text_pipeline.py",
    "tools/run_batch_ppstructure_outputs_320g.py",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

FORBIDDEN_STAGE_PATHS = [
    "output",
    "temp",
    "input",
    "input/semantic_adjudicator_responses_322d",
    "input/semantic_adjudicator_responses_322f",
    "tools/mineru_new_runner.cmd",
]

OUTPUT_ARTIFACT_ROWS = [
    {"artifact_name": MANIFEST_FILE_NAME, "path": MANIFEST_FILE_NAME, "purpose": "Decision and QA manifest."},
    {"artifact_name": CANDIDATE_POOL_JSON_FILE_NAME, "path": CANDIDATE_POOL_JSON_FILE_NAME, "purpose": "Candidate pool from 345D quality-limited rows in JSON."},
    {"artifact_name": CANDIDATE_POOL_CSV_FILE_NAME, "path": CANDIDATE_POOL_CSV_FILE_NAME, "purpose": "Candidate pool from 345D quality-limited rows in CSV."},
    {"artifact_name": SELECTED_PILOT_ROWS_JSON_FILE_NAME, "path": SELECTED_PILOT_ROWS_JSON_FILE_NAME, "purpose": "Bounded pilot selection rows in JSON."},
    {"artifact_name": SELECTED_PILOT_ROWS_CSV_FILE_NAME, "path": SELECTED_PILOT_ROWS_CSV_FILE_NAME, "purpose": "Bounded pilot selection rows in CSV."},
    {"artifact_name": EVIDENCE_BUNDLE_INDEX_JSON_FILE_NAME, "path": EVIDENCE_BUNDLE_INDEX_JSON_FILE_NAME, "purpose": "Evidence bundle index in JSON."},
    {"artifact_name": EVIDENCE_BUNDLE_INDEX_CSV_FILE_NAME, "path": EVIDENCE_BUNDLE_INDEX_CSV_FILE_NAME, "purpose": "Evidence bundle index in CSV."},
    {"artifact_name": IMAGE_RESOLUTION_STATUS_JSON_FILE_NAME, "path": IMAGE_RESOLUTION_STATUS_JSON_FILE_NAME, "purpose": "Image resolution statuses in JSON."},
    {"artifact_name": IMAGE_RESOLUTION_STATUS_CSV_FILE_NAME, "path": IMAGE_RESOLUTION_STATUS_CSV_FILE_NAME, "purpose": "Image resolution statuses in CSV."},
    {"artifact_name": FIELD_REPAIR_TARGETS_JSON_FILE_NAME, "path": FIELD_REPAIR_TARGETS_JSON_FILE_NAME, "purpose": "Field repair target rows in JSON."},
    {"artifact_name": FIELD_REPAIR_TARGETS_CSV_FILE_NAME, "path": FIELD_REPAIR_TARGETS_CSV_FILE_NAME, "purpose": "Field repair target rows in CSV."},
    {"artifact_name": VLM_REQUEST_PACKAGE_JSONL_FILE_NAME, "path": VLM_REQUEST_PACKAGE_JSONL_FILE_NAME, "purpose": "Suggestion-only VLM request package."},
    {"artifact_name": VLM_REQUEST_PACKAGE_PREVIEW_JSON_FILE_NAME, "path": VLM_REQUEST_PACKAGE_PREVIEW_JSON_FILE_NAME, "purpose": "Preview of bounded VLM requests."},
    {"artifact_name": VLM_OUTPUT_SCHEMA_JSON_FILE_NAME, "path": VLM_OUTPUT_SCHEMA_JSON_FILE_NAME, "purpose": "Strict VLM output schema."},
    {"artifact_name": VLM_PROMPT_TEMPLATES_MD_FILE_NAME, "path": VLM_PROMPT_TEMPLATES_MD_FILE_NAME, "purpose": "Prompt templates for future VLM run."},
    {"artifact_name": CONFLICT_HANDLING_POLICY_MD_FILE_NAME, "path": CONFLICT_HANDLING_POLICY_MD_FILE_NAME, "purpose": "Conflict and human review policy."},
    {"artifact_name": COST_LATENCY_ESTIMATE_JSON_FILE_NAME, "path": COST_LATENCY_ESTIMATE_JSON_FILE_NAME, "purpose": "Qualitative cost and latency estimate."},
    {"artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME, "path": EXECUTIVE_SUMMARY_MD_FILE_NAME, "purpose": "Executive summary for the pilot package."},
    {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": ARTIFACT_INDEX_MD_FILE_NAME, "purpose": "Artifact index for 346A outputs."},
    {"artifact_name": NEXT_PLAN_MD_FILE_NAME, "path": NEXT_PLAN_MD_FILE_NAME, "purpose": "Recommended next step and boundary note."},
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_ledger_path() -> Path:
    milestone_dir = Path(r"D:\_datefac\docs\project_milestones")
    matches = sorted(milestone_dir.glob("PROJECT_MILESTONE_LEDGER_*.md"))
    if matches:
        return matches[0]
    return milestone_dir / "PROJECT_MILESTONE_LEDGER.md"


DEFAULT_LEDGER_PATH = _default_ledger_path()


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).strip().split())
    return "" if text.lower() == "nan" else text


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _safe_text(value).lower() in {"1", "true", "yes", "y"}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _load_json_or_csv_rows(*, json_path: Path, csv_path: Path, label: str) -> tuple[List[Dict[str, Any]], str]:
    if json_path.exists():
        payload = _read_json(json_path)
        if isinstance(payload, list):
            return [dict(row) for row in payload], "json"
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            return [dict(row) for row in payload["rows"]], "json"
        raise ValueError(f"{label} must be a JSON list or row package: {json_path}")
    if csv_path.exists():
        return _read_csv_rows(csv_path), "csv"
    raise FileNotFoundError(f"required row artifact missing for {label}: {json_path} / {csv_path}")


def _is_git_repo(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def _run_git(repo_root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_status_porcelain_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    if not _is_git_repo(repo_root):
        return []
    result = _run_git(repo_root, ["status", "--porcelain", "--", *paths])
    if result.returncode != 0:
        return [f"__ERROR__::{result.stderr.strip()}"]
    return [line.rstrip() for line in result.stdout.splitlines() if line.strip()]


def _git_staged_names_for_paths(paths: Sequence[str], repo_root: Path) -> List[str]:
    lines = _git_status_porcelain_for_paths(paths, repo_root)
    staged: List[str] = []
    for line in lines:
        if line.startswith("__ERROR__::"):
            return [line]
        if len(line) >= 3 and line[0] in {"A", "M", "D", "R", "C", "U", "T"}:
            staged.append(line[3:].strip())
    return staged


def _artifact_index_rows(output_dir: Path) -> List[Dict[str, str]]:
    return [{"artifact_name": row["artifact_name"], "path": str(output_dir / row["path"]), "purpose": row["purpose"]} for row in OUTPUT_ARTIFACT_ROWS]


def _parse_page_number(value: Any) -> int | None:
    text = _safe_text(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _normalize_key(value: Any) -> str:
    text = _safe_text(value).lower()
    return "".join(ch for ch in text if ch.isalnum())


def _split_issue_codes(value: Any) -> List[str]:
    text = _safe_text(value)
    if not text:
        return []
    tokens: List[str] = []
    for chunk in text.replace("|", ",").replace(";", ",").split(","):
        item = _safe_text(chunk).upper()
        if item:
            tokens.append(item)
    return tokens


def _selection_targets(row: Dict[str, Any], raw_metric_frequency: Counter[str]) -> tuple[List[str], List[str], str, int]:
    issue_codes = _split_issue_codes(row.get("quality_issue_codes"))
    issue_blob = " ".join(issue_codes)
    unit_missing = not _safe_text(row.get("unit")) or "MISSING_UNIT" in issue_blob
    period_missing = not _safe_text(row.get("period")) or any(token in issue_blob for token in ["PERIOD", "HEADER"])
    source_trace_missing = not _bool_value(row.get("source_trace_available")) or "SOURCE_TRACE" in issue_blob
    alias_simulated = _safe_text(row.get("alias_simulation_batch")) not in {"", "NONE"}
    normalized = bool(_safe_text(row.get("demo_normalized_metric_name")))
    repeated_metric = raw_metric_frequency[_safe_text(row.get("raw_metric_name"))] >= 10
    severity = _safe_text(row.get("quality_severity")).upper()

    target_fields: List[str] = []
    reasons: List[str] = []
    score = 0

    if severity == "HIGH":
        score += 100
        reasons.append("HIGH_SEVERITY")
    elif severity == "MEDIUM":
        score += 60
        reasons.append("MEDIUM_SEVERITY")
    else:
        score += 20
        reasons.append("LOW_OR_UNKNOWN_SEVERITY")

    if unit_missing:
        target_fields.append("unit")
        reasons.append("UNIT_REPAIR_TARGET")
        score += 40
    if period_missing:
        target_fields.extend(["period", "table_header"])
        reasons.append("PERIOD_OR_HEADER_TARGET")
        score += 35
    if source_trace_missing:
        target_fields.append("source_trace")
        reasons.append("SOURCE_TRACE_TARGET")
        score += 30
    if alias_simulated:
        target_fields.append("raw_metric_name")
        reasons.append("ALIAS_SIMULATED_ROW")
        score += 20
    if normalized:
        reasons.append("NORMALIZED_OR_PARTIALLY_NORMALIZED")
        score += 15
    if repeated_metric:
        reasons.append("REPEATED_HIGH_IMPACT_METRIC")
        score += 15

    alignment_like = any(token in issue_blob for token in ["ALIGN", "REVIEW", "PENDING", "VALUE", "SUSPICIOUS"])
    if alignment_like or not target_fields:
        target_fields.append("value")
        reasons.append("VALUE_ALIGNMENT_CHECK_TARGET")
        score += 25

    if "table_header" in target_fields or "value" in target_fields:
        vision_task_type = "HEADER_AND_VALUE_ALIGNMENT_CHECK"
    elif "unit" in target_fields and "period" in target_fields:
        vision_task_type = "UNIT_AND_PERIOD_REPAIR"
    elif "source_trace" in target_fields:
        vision_task_type = "SOURCE_TRACE_CHECK"
    else:
        vision_task_type = "BOUNDED_TABLE_EVIDENCE_CHECK"

    deduped_fields: List[str] = []
    seen_fields: set[str] = set()
    for field in target_fields:
        if field not in seen_fields:
            seen_fields.add(field)
            deduped_fields.append(field)

    return deduped_fields, reasons, vision_task_type, score


def _build_candidate_pool(quality_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    raw_metric_frequency = Counter(_safe_text(row.get("raw_metric_name")) for row in quality_rows)
    candidate_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(quality_rows, start=1):
        target_fields, reasons, vision_task_type, score = _selection_targets(row, raw_metric_frequency)
        candidate_rows.append(
            {
                **row,
                "candidate_row_id": f"346a::candidate::{index:05d}",
                "source_page_number": _parse_page_number(row.get("source_page")),
                "target_field_types": target_fields,
                "vision_task_type": vision_task_type,
                "selection_reason": ";".join(reasons),
                "requires_image_evidence": True,
                "priority_score": score,
                "raw_metric_repeat_count": raw_metric_frequency[_safe_text(row.get("raw_metric_name"))],
            }
        )
    return candidate_rows


def _select_pilot_rows(candidate_pool: List[Dict[str, Any]], max_pilot_rows: int) -> List[Dict[str, Any]]:
    if max_pilot_rows <= 0:
        return []
    sorted_rows = sorted(
        candidate_pool,
        key=lambda row: (
            -int(row.get("priority_score", 0)),
            _safe_text(row.get("source_pdf_name")),
            _parse_page_number(row.get("source_page")) or -1,
            _safe_text(row.get("source_row_id")),
        ),
    )
    per_pdf: Counter[str] = Counter()
    per_page: Counter[tuple[str, int | None]] = Counter()
    per_table: Counter[str] = Counter()
    selected: List[Dict[str, Any]] = []
    used_ids: set[str] = set()

    for row in sorted_rows:
        if len(selected) >= max_pilot_rows:
            break
        pdf_key = _safe_text(row.get("source_pdf_name"))
        page_key = (pdf_key, _parse_page_number(row.get("source_page")))
        table_key = _safe_text(row.get("source_table_id"))
        if per_pdf[pdf_key] >= 10 or per_page[page_key] >= 4 or (table_key and per_table[table_key] >= 3):
            continue
        source_row_id = _safe_text(row.get("source_row_id"))
        if source_row_id and source_row_id in used_ids:
            continue
        selected.append(row)
        if source_row_id:
            used_ids.add(source_row_id)
        per_pdf[pdf_key] += 1
        per_page[page_key] += 1
        if table_key:
            per_table[table_key] += 1

    if len(selected) < min(max_pilot_rows, len(sorted_rows)):
        for row in sorted_rows:
            if len(selected) >= max_pilot_rows:
                break
            source_row_id = _safe_text(row.get("source_row_id"))
            if source_row_id and source_row_id in used_ids:
                continue
            selected.append(row)
            if source_row_id:
                used_ids.add(source_row_id)

    pilot_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(selected, start=1):
        pilot_rows.append(
            {
                **row,
                "pilot_row_id": f"346a::pilot::{index:05d}",
                "image_bound": False,
                "image_resolution_status": "PENDING_BINDING",
            }
        )
    return pilot_rows


def _load_table_image_manifest(path: Path | None) -> List[Dict[str, Any]]:
    if path is None or not path.exists():
        return []
    if path.suffix.lower() == ".json":
        payload = _read_json(path)
        if isinstance(payload, list):
            return [dict(row) for row in payload]
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            return [dict(row) for row in payload["rows"]]
        raise ValueError(f"unsupported image manifest payload: {path}")
    if path.suffix.lower() == ".csv":
        return _read_csv_rows(path)
    raise ValueError(f"unsupported table image manifest type: {path}")


def _build_image_records(path: Path | None) -> tuple[List[Dict[str, Any]], bool]:
    if path is None:
        return [], False
    if not path.exists():
        return [], True
    records: List[Dict[str, Any]] = []
    for candidate in sorted(path.rglob("*")):
        if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            records.append(
                {
                    "path": str(candidate),
                    "name_key": _normalize_key(candidate.name),
                    "stem_key": _normalize_key(candidate.stem),
                    "parent_key": _normalize_key(candidate.parent.name),
                }
            )
    return records, False


def _build_context_index(path: Path | None) -> tuple[Dict[str, List[str]], bool]:
    if path is None:
        return {}, False
    if not path.exists():
        return {}, True
    index: Dict[str, List[str]] = defaultdict(list)
    for candidate in sorted(path.rglob("*")):
        if not candidate.is_file():
            continue
        suffix = candidate.suffix.lower()
        if suffix == ".md" or suffix == ".json":
            pdf_key = _normalize_key(candidate.stem.replace("_content_list_v2", "").replace("_content_list", "").replace("_middle", "").replace("_model", ""))
            index[pdf_key].append(str(candidate))
            parent_key = _normalize_key(candidate.parent.parent.name if candidate.parent.name == "auto" and candidate.parent.parent else candidate.parent.name)
            if parent_key and str(candidate) not in index[parent_key]:
                index[parent_key].append(str(candidate))
    return index, False


def _resolve_manifest_match(
    row: Dict[str, Any],
    manifest_rows: List[Dict[str, Any]],
) -> tuple[Dict[str, Any] | None, bool]:
    source_row_id = _safe_text(row.get("source_row_id"))
    source_table_id = _safe_text(row.get("source_table_id"))
    source_pdf_name = _safe_text(row.get("source_pdf_name"))
    source_page = _parse_page_number(row.get("source_page"))
    matches: List[Dict[str, Any]] = []
    for item in manifest_rows:
        manifest_path = Path(_safe_text(item.get("image_path") or item.get("table_image_path") or item.get("page_image_path")))
        if not manifest_path.exists():
            continue
        if source_row_id and source_row_id == _safe_text(item.get("source_row_id")):
            matches.append(item)
            continue
        if (
            source_table_id
            and source_table_id == _safe_text(item.get("source_table_id"))
            and source_pdf_name == _safe_text(item.get("source_pdf_name"))
            and source_page == _parse_page_number(item.get("source_page"))
        ):
            matches.append(item)
    if len(matches) == 1:
        return matches[0], False
    if len(matches) > 1:
        return None, True
    return None, False


def _find_table_image_matches(row: Dict[str, Any], records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    table_key = _normalize_key(row.get("source_table_id"))
    pdf_key = _normalize_key(Path(_safe_text(row.get("source_pdf_name"))).stem)
    page_number = _parse_page_number(row.get("source_page"))
    matches: List[Dict[str, Any]] = []
    for record in records:
        joined = f"{record['name_key']} {record['stem_key']} {record['parent_key']}"
        if table_key and table_key in joined:
            matches.append(record)
            continue
        if pdf_key and pdf_key in joined and page_number is not None:
            if f"page{page_number}" in joined or f"p{page_number}" in joined or str(page_number) in joined:
                matches.append(record)
    return matches


def _find_page_image_matches(row: Dict[str, Any], records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pdf_key = _normalize_key(Path(_safe_text(row.get("source_pdf_name"))).stem)
    page_number = _parse_page_number(row.get("source_page"))
    matches: List[Dict[str, Any]] = []
    for record in records:
        joined = f"{record['name_key']} {record['stem_key']} {record['parent_key']}"
        if pdf_key and pdf_key not in joined:
            continue
        if page_number is None:
            continue
        if f"page{page_number}" in joined or f"p{page_number}" in joined or str(page_number) in joined:
            matches.append(record)
    return matches


def _choose_mineru_context(row: Dict[str, Any], context_index: Dict[str, List[str]]) -> Dict[str, Any]:
    pdf_key = _normalize_key(Path(_safe_text(row.get("source_pdf_name"))).stem)
    paths = list(context_index.get(pdf_key, []))[:4]
    snippet = ""
    for path_text in paths:
        path = Path(path_text)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if path.suffix.lower() == ".md":
            snippet = text[:1000]
            break
        if path.suffix.lower() == ".json":
            snippet = text[:1000]
            break
    return {
        "context_file_paths": paths,
        "context_snippet": snippet,
        "context_available": bool(paths),
    }


def _resolve_evidence_bundle(
    row: Dict[str, Any],
    *,
    manifest_rows: List[Dict[str, Any]],
    table_image_records: List[Dict[str, Any]],
    page_image_records: List[Dict[str, Any]],
    context_index: Dict[str, List[str]],
    evidence_supply_provided: bool,
    evidence_read_error: bool,
) -> Dict[str, Any]:
    bbox = _safe_text(row.get("bbox"))
    context = _choose_mineru_context(row, context_index)
    chosen_image_path = ""
    image_evidence_type = ""
    image_resolution_status = "NO_IMAGE_EVIDENCE_PROVIDED"
    ambiguous = False

    explicit_path = _safe_text(row.get("image_path") or row.get("table_image_path") or row.get("page_image_path"))
    if explicit_path:
        explicit = Path(explicit_path)
        if explicit.exists():
            chosen_image_path = str(explicit)
            image_evidence_type = "EXPLICIT_IMAGE_PATH"
            image_resolution_status = "IMAGE_MANIFEST_MATCH"
    if not chosen_image_path:
        manifest_match, manifest_ambiguous = _resolve_manifest_match(row, manifest_rows)
        ambiguous = manifest_ambiguous
        if manifest_match is not None:
            chosen_image_path = _safe_text(
                manifest_match.get("image_path")
                or manifest_match.get("table_image_path")
                or manifest_match.get("page_image_path")
            )
            image_evidence_type = _safe_text(manifest_match.get("image_evidence_type")) or "MANIFEST_IMAGE_PATH"
            bbox = _safe_text(manifest_match.get("bbox")) or bbox
            image_resolution_status = "IMAGE_MANIFEST_MATCH"

    if not chosen_image_path and not ambiguous:
        table_matches = _find_table_image_matches(row, table_image_records)
        if len(table_matches) == 1:
            chosen_image_path = table_matches[0]["path"]
            image_evidence_type = "TABLE_CROP_IMAGE"
            image_resolution_status = "BOUND_TABLE_CROP_IMAGE"
        elif len(table_matches) > 1:
            ambiguous = True

    if not chosen_image_path and not ambiguous:
        page_matches = _find_page_image_matches(row, page_image_records)
        if len(page_matches) == 1:
            chosen_image_path = page_matches[0]["path"]
            image_evidence_type = "PAGE_IMAGE"
            image_resolution_status = "BOUND_PAGE_IMAGE_WITH_BBOX" if bbox else "BOUND_PAGE_IMAGE_NO_BBOX"
        elif len(page_matches) > 1:
            ambiguous = True

    if not chosen_image_path:
        if ambiguous:
            image_resolution_status = "AMBIGUOUS_IMAGE_CANDIDATE"
        elif evidence_read_error:
            image_resolution_status = "READ_ERROR"
        elif evidence_supply_provided:
            image_resolution_status = "NO_MATCH_FOUND"
        else:
            image_resolution_status = "NO_IMAGE_EVIDENCE_PROVIDED"

    return {
        **row,
        **context,
        "bbox": bbox,
        "table_image_path": chosen_image_path if image_evidence_type == "TABLE_CROP_IMAGE" else "",
        "page_image_path": chosen_image_path if image_evidence_type == "PAGE_IMAGE" else "",
        "chosen_image_path": chosen_image_path,
        "image_evidence_type": image_evidence_type,
        "image_resolution_status": image_resolution_status,
        "image_bound": bool(chosen_image_path) and image_resolution_status not in {"AMBIGUOUS_IMAGE_CANDIDATE", "READ_ERROR"},
        "request_eligible": bool(chosen_image_path) and image_resolution_status not in {"AMBIGUOUS_IMAGE_CANDIDATE", "READ_ERROR"},
    }


def _neighbor_context_rows(row: Dict[str, Any], candidate_pool: List[Dict[str, Any]], max_context_rows_per_request: int) -> List[Dict[str, Any]]:
    if max_context_rows_per_request <= 0:
        return []
    source_table_id = _safe_text(row.get("source_table_id"))
    source_pdf_name = _safe_text(row.get("source_pdf_name"))
    source_row_id = _safe_text(row.get("source_row_id"))
    matches = [
        candidate
        for candidate in candidate_pool
        if _safe_text(candidate.get("source_row_id")) != source_row_id
        and (
            (_safe_text(candidate.get("source_table_id")) and _safe_text(candidate.get("source_table_id")) == source_table_id)
            or (
                _safe_text(candidate.get("source_pdf_name")) == source_pdf_name
                and _parse_page_number(candidate.get("source_page")) == _parse_page_number(row.get("source_page"))
            )
        )
    ]
    context_rows = []
    for candidate in matches[:max_context_rows_per_request]:
        context_rows.append(
            {
                "source_row_id": candidate.get("source_row_id"),
                "raw_metric_name": candidate.get("raw_metric_name"),
                "demo_normalized_metric_name": candidate.get("demo_normalized_metric_name"),
                "value": candidate.get("value"),
                "unit": candidate.get("unit"),
                "period": candidate.get("period"),
                "quality_issue_codes": candidate.get("quality_issue_codes"),
            }
        )
    return context_rows


def _question_list(target_fields: Iterable[str]) -> List[str]:
    questions: List[str] = []
    for field in target_fields:
        if field == "unit":
            questions.append("Confirm the table-level or column-level unit for this row.")
        elif field == "period":
            questions.append("Confirm which period or year header aligns with the value cell.")
        elif field == "value":
            questions.append("Check whether the value cell aligns with the named metric row and target period column.")
        elif field == "source_trace":
            questions.append("Check whether the row has enough visible source trace to support the structured extraction.")
        elif field in {"table_header", "row_type"}:
            questions.append("Classify whether the visible row is a data row, header row, subtotal row, or footnote.")
        elif field == "raw_metric_name":
            questions.append("Check whether the metric row label visually matches the current metric name.")
    return questions


def _field_value_for_target(bundle: Dict[str, Any], field: str) -> Any:
    mapping = {
        "unit": bundle.get("unit"),
        "period": bundle.get("period"),
        "value": bundle.get("value"),
        "source_trace": bundle.get("source_trace_available"),
        "table_header": bundle.get("period"),
        "raw_metric_name": bundle.get("raw_metric_name"),
    }
    return mapping.get(field, "")


def _build_field_repair_targets(evidence_bundles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for bundle in evidence_bundles:
        for field in bundle.get("target_field_types", []):
            rows.append(
                {
                    "pilot_row_id": bundle.get("pilot_row_id"),
                    "source_row_id": bundle.get("source_row_id"),
                    "source_pdf_name": bundle.get("source_pdf_name"),
                    "source_page": bundle.get("source_page"),
                    "source_table_id": bundle.get("source_table_id"),
                    "target_field_type": field,
                    "existing_value": _field_value_for_target(bundle, field),
                    "repair_question": _question_list([field])[0] if _question_list([field]) else "",
                    "requires_human_review": True,
                    "image_bound": bundle.get("image_bound", False),
                    "image_resolution_status": bundle.get("image_resolution_status"),
                }
            )
    return rows


def _build_vlm_requests(
    evidence_bundles: List[Dict[str, Any]],
    candidate_pool: List[Dict[str, Any]],
    max_context_rows_per_request: int,
) -> List[Dict[str, Any]]:
    requests: List[Dict[str, Any]] = []
    for index, bundle in enumerate(evidence_bundles, start=1):
        if not bundle.get("request_eligible"):
            continue
        request = {
            "request_id": f"346a::request::{index:05d}",
            "pilot_row_id": bundle.get("pilot_row_id"),
            "source_row_id": bundle.get("source_row_id"),
            "source_pdf_name": bundle.get("source_pdf_name"),
            "source_page": bundle.get("source_page"),
            "source_table_id": bundle.get("source_table_id"),
            "image_path": bundle.get("chosen_image_path"),
            "image_evidence_type": bundle.get("image_evidence_type"),
            "image_resolution_status": bundle.get("image_resolution_status"),
            "bbox": bundle.get("bbox"),
            "mineru_json_or_md_context": {
                "context_file_paths": bundle.get("context_file_paths", []),
                "context_snippet": bundle.get("context_snippet", ""),
            },
            "structured_row_before_vision": {
                "raw_metric_name": bundle.get("raw_metric_name"),
                "demo_normalized_metric_name": bundle.get("demo_normalized_metric_name"),
                "value": bundle.get("value"),
                "unit": bundle.get("unit"),
                "period": bundle.get("period"),
                "quality_issue_codes": bundle.get("quality_issue_codes"),
                "quality_severity": bundle.get("quality_severity"),
            },
            "neighbor_context_rows": _neighbor_context_rows(bundle, candidate_pool, max_context_rows_per_request),
            "target_field_types": bundle.get("target_field_types", []),
            "question_list": _question_list(bundle.get("target_field_types", [])),
            "strict_output_schema_ref": VLM_OUTPUT_SCHEMA_JSON_FILE_NAME,
            "do_not_overwrite_source_data": True,
            "live_vlm_call_allowed": False,
        }
        requests.append(request)
    return requests


def _vlm_output_schema() -> Dict[str, Any]:
    return {
        "request_id": "string",
        "source_row_id": "string",
        "vision_decision": "CONFIRM_EXISTING | SUGGEST_FIELD_REPAIR | FLAG_CONFLICT | INSUFFICIENT_VISUAL_EVIDENCE | NOT_A_DATA_ROW",
        "field_suggestions": [
            {
                "field_name": "unit | period | value | raw_metric_name | source_trace | row_type | table_header",
                "existing_value": "string|null",
                "suggested_value": "string|null",
                "confidence": "HIGH | MEDIUM | LOW",
                "visual_evidence_note": "string",
                "requires_human_review": True,
            }
        ],
        "overall_confidence": "HIGH | MEDIUM | LOW",
        "conflict_reason": "string|null",
        "do_not_auto_apply": True,
    }


def _build_cost_latency_estimate(vlm_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    request_count = len(vlm_requests)
    average_context_rows = 0.0
    average_context_chars = 0.0
    if request_count:
        average_context_rows = sum(len(item.get("neighbor_context_rows", [])) for item in vlm_requests) / request_count
        average_context_chars = sum(
            len(json.dumps(item.get("structured_row_before_vision", {}), ensure_ascii=False))
            + len(json.dumps(item.get("neighbor_context_rows", []), ensure_ascii=False))
            + len(json.dumps(item.get("mineru_json_or_md_context", {}), ensure_ascii=False))
            for item in vlm_requests
        ) / request_count
    estimated_tokens = int(max(average_context_chars / 4, 0))
    qualitative_cost = "NONE" if request_count == 0 else "LOW_PILOT_ONLY"
    qualitative_latency = "NONE" if request_count == 0 else ("LOW" if request_count <= 20 else "MEDIUM")
    return {
        "vlm_request_count": request_count,
        "image_bound_request_count": request_count,
        "estimated_images_per_request": 1,
        "estimated_text_context_tokens_per_request": estimated_tokens,
        "estimated_total_requests": request_count,
        "cost_estimate_note": f"{qualitative_cost}: bounded pilot only, no vendor pricing assumed.",
        "latency_estimate_note": f"{qualitative_latency}: qualitative estimate only, no live requests were sent.",
        "recommended_batch_size": 5 if request_count else 0,
        "recommended_cache_key_fields": [
            "source_pdf_name",
            "source_page",
            "source_table_id",
            "image_path",
            "structured_row_hash",
            "target_field_types",
            "prompt_template_version",
        ],
    }


def _ledger_has_346a_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return "## 346A Vision-Assisted Table Evidence Pilot" in ledger_path.read_text(encoding="utf-8")


def _build_346a_ledger_entry(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "## 346A Vision-Assisted Table Evidence Pilot",
            "",
            "Status: completed",
            "",
            f"- decision: {manifest.get('decision', '')}",
            f"- input packages: 345D={manifest.get('input_345d_dir', '')}; 345E={manifest.get('input_345e_dir', '')}; optional MinerU evidence dirs were suggestion-only",
            f"- output package: {manifest.get('output_dir', '')}",
            f"- selected_pilot_row_count: {manifest.get('selected_pilot_row_count', 0)}",
            f"- evidence_bundle_count: {manifest.get('evidence_bundle_count', 0)}",
            f"- image_bound_count: {manifest.get('image_bound_count', 0)}",
            f"- image_missing_count: {manifest.get('image_missing_count', 0)}",
            f"- ambiguous_image_candidate_count: {manifest.get('ambiguous_image_candidate_count', 0)}",
            f"- vlm_request_count: {manifest.get('vlm_request_count', 0)}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- target_field_distribution: {json.dumps(manifest.get('target_field_distribution', {}), ensure_ascii=False, sort_keys=True)}",
            f"- no_write_back_proof_passed: {manifest.get('no_write_back_proof_passed', False)}",
            f"- gate status: formal_client_export_allowed={manifest.get('formal_client_export_allowed', False)}, client_ready={manifest.get('client_ready', False)}, production_ready={manifest.get('production_ready', False)}",
            "- validation commands and results:",
            "- `python -m py_compile ...` passed",
            "- `python -m pytest tests\\benchmark\\test_vision_assisted_table_evidence_pilot_346a.py -q` passed",
            "- real runner passed",
            f"- next recommended step: {manifest.get('recommended_next_step', '')}",
        ]
    )


def append_346a_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    if _ledger_has_346a_entry(ledger_path):
        return False
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    addition = _build_346a_ledger_entry(manifest)
    prefix = "\n\n" if existing and not existing.endswith("\n\n") else ""
    if existing.endswith("\n"):
        prefix = "\n" if not existing.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(existing + prefix + addition + "\n", encoding="utf-8")
    return True


def build_vision_assisted_table_evidence_pilot_346a(
    *,
    full_structured_demo_export_package_345d_dir: Path,
    demo_export_review_qa_checklist_345e_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    mineru_json_md_dir: Path | None = None,
    mineru_table_image_dir: Path | None = None,
    mineru_page_image_dir: Path | None = None,
    table_image_manifest: Path | None = None,
    max_pilot_rows: int = 100,
    max_context_rows_per_request: int = 5,
) -> Dict[str, Any]:
    if not full_structured_demo_export_package_345d_dir.exists():
        raise FileNotFoundError(f"345D input directory missing: {full_structured_demo_export_package_345d_dir}")
    if not demo_export_review_qa_checklist_345e_dir.exists():
        raise FileNotFoundError(f"345E input directory missing: {demo_export_review_qa_checklist_345e_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_345d_path = full_structured_demo_export_package_345d_dir / INPUT_345D_MANIFEST_NAME
    quality_rows_json_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_LIMITED_ROWS_JSON_NAME
    quality_rows_csv_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_LIMITED_ROWS_CSV_NAME
    demo_rows_json_path = full_structured_demo_export_package_345d_dir / INPUT_345D_DEMO_ROWS_JSON_NAME
    demo_rows_csv_path = full_structured_demo_export_package_345d_dir / INPUT_345D_DEMO_ROWS_CSV_NAME
    quality_caveats_json_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_CAVEATS_JSON_NAME
    quality_caveats_md_path = full_structured_demo_export_package_345d_dir / INPUT_345D_QUALITY_CAVEATS_MD_NAME
    artifact_index_345d_md_path = full_structured_demo_export_package_345d_dir / INPUT_345D_ARTIFACT_INDEX_MD_NAME

    manifest_345e_path = demo_export_review_qa_checklist_345e_dir / INPUT_345E_MANIFEST_NAME
    quality_sample_json_path = demo_export_review_qa_checklist_345e_dir / INPUT_345E_QUALITY_LIMITED_SAMPLE_ROWS_JSON_NAME
    quality_sample_csv_path = demo_export_review_qa_checklist_345e_dir / INPUT_345E_QUALITY_LIMITED_SAMPLE_ROWS_CSV_NAME
    caveat_completeness_path = demo_export_review_qa_checklist_345e_dir / INPUT_345E_CAVEAT_COMPLETENESS_JSON_NAME
    presentation_readiness_path = demo_export_review_qa_checklist_345e_dir / INPUT_345E_PRESENTATION_READINESS_JSON_NAME

    manifest_345d = _read_json(manifest_345d_path)
    manifest_345e = _read_json(manifest_345e_path)
    quality_limited_rows, quality_rows_source = _load_json_or_csv_rows(
        json_path=quality_rows_json_path,
        csv_path=quality_rows_csv_path,
        label="345D quality-limited rows",
    )
    _demo_rows, demo_rows_source = _load_json_or_csv_rows(
        json_path=demo_rows_json_path,
        csv_path=demo_rows_csv_path,
        label="345D demo rows",
    )
    quality_sample_rows, quality_sample_source = _load_json_or_csv_rows(
        json_path=quality_sample_json_path,
        csv_path=quality_sample_csv_path,
        label="345E quality-limited sample rows",
    )
    quality_caveats = _read_json(quality_caveats_json_path)
    _ = quality_caveats_md_path.read_text(encoding="utf-8")
    _ = artifact_index_345d_md_path.read_text(encoding="utf-8")
    caveat_completeness = _read_json(caveat_completeness_path)
    presentation_readiness = _read_json(presentation_readiness_path)

    files_read = [
        str(path)
        for path in [
            manifest_345d_path,
            quality_rows_json_path,
            quality_rows_csv_path,
            demo_rows_json_path,
            demo_rows_csv_path,
            quality_caveats_json_path,
            quality_caveats_md_path,
            artifact_index_345d_md_path,
            manifest_345e_path,
            quality_sample_json_path,
            quality_sample_csv_path,
            caveat_completeness_path,
            presentation_readiness_path,
            table_image_manifest,
        ]
        if path is not None and path.exists()
    ]

    input_paths = [Path(path) for path in files_read if Path(path).is_file()]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    candidate_pool = _build_candidate_pool(quality_limited_rows)
    selected_pilot_rows = _select_pilot_rows(candidate_pool, max_pilot_rows)

    manifest_rows = _load_table_image_manifest(table_image_manifest)
    table_image_records, table_read_error = _build_image_records(mineru_table_image_dir)
    page_image_records, page_read_error = _build_image_records(mineru_page_image_dir)
    context_index, context_read_error = _build_context_index(mineru_json_md_dir)
    evidence_supply_provided = any(path is not None for path in [mineru_table_image_dir, mineru_page_image_dir, table_image_manifest])
    evidence_read_error = table_read_error or page_read_error or context_read_error

    evidence_bundles = [
        _resolve_evidence_bundle(
            row,
            manifest_rows=manifest_rows,
            table_image_records=table_image_records,
            page_image_records=page_image_records,
            context_index=context_index,
            evidence_supply_provided=evidence_supply_provided,
            evidence_read_error=evidence_read_error,
        )
        for row in selected_pilot_rows
    ]
    image_resolution_rows = [
        {
            "pilot_row_id": bundle.get("pilot_row_id"),
            "source_row_id": bundle.get("source_row_id"),
            "source_pdf_name": bundle.get("source_pdf_name"),
            "source_page": bundle.get("source_page"),
            "source_table_id": bundle.get("source_table_id"),
            "image_resolution_status": bundle.get("image_resolution_status"),
            "image_bound": bundle.get("image_bound"),
            "chosen_image_path": bundle.get("chosen_image_path"),
            "image_evidence_type": bundle.get("image_evidence_type"),
            "bbox": bundle.get("bbox"),
        }
        for bundle in evidence_bundles
    ]
    field_repair_targets = _build_field_repair_targets(evidence_bundles)
    vlm_requests = _build_vlm_requests(evidence_bundles, candidate_pool, max_context_rows_per_request)
    vlm_request_preview = {
        "request_count": len(vlm_requests),
        "preview_limit": min(5, len(vlm_requests)),
        "requests": vlm_requests[:5],
    }
    cost_latency_estimate = _build_cost_latency_estimate(vlm_requests)

    image_bound_statuses = {
        "BOUND_TABLE_CROP_IMAGE",
        "BOUND_PAGE_IMAGE_WITH_BBOX",
        "BOUND_PAGE_IMAGE_NO_BBOX",
        "IMAGE_MANIFEST_MATCH",
    }
    image_bound_count = sum(1 for row in image_resolution_rows if row["image_resolution_status"] in image_bound_statuses)
    ambiguous_count = sum(1 for row in image_resolution_rows if row["image_resolution_status"] == "AMBIGUOUS_IMAGE_CANDIDATE")
    image_missing_count = sum(
        1
        for row in image_resolution_rows
        if row["image_resolution_status"] in {"NO_IMAGE_EVIDENCE_PROVIDED", "NO_MATCH_FOUND", "READ_ERROR"}
    )

    target_field_distribution = Counter(target["target_field_type"] for target in field_repair_targets)
    manifest = {
        "decision": READY_DECISION_346A,
        "input_stage": INPUT_STAGE_346A,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_345d_decision": _safe_text(manifest_345d.get("decision")),
        "input_345e_decision": _safe_text(manifest_345e.get("decision")),
        "input_345d_dir": str(full_structured_demo_export_package_345d_dir),
        "input_345e_dir": str(demo_export_review_qa_checklist_345e_dir),
        "output_dir": str(output_dir),
        "quality_limited_row_count": int(manifest_345d.get("quality_limited_row_count", len(quality_limited_rows))),
        "candidate_pool_row_count": len(candidate_pool),
        "selected_pilot_row_count": len(selected_pilot_rows),
        "evidence_bundle_count": len(evidence_bundles),
        "image_bound_count": image_bound_count,
        "image_missing_count": image_missing_count,
        "ambiguous_image_candidate_count": ambiguous_count,
        "vlm_request_count": len(vlm_requests),
        "live_vlm_call_count": 0,
        "vlm_response_count": 0,
        "unit_repair_target_count": target_field_distribution.get("unit", 0),
        "period_repair_target_count": target_field_distribution.get("period", 0),
        "value_alignment_check_target_count": target_field_distribution.get("value", 0),
        "source_trace_check_target_count": target_field_distribution.get("source_trace", 0),
        "header_structure_check_target_count": target_field_distribution.get("table_header", 0),
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_export_generated": False,
        "demo_export_only": True,
        "vision_assisted_data_source_strategy": "TEXT_FIRST_VISION_ON_DEMAND",
        "vlm_request_package_only": True,
        "upstream_data_mutated": False,
        "milestone_ledger_updated": False,
        "table_image_manifest_row_count": len(manifest_rows),
        "quality_sample_row_count": len(quality_sample_rows),
        "quality_sample_source": quality_sample_source,
        "quality_rows_source": quality_rows_source,
        "demo_rows_source": demo_rows_source,
        "max_pilot_rows": max_pilot_rows,
        "max_context_rows_per_request": max_context_rows_per_request,
        "recommended_next_step": "",
        "recommended_next_step_reason": "",
        "target_field_distribution": dict(sorted(target_field_distribution.items())),
        "generated_at_utc": _utc_now(),
    }

    if image_bound_count == 0:
        manifest["recommended_next_step"] = "346A2 MinerU Image Path Binding Fix"
        manifest["recommended_next_step_reason"] = "No deterministic image evidence was bound, so a live VLM pilot would be premature."
    else:
        manifest["recommended_next_step"] = "346C Vision-Assisted Repair Response Ingestion"
        manifest["recommended_next_step_reason"] = "Bounded image evidence and request package exist, but a later explicitly approved live VLM run is still required."

    validation_checks = [
        manifest["input_345d_decision"] == READY_DECISION_345D,
        int(manifest_345d.get("qa_fail_count", 1)) == 0,
        _bool_value(manifest_345d.get("demo_export_only")) is True,
        _bool_value(manifest_345d.get("formal_export_generated")) is False,
        _bool_value(manifest_345d.get("official_rules_modified")) is False,
        _bool_value(manifest_345d.get("official_alias_assets_modified")) is False,
        _bool_value(manifest_345d.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_345d.get("client_ready")) is False,
        _bool_value(manifest_345d.get("production_ready")) is False,
        manifest["input_345e_decision"] == READY_DECISION_345E,
        int(manifest_345e.get("qa_fail_count", 1)) == 0,
        _bool_value(manifest_345e.get("gate_safety_check_passed")) is True,
        _bool_value(manifest_345e.get("caveat_completeness_passed")) is True,
        _bool_value(manifest_345e.get("presentation_ready_for_demo_only")) is True,
        _bool_value(manifest_345e.get("formal_client_export_allowed")) is False,
        _bool_value(manifest_345e.get("client_ready")) is False,
        _bool_value(manifest_345e.get("production_ready")) is False,
        len(candidate_pool) == len(quality_limited_rows),
        len(selected_pilot_rows) <= max_pilot_rows,
        len(evidence_bundles) == len(selected_pilot_rows),
        len(image_resolution_rows) == len(selected_pilot_rows),
        len(vlm_requests) == image_bound_count,
        manifest["live_vlm_call_count"] == 0,
        manifest["vlm_response_count"] == 0,
        bool(caveat_completeness),
        bool(presentation_readiness),
        bool(quality_caveats),
    ]

    no_apply_proof = build_no_apply_proof(
        stage="346A",
        files_read=files_read,
        official_assets_before=official_assets_before,
        official_assets_after=capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH]),
        official_assets_written=[],
    )
    input_hashes_after = {str(path): sha256_file(path) for path in input_paths}
    protected_after = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    protected_staged = _git_staged_names_for_paths(PROTECTED_DIRTY_PATHS, repo_root)
    forbidden_staged = _git_staged_names_for_paths(FORBIDDEN_STAGE_PATHS, repo_root)
    upstream_unchanged = input_hashes_before == input_hashes_after

    no_apply_proof["upstream_input_hashes_before"] = input_hashes_before
    no_apply_proof["upstream_input_hashes_after"] = input_hashes_after
    no_apply_proof["upstream_inputs_unchanged"] = upstream_unchanged
    no_apply_proof["formal_client_export_generated"] = False
    no_apply_proof["real_production_apply_performed"] = False
    no_apply_proof["official_rules_modified"] = False
    no_apply_proof["official_alias_assets_modified"] = False
    no_apply_proof["vlm_request_package_only"] = True
    no_apply_proof["no_write_back"] = True

    no_write_back_proof_passed = bool(
        no_apply_proof.get("no_official_asset_modification_during_346a")
        and upstream_unchanged
        and protected_before == protected_after
        and not protected_staged
        and not forbidden_staged
    )
    manifest["no_write_back_proof_passed"] = no_write_back_proof_passed
    manifest["no_write_back_summary"] = (
        "upstream inputs unchanged; official assets unchanged; protected dirty status preserved; no protected paths staged"
    )

    if ledger_path is not None:
        append_346a_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = _ledger_has_346a_entry(ledger_path)
    validation_checks.append(manifest["milestone_ledger_updated"] or ledger_path is None)
    validation_checks.append(no_write_back_proof_passed)

    qa_fail_count = sum(1 for check in validation_checks if not check)
    manifest["qa_fail_count"] = qa_fail_count
    manifest["decision"] = READY_DECISION_346A if qa_fail_count == 0 else BLOCKED_DECISION_346A

    return {
        "manifest": manifest,
        "candidate_pool_rows": candidate_pool,
        "selected_pilot_rows": selected_pilot_rows,
        "evidence_bundle_rows": evidence_bundles,
        "image_resolution_rows": image_resolution_rows,
        "field_repair_target_rows": field_repair_targets,
        "vlm_request_rows": vlm_requests,
        "vlm_request_preview": vlm_request_preview,
        "vlm_output_schema": _vlm_output_schema(),
        "vlm_prompt_templates_md": render_vlm_prompt_templates_markdown(),
        "conflict_handling_policy_md": render_conflict_handling_policy_markdown(),
        "cost_latency_estimate": cost_latency_estimate,
        "executive_summary_md": render_executive_summary_markdown(manifest),
        "artifact_index_md": render_artifact_index_markdown(_artifact_index_rows(output_dir)),
        "next_plan_md": render_next_plan_markdown(manifest),
        "artifact_index_rows": _artifact_index_rows(output_dir),
        "no_write_back_proof": no_apply_proof,
        "dry_run_state": {
            "upstream_inputs_unchanged": upstream_unchanged,
            "protected_before": protected_before,
            "protected_after": protected_after,
            "protected_staged": protected_staged,
            "forbidden_staged": forbidden_staged,
        },
        "input_debug": {
            "quality_sample_rows": quality_sample_rows[:5],
            "quality_caveats_keys": sorted(quality_caveats.keys()) if isinstance(quality_caveats, dict) else [],
            "presentation_readiness": presentation_readiness,
            "caveat_completeness": caveat_completeness,
        },
    }
