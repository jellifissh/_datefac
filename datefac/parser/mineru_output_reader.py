from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from datefac.domain.table_asset import MineruSourceFile, TableAsset, TableAssetWarning, make_source_file


@dataclass
class MineruReadResult:
    source_root: str
    table_assets: List[TableAsset] = field(default_factory=list)
    warnings: List[TableAssetWarning] = field(default_factory=list)
    source_files: List[MineruSourceFile] = field(default_factory=list)

    def summary(self) -> Dict[str, Any]:
        role_counts: Dict[str, int] = {}
        for asset in self.table_assets:
            role_counts[asset.table_role_guess] = role_counts.get(asset.table_role_guess, 0) + 1
        return {
            "source_root": self.source_root,
            "table_asset_count": len(self.table_assets),
            "warning_count": len(self.warnings),
            "source_file_count": len(self.source_files),
            "role_counts": role_counts,
        }


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_int(value: Any) -> Optional[int]:
    s = _norm(value)
    if not s:
        return None
    try:
        return int(float(s))
    except Exception:
        return None


def _to_bbox(value: Any) -> Optional[List[float]]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        out: List[float] = []
        for item in value:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                out.extend([float(item[0]), float(item[1])])
            else:
                try:
                    out.append(float(item))
                except Exception:
                    continue
        return out if out else None
    if isinstance(value, dict):
        if {"x0", "y0", "x1", "y1"}.issubset(set(value.keys())):
            try:
                return [float(value["x0"]), float(value["y0"]), float(value["x1"]), float(value["y1"])]
            except Exception:
                return None
        vals = []
        for k in ("left", "top", "right", "bottom"):
            if k in value:
                vals.append(value[k])
        if len(vals) == 4:
            try:
                return [float(v) for v in vals]
            except Exception:
                return None
    return None


def _extract_first(data: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def _extract_text_like(data: Dict[str, Any], keys: Iterable[str]) -> str:
    value = _extract_first(data, keys)
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return " ".join(_norm(x) for x in value if _norm(x))
    if isinstance(value, dict):
        # common nested path format {"text": "..."}
        for k in ("text", "content", "value", "caption"):
            if k in value:
                return _norm(value[k])
    return _norm(value)


def _extract_block_type(data: Dict[str, Any]) -> str:
    return _norm(_extract_first(data, ("block_type", "type", "category", "kind", "node_type", "label"))).lower()


def _is_table_block(data: Dict[str, Any]) -> bool:
    bt = _extract_block_type(data)
    if "table" in bt:
        return True
    # fallback: has explicit table-like fields
    keys = set(data.keys())
    return bool({"table", "table_body", "table_rows"} & keys)


def _text_from_neighbor_block(obj: Any) -> str:
    if not isinstance(obj, dict):
        return ""
    return _extract_text_like(obj, ("text", "content", "html", "markdown", "caption", "title", "footnote"))


def _nearby_text_from_siblings(siblings: List[Any], idx: int, radius: int = 1) -> str:
    nearby: List[str] = []
    for j in range(max(0, idx - radius), min(len(siblings), idx + radius + 1)):
        if j == idx:
            continue
        txt = _text_from_neighbor_block(siblings[j])
        if txt:
            nearby.append(txt)
    return " ".join(nearby).strip()


def _resolve_image_path(raw_image: str, source_file: Path, root: Path, image_dirs: List[Path]) -> str:
    value = _norm(raw_image)
    if not value:
        return ""
    p = Path(value)
    if p.is_absolute():
        return str(p)
    cands = [source_file.parent / p, root / p]
    for img_dir in image_dirs:
        cands.append(img_dir / p)
        cands.append(img_dir / p.name)
    for cand in cands:
        if cand.exists():
            return str(cand.resolve())
    return str((source_file.parent / p).resolve())


def _guess_table_role(caption: str, footnote: str, nearby_text: str) -> Tuple[str, str]:
    text = f"{caption} {footnote} {nearby_text}".lower()
    keyword_sets: List[Tuple[str, List[str]]] = [
        ("financial_statement_table", ["资产负债表", "利润表", "现金流量表", "合并利润", "balance sheet", "income statement", "cash flow"]),
        ("valuation_table", ["估值", "pe", "p/e", "pb", "p/b", "ev/ebitda", "倍", "valuation"]),
        ("core_metric_table", ["营业收入", "归母净利润", "毛利率", "roe", "每股收益", "eps", "revenue", "net profit", "gross margin"]),
        ("forecast_table", ["预测", "展望", "forecast", "预计", "2025e", "2026e"]),
    ]
    for role, words in keyword_sets:
        for w in words:
            if w in text:
                return role, f"matched_keyword:{w}"
    return "general_table", "default_no_keyword_match"


def _flatten_for_json(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for k, v in value.items():
            if len(out) >= 12:
                break
            out[_norm(k)] = _flatten_for_json(v)
        return out
    if isinstance(value, list):
        return [_flatten_for_json(x) for x in value[:12]]
    return _norm(value)


def discover_mineru_sources(source_root: Path) -> Tuple[List[Path], List[Path], List[Path], List[MineruSourceFile], List[TableAssetWarning]]:
    root = source_root.resolve()
    content_v2 = sorted(root.rglob("*_content_list_v2.json"))
    content_v1 = sorted(root.rglob("*_content_list.json"))
    mds = sorted(root.rglob("*.md"))
    image_dirs = sorted([p for p in root.rglob("*") if p.is_dir() and p.name.lower() == "images"])
    warnings: List[TableAssetWarning] = []
    source_files: List[MineruSourceFile] = []

    for p in content_v2:
        source_files.append(make_source_file(p, "content_list_v2", related_images_dir=str(p.parent / "images")))
    for p in content_v1:
        source_files.append(make_source_file(p, "content_list", related_images_dir=str(p.parent / "images")))
    for p in mds:
        source_files.append(make_source_file(p, "markdown", related_images_dir=str(p.parent / "images")))
    for p in image_dirs:
        source_files.append(make_source_file(p, "images_dir"))

    if not content_v2 and not content_v1:
        # fallback: tolerate non-standard json naming
        generic_jsons = sorted(
            [
                p
                for p in root.rglob("*.json")
                if not p.name.endswith("_meta.json") and "_summary" not in p.name and "_report" not in p.name
            ]
        )
        if generic_jsons:
            warnings.append(
                TableAssetWarning(
                    source_file=str(root),
                    warning_code="non_standard_content_list_name",
                    warning_message="未发现 *_content_list*.json，已回退扫描 generic json。",
                )
            )
            for p in generic_jsons:
                source_files.append(make_source_file(p, "generic_json", related_images_dir=str(p.parent / "images")))
            return generic_jsons, mds, image_dirs, source_files, warnings

    json_files = sorted(set(content_v2 + content_v1))
    return json_files, mds, image_dirs, source_files, warnings


def _extract_assets_from_json(
    root: Path,
    source_file: Path,
    source_kind: str,
    payload: Any,
    image_dirs: List[Path],
    warnings: List[TableAssetWarning],
) -> List[TableAsset]:
    assets: List[TableAsset] = []
    block_counter = 0
    doc_id = source_file.stem.replace("_content_list_v2", "").replace("_content_list", "")

    def walk(node: Any, siblings: Optional[List[Any]] = None, sibling_idx: int = -1) -> None:
        nonlocal block_counter
        if isinstance(node, dict):
            if _is_table_block(node):
                page_idx = _to_int(_extract_first(node, ("page_idx", "page_index", "page_no", "page", "page_id")))
                if page_idx is None and isinstance(node.get("position"), dict):
                    page_idx = _to_int(node["position"].get("page_idx"))
                bbox = _to_bbox(_extract_first(node, ("bbox", "box", "bounding_box", "rect", "polygon")))
                if bbox is None and isinstance(node.get("position"), dict):
                    bbox = _to_bbox(node["position"].get("bbox"))
                image_raw = _extract_text_like(node, ("image_path", "img_path", "image", "img", "table_image", "crop_image"))
                if not image_raw and isinstance(node.get("images"), list) and node["images"]:
                    image_raw = _norm(node["images"][0])
                image_path = _resolve_image_path(image_raw, source_file, root, image_dirs) if image_raw else ""
                caption = _extract_text_like(node, ("caption", "title", "table_caption"))
                footnote = _extract_text_like(node, ("footnote", "notes", "table_footnote"))
                nearby_text = _extract_text_like(node, ("nearby_text", "context", "surrounding_text", "text_before_after"))
                if not nearby_text and siblings is not None and sibling_idx >= 0:
                    nearby_text = _nearby_text_from_siblings(siblings, sibling_idx)
                role, reason = _guess_table_role(caption, footnote, nearby_text)

                block_counter += 1
                asset = TableAsset(
                    source_root=str(root),
                    source_file=str(source_file),
                    source_kind=source_kind,
                    block_index=block_counter,
                    page_idx=page_idx,
                    bbox=bbox,
                    image_path=image_path,
                    caption=caption,
                    footnote=footnote,
                    nearby_text=nearby_text,
                    table_role_guess=role,
                    table_role_reason=reason,
                    raw_block_type=_norm(_extract_first(node, ("block_type", "type", "category", "kind"))),
                    raw_block_id=_norm(_extract_first(node, ("id", "block_id", "uuid"))),
                    source_doc_id=doc_id,
                    extra={"raw_block": _flatten_for_json(node)},
                )
                assets.append(asset)

                if asset.page_idx is None:
                    warnings.append(
                        TableAssetWarning(
                            source_file=str(source_file),
                            warning_code="missing_page_idx",
                            warning_message="table block 缺少 page_idx/page 信息。",
                            block_index=asset.block_index,
                            block_id=asset.raw_block_id,
                        )
                    )
                if asset.bbox is None:
                    warnings.append(
                        TableAssetWarning(
                            source_file=str(source_file),
                            warning_code="missing_bbox",
                            warning_message="table block 缺少 bbox。",
                            block_index=asset.block_index,
                            block_id=asset.raw_block_id,
                        )
                    )
                if not asset.image_path:
                    warnings.append(
                        TableAssetWarning(
                            source_file=str(source_file),
                            warning_code="missing_image_path",
                            warning_message="table block 缺少 image_path。",
                            block_index=asset.block_index,
                            block_id=asset.raw_block_id,
                        )
                    )

            for v in node.values():
                walk(v, None, -1)
            return

        if isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, node, i)
            return

    walk(payload, None, -1)
    return assets


_MARKDOWN_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}.*\|\s*$")


def _extract_assets_from_markdown(
    root: Path,
    md_file: Path,
    image_dirs: List[Path],
    warnings: List[TableAssetWarning],
) -> List[TableAsset]:
    text = md_file.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    assets: List[TableAsset] = []
    i = 0
    block_counter = 0
    while i < len(lines):
        line = lines[i]
        if "|" in line and i + 1 < len(lines) and _MARKDOWN_TABLE_SEP.search(lines[i + 1] or ""):
            start = i
            end = i + 2
            while end < len(lines) and "|" in lines[end]:
                end += 1
            block_counter += 1
            caption = ""
            for j in range(start - 1, max(-1, start - 8), -1):
                s = _norm(lines[j])
                if s:
                    caption = s
                    break
            nearby = " ".join(_norm(x) for x in lines[max(0, start - 2) : min(len(lines), end + 2)] if _norm(x))
            image_raw = ""
            for j in range(max(0, start - 4), min(len(lines), end + 4)):
                m = re.search(r"!\[[^\]]*\]\(([^)]+)\)", lines[j])
                if m:
                    image_raw = m.group(1)
                    break
            image_path = _resolve_image_path(image_raw, md_file, root, image_dirs) if image_raw else ""
            role, reason = _guess_table_role(caption, "", nearby)
            assets.append(
                TableAsset(
                    source_root=str(root),
                    source_file=str(md_file),
                    source_kind="markdown",
                    block_index=block_counter,
                    page_idx=None,
                    bbox=None,
                    image_path=image_path,
                    caption=caption,
                    footnote="",
                    nearby_text=nearby,
                    table_role_guess=role,
                    table_role_reason=reason,
                    raw_block_type="markdown_table",
                    raw_block_id=f"md_table_{block_counter}",
                    source_doc_id=md_file.stem,
                    extra={"line_range": [start + 1, end]},
                )
            )
            warnings.append(
                TableAssetWarning(
                    source_file=str(md_file),
                    warning_code="markdown_table_missing_layout_fields",
                    warning_message="Markdown 表格缺少 page_idx/bbox，已按弱结构记录。",
                    block_index=block_counter,
                )
            )
            i = end
            continue
        i += 1
    return assets


def read_mineru_output(source_root: Path | str) -> MineruReadResult:
    root = Path(source_root).resolve()
    result = MineruReadResult(source_root=str(root))

    if not root.exists():
        result.warnings.append(
            TableAssetWarning(
                source_file=str(root),
                warning_code="source_root_not_found",
                warning_message="输入目录不存在。",
            )
        )
        return result

    json_files, mds, image_dirs, source_files, discover_warnings = discover_mineru_sources(root)
    result.source_files.extend(source_files)
    result.warnings.extend(discover_warnings)

    if not json_files and not mds:
        result.warnings.append(
            TableAssetWarning(
                source_file=str(root),
                warning_code="no_content_files_found",
                warning_message="未找到 content_list/json 或 markdown 文件。",
            )
        )
        return result

    for jf in json_files:
        try:
            payload = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as exc:
            result.warnings.append(
                TableAssetWarning(
                    source_file=str(jf),
                    warning_code="json_load_failed",
                    warning_message=f"JSON 读取失败: {exc}",
                )
            )
            continue

        source_kind = "content_list_v2" if jf.name.endswith("_content_list_v2.json") else ("content_list" if jf.name.endswith("_content_list.json") else "generic_json")
        result.table_assets.extend(
            _extract_assets_from_json(
                root=root,
                source_file=jf,
                source_kind=source_kind,
                payload=payload,
                image_dirs=image_dirs,
                warnings=result.warnings,
            )
        )

    for md in mds:
        try:
            result.table_assets.extend(_extract_assets_from_markdown(root=root, md_file=md, image_dirs=image_dirs, warnings=result.warnings))
        except Exception as exc:
            result.warnings.append(
                TableAssetWarning(
                    source_file=str(md),
                    warning_code="markdown_parse_failed",
                    warning_message=f"Markdown 解析失败: {exc}",
                )
            )

    if not result.table_assets:
        result.warnings.append(
            TableAssetWarning(
                source_file=str(root),
                warning_code="no_table_blocks_extracted",
                warning_message="未提取到 table block，请检查 MinerU 输出格式是否兼容。",
            )
        )

    return result

