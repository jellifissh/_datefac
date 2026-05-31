from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SandboxDeliveryManifest:
    bundle_name: str
    created_at: str
    source_input_dir: str
    output_dir: str
    source_candidate_count: int
    trusted_delivery_count: int
    review_required_delivery_count: int
    rejected_source_count: int
    unique_metric_count: int
    unique_year_count: int
    qa_pass_count: int
    qa_warn_count: int
    qa_fail_count: int
    delivery_decision: str
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QACheckRow:
    check_name: str
    status: str
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_provenance_json(text: Any) -> Dict[str, Any]:
    if text is None:
        return {}
    t = str(text).strip()
    if not t:
        return {}
    try:
        obj = __import__("json").loads(t)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    return {}


def as_optional_text(v: Any) -> Optional[str]:
    if v is None:
        return None
    t = str(v).strip()
    if not t or t.lower() in {"nan", "none"}:
        return None
    return t
