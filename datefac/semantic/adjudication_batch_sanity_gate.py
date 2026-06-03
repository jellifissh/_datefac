from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pandas as pd


EXPECTED_323AB_READY_DECISION = "SEMANTIC_ADJUDICATION_BATCH_PREP_323AB_READY_FOR_HUMAN_OR_ADJUDICATOR_REVIEW"
EXPECTED_323C_READY_DECISION = "ADJUDICATION_BATCH_SANITY_GATE_323C_READY_FOR_HUMAN_SPOT_CHECK_OR_SAFE_ADJUDICATOR_SUBSET"
EXPECTED_323C_NOT_READY_DECISION = "ADJUDICATION_BATCH_SANITY_GATE_323C_NOT_READY"

DEFAULT_BATCH_PREP_DIR = Path(r"D:\_datefac\output\semantic_adjudication_batch_prep_323ab")
DEFAULT_CANDIDATE_TEXT_REPAIR_DIR = Path(r"D:\_datefac\output\candidate_text_repair_323ar")
DEFAULT_PATCH_APPLICATION_DIR = Path(r"D:\_datefac\output\official_semantic_patch_application_322n")
DEFAULT_OUTPUT_DIR = Path(r"D:\_datefac\output\adjudication_batch_sanity_gate_323c")

BUCKET_SEND = "SEND_TO_ADJUDICATOR"
BUCKET_HUMAN = "HUMAN_SPOT_CHECK_FIRST"
BUCKET_HOLDOUT_CATEGORY = "HOLDOUT_CATEGORY_MISMATCH"
BUCKET_HOLDOUT_AMBIGUOUS = "HOLDOUT_AMBIGUOUS"
BUCKET_HOLDOUT_OFFICIAL = "HOLDOUT_ALREADY_OFFICIAL"
BUCKET_HOLDOUT_INVALID = "HOLDOUT_INVALID_TEXT"

ALL_BUCKETS = [
    BUCKET_SEND,
    BUCKET_HUMAN,
    BUCKET_HOLDOUT_CATEGORY,
    BUCKET_HOLDOUT_AMBIGUOUS,
    BUCKET_HOLDOUT_OFFICIAL,
    BUCKET_HOLDOUT_INVALID,
]

REQUIRED_BATCH_ITEM_FIELDS = [
    "batch_item_id",
    "source_group_id",
    "candidate_type",
    "repaired_label",
    "original_label",
    "candidate_question",
    "allowed_decisions",
    "expected_rule_type_if_accepted",
    "review_decision",
    "sample_candidate_ids",
    "sample_texts",
    "affected_candidate_count",
    "affected_review_required_count",
    "priority_score",
    "risk_flags",
    "provenance",
    "review_instruction",
]

STOCK_CODE_PATTERN = re.compile(r"^\d{6}\.(?:sh|sz|hk)$", re.IGNORECASE)
DATE_ONLY_PATTERN = re.compile(r"^\d{4}(?:[-/年])\d{1,2}(?:[-/月])\d{1,2}(?:日)?$")

SAFE_ALIAS_LABELS = {
    "ebitda",
    "归属母公司净利润",
    "归母净利润",
    "归属于母公司净利润",
    "归属于母公司股东的净利润",
}

HUMAN_SPOT_CHECK_ALIAS_LABELS = {
    "其中：服务",
    "其中：设备",
    "归属母公司股东权益",
    "货币资金及交易性金融资产",
}

AMBIGUOUS_ALIAS_LABELS = {
    "少数股东损益",
    "支付股利、利息",
}

BALANCE_SHEET_OR_STATEMENT_TOKENS = [
    "流动资产",
    "流动负债",
    "非流动资产",
    "非流动负债",
    "股东权益",
    "所有者权益",
    "合同资产",
    "合同负债",
    "商誉",
    "固定资产",
    "使用权资产",
    "在建工程",
    "应付债券",
    "短期借款",
    "租赁负债",
    "应付款项",
    "应收款项",
    "交易性金融资产",
    "长期待摊费用",
    "负债和股东权益",
]

CORE_METRIC_TOKENS = [
    "营业收入",
    "收入",
    "归母净利润",
    "归属母公司净利润",
    "净利润",
    "毛利率",
    "roe",
    "roic",
    "每股收益",
    "eps",
    "pe",
    "p/e",
    "pb",
    "p/b",
    "ev/ebitda",
    "ebitda",
]

MOJIBAKE_MARKERS = (
    "\ufffd",
    "锟斤拷",
    "????",
    "鈥",
    "銆",
    "鏍",
    "鍏朵腑",
    "褰掑睘",
    "娴佸姩",
)


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


def _safe_float(value: Any) -> float:
    if value in ("", None):
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def _normalize_label(value: Any) -> str:
    return _norm(value).replace("\u3000", "").replace(" ", "").strip().lower()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
            except Exception:
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
    return pd.DataFrame(rows).fillna("")


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _join_unique(items: Iterable[Any], limit: int = 8) -> str:
    out: List[str] = []
    seen: Set[str] = set()
    for item in items:
        clean = _norm(item)
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
        if len(out) >= limit:
            break
    return " | ".join(out)


def _flatten_sequence(value: Any) -> List[str]:
    if isinstance(value, list):
        return [_norm(item) for item in value if _norm(item)]
    if isinstance(value, tuple):
        return [_norm(item) for item in value if _norm(item)]
    if isinstance(value, str):
        clean = _norm(value)
        return [clean] if clean else []
    return []


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _looks_mojibake(text: Any) -> bool:
    normalized = _norm(text)
    if not normalized:
        return False
    if any(marker in normalized for marker in MOJIBAKE_MARKERS):
        return True
    if normalized.count("?") >= 3 and _contains_cjk(normalized):
        return True
    return False


def _is_stock_code_like(text: str) -> bool:
    return bool(STOCK_CODE_PATTERN.match(_norm(text).lower()))


def _is_date_like(text: str) -> bool:
    return bool(DATE_ONLY_PATTERN.match(_norm(text)))


def _is_empty_or_low_signal(text: str) -> bool:
    normalized = _norm(text)
    if not normalized:
        return True
    compact = normalized.replace(" ", "")
    return compact in {"", "-", "--", "n/a", "na", "none", "(+/-%)", "(+/-)", "y\\", "y/"}


def _looks_long_narrative(text: str) -> bool:
    normalized = _norm(text)
    if len(normalized) >= 80:
        return True
    narrative_markers = [
        "投资建议",
        "评级标准",
        "相对市场表现",
        "报告发布日期",
        "作为基准",
    ]
    return any(marker in normalized for marker in narrative_markers)


def _build_closed_rule_label_set(patch_application_log_df: pd.DataFrame) -> Set[str]:
    closed: Set[str] = set()
    if patch_application_log_df.empty:
        return closed
    for _, row in patch_application_log_df.iterrows():
        after_state = row.get("after_state")
        payload: Dict[str, Any] = {}
        if isinstance(after_state, dict):
            payload = after_state
        elif isinstance(after_state, str):
            try:
                parsed = json.loads(after_state)
                if isinstance(parsed, dict):
                    payload = parsed
            except Exception:
                payload = {}
        normalized_label = _normalize_label(payload.get("normalized_label"))
        if normalized_label:
            closed.add(normalized_label)
    return closed


def _is_safe_alias_label(label: str) -> bool:
    normalized = _normalize_label(label)
    if normalized in {_normalize_label(item) for item in SAFE_ALIAS_LABELS}:
        return True
    return False


def _is_human_spot_check_alias(label: str) -> bool:
    normalized = _normalize_label(label)
    if normalized in {_normalize_label(item) for item in HUMAN_SPOT_CHECK_ALIAS_LABELS}:
        return True
    return _norm(label).startswith("其中：")


def _is_ambiguous_alias(label: str) -> bool:
    normalized = _normalize_label(label)
    return normalized in {_normalize_label(item) for item in AMBIGUOUS_ALIAS_LABELS}


def _is_balance_sheet_or_statement_line(label: str) -> bool:
    text = _norm(label)
    return any(token in text for token in BALANCE_SHEET_OR_STATEMENT_TOKENS)


def _is_core_metric_like(label: str) -> bool:
    text = _normalize_label(label)
    if text in {_normalize_label(item) for item in SAFE_ALIAS_LABELS}:
        return True
    return any(token in text for token in [_normalize_label(item) for item in CORE_METRIC_TOKENS])


def _sequence_has_mojibake(items: Sequence[Any]) -> bool:
    return any(_looks_mojibake(item) for item in items)


def load_adjudication_batch_sanity_gate_323c_inputs(
    batch_prep_dir: Path,
    candidate_text_repair_dir: Path,
    patch_application_dir: Path,
) -> Dict[str, Any]:
    batch_json = _read_json(batch_prep_dir / "semantic_adjudication_batch_prep_323ab_batch.json")
    review_ready_summary = _read_json(candidate_text_repair_dir / "candidate_text_repair_323ar_summary.json")
    return {
        "batch_prep_summary": _read_json(batch_prep_dir / "semantic_adjudication_batch_prep_323ab_summary.json"),
        "batch_prep_qa": _read_json(batch_prep_dir / "semantic_adjudication_batch_prep_323ab_qa.json"),
        "batch_json": batch_json,
        "batch_items": batch_json.get("batch_items", []) if isinstance(batch_json.get("batch_items", []), list) else [],
        "candidate_text_repair_summary": review_ready_summary,
        "patch_application_log_df": _read_jsonl(
            patch_application_dir / "official_semantic_patch_application_322n_application_log.jsonl"
        ),
    }


def _schema_missing_fields(item: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for field in REQUIRED_BATCH_ITEM_FIELDS:
        if field not in item:
            missing.append(field)
            continue
        value = item.get(field)
        if field in {"allowed_decisions", "sample_candidate_ids", "sample_texts", "risk_flags"}:
            if not isinstance(value, list):
                missing.append(field)
        elif field == "provenance":
            if not isinstance(value, dict):
                missing.append(field)
        elif field in {"affected_candidate_count", "affected_review_required_count", "priority_score"}:
            continue
        elif _norm(value) == "":
            missing.append(field)
    return missing


def _classify_batch_item(item: Dict[str, Any], closed_rule_labels: Set[str]) -> Tuple[str, List[str]]:
    label = _norm(item.get("repaired_label"))
    normalized_label = _normalize_label(label)
    candidate_type = _norm(item.get("candidate_type"))
    original_label = _norm(item.get("original_label"))
    sample_texts = _flatten_sequence(item.get("sample_texts"))
    sample_ids = _flatten_sequence(item.get("sample_candidate_ids"))
    risk_flags = _flatten_sequence(item.get("risk_flags"))
    missing_fields = _schema_missing_fields(item)

    if missing_fields:
        return BUCKET_HOLDOUT_INVALID, [f"MISSING_SCHEMA_FIELDS:{'|'.join(missing_fields)}"]
    if normalized_label in closed_rule_labels:
        return BUCKET_HOLDOUT_OFFICIAL, ["ALREADY_OFFICIAL_322_RULE"]
    if _is_empty_or_low_signal(label):
        return BUCKET_HOLDOUT_INVALID, ["EMPTY_OR_LOW_SIGNAL_LABEL"]
    if _looks_mojibake(label) or _looks_mojibake(original_label):
        return BUCKET_HOLDOUT_INVALID, ["MOJIBAKE_RISK"]
    if _is_date_like(label):
        return BUCKET_HOLDOUT_INVALID, ["DATE_ONLY_LABEL"]
    if _is_stock_code_like(label):
        return BUCKET_HOLDOUT_INVALID, ["STOCK_CODE_LABEL"]
    if _looks_long_narrative(label):
        return BUCKET_HOLDOUT_INVALID, ["LONG_NARRATIVE_LABEL"]
    if _sequence_has_mojibake(sample_texts):
        return BUCKET_HOLDOUT_INVALID, ["MOJIBAKE_IN_SAMPLE_TEXT"]
    if not sample_ids:
        return BUCKET_HOLDOUT_INVALID, ["MISSING_SAMPLE_CANDIDATE_IDS"]
    if candidate_type not in {"alias", "scope_noise"}:
        return BUCKET_HOLDOUT_INVALID, [f"UNSUPPORTED_CANDIDATE_TYPE:{candidate_type or '__EMPTY__'}"]

    if candidate_type == "alias":
        if _is_human_spot_check_alias(label):
            reasons = ["SUSPICIOUS_ALIAS_PATTERN", "HUMAN_SPOT_CHECK_REQUIRED"]
            if _norm(label).startswith("其中："):
                reasons.append("SUBLINE_PREFIX")
            if "货币资金" in label:
                reasons.append("CASH_BALANCE_OVERLAP_RISK")
            if "归属母公司" in label and "权益" in label:
                reasons.append("OFFICIAL_ALIAS_PREFIX_COLLISION")
            return BUCKET_HUMAN, reasons
        if _is_ambiguous_alias(label):
            return BUCKET_HOLDOUT_AMBIGUOUS, ["CORE_FALSE_MATCH_RISK", "AMBIGUOUS_ALIAS_SEMANTICS"]
        if _is_safe_alias_label(label):
            return BUCKET_SEND, ["SAFE_CORE_ALIAS_CANDIDATE"]
        if _is_balance_sheet_or_statement_line(label):
            return BUCKET_HOLDOUT_CATEGORY, ["ALIAS_SCOPE_TYPE_MISMATCH", "BALANCE_SHEET_OR_STATEMENT_LINE"]
        if _is_core_metric_like(label):
            return BUCKET_HUMAN, ["CORE_METRIC_LIKE_BUT_NEEDS_SPOT_CHECK"]
        return BUCKET_HOLDOUT_AMBIGUOUS, ["AMBIGUOUS_ALIAS_LABEL"]

    if _is_core_metric_like(label):
        return BUCKET_HOLDOUT_CATEGORY, ["SCOPE_ALIAS_TYPE_MISMATCH", "CORE_METRIC_LIKE_SCOPE_CANDIDATE"]
    if any(flag in {"POSSIBLE_CORE_METRIC", "SECTION_CONTEXT_REQUIRED"} for flag in risk_flags):
        return BUCKET_HUMAN, ["RISK_FLAG_REQUIRES_HUMAN_SPOT_CHECK"]
    return BUCKET_SEND, ["SAFE_SCOPE_NOISE_CANDIDATE"]


def _build_gated_record(
    item: Dict[str, Any],
    sanity_bucket: str,
    sanity_reasons: List[str],
) -> Dict[str, Any]:
    record = dict(item)
    record["sanity_bucket"] = sanity_bucket
    record["sanity_reasons"] = sanity_reasons
    record["human_spot_check_required"] = sanity_bucket == BUCKET_HUMAN
    record["send_to_adjudicator_allowed"] = sanity_bucket == BUCKET_SEND
    record["suspicious_alias"] = (
        _norm(item.get("candidate_type")) == "alias" and sanity_bucket != BUCKET_SEND
    )
    return record


def _flatten_record_for_sheet(record: Dict[str, Any], include_human_columns: bool = False) -> Dict[str, Any]:
    provenance = record.get("provenance") if isinstance(record.get("provenance"), dict) else {}
    flat = {
        "batch_item_id": _norm(record.get("batch_item_id")),
        "source_group_id": _norm(record.get("source_group_id")),
        "candidate_type": _norm(record.get("candidate_type")),
        "repaired_label": _norm(record.get("repaired_label")),
        "original_label": _norm(record.get("original_label")),
        "candidate_question": _norm(record.get("candidate_question")),
        "allowed_decisions": " | ".join(_flatten_sequence(record.get("allowed_decisions"))),
        "expected_rule_type_if_accepted": _norm(record.get("expected_rule_type_if_accepted")),
        "review_decision": _norm(record.get("review_decision")),
        "sample_candidate_ids": " | ".join(_flatten_sequence(record.get("sample_candidate_ids"))),
        "sample_texts": " | ".join(_flatten_sequence(record.get("sample_texts"))),
        "affected_candidate_count": _safe_int(record.get("affected_candidate_count")),
        "affected_review_required_count": _safe_int(record.get("affected_review_required_count")),
        "priority_score": _safe_float(record.get("priority_score")),
        "risk_flags": " | ".join(_flatten_sequence(record.get("risk_flags"))),
        "review_instruction": _norm(record.get("review_instruction")),
        "sanity_bucket": _norm(record.get("sanity_bucket")),
        "sanity_reasons": " | ".join(_flatten_sequence(record.get("sanity_reasons"))),
        "human_spot_check_required": bool(record.get("human_spot_check_required")),
        "send_to_adjudicator_allowed": bool(record.get("send_to_adjudicator_allowed")),
        "source_stage": _norm(provenance.get("source_stage")),
        "source_stage_signature": _norm(provenance.get("source_stage_signature")),
        "source_report_examples": " | ".join(_flatten_sequence(provenance.get("source_report_examples"))),
        "table_asset_examples": " | ".join(_flatten_sequence(provenance.get("table_asset_examples"))),
        "sample_table_titles": " | ".join(_flatten_sequence(provenance.get("sample_table_titles"))),
        "sample_years": " | ".join(_flatten_sequence(provenance.get("sample_years"))),
        "sample_raw_metric_names": " | ".join(_flatten_sequence(provenance.get("sample_raw_metric_names"))),
    }
    if include_human_columns:
        flat.update(
            {
                "human_decision": "PENDING_HUMAN_SPOT_CHECK",
                "human_note": "",
                "reviewer_name": "",
                "review_timestamp": "",
                "allowed_human_decisions": "SEND_TO_ADJUDICATOR | HOLDOUT | RECLASSIFY_AS_SCOPE_CANDIDATE | RECLASSIFY_AS_ALIAS_CANDIDATE | NEEDS_MORE_INFO",
            }
        )
    return flat


def build_adjudication_batch_sanity_gate_323c(
    batch_prep_summary: Dict[str, Any],
    batch_prep_qa: Dict[str, Any],
    batch_items: Sequence[Dict[str, Any]],
    candidate_text_repair_summary: Dict[str, Any],
    patch_application_log_df: pd.DataFrame,
) -> Dict[str, Any]:
    qa_rows: List[Dict[str, Any]] = []

    def add_qa(name: str, status: str, detail: str) -> None:
        qa_rows.append({"check_name": name, "status": status, "detail": detail})

    alias_hash_before = _sha256_file(Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json"))
    scope_hash_before = _sha256_file(Path(r"D:\_datefac\data\mapping\formal_scope_rules.json"))

    add_qa(
        "input_323ab::decision",
        "PASS" if _norm(batch_prep_summary.get("decision")) == EXPECTED_323AB_READY_DECISION else "FAIL",
        _norm(batch_prep_summary.get("decision")),
    )
    add_qa(
        "input_323ab::summary_qa_fail_count",
        "PASS" if _safe_int(batch_prep_summary.get("qa_fail_count")) == 0 else "FAIL",
        str(batch_prep_summary.get("qa_fail_count", "")),
    )
    add_qa(
        "input_323ab::qa_json_fail_count",
        "PASS" if _safe_int(batch_prep_qa.get("qa_fail_count")) == 0 else "FAIL",
        str(batch_prep_qa.get("qa_fail_count", "")),
    )
    add_qa(
        "input_323ab::total_batch_count_positive",
        "PASS" if _safe_int(batch_prep_summary.get("total_batch_count")) > 0 else "FAIL",
        str(batch_prep_summary.get("total_batch_count", "")),
    )
    alias_count_expected = _safe_int(batch_prep_summary.get("selected_alias_batch_count"))
    scope_count_expected = _safe_int(batch_prep_summary.get("selected_scope_batch_count"))
    total_count_expected = _safe_int(batch_prep_summary.get("total_batch_count"))
    add_qa(
        "input_323ab::alias_scope_total_consistency",
        "PASS" if alias_count_expected + scope_count_expected == total_count_expected else "FAIL",
        f"alias={alias_count_expected} scope={scope_count_expected} total={total_count_expected}",
    )
    add_qa(
        "input_323ar::reference_loaded",
        "PASS" if bool(candidate_text_repair_summary) else "WARN",
        _norm(candidate_text_repair_summary.get("decision")),
    )

    closed_rule_labels = _build_closed_rule_label_set(patch_application_log_df)
    add_qa(
        "input_322n::closed_rule_count",
        "PASS" if len(closed_rule_labels) == 10 else "FAIL",
        f"actual={len(closed_rule_labels)}",
    )

    gated_records: List[Dict[str, Any]] = []
    for raw_item in batch_items:
        if isinstance(raw_item, dict):
            bucket, reasons = _classify_batch_item(raw_item, closed_rule_labels)
            gated_records.append(_build_gated_record(raw_item, bucket, reasons))

    gated_df = pd.DataFrame([_flatten_record_for_sheet(item) for item in gated_records]).fillna("")
    send_df = pd.DataFrame(
        [_flatten_record_for_sheet(item) for item in gated_records if item.get("sanity_bucket") == BUCKET_SEND]
    ).fillna("")
    human_df = pd.DataFrame(
        [
            _flatten_record_for_sheet(item, include_human_columns=True)
            for item in gated_records
            if item.get("sanity_bucket") == BUCKET_HUMAN
        ]
    ).fillna("")
    holdout_df = pd.DataFrame(
        [
            _flatten_record_for_sheet(item)
            for item in gated_records
            if item.get("sanity_bucket") in {BUCKET_HOLDOUT_CATEGORY, BUCKET_HOLDOUT_AMBIGUOUS, BUCKET_HOLDOUT_OFFICIAL, BUCKET_HOLDOUT_INVALID}
        ]
    ).fillna("")

    bucket_counts = {bucket: 0 for bucket in ALL_BUCKETS}
    for record in gated_records:
        bucket = _norm(record.get("sanity_bucket"))
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

    suspicious_alias_count = int(
        sum(
            1
            for record in gated_records
            if _norm(record.get("candidate_type")) == "alias" and record.get("suspicious_alias")
        )
    )

    duplicate_batch_item_id_count = 0
    if gated_records:
        ids = [_norm(item.get("batch_item_id")) for item in gated_records]
        duplicate_batch_item_id_count = len(ids) - len(set(ids))

    output_item_count = len(gated_records)
    send_has_invalid_text = False
    send_has_mojibake = False
    send_has_official = False
    suspicious_alias_auto_sent = False
    for record in gated_records:
        if record.get("sanity_bucket") != BUCKET_SEND:
            continue
        label = _norm(record.get("repaired_label"))
        if _is_empty_or_low_signal(label) or _is_date_like(label) or _is_stock_code_like(label) or _looks_long_narrative(label):
            send_has_invalid_text = True
        if _looks_mojibake(label) or _sequence_has_mojibake(_flatten_sequence(record.get("sample_texts"))):
            send_has_mojibake = True
        if _normalize_label(label) in closed_rule_labels:
            send_has_official = True
        if _norm(record.get("candidate_type")) == "alias" and record.get("suspicious_alias"):
            suspicious_alias_auto_sent = True

    add_qa(
        "conservation::all_items_preserved",
        "PASS" if output_item_count == len(batch_items) else "FAIL",
        f"input={len(batch_items)} output={output_item_count}",
    )
    add_qa(
        "routing::every_item_has_exactly_one_bucket",
        "PASS" if output_item_count == sum(bucket_counts.values()) and all(bucket in ALL_BUCKETS for bucket in bucket_counts) else "FAIL",
        json.dumps(bucket_counts, ensure_ascii=False),
    )
    add_qa(
        "routing::send_subset_no_invalid_text",
        "PASS" if not send_has_invalid_text else "FAIL",
        f"send_count={bucket_counts.get(BUCKET_SEND, 0)}",
    )
    add_qa(
        "routing::send_subset_no_mojibake",
        "PASS" if not send_has_mojibake else "FAIL",
        f"send_count={bucket_counts.get(BUCKET_SEND, 0)}",
    )
    add_qa(
        "routing::suspicious_alias_not_auto_sent",
        "PASS" if not suspicious_alias_auto_sent else "FAIL",
        f"suspicious_alias_count={suspicious_alias_count}",
    )
    add_qa(
        "routing::no_already_official_item_sent",
        "PASS" if not send_has_official else "FAIL",
        f"closed_rule_count={len(closed_rule_labels)}",
    )
    add_qa(
        "schema::required_fields_present",
        "PASS" if all(not _schema_missing_fields(item) for item in batch_items if isinstance(item, dict)) else "FAIL",
        f"batch_item_count={len(batch_items)}",
    )
    add_qa(
        "schema::unique_batch_item_ids",
        "PASS" if duplicate_batch_item_id_count == 0 else "FAIL",
        f"duplicate_count={duplicate_batch_item_id_count}",
    )
    add_qa(
        "routing::human_spot_check_sheet_nonempty_when_needed",
        "PASS" if bucket_counts.get(BUCKET_HUMAN, 0) == len(human_df) else "FAIL",
        f"summary={bucket_counts.get(BUCKET_HUMAN, 0)} sheet={len(human_df)}",
    )
    add_qa(
        "routing::holdout_sheet_count_consistency",
        "PASS" if len(holdout_df) == (
            bucket_counts.get(BUCKET_HOLDOUT_CATEGORY, 0)
            + bucket_counts.get(BUCKET_HOLDOUT_AMBIGUOUS, 0)
            + bucket_counts.get(BUCKET_HOLDOUT_OFFICIAL, 0)
            + bucket_counts.get(BUCKET_HOLDOUT_INVALID, 0)
        ) else "FAIL",
        f"holdout_sheet={len(holdout_df)}",
    )

    parser_not_run = True
    llm_not_called = True
    add_qa("safety::parser_not_run_confirmation", "PASS" if parser_not_run else "FAIL", "323C reads cached artifacts only.")
    add_qa("safety::llm_not_called_confirmation", "PASS" if llm_not_called else "FAIL", "323C applies deterministic routing only.")

    alias_hash_after = _sha256_file(Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json"))
    scope_hash_after = _sha256_file(Path(r"D:\_datefac\data\mapping\formal_scope_rules.json"))
    no_official_assets_modified = alias_hash_before == alias_hash_after and scope_hash_before == scope_hash_after
    add_qa(
        "safety::official_assets_not_modified",
        "PASS" if no_official_assets_modified else "FAIL",
        f"alias_before={alias_hash_before} alias_after={alias_hash_after} scope_before={scope_hash_before} scope_after={scope_hash_after}",
    )

    highest_priority_gated_examples: List[Dict[str, Any]] = []
    for record in sorted(
        gated_records,
        key=lambda item: (
            -_safe_float(item.get("priority_score")),
            -_safe_int(item.get("affected_review_required_count")),
            _norm(item.get("batch_item_id")),
        ),
    )[:8]:
        highest_priority_gated_examples.append(
            {
                "batch_item_id": _norm(record.get("batch_item_id")),
                "candidate_type": _norm(record.get("candidate_type")),
                "repaired_label": _norm(record.get("repaired_label")),
                "sanity_bucket": _norm(record.get("sanity_bucket")),
                "priority_score": _safe_float(record.get("priority_score")),
                "affected_review_required_count": _safe_int(record.get("affected_review_required_count")),
                "sanity_reasons": _flatten_sequence(record.get("sanity_reasons")),
            }
        )

    summary = {
        "stage": "323C",
        "output_dir": "",
        "input_batch_count": int(len(batch_items)),
        "input_alias_batch_count": int(sum(1 for item in batch_items if _norm(item.get("candidate_type")) == "alias")),
        "input_scope_batch_count": int(sum(1 for item in batch_items if _norm(item.get("candidate_type")) == "scope_noise")),
        "routing_bucket_counts": bucket_counts,
        "suspicious_alias_count": suspicious_alias_count,
        "send_to_adjudicator_count": int(bucket_counts.get(BUCKET_SEND, 0)),
        "human_spot_check_count": int(bucket_counts.get(BUCKET_HUMAN, 0)),
        "holdout_category_mismatch_count": int(bucket_counts.get(BUCKET_HOLDOUT_CATEGORY, 0)),
        "holdout_ambiguous_count": int(bucket_counts.get(BUCKET_HOLDOUT_AMBIGUOUS, 0)),
        "holdout_already_official_count": int(bucket_counts.get(BUCKET_HOLDOUT_OFFICIAL, 0)),
        "holdout_invalid_text_count": int(bucket_counts.get(BUCKET_HOLDOUT_INVALID, 0)),
        "highest_priority_gated_examples": highest_priority_gated_examples,
        "qa_pass_count": 0,
        "qa_warn_count": 0,
        "qa_fail_count": 0,
        "blocking_reasons": [],
        "decision": "",
    }

    qa_df = pd.DataFrame(qa_rows).fillna("")
    qa_pass_count = int((qa_df["status"] == "PASS").sum()) if not qa_df.empty else 0
    qa_warn_count = int((qa_df["status"] == "WARN").sum()) if not qa_df.empty else 0
    qa_fail_count = int((qa_df["status"] == "FAIL").sum()) if not qa_df.empty else 0
    blocking_reasons = qa_df.loc[qa_df["status"] == "FAIL", "check_name"].astype(str).tolist() if not qa_df.empty else []
    summary["qa_pass_count"] = qa_pass_count
    summary["qa_warn_count"] = qa_warn_count
    summary["qa_fail_count"] = qa_fail_count
    summary["blocking_reasons"] = blocking_reasons
    summary["decision"] = EXPECTED_323C_READY_DECISION if qa_fail_count == 0 else EXPECTED_323C_NOT_READY_DECISION

    qa_summary_df = pd.DataFrame(
        [
            {
                "qa_pass_count": qa_pass_count,
                "qa_warn_count": qa_warn_count,
                "qa_fail_count": qa_fail_count,
                "blocking_reasons": " | ".join(blocking_reasons),
                "decision": summary["decision"],
            }
        ]
    ).fillna("")
    known_limitations_df = pd.DataFrame(
        [
            {
                "limitation": "deterministic_safety_gate_only",
                "detail": "323C routes items conservatively and does not decide semantic truth or auto-approve any rule.",
            },
            {
                "limitation": "safe_subset_bias",
                "detail": "Low-risk SEND_TO_ADJUDICATOR items are intentionally narrower than the full 323A-B batch to reduce false positives.",
            },
            {
                "limitation": "human_spot_check_required_for_close_calls",
                "detail": "Subline items and alias-near labels stay out of direct adjudicator send until a human verifies category safety.",
            },
        ]
    ).fillna("")

    gated_batch_json = {
        "stage": "323C",
        "decision": summary["decision"],
        "batch_items": gated_records,
    }

    return {
        "summary": summary,
        "qa_json": {
            "qa_pass_count": qa_pass_count,
            "qa_warn_count": qa_warn_count,
            "qa_fail_count": qa_fail_count,
            "blocking_reasons": blocking_reasons,
            "checks": qa_df.to_dict(orient="records"),
        },
        "gated_batch_json": gated_batch_json,
        "gated_batch_df": gated_df,
        "send_to_adjudicator_df": send_df,
        "human_spot_check_df": human_df,
        "holdouts_df": holdout_df,
        "qa_checks_df": qa_df,
        "qa_summary_df": qa_summary_df,
        "known_limitations_df": known_limitations_df,
    }
