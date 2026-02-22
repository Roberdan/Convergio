from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.security_headers import SecurityHeadersMiddleware, get_allowed_origins


def test_get_allowed_origins_uses_env_whitelist():
    origins = get_allowed_origins(
        environment="production",
        allowed_origins_env="https://app.convergio.io, https://admin.convergio.io",
    )
    assert origins == ["https://app.convergio.io", "https://admin.convergio.io"]


def test_get_allowed_origins_rejects_wildcard_in_production():
    try:
        get_allowed_origins(environment="production", allowed_origins_env="*")
        assert False, "Expected ValueError when wildcard is used in production"
    except ValueError as exc:
        assert "Wildcard CORS" in str(exc)


def test_security_headers_include_csp_nonce_and_strict_dynamic():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, csp_report_uri="/csp-report")

    @app.get("/ping")
    def ping():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/ping")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in response.headers
    assert "Content-Security-Policy" in response.headers
    assert "strict-dynamic" in response.headers["Content-Security-Policy"]
    assert "nonce-" in response.headers["Content-Security-Policy"]
    assert "report-uri /csp-report" in response.headers["Content-Security-Policy"]
