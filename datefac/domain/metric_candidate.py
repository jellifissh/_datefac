from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MetricCandidate:
    candidate_id: str
    source_stage: str
    source_file: str
    source_doc_name: Optional[str]
    source_table_id: Optional[str]
    source_row_index: Optional[int]
    source_row_text: str
    metric_code: str
    canonical_metric_name: str
    raw_metric_name: str
    year: str
    period_type: str
    raw_value: str
    normalized_value: Optional[float]
    unit: Optional[str]
    unit_source: str
    currency: Optional[str]
    confidence: float
    risk_tags: List[str] = field(default_factory=list)
    split_decision: str = "review_required_preview"
    split_reason: str = ""
    provenance_json: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
