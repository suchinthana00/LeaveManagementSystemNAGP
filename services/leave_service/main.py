from datetime import date

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from services.leave_service import crud
from services.leave_service.events import publish_event
from services.leave_service.models import LeaveRequest
from services.leave_service.schemas import (
	ApplyLeaveRequest,
	CancelLeaveRequest,
	LeaveActionRequest,
	LeaveBalanceResponse,
	LeaveRequestResponse,
)
from shared.app_factory import create_app
from shared.config import get_settings
from shared.database import Base
from shared.db_utils import build_session_local
from shared.deps import get_current_user_token


settings = get_settings()
engine, SessionLocal = build_session_local(settings.database_url)
app = create_app("leave-service")


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


@app.on_event("startup")
def startup() -> None:
	Base.metadata.create_all(bind=engine)
	with SessionLocal() as db:
		crud.seed_leave_balances(db)


def to_leave_response(record: LeaveRequest) -> LeaveRequestResponse:
	return LeaveRequestResponse(
		id=record.id,
		employee_user_id=record.employee_user_id,
		manager_user_id=record.manager_user_id,
		leave_type=record.leave_type,
		start_date=record.start_date,
		end_date=record.end_date,
		number_of_days=record.number_of_days,
		reason=record.reason,
		status=record.status,
		rejection_reason=record.rejection_reason,
		created_at=record.created_at,
	)


@app.get("/leave/balances", response_model=list[LeaveBalanceResponse])
def get_my_leave_balances(token: dict = Depends(get_current_user_token), db: Session = Depends(get_db)):
	user_id = int(token["userId"])
	balances = crud.get_balances_for_user(db, user_id)
	return [
		LeaveBalanceResponse(
			leave_type=balance.leave_type,
			allocated=balance.allocated,
			used=balance.used,
			remaining=balance.remaining,
		)
		for balance in balances
	]


@app.post("/leave/apply", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def apply_leave(payload: ApplyLeaveRequest, token: dict = Depends(get_current_user_token), db: Session = Depends(get_db)):
	if str(token["role"]) != "Employee":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only employees can apply leave")

	user_id = int(token["userId"])
	reporting_manager_id = token.get("manager_id")
	if reporting_manager_id is not None and int(reporting_manager_id) != payload.reporting_manager_user_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reporting manager does not match employee mapping")
	today = date.today()
	if payload.start_date < today:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date cannot be in the past")
	if payload.start_date > payload.end_date:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date must be before or equal to end date")

	balance = crud.get_balance(db, user_id, payload.leave_type)
	if balance is None:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Leave type not configured")
	if balance.remaining < payload.number_of_days:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient leave balance")
	if crud.has_overlapping_request(db, user_id, payload.start_date, payload.end_date):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Overlapping leave request exists")

	request_record = LeaveRequest(
		employee_user_id=user_id,
		manager_user_id=payload.reporting_manager_user_id,
		leave_type=payload.leave_type,
		start_date=payload.start_date,
		end_date=payload.end_date,
		number_of_days=payload.number_of_days,
		reason=payload.reason,
		status="Pending",
	)
	created = crud.create_leave_request(db, request_record)

	publish_event(
		"LeaveApplied",
		{
			"leave_request_id": created.id,
			"employee_user_id": created.employee_user_id,
			"manager_user_id": created.manager_user_id,
			"status": created.status,
		},
	)
	return to_leave_response(created)


@app.get("/leave/manager/requests", response_model=list[LeaveRequestResponse])
def get_pending_manager_requests(
	token: dict = Depends(get_current_user_token),
	db: Session = Depends(get_db),
	status_filter: str | None = Query(default="Pending"),
	employee_user_id: int | None = Query(default=None),
	start_date_from: date | None = Query(default=None),
	start_date_to: date | None = Query(default=None),
):
	if str(token["role"]) != "Manager":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can view these requests")
	records = crud.get_manager_requests_filtered(
		db,
		manager_user_id=int(token["userId"]),
		status_filter=status_filter,
		employee_user_id=employee_user_id,
		start_date_from=start_date_from,
		start_date_to=start_date_to,
	)
	return [to_leave_response(record) for record in records]


@app.post("/leave/{request_id}/approve", response_model=LeaveRequestResponse)
def approve_leave(
	request_id: int,
	token: dict = Depends(get_current_user_token),
	db: Session = Depends(get_db),
):
	if str(token["role"]) != "Manager":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can approve requests")

	request_record = crud.get_request_by_id(db, request_id)
	if request_record is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
	if request_record.manager_user_id != int(token["userId"]):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your team member request")
	if request_record.status != "Pending":
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be approved")

	balance = crud.get_balance(db, request_record.employee_user_id, request_record.leave_type)
	if balance is None or balance.remaining < request_record.number_of_days:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient leave balance for approval")

	balance.used += request_record.number_of_days
	balance.remaining -= request_record.number_of_days
	request_record.status = "Approved"
	request_record.rejection_reason = None
	db.add(balance)
	updated = crud.update_leave_request(db, request_record)

	publish_event(
		"LeaveApproved",
		{
			"leave_request_id": updated.id,
			"employee_user_id": updated.employee_user_id,
			"manager_user_id": updated.manager_user_id,
			"status": updated.status,
		},
	)
	return to_leave_response(updated)


@app.post("/leave/{request_id}/reject", response_model=LeaveRequestResponse)
def reject_leave(
	request_id: int,
	payload: LeaveActionRequest,
	token: dict = Depends(get_current_user_token),
	db: Session = Depends(get_db),
):
	if str(token["role"]) != "Manager":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers can reject requests")

	request_record = crud.get_request_by_id(db, request_id)
	if request_record is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
	if request_record.manager_user_id != int(token["userId"]):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your team member request")
	if request_record.status != "Pending":
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending requests can be rejected")

	request_record.status = "Rejected"
	request_record.rejection_reason = payload.comments or "No comments"
	updated = crud.update_leave_request(db, request_record)

	publish_event(
		"LeaveRejected",
		{
			"leave_request_id": updated.id,
			"employee_user_id": updated.employee_user_id,
			"manager_user_id": updated.manager_user_id,
			"status": updated.status,
			"reason": updated.rejection_reason,
		},
	)
	return to_leave_response(updated)


@app.get("/leave/history", response_model=list[LeaveRequestResponse])
def leave_history(
	token: dict = Depends(get_current_user_token),
	db: Session = Depends(get_db),
	status_filter: str | None = Query(default=None),
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=10, ge=1, le=100),
):
	user_id = int(token["userId"])
	records = crud.get_leave_history(db, user_id, status_filter=status_filter, page=page, page_size=page_size)
	return [to_leave_response(record) for record in records]


@app.post("/leave/{request_id}/cancel", response_model=LeaveRequestResponse)
def cancel_leave(
	request_id: int,
	payload: CancelLeaveRequest,
	token: dict = Depends(get_current_user_token),
	db: Session = Depends(get_db),
):
	request_record = crud.get_request_by_id(db, request_id)
	if request_record is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
	if request_record.employee_user_id != int(token["userId"]):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can cancel only your own request")
	if request_record.status not in {"Pending", "Approved"}:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending or approved requests can be cancelled")

	if request_record.status == "Approved":
		balance = crud.get_balance(db, request_record.employee_user_id, request_record.leave_type)
		if balance is not None:
			balance.used -= request_record.number_of_days
			balance.remaining += request_record.number_of_days
			db.add(balance)

	request_record.status = "Cancelled"
	request_record.rejection_reason = payload.comments or "Cancelled by employee"
	updated = crud.update_leave_request(db, request_record)

	publish_event(
		"LeaveCancelled",
		{
			"leave_request_id": updated.id,
			"employee_user_id": updated.employee_user_id,
			"status": updated.status,
			"reason": updated.rejection_reason,
		},
	)
	return to_leave_response(updated)

