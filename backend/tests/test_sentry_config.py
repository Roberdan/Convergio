"""Tests for Sentry configuration and breadcrumb sanitization."""


def test_before_breadcrumb_strips_email_and_password():
    from core.sentry_config import before_breadcrumb

    breadcrumb = {
        "message": "Login failed for user alice@example.com",
        "data": {
            "email": "alice@example.com",
            "password": "super-secret",
            "detail": "kept",
        },
    }

    sanitized = before_breadcrumb(breadcrumb, {})

    assert sanitized is not None
    assert "email" not in sanitized["data"]
    assert "password" not in sanitized["data"]
    assert sanitized["data"]["detail"] == "kept"
    assert "alice@example.com" not in sanitized["message"]


def test_init_sentry_uses_env_dsn_and_environment(monkeypatch):
    import core.sentry_config as sentry_config

    calls = {}

    class DummySentry:
        @staticmethod
        def init(**kwargs):
            calls.update(kwargs)

    monkeypatch.setattr(sentry_config, "sentry_sdk", DummySentry)
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/12")
    monkeypatch.setenv("ENVIRONMENT", "staging")

    sentry_config.init_sentry()

    assert calls["dsn"] == "https://public@example.ingest.sentry.io/12"
    assert calls["environment"] == "staging"
    assert calls["before_breadcrumb"] is sentry_config.before_breadcrumb
