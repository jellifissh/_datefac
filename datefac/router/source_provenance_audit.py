from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


PURE_VLM_IMAGE_ONLY = "PURE_VLM_IMAGE_ONLY"
MINERU_TABLE_BODY_STRUCTURING = "MINERU_TABLE_BODY_STRUCTURING"


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _contains_source_signal(payload: Any, token: str) -> bool:
    token_lower = token.lower()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if _norm(key).lower() == "forbidden_sources":
                continue
            if _contains_source_signal(value, token):
                return True
        return False
    if isinstance(payload, list):
        for item in payload:
            if _contains_source_signal(item, token):
                return True
        return False
    return token_lower in _norm(payload).lower()


def audit_vlm_output_root(
    root: Path,
    dataset_label: str,
    expected_recognition_source: Optional[str] = None,
    assume_manual_sample_contamination: bool = False,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if not root.exists() or not root.is_dir():
        return pd.DataFrame(
            [
                {
                    "dataset_label": dataset_label,
                    "sample_id": "",
                    "folder_path": str(root),
                    "table_meta_exists": False,
                    "recognition_source": None,
                    "is_pure_vlm": None,
                    "source_stage": None,
                    "source_image_path": None,
                    "meta_forbidden_sources": "",
                    "audit_status": "WARN",
                    "risk_tags": "MISSING_SOURCE_ROOT",
                    "recommended_label": expected_recognition_source or dataset_label,
                    "source_confidence": 0.0,
                    "audit_reason": "source root missing",
                }
            ]
        )

    for folder in sorted([path for path in root.iterdir() if path.is_dir()]):
        meta_path = folder / "table_meta.json"
        meta = _read_json(meta_path)
        forbidden_sources = meta.get("forbidden_sources") if isinstance(meta.get("forbidden_sources"), list) else []
        forbidden_text = "|".join(_norm(item) for item in forbidden_sources if _norm(item))
        recognition_source = _norm(meta.get("recognition_source")) or None
        is_pure_vlm = meta.get("is_pure_vlm")
        source_stage = _norm(meta.get("source_stage")) or None
        source_image_path = _norm(meta.get("source_image_path")) or None
        audit_status = "PASS"
        risk_tags: List[str] = []
        recommended_label = expected_recognition_source or dataset_label
        source_confidence = 1.0
        audit_reason = "source metadata verified"

        if not meta_path.exists():
            audit_status = "WARN"
            risk_tags.append("MISSING_TABLE_META")
            source_confidence = 0.0
            audit_reason = "table_meta.json missing"
        elif dataset_label == "PURE_VLM_OUTPUT_ROOT":
            if recognition_source != PURE_VLM_IMAGE_ONLY:
                audit_status = "FAIL"
                risk_tags.append("PURE_VLM_SOURCE_MISMATCH")
                source_confidence = 0.2
            if is_pure_vlm is not True:
                audit_status = "FAIL"
                risk_tags.append("PURE_VLM_FLAG_MISSING")
                source_confidence = min(source_confidence, 0.2)
            if _contains_source_signal(meta, "table_body") or _contains_source_signal(meta, "table_caption") or _contains_source_signal(meta, "content_list"):
                # Allowed when present only as forbidden source declarations.
                pass
            if source_stage != "321D_pure_vlm_image_only":
                audit_status = "WARN" if audit_status == "PASS" else audit_status
                risk_tags.append("PURE_VLM_STAGE_UNEXPECTED")
                source_confidence = min(source_confidence, 0.8)
            if audit_status == "PASS":
                audit_reason = "recognition_source=PURE_VLM_IMAGE_ONLY and is_pure_vlm=true"
        else:
            recommended_label = MINERU_TABLE_BODY_STRUCTURING
            source_confidence = 0.35
            audit_status = "WARN"
            if not recognition_source:
                risk_tags.append("MISSING_RECOGNITION_SOURCE")
            if assume_manual_sample_contamination:
                risk_tags.append("SOURCE_CONTAMINATION_RISK")
            if source_stage and "manual_vlm_sample" in source_stage.lower():
                risk_tags.append("MANUAL_SAMPLE_LABEL_ONLY")
            audit_reason = "manual sample root should not be treated as pure VLM"

        rows.append(
            {
                "dataset_label": dataset_label,
                "sample_id": _norm(meta.get("sample_id")) or folder.name,
                "folder_path": str(folder),
                "table_meta_exists": meta_path.exists(),
                "recognition_source": recognition_source,
                "is_pure_vlm": is_pure_vlm,
                "source_stage": source_stage,
                "source_image_path": source_image_path,
                "meta_forbidden_sources": forbidden_text,
                "audit_status": audit_status,
                "risk_tags": "|".join(sorted(set(tag for tag in risk_tags if tag))),
                "recommended_label": recommended_label,
                "source_confidence": source_confidence,
                "audit_reason": audit_reason,
            }
        )

    return pd.DataFrame(rows)
