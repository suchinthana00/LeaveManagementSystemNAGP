# Leave Management System Plan

## Goal

Build a backend-only microservices-based Leave Management System in the current workspace using Python, FastAPI, SQLite, RabbitMQ, Consul, Docker, and Docker Compose.

## Architecture Decisions

- Use FastAPI for all services, including the API gateway, to keep the stack consistent in Python.
- Use SQLite per service for simplicity while preserving service ownership boundaries.
- Use Consul as a real service discovery component from day one.
- Use RabbitMQ for asynchronous notification events.
- Implement JWT-based authentication with role-based authorization.
- Wire distributed tracing, structured logging, global exception handling, health checks, and circuit breaker behavior across services.
- Seed predefined managers and employees at startup so the system is demo-ready immediately.

## Main Components To Implement

### 1. API Gateway

Responsibilities:
- Single external entry point for all client requests
- Validate JWT on protected endpoints
- Route requests to downstream services using Consul discovery
- Forward correlation IDs and tracing headers
- Centralize request logging and error translation

Suggested location:
- `gateway/`

### 2. Auth Service

Responsibilities:
- Authenticate predefined users
- Generate JWT containing `userId`, `role`, and expiration
- Validate tokens for protected flows
- Store seeded user data and credentials in SQLite
- Expose internal token verification endpoint for other services if needed

Suggested location:
- `services/auth-service/`

### 3. Employee Service

Responsibilities:
- Manage employee profile data
- Store reporting manager mappings
- Support manager team lookup
- Enforce employee-self and manager-team access rules
- Support automatic leave balance initialization contract when employee data is created

Suggested location:
- `services/employee-service/`

### 4. Leave Service

Responsibilities:
- View leave balances by leave type
- Apply for leave with validation
- Prevent overlapping leave requests
- Validate date rules and leave balance sufficiency
- Store pending, approved, rejected, and cancelled leave requests
- Allow managers to approve or reject pending requests
- Deduct leave balance on approval
- Persist rejection reasons and comments
- Provide paginated leave history with filters

Suggested location:
- `services/leave-service/`

### 5. Notification Service

Responsibilities:
- Consume RabbitMQ events for leave applied, approved, rejected, and error scenarios
- Log structured notification entries for employees and managers
- Optionally persist notification records in SQLite for audit support

Suggested location:
- `services/notification-service/`

### 6. Shared Platform Library

Responsibilities:
- Common configuration loader
- JWT helper utilities
- Authorization dependencies and role checks
- Structured logging setup
- OpenTelemetry tracing setup
- Shared exception and error response models
- Circuit breaker wrapper for inter-service calls
- Health and readiness helpers
- Consul registration helper
- Shared HTTP client utilities

Suggested location:
- `shared/`

### 7. Infrastructure Components

Responsibilities:
- Dockerfiles for each service
- Root `docker-compose.yml` for all services and dependencies
- Consul container for discovery
- RabbitMQ container for messaging
- Persistent volumes for SQLite databases where needed
- Environment variable templates

Suggested location:
- Project root and `infra/`

### 8. Documentation And Delivery Assets

Responsibilities:
- README with setup and run instructions
- API endpoint documentation with request and response samples
- Architecture and inter-service communication writeup
- Postman collection JSON
- Docker image list placeholders
- Demo checklist and assumptions

Suggested location:
- `docs/` and project root

## Planned Folder Structure

```text
LeaveManagementSystemNAGP/
  gateway/
  services/
    auth-service/
    employee-service/
    leave-service/
    notification-service/
  shared/
  infra/
  docs/
  scripts/
  docker-compose.yml
  .env.example
  README.md
  plan.md
  assignment_guidance.md
```

## Implementation Phases

### Phase 1: Foundation

1. Create the workspace structure.
2. Add dependency management and base FastAPI application templates.
3. Build the shared library for config, auth, logging, tracing, errors, resilience, and discovery.
4. Add Dockerfiles and the root Docker Compose setup.
5. Bring up Consul and RabbitMQ with health checks.

### Phase 2: Core Business Services

1. Implement the Auth Service with seeded users and JWT issuance.
2. Implement the Employee Service with manager mappings and access control.
3. Implement the Leave Service with balances, requests, approvals, rejections, and history.
4. Implement the Notification Service with RabbitMQ consumers and structured logging.

### Phase 3: Gateway And Cross-Cutting Completion

1. Implement the API Gateway routing and JWT enforcement.
2. Register all services in Consul.
3. Enable tracing propagation across all services.
4. Add circuit breaker behavior for service-to-service HTTP calls.
5. Add consistent global exception handling and health endpoints everywhere.

### Phase 4: Documentation And Demo Readiness

1. Complete README and environment documentation.
2. Document APIs with request and response examples.
3. Create Postman collection entries for success and failure scenarios.
4. Write the architecture and inter-service communication notes.
5. Prepare demo steps covering auth, leave application, approval, rejection, notifications, and failure cases.

## Business Rules To Cover

- Predefined users can log in as Employee or Manager.
- JWT is mandatory for protected APIs.
- Employees can only access their own data.
- Managers can only access their team members' data.
- Default leave allocation on employee creation:
  - Casual Leave: 12
  - Sick Leave: 10
  - Privilege Leave: 15
- Leave application must validate:
  - start date is not in the past
  - start date is before or equal to end date
  - sufficient leave balance exists
  - no overlapping leave requests exist
- Manager approval deducts leave balance.
- Manager rejection stores rejection reason.
- Notifications must be produced for apply, approve, reject, and error scenarios.

## Verification Plan

1. Start the full stack with Docker Compose.
2. Verify all services register successfully in Consul.
3. Verify login returns a valid JWT with the required claims.
4. Verify protected endpoints reject missing, invalid, expired, or unauthorized tokens.
5. Test employee leave balance and leave application flows.
6. Test manager request view and approve or reject flows.
7. Verify notification logs are generated through RabbitMQ consumers.
8. Verify tracing and correlation IDs across gateway and services.
9. Verify circuit breaker behavior when a dependent service is unavailable.

## Immediate Build Order

1. Scaffold folders and shared dependencies.
2. Add shared auth, config, logging, tracing, and discovery helpers.
3. Implement Auth Service.
4. Implement Employee Service.
5. Implement Leave Service.
6. Implement Notification Service.
7. Implement API Gateway.
8. Add Compose, Dockerfiles, docs, and testing assets.