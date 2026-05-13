import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict


VISION_ENV_KEYS = [
    "HF_HOME",
    "HF_HUB_CACHE",
    "TRANSFORMERS_CACHE",
    "HF_DATASETS_CACHE",
    "TORCH_HOME",
    "MARKER_MODEL_DIR",
    "DATALAB_CACHE_DIR",
    "DATALAB_HOME",
    "SURYA_CACHE_DIR",
    "XDG_CACHE_HOME",
    "LOCALAPPDATA",
    "APPDATA",
    "USERPROFILE",
    "HOME",
    "MPLCONFIGDIR",
    "TEMP",
    "TMP",
    "PYTHONUTF8",
    "PYTHONIOENCODING",
]


def build_vision_env(base_ai_path: str, cache_dir: str) -> Dict[str, str]:
    root = Path(base_ai_path).resolve()
    env = os.environ.copy()

    env_map = {
        "HF_HOME": str(root / "hf"),
        "HF_HUB_CACHE": str(root / "hf" / "hub"),
        "TRANSFORMERS_CACHE": str(root / "hf" / "transformers"),
        "HF_DATASETS_CACHE": str(root / "hf" / "datasets"),
        "TORCH_HOME": str(root / "torch"),
        "MARKER_MODEL_DIR": str(root / "marker"),
        "DATALAB_CACHE_DIR": str(root / "datalab"),
        "DATALAB_HOME": str(root / "datalab"),
        "SURYA_CACHE_DIR": str(root / "surya"),
        "XDG_CACHE_HOME": str(root / "xd"),
        "LOCALAPPDATA": str(root / "localappdata"),
        "APPDATA": str(root / "appdata"),
        "USERPROFILE": str(root / "userprofile"),
        "HOME": str(root / "home"),
        "MPLCONFIGDIR": str(root / "matplotlib"),
        "TEMP": str(root / "tmp"),
        "TMP": str(root / "tmp"),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    }

    for key in [
        "HF_HOME",
        "HF_HUB_CACHE",
        "TRANSFORMERS_CACHE",
        "HF_DATASETS_CACHE",
        "TORCH_HOME",
        "MARKER_MODEL_DIR",
        "DATALAB_CACHE_DIR",
        "DATALAB_HOME",
        "SURYA_CACHE_DIR",
        "XDG_CACHE_HOME",
        "LOCALAPPDATA",
        "APPDATA",
        "USERPROFILE",
        "HOME",
        "MPLCONFIGDIR",
        "TEMP",
        "TMP",
    ]:
        os.makedirs(env_map[key], exist_ok=True)

    os.makedirs(cache_dir, exist_ok=True)

    env.update(env_map)
    return env


def write_vision_env_diagnostics(env: Dict[str, str], cache_dir: str, phase: str) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    log_path = Path(cache_dir) / "vision_env_diagnostics.log"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] phase={phase}\n")
        for key in VISION_ENV_KEYS:
            f.write(f"{key}={env.get(key, '')}\n")
        f.write(f"pathlib.Path.home={Path.home()}\n")
        f.write(f"tempfile.gettempdir={tempfile.gettempdir()}\n")
        f.write(f"os.getcwd={os.getcwd()}\n")
        f.write("\n")
    return str(log_path)

