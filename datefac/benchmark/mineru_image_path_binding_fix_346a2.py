from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from datefac.benchmark.mineru_image_path_binding_fix_346a2_report import (
    render_artifact_index_markdown,
    render_executive_summary_markdown,
    render_next_plan_markdown,
)
from datefac.trust.no_apply_proof import (
    FORMAL_SCOPE_RULES_PATH,
    SEMANTIC_ALIAS_ASSET_PATH,
    build_no_apply_proof,
    capture_official_asset_hashes,
    sha256_file,
)


READY_DECISION_346A = "VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_READY"
READY_DECISION_346A2 = "MINERU_IMAGE_PATH_BINDING_FIX_346A2_READY"
BLOCKED_DECISION_346A2 = "MINERU_IMAGE_PATH_BINDING_FIX_346A2_BLOCKED"
INPUT_STAGE_346A2 = "POST_346A_MINERU_IMAGE_PATH_BINDING_FIX"

DEFAULT_VISION_ASSISTED_TABLE_EVIDENCE_PILOT_346A_DIR = Path(
    r"D:\_datefac\output\vision_assisted_table_evidence_pilot_346a"
)
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\mineru_image_path_binding_fix_346a2")

MANIFEST_FILE_NAME = "mineru_image_path_binding_fix_346a2_manifest.json"
EVIDENCE_CATALOG_JSON_FILE_NAME = "mineru_image_path_binding_fix_346a2_evidence_catalog.json"
EVIDENCE_CATALOG_CSV_FILE_NAME = "mineru_image_path_binding_fix_346a2_evidence_catalog.csv"
BINDING_CANDIDATES_JSON_FILE_NAME = "mineru_image_path_binding_fix_346a2_binding_candidates.json"
BINDING_CANDIDATES_CSV_FILE_NAME = "mineru_image_path_binding_fix_346a2_binding_candidates.csv"
BOUND_ROWS_JSON_FILE_NAME = "mineru_image_path_binding_fix_346a2_bound_rows.json"
BOUND_ROWS_CSV_FILE_NAME = "mineru_image_path_binding_fix_346a2_bound_rows.csv"
UNRESOLVED_ROWS_JSON_FILE_NAME = "mineru_image_path_binding_fix_346a2_unresolved_rows.json"
UNRESOLVED_ROWS_CSV_FILE_NAME = "mineru_image_path_binding_fix_346a2_unresolved_rows.csv"
AMBIGUOUS_ROWS_JSON_FILE_NAME = "mineru_image_path_binding_fix_346a2_ambiguous_rows.json"
AMBIGUOUS_ROWS_CSV_FILE_NAME = "mineru_image_path_binding_fix_346a2_ambiguous_rows.csv"
IMAGE_RESOLUTION_STATUS_JSON_FILE_NAME = "mineru_image_path_binding_fix_346a2_image_resolution_status.json"
IMAGE_RESOLUTION_STATUS_CSV_FILE_NAME = "mineru_image_path_binding_fix_346a2_image_resolution_status.csv"
JSON_MD_CONTEXT_INDEX_JSON_FILE_NAME = "mineru_image_path_binding_fix_346a2_json_md_context_index.json"
JSON_MD_CONTEXT_INDEX_CSV_FILE_NAME = "mineru_image_path_binding_fix_346a2_json_md_context_index.csv"
VLM_REQUEST_PACKAGE_JSONL_FILE_NAME = "mineru_image_path_binding_fix_346a2_vlm_request_package.jsonl"
VLM_REQUEST_PACKAGE_PREVIEW_JSON_FILE_NAME = "mineru_image_path_binding_fix_346a2_vlm_request_package_preview.json"
BINDING_SUMMARY_JSON_FILE_NAME = "mineru_image_path_binding_fix_346a2_binding_summary.json"
EXECUTIVE_SUMMARY_MD_FILE_NAME = "mineru_image_path_binding_fix_346a2_executive_summary.md"
ARTIFACT_INDEX_MD_FILE_NAME = "mineru_image_path_binding_fix_346a2_artifact_index.md"
NEXT_PLAN_MD_FILE_NAME = "mineru_image_path_binding_fix_346a2_next_plan.md"

INPUT_346A_MANIFEST_NAME = "vision_assisted_table_evidence_pilot_346a_manifest.json"
INPUT_346A_SELECTED_ROWS_JSON_NAME = "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.json"
INPUT_346A_SELECTED_ROWS_CSV_NAME = "vision_assisted_table_evidence_pilot_346a_selected_pilot_rows.csv"
INPUT_346A_EVIDENCE_BUNDLE_JSON_NAME = "vision_assisted_table_evidence_pilot_346a_evidence_bundle_index.json"
INPUT_346A_EVIDENCE_BUNDLE_CSV_NAME = "vision_assisted_table_evidence_pilot_346a_evidence_bundle_index.csv"
INPUT_346A_VLM_SCHEMA_NAME = "vision_assisted_table_evidence_pilot_346a_vlm_output_schema.json"

SUPPORTED_JSON_MD_SUFFIXES = {".json", ".md", ".markdown"}
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
PAGE_PATTERN = re.compile(r"(?:^|[_\-])(?:page|p)[_\-]?(\d{1,4})(?:[_\-\.]|$)", re.IGNORECASE)
TABLE_PATTERN = re.compile(r"(?:^|[_\-])(?:table|tbl)[_\-]?(\d{1,4})(?:[_\-\.]|$)", re.IGNORECASE)
CONTENT_LIST_PATTERN = re.compile(r"^(?P<pdf_stem>.+?)_(?P<variant>content_list(?:_v2)?)\.json$", re.IGNORECASE)
CONTENT_JSON_SUFFIX_PATTERN = re.compile(r"_(content_list(?:_v2)?|middle|model)$", re.IGNORECASE)
SOURCE_TABLE_ID_PATTERN = re.compile(
    r"(?P<variant>content_list(?:_v2)?)_(?P<ordinal>\d{3})$",
    re.IGNORECASE,
)

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
    {"artifact_name": EVIDENCE_CATALOG_JSON_FILE_NAME, "path": EVIDENCE_CATALOG_JSON_FILE_NAME, "purpose": "Evidence catalog in JSON."},
    {"artifact_name": EVIDENCE_CATALOG_CSV_FILE_NAME, "path": EVIDENCE_CATALOG_CSV_FILE_NAME, "purpose": "Evidence catalog in CSV."},
    {"artifact_name": BINDING_CANDIDATES_JSON_FILE_NAME, "path": BINDING_CANDIDATES_JSON_FILE_NAME, "purpose": "Binding candidates in JSON."},
    {"artifact_name": BINDING_CANDIDATES_CSV_FILE_NAME, "path": BINDING_CANDIDATES_CSV_FILE_NAME, "purpose": "Binding candidates in CSV."},
    {"artifact_name": BOUND_ROWS_JSON_FILE_NAME, "path": BOUND_ROWS_JSON_FILE_NAME, "purpose": "Final bound rows in JSON."},
    {"artifact_name": BOUND_ROWS_CSV_FILE_NAME, "path": BOUND_ROWS_CSV_FILE_NAME, "purpose": "Final bound rows in CSV."},
    {"artifact_name": UNRESOLVED_ROWS_JSON_FILE_NAME, "path": UNRESOLVED_ROWS_JSON_FILE_NAME, "purpose": "Unresolved rows in JSON."},
    {"artifact_name": UNRESOLVED_ROWS_CSV_FILE_NAME, "path": UNRESOLVED_ROWS_CSV_FILE_NAME, "purpose": "Unresolved rows in CSV."},
    {"artifact_name": AMBIGUOUS_ROWS_JSON_FILE_NAME, "path": AMBIGUOUS_ROWS_JSON_FILE_NAME, "purpose": "Ambiguous rows in JSON."},
    {"artifact_name": AMBIGUOUS_ROWS_CSV_FILE_NAME, "path": AMBIGUOUS_ROWS_CSV_FILE_NAME, "purpose": "Ambiguous rows in CSV."},
    {"artifact_name": IMAGE_RESOLUTION_STATUS_JSON_FILE_NAME, "path": IMAGE_RESOLUTION_STATUS_JSON_FILE_NAME, "purpose": "Image resolution status rows in JSON."},
    {"artifact_name": IMAGE_RESOLUTION_STATUS_CSV_FILE_NAME, "path": IMAGE_RESOLUTION_STATUS_CSV_FILE_NAME, "purpose": "Image resolution status rows in CSV."},
    {"artifact_name": JSON_MD_CONTEXT_INDEX_JSON_FILE_NAME, "path": JSON_MD_CONTEXT_INDEX_JSON_FILE_NAME, "purpose": "JSON/MD context index in JSON."},
    {"artifact_name": JSON_MD_CONTEXT_INDEX_CSV_FILE_NAME, "path": JSON_MD_CONTEXT_INDEX_CSV_FILE_NAME, "purpose": "JSON/MD context index in CSV."},
    {"artifact_name": VLM_REQUEST_PACKAGE_JSONL_FILE_NAME, "path": VLM_REQUEST_PACKAGE_JSONL_FILE_NAME, "purpose": "Refreshed live-ready VLM request package for image-bound rows only."},
    {"artifact_name": VLM_REQUEST_PACKAGE_PREVIEW_JSON_FILE_NAME, "path": VLM_REQUEST_PACKAGE_PREVIEW_JSON_FILE_NAME, "purpose": "Preview of regenerated VLM requests."},
    {"artifact_name": BINDING_SUMMARY_JSON_FILE_NAME, "path": BINDING_SUMMARY_JSON_FILE_NAME, "purpose": "Binding summary metrics and supplied roots."},
    {"artifact_name": EXECUTIVE_SUMMARY_MD_FILE_NAME, "path": EXECUTIVE_SUMMARY_MD_FILE_NAME, "purpose": "Executive summary of 346A2 results."},
    {"artifact_name": ARTIFACT_INDEX_MD_FILE_NAME, "path": ARTIFACT_INDEX_MD_FILE_NAME, "purpose": "Artifact index for 346A2 outputs."},
    {"artifact_name": NEXT_PLAN_MD_FILE_NAME, "path": NEXT_PLAN_MD_FILE_NAME, "purpose": "Recommended next step and unresolved-gap note."},
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
        raise ValueError(f"{label} must be a JSON list: {json_path}")
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


def _normalize_key(value: Any) -> str:
    text = _safe_text(value).lower()
    return "".join(ch for ch in text if ch.isalnum())


def _parse_page_number(value: Any) -> int | None:
    text = _safe_text(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _fingerprint_file(path: Path) -> str:
    stat = path.stat()
    token = f"{path.name}|{stat.st_size}|{int(stat.st_mtime)}".encode("utf-8")
    return hashlib.sha256(token).hexdigest()


def _content_pdf_stem(path: Path) -> str:
    stem = path.stem
    return CONTENT_JSON_SUFFIX_PATTERN.sub("", stem)


def _extract_page_candidate_from_name(name: str) -> int | None:
    match = PAGE_PATTERN.search(name)
    if not match:
        return None
    return int(match.group(1))


def _extract_table_candidate_from_name(name: str) -> int | None:
    match = TABLE_PATTERN.search(name)
    if not match:
        return None
    return int(match.group(1))


def _iter_unique_files(roots: Iterable[Path]) -> Iterable[Path]:
    seen: set[str] = set()
    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            yield path


def _load_manifest_rows(path: Path | None) -> List[Dict[str, Any]]:
    if path is None or not path.exists():
        return []
    if path.suffix.lower() == ".json":
        payload = _read_json(path)
        if isinstance(payload, list):
            return [dict(row) for row in payload]
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            return [dict(row) for row in payload["rows"]]
        raise ValueError(f"unsupported manifest payload: {path}")
    if path.suffix.lower() == ".csv":
        return _read_csv_rows(path)
    raise ValueError(f"unsupported manifest type: {path}")


def _snip_text(value: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    return value[:max_chars]


def _context_payload_snippet(json_path: str | None, md_path: str | None, max_chars: int) -> Dict[str, Any]:
    snippet_parts: List[str] = []
    json_text = ""
    md_text = ""
    if json_path:
        try:
            json_text = Path(json_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            json_text = ""
    if md_path:
        try:
            md_text = Path(md_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            md_text = ""
    if json_text:
        snippet_parts.append(json_text)
    if md_text:
        snippet_parts.append(md_text)
    return {
        "json_path": json_path or "",
        "md_path": md_path or "",
        "context_snippet": _snip_text("\n\n".join(snippet_parts), max_chars),
    }


def _parse_source_table_id(value: Any) -> tuple[str | None, int | None]:
    match = SOURCE_TABLE_ID_PATTERN.search(_safe_text(value))
    if not match:
        return None, None
    return match.group("variant").lower(), int(match.group("ordinal"))


def _parse_table_manifest_matches(
    manifest_rows: List[Dict[str, Any]],
    row: Dict[str, Any],
) -> List[Dict[str, Any]]:
    source_row_id = _safe_text(row.get("source_row_id"))
    source_pdf_name = _safe_text(row.get("source_pdf_name"))
    source_page = _parse_page_number(row.get("source_page"))
    source_table_id = _safe_text(row.get("source_table_id"))
    matches: List[Dict[str, Any]] = []
    for item in manifest_rows:
        item_path = Path(_safe_text(item.get("image_path") or item.get("table_image_path") or item.get("page_image_path")))
        if not item_path.exists():
            continue
        if source_row_id and source_row_id == _safe_text(item.get("source_row_id")):
            matches.append(item)
            continue
        if (
            source_pdf_name
            and source_pdf_name == _safe_text(item.get("source_pdf_name"))
            and source_page == _parse_page_number(item.get("source_page"))
            and source_table_id
            and source_table_id == _safe_text(item.get("source_table_id"))
        ):
            matches.append(item)
    return matches


def _parse_page_manifest_matches(
    manifest_rows: List[Dict[str, Any]],
    row: Dict[str, Any],
) -> List[Dict[str, Any]]:
    source_pdf_name = _safe_text(row.get("source_pdf_name"))
    source_page = _parse_page_number(row.get("source_page"))
    matches: List[Dict[str, Any]] = []
    for item in manifest_rows:
        item_path = Path(_safe_text(item.get("image_path") or item.get("page_image_path")))
        if not item_path.exists():
            continue
        if (
            source_pdf_name
            and source_pdf_name == _safe_text(item.get("source_pdf_name"))
            and source_page == _parse_page_number(item.get("source_page"))
        ):
            matches.append(item)
    return matches


def _find_neighbor_rows(row: Dict[str, Any], selected_rows: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []
    source_row_id = _safe_text(row.get("source_row_id"))
    source_table_id = _safe_text(row.get("source_table_id"))
    source_pdf_name = _safe_text(row.get("source_pdf_name"))
    source_page = _parse_page_number(row.get("source_page"))
    neighbors = []
    for candidate in selected_rows:
        if _safe_text(candidate.get("source_row_id")) == source_row_id:
            continue
        if (
            (_safe_text(candidate.get("source_table_id")) and _safe_text(candidate.get("source_table_id")) == source_table_id)
            or (
                _safe_text(candidate.get("source_pdf_name")) == source_pdf_name
                and _parse_page_number(candidate.get("source_page")) == source_page
            )
        ):
            neighbors.append(
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
        if len(neighbors) >= limit:
            break
    return neighbors


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


def _ledger_has_346a2_entry(ledger_path: Path) -> bool:
    if not ledger_path.exists():
        return False
    return "## 346A2 MinerU Image Path Binding Fix" in ledger_path.read_text(encoding="utf-8")


def _build_346a2_ledger_entry(manifest: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "## 346A2 MinerU Image Path Binding Fix",
            "",
            "Status: completed",
            "",
            f"- decision: {manifest.get('decision', '')}",
            f"- input_346a_dir: {manifest.get('input_346a_dir', '')}",
            f"- supplied_mineru_evidence_dirs: {', '.join(manifest.get('supplied_evidence_roots', [])) or 'none'}",
            f"- output_dir: {manifest.get('output_dir', '')}",
            f"- selected_pilot_row_count: {manifest.get('selected_pilot_row_count', 0)}",
            f"- binding_candidate_count: {manifest.get('binding_candidate_count', 0)}",
            f"- image_bound_count: {manifest.get('image_bound_count', 0)}",
            f"- table_crop_bound_count: {manifest.get('table_crop_bound_count', 0)}",
            f"- page_image_bound_count: {manifest.get('page_image_bound_count', 0)}",
            f"- json_md_context_bound_count: {manifest.get('json_md_context_bound_count', 0)}",
            f"- image_missing_count: {manifest.get('image_missing_count', 0)}",
            f"- ambiguous_image_candidate_count: {manifest.get('ambiguous_image_candidate_count', 0)}",
            f"- vlm_request_count: {manifest.get('vlm_request_count', 0)}",
            f"- live_vlm_call_count: {manifest.get('live_vlm_call_count', 0)}",
            f"- no_write_back_proof_passed: {manifest.get('no_write_back_proof_passed', False)}",
            f"- gate_status: formal_client_export_allowed={manifest.get('formal_client_export_allowed', False)}, client_ready={manifest.get('client_ready', False)}, production_ready={manifest.get('production_ready', False)}",
            f"- next_recommended_step: {manifest.get('recommended_next_step', '')}",
        ]
    )


def append_346a2_ledger_entry(*, manifest: Dict[str, Any], ledger_path: Path) -> bool:
    if _ledger_has_346a2_entry(ledger_path):
        return False
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    addition = _build_346a2_ledger_entry(manifest)
    prefix = "\n\n" if existing and not existing.endswith("\n\n") else ""
    if existing.endswith("\n"):
        prefix = "\n" if not existing.endswith("\n\n") else ""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(existing + prefix + addition + "\n", encoding="utf-8")
    return True


class EvidenceState:
    def __init__(self) -> None:
        self.evidence_catalog_rows: List[Dict[str, Any]] = []
        self.binding_candidate_rows: List[Dict[str, Any]] = []
        self.context_index_rows: List[Dict[str, Any]] = []
        self.context_index: Dict[str, Dict[str, Any]] = {}
        self.table_binding_index: Dict[tuple[str, str, int], Dict[str, Any]] = {}
        self.table_path_metadata: Dict[str, Dict[str, Any]] = {}
        self.page_image_index: Dict[tuple[str, int], List[Dict[str, Any]]] = defaultdict(list)
        self.table_image_records: Dict[str, Dict[str, Any]] = {}
        self.page_image_records: Dict[str, Dict[str, Any]] = {}
        self.read_errors: List[str] = []


def _ensure_context_index_row(state: EvidenceState, pdf_stem: str) -> Dict[str, Any]:
    if pdf_stem not in state.context_index:
        row = {
            "source_pdf_stem": pdf_stem,
            "json_paths": [],
            "md_paths": [],
            "content_list_paths": [],
            "content_list_v2_paths": [],
            "middle_json_paths": [],
            "model_json_paths": [],
            "table_entry_count": 0,
        }
        state.context_index[pdf_stem] = row
        state.context_index_rows.append(row)
    return state.context_index[pdf_stem]


def _register_content_list_tables(state: EvidenceState, path: Path) -> None:
    match = CONTENT_LIST_PATTERN.match(path.name)
    if not match:
        return
    pdf_stem = match.group("pdf_stem")
    variant = match.group("variant").lower()
    context_row = _ensure_context_index_row(state, pdf_stem)
    if variant == "content_list":
        context_row["content_list_paths"].append(str(path))
    else:
        context_row["content_list_v2_paths"].append(str(path))
    try:
        payload = _read_json(path)
    except Exception as exc:  # noqa: BLE001
        state.read_errors.append(f"failed to parse {path}: {exc}")
        return
    if not isinstance(payload, list):
        state.read_errors.append(f"content_list payload is not a list: {path}")
        return
    table_index = 0
    for row in payload:
        if isinstance(row, list):
            for nested in row:
                if isinstance(nested, dict) and nested.get("type") == "table":
                    table_index += 1
                    img_relative = _safe_text(nested.get("img_path"))
                    img_path = str((path.parent / img_relative).resolve()) if img_relative else ""
                    table_info = {
                        "source_pdf_stem": pdf_stem,
                        "variant": variant,
                        "table_ordinal": table_index,
                        "page_candidate": _parse_page_number(nested.get("page_idx")),
                        "bbox_candidate": nested.get("bbox"),
                        "image_path": img_path,
                        "json_context_path": str(path),
                        "table_body": _safe_text(nested.get("table_body")),
                    }
                    state.table_binding_index[(pdf_stem, variant, table_index)] = table_info
                    if img_path:
                        current = state.table_path_metadata.setdefault(
                            img_path,
                            {
                                "source_pdf_stem": pdf_stem,
                                "page_candidate": table_info["page_candidate"],
                                "bbox_candidate": table_info["bbox_candidate"],
                                "table_id_candidates": [],
                            },
                        )
                        current["page_candidate"] = table_info["page_candidate"]
                        current["bbox_candidate"] = table_info["bbox_candidate"]
                        candidate_id = f"{variant}_{table_index:03d}"
                        if candidate_id not in current["table_id_candidates"]:
                            current["table_id_candidates"].append(candidate_id)
                    context_row["table_entry_count"] += 1
            continue
        if row.get("type") != "table":
            continue
        table_index += 1
        img_relative = _safe_text(row.get("img_path"))
        img_path = str((path.parent / img_relative).resolve()) if img_relative else ""
        table_info = {
            "source_pdf_stem": pdf_stem,
            "variant": variant,
            "table_ordinal": table_index,
            "page_candidate": _parse_page_number(row.get("page_idx")),
            "bbox_candidate": row.get("bbox"),
            "image_path": img_path,
            "json_context_path": str(path),
            "table_body": _safe_text(row.get("table_body")),
        }
        state.table_binding_index[(pdf_stem, variant, table_index)] = table_info
        if img_path:
            current = state.table_path_metadata.setdefault(
                img_path,
                {
                    "source_pdf_stem": pdf_stem,
                    "page_candidate": table_info["page_candidate"],
                    "bbox_candidate": table_info["bbox_candidate"],
                    "table_id_candidates": [],
                },
            )
            current["page_candidate"] = table_info["page_candidate"]
            current["bbox_candidate"] = table_info["bbox_candidate"]
            candidate_id = f"{variant}_{table_index:03d}"
            if candidate_id not in current["table_id_candidates"]:
                current["table_id_candidates"].append(candidate_id)
        context_row["table_entry_count"] += 1


def _catalog_json_md_roots(state: EvidenceState, roots: List[Path]) -> None:
    evidence_id = len(state.evidence_catalog_rows)
    for path in _iter_unique_files(roots):
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_JSON_MD_SUFFIXES:
            continue
        pdf_stem = _content_pdf_stem(path)
        page_candidate = _extract_page_candidate_from_name(path.stem)
        table_candidate = _extract_table_candidate_from_name(path.stem)
        evidence_type = "JSON_CONTEXT" if suffix == ".json" else "MD_CONTEXT"
        context_row = _ensure_context_index_row(state, pdf_stem)
        if evidence_type == "JSON_CONTEXT":
            if path.name.endswith("_middle.json"):
                context_row["middle_json_paths"].append(str(path))
            elif path.name.endswith("_model.json"):
                context_row["model_json_paths"].append(str(path))
            else:
                context_row["json_paths"].append(str(path))
        else:
            context_row["md_paths"].append(str(path))
        evidence_id += 1
        state.evidence_catalog_rows.append(
            {
                "evidence_id": f"346a2::evidence::{evidence_id:05d}",
                "evidence_type": evidence_type,
                "path": str(path),
                "filename": path.name,
                "suffix": suffix,
                "source_pdf_name_candidate": f"{pdf_stem}.pdf" if pdf_stem else "",
                "source_pdf_name_candidate_stem": pdf_stem,
                "page_candidate": page_candidate,
                "table_id_candidate": table_candidate,
                "bbox_candidate": "",
                "hash_or_size_mtime_fingerprint": _fingerprint_file(path),
            }
        )
        if suffix == ".json":
            _register_content_list_tables(state, path)


def _page_image_candidate(path: Path) -> tuple[str, int | None]:
    stem = path.stem
    page = _extract_page_candidate_from_name(stem)
    if page is None:
        return _normalize_key(stem), None
    match = PAGE_PATTERN.search(stem)
    prefix = stem[: match.start()] if match else stem
    prefix = prefix.rstrip("_- ")
    pdf_stem = _normalize_key(prefix)
    return pdf_stem or _normalize_key(stem), page


def _catalog_table_image_roots(state: EvidenceState, roots: List[Path]) -> None:
    evidence_id = len(state.evidence_catalog_rows)
    for path in _iter_unique_files(roots):
        if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            continue
        path_text = str(path.resolve())
        metadata = state.table_path_metadata.get(path_text, {})
        table_candidate = metadata.get("table_id_candidates", [])
        evidence_id += 1
        row = {
            "evidence_id": f"346a2::evidence::{evidence_id:05d}",
            "evidence_type": "TABLE_CROP_IMAGE",
            "path": path_text,
            "filename": path.name,
            "suffix": path.suffix.lower(),
            "source_pdf_name_candidate": f"{metadata.get('source_pdf_stem', '')}.pdf" if metadata.get("source_pdf_stem") else "",
            "source_pdf_name_candidate_stem": metadata.get("source_pdf_stem", ""),
            "page_candidate": metadata.get("page_candidate"),
            "table_id_candidate": "|".join(table_candidate),
            "bbox_candidate": metadata.get("bbox_candidate", ""),
            "hash_or_size_mtime_fingerprint": _fingerprint_file(path),
        }
        state.evidence_catalog_rows.append(row)
        state.table_image_records[path_text] = row


def _catalog_page_image_roots(state: EvidenceState, roots: List[Path]) -> None:
    evidence_id = len(state.evidence_catalog_rows)
    for path in _iter_unique_files(roots):
        if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            continue
        pdf_stem_candidate, page_candidate = _page_image_candidate(path)
        if page_candidate is None:
            continue
        evidence_id += 1
        row = {
            "evidence_id": f"346a2::evidence::{evidence_id:05d}",
            "evidence_type": "PAGE_IMAGE",
            "path": str(path.resolve()),
            "filename": path.name,
            "suffix": path.suffix.lower(),
            "source_pdf_name_candidate": f"{pdf_stem_candidate}.pdf" if pdf_stem_candidate else "",
            "source_pdf_name_candidate_stem": pdf_stem_candidate,
            "page_candidate": page_candidate,
            "table_id_candidate": "",
            "bbox_candidate": "",
            "hash_or_size_mtime_fingerprint": _fingerprint_file(path),
        }
        state.evidence_catalog_rows.append(row)
        state.page_image_records[str(path.resolve())] = row
        state.page_image_index[(pdf_stem_candidate, page_candidate)].append(row)


def _catalog_manifest_rows(state: EvidenceState, rows: List[Dict[str, Any]], kind: str) -> None:
    evidence_id = len(state.evidence_catalog_rows)
    for item in rows:
        evidence_id += 1
        path_value = _safe_text(item.get("image_path") or item.get("table_image_path") or item.get("page_image_path"))
        path = Path(path_value)
        state.evidence_catalog_rows.append(
            {
                "evidence_id": f"346a2::evidence::{evidence_id:05d}",
                "evidence_type": "MANIFEST_ROW",
                "manifest_kind": kind,
                "path": path_value,
                "filename": path.name if path_value else "",
                "suffix": path.suffix.lower() if path_value else "",
                "source_pdf_name_candidate": _safe_text(item.get("source_pdf_name")),
                "source_pdf_name_candidate_stem": _normalize_key(Path(_safe_text(item.get("source_pdf_name"))).stem),
                "page_candidate": _parse_page_number(item.get("source_page")),
                "table_id_candidate": _safe_text(item.get("source_table_id")),
                "bbox_candidate": item.get("bbox", ""),
                "hash_or_size_mtime_fingerprint": _fingerprint_file(path) if path_value and path.exists() else "__MISSING__",
            }
        )


def _binding_candidate_row(
    *,
    pilot_row_id: str,
    source_row_id: str,
    source_pdf_name: str,
    source_page: Any,
    source_table_id: str,
    source_kind: str,
    candidate_rank: int,
    candidate_source: str,
    evidence_type: str,
    path: str,
    page_candidate: int | None,
    table_id_candidate: str,
    bbox_candidate: Any,
    deterministic_match: bool,
    reason: str,
) -> Dict[str, Any]:
    return {
        "pilot_row_id": pilot_row_id,
        "source_row_id": source_row_id,
        "source_pdf_name": source_pdf_name,
        "source_page": source_page,
        "source_table_id": source_table_id,
        "candidate_rank": candidate_rank,
        "candidate_source": candidate_source,
        "source_kind": source_kind,
        "evidence_type": evidence_type,
        "path": path,
        "page_candidate": page_candidate,
        "table_id_candidate": table_id_candidate,
        "bbox_candidate": bbox_candidate,
        "deterministic_match": deterministic_match,
        "reason": reason,
    }


def _refresh_binding_for_row(
    row: Dict[str, Any],
    *,
    state: EvidenceState,
    selected_rows: List[Dict[str, Any]],
    table_manifest_rows: List[Dict[str, Any]],
    page_manifest_rows: List[Dict[str, Any]],
    max_binding_candidates_per_row: int,
    max_context_chars: int,
    evidence_supplied: bool,
) -> Dict[str, Any]:
    pilot_row_id = _safe_text(row.get("pilot_row_id"))
    source_row_id = _safe_text(row.get("source_row_id"))
    source_pdf_name = _safe_text(row.get("source_pdf_name"))
    source_pdf_stem = _normalize_key(Path(source_pdf_name).stem)
    source_page = row.get("source_page")
    source_page_number = _parse_page_number(source_page)
    source_table_id = _safe_text(row.get("source_table_id"))
    chosen_image_path = ""
    image_evidence_type = ""
    image_resolution_status = ""
    bbox = row.get("bbox", "")
    candidate_rows: List[Dict[str, Any]] = []

    def add_candidate(
        *,
        source_kind: str,
        candidate_source: str,
        evidence_type: str,
        path: str,
        page_candidate: int | None,
        table_id_candidate: str,
        bbox_candidate: Any,
        deterministic_match: bool,
        reason: str,
    ) -> None:
        if len(candidate_rows) >= max_binding_candidates_per_row:
            return
        candidate_rows.append(
            _binding_candidate_row(
                pilot_row_id=pilot_row_id,
                source_row_id=source_row_id,
                source_pdf_name=source_pdf_name,
                source_page=source_page,
                source_table_id=source_table_id,
                source_kind=source_kind,
                candidate_rank=len(candidate_rows) + 1,
                candidate_source=candidate_source,
                evidence_type=evidence_type,
                path=path,
                page_candidate=page_candidate,
                table_id_candidate=table_id_candidate,
                bbox_candidate=bbox_candidate,
                deterministic_match=deterministic_match,
                reason=reason,
            )
        )

    explicit_path = _safe_text(row.get("chosen_image_path") or row.get("table_image_path") or row.get("page_image_path"))
    if explicit_path and Path(explicit_path).exists():
        explicit_type = "PAGE_IMAGE" if _safe_text(row.get("page_image_path")) else "TABLE_CROP_IMAGE"
        add_candidate(
            source_kind="explicit_row_path",
            candidate_source="EXPLICIT_IMAGE_PATH",
            evidence_type=explicit_type,
            path=explicit_path,
            page_candidate=source_page_number,
            table_id_candidate=source_table_id,
            bbox_candidate=row.get("bbox", ""),
            deterministic_match=True,
            reason="346A row already carries an explicit image path that still exists.",
        )

    table_manifest_matches = _parse_table_manifest_matches(table_manifest_rows, row)
    for item in table_manifest_matches[:max_binding_candidates_per_row]:
        add_candidate(
            source_kind="table_image_manifest",
            candidate_source="TABLE_IMAGE_MANIFEST",
            evidence_type="TABLE_CROP_IMAGE",
            path=_safe_text(item.get("image_path") or item.get("table_image_path")),
            page_candidate=_parse_page_number(item.get("source_page")),
            table_id_candidate=_safe_text(item.get("source_table_id")),
            bbox_candidate=item.get("bbox", ""),
            deterministic_match=len(table_manifest_matches) == 1,
            reason="Manifest row matched source PDF, page, and table id.",
        )

    page_manifest_matches = _parse_page_manifest_matches(page_manifest_rows, row)
    for item in page_manifest_matches[:max_binding_candidates_per_row - len(candidate_rows)]:
        add_candidate(
            source_kind="page_image_manifest",
            candidate_source="PAGE_IMAGE_MANIFEST",
            evidence_type="PAGE_IMAGE",
            path=_safe_text(item.get("image_path") or item.get("page_image_path")),
            page_candidate=_parse_page_number(item.get("source_page")),
            table_id_candidate="",
            bbox_candidate=item.get("bbox", ""),
            deterministic_match=len(page_manifest_matches) == 1,
            reason="Page-image manifest row matched source PDF and page.",
        )

    variant, ordinal = _parse_source_table_id(source_table_id)
    table_binding = None
    if variant is not None and ordinal is not None:
        table_binding = state.table_binding_index.get((Path(source_pdf_name).stem, variant, ordinal))
        if table_binding is None:
            table_binding = state.table_binding_index.get((source_pdf_stem, variant, ordinal))
    if table_binding and _safe_text(table_binding.get("image_path")):
        add_candidate(
            source_kind="mineru_content_list",
            candidate_source="CONTENT_LIST_TABLE_BINDING",
            evidence_type="TABLE_CROP_IMAGE",
            path=_safe_text(table_binding.get("image_path")),
            page_candidate=table_binding.get("page_candidate"),
            table_id_candidate=f"{variant}_{ordinal:03d}" if variant is not None and ordinal is not None else "",
            bbox_candidate=table_binding.get("bbox_candidate", ""),
            deterministic_match=True,
            reason="source_table_id ordinal matched a MinerU content_list table block.",
        )

    page_matches = state.page_image_index.get((source_pdf_stem, source_page_number), [])
    for item in page_matches[:max_binding_candidates_per_row - len(candidate_rows)]:
        add_candidate(
            source_kind="page_image_directory",
            candidate_source="PAGE_IMAGE_DIRECTORY_MATCH",
            evidence_type="PAGE_IMAGE",
            path=_safe_text(item.get("path")),
            page_candidate=source_page_number,
            table_id_candidate="",
            bbox_candidate="",
            deterministic_match=len(page_matches) == 1,
            reason="Page-image directory filename matched source PDF stem and page.",
        )

    context = state.context_index.get(Path(source_pdf_name).stem) or state.context_index.get(source_pdf_stem)
    if context and context.get("json_paths"):
        add_candidate(
            source_kind="json_context",
            candidate_source="JSON_CONTEXT_MATCH",
            evidence_type="JSON_CONTEXT",
            path=_safe_text(context["json_paths"][0]),
            page_candidate=source_page_number,
            table_id_candidate=source_table_id,
            bbox_candidate=bbox,
            deterministic_match=True,
            reason="MinerU JSON context exists for the same PDF stem.",
        )
    if context and context.get("md_paths"):
        add_candidate(
            source_kind="md_context",
            candidate_source="MD_CONTEXT_MATCH",
            evidence_type="MD_CONTEXT",
            path=_safe_text(context["md_paths"][0]),
            page_candidate=source_page_number,
            table_id_candidate=source_table_id,
            bbox_candidate=bbox,
            deterministic_match=True,
            reason="MinerU Markdown context exists for the same PDF stem.",
        )

    deterministic_image_candidates = [
        item
        for item in candidate_rows
        if item["evidence_type"] in {"TABLE_CROP_IMAGE", "PAGE_IMAGE"} and item["deterministic_match"]
    ]
    ambiguous_image_candidates = [
        item
        for item in candidate_rows
        if item["evidence_type"] in {"TABLE_CROP_IMAGE", "PAGE_IMAGE"} and not item["deterministic_match"]
    ]
    json_candidate = next((item for item in candidate_rows if item["evidence_type"] == "JSON_CONTEXT"), None)
    md_candidate = next((item for item in candidate_rows if item["evidence_type"] == "MD_CONTEXT"), None)

    final_candidate = deterministic_image_candidates[0] if deterministic_image_candidates else None
    image_bound = False
    request_eligible = False
    if final_candidate is not None:
        chosen_image_path = final_candidate["path"]
        image_evidence_type = final_candidate["evidence_type"]
        bbox = final_candidate["bbox_candidate"] or bbox
        image_bound = True
        request_eligible = True
        if final_candidate["candidate_source"] in {"TABLE_IMAGE_MANIFEST", "PAGE_IMAGE_MANIFEST"}:
            image_resolution_status = "IMAGE_MANIFEST_MATCH"
        elif image_evidence_type == "TABLE_CROP_IMAGE":
            image_resolution_status = "BOUND_TABLE_CROP_IMAGE"
        elif image_evidence_type == "PAGE_IMAGE":
            image_resolution_status = "BOUND_PAGE_IMAGE_WITH_BBOX" if bbox else "BOUND_PAGE_IMAGE_NO_BBOX"
    elif ambiguous_image_candidates:
        image_resolution_status = "AMBIGUOUS_IMAGE_CANDIDATE"
    elif json_candidate and md_candidate:
        image_resolution_status = "BOUND_TEXT_CONTEXT_ONLY"
    elif json_candidate:
        image_resolution_status = "BOUND_JSON_CONTEXT_ONLY"
    elif md_candidate:
        image_resolution_status = "BOUND_MD_CONTEXT_ONLY"
    elif not evidence_supplied:
        image_resolution_status = "NO_IMAGE_EVIDENCE_PROVIDED"
    elif state.read_errors:
        image_resolution_status = "READ_ERROR"
    else:
        image_resolution_status = "NO_MATCH_FOUND"

    context_payload = _context_payload_snippet(
        json_candidate["path"] if json_candidate else "",
        md_candidate["path"] if md_candidate else "",
        max_context_chars,
    )
    final_row = {
        **row,
        "candidate_count": len(candidate_rows),
        "image_bound": image_bound,
        "request_eligible": request_eligible,
        "image_resolution_status": image_resolution_status,
        "chosen_image_path": chosen_image_path,
        "image_evidence_type": image_evidence_type,
        "table_image_path": chosen_image_path if image_evidence_type == "TABLE_CROP_IMAGE" else "",
        "page_image_path": chosen_image_path if image_evidence_type == "PAGE_IMAGE" else "",
        "bbox": bbox,
        "context_available": bool(json_candidate or md_candidate),
        "json_context_path": json_candidate["path"] if json_candidate else "",
        "md_context_path": md_candidate["path"] if md_candidate else "",
        "context_snippet": context_payload["context_snippet"],
        "neighbor_context_rows": _find_neighbor_rows(row, selected_rows, 5),
    }
    return {
        "final_row": final_row,
        "candidate_rows": candidate_rows,
    }


def _build_vlm_requests(final_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    requests: List[Dict[str, Any]] = []
    for index, row in enumerate(final_rows, start=1):
        if not row.get("request_eligible"):
            continue
        requests.append(
            {
                "request_id": f"346a2::request::{index:05d}",
                "pilot_row_id": row.get("pilot_row_id"),
                "source_row_id": row.get("source_row_id"),
                "source_pdf_name": row.get("source_pdf_name"),
                "source_page": row.get("source_page"),
                "source_table_id": row.get("source_table_id"),
                "image_path": row.get("chosen_image_path"),
                "image_evidence_type": row.get("image_evidence_type"),
                "bbox": row.get("bbox"),
                "mineru_json_or_md_context": {
                    "json_path": row.get("json_context_path", ""),
                    "md_path": row.get("md_context_path", ""),
                    "context_snippet": row.get("context_snippet", ""),
                },
                "structured_row_before_vision": {
                    "raw_metric_name": row.get("raw_metric_name"),
                    "demo_normalized_metric_name": row.get("demo_normalized_metric_name"),
                    "value": row.get("value"),
                    "unit": row.get("unit"),
                    "period": row.get("period"),
                    "quality_issue_codes": row.get("quality_issue_codes"),
                    "quality_severity": row.get("quality_severity"),
                },
                "neighbor_context_rows": row.get("neighbor_context_rows", []),
                "target_field_types": row.get("target_field_types", []),
                "question_list": _question_list(row.get("target_field_types", [])),
                "strict_output_schema_ref": INPUT_346A_VLM_SCHEMA_NAME,
                "do_not_overwrite_source_data": True,
                "live_vlm_call_allowed": False,
            }
        )
    return requests


def _binding_summary(manifest: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "decision": manifest["decision"],
        "input_346a_dir": manifest["input_346a_dir"],
        "output_dir": manifest["output_dir"],
        "supplied_evidence_roots": manifest["supplied_evidence_roots"],
        "binding_candidate_count": manifest["binding_candidate_count"],
        "evidence_catalog_count": manifest["evidence_catalog_count"],
        "bound_row_count": manifest["bound_row_count"],
        "image_bound_count": manifest["image_bound_count"],
        "image_missing_count": manifest["image_missing_count"],
        "ambiguous_image_candidate_count": manifest["ambiguous_image_candidate_count"],
        "json_md_context_bound_count": manifest["json_md_context_bound_count"],
        "vlm_request_count": manifest["vlm_request_count"],
        "live_ready_request_package": manifest["live_ready_request_package"],
    }


def build_mineru_image_path_binding_fix_346a2(
    *,
    vision_assisted_table_evidence_pilot_346a_dir: Path,
    output_dir: Path,
    repo_root: Path,
    ledger_path: Path | None,
    mineru_output_root: Path | None = None,
    mineru_json_md_dir: Path | None = None,
    mineru_table_image_dir: Path | None = None,
    mineru_page_image_dir: Path | None = None,
    table_image_manifest: Path | None = None,
    page_image_manifest: Path | None = None,
    max_binding_candidates_per_row: int = 5,
    max_context_chars: int = 4000,
) -> Dict[str, Any]:
    if not vision_assisted_table_evidence_pilot_346a_dir.exists():
        raise FileNotFoundError(f"346A input directory missing: {vision_assisted_table_evidence_pilot_346a_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_346a_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_MANIFEST_NAME
    selected_rows_json_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_SELECTED_ROWS_JSON_NAME
    selected_rows_csv_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_SELECTED_ROWS_CSV_NAME
    evidence_bundle_json_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_EVIDENCE_BUNDLE_JSON_NAME
    evidence_bundle_csv_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_EVIDENCE_BUNDLE_CSV_NAME
    vlm_schema_path = vision_assisted_table_evidence_pilot_346a_dir / INPUT_346A_VLM_SCHEMA_NAME

    manifest_346a = _read_json(manifest_346a_path)
    selected_rows, selected_rows_source = _load_json_or_csv_rows(
        json_path=selected_rows_json_path,
        csv_path=selected_rows_csv_path,
        label="346A selected pilot rows",
    )
    evidence_bundle_rows, evidence_bundle_source = _load_json_or_csv_rows(
        json_path=evidence_bundle_json_path,
        csv_path=evidence_bundle_csv_path,
        label="346A evidence bundle index",
    )
    _ = _read_json(vlm_schema_path)

    evidence_bundle_by_pilot = {
        _safe_text(row.get("pilot_row_id")): row
        for row in evidence_bundle_rows
        if _safe_text(row.get("pilot_row_id"))
    }
    merged_rows = [
        {
            **selected_row,
            **evidence_bundle_by_pilot.get(_safe_text(selected_row.get("pilot_row_id")), {}),
        }
        for selected_row in selected_rows
    ]

    json_md_roots: List[Path] = []
    table_image_roots: List[Path] = []
    page_image_roots: List[Path] = []
    if mineru_output_root is not None:
        json_md_roots.append(mineru_output_root)
        table_image_roots.append(mineru_output_root)
        page_image_roots.append(mineru_output_root)
    if mineru_json_md_dir is not None:
        json_md_roots.append(mineru_json_md_dir)
    if mineru_table_image_dir is not None:
        table_image_roots.append(mineru_table_image_dir)
    if mineru_page_image_dir is not None:
        page_image_roots.append(mineru_page_image_dir)
    supplied_evidence_roots = [str(path) for path in [mineru_output_root, mineru_json_md_dir, mineru_table_image_dir, mineru_page_image_dir, table_image_manifest, page_image_manifest] if path is not None]
    evidence_supplied = bool(supplied_evidence_roots)

    files_read = [
        str(path)
        for path in [
            manifest_346a_path,
            selected_rows_json_path,
            selected_rows_csv_path,
            evidence_bundle_json_path,
            evidence_bundle_csv_path,
            vlm_schema_path,
            table_image_manifest,
            page_image_manifest,
        ]
        if path is not None and path.exists()
    ]
    for root in json_md_roots + table_image_roots + page_image_roots:
        if root.exists():
            files_read.append(str(root))

    input_paths = [Path(path) for path in files_read if Path(path).is_file()]
    input_hashes_before = {str(path): sha256_file(path) for path in input_paths}
    official_assets_before = capture_official_asset_hashes([SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    protected_before = _git_status_porcelain_for_paths(PROTECTED_DIRTY_PATHS, repo_root)

    table_manifest_rows = _load_manifest_rows(table_image_manifest)
    page_manifest_rows = _load_manifest_rows(page_image_manifest)

    state = EvidenceState()
    _catalog_json_md_roots(state, json_md_roots)
    _catalog_table_image_roots(state, table_image_roots)
    _catalog_page_image_roots(state, page_image_roots)
    _catalog_manifest_rows(state, table_manifest_rows, "table")
    _catalog_manifest_rows(state, page_manifest_rows, "page")

    final_rows: List[Dict[str, Any]] = []
    for row in merged_rows:
        refreshed = _refresh_binding_for_row(
            row,
            state=state,
            selected_rows=merged_rows,
            table_manifest_rows=table_manifest_rows,
            page_manifest_rows=page_manifest_rows,
            max_binding_candidates_per_row=max_binding_candidates_per_row,
            max_context_chars=max_context_chars,
            evidence_supplied=evidence_supplied,
        )
        final_rows.append(refreshed["final_row"])
        state.binding_candidate_rows.extend(refreshed["candidate_rows"])

    image_bound_statuses = {
        "BOUND_TABLE_CROP_IMAGE",
        "BOUND_PAGE_IMAGE_WITH_BBOX",
        "BOUND_PAGE_IMAGE_NO_BBOX",
        "IMAGE_MANIFEST_MATCH",
    }
    bound_statuses = image_bound_statuses | {
        "BOUND_JSON_CONTEXT_ONLY",
        "BOUND_MD_CONTEXT_ONLY",
        "BOUND_TEXT_CONTEXT_ONLY",
    }
    bound_rows = [row for row in final_rows if row.get("image_resolution_status") in bound_statuses]
    unresolved_rows = [
        row
        for row in final_rows
        if row.get("image_resolution_status") in {"NO_IMAGE_EVIDENCE_PROVIDED", "NO_MATCH_FOUND", "READ_ERROR"}
    ]
    ambiguous_rows = [row for row in final_rows if row.get("image_resolution_status") == "AMBIGUOUS_IMAGE_CANDIDATE"]

    image_bound_count = sum(1 for row in final_rows if row.get("image_resolution_status") in image_bound_statuses)
    table_crop_bound_count = sum(1 for row in final_rows if row.get("image_evidence_type") == "TABLE_CROP_IMAGE" and row.get("image_bound"))
    page_image_bound_count = sum(1 for row in final_rows if row.get("image_evidence_type") == "PAGE_IMAGE" and row.get("image_bound"))
    json_md_context_bound_count = sum(1 for row in final_rows if row.get("context_available"))
    image_missing_count = len(final_rows) - image_bound_count
    ambiguous_count = len(ambiguous_rows)

    image_resolution_rows = [
        {
            "pilot_row_id": row.get("pilot_row_id"),
            "source_row_id": row.get("source_row_id"),
            "source_pdf_name": row.get("source_pdf_name"),
            "source_page": row.get("source_page"),
            "source_table_id": row.get("source_table_id"),
            "image_resolution_status": row.get("image_resolution_status"),
            "image_bound": row.get("image_bound"),
            "chosen_image_path": row.get("chosen_image_path"),
            "image_evidence_type": row.get("image_evidence_type"),
            "json_context_path": row.get("json_context_path"),
            "md_context_path": row.get("md_context_path"),
            "bbox": row.get("bbox"),
        }
        for row in final_rows
    ]
    vlm_request_rows = _build_vlm_requests(final_rows)
    vlm_request_preview = {
        "request_count": len(vlm_request_rows),
        "live_ready_request_package": bool(vlm_request_rows),
        "empty_reason": "" if vlm_request_rows else "No deterministic image-bound rows were available.",
        "requests": vlm_request_rows[:5],
    }

    context_index_export_rows = []
    for row in state.context_index_rows:
        context_index_export_rows.append(
            {
                **row,
                "json_paths": row.get("json_paths", []),
                "md_paths": row.get("md_paths", []),
                "content_list_paths": row.get("content_list_paths", []),
                "content_list_v2_paths": row.get("content_list_v2_paths", []),
                "middle_json_paths": row.get("middle_json_paths", []),
                "model_json_paths": row.get("model_json_paths", []),
            }
        )

    manifest = {
        "decision": READY_DECISION_346A2,
        "input_stage": INPUT_STAGE_346A2,
        "qa_fail_count": 0,
        "no_write_back_proof_passed": False,
        "formal_client_export_allowed": False,
        "client_ready": False,
        "production_ready": False,
        "global_strict_human_review_completed": False,
        "input_346a_decision": _safe_text(manifest_346a.get("decision")),
        "input_346a_qa_fail_count": int(manifest_346a.get("qa_fail_count", 1)),
        "input_346a_dir": str(vision_assisted_table_evidence_pilot_346a_dir),
        "output_dir": str(output_dir),
        "selected_pilot_row_count": len(final_rows),
        "input_346a_image_bound_count": int(manifest_346a.get("image_bound_count", 0)),
        "input_346a_image_missing_count": int(manifest_346a.get("image_missing_count", 0)),
        "binding_candidate_count": len(state.binding_candidate_rows),
        "evidence_catalog_count": len(state.evidence_catalog_rows),
        "table_crop_image_catalog_count": sum(1 for row in state.evidence_catalog_rows if row.get("evidence_type") == "TABLE_CROP_IMAGE"),
        "page_image_catalog_count": sum(1 for row in state.evidence_catalog_rows if row.get("evidence_type") == "PAGE_IMAGE"),
        "json_context_catalog_count": sum(1 for row in state.evidence_catalog_rows if row.get("evidence_type") == "JSON_CONTEXT"),
        "md_context_catalog_count": sum(1 for row in state.evidence_catalog_rows if row.get("evidence_type") == "MD_CONTEXT"),
        "bound_row_count": len(bound_rows),
        "image_bound_count": image_bound_count,
        "table_crop_bound_count": table_crop_bound_count,
        "page_image_bound_count": page_image_bound_count,
        "json_md_context_bound_count": json_md_context_bound_count,
        "image_missing_count": image_missing_count,
        "ambiguous_image_candidate_count": ambiguous_count,
        "vlm_request_count": len(vlm_request_rows),
        "live_vlm_call_count": 0,
        "vlm_response_count": 0,
        "official_rules_modified": False,
        "official_alias_assets_modified": False,
        "formal_export_generated": False,
        "demo_export_only": True,
        "vlm_request_package_only": True,
        "upstream_data_mutated": False,
        "milestone_ledger_updated": False,
        "supplied_evidence_roots": supplied_evidence_roots,
        "selected_rows_source": selected_rows_source,
        "evidence_bundle_source": evidence_bundle_source,
        "live_ready_request_package": bool(vlm_request_rows),
        "max_binding_candidates_per_row": max_binding_candidates_per_row,
        "max_context_chars": max_context_chars,
        "read_error_count": len(state.read_errors),
        "read_errors": state.read_errors[:20],
        "recommended_next_step": "",
        "recommended_next_step_reason": "",
        "generated_at_utc": _utc_now(),
    }

    if not evidence_supplied:
        manifest["recommended_next_step"] = "346A2R Provide MinerU Evidence Roots"
        manifest["recommended_next_step_reason"] = "No MinerU evidence roots or manifests were supplied, so image binding could not start."
    elif image_bound_count >= max(10, len(final_rows) // 5):
        manifest["recommended_next_step"] = "346B Quality-Limited Row Recovery Pilot"
        manifest["recommended_next_step_reason"] = "Enough deterministic image-bound rows now exist to support a bounded recovery pilot."
    else:
        manifest["recommended_next_step"] = "346A3 Binding Rule Refinement"
        manifest["recommended_next_step_reason"] = "Evidence roots were supplied, but too many rows remain unresolved or ambiguous."

    validation_checks = [
        manifest["input_346a_decision"] == READY_DECISION_346A,
        manifest["input_346a_qa_fail_count"] == 0,
        len(final_rows) == int(manifest_346a.get("selected_pilot_row_count", len(final_rows))),
        manifest["binding_candidate_count"] >= 0,
        manifest["evidence_catalog_count"] >= 0,
        manifest["live_vlm_call_count"] == 0,
        manifest["official_rules_modified"] is False,
        manifest["official_alias_assets_modified"] is False,
        manifest["formal_export_generated"] is False,
        manifest["demo_export_only"] is True,
        manifest["formal_client_export_allowed"] is False,
        manifest["client_ready"] is False,
        manifest["production_ready"] is False,
        manifest["vlm_request_count"] == image_bound_count,
        (manifest["image_missing_count"] == len(final_rows) if not evidence_supplied else manifest["image_missing_count"] == len(final_rows) - image_bound_count),
    ]

    no_apply_proof = build_no_apply_proof(
        stage="346A2",
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
        no_apply_proof.get("no_official_asset_modification_during_346a2")
        and upstream_unchanged
        and protected_before == protected_after
        and not protected_staged
        and not forbidden_staged
    )
    manifest["no_write_back_proof_passed"] = no_write_back_proof_passed
    manifest["no_write_back_summary"] = "upstream inputs unchanged; official assets unchanged; protected dirty status preserved; no protected paths staged"

    if ledger_path is not None:
        append_346a2_ledger_entry(manifest=manifest, ledger_path=ledger_path)
        manifest["milestone_ledger_updated"] = _ledger_has_346a2_entry(ledger_path)
    validation_checks.append(manifest["milestone_ledger_updated"] or ledger_path is None)
    validation_checks.append(no_write_back_proof_passed)

    qa_fail_count = sum(1 for check in validation_checks if not check)
    manifest["qa_fail_count"] = qa_fail_count
    manifest["decision"] = READY_DECISION_346A2 if qa_fail_count == 0 else BLOCKED_DECISION_346A2

    return {
        "manifest": manifest,
        "evidence_catalog_rows": state.evidence_catalog_rows,
        "binding_candidate_rows": state.binding_candidate_rows,
        "bound_rows": bound_rows,
        "unresolved_rows": unresolved_rows,
        "ambiguous_rows": ambiguous_rows,
        "image_resolution_rows": image_resolution_rows,
        "context_index_rows": context_index_export_rows,
        "vlm_request_rows": vlm_request_rows,
        "vlm_request_preview": vlm_request_preview,
        "binding_summary": _binding_summary(manifest),
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
    }
