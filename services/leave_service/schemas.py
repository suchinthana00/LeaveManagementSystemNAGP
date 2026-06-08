from datetime import date, datetime

from pydantic import BaseModel, Field


class LeaveBalanceResponse(BaseModel):
    leave_type: str
    allocated: int
    used: int
    remaining: int


class ApplyLeaveRequest(BaseModel):
    leave_type: str = Field(min_length=1)
    start_date: date
    end_date: date
    number_of_days: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=300)
    reporting_manager_user_id: int


class LeaveRequestResponse(BaseModel):
    id: int
    employee_user_id: int
    manager_user_id: int
    leave_type: str
    start_date: date
    end_date: date
    number_of_days: int
    reason: str
    status: str
    rejection_reason: str | None = None
    created_at: datetime


class LeaveActionRequest(BaseModel):
    comments: str | None = Field(default=None, max_length=300)


class CancelLeaveRequest(BaseModel):
    comments: str | None = Field(default=None, max_length=300)
