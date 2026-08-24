import importlib

import httpx
import pytest


def _reload_provider(monkeypatch, **env):
    for key in ("GROQ_API_KEY", "GROQ_MODEL", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    import src.llm.provider as provider

    importlib.reload(provider)
    return provider


def test_no_provider_configured(monkeypatch):
    provider = _reload_provider(monkeypatch)
    assert provider.active_provider() is None
    with pytest.raises(provider.LLMNotConfigured):
        provider.complete("system", "user")


def test_groq_takes_precedence_when_both_set(monkeypatch):
    provider = _reload_provider(monkeypatch, GROQ_API_KEY="groq-key", ANTHROPIC_API_KEY="anthropic-key")
    assert provider.active_provider() == "groq"


def test_anthropic_used_when_only_anthropic_set(monkeypatch):
    provider = _reload_provider(monkeypatch, ANTHROPIC_API_KEY="anthropic-key")
    assert provider.active_provider() == "anthropic"


def test_complete_calls_groq_chat_completions(monkeypatch):
    provider = _reload_provider(monkeypatch, GROQ_API_KEY="groq-key", GROQ_MODEL="llama-3.3-70b-versatile")

    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        request = httpx.Request("POST", url)
        return httpx.Response(200, json={"choices": [{"message": {"content": "hello from groq"}}]}, request=request)

    monkeypatch.setattr(provider.httpx, "post", fake_post)

    result = provider.complete("sys prompt", "user prompt", max_tokens=64)

    assert result == "hello from groq"
    assert captured["url"] == provider.GROQ_CHAT_URL
    assert captured["headers"]["Authorization"] == "Bearer groq-key"
    assert captured["json"]["model"] == "llama-3.3-70b-versatile"
    assert captured["json"]["messages"] == [
        {"role": "system", "content": "sys prompt"},
        {"role": "user", "content": "user prompt"},
    ]


def test_complete_raises_on_groq_http_error(monkeypatch):
    provider = _reload_provider(monkeypatch, GROQ_API_KEY="groq-key")

    def fake_post(url, headers=None, json=None, timeout=None):
        request = httpx.Request("POST", url)
        return httpx.Response(401, json={"error": "invalid api key"}, request=request)

    monkeypatch.setattr(provider.httpx, "post", fake_post)

    with pytest.raises(httpx.HTTPStatusError):
        provider.complete("sys", "user")
