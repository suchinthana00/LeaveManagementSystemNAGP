import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from shared.config import get_settings
from shared.discovery import DiscoveryClient
from shared.health import build_health_router
from shared.logging_utils import configure_logging


def create_app(service_name: str) -> FastAPI:
    settings = get_settings()
    configure_logging(service_name)
    app = FastAPI(title=service_name.replace("-", " ").title())
    app.include_router(build_health_router(service_name))

    discovery = DiscoveryClient()

    @app.on_event("startup")
    def register_service() -> None:
        host = settings.service_host
        # In containers, localhost/0.0.0.0 is not reachable from Consul's container.
        if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
            host = service_name
        discovery.register(service_name=service_name, host=host, port=settings.server_port)

    @app.on_event("shutdown")
    def deregister_service() -> None:
        discovery.deregister()

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next):
        correlation_id = request.headers.get("x-correlation-id") or str(uuid4())
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["x-correlation-id"] = correlation_id
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "service": service_name,
                "correlationId": getattr(request.state, "correlation_id", "n/a"),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logging.getLogger(service_name).exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "service": service_name,
                "correlationId": getattr(request.state, "correlation_id", "n/a"),
            },
        )

    return app
