import importlib

import pytest


def _reload_main_under(monkeypatch, **env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import apps.api.config as config
    import apps.api.main as main

    importlib.reload(config)
    importlib.reload(main)
    return main


def test_production_with_default_secret_raises(monkeypatch):
    main = _reload_main_under(monkeypatch, ENVIRONMENT="production", SECRET_KEY="dev-secret-change-me", CORS_ALLOWED_ORIGINS="https://evolis.example")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        main._check_production_config()


def test_production_with_wildcard_cors_raises(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    main = _reload_main_under(monkeypatch, ENVIRONMENT="production", SECRET_KEY="a-real-secret")
    with pytest.raises(RuntimeError, match="CORS_ALLOWED_ORIGINS"):
        main._check_production_config()


def test_production_with_real_config_boots_clean(monkeypatch):
    main = _reload_main_under(
        monkeypatch, ENVIRONMENT="production", SECRET_KEY="a-real-secret", CORS_ALLOWED_ORIGINS="https://evolis.example"
    )
    main._check_production_config()  # must not raise


def test_development_never_raises(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    main = _reload_main_under(monkeypatch, ENVIRONMENT="development", SECRET_KEY="dev-secret-change-me")
    main._check_production_config()  # must not raise
