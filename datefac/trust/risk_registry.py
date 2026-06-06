from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping


SEVERITY_BLOCKING = "BLOCKING"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"


@dataclass(frozen=True)
class RiskDefinition:
    risk_code: str
    severity: str
    blocking: bool
    description: str
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _build_registry() -> Dict[str, RiskDefinition]:
    rows = [
        RiskDefinition(
            risk_code="UNIT_UNKNOWN",
            severity=SEVERITY_WARNING,
            blocking=False,
            description="Unit is missing or unresolved from current evidence.",
            recommended_action="Review unit context and confirm with source rows before trusting.",
        ),
        RiskDefinition(
            risk_code="UNIT_CONFLICT",
            severity=SEVERITY_BLOCKING,
            blocking=True,
            description="Conflicting unit signals were detected across sources.",
            recommended_action="Reject trust promotion until the unit conflict is resolved deterministically.",
        ),
        RiskDefinition(
            risk_code="YEAR_MISSING",
            severity=SEVERITY_WARNING,
            blocking=False,
            description="Candidate record has no resolved year.",
            recommended_action="Request review or more context before trusting year-sensitive metrics.",
        ),
        RiskDefinition(
            risk_code="YEAR_MISMATCH",
            severity=SEVERITY_BLOCKING,
            blocking=True,
            description="Year signals disagree across evidence or parser sources.",
            recommended_action="Send for review and resolve the year mismatch before downstream use.",
        ),
        RiskDefinition(
            risk_code="VALUE_PARSE_FAILED",
            severity=SEVERITY_BLOCKING,
            blocking=True,
            description="Value parsing failed and the numeric payload is not reliable.",
            recommended_action="Reject or re-extract the candidate until the value parses cleanly.",
        ),
        RiskDefinition(
            risk_code="PARSER_CONFLICT",
            severity=SEVERITY_BLOCKING,
            blocking=True,
            description="Multiple parsers disagree on the extracted candidate payload.",
            recommended_action="Route to review and resolve parser disagreement before trusting.",
        ),
        RiskDefinition(
            risk_code="LOW_EVIDENCE_STRENGTH",
            severity=SEVERITY_WARNING,
            blocking=False,
            description="Evidence volume or support quality is weak for this candidate.",
            recommended_action="Prefer manual review or collect stronger supporting evidence.",
        ),
        RiskDefinition(
            risk_code="LABEL_AMBIGUOUS",
            severity=SEVERITY_WARNING,
            blocking=False,
            description="The metric label is ambiguous and may map to multiple concepts.",
            recommended_action="Require human review before any trust promotion or rule authoring.",
        ),
        RiskDefinition(
            risk_code="TARGET_METRIC_AMBIGUOUS",
            severity=SEVERITY_BLOCKING,
            blocking=True,
            description="The likely target metric is ambiguous across available evidence.",
            recommended_action="Reject auto-trust and resolve the target mapping explicitly.",
        ),
        RiskDefinition(
            risk_code="SCOPE_NOISE_RISK",
            severity=SEVERITY_WARNING,
            blocking=False,
            description="Candidate text may contain disclosure or scope-noise phrasing.",
            recommended_action="Route to review and verify the candidate is genuinely in scope.",
        ),
        RiskDefinition(
            risk_code="ALIAS_MAPPING_RISK",
            severity=SEVERITY_WARNING,
            blocking=False,
            description="Alias mapping exists but still carries semantic ambiguity risk.",
            recommended_action="Keep under review until deterministic evidence is strong enough.",
        ),
        RiskDefinition(
            risk_code="ADJUSTED_METRIC_RISK",
            severity=SEVERITY_WARNING,
            blocking=False,
            description="Adjusted metric labels are definition-sensitive and easy to over-map.",
            recommended_action="Require semantic review and definition confirmation before trusting.",
        ),
        RiskDefinition(
            risk_code="DILUTED_EPS_RISK",
            severity=SEVERITY_WARNING,
            blocking=False,
            description="Diluted EPS style labels are sensitive to exact share basis.",
            recommended_action="Confirm the diluted EPS definition before accepting the candidate.",
        ),
        RiskDefinition(
            risk_code="LONG_NARRATIVE_LABEL",
            severity=SEVERITY_INFO,
            blocking=False,
            description="Candidate label is unusually long and may include narrative noise.",
            recommended_action="Trim or review label context before downstream standardization.",
        ),
        RiskDefinition(
            risk_code="TABLE_STRUCTURE_UNSTABLE",
            severity=SEVERITY_WARNING,
            blocking=False,
            description="Table segmentation or layout signals are unstable for this record.",
            recommended_action="Review structure diagnostics before elevating confidence.",
        ),
        RiskDefinition(
            risk_code="OFFICIAL_RULE_CONFLICT",
            severity=SEVERITY_BLOCKING,
            blocking=True,
            description="Candidate conflicts with an existing official alias or scope rule.",
            recommended_action="Reject auto-trust and resolve the official-rule conflict first.",
        ),
        RiskDefinition(
            risk_code="HISTORICAL_DUPLICATE_WARNING",
            severity=SEVERITY_INFO,
            blocking=False,
            description="Historical duplicate artifacts are known in adjacent data or assets.",
            recommended_action="Record as warning-only unless a new duplicate is introduced.",
        ),
        RiskDefinition(
            risk_code="MOJIBAKE_ENCODING_ARTIFACT",
            severity=SEVERITY_INFO,
            blocking=False,
            description="Encoding artifacts are present in nearby labels or reference assets.",
            recommended_action="Preserve provenance and review human-readable text before trusting.",
        ),
    ]
    return {row.risk_code: row for row in rows}


RISK_REGISTRY: Dict[str, RiskDefinition] = _build_registry()


def get_risk_definition(risk_code: str) -> RiskDefinition:
    key = str(risk_code or "").strip().upper()
    if key not in RISK_REGISTRY:
        raise KeyError(f"Unknown risk code: {risk_code}")
    return RISK_REGISTRY[key]


def normalize_risk_flags(risk_flags: Iterable[Any]) -> List[str]:
    normalized: List[str] = []
    seen = set()
    for item in risk_flags or []:
        key = str(item or "").strip().upper()
        if not key:
            continue
        definition = get_risk_definition(key)
        if definition.risk_code not in seen:
            normalized.append(definition.risk_code)
            seen.add(definition.risk_code)
    return normalized


def derive_risk_buckets(risk_flags: Iterable[Any]) -> Dict[str, List[str]]:
    normalized = normalize_risk_flags(risk_flags)
    blocking = [code for code in normalized if get_risk_definition(code).blocking]
    warning = [
        code
        for code in normalized
        if not get_risk_definition(code).blocking
        and get_risk_definition(code).severity in {SEVERITY_WARNING, SEVERITY_INFO}
    ]
    return {
        "risk_flags": normalized,
        "blocking_risks": blocking,
        "warning_risks": warning,
    }


def risk_registry_rows() -> List[Dict[str, Any]]:
    return [row.to_dict() for row in RISK_REGISTRY.values()]


def risk_registry_map() -> Dict[str, Dict[str, Any]]:
    return {key: value.to_dict() for key, value in RISK_REGISTRY.items()}


def coerce_risk_registry_summary(extra_fields: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "risk_registry_count": len(RISK_REGISTRY),
        "blocking_risk_count": sum(1 for row in RISK_REGISTRY.values() if row.blocking),
        "warning_or_info_risk_count": sum(1 for row in RISK_REGISTRY.values() if not row.blocking),
    }
    if extra_fields:
        payload.update(dict(extra_fields))
    return payload
