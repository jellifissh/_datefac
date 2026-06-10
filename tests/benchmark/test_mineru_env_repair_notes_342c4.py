from __future__ import annotations

from datefac.benchmark.mineru_env_repair_notes_342c4 import (
    DISALLOWED_HUGGINGFACE_HUB_MAJOR,
    RECOMMENDED_MINERU_COMMAND,
    SAFE_HUGGINGFACE_HUB_VERSION,
    TASK_NOTES,
    USER_SITE_POLLUTION_MARKER,
)


def test_safe_huggingface_hub_version() -> None:
    assert SAFE_HUGGINGFACE_HUB_VERSION == "0.36.2"


def test_disallowed_huggingface_hub_major_note() -> None:
    assert ">=1.0" in DISALLOWED_HUGGINGFACE_HUB_MAJOR


def test_recommended_mineru_command_shape() -> None:
    assert "mineru" in RECOMMENDED_MINERU_COMMAND
    assert "-b pipeline" in RECOMMENDED_MINERU_COMMAND
    assert "--formula false" in RECOMMENDED_MINERU_COMMAND
    assert "--table true" in RECOMMENDED_MINERU_COMMAND


def test_user_site_pollution_marker() -> None:
    assert "AppData" in USER_SITE_POLLUTION_MARKER


def test_notes_do_not_overclaim_readiness() -> None:
    joined = " ".join(TASK_NOTES).lower()
    assert "client_ready remains false" in joined
    assert "production_ready remains false" in joined
    assert "client_ready true" not in joined
    assert "production_ready true" not in joined

