from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Set

import pandas as pd


SHEET_ORDER = [
    "summary",
    "risk_registry",
    "example_trust_records",
    "routing_smoke_tests",
    "closure_validation",
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


def trust_engine_foundation_330a_markdown(summary: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Trust Engine Foundation 330A",
            "",
            "## Decision",
            f"- decision: {summary.get('decision', '')}",
            "",
            "## Foundation Scope",
            f"- risk_registry_count: {summary.get('risk_registry_count', 0)}",
            f"- example_trust_record_count: {summary.get('example_trust_record_count', 0)}",
            f"- routing_policy_smoke_test_count: {summary.get('routing_policy_smoke_test_count', 0)}",
            f"- routing_policy_smoke_test_passed: {summary.get('routing_policy_smoke_test_passed', False)}",
            "",
            "## Input Validation",
            f"- validated_325p_closure: {summary.get('validated_325p_closure', False)}",
            f"- no_official_asset_modification_during_330a: {summary.get('no_official_asset_modification_during_330a', False)}",
            "",
            "## QA",
            f"- qa_pass_count: {summary.get('qa_pass_count', 0)}",
            f"- qa_warn_count: {summary.get('qa_warn_count', 0)}",
            f"- qa_fail_count: {summary.get('qa_fail_count', 0)}",
            "",
            "## Notes",
            "- 330A is an architectural foundation stage and does not change production routing behavior.",
            "- Example trust records are smoke fixtures built from cached-cycle conventions only.",
            "- Official assets are read-only and validated through before/after hash proof.",
            "",
        ]
    )
