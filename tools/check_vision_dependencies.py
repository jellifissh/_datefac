import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import requests


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_kv(key: str, value) -> None:
    print(f"{key}: {value}")


def find_pkg_path(pkg_name: str) -> str:
    try:
        spec = importlib.util.find_spec(pkg_name)
        if spec is None:
            return "NOT_FOUND"
        if spec.origin:
            return spec.origin
        if spec.submodule_search_locations:
            return ";".join(spec.submodule_search_locations)
        return "FOUND_BUT_NO_PATH"
    except Exception as exc:
        return f"ERROR: {exc}"


def test_url(url: str, timeout: int = 15) -> None:
    print(f"- GET {url}")
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        print(f"  status_code={resp.status_code} final_url={resp.url}")
    except Exception as exc:
        print(f"  EXCEPTION: {type(exc).__name__}: {exc}")


def list_key_dirs(base: Path, max_depth: int = 3) -> None:
    if not base.exists():
        print(f"{base} -> MISSING")
        return
    print(f"{base} -> EXISTS")
    root_len = len(base.parts)
    keywords = ("manifest", "layout", "recognition", "table_rec", "table", "models")
    shown = 0
    for p in sorted(base.rglob("*")):
        depth = len(p.parts) - root_len
        if depth > max_depth:
            continue
        name = p.name.lower()
        if p.is_dir() and any(k in name for k in keywords):
            print(f"  [DIR]  {p}")
            shown += 1
        elif p.is_file() and ("manifest" in name or name.endswith(".json")):
            print(f"  [FILE] {p}")
            shown += 1
        if shown >= 200:
            print("  ... output truncated (200 entries)")
            break


def main() -> int:
    print_section("Python Runtime")
    print_kv("sys.executable", sys.executable)
    print_kv("sys.version", sys.version.replace("\n", " "))

    print_section("Package Paths")
    for pkg in ["marker", "surya", "datalab", "torch", "requests"]:
        print_kv(pkg, find_pkg_path(pkg))

    print_section("Environment Variables")
    env_keys = [
        "HF_HOME",
        "HF_HUB_CACHE",
        "TRANSFORMERS_CACHE",
        "TORCH_HOME",
        "MARKER_MODEL_DIR",
        "DATALAB_CACHE_DIR",
        "DATALAB_HOME",
        "SURYA_CACHE_DIR",
        "LOCALAPPDATA",
        "APPDATA",
        "USERPROFILE",
        "HOME",
        "TEMP",
        "TMP",
    ]
    for key in env_keys:
        print_kv(key, os.environ.get(key, ""))

    print_section("Path & Temp")
    print_kv("pathlib.Path.home()", Path.home())
    print_kv("tempfile.gettempdir()", tempfile.gettempdir())
    print_kv("os.getcwd()", os.getcwd())

    print_section("Network Checks")
    test_url("https://models.datalab.to")
    test_url("https://models.datalab.to/layout/2025_09_23/manifest.json")

    print_section("Local Cache Structure")
    bases = [
        Path(r"D:\_datefac\ai_models\datalab"),
        Path(r"D:\_datefac\ai_models\surya"),
        Path(r"D:\_datefac\ai_models\hf"),
    ]
    for base in bases:
        list_key_dirs(base)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

