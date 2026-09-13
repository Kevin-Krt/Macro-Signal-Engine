import structlog
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from structlog.testing import capture_logs

from app.core.logging import RequestLoggingMiddleware


def make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    return app


async def test_request_produces_one_structured_log() -> None:
    transport = ASGITransport(app=make_app())
    with capture_logs(
        processors=[structlog.contextvars.merge_contextvars]
    ) as logs:
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/ping")

    access = [e for e in logs if e["event"] == "http_request"]
    assert len(access) == 1
    entry = access[0]
    assert entry["method"] == "GET"
    assert entry["path"] == "/ping"
    assert entry["status"] == 200
    assert entry["duration_ms"] >= 0
    assert entry["request_id"] == response.headers["x-request-id"]


async def test_valid_incoming_request_id_is_reused() -> None:
    transport = ASGITransport(app=make_app())
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get(
            "/ping", headers={"X-Request-ID": "abc-12345-def"}
        )
    assert response.headers["x-request-id"] == "abc-12345-def"


async def test_malicious_request_id_is_replaced() -> None:
    transport = ASGITransport(app=make_app())
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        response = await client.get(
            "/ping", headers={"X-Request-ID": "not a valid id!"}
        )
    assert response.headers["x-request-id"] != "not a valid id!"
    assert len(response.headers["x-request-id"]) == 32


async def test_server_error_is_logged_as_error() -> None:
    app = make_app()

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("kaboom")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    with capture_logs() as logs:
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/boom")

    assert response.status_code == 500
    access = [e for e in logs if e["event"] == "http_request"]
    assert access[0]["status"] == 500
    assert access[0]["log_level"] == "error"
