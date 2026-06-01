from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


VLM_PRIMARY = "VLM_PRIMARY"
MINERU_MARKDOWN_DIRECT = "MINERU_MARKDOWN_DIRECT"
PPSTRUCTURE_FALLBACK = "PPSTRUCTURE_FALLBACK"
MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
SKIP_NON_CORE_TABLE = "SKIP_NON_CORE_TABLE"
UNSUPPORTED_TABLE_TYPE = "UNSUPPORTED_TABLE_TYPE"

ROUTE_ORDER = [
    VLM_PRIMARY,
    MINERU_MARKDOWN_DIRECT,
    PPSTRUCTURE_FALLBACK,
    MANUAL_REVIEW_REQUIRED,
    SKIP_NON_CORE_TABLE,
    UNSUPPORTED_TABLE_TYPE,
]

CORE_ROLE_SET = {
    "BALANCE_SHEET",
    "INCOME_STATEMENT",
    "CASH_FLOW_STATEMENT",
    "CORE_METRIC_TABLE",
    "FINANCIAL_FORECAST_VALUATION",
}
NON_CORE_ROLE_SET = {
    "RATING_STANDARD",
    "DISCLAIMER_OR_LEGAL",
    "CHART_OR_MARKET_TREND",
}
SIMPLE_ROLE_SET = {
    "BASIC_DATA",
}

CORE_KEYWORDS = [
    "资产负债表",
    "利润表",
    "损益表",
    "现金流量表",
    "关键财务",
    "估值",
    "盈利预测",
    "财务预测",
    "财务指标",
    "盈利能力",
    "营业收入",
    "归母净利润",
    "净利润",
    "毛利率",
    "ROE",
    "EPS",
    "PE",
    "PB",
    "EV/EBITDA",
]
SIMPLE_MARKDOWN_KEYWORDS = [
    "基础数据",
    "市场数据",
    "股价",
    "收盘价",
    "每股净资产",
]
SKIP_KEYWORDS = [
    "评级",
    "评级标准",
    "免责声明",
    "法律声明",
    "作者",
    "分析师",
    "联系人",
    "执业证书",
]
UNSUPPORTED_KEYWORDS = [
    "分部",
    "拆分",
    "分项",
    "结构图",
    "区域",
    "分业务",
    "分产品",
    "分渠道",
    "按地区",
    "按业务",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _norm(value).lower() in {"1", "true", "yes", "y"}


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    try:
        return int(float(str(value).strip()))
    except Exception:
        return None


def _contains_any(text: str, keywords: List[str]) -> bool:
    haystack = _norm(text).lower()
    if not haystack:
        return False
    return any(keyword.lower() in haystack for keyword in keywords)


def infer_value_score(row: Dict[str, Any]) -> int:
    score = 0
    role = _norm(row.get("effective_role_category") or row.get("role_category") or row.get("table_role_guess"))
    title = _norm(row.get("table_title") or row.get("caption"))
    nearby = _norm(row.get("nearby_text_preview") or row.get("nearby_text"))
    issue_tags = _norm(row.get("vlm_issue_tags"))

    if role in {"BALANCE_SHEET", "INCOME_STATEMENT", "CASH_FLOW_STATEMENT"}:
        score += 95
    elif role in {"CORE_METRIC_TABLE", "FINANCIAL_FORECAST_VALUATION"}:
        score += 82
    elif role == "BASIC_DATA":
        score += 42
    elif role in NON_CORE_ROLE_SET:
        score += 5
    else:
        score += 20

    if _contains_any(title, CORE_KEYWORDS):
        score += 30
    if _contains_any(nearby, CORE_KEYWORDS):
        score += 15
    if _contains_any(issue_tags, ["SCHEMA_REVIEW_REQUIRED", "TABLE_NOT_READY_321A"]):
        score -= 5
    if _contains_any(title, SKIP_KEYWORDS) or _contains_any(nearby, SKIP_KEYWORDS):
        score -= 25

    return max(0, min(score, 100))


def infer_cost_class(route: str) -> str:
    if route == VLM_PRIMARY:
        return "HIGH"
    if route == PPSTRUCTURE_FALLBACK:
        return "MEDIUM"
    if route == MINERU_MARKDOWN_DIRECT:
        return "LOW"
    if route == MANUAL_REVIEW_REQUIRED:
        return "MANUAL"
    return "LOW"


def infer_confidence_score(row: Dict[str, Any]) -> float:
    score = 0.35
    if _to_bool(row.get("image_exists")):
        score += 0.1
    if _to_bool(row.get("vlm_output_available")):
        score += 0.15
    if _norm(row.get("vlm_quality_decision")) == "VLM_TABLE_READY_FOR_MAPPING":
        score += 0.2
    if _norm(row.get("vlm_qa_status")) == "PASS":
        score += 0.1
    if (_to_int(row.get("vlm_trusted_count")) or 0) > 0:
        score += 0.1
    if (_to_int(row.get("ppstructure_trusted_count")) or 0) > 0:
        score += 0.08
    if (_to_int(row.get("vlm_conflict_count")) or 0) > 20:
        score -= 0.08
    if (_to_int(row.get("vlm_unit_unknown_count")) or 0) > 0:
        score -= 0.05
    if _norm(row.get("schema_shape")) in {"A", "B"}:
        score -= 0.06
    return max(0.0, min(score, 1.0))


def infer_effective_role(row: Dict[str, Any]) -> str:
    role = _norm(row.get("role_category") or row.get("table_role_guess"))
    table_title = _norm(row.get("table_title"))
    caption = _norm(row.get("caption"))
    nearby = _norm(row.get("nearby_text_preview") or row.get("nearby_text"))
    table_type = _norm(row.get("table_type"))
    joined = " ".join([table_title, caption, nearby, table_type])

    if _contains_any(joined, ["资产负债表"]):
        return "BALANCE_SHEET"
    if _contains_any(joined, ["利润表", "损益表"]):
        return "INCOME_STATEMENT"
    if _contains_any(joined, ["现金流量表"]):
        return "CASH_FLOW_STATEMENT"
    if _contains_any(joined, ["关键财务", "估值", "盈利预测", "财务预测", "EPS", "ROE", "PE", "PB", "EV/EBITDA"]):
        return "FINANCIAL_FORECAST_VALUATION"
    if role:
        return role
    return "UNKNOWN_TABLE"


def is_non_core_table(row: Dict[str, Any]) -> bool:
    role = _norm(row.get("effective_role_category") or row.get("role_category") or row.get("table_role_guess"))
    title = _norm(row.get("table_title") or row.get("caption"))
    nearby = _norm(row.get("nearby_text_preview") or row.get("nearby_text"))
    if role in NON_CORE_ROLE_SET:
        return True
    return _contains_any(title, SKIP_KEYWORDS) or _contains_any(nearby, SKIP_KEYWORDS)


def is_unsupported_table(row: Dict[str, Any]) -> bool:
    table_title = _norm(row.get("table_title"))
    caption = _norm(row.get("caption"))
    table_type = _norm(row.get("table_type"))
    main_issue = _norm(row.get("vlm_main_issue"))
    current_decision = _norm(row.get("vlm_current_decision"))
    schema_shape = _norm(row.get("schema_shape"))
    issue_tags = _norm(row.get("vlm_issue_tags"))
    joined = " ".join([table_title, caption, table_type, main_issue, current_decision, issue_tags])

    if current_decision == "VLM_TABLE_SCHEMA_INVALID":
        return True
    if schema_shape in {"A", "B"} and _contains_any(joined, ["分部", "业务", "区域", "渠道", "产品"]):
        return True
    return _contains_any(joined, UNSUPPORTED_KEYWORDS)


def looks_simple_markdown_table(row: Dict[str, Any]) -> bool:
    role = _norm(row.get("effective_role_category") or row.get("role_category") or row.get("table_role_guess"))
    title = _norm(row.get("table_title") or row.get("caption"))
    nearby = _norm(row.get("nearby_text_preview") or row.get("nearby_text"))
    if role in SIMPLE_ROLE_SET:
        return True
    return _contains_any(title, SIMPLE_MARKDOWN_KEYWORDS) or _contains_any(nearby, SIMPLE_MARKDOWN_KEYWORDS)


@dataclass
class RouteDecision:
    recommended_route: str
    route_reason: str
    blocker_reason: str
    estimated_value_score: int
    estimated_cost_class: str
    confidence_score: float
    effective_role_category: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommended_route": self.recommended_route,
            "route_reason": self.route_reason,
            "blocker_reason": self.blocker_reason,
            "estimated_value_score": self.estimated_value_score,
            "estimated_cost_class": self.estimated_cost_class,
            "confidence_score": self.confidence_score,
            "effective_role_category": self.effective_role_category,
        }


def decide_route(row: Dict[str, Any]) -> RouteDecision:
    effective_role = infer_effective_role(row)
    row = dict(row)
    row["effective_role_category"] = effective_role
    value_score = infer_value_score(row)
    confidence_score = infer_confidence_score(row)
    image_exists = _to_bool(row.get("image_exists"))
    vlm_output_available = _to_bool(row.get("vlm_output_available"))
    ppstructure_output_available = _to_bool(row.get("ppstructure_output_available"))
    vlm_quality_decision = _norm(row.get("vlm_quality_decision"))
    vlm_qa_status = _norm(row.get("vlm_qa_status"))
    vlm_trusted = _to_int(row.get("vlm_trusted_count")) or 0
    pp_trusted = _to_int(row.get("ppstructure_trusted_count")) or 0
    reasons: List[str] = []
    blocker_reason = ""

    if not image_exists:
        reasons.append("image_missing")
        blocker_reason = "IMAGE_PATH_MISSING"
        route = MANUAL_REVIEW_REQUIRED if value_score >= 70 else SKIP_NON_CORE_TABLE
        return RouteDecision(
            recommended_route=route,
            route_reason="|".join(reasons),
            blocker_reason=blocker_reason,
            estimated_value_score=value_score,
            estimated_cost_class=infer_cost_class(route),
            confidence_score=confidence_score,
            effective_role_category=effective_role,
        )

    if is_non_core_table(row):
        reasons.append("non_core_table")
        route = SKIP_NON_CORE_TABLE
        return RouteDecision(
            recommended_route=route,
            route_reason="|".join(reasons),
            blocker_reason="",
            estimated_value_score=value_score,
            estimated_cost_class=infer_cost_class(route),
            confidence_score=confidence_score,
            effective_role_category=effective_role,
        )

    if is_unsupported_table(row):
        reasons.append("unsupported_schema_or_segment")
        if value_score >= 70:
            blocker_reason = "SCHEMA_SUPPORT_NEEDED"
        route = UNSUPPORTED_TABLE_TYPE
        return RouteDecision(
            recommended_route=route,
            route_reason="|".join(reasons),
            blocker_reason=blocker_reason,
            estimated_value_score=value_score,
            estimated_cost_class=infer_cost_class(route),
            confidence_score=confidence_score,
            effective_role_category=effective_role,
        )

    if effective_role in CORE_ROLE_SET or value_score >= 75:
        reasons.append("core_or_high_value_table")
        if vlm_output_available and vlm_quality_decision == "VLM_TABLE_READY_FOR_MAPPING" and vlm_qa_status in {"", "PASS"}:
            reasons.append("vlm_quality_gate_passed")
            if vlm_trusted > 0:
                reasons.append("vlm_trusted_output_available")
            route = VLM_PRIMARY
        elif vlm_output_available and vlm_quality_decision and vlm_quality_decision != "VLM_TABLE_READY_FOR_MAPPING":
            reasons.append("vlm_output_present_but_quality_not_ready")
            route = MANUAL_REVIEW_REQUIRED
            blocker_reason = vlm_quality_decision
        else:
            reasons.append("manual_vlm_recommended_for_high_value_table")
            route = VLM_PRIMARY
        return RouteDecision(
            recommended_route=route,
            route_reason="|".join(reasons),
            blocker_reason=blocker_reason,
            estimated_value_score=value_score,
            estimated_cost_class=infer_cost_class(route),
            confidence_score=confidence_score,
            effective_role_category=effective_role,
        )

    if looks_simple_markdown_table(row):
        reasons.append("simple_table_markdown_sufficient")
        route = MINERU_MARKDOWN_DIRECT
        return RouteDecision(
            recommended_route=route,
            route_reason="|".join(reasons),
            blocker_reason="",
            estimated_value_score=value_score,
            estimated_cost_class=infer_cost_class(route),
            confidence_score=confidence_score,
            effective_role_category=effective_role,
        )

    if ppstructure_output_available or pp_trusted > 0:
        reasons.append("ppstructure_fallback_available")
        if pp_trusted > 0:
            reasons.append("ppstructure_has_trusted_candidates")
        route = PPSTRUCTURE_FALLBACK
        return RouteDecision(
            recommended_route=route,
            route_reason="|".join(reasons),
            blocker_reason="",
            estimated_value_score=value_score,
            estimated_cost_class=infer_cost_class(route),
            confidence_score=confidence_score,
            effective_role_category=effective_role,
        )

    reasons.append("insufficient_recognizer_evidence")
    route = MANUAL_REVIEW_REQUIRED
    blocker_reason = "NO_RELIABLE_RECOGNIZER_OUTPUT"
    return RouteDecision(
        recommended_route=route,
        route_reason="|".join(reasons),
        blocker_reason=blocker_reason,
        estimated_value_score=value_score,
        estimated_cost_class=infer_cost_class(route),
        confidence_score=confidence_score,
        effective_role_category=effective_role,
    )


def build_policy_rows() -> List[Dict[str, Any]]:
    return [
        {
            "route": VLM_PRIMARY,
            "cost_class": "HIGH",
            "applies_to": "core financial statements, valuation, forecast, high-value metric tables",
            "conditions": "image exists and table is core/high-value; prefer even more when 321B VLM quality is ready",
            "notes": "manual/offline VLM workflow until stable API exists",
        },
        {
            "route": MINERU_MARKDOWN_DIRECT,
            "cost_class": "LOW",
            "applies_to": "simple tables such as 基础数据/市场数据",
            "conditions": "markdown text is likely enough and no visual reconstruction is needed",
            "notes": "keeps cost low for simple rows",
        },
        {
            "route": PPSTRUCTURE_FALLBACK,
            "cost_class": "MEDIUM",
            "applies_to": "lower-value tables with known row-text support",
            "conditions": "use when VLM unavailable and PPStructure evidence already exists",
            "notes": "fallback and diagnostic route only",
        },
        {
            "route": MANUAL_REVIEW_REQUIRED,
            "cost_class": "MANUAL",
            "applies_to": "valuable tables with low confidence or broken quality",
            "conditions": "schema invalid, quality not ready, or no reliable recognizer output",
            "notes": "hold before entering mapping",
        },
        {
            "route": SKIP_NON_CORE_TABLE,
            "cost_class": "LOW",
            "applies_to": "ratings, disclaimers, contacts, legal, small metadata",
            "conditions": "no target financial metric value expected",
            "notes": "do not spend recognizer budget",
        },
        {
            "route": UNSUPPORTED_TABLE_TYPE,
            "cost_class": "LOW",
            "applies_to": "segment/hierarchical/multi-panel unsupported schemas",
            "conditions": "needs schema expansion before trusted mapping",
            "notes": "keep explicit, do not silently trust",
        },
    ]


def build_quality_gate_rows() -> List[Dict[str, Any]]:
    return [
        {"gate": "321B VLM benchmark exists", "required_status": "PASS_OR_WARN", "reason": "router depends on VLM benchmark evidence"},
        {"gate": "VLM qa_fail_count == 0", "required_status": "PASS", "reason": "high-risk VLM output must not flow into mapping"},
        {"gate": "route_reason populated", "required_status": "PASS", "reason": "every decision must be reviewable"},
        {"gate": "VLM_PRIMARY only for image-existing tables", "required_status": "PASS", "reason": "manual/VLM route requires source crop"},
        {"gate": "unsupported tables explicit", "required_status": "PASS", "reason": "avoid silent trust on unsupported schemas"},
        {"gate": "manual manifest path outside repo output", "required_status": "PASS", "reason": "offline workflow must stay outside git-tracked outputs"},
        {"gate": "Chinese text preserved", "required_status": "PASS", "reason": "financial labels must remain UTF-8 readable"},
    ]


def build_known_limitations_rows() -> List[Dict[str, Any]]:
    return [
        {"limitation": "321C uses existing benchmark outputs only", "impact": "no fresh recognizer reruns in this stage"},
        {"limitation": "MinerU role classification can under-detect core tables", "impact": "router upgrades roles using VLM title/caption keywords where possible"},
        {"limitation": "VLM sample set is still small", "impact": "policy is directionally strong but still sandbox-only"},
        {"limitation": "unsupported hierarchical/segment schemas remain blocked", "impact": "needs later schema expansion before trusted mapping"},
    ]


def policy_json() -> Dict[str, Any]:
    return {
        "routes": ROUTE_ORDER,
        "core_roles": sorted(CORE_ROLE_SET),
        "non_core_roles": sorted(NON_CORE_ROLE_SET),
        "simple_markdown_roles": sorted(SIMPLE_ROLE_SET),
        "policy_rows": build_policy_rows(),
        "quality_gate_requirements": build_quality_gate_rows(),
        "known_limitations": build_known_limitations_rows(),
        "notes": "deterministic sandbox routing plan for 321C",
    }


def dumps_policy_json() -> str:
    return json.dumps(policy_json(), ensure_ascii=False, indent=2)
