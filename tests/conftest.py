import pytest

from app.core.config import get_settings

TEST_JWT_SECRET = "test-secret-key-with-at-least-32-bytes!"


@pytest.fixture(autouse=True)
def test_env(monkeypatch: pytest.MonkeyPatch):
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    yield
    get_settings.cache_clear()
