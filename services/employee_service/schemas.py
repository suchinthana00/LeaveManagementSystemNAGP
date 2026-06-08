from pydantic import BaseModel


class EmployeeResponse(BaseModel):
    id: int
    user_id: int
    username: str
    name: str
    role: str
    manager_user_id: int | None = None


class TeamResponse(BaseModel):
    manager_user_id: int
    members: list[EmployeeResponse]
