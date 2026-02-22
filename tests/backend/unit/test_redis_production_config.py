from __future__ import annotations

import importlib


def test_build_redis_connection_options_includes_ca_cert_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SUPABASE_CA_CERT_PATH", "/etc/ssl/certs/supabase-ca.crt")

    redis_module = importlib.import_module("backend.src.core.redis")
    kwargs = redis_module.build_redis_connection_options(pool_size=20)

    assert kwargs["max_connections"] == 20
    assert kwargs["retry_on_timeout"] is True
    assert kwargs["decode_responses"] is True
    assert kwargs["ssl"] is True
    assert kwargs["ssl_ca_certs"] == "/etc/ssl/certs/supabase-ca.crt"


def test_build_redis_connection_options_defaults_without_ca_cert(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("SUPABASE_CA_CERT_PATH", raising=False)

    redis_module = importlib.import_module("backend.src.core.redis")
    kwargs = redis_module.build_redis_connection_options(pool_size=8)

    assert kwargs == {
        "max_connections": 8,
        "retry_on_timeout": True,
        "decode_responses": True,
    }
