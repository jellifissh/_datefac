from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List


SEMANTIC_ALIAS_ASSET_PATH = Path(r"D:\_datefac\data\overrides\semantic_alias_candidates.json")
FORMAL_SCOPE_RULES_PATH = Path(r"D:\_datefac\data\mapping\formal_scope_rules.json")


def sha256_file(path: Path) -> str:
    if not path.exists():
        return "__MISSING__"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_official_asset_hashes(paths: Iterable[Path] | None = None) -> Dict[str, str]:
    selected = list(paths or [SEMANTIC_ALIAS_ASSET_PATH, FORMAL_SCOPE_RULES_PATH])
    return {str(path): sha256_file(path) for path in selected}


def build_no_apply_proof(
    *,
    stage: str,
    files_read: List[str],
    official_assets_before: Dict[str, str],
    official_assets_after: Dict[str, str],
    official_assets_written: List[str] | None = None,
) -> Dict[str, Any]:
    written = list(official_assets_written or [])
    unchanged = official_assets_before == official_assets_after and not written
    return {
        "stage": stage,
        "files_read": files_read,
        "official_assets_before": official_assets_before,
        "official_assets_after": official_assets_after,
        "official_assets_written": written,
        f"no_official_asset_modification_during_{stage.lower()}": unchanged,
    }
