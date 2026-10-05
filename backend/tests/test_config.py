"""Unit tests for backend/ichnoscope/config.py."""

import pytest
from ichnoscope.config import ConfigError, get_settings, load_settings


def test_config_defaults():
    settings = load_settings({})
    assert settings.dry_run is True
    assert settings.window_hours == 24
    assert settings.p1_users == 50
    assert settings.p1_events == 100
    assert settings.p2_users == 10
    assert settings.p2_events == 20
    assert settings.use_stub_github is False
    assert settings.use_stub_llm is False
    assert settings.path_prefix_strip == ""
    assert settings.github_token is None
    assert settings.github_repository is None
    assert settings.github_owner is None
    assert settings.github_repo_name is None


def test_bool_parsing():
    for val in ("TRUE", "1", "yes", "on", "True", "YES"):
        settings = load_settings({"DRY_RUN": val})
        assert settings.dry_run is True

    for val in ("false", "0", "no", "off", "FALSE", "No"):
        settings = load_settings({"DRY_RUN": val})
        assert settings.dry_run is False

    with pytest.raises(ConfigError) as exc_info:
        load_settings({"DRY_RUN": "maybe"})
    assert "DRY_RUN" in str(exc_info.value)


def test_int_parsing():
    with pytest.raises(ConfigError) as exc_info:
        load_settings({"P1_USERS": "abc"})
    assert "P1_USERS" in str(exc_info.value)

    with pytest.raises(ConfigError) as exc_info:
        load_settings({"WINDOW_HOURS": "0"})
    assert "WINDOW_HOURS" in str(exc_info.value)

    with pytest.raises(ConfigError) as exc_info:
        load_settings({"P1_USERS": "50", "P2_USERS": "60"})
    assert "P2_USERS" in str(exc_info.value)
    assert "P1_USERS" in str(exc_info.value)


def test_repo_parsing():
    settings = load_settings({"GITHUB_REPOSITORY": "octo/app"})
    assert settings.github_owner == "octo"
    assert settings.github_repo_name == "app"

    for invalid_repo in ("octo", "a/b/c", "/app"):
        with pytest.raises(ConfigError):
            load_settings({"GITHUB_REPOSITORY": invalid_repo})


def test_path_prefix_normalization():
    settings = load_settings({"PATH_PREFIX_STRIP": "/app"})
    assert settings.path_prefix_strip == "/app/"

    settings_empty = load_settings({"PATH_PREFIX_STRIP": ""})
    assert settings_empty.path_prefix_strip == ""

    settings_already_slashed = load_settings({"PATH_PREFIX_STRIP": "/app/"})
    assert settings_already_slashed.path_prefix_strip == "/app/"


def test_secrets_redaction():
    secret_token = "ghp_SECRET123"
    settings = load_settings({"GITHUB_TOKEN": secret_token})

    # repr and str must not expose the secret
    assert secret_token not in repr(settings)
    assert secret_token not in str(settings)

    summary = settings.safe_summary()
    assert secret_token not in str(summary)
    assert summary["github_token"] == "configured"
    assert summary["sentry_client_secret"] == "missing"


def test_llm_chain():
    # groq and gemini configured, priority order groq first
    env = {
        "LLM_CHAIN": "groq,gemini",
        "GROQ_API_KEY": "gsk_123",
        "GROQ_MODEL": "llama-3.3-70b-versatile",
        "GEMINI_API_KEY": "gem_123",
        "GEMINI_MODEL": "gemini-2.0-flash",
    }
    settings = load_settings(env)
    providers = settings.llm_providers()
    assert len(providers) == 2
    assert providers[0].name == "groq"
    assert providers[0].model == "llama-3.3-70b-versatile"
    assert providers[1].name == "gemini"

    # Provider with missing model is skipped and appears in llm_skipped
    env_missing_model = {
        "LLM_CHAIN": "groq",
        "GROQ_API_KEY": "gsk_123",
    }
    settings_missing = load_settings(env_missing_model)
    assert len(settings_missing.llm_providers()) == 0
    skipped = settings_missing.llm_skipped()
    assert "groq" in skipped
    assert "missing GROQ_MODEL" in skipped["groq"]

    # ollama is usable with only a model set (no key needed, default base URL exists)
    env_ollama = {
        "LLM_CHAIN": "ollama",
        "OLLAMA_MODEL": "deepseek-r1:8b",
    }
    settings_ollama = load_settings(env_ollama)
    ollama_providers = settings_ollama.llm_providers()
    assert len(ollama_providers) == 1
    assert ollama_providers[0].name == "ollama"
    assert ollama_providers[0].base_url == "http://localhost:11434/v1"

    # pollinations is skipped when its base URL is missing
    env_pollinations = {
        "LLM_CHAIN": "pollinations",
        "POLLINATIONS_MODEL": "mistral",
    }
    settings_pollinations = load_settings(env_pollinations)
    assert len(settings_pollinations.llm_providers()) == 0
    assert settings_pollinations.llm_skipped()["pollinations"] == "no base URL"

    # Unknown name in LLM_CHAIN raises ConfigError
    with pytest.raises(ConfigError) as exc_info:
        load_settings({"LLM_CHAIN": "groq,unknown_llm"})
    assert "unknown_llm" in str(exc_info.value)


def test_missing_for_pipeline():
    # Empty settings -> requires GitHub vars and LLM provider
    settings_empty = load_settings({})
    missing = settings_empty.missing_for_pipeline()
    assert "GITHUB_TOKEN" in missing
    assert "GITHUB_REPOSITORY" in missing
    assert "LLM_CHAIN (no usable provider)" in missing

    # Both stubs True -> empty list
    settings_stubs = load_settings({
        "USE_STUB_GITHUB": "true",
        "USE_STUB_LLM": "true",
    })
    assert settings_stubs.missing_for_pipeline() == []


def test_no_import_time_reads_and_cache(monkeypatch):
    # Ensure importing/accessing get_settings doesn't require env
    get_settings.cache_clear()
    monkeypatch.setenv("WINDOW_HOURS", "48")

    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    assert s1.window_hours == 48

    # Changing environment and clearing cache returns a new instance
    monkeypatch.setenv("WINDOW_HOURS", "72")
    get_settings.cache_clear()
    s3 = get_settings()
    assert s3 is not s1
    assert s3.window_hours == 72
    get_settings.cache_clear()
