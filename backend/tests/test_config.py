"""Tests for the centralized, validated configuration module.

These exercise defaults, environment-variable overrides, and the derived
convenience properties on ``Settings``. Every test constructs its own
``Settings()`` (via ``get_settings()``) after adjusting the environment
with ``monkeypatch``, matching the pattern already used for
``LyzrGovernance`` in ``test_governance.py`` — this keeps the settings
object honest about live environment changes rather than caching a stale
snapshot.
"""

import pytest

from config import Settings, get_settings


def test_defaults_match_previous_os_getenv_fallbacks(monkeypatch):
    for name in (
        "LYZR_API_KEY",
        "LYZR_BASE_URL",
        "LYZR_CHAT_TIMEOUT",
        "LYZR_USE_SDK",
        "LYZR_SDK_FALLBACK",
        "LYZR_USER_ID",
        "BUYER_AGENT_ID",
        "SUPPLIER_AGENT_ID",
        "LYZR_GUARDRAIL_URL",
        "LYZR_GUARDRAIL_TOKEN",
        "LYZR_GOVERNANCE_TIMEOUT",
        "LYZR_RAI_POLICY_ID",
        "LYZR_RESPONSIBLE_AI_ENABLED",
        "LYZR_VERIFY_AGENT_FEATURES",
        "LYZR_AIMS_WEBHOOK_URL",
        "LYZR_AIMS_TOKEN",
        "LYZR_AIMS_OUTBOX",
        "CORS_ORIGINS",
        "PUBLIC_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = get_settings()

    assert settings.LYZR_API_KEY == ""
    assert settings.LYZR_BASE_URL == "https://agent-prod.studio.lyzr.ai"
    assert settings.LYZR_CHAT_TIMEOUT == 90.0
    assert settings.LYZR_USE_SDK == "1"
    assert settings.LYZR_SDK_FALLBACK == "1"
    assert settings.LYZR_USER_ID == "buyer-system"
    assert settings.BUYER_AGENT_ID == ""
    assert settings.SUPPLIER_AGENT_ID == ""
    assert settings.LYZR_GUARDRAIL_URL == ""
    assert settings.LYZR_GOVERNANCE_TIMEOUT == 8.0
    assert settings.LYZR_AIMS_OUTBOX == "data/aims_outbox.jsonl"
    assert settings.CORS_ORIGINS == "*"
    assert settings.PUBLIC_BASE_URL == ""


def test_env_overrides_are_picked_up(monkeypatch):
    monkeypatch.setenv("LYZR_BASE_URL", "https://example.test")
    monkeypatch.setenv("LYZR_CHAT_TIMEOUT", "12.5")
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example, https://b.example")

    settings = get_settings()

    assert settings.LYZR_BASE_URL == "https://example.test"
    assert settings.LYZR_CHAT_TIMEOUT == 12.5
    assert settings.cors_origin_list == ["https://a.example", "https://b.example"]


def test_get_settings_is_not_cached_and_reflects_live_changes(monkeypatch):
    monkeypatch.delenv("BUYER_AGENT_ID", raising=False)
    first = get_settings()
    assert first.BUYER_AGENT_ID == ""

    monkeypatch.setenv("BUYER_AGENT_ID", "buyer-123")
    second = get_settings()
    assert second.BUYER_AGENT_ID == "buyer-123"

    # The first instance is a snapshot in time and is not retroactively
    # mutated; a fresh call is required to observe the change.
    assert first.BUYER_AGENT_ID == ""


def test_sdk_preferred_matches_exact_string_comparison(monkeypatch):
    monkeypatch.setenv("LYZR_USE_SDK", "1")
    assert get_settings().sdk_preferred is True

    monkeypatch.setenv("LYZR_USE_SDK", "0")
    assert get_settings().sdk_preferred is False

    # Historical behavior: only the exact string "1" counts as enabled,
    # so an unexpected truthy-looking value like "true" is treated the
    # same as "off" — preserved here rather than "improved" so behavior
    # does not silently change for existing deployments.
    monkeypatch.setenv("LYZR_USE_SDK", "true")
    assert get_settings().sdk_preferred is False


def test_studio_agents_configured_requires_both_ids(monkeypatch):
    monkeypatch.delenv("BUYER_AGENT_ID", raising=False)
    monkeypatch.delenv("SUPPLIER_AGENT_ID", raising=False)
    assert get_settings().studio_agents_configured is False

    monkeypatch.setenv("BUYER_AGENT_ID", "buyer-1")
    assert get_settings().studio_agents_configured is False

    monkeypatch.setenv("SUPPLIER_AGENT_ID", "supplier-1")
    assert get_settings().studio_agents_configured is True


def test_lyzr_api_key_configured_strips_whitespace(monkeypatch):
    monkeypatch.setenv("LYZR_API_KEY", "   ")
    assert get_settings().lyzr_api_key_configured is False

    monkeypatch.setenv("LYZR_API_KEY", " sk-test ")
    assert get_settings().lyzr_api_key_configured is True


def test_aims_and_governance_configured_flags(monkeypatch):
    monkeypatch.delenv("LYZR_GUARDRAIL_URL", raising=False)
    monkeypatch.delenv("LYZR_AIMS_WEBHOOK_URL", raising=False)
    settings = get_settings()
    assert settings.responsible_ai_endpoint_configured is False
    assert settings.aims_sink_configured is False

    monkeypatch.setenv("LYZR_GUARDRAIL_URL", "https://guardrail.example")
    monkeypatch.setenv("LYZR_AIMS_WEBHOOK_URL", "https://aims.example")
    settings = get_settings()
    assert settings.responsible_ai_endpoint_configured is True
    assert settings.aims_sink_configured is True


def test_invalid_numeric_timeout_raises_at_construction(monkeypatch):
    monkeypatch.setenv("LYZR_CHAT_TIMEOUT", "not-a-number")
    with pytest.raises(Exception):
        Settings()


def test_non_positive_timeout_is_rejected(monkeypatch):
    monkeypatch.setenv("LYZR_GOVERNANCE_TIMEOUT", "0")
    with pytest.raises(Exception):
        Settings()
