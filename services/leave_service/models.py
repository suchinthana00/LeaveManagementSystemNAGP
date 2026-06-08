from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    __table_args__ = (UniqueConstraint("employee_user_id", "leave_type", name="uq_user_leave_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_user_id: Mapped[int] = mapped_column(index=True)
    leave_type: Mapped[str] = mapped_column(String(30), index=True)
    allocated: Mapped[int] = mapped_column(default=0)
    used: Mapped[int] = mapped_column(default=0)
    remaining: Mapped[int] = mapped_column(default=0)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_user_id: Mapped[int] = mapped_column(index=True)
    manager_user_id: Mapped[int] = mapped_column(index=True)
    leave_type: Mapped[str] = mapped_column(String(30), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    number_of_days: Mapped[int]
    reason: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), index=True, default="Pending")
    rejection_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
