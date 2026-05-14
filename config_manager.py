import copy
import json
import os
from typing import Any, Dict

try:
    import yaml
except ImportError:  # pragma: no cover - depends on local environment
    yaml = None


DEFAULT_CONFIG: Dict[str, Any] = {
    "paths": {
        "base_ai_path": r"D:\_datefac\ai_models",
        "input_dir": r"D:\_datefac\input",
        "output_dir": r"D:\_datefac\output",
        "temp_cache_dir": r"D:\_datefac\output\.temp_cache",
    },
    "ollama": {
        "url": "http://localhost:11434/api/generate",
        "model": "my-brain",
        "timeout": 400,
    },
    "runtime": {
        "require_cuda": True,
        "keep_markdown_cache": True,
        "overwrite_output": False,
        "reuse_vision_cache": False,
        "markdown_replay_mode": False,
        "markdown_replay_dir": "",
    },
    "table_cleaning": {
        "enabled": True,
        "strict_dedup": True,
        "log_detail": True,
        "explain": False,
        "explain_sample_limit": 20,
    },
    "table_classification": {
        "enabled": True,
        "output_report": True,
        "min_confidence": 0.25,
        "log_detail": True,
    },
    "financial_standardization": {
        "enabled": True,
        "output_report": True,
        "log_detail": True,
    },
    "table_extraction": {
        "preferred_backend": "pdfplumber",
        "pdfplumber_enabled": True,
        "fallback_to_marker": True,
        "output_raw_marker_tables": False,
        "min_pdfplumber_tables": 1,
        "add_index_sheet": True,
        "sheet_name_strategy": "page_table",
        "merge_diagnostics_enabled": True,
        "output_merge_diagnostics": True,
        "pdfplumber_quality_gate": True,
        "pdfplumber_min_quality_score": 0.5,
        "pdfplumber_min_valid_tables": 1,
    },
    "pdfplumber_profiles": {
        "enabled": True,
        "fallback_enabled": True,
        "profiles": ["default", "text_text", "text_lines"],
        "fallback_min_good_tables": 1,
        "fallback_trigger_if_table_count_lt": 3,
        "fallback_trigger_if_all_bad": True,
        "output_profile_diagnostics": True,
    },
    "glued_table_splitter": {
        "enabled": True,
        "append_split_tables": True,
        "min_col_count": 10,
        "min_row_count": 10,
        "trigger_flags": ["possible_glued_table"],
        "output_diagnostics": True,
        "max_split_tables_per_source": 5,
    },
    "table_segmentation": {
        "enabled": True,
        "apply_to_backend": "marker",
        "min_rows_for_segmentation": 20,
        "add_index_sheet": True,
        "log_detail": True,
        "coalesce_enabled": True,
        "coalesce_same_type": True,
        "coalesce_ratio_sections": True,
        "min_rows_for_standalone_segment": 3,
    },
    "segment_validation": {
        "enabled": True,
        "output_report": True,
        "pollution_warning_threshold": 2,
        "log_detail": True,
    },
    "extractor_probe": {
        "enabled": True,
        "backends": ["pdfplumber", "marker", "docling"],
        "output_report": True,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = copy.deepcopy(DEFAULT_CONFIG)
        self.loaded_from_file = False
        self.load_warning = ""

    def load(self) -> Dict[str, Any]:
        file_config = {}
        if os.path.exists(self.config_path):
            try:
                file_config = self._read_config_file(self.config_path)
                self.loaded_from_file = True
            except Exception as exc:
                self.load_warning = f"读取配置文件失败，已回退默认配置: {exc}"
        self.config = _deep_merge(DEFAULT_CONFIG, file_config)
        self._normalize_paths()
        return self.config

    def _read_config_file(self, path: str) -> Dict[str, Any]:
        if path.lower().endswith(".json"):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f) or {}

        if yaml is None:
            raise RuntimeError("未安装 PyYAML，无法读取 YAML 配置。可执行 `pip install pyyaml`。")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError("配置文件根节点必须是对象/映射。")
        return data

    def _normalize_paths(self) -> None:
        paths = self.config.setdefault("paths", {})
        output_dir = paths.get("output_dir", DEFAULT_CONFIG["paths"]["output_dir"])
        paths.setdefault("base_ai_path", DEFAULT_CONFIG["paths"]["base_ai_path"])
        paths.setdefault("input_dir", DEFAULT_CONFIG["paths"]["input_dir"])
        paths.setdefault("output_dir", output_dir)
        paths.setdefault("temp_cache_dir", os.path.join(output_dir, ".temp_cache"))
        paths["logs_dir"] = os.path.join(paths["output_dir"], "logs")

    def ensure_directories(self) -> None:
        paths = self.config["paths"]
        for key in ("base_ai_path", "input_dir", "output_dir", "temp_cache_dir", "logs_dir"):
            os.makedirs(paths[key], exist_ok=True)

    def apply_environment(self) -> None:
        base_ai_path = self.config["paths"]["base_ai_path"]
        env_map = {
            "HF_HOME": os.path.join(base_ai_path, "hf"),
            "HF_HUB_CACHE": os.path.join(base_ai_path, "hf", "hub"),
            "TORCH_HOME": os.path.join(base_ai_path, "torch"),
            "MARKER_MODEL_DIR": os.path.join(base_ai_path, "marker"),
            "DATALAB_CACHE_DIR": os.path.join(base_ai_path, "datalab"),
            "DATALAB_HOME": os.path.join(base_ai_path, "datalab"),
            "SURYA_CACHE_DIR": os.path.join(base_ai_path, "surya"),
            "XDG_CACHE_HOME": os.path.join(base_ai_path, "xd"),
            "LOCALAPPDATA": os.path.join(base_ai_path, "localappdata"),
        }
        for path in env_map.values():
            os.makedirs(path, exist_ok=True)
        for k, v in env_map.items():
            os.environ[k] = v

    def build_summary(self) -> Dict[str, Any]:
        return {
            "config_path": self.config_path,
            "loaded_from_file": self.loaded_from_file,
            "load_warning": self.load_warning,
            "paths": self.config.get("paths", {}),
            "ollama": self.config.get("ollama", {}),
            "runtime": self.config.get("runtime", {}),
            "table_cleaning": self.config.get("table_cleaning", {}),
            "table_classification": self.config.get("table_classification", {}),
            "financial_standardization": self.config.get("financial_standardization", {}),
            "table_extraction": self.config.get("table_extraction", {}),
            "pdfplumber_profiles": self.config.get("pdfplumber_profiles", {}),
            "glued_table_splitter": self.config.get("glued_table_splitter", {}),
            "table_segmentation": self.config.get("table_segmentation", {}),
            "segment_validation": self.config.get("segment_validation", {}),
            "extractor_probe": self.config.get("extractor_probe", {}),
        }
