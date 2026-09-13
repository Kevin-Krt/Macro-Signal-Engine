from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import HealthCheckError
from app.core.logging import RequestLoggingMiddleware, configure_logging
from app.modules.health.router import health_router

settings = get_settings()
configure_logging(
    json_logs=settings.log_format == "json",
    level=settings.log_level,
    log_sql=settings.log_sql,
)

app = FastAPI()
app.include_router(health_router, prefix="/api")
app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(HealthCheckError)
async def health_check_handler(
    request: Request, exc: HealthCheckError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "unavailable", "checks": exc.checks},
    )
