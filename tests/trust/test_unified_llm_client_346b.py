from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datefac.llm.client import extract_message_content  # noqa: E402
from datefac.llm.config import (  # noqa: E402
    resolve_ai_review_runtime_config,
    resolve_deepseek_runtime_config,
)
from datefac.llm.json_utils import parse_model_json  # noqa: E402
from datefac.trust.ai_review_model_ab_338b import (  # noqa: E402
    AIReviewRuntimeConfig as ABRuntimeConfig,
    AIReviewTextClient as ABClient,
    parse_model_json as parse_model_json_338b,
    resolve_runtime_config as resolve_runtime_config_338b,
)
from datefac.trust.deepseek_text_adjudicator_338a import (  # noqa: E402
    DeepSeekRuntimeConfig,
    DeepSeekTextClient,
    parse_model_json as parse_model_json_338a,
)
from datefac.trust.grounded_ai_review_338c import (  # noqa: E402
    AIReviewRuntimeConfig as GroundedRuntimeConfig,
    AIReviewTextClient as GroundedClient,
    parse_model_json as parse_model_json_338c,
    resolve_runtime_config as resolve_runtime_config_338c,
)


def test_parse_model_json_supports_raw_json() -> None:
    parsed, method = parse_model_json('{"decision":"CONFIRM_REVIEWED"}')
    assert parsed == {"decision": "CONFIRM_REVIEWED"}
    assert method == "raw_json"


def test_parse_model_json_repairs_fenced_json() -> None:
    parsed, method = parse_model_json("```json\n{\"decision\":\"REJECT\"}\n```")
    assert parsed == {"decision": "REJECT"}
    assert method == "fence_repair"


def test_parse_model_json_repairs_bracket_slice() -> None:
    parsed, method = parse_model_json("prefix {\"decision\":\"NEEDS_MORE_CONTEXT\"} suffix")
    assert parsed == {"decision": "NEEDS_MORE_CONTEXT"}
    assert method == "bracket_repair"


def test_extract_message_content_reads_openai_compatible_shape() -> None:
    content = extract_message_content(
        {
            "choices": [
                {
                    "message": {
                        "content": "  {\"ok\":true}\n"
                    }
                }
            ]
        }
    )
    assert content == '{"ok":true}'


def test_resolve_ai_review_runtime_config_prefers_ai_review_env() -> None:
    config, statuses = resolve_ai_review_runtime_config(
        {
            "AI_REVIEW_API_KEY": "ai-key",
            "AI_REVIEW_BASE_URL": "https://ai.example",
            "AI_MODEL": "ai-model",
            "DEEPSEEK_API_KEY": "deepseek-key",
            "DEEPSEEK_BASE_URL": "https://deepseek.example",
            "DEEPSEEK_MODEL": "deepseek-model",
        }
    )
    assert config is not None
    assert config.env_source == "AI_REVIEW"
    assert config.model == "ai-model"
    assert statuses["AI_REVIEW_API_KEY"] == "SET"


def test_resolve_ai_review_runtime_config_falls_back_to_deepseek() -> None:
    config, statuses = resolve_ai_review_runtime_config(
        {
            "DEEPSEEK_API_KEY": "deepseek-key",
            "DEEPSEEK_BASE_URL": "https://deepseek.example",
            "DEEPSEEK_MODEL": "deepseek-model",
        }
    )
    assert config is not None
    assert config.env_source == "DEEPSEEK_FALLBACK"
    assert config.model == "deepseek-model"
    assert statuses["DEEPSEEK_MODEL"] == "SET"


def test_resolve_deepseek_runtime_config_is_deepseek_only() -> None:
    config, statuses = resolve_deepseek_runtime_config(
        {
            "AI_REVIEW_API_KEY": "ai-key",
            "AI_REVIEW_BASE_URL": "https://ai.example",
            "AI_MODEL": "ai-model",
            "DEEPSEEK_API_KEY": "deepseek-key",
            "DEEPSEEK_BASE_URL": "https://deepseek.example",
            "DEEPSEEK_MODEL": "deepseek-model",
        }
    )
    assert config is not None
    assert config.env_source == "DEEPSEEK"
    assert config.model == "deepseek-model"
    assert statuses["DEEPSEEK_API_KEY"] == "SET"


def test_338a_338b_338c_parse_aliases_keep_shared_behavior() -> None:
    text = "```json\n{\"decision\":\"CONFIRM_REVIEWED\"}\n```"
    assert parse_model_json_338a(text)[1] == "fence_repair"
    assert parse_model_json_338b(text)[1] == "fence_repair"
    assert parse_model_json_338c(text)[1] == "fence_repair"


def test_338b_and_338c_runtime_resolvers_keep_compatibility() -> None:
    env = {
        "AI_REVIEW_API_KEY": "ai-key",
        "AI_REVIEW_BASE_URL": "https://ai.example",
        "AI_MODEL": "ai-model",
    }
    config_338b, _ = resolve_runtime_config_338b(env=env)
    config_338c, _ = resolve_runtime_config_338c(env=env)
    assert config_338b is not None
    assert config_338c is not None
    assert config_338b.env_source == "AI_REVIEW"
    assert config_338c.env_source == "AI_REVIEW"


def test_public_clients_still_construct() -> None:
    deepseek_client = DeepSeekTextClient(
        DeepSeekRuntimeConfig(
            api_key="k",
            base_url="https://deepseek.example",
            model="deepseek-model",
            timeout_seconds=5,
        )
    )
    ab_client = ABClient(
        ABRuntimeConfig(
            api_key="k",
            base_url="https://ai.example",
            model="ai-model",
            env_source="AI_REVIEW",
            timeout_seconds=5,
        )
    )
    grounded_client = GroundedClient(
        GroundedRuntimeConfig(
            api_key="k",
            base_url="https://ai.example",
            model="ai-model",
            env_source="AI_REVIEW",
            timeout_seconds=5,
        )
    )
    assert deepseek_client.config.model == "deepseek-model"
    assert ab_client.config.env_source == "AI_REVIEW"
    assert grounded_client.config.env_source == "AI_REVIEW"
