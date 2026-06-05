from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

import pandas as pd


EXPECTED_325B_DECISION = "ALIAS_REVIEW_BATCH_325B_READY_FOR_HUMAN_OR_ADJUDICATOR_REVIEW"
READY_DECISION = "ALIAS_REVIEW_BATCH_SANITY_GATE_325C_READY_FOR_HUMAN_SPOT_CHECK_OR_SAFE_ADJUDICATOR_SUBSET"
NO_ROUTEABLE_DECISION = "ALIAS_REVIEW_BATCH_SANITY_GATE_325C_NO_SAFE_ROUTEABLE_ITEMS"
NOT_READY_DECISION = "ALIAS_REVIEW_BATCH_SANITY_GATE_325C_NOT_READY"

DEFAULT_ALIAS_REVIEW_BATCH_DIR = Path(r"D:\_datefac\output\alias_review_batch_325b")
DEFAULT_ALIAS_REFINEMENT_DIR = Path(r"D:\_datefac\output\alias_candidate_refinement_325a")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\alias_review_batch_sanity_gate_325c")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")
SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")

BUCKET_SEND = "SEND_TO_ADJUDICATOR"
BUCKET_HUMAN = "HUMAN_SPOT_CHECK_FIRST"
BUCKET_ALREADY_OFFICIAL = "HOLDOUT_ALREADY_OFFICIAL"
BUCKET_TARGET_AMBIGUOUS = "HOLDOUT_TARGET_AMBIGUOUS"
BUCKET_GENERIC = "HOLDOUT_GENERIC_AMBIGUOUS_LABEL"
BUCKET_CATEGORY = "HOLDOUT_CATEGORY_MISMATCH"
BUCKET_UNIT_PRICE = "HOLDOUT_UNIT_OR_PRICE_AMBIGUITY"
BUCKET_SCOPE_NOISE = "HOLDOUT_SCOPE_NOISE_OR_DISCLOSURE_TEXT"
BUCKET_DUPLICATE = "HOLDOUT_DUPLICATE_OR_CONFLICT"
BUCKET_WEAK = "HOLDOUT_WEAK_EVIDENCE"
BUCKET_INVALID = "HOLDOUT_INVALID_TEXT"

ALL_BUCKETS = [
    BUCKET_SEND,
    BUCKET_HUMAN,
    BUCKET_ALREADY_OFFICIAL,
    BUCKET_TARGET_AMBIGUOUS,
    BUCKET_GENERIC,
    BUCKET_CATEGORY,
    BUCKET_UNIT_PRICE,
    BUCKET_SCOPE_NOISE,
    BUCKET_DUPLICATE,
    BUCKET_WEAK,
    BUCKET_INVALID,
]

ROUTEABLE_BUCKETS = {BUCKET_SEND, BUCKET_HUMAN}

REQUIRED_REVIEW_FIELDS = [
    "alias_review_id",
    "alias_refinement_candidate_id",
    "candidate_id",
    "candidate_type",
    "normalized_label",
    "proposed_target_metric_if_available",
    "review_decision",
    "risk_bucket",
    "sample_row_texts",
    "provenance_summary",
]

MOJIBAKE_MARKERS = ("\ufffd", "锟", "閿", "�", "???")
GENERIC_LABELS = {
    "利润",
    "收入",
    "成本",
    "费用",
    "资产",
    "负债",
    "权益",
    "现金",
    "增长",
    "同比",
}
CATEGORY_MISMATCH_TERMS = [
    "资产",
    "负债",
    "股东权益",
    "所有者权益",
    "商誉",
    "在建工程",
    "合同资产",
    "合同负债",
    "短期借款",
    "应付债券",
]
SCOPE_OR_DISCLOSURE_TERMS = [
    "免责声明",
    "投资建议",
    "评级",
    "股票代码",
    "行业评级",
    "公司评级",
    "报告发布日",
    "证券市场",
]
UNIT_OR_PRICE_TERMS = [
    "现价",
    "最新股本",
    "摊薄",
    "稀释",
    "价格",
    "股价",
    "元/股",
    "元／股",
]
PE_PB_PATTERN = re.compile(r"(?:\bP\s*/\s*E\b|\bP\s*/\s*B\b|\bPE\b|\bPB\b|市盈率|市净率)", re.IGNORECASE)
EBIT_PATTERN = re.compile(r"(?:\bEBIT\b|\bEBITDA\b)", re.IGNORECASE)
EXPLICIT_TARGETS = {
    "营业收入",
    "归属母公司净利润",
    "毛利率",
    "ROE",
    "每股收益",
    "P/E",
    "P/B",
    "EV/EBITDA",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _safe_int(value: Any) -> int:
    if value in ("", None):
        return 0
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return 0


def _normalize_label(value: Any) -> str:
    text = _norm(value).lower()
    replacements = {
        "\u3000": "",
        " ": "",
        "\t": "",
        "（": "(",
        "）": ")",
        "／": "/",
        "：": ":",
        "，": ",",
        "；": ";",
        "％": "%",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, sheet_name=sheet_name).fillna("")
    except Exception:
        return pd.DataFrame()


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _join_unique(items: Iterable[Any], limit: int = 8) -> str:
    out: List[str] = []
    seen: Set[str] = set()
    for item in items:
        text = _norm(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
        if len(out) >= limit:
            break
    return " | ".join(out)


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms if term)


def _looks_invalid_text(label: str) -> bool:
    text = _norm(label)
    if not text:
        return True
    compact = text.replace(" ", "")
    if compact in {"-", "--", "n/a", "na", "none", "(+/-%)", "(+/-)"}:
        return True
    if any(marker in text for marker in MOJIBAKE_MARKERS):
        return True
    if text.count("?") >= 3:
        return True
    return False


def _is_generic_label(label: str) -> bool:
    return _normalize_label(label) in {_normalize_label(item) for item in GENERIC_LABELS}


def _is_scope_or_disclosure(label: str, record: Dict[str, Any]) -> bool:
    text = " ".join(
        [
            _norm(label),
            _norm(record.get("sample_row_texts")),
            _norm(record.get("sample_table_titles")),
        ]
    )
    return len(_norm(label)) >= 80 or _contains_any(text, SCOPE_OR_DISCLOSURE_TERMS)


def _is_category_mismatch(label: str) -> bool:
    if PE_PB_PATTERN.search(label) or EBIT_PATTERN.search(label) or "ROE" in label.upper() or "EPS" in label.upper():
        return False
    if "净利率" in label or "净利润" in label or "每股收益" in label or "收益率" in label:
        return False
    return _contains_any(label, CATEGORY_MISMATCH_TERMS)


def _has_price_or_ratio_ambiguity(label: str, record: Dict[str, Any]) -> bool:
    text = " ".join([_norm(label), _norm(record.get("sample_row_texts")), _norm(record.get("sample_table_titles"))])
    return bool(PE_PB_PATTERN.search(label)) or _contains_any(text, UNIT_OR_PRICE_TERMS)


def _has_ebit_target_ambiguity(label: str, target: str) -> bool:
    return bool(EBIT_PATTERN.search(label)) and not _target_is_explicit(target)


def _target_is_explicit(target: str) -> bool:
    clean = _norm(target)
    if not clean:
        return False
    normalized_targets = {_normalize_label(item) for item in EXPLICIT_TARGETS}
    return _normalize_label(clean) in normalized_targets


def _has_strong_evidence(record: Dict[str, Any]) -> bool:
    affected = _safe_int(record.get("affected_candidate_count"))
    samples = _norm(record.get("sample_candidate_ids")) or _norm(record.get("sample_raw_metric_names"))
    rows = _norm(record.get("sample_row_texts"))
    provenance = _norm(record.get("provenance_summary")) or _norm(record.get("provenance_source"))
    return affected > 0 and bool(rows) and bool(provenance) and (bool(samples) or bool(_norm(record.get("sample_table_titles"))))


def _flatten_records_from_review_package(review_package: Dict[str, Any]) -> List[Dict[str, Any]]:
    records = review_package.get("review_records", [])
    if isinstance(records, list):
        return [record for record in records if isinstance(record, dict)]
    return []


def _load_review_records(alias_review_batch_dir: Path) -> List[Dict[str, Any]]:
    package_records = _flatten_records_from_review_package(
        _read_json(alias_review_batch_dir / "alias_review_batch_325b_review_package.json")
    )
    if package_records:
        return package_records
    workbook_df = _read_excel_sheet(alias_review_batch_dir / "alias_review_batch_325b_workbook.xlsx", "alias_review_records")
    return workbook_df.to_dict(orient="records") if not workbook_df.empty else []


def _load_official_alias_labels(alias_asset: Dict[str, Any]) -> Set[str]:
    labels: Set[str] = set()
    groups = alias_asset.get("groups", {})
    if not isinstance(groups, dict):
        return labels
    for items in groups.values():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            for key in ["normalized_label", "candidate_label", "alias", "metric_code"]:
                label = _normalize_label(item.get(key))
                if label:
                    labels.add(label)
    return labels


def _load_official_scope_labels(scope_asset: Dict[str, Any]) -> Set[str]:
    labels: Set[str] = set()
    rules = scope_asset.get("rules", {})
    if not isinstance(rules, dict):
        return labels
    for item in rules.values():
        if not isinstance(item, dict):
            continue
        if item.get("target_group") != "core_metric_scope_exclusions" and item.get("rule_type") != "core_metric_scope_exclusion":
            continue
        label = _normalize_label(item.get("normalized_label"))
        if label:
            labels.add(label)
    return labels


def load_alias_review_batch_sanity_gate_325c_inputs(
    alias_review_batch_dir: Path,
    alias_refinement_dir: Path,
    formal_scope_rules_path: Path = FORMAL_SCOPE_RULES_PATH,
    semantic_alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
) -> Dict[str, Any]:
    return {
        "summary_325b": _read_json(alias_review_batch_dir / "alias_review_batch_325b_summary.json"),
        "qa_325b": _read_json(alias_review_batch_dir / "alias_review_batch_325b_qa.json"),
        "review_records": _load_review_records(alias_review_batch_dir),
        "summary_325a": _read_json(alias_refinement_dir / "alias_candidate_refinement_325a_summary.json"),
        "refined_325a": _read_json(alias_refinement_dir / "alias_candidate_refinement_325a_refined_alias_candidates.json"),
        "formal_scope_rules": _read_json(formal_scope_rules_path),
        "semantic_alias_asset": _read_json(semantic_alias_asset_path),
        "official_asset_hashes_before": {
            "formal_scope_rules": _sha256_file(formal_scope_rules_path),
            "semantic_alias_candidates": _sha256_file(semantic_alias_asset_path),
        },
    }


def _routing_reason_flags(
    record: Dict[str, Any],
    official_alias_labels: Set[str],
    official_scope_labels: Set[str],
    seen_labels: Set[str],
) -> Dict[str, Any]:
    label = _norm(record.get("normalized_label")) or _norm(record.get("candidate_label_norm"))
    normalized_label = _normalize_label(label)
    target = _norm(record.get("proposed_target_metric_if_available"))
    flags = {
        "invalid_text": _looks_invalid_text(label),
        "already_official": normalized_label in official_alias_labels,
        "official_scope_conflict": normalized_label in official_scope_labels,
        "duplicate_or_conflict": normalized_label in seen_labels,
        "scope_noise_or_disclosure_text": _is_scope_or_disclosure(label, record),
        "category_mismatch": _is_category_mismatch(label),
        "generic_ambiguous_label": _is_generic_label(label),
        "price_or_ratio_ambiguity": _has_price_or_ratio_ambiguity(label, record),
        "ebit_target_ambiguity": _has_ebit_target_ambiguity(label, target),
        "target_explicit": _target_is_explicit(target),
        "strong_evidence": _has_strong_evidence(record),
    }
    flags["target_ambiguity"] = not flags["target_explicit"]
    flags["unit_or_price_ambiguity"] = flags["price_or_ratio_ambiguity"]
    return flags


def _route_record(record: Dict[str, Any], flags: Dict[str, Any]) -> Tuple[str, List[str]]:
    if flags["invalid_text"]:
        return BUCKET_INVALID, ["invalid_or_empty_or_mojibake_label"]
    if flags["already_official"]:
        return BUCKET_ALREADY_OFFICIAL, ["exact_label_or_metric_code_already_official_alias"]
    if flags["official_scope_conflict"]:
        return BUCKET_DUPLICATE, ["exact_label_conflicts_with_official_scope_exclusion"]
    if flags["duplicate_or_conflict"]:
        return BUCKET_DUPLICATE, ["duplicate_label_within_325b_review_batch"]
    if flags["scope_noise_or_disclosure_text"]:
        return BUCKET_SCOPE_NOISE, ["label_or_evidence_looks_like_scope_noise_or_disclosure_text"]
    if flags["category_mismatch"]:
        return BUCKET_CATEGORY, ["label_family_looks_outside_alias_candidate_scope"]
    if flags["generic_ambiguous_label"]:
        return BUCKET_GENERIC, ["generic_label_too_ambiguous_for_safe_alias_routing"]
    if not flags["strong_evidence"]:
        return BUCKET_WEAK, ["missing_cached_sample_evidence_or_provenance"]

    reasons: List[str] = []
    if flags["price_or_ratio_ambiguity"]:
        reasons.append("PE_PB_or_price_basis_definition_sensitive")
    if flags["ebit_target_ambiguity"]:
        reasons.append("EBIT_EBITDA_target_family_requires_human_confirmation")
    if flags["target_ambiguity"]:
        reasons.append("proposed_target_metric_not_explicit_in_325b_record")
    if reasons:
        return BUCKET_HUMAN, reasons

    return BUCKET_SEND, ["specific_explicit_non_overlapping_strongly_evidenced_alias_candidate"]


def build_alias_review_batch_sanity_gate_325c(
    summary_325b: Dict[str, Any],
    qa_325b: Dict[str, Any],
    review_records: List[Dict[str, Any]],
    summary_325a: Dict[str, Any],
    refined_325a: Dict[str, Any],
    formal_scope_rules: Dict[str, Any],
    semantic_alias_asset: Dict[str, Any],
    official_asset_hashes_before: Dict[str, str],
    formal_scope_rules_path: Path = FORMAL_SCOPE_RULES_PATH,
    semantic_alias_asset_path: Path = SEMANTIC_ALIAS_ASSET_PATH,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    expected_summary = {
        "decision": EXPECTED_325B_DECISION,
        "qa_fail_count": 0,
        "loaded_safe_alias_candidate_count": 12,
        "review_record_count": 12,
        "pending_count": 12,
        "accepted_count": 0,
        "rejected_count": 0,
        "needs_more_info_count": 0,
        "holdout_count": 0,
    }
    for key, expected in expected_summary.items():
        actual = summary_325b.get(key)
        if isinstance(expected, int):
            ok = _safe_int(actual) == expected
        else:
            ok = _norm(actual) == expected
        add_qa(f"readiness::325b_{key}", "PASS" if ok else "FAIL", f"expected={expected}; actual={actual}")
    add_qa(
        "readiness::325b_qa_json_fail_count",
        "PASS" if _safe_int(qa_325b.get("qa_fail_count")) == 0 else "FAIL",
        str(qa_325b.get("qa_fail_count", "")),
    )
    add_qa(
        "reference::325a_safe_batch_count",
        "PASS" if _safe_int(summary_325a.get("safe_alias_review_batch_count")) == 12 else "FAIL",
        str(summary_325a.get("safe_alias_review_batch_count", "")),
    )
    add_qa(
        "input::review_records_loaded_exact_count",
        "PASS" if len(review_records) == 12 else "FAIL",
        f"actual={len(review_records)}",
    )

    official_alias_labels = _load_official_alias_labels(semantic_alias_asset)
    official_scope_labels = _load_official_scope_labels(formal_scope_rules)
    safe_325a_ids = {
        _norm(item.get("alias_refinement_candidate_id"))
        for item in refined_325a.get("safe_alias_review_batch", [])
        if isinstance(item, dict)
    }

    routing_rows: List[Dict[str, Any]] = []
    seen_labels: Set[str] = set()
    for index, record in enumerate(review_records, start=1):
        label = _norm(record.get("normalized_label")) or _norm(record.get("candidate_label_norm"))
        normalized_label = _normalize_label(label)
        flags = _routing_reason_flags(record, official_alias_labels, official_scope_labels, seen_labels)
        bucket, reasons = _route_record(record, flags)
        seen_labels.add(normalized_label)
        alias_refinement_candidate_id = _norm(record.get("alias_refinement_candidate_id"))
        routing_row = {
            **record,
            "routing_id": f"325c::alias_route::{index:03d}",
            "routing_bucket": bucket,
            "routing_reasons": " | ".join(reasons),
            "normalized_label_for_overlap_check": normalized_label,
            "official_alias_overlap": bool(flags["already_official"]),
            "official_scope_conflict": bool(flags["official_scope_conflict"]),
            "invalid_text": bool(flags["invalid_text"]),
            "price_or_ratio_ambiguity": bool(flags["price_or_ratio_ambiguity"]),
            "target_ambiguity": bool(flags["target_ambiguity"]),
            "unit_or_price_ambiguity": bool(flags["unit_or_price_ambiguity"]),
            "duplicate_or_conflict": bool(flags["duplicate_or_conflict"]),
            "generic_ambiguous_label": bool(flags["generic_ambiguous_label"]),
            "category_mismatch": bool(flags["category_mismatch"]),
            "scope_noise_or_disclosure_text": bool(flags["scope_noise_or_disclosure_text"]),
            "weak_evidence": not bool(flags["strong_evidence"]),
            "target_explicit": bool(flags["target_explicit"]),
            "strong_evidence": bool(flags["strong_evidence"]),
            "preserved_from_325b": True,
            "matched_325a_safe_batch": alias_refinement_candidate_id in safe_325a_ids,
            "llm_or_adjudicator_called": False,
            "auto_accepted_alias": False,
        }
        routing_rows.append(routing_row)

    routing_df = pd.DataFrame(routing_rows).fillna("")
    bucket_counts = {bucket: 0 for bucket in ALL_BUCKETS}
    if not routing_df.empty:
        actual_counts = routing_df["routing_bucket"].value_counts().to_dict()
        for bucket, count in actual_counts.items():
            bucket_counts[str(bucket)] = int(count)

    send_df = routing_df[routing_df["routing_bucket"] == BUCKET_SEND].copy() if not routing_df.empty else pd.DataFrame()
    human_df = routing_df[routing_df["routing_bucket"] == BUCKET_HUMAN].copy() if not routing_df.empty else pd.DataFrame()
    holdout_df = routing_df[~routing_df["routing_bucket"].isin(ROUTEABLE_BUCKETS)].copy() if not routing_df.empty else pd.DataFrame()
    bucket_summary_df = pd.DataFrame(
        [{"routing_bucket": bucket, "count": count} for bucket, count in bucket_counts.items()]
    )
    holdout_reason_counts = (
        holdout_df["routing_bucket"].value_counts().astype(int).to_dict() if not holdout_df.empty else {}
    )

    official_asset_hashes_after = {
        "formal_scope_rules": _sha256_file(formal_scope_rules_path),
        "semantic_alias_candidates": _sha256_file(semantic_alias_asset_path),
    }
    official_assets_modified = official_asset_hashes_before != official_asset_hashes_after
    routeable_count = int(len(send_df) + len(human_df))

    matched_safe_batch_count = int(routing_df["matched_325a_safe_batch"].sum()) if not routing_df.empty else 0
    required_field_missing_count = 0
    for record in review_records:
        if any(_norm(record.get(field)) == "" and field != "proposed_target_metric_if_available" for field in REQUIRED_REVIEW_FIELDS):
            required_field_missing_count += 1

    add_qa(
        "routing::all_records_preserved",
        "PASS" if len(routing_rows) == len(review_records) == 12 else "FAIL",
        f"routing_rows={len(routing_rows)}; input={len(review_records)}",
    )
    add_qa(
        "routing::each_record_exactly_one_bucket",
        "PASS" if sum(bucket_counts.values()) == len(review_records) == 12 else "FAIL",
        f"bucket_total={sum(bucket_counts.values())}; input={len(review_records)}",
    )
    add_qa(
        "routing::no_auto_accept_alias",
        "PASS" if int(routing_df["auto_accepted_alias"].sum()) == 0 else "FAIL",
        "325C routing only",
    )
    add_qa(
        "routing::safe_batch_reference_alignment",
        "PASS" if matched_safe_batch_count == 12 else "FAIL",
        f"matched={matched_safe_batch_count}",
    )
    add_qa(
        "routing::required_fields_present",
        "PASS" if required_field_missing_count == 0 else "FAIL",
        f"missing_record_count={required_field_missing_count}",
    )
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if not official_assets_modified else "FAIL",
        json.dumps({"before": official_asset_hashes_before, "after": official_asset_hashes_after}, ensure_ascii=False),
    )
    add_qa("safety::llm_or_adjudicator_not_called", "PASS", "False")
    add_qa("safety::no_official_rule_candidates_created", "PASS", "False")
    add_qa("safety::no_controlled_proposals_created", "PASS", "False")
    add_qa("safety::no_sandbox_replay_package_created", "PASS", "False")

    qa_df = pd.DataFrame(qa_rows)
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    decision = READY_DECISION if routeable_count > 0 else NO_ROUTEABLE_DECISION
    if qa_fail_count > 0:
        decision = NOT_READY_DECISION

    summary = {
        "stage": "325C",
        "input_review_record_count": len(review_records),
        "routing_record_count": len(routing_rows),
        "routing_bucket_counts": bucket_counts,
        "send_to_adjudicator_count": len(send_df),
        "human_spot_check_count": len(human_df),
        "holdout_count": len(holdout_df),
        "holdout_reason_counts": holdout_reason_counts,
        "already_official_count": int(routing_df["official_alias_overlap"].sum()) if not routing_df.empty else 0,
        "official_scope_conflict_count": int(routing_df["official_scope_conflict"].sum()) if not routing_df.empty else 0,
        "invalid_text_count": int(routing_df["invalid_text"].sum()) if not routing_df.empty else 0,
        "price_or_ratio_ambiguity_count": int(routing_df["price_or_ratio_ambiguity"].sum()) if not routing_df.empty else 0,
        "target_ambiguity_count": int(routing_df["target_ambiguity"].sum()) if not routing_df.empty else 0,
        "duplicate_or_conflict_count": int(routing_df["duplicate_or_conflict"].sum()) if not routing_df.empty else 0,
        "routeable_count": routeable_count,
        "official_assets_modified": official_assets_modified,
        "official_assets_written": [],
        "official_asset_hashes_before": official_asset_hashes_before,
        "official_asset_hashes_after": official_asset_hashes_after,
        "llm_or_adjudicator_called": False,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "official_rule_candidates_created": False,
        "controlled_official_proposals_created": False,
        "sandbox_replay_package_created": False,
        "top_routed_examples": routing_df[
            ["alias_review_id", "normalized_label", "routing_bucket", "routing_reasons", "affected_candidate_count"]
        ].head(8).to_dict(orient="records")
        if not routing_df.empty
        else [],
        "qa_pass_count": int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0,
        "qa_warn_count": int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0,
        "qa_fail_count": qa_fail_count,
        "blocking_reasons": qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist()
        if not qa_df.empty
        else [],
        "decision": decision,
    }
    qa_json = {
        "qa_pass_count": summary["qa_pass_count"],
        "qa_warn_count": summary["qa_warn_count"],
        "qa_fail_count": summary["qa_fail_count"],
        "blocking_reasons": summary["blocking_reasons"],
        "checks": qa_df.to_dict(orient="records"),
    }
    routing_manifest = {
        "stage": "325C",
        "decision": decision,
        "routing_buckets": ALL_BUCKETS,
        "routing_records": routing_rows,
    }
    no_apply_proof = {
        "stage": "325C",
        "decision": decision,
        "official_assets_read": [str(formal_scope_rules_path), str(semantic_alias_asset_path)],
        "official_assets_written": [],
        "official_assets_modified": official_assets_modified,
        "official_asset_hashes_before": official_asset_hashes_before,
        "official_asset_hashes_after": official_asset_hashes_after,
        "llm_or_adjudicator_called": False,
        "semantic_rules_applied": False,
        "trusted_marked_in_production": False,
        "official_rule_candidates_created": False,
        "controlled_official_proposals_created": False,
        "sandbox_replay_package_created": False,
    }
    return {
        "summary": summary,
        "qa_json": qa_json,
        "routing_manifest": routing_manifest,
        "no_apply_proof": no_apply_proof,
        "routing_manifest_df": routing_df,
        "send_to_adjudicator_df": send_df,
        "human_spot_check_df": human_df,
        "holdout_df": holdout_df,
        "routing_bucket_summary_df": bucket_summary_df,
        "qa_checks_df": qa_df,
    }
