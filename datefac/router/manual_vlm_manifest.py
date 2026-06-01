from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from .router_policy import VLM_PRIMARY


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _priority(value_score: Any) -> str:
    try:
        score = int(float(value_score))
    except Exception:
        score = 0
    if score >= 90:
        return "P0"
    if score >= 75:
        return "P1"
    return "P2"


def build_manual_vlm_manifest(preview_df: pd.DataFrame, output_root: Path) -> pd.DataFrame:
    if preview_df.empty:
        return pd.DataFrame(
            columns=[
                "manifest_id",
                "source_report_name",
                "table_asset_id",
                "image_path",
                "table_role_guess",
                "recommended_prompt_version",
                "recommended_output_dir",
                "expected_output_files",
                "priority",
                "reason_selected",
            ]
        )

    rows: List[Dict[str, Any]] = []
    selected = preview_df[preview_df["recommended_route"] == VLM_PRIMARY].copy()
    selected = selected.sort_values(
        ["estimated_value_score", "confidence_score", "source_report_name", "table_asset_id"],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)
    for _, row in selected.iterrows():
        manifest_id = _norm(row.get("table_asset_id")) or _norm(row.get("image_filename")) or _norm(row.get("source_report_name"))
        recommended_dir = output_root / manifest_id
        reason_parts = [_norm(row.get("route_reason"))]
        if _norm(row.get("vlm_quality_decision")) == "VLM_TABLE_READY_FOR_MAPPING":
            reason_parts.append("existing_vlm_quality_ready")
        elif _norm(row.get("vlm_quality_decision")):
            reason_parts.append(f"existing_vlm_quality={_norm(row.get('vlm_quality_decision'))}")
        else:
            reason_parts.append("needs_manual_vlm_output")
        rows.append(
            {
                "manifest_id": manifest_id,
                "source_report_name": _norm(row.get("source_report_name")),
                "table_asset_id": _norm(row.get("table_asset_id")),
                "image_path": _norm(row.get("image_path")),
                "table_role_guess": _norm(row.get("effective_role_category") or row.get("table_role_guess")),
                "recommended_prompt_version": "321C_ROUTER_STRICT_JSON_V1",
                "recommended_output_dir": str(recommended_dir),
                "expected_output_files": json.dumps(["table_meta.json", "raw_response.txt", "vlm_output.json"], ensure_ascii=False),
                "priority": _priority(row.get("estimated_value_score")),
                "reason_selected": "|".join([x for x in reason_parts if x]),
            }
        )
    return pd.DataFrame(rows)
