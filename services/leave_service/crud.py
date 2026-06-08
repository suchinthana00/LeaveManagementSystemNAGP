from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from services.leave_service.models import LeaveBalance, LeaveRequest


DEFAULT_ALLOCATIONS = {
    "Casual": 12,
    "Sick": 10,
    "Privilege": 15,
}


def seed_leave_balances(db: Session) -> None:
    if db.query(LeaveBalance).first():
        return

    for user_id in (2, 3):
        for leave_type, allocation in DEFAULT_ALLOCATIONS.items():
            db.add(
                LeaveBalance(
                    employee_user_id=user_id,
                    leave_type=leave_type,
                    allocated=allocation,
                    used=0,
                    remaining=allocation,
                )
            )
    db.commit()


def get_balances_for_user(db: Session, user_id: int) -> list[LeaveBalance]:
    statement = select(LeaveBalance).where(LeaveBalance.employee_user_id == user_id)
    return list(db.execute(statement).scalars().all())


def get_balance(db: Session, user_id: int, leave_type: str) -> LeaveBalance | None:
    statement = select(LeaveBalance).where(
        and_(LeaveBalance.employee_user_id == user_id, LeaveBalance.leave_type == leave_type)
    )
    return db.execute(statement).scalar_one_or_none()


def has_overlapping_request(db: Session, user_id: int, start_date: date, end_date: date) -> bool:
    statement = select(LeaveRequest).where(
        and_(
            LeaveRequest.employee_user_id == user_id,
            LeaveRequest.status.in_(["Pending", "Approved"]),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )
    )
    return db.execute(statement).scalar_one_or_none() is not None


def create_leave_request(db: Session, leave_request: LeaveRequest) -> LeaveRequest:
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    return leave_request


def get_request_by_id(db: Session, request_id: int) -> LeaveRequest | None:
    statement = select(LeaveRequest).where(LeaveRequest.id == request_id)
    return db.execute(statement).scalar_one_or_none()


def update_leave_request(db: Session, leave_request: LeaveRequest) -> LeaveRequest:
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    return leave_request


def get_manager_requests(db: Session, manager_user_id: int, status_filter: str | None = None) -> list[LeaveRequest]:
    statement = select(LeaveRequest).where(LeaveRequest.manager_user_id == manager_user_id)
    if status_filter:
        statement = statement.where(LeaveRequest.status == status_filter)
    statement = statement.order_by(LeaveRequest.created_at.desc())
    return list(db.execute(statement).scalars().all())


def get_manager_requests_filtered(
    db: Session,
    manager_user_id: int,
    status_filter: str | None,
    employee_user_id: int | None,
    start_date_from: date | None,
    start_date_to: date | None,
) -> list[LeaveRequest]:
    statement = select(LeaveRequest).where(LeaveRequest.manager_user_id == manager_user_id)
    if status_filter:
        statement = statement.where(LeaveRequest.status == status_filter)
    if employee_user_id is not None:
        statement = statement.where(LeaveRequest.employee_user_id == employee_user_id)
    if start_date_from is not None:
        statement = statement.where(LeaveRequest.start_date >= start_date_from)
    if start_date_to is not None:
        statement = statement.where(LeaveRequest.start_date <= start_date_to)
    statement = statement.order_by(LeaveRequest.created_at.desc())
    return list(db.execute(statement).scalars().all())


def get_leave_history(
    db: Session,
    employee_user_id: int,
    status_filter: str | None,
    page: int,
    page_size: int,
) -> list[LeaveRequest]:
    statement = select(LeaveRequest).where(LeaveRequest.employee_user_id == employee_user_id)
    if status_filter:
        statement = statement.where(LeaveRequest.status == status_filter)
    statement = statement.order_by(LeaveRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return list(db.execute(statement).scalars().all())
