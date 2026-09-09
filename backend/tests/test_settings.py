import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_missing_required_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost:5432/test_db")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("FERNET_KEY", "fake-fernet-key-for-testing")

    with pytest.raises(ValidationError) as err:
        Settings(_env_file=None)

    errors = err.value.errors()

    assert any(
        e["loc"] == ("jwt_secret",) and e["type"] == "missing" for e in errors
    )
