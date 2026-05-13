import argparse
import os
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_kv(key: str, value) -> None:
    print(f"{key}: {value}")


def print_tmp_phase(phase: str) -> None:
    print(f"[TMP_PHASE] {phase}")
    print_kv("TEMP", os.environ.get("TEMP", ""))
    print_kv("TMP", os.environ.get("TMP", ""))
    print_kv("tempfile.gettempdir()", tempfile.gettempdir())


def print_runtime_env_snapshot(prefix: str = "") -> None:
    if prefix:
        print(prefix)
    print_kv("sys.executable", sys.executable)
    print_kv("os.getcwd()", os.getcwd())
    print_kv("TEMP", os.environ.get("TEMP", ""))
    print_kv("TMP", os.environ.get("TMP", ""))
    print_kv("Path.home()", Path.home())
    print_kv("tempfile.gettempdir()", tempfile.gettempdir())


def network_probe(url: str, phase: str, headers: dict | None = None, use_stream: bool = False) -> dict:
    print(f"[NETWORK] phase={phase}")
    print_kv("url", url)
    with requests.Session() as session:
        print_kv("requests.Session().trust_env", session.trust_env)
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        print_kv(key, os.environ.get(key, ""))
    print_runtime_env_snapshot()

    result = {
        "ok": False,
        "status_code": "",
        "content_length": "",
        "content_range": "",
        "final_url": "",
        "exception_type": "",
        "exception_message": "",
    }
    try:
        with requests.get(
            url,
            timeout=20,
            allow_redirects=True,
            headers=headers or {},
            stream=use_stream,
        ) as resp:
            result["ok"] = True
            result["status_code"] = str(resp.status_code)
            result["content_length"] = str(resp.headers.get("content-length", ""))
            result["content_range"] = str(resp.headers.get("content-range", ""))
            result["final_url"] = str(resp.url)
    except Exception as exc:
        result["exception_type"] = type(exc).__name__
        result["exception_message"] = str(exc)

    print_kv("status_code", result["status_code"])
    print_kv("content-length", result["content_length"])
    print_kv("content-range", result["content_range"])
    print_kv("final_url", result["final_url"])
    print_kv("exception_type", result["exception_type"])
    print_kv("exception_message", result["exception_message"])
    return result


def run_network_suite(phase_prefix: str) -> dict:
    manifest = network_probe(
        "https://models.datalab.to/layout/2025_09_23/manifest.json",
        phase=f"{phase_prefix}:manifest",
    )
    model_range = network_probe(
        "https://models.datalab.to/layout/2025_09_23/model.safetensors",
        phase=f"{phase_prefix}:model_range",
        headers={"Range": "bytes=0-1023"},
        use_stream=True,
    )
    return {
        "manifest": manifest,
        "range": model_range,
    }


def list_entries(base: Path, max_items: int) -> None:
    print(f"[SCAN] {base}")
    if not base.exists():
        print("  MISSING")
        return
    count = 0
    for p in sorted(base.rglob("*")):
        rel = str(p.relative_to(base))
        kind = "DIR " if p.is_dir() else "FILE"
        print(f"  [{kind}] {rel}")
        count += 1
        if count >= max_items:
            print(f"  ... truncated at {max_items} items")
            break


def load_runtime_modules():
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from config_manager import ConfigManager, DEFAULT_CONFIG
    from vision_runtime import build_vision_env

    return ConfigManager, DEFAULT_CONFIG, build_vision_env


def load_config():
    ConfigManager, DEFAULT_CONFIG, _ = load_runtime_modules()
    cfg = ConfigManager(config_path=str(PROJECT_ROOT / "config.yaml"))
    config = cfg.load()
    paths = config.get("paths", {})
    defaults = DEFAULT_CONFIG.get("paths", {})
    base_ai_path = paths.get("base_ai_path", defaults.get("base_ai_path", r"D:\_datefac\ai_models"))
    temp_cache_dir = paths.get("temp_cache_dir", defaults.get("temp_cache_dir", r"D:\_datefac\output\.temp_cache"))
    return config, base_ai_path, temp_cache_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Prewarm marker/surya models with TEMP/TMP diagnostics.")
    parser.add_argument(
        "--tmp-mode",
        choices=["default", "isolated-before-network", "isolated-before-model"],
        default="default",
        help="TEMP/TMP switch strategy for diagnostics.",
    )
    parser.add_argument(
        "--network-only",
        action="store_true",
        help="Only run env + network diagnostics; skip tmp creation, imports, and model loading.",
    )
    parser.add_argument(
        "--network-first-before-env",
        action="store_true",
        help="Run an initial network check before importing config_manager/vision_runtime or applying vision env.",
    )
    args = parser.parse_args()

    print_section("Startup")
    print_kv("tmp_mode", args.tmp_mode)
    print_kv("network_only", args.network_only)
    print_kv("network_first_before_env", args.network_first_before_env)

    if args.network_first_before_env:
        print_section("Network First Before Env")
        run_network_suite("before_env")

    _, base_ai_path, temp_cache_dir = load_config()
    _, _, build_vision_env = load_runtime_modules()
    env = build_vision_env(base_ai_path, temp_cache_dir)
    os.environ.update(env)
    print_tmp_phase("after_build_vision_env")

    print_section("Runtime")
    print_runtime_env_snapshot()
    for key in [
        "DATALAB_CACHE_DIR",
        "SURYA_CACHE_DIR",
        "HF_HOME",
        "HF_HUB_CACHE",
        "LOCALAPPDATA",
        "USERPROFILE",
        "HOME",
        "TEMP",
        "TMP",
    ]:
        print_kv(key, os.environ.get(key, ""))

    if args.network_only:
        print_section("Network Only")
        print_tmp_phase("before_network_precheck")
        net = run_network_suite("network_only_after_env")
        print_tmp_phase("after_network_precheck")
        print_kv("manifest_precheck_status", net["manifest"]["status_code"] or net["manifest"]["exception_type"])
        print_kv("range_precheck_status", net["range"]["status_code"] or net["range"]["exception_type"])
        print_kv("marker_import_ok", False)
        print_kv("surya_import_ok", False)
        print_kv("torch_import_ok", False)
        print_kv("create_model_dict_ok", False)
        return 0

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    prewarm_tmp = Path(base_ai_path) / "tmp" / f"prewarm_{ts}"
    prewarm_tmp.mkdir(parents=True, exist_ok=True)
    if args.tmp_mode == "isolated-before-network":
        os.environ["TEMP"] = str(prewarm_tmp)
        os.environ["TMP"] = str(prewarm_tmp)

    print_section("Network Precheck")
    print_tmp_phase("before_network_precheck")
    net = run_network_suite("prewarm")
    print_tmp_phase("after_network_precheck")
    print_kv("manifest_precheck_status", net["manifest"]["status_code"] or net["manifest"]["exception_type"])
    print_kv("range_precheck_status", net["range"]["status_code"] or net["range"]["exception_type"])

    winerror_10013 = False
    winerror_5 = False
    marker_import_ok = False
    surya_import_ok = False
    torch_import_ok = False
    create_model_dict_ok = False

    print_section("Import Packages")
    print_tmp_phase("before_import_packages")
    try:
        import marker  # type: ignore

        print_kv("marker.__file__", getattr(marker, "__file__", ""))
        marker_import_ok = True
    except Exception as exc:
        print_kv("marker_import_error", f"{type(exc).__name__}: {exc}")

    try:
        import surya  # type: ignore

        print_kv("surya.__file__", getattr(surya, "__file__", ""))
        surya_import_ok = True
    except Exception as exc:
        print_kv("surya_import_error", f"{type(exc).__name__}: {exc}")

    try:
        import torch  # type: ignore

        print_kv("torch.__file__", getattr(torch, "__file__", ""))
        torch_import_ok = True
    except Exception as exc:
        print_kv("torch_import_error", f"{type(exc).__name__}: {exc}")
    print_tmp_phase("after_import_packages")
    print_kv("marker_import_ok", marker_import_ok)
    print_kv("surya_import_ok", surya_import_ok)
    print_kv("torch_import_ok", torch_import_ok)

    print_section("Model Prewarm")
    if args.tmp_mode == "isolated-before-model":
        os.environ["TEMP"] = str(prewarm_tmp)
        os.environ["TMP"] = str(prewarm_tmp)
    print_tmp_phase("before_create_model_dict")
    try:
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict

        print("trigger=create_model_dict()")
        model_dict = create_model_dict()
        create_model_dict_ok = True
        print_kv("model_dict_type", type(model_dict).__name__)
        print("trigger=PdfConverter(artifact_dict=model_dict)")
        converter = PdfConverter(artifact_dict=model_dict)
        print_kv("converter_type", type(converter).__name__)
        print("prewarm_result=success")
    except Exception:
        tb = traceback.format_exc()
        print("prewarm_result=failed")
        print(tb)
        lower = tb.lower()
        winerror_10013 = "winerror 10013" in lower
        winerror_5 = "winerror 5" in lower
    finally:
        print_tmp_phase("after_create_model_dict_or_error")
        print_section("Error Flags")
        print_kv("create_model_dict_ok", create_model_dict_ok)
        print_kv("has_winerror_10013", winerror_10013)
        print_kv("has_winerror_5", winerror_5)
        print_kv("prewarm_tmp_dir", prewarm_tmp)

    print_section("Cache Snapshot")
    list_entries(Path(base_ai_path) / "datalab", max_items=200)
    list_entries(Path(base_ai_path) / "surya", max_items=200)
    list_entries(Path(base_ai_path) / "hf", max_items=200)
    list_entries(Path(base_ai_path) / "tmp", max_items=100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
