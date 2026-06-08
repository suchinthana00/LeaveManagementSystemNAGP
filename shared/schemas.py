from enum import Enum

from pydantic import BaseModel


class Role(str, Enum):
    employee = "Employee"
    manager = "Manager"


class ErrorResponse(BaseModel):
    detail: str
