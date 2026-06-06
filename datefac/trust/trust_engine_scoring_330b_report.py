from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "foundation_validation",
    "scoring_model",
    "scored_examples",
    "routing_smoke_tests",
    "cached_sidecar_samples",
    "official_asset_proof",
    "qa_summary",
    "qa_checks",
    "known_limitations",
]


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def _safe_sheet_name(name: str, used: Set[str]) -> str:
    base = (
        _norm(name)
        .replace("\\", "_")
        .replace("/", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace(":", "_")
        .replace("[", "_")
        .replace("]", "_")
    )[:31] or "Sheet"
    out = base
    index = 1
    while out in used:
        suffix = f"_{index}"
        out = f"{base[:31 - len(suffix)]}{suffix}"
        index += 1
    used.add(out)
    return out


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def write_excel(path: Path, sheets: Dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name in SHEET_ORDER:
            sheets.get(name, pd.DataFrame()).to_excel(
                writer,
                sheet_name=_safe_sheet_name(name, used),
                index=False,
            )


def trust_engine_scoring_330b_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Trust Engine Scoring 330B",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            "",
            "## Foundation Validation",
            f"- validated_330a_foundation: {summary.get('validated_330a_foundation', False)}",
            f"- risk_registry_count: {summary.get('risk_registry_count', 0)}",
            "",
            "## Scoring",
            f"- scoring_model_component_count: {summary.get('scoring_model_component_count', 0)}",
            f"- scored_example_count: {summary.get('scored_example_count', 0)}",
            f"- routing_policy_reused: {summary.get('routing_policy_reused', False)}",
            f"- routing_policy_smoke_test_count: {summary.get('routing_policy_smoke_test_count', 0)}",
            f"- routing_policy_smoke_test_passed: {summary.get('routing_policy_smoke_test_passed', False)}",
            "",
            "## Sidecar Samples",
            f"- cached_candidate_sidecar_sample_count: {summary.get('cached_candidate_sidecar_sample_count', 0)}",
            f"- cached_candidate_sidecar_sample_reason: {summary.get('cached_candidate_sidecar_sample_reason', '')}",
            "",
            "## Safety",
            f"- no_official_asset_modification_during_330b: {summary.get('no_official_asset_modification_during_330b', False)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Notes",
            "- 330B is sidecar scoring only and must not override existing production routing behavior.",
            "- Routing decisions shown here are derived through the reused 330A routing helper.",
            "- Cached candidate-like samples are optional and do not gate QA when unavailable.",
            "",
        ]
    )
