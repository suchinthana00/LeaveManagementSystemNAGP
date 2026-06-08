from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
import httpx
from typing import Any

from shared.app_factory import create_app
from shared.config import get_settings
from shared.deps import get_current_user_token
from shared.discovery import DiscoveryClient
from shared.resilience import gateway_breaker


settings = get_settings()
app = create_app("gateway")
discovery = DiscoveryClient()


def resolve_service_base_urls(service_name: str, fallback: str) -> list[str]:
	discovered = discovery.discover(service_name)
	urls = [url for url in [discovered, fallback] if url]
	unique_urls: list[str] = []
	for url in urls:
		if url not in unique_urls:
			unique_urls.append(url)
	return unique_urls


def build_forward_headers(request: Request) -> dict[str, str]:
	headers: dict[str, str] = {}
	auth = request.headers.get("Authorization")
	if auth:
		headers["Authorization"] = auth

	correlation_id = request.headers.get("x-correlation-id") or getattr(request.state, "correlation_id", "")
	if correlation_id:
		headers["x-correlation-id"] = correlation_id
	return headers


async def proxy_request(
	request: Request,
	method: str,
	service_name: str,
	fallback_base: str,
	downstream_path: str,
) -> JSONResponse:
	headers = build_forward_headers(request)
	body: Any = None
	if method in {"POST", "PUT", "PATCH"}:
		try:
			body = await request.json()
		except Exception:
			body = None

	targets = resolve_service_base_urls(service_name, fallback_base)
	timeout = httpx.Timeout(connect=5.0, read=20.0, write=20.0, pool=20.0)
	last_error: httpx.HTTPError | None = None

	for base_url in targets:
		url = f"{base_url}{downstream_path}"
		try:
			async with httpx.AsyncClient(timeout=timeout) as client:
				request_obj = gateway_breaker.call(
					lambda: client.build_request(
						method,
						url,
						headers=headers,
						params=request.query_params,
						json=body,
					)
				)
				raw = await client.send(request_obj)
			try:
				content = raw.json()
			except ValueError:
				content = {"detail": raw.text}
			return JSONResponse(status_code=raw.status_code, content=content)
		except httpx.HTTPError as exc:
			last_error = exc
			continue

	if last_error is None:
		detail = "Downstream call failed: no target service URL available"
	else:
		error_name = type(last_error).__name__
		error_message = str(last_error) or repr(last_error)
		detail = f"Downstream call failed: {error_name}: {error_message}"
	raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


@app.post("/api/auth/login")
async def login(request: Request):
    return await proxy_request(request, "POST", "auth-service", settings.auth_service_url, "/auth/login")


@app.get("/api/auth/me")
async def me(request: Request, _: dict = Depends(get_current_user_token)):
    return await proxy_request(request, "GET", "auth-service", settings.auth_service_url, "/auth/me")


@app.get("/api/auth/validate")
async def validate(request: Request, _: dict = Depends(get_current_user_token)):
    return await proxy_request(request, "GET", "auth-service", settings.auth_service_url, "/auth/validate")


@app.get("/api/employees/me")
async def employee_me(request: Request, _: dict = Depends(get_current_user_token)):
    return await proxy_request(request, "GET", "employee-service", settings.employee_service_url, "/employees/me")


@app.get("/api/employees/{user_id}")
async def employee_by_id(user_id: int, request: Request, _: dict = Depends(get_current_user_token)):
	return await proxy_request(
		request,
		"GET",
		"employee-service",
		settings.employee_service_url,
		f"/employees/{user_id}",
	)


@app.get("/api/managers/{manager_user_id}/team")
async def manager_team(manager_user_id: int, request: Request, _: dict = Depends(get_current_user_token)):
	return await proxy_request(
		request,
		"GET",
		"employee-service",
		settings.employee_service_url,
		f"/managers/{manager_user_id}/team",
	)


@app.get("/api/leave/balances")
async def leave_balances(request: Request, _: dict = Depends(get_current_user_token)):
    return await proxy_request(request, "GET", "leave-service", settings.leave_service_url, "/leave/balances")


@app.post("/api/leave/apply")
async def leave_apply(request: Request, _: dict = Depends(get_current_user_token)):
    return await proxy_request(request, "POST", "leave-service", settings.leave_service_url, "/leave/apply")


@app.get("/api/leave/manager/requests")
async def leave_manager_requests(request: Request, _: dict = Depends(get_current_user_token)):
	return await proxy_request(
		request,
		"GET",
		"leave-service",
		settings.leave_service_url,
		"/leave/manager/requests",
	)


@app.post("/api/leave/{request_id}/approve")
async def leave_approve(request_id: int, request: Request, _: dict = Depends(get_current_user_token)):
	return await proxy_request(
		request,
		"POST",
		"leave-service",
		settings.leave_service_url,
		f"/leave/{request_id}/approve",
	)


@app.post("/api/leave/{request_id}/reject")
async def leave_reject(request_id: int, request: Request, _: dict = Depends(get_current_user_token)):
	return await proxy_request(
		request,
		"POST",
		"leave-service",
		settings.leave_service_url,
		f"/leave/{request_id}/reject",
	)


@app.post("/api/leave/{request_id}/cancel")
async def leave_cancel(request_id: int, request: Request, _: dict = Depends(get_current_user_token)):
	return await proxy_request(
		request,
		"POST",
		"leave-service",
		settings.leave_service_url,
		f"/leave/{request_id}/cancel",
	)


@app.get("/api/leave/history")
async def leave_history(request: Request, _: dict = Depends(get_current_user_token)):
    return await proxy_request(request, "GET", "leave-service", settings.leave_service_url, "/leave/history")


@app.post("/api/notifications/poll")
async def notifications_poll(request: Request, _: dict = Depends(get_current_user_token)):
	return await proxy_request(
		request,
		"POST",
		"notification-service",
		settings.notification_service_url,
		"/notifications/poll",
	)


@app.get("/api/notifications/poll-now")
async def notifications_poll_now(request: Request, token: dict = Depends(get_current_user_token)):
	if str(token.get("role")) != "Manager":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can trigger notification polling")
	return await proxy_request(
		request,
		"GET",
		"notification-service",
		settings.notification_service_url,
		"/notifications/poll-now",
	)
