# API Endpoint Documentation

## Authentication

Gateway:
- POST /api/auth/login
- GET /api/auth/me
- GET /api/auth/validate

Auth service:
- POST /auth/login
- GET /auth/me
- GET /auth/validate

Sample login request:
{
  "username": "employee1",
  "password": "Password@123"
}

Sample login response:
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}

Sample validate response:
{
  "valid": true,
  "user": {
    "id": 2,
    "username": "employee1",
    "role": "Employee",
    "employee_name": "Bob Employee",
    "manager_id": 1
  }
}

## Employee APIs

Gateway:
- GET /api/employees/me
- GET /api/employees/{user_id}
- GET /api/managers/{manager_user_id}/team

Sample team response:
{
  "manager_user_id": 1,
  "members": [
    {
      "id": 2,
      "user_id": 2,
      "username": "employee1",
      "name": "Bob Employee",
      "role": "Employee",
      "manager_user_id": 1
    }
  ]
}

## Leave APIs

Gateway:
- GET /api/leave/balances
- POST /api/leave/apply
- GET /api/leave/manager/requests
- POST /api/leave/{request_id}/approve
- POST /api/leave/{request_id}/reject
- POST /api/leave/{request_id}/cancel
- GET /api/leave/history

Manager request filters:
- `status_filter` (Pending/Approved/Rejected/Cancelled)
- `employee_user_id`
- `start_date_from`
- `start_date_to`

Sample apply leave request:
{
  "leave_type": "Casual",
  "start_date": "2026-06-20",
  "end_date": "2026-06-21",
  "number_of_days": 2,
  "reason": "Family event",
  "reporting_manager_user_id": 1
}

Sample manager reject request:
{
  "comments": "Project deadline this week"
}

Sample cancel request:
{
  "comments": "Plan changed"
}

Sample leave request response:
{
  "id": 10,
  "employee_user_id": 2,
  "manager_user_id": 1,
  "leave_type": "Casual",
  "start_date": "2026-06-20",
  "end_date": "2026-06-21",
  "number_of_days": 2,
  "reason": "Family event",
  "status": "Pending",
  "rejection_reason": null,
  "created_at": "2026-06-08T17:00:00"
}

## Notification APIs

Gateway:
- POST /api/notifications/poll
- GET /api/notifications/poll-now

Notification service:
- POST /notifications/poll
- GET /notifications/poll-now

## Status Codes

- 200: successful read or action
- 201: leave request created
- 400: business validation failure
- 401: missing or invalid token
- 403: role or ownership forbidden
- 404: entity not found
- 503: downstream service unavailable

## Failure Scenarios To Validate

- Invalid credentials on login
- Missing JWT on protected routes
- Employee accessing another employee's data
- Manager accessing non-team employee data
- Apply leave with past date
- Apply leave with start date > end date
- Apply leave with insufficient balance
- Apply leave with overlapping dates
- Approve/reject non-pending request
