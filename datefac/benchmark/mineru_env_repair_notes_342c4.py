from __future__ import annotations

EXPECTED_CONDA_ENV = "mineru_new"
SAFE_HUGGINGFACE_HUB_VERSION = "0.36.2"
DISALLOWED_HUGGINGFACE_HUB_MAJOR = ">=1.0"
USER_SITE_POLLUTION_MARKER = r"AppData\Roaming\Python\Python312\site-packages"
RECOMMENDED_MINERU_COMMAND = (
    r"mineru -p E:\mineru_lab\input -o E:\mineru_lab\output_new -b pipeline --formula false --table true"
)

TASK_NOTES = [
    "342C4 repairs the MinerU environment instead of changing DateFac pipeline logic.",
    "The dominant failure is HuggingFace access during MinerU model initialization, not PDF parsing semantics.",
    "PYTHONNOUSERSITE=1 is required to block user site-packages pollution from AppData roaming paths.",
    "huggingface_hub must stay below 1.0 for the current MinerU-related transformers/tokenizers stack.",
    "verify=False is not a formal fix because it weakens SSL trust instead of repairing certificates or package provenance.",
    "client_ready remains false and production_ready remains false until MinerU pilot retry produces successful outputs.",
]

