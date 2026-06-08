import logging
import time
from uuid import uuid4

import consul

from shared.config import get_settings


logger = logging.getLogger("service-discovery")


class DiscoveryClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = consul.Consul(host=settings.consul_host, port=settings.consul_port)
        self._service_id: str | None = None

    def register(self, service_name: str, host: str, port: int) -> str | None:
        service_id = f"{service_name}-{uuid4()}"
        last_error: Exception | None = None
        for attempt in range(1, 6):
            try:
                self._client.agent.service.register(
                    name=service_name,
                    service_id=service_id,
                    address=host,
                    port=port,
                    token=None,
                )
                self._service_id = service_id
                logger.info("Registered with consul service_name=%s service_id=%s", service_name, service_id)
                return service_id
            except Exception as exc:  # pragma: no cover - infra dependent
                last_error = exc
                time.sleep(2)

        logger.warning("Consul registration failed for %s after retries: %s", service_name, last_error)
        return None

    def deregister(self) -> None:
        if not self._service_id:
            return
        try:
            self._client.agent.service.deregister(self._service_id)
            logger.info("Deregistered from consul service_id=%s", self._service_id)
        except Exception as exc:  # pragma: no cover - infra dependent
            logger.warning("Consul deregistration failed for %s: %s", self._service_id, exc)

    def discover(self, service_name: str) -> str | None:
        try:
            _, services = self._client.catalog.service(service_name)
            if not services:
                return None
            service = services[0]
            return f"http://{service['ServiceAddress']}:{service['ServicePort']}"
        except Exception as exc:  # pragma: no cover - infra dependent
            logger.warning("Consul discovery failed for %s: %s", service_name, exc)
            return None
