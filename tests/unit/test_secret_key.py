import pytest

from backend.routes.auth import _load_secret_key


def test_uses_env_key_when_set(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "from-env")
    assert _load_secret_key() == "from-env"


def test_production_without_key_refuses_to_start(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("ENV", "production")
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        _load_secret_key()


def test_development_without_key_generates_random_key(monkeypatch, caplog):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("ENV", "development")
    first, second = _load_secret_key(), _load_secret_key()
    assert first != second
    assert len(first) >= 64
    assert "JWT_SECRET_KEY is not set" in caplog.text
