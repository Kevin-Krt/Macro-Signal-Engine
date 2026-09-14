import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_missing_required_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_DATABASE_URL", "postgresql://localhost:5432/test_db")
    monkeypatch.setenv("APP_REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("APP_FERNET_KEY", "fake-fernet-key-for-testing")
    monkeypatch.delenv("APP_JWT_SECRET", raising=False)

    with pytest.raises(ValidationError) as err:
        Settings(_env_file=None)

    errors = err.value.errors()
    assert any(e["loc"] == ("jwt_secret",) and e["type"] == "missing" for e in errors)
