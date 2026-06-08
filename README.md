# Leave Management System

Backend-only microservices leave management system built with Python, FastAPI, SQLite, RabbitMQ, Consul, Docker, and Docker Compose.

## Repository

- GitHub repository link: https://github.com/suchinthana00/LeaveManagementSystemNAGP

## Current Status

- Root project structure created
- Shared FastAPI foundation created
- Auth service implemented with seeded users and JWT login
- Auth token validation endpoint implemented
- Employee service implemented with manager-team access rules
- Leave service implemented with balances, apply, manager review with filters, approve/reject, cancel, and history
- Notification service implemented with RabbitMQ polling and structured logging
- API gateway implemented with route proxying to downstream services
- Consul service registration and gateway discovery fallback implemented
- Global exception handling and correlation ID middleware implemented
- Gateway circuit breaker behavior enabled for downstream calls

## Services

- API gateway
- Auth service
- Employee service
- Leave service
- Notification service

## Docker Image Strategy

- Yes, every service has its own Dockerfile:
	- `gateway/Dockerfile`
	- `services/auth_service/Dockerfile`
	- `services/employee_service/Dockerfile`
	- `services/leave_service/Dockerfile`
	- `services/notification_service/Dockerfile`
- All service images use the same root `requirements.txt`.
- This is a valid and common pattern for microservices when dependencies overlap.
- If needed later, we can split per-service requirements for smaller images.

## Run Approach

1. `.env` is also commited only because it contains generic values.
2. Build and start containers:
	 - `docker compose up --build`
3. Access services:
	 - Gateway: `http://localhost:9000/docs`
	 - Auth service: `http://localhost:9001/docs`
	 - Employee service: `http://localhost:9002/docs`
	 - Leave service: `http://localhost:9003/docs`
	 - Notification service: `http://localhost:9004/docs`
	 - Consul UI: `http://localhost:8501`
	 - RabbitMQ UI: `http://localhost:15678`

## Environment Variables

- `ENVIRONMENT` default `development`
- `JWT_SECRET` secret for signing JWT tokens
- `JWT_ALGORITHM` default `HS256`
- `JWT_EXPIRY_MINUTES` token validity in minutes
- `CONSUL_HOST` service discovery host
- `CONSUL_PORT` service discovery port
- `RABBITMQ_HOST` broker host for service-to-service messaging
- `RABBITMQ_PORT` broker port used internally by services
- `RABBITMQ_QUEUE` queue name for leave notification events
- `RABBITMQ_HOST_PORT` host port mapped to RabbitMQ container `5672`
- `RABBITMQ_MANAGEMENT_HOST_PORT` host port mapped to RabbitMQ UI `15672`
- `GATEWAY_HOST_PORT` host port mapped to gateway `8000`
- `AUTH_HOST_PORT` host port mapped to auth service `8001`
- `EMPLOYEE_HOST_PORT` host port mapped to employee service `8002`
- `LEAVE_HOST_PORT` host port mapped to leave service `8003`
- `NOTIFICATION_HOST_PORT` host port mapped to notification service `8004`
- `AUTH_SERVICE_URL` fallback internal URL for gateway routing
- `EMPLOYEE_SERVICE_URL` fallback internal URL for gateway routing
- `LEAVE_SERVICE_URL` fallback internal URL for gateway routing
- `NOTIFICATION_SERVICE_URL` fallback internal URL for gateway routing

Default host port mapping for this project uses gateway/service ports `9000-9004`, Consul `8501`, and RabbitMQ `5678/15678` to avoid collisions with other local stacks.
Consul host UI port is configurable with `CONSUL_HOST_PORT` (default `8501` in `.env.example`) to avoid collisions on `8500`.

Temporary conflict-free startup command (recommended when your machine has existing local stacks):
	- `CONSUL_HOST_PORT=8501 GATEWAY_HOST_PORT=9000 AUTH_HOST_PORT=9001 EMPLOYEE_HOST_PORT=9002 LEAVE_HOST_PORT=9003 NOTIFICATION_HOST_PORT=9004 RABBITMQ_HOST_PORT=5678 RABBITMQ_MANAGEMENT_HOST_PORT=15678 docker compose up -d`

If a service fails during startup after dependency changes, please run:
	- `docker compose down`
	- `docker compose build --no-cache`
	- `docker compose up`

Useful checks:
	- `docker compose ps`
	- `docker compose logs auth-service --tail=200`
	- `curl http://localhost:8001/health`

## API Testing Instructions

1. Import Postman collection from `docs/postman_collection.json`.
2. Set `baseUrl` variable to `http://localhost:8000`.
3. Run `Auth - Login (Employee)` and copy `access_token` to `employeeToken`.
4. Run `Auth - Login (Manager)` and copy `access_token` to `managerToken`.
5. Execute employee flow requests followed by manager flow requests.
6. Execute negative/failure scenarios for validation and authorization.

## Quick API Smoke Flow (via Gateway)

1. Login:
	- `POST /api/auth/login`
2. Get profile:
	- `GET /api/auth/me`
3. Employee leave actions:
	- `GET /api/leave/balances`
	- `POST /api/leave/apply`
	- `GET /api/leave/history`
	- `POST /api/leave/{request_id}/cancel`
4. Manager actions:
	- `GET /api/managers/{manager_user_id}/team`
	- `GET /api/leave/manager/requests?status_filter=Pending&employee_user_id=2`
	- `POST /api/leave/{request_id}/approve`
	- `POST /api/leave/{request_id}/reject`
5. Notification polling:
	- `GET /api/notifications/poll-now` (manager)

## Seeded Credentials

- Manager:
	- username: `manager1`
	- password: `Password@123`
- Employees:
	- username: `employee1`, password: `Password@123`
	- username: `employee2`, password: `Password@123`

## Docker Hub Image Paths

Fill these after pushing images:
- `suchinthana/leavemanagement-auth-service:latest`
- `suchinthana/leavemanagement-employee-service:latest`
- `suchinthana/leavemanagement-leave-service:latest`
- `suchinthana/leavemanagement-notification-service:latest`
- `suchinthana/leavemanagement-gateway:latest`

## Demo Video

- Demo recording Link: [Link](https://github.com/suchinthana00/LeaveManagementSystemNAGP/raw/refs/heads/main/Video%20Demo.mp4 "Download video")