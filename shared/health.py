from fastapi import APIRouter


def build_health_router(service_name: str) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"service": service_name, "status": "ok"}

    return router
