import argparse
import glob
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd


BASE_DIR = Path(r"D:\_datefac")
DELIVERY_DIR = BASE_DIR / "output" / "delivery_package"
TRIAL_DIR = BASE_DIR / "output" / "_stage1_safe_runner_trial" / "run_20260519_101315" / "ai_repair_provider_intake" / "offline_file_replay_after_intake"
PRODUCTION_GUARD_PATTERNS = ["01_*.xlsx", "02_*.xlsx", "02A_*.xlsx", "06_*.xlsx"]


def _norm(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    return str(v).strip()


def _key(asset: str, metric: str, year: str) -> str:
    return "|".join([_norm(asset), _norm(metric), _norm(year)])


def _candidate_id(source_stage: str, metric_key: str) -> str:
    digest = hashlib.md5(f"{source_stage}|{metric_key}".encode("utf-8")).hexdigest()[:8]
    return f"{source_stage.upper()}_{digest}"


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _collect_production_guard_files() -> Dict[str, Path]:
    out: Dict[str, Path] = {}
    for pat in PRODUCTION_GUARD_PATTERNS:
        matched = sorted(DELIVERY_DIR.glob(pat))
        if matched:
            if pat.startswith("01_"):
                out["01"] = matched[0]
            elif pat.startswith("02A_"):
                out["02A"] = matched[0]
            elif pat.startswith("02_"):
                # prefer non-backup
                preferred = [p for p in matched if "backup" not in p.name.lower()]
                out["02"] = preferred[0] if preferred else matched[0]
            elif pat.startswith("06_"):
                preferred = [p for p in matched if "_copy_" not in p.name]
                out["06"] = preferred[0] if preferred else matched[0]
    return out


def _snapshot(files: Dict[str, Path]) -> Dict[str, str]:
    snap: Dict[str, str] = {}
    for k, p in files.items():
        snap[k] = _hash(p) if p.exists() else ""
    return snap


def _run_delivery_check() -> Dict[str, Any]:
    script = BASE_DIR / "tools" / "check_delivery_state.py"
    p = subprocess.run(
        [sys.executable, str(script), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return json.loads((p.stdout or "").strip() or "{}")
    except Exception:
        return {"overall_status": "UNKNOWN"}


def _recommended_action(reason: str, source_stage: str) -> str:
    r = _norm(reason).lower()
    if "conflict" in r:
        return "RESOLVE_CONFLICT"
    if "mapping" in r or "target" in r:
        return "FIX_TARGET_MAPPING"
    if "non_target" in r or "rejected" in r:
        return "REJECT_CANDIDATE"
    if source_stage == "allowlist_manual_review":
        return "MANUAL_VERIFY_EVIDENCE"
    return "READY_FOR_STAGE1B_REVIEW"


def _load_inputs() -> Dict[str, pd.DataFrame]:
    paths = {
        "manual_review": TRIAL_DIR / "ai_extract_candidates_manual_review.xlsx",
        "merge_blocked": TRIAL_DIR / "ai_extract_merge_blocked.xlsx",
        "apply_review": TRIAL_DIR / "ai_extract_apply_plan_review.xlsx",
        "apply_blocked": TRIAL_DIR / "ai_extract_apply_plan_blocked.xlsx",
    }
    out: Dict[str, pd.DataFrame] = {}
    if paths["manual_review"].exists():
        out["manual_review"] = pd.read_excel(paths["manual_review"], sheet_name="manual_review")
    if paths["merge_blocked"].exists():
        out["merge_blocked"] = pd.read_excel(paths["merge_blocked"], sheet_name="blocked")
    if paths["apply_review"].exists():
        out["apply_review"] = pd.read_excel(paths["apply_review"], sheet_name="review_before_apply")
    if paths["apply_blocked"].exists():
        out["apply_blocked"] = pd.read_excel(paths["apply_blocked"], sheet_name="blocked")
    return out


def build_inventory() -> int:
    guard_files = _collect_production_guard_files()
    snap_before = _snapshot(guard_files)

    frames = _load_inputs()

    records: List[Dict[str, Any]] = []

    # 1) allowlist manual review
    for _, r in frames.get("manual_review", pd.DataFrame()).iterrows():
        asset = _norm(r.get("asset_package"))
        metric = _norm(r.get("standardized_metric"))
        year = _norm(r.get("year"))
        metric_key = _key(asset, metric, year)
        source_stage = "allowlist_manual_review"
        reason = _norm(r.get("gate_reason")) or _norm(r.get("gate_decision")) or "manual_review_routed"
        records.append(
            {
                "candidate_id": _candidate_id(source_stage, metric_key),
                "metric_key": metric_key,
                "company": _norm(r.get("company")),
                "report": asset,
                "year": year,
                "target_sheet": "06_最终核心财务指标",
                "target_row / target_column / target_cell": "",
                "extracted_value / proposed_value": _norm(r.get("value")),
                "evidence / source_reference": _norm(r.get("source_trace_id")) or _norm(r.get("source_cell_or_segment")) or _norm(r.get("evidence")),
                "block_or_review_reason": reason,
                "current_status": "manual_review_pending",
                "source_stage": source_stage,
            }
        )

    # 2) merge blocked (contains conflict)
    for _, r in frames.get("merge_blocked", pd.DataFrame()).iterrows():
        asset = _norm(r.get("resolved_asset_package"))
        metric = _norm(r.get("standardized_metric"))
        year = _norm(r.get("year"))
        metric_key = _key(asset, metric, year)
        source_stage = "merge_conflict" if _norm(r.get("merge_decision")) == "BLOCK_CONFLICT" else "merge_blocked"
        reason = _norm(r.get("merge_reason")) or _norm(r.get("merge_decision"))
        records.append(
            {
                "candidate_id": _candidate_id(source_stage, metric_key),
                "metric_key": metric_key,
                "company": _norm(r.get("company")),
                "report": asset,
                "year": year,
                "target_sheet": "06_最终核心财务指标",
                "target_row / target_column / target_cell": "",
                "extracted_value / proposed_value": _norm(r.get("value")),
                "evidence / source_reference": _norm(r.get("source_trace_id")) or _norm(r.get("source_cell_or_segment")) or _norm(r.get("evidence")),
                "block_or_review_reason": reason,
                "current_status": "blocked",
                "source_stage": source_stage,
            }
        )

    # 3) review before apply
    for _, r in frames.get("apply_review", pd.DataFrame()).iterrows():
        asset = _norm(r.get("resolved_asset_package"))
        metric = _norm(r.get("standardized_metric"))
        year = _norm(r.get("year"))
        metric_key = _key(asset, metric, year)
        source_stage = "review_before_apply"
        reason = _norm(r.get("apply_plan_reason")) or _norm(r.get("merge_reason")) or "review_before_apply"
        records.append(
            {
                "candidate_id": _candidate_id(source_stage, metric_key),
                "metric_key": metric_key,
                "company": _norm(r.get("company")),
                "report": asset,
                "year": year,
                "target_sheet": "06_最终核心财务指标",
                "target_row / target_column / target_cell": "",
                "extracted_value / proposed_value": _norm(r.get("value")),
                "evidence / source_reference": _norm(r.get("source_trace_id")) or _norm(r.get("source_cell_or_segment")) or _norm(r.get("evidence")),
                "block_or_review_reason": reason,
                "current_status": "review_before_apply",
                "source_stage": source_stage,
            }
        )

    # 4) apply blocked (mostly overlaps merge_blocked; keep as source trace, then dedupe)
    for _, r in frames.get("apply_blocked", pd.DataFrame()).iterrows():
        asset = _norm(r.get("resolved_asset_package"))
        metric = _norm(r.get("standardized_metric"))
        year = _norm(r.get("year"))
        metric_key = _key(asset, metric, year)
        source_stage = "merge_conflict" if _norm(r.get("merge_decision")) == "BLOCK_CONFLICT" else "merge_blocked"
        reason = _norm(r.get("block_reason")) or _norm(r.get("merge_reason")) or _norm(r.get("merge_decision"))
        records.append(
            {
                "candidate_id": _candidate_id(source_stage, metric_key),
                "metric_key": metric_key,
                "company": _norm(r.get("company")),
                "report": asset,
                "year": year,
                "target_sheet": "06_最终核心财务指标",
                "target_row / target_column / target_cell": "",
                "extracted_value / proposed_value": _norm(r.get("value")),
                "evidence / source_reference": _norm(r.get("source_trace_id")) or _norm(r.get("source_cell_or_segment")) or _norm(r.get("evidence")),
                "block_or_review_reason": reason,
                "current_status": "blocked",
                "source_stage": source_stage,
            }
        )

    raw_df = pd.DataFrame(records)
    if raw_df.empty:
        raise RuntimeError("No backlog records found from Stage 1 artifacts.")

    # dedupe by source_stage + metric_key + proposed value
    raw_df["dedupe_key"] = (
        raw_df["source_stage"].astype(str)
        + "||"
        + raw_df["metric_key"].astype(str)
        + "||"
        + raw_df["extracted_value / proposed_value"].astype(str)
    )
    backlog_df = raw_df.drop_duplicates(subset=["dedupe_key"]).copy().reset_index(drop=True)
    backlog_df.drop(columns=["dedupe_key"], inplace=True)

    backlog_df["recommended_next_action"] = backlog_df.apply(
        lambda r: _recommended_action(_norm(r.get("block_or_review_reason")), _norm(r.get("source_stage"))),
        axis=1,
    )

    # stage counts from source artifacts (for requested fixed counters)
    manual_review_candidate_count = len(frames.get("manual_review", pd.DataFrame()))
    blocked_candidate_count = len(frames.get("merge_blocked", pd.DataFrame()))
    conflict_candidate_count = int(
        (
            frames.get("merge_blocked", pd.DataFrame())
            .get("merge_decision", pd.Series(dtype=str))
            .astype(str)
            .eq("BLOCK_CONFLICT")
            .sum()
        )
    )
    review_before_apply_candidate_count = len(frames.get("apply_review", pd.DataFrame()))

    unique_backlog_candidate_count = len(backlog_df)
    action_counts = Counter(backlog_df["recommended_next_action"].tolist())
    ready_for_stage1b_review_count = int(action_counts.get("READY_FOR_STAGE1B_REVIEW", 0))
    reject_recommended_count = int(action_counts.get("REJECT_CANDIDATE", 0))
    fix_mapping_required_count = int(action_counts.get("FIX_TARGET_MAPPING", 0))
    conflict_resolution_required_count = int(action_counts.get("RESOLVE_CONFLICT", 0))

    # write outputs
    out_xlsx = DELIVERY_DIR / "75_stage1b_backlog_inventory.xlsx"
    out_md = DELIVERY_DIR / "75_stage1b_backlog_inventory.md"
    out_json = DELIVERY_DIR / "76_stage1b_backlog_summary.json"

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        backlog_df.to_excel(writer, sheet_name="backlog_inventory", index=False)
        pd.DataFrame(
            [
                {"field": "manual_review_candidate_count", "value": manual_review_candidate_count},
                {"field": "blocked_candidate_count", "value": blocked_candidate_count},
                {"field": "conflict_candidate_count", "value": conflict_candidate_count},
                {"field": "review_before_apply_candidate_count", "value": review_before_apply_candidate_count},
                {"field": "unique_backlog_candidate_count", "value": unique_backlog_candidate_count},
                {"field": "ready_for_stage1b_review_count", "value": ready_for_stage1b_review_count},
                {"field": "reject_recommended_count", "value": reject_recommended_count},
                {"field": "fix_mapping_required_count", "value": fix_mapping_required_count},
                {"field": "conflict_resolution_required_count", "value": conflict_resolution_required_count},
            ]
        ).to_excel(writer, sheet_name="summary", index=False)
        pd.DataFrame([{"action": k, "count": v} for k, v in sorted(action_counts.items())]).to_excel(
            writer, sheet_name="action_distribution", index=False
        )
        pd.DataFrame([{"source_stage": k, "count": v} for k, v in sorted(Counter(backlog_df["source_stage"]).items())]).to_excel(
            writer, sheet_name="stage_distribution", index=False
        )

    out_md.write_text(
        "\n".join(
            [
                "# Stage 1B Backlog Inventory",
                "",
                f"- manual_review_candidate_count: {manual_review_candidate_count}",
                f"- blocked_candidate_count: {blocked_candidate_count}",
                f"- conflict_candidate_count: {conflict_candidate_count}",
                f"- review_before_apply_candidate_count: {review_before_apply_candidate_count}",
                f"- unique_backlog_candidate_count: {unique_backlog_candidate_count}",
                f"- ready_for_stage1b_review_count: {ready_for_stage1b_review_count}",
                f"- reject_recommended_count: {reject_recommended_count}",
                f"- fix_mapping_required_count: {fix_mapping_required_count}",
                f"- conflict_resolution_required_count: {conflict_resolution_required_count}",
                "",
                "## Source Stages",
                "- allowlist_manual_review",
                "- merge_blocked",
                "- merge_conflict",
                "- review_before_apply",
            ]
        ),
        encoding="utf-8",
    )

    snap_after = _snapshot(guard_files)
    production_files_unchanged = snap_before == snap_after
    delivery_status = _run_delivery_check()

    summary = {
        "manual_review_candidate_count": manual_review_candidate_count,
        "blocked_candidate_count": blocked_candidate_count,
        "conflict_candidate_count": conflict_candidate_count,
        "review_before_apply_candidate_count": review_before_apply_candidate_count,
        "unique_backlog_candidate_count": unique_backlog_candidate_count,
        "ready_for_stage1b_review_count": ready_for_stage1b_review_count,
        "reject_recommended_count": reject_recommended_count,
        "fix_mapping_required_count": fix_mapping_required_count,
        "conflict_resolution_required_count": conflict_resolution_required_count,
        "production_files_unchanged": bool(production_files_unchanged),
        "ai_called": False,
        "factory_core_called": False,
        "ocr_called": False,
        "delivery_status_after": delivery_status.get("overall_status", "UNKNOWN"),
    }
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"manual_review_candidate_count: {manual_review_candidate_count}")
    print(f"blocked_candidate_count: {blocked_candidate_count}")
    print(f"conflict_candidate_count: {conflict_candidate_count}")
    print(f"review_before_apply_candidate_count: {review_before_apply_candidate_count}")
    print(f"unique_backlog_candidate_count: {unique_backlog_candidate_count}")
    print(f"ready_for_stage1b_review_count: {ready_for_stage1b_review_count}")
    print(f"reject_recommended_count: {reject_recommended_count}")
    print(f"fix_mapping_required_count: {fix_mapping_required_count}")
    print(f"conflict_resolution_required_count: {conflict_resolution_required_count}")
    print(f"production_files_unchanged: {production_files_unchanged}")
    print(f"delivery_status_after: {delivery_status.get('overall_status', 'UNKNOWN')}")
    print(f"out_xlsx: {out_xlsx}")
    print(f"out_md: {out_md}")
    print(f"out_json: {out_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(build_inventory())
