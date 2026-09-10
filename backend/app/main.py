from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import HealthCheckError
from app.modules.health.router import health_router

app = FastAPI()
app.include_router(health_router, prefix="/api")


@app.exception_handler(HealthCheckError)
async def health_check_handler(
    request: Request, exc: HealthCheckError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "unavailable", "checks": exc.checks},
    )
