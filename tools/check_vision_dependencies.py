import argparse
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config_manager import ConfigManager, DEFAULT_CONFIG
from vision_runtime import build_vision_env


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


def test_url(
    url: str,
    timeout: int = 15,
    headers: dict | None = None,
    label: str | None = None,
) -> None:
    request_label = label or url
    print(f"- GET {request_label}")
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=headers or {},
            stream=True,
        )
        print(f"  status_code={resp.status_code}")
        print(f"  content-length={resp.headers.get('content-length', '')}")
        print(f"  content-range={resp.headers.get('content-range', '')}")
        print(f"  final_url={resp.url}")
    except Exception as exc:
        print(f"  exception_type={type(exc).__name__}")
        print(f"  exception_message={exc}")


def maybe_apply_vision_env(use_vision_env: bool) -> str:
    if not use_vision_env:
        return "current_shell"

    cfg = ConfigManager(config_path=str(Path(__file__).resolve().parents[1] / "config.yaml"))
    config = cfg.load()
    paths = config.get("paths", {})
    default_paths = DEFAULT_CONFIG.get("paths", {})
    base_ai_path = paths.get("base_ai_path", default_paths.get("base_ai_path", r"D:\_datefac\ai_models"))
    temp_cache_dir = paths.get(
        "temp_cache_dir",
        default_paths.get("temp_cache_dir", r"D:\_datefac\output\.temp_cache"),
    )
    env = build_vision_env(base_ai_path, temp_cache_dir)
    os.environ.update(env)
    return "vision_env"


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
    parser = argparse.ArgumentParser(
        description="Diagnose marker/surya/datalab dependencies and cache/network status."
    )
    parser.add_argument(
        "--use-vision-env",
        action="store_true",
        help="Apply isolated vision runtime env from config.yaml before diagnostics.",
    )
    args = parser.parse_args()

    diagnostic_mode = maybe_apply_vision_env(args.use_vision_env)

    print_section("Python Runtime")
    print_kv("sys.executable", sys.executable)
    print_kv("sys.version", sys.version.replace("\n", " "))
    print_kv("diagnostic_mode", diagnostic_mode)

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
    test_url(
        "https://models.datalab.to/layout/2025_09_23/model.safetensors",
        headers={"Range": "bytes=0-1023"},
        label="https://models.datalab.to/layout/2025_09_23/model.safetensors (Range: bytes=0-1023)",
    )

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
