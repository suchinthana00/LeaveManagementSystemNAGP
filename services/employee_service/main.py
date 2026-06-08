from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from services.employee_service import crud
from services.employee_service.models import Employee
from services.employee_service.schemas import EmployeeResponse, TeamResponse
from shared.app_factory import create_app
from shared.config import get_settings
from shared.database import Base
from shared.db_utils import build_session_local
from shared.deps import get_current_user_token


settings = get_settings()
engine, SessionLocal = build_session_local(settings.database_url)
app = create_app("employee-service")


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
		crud.seed_employees(db)


def to_response(employee: Employee) -> EmployeeResponse:
	return EmployeeResponse(
		id=employee.id,
		user_id=employee.user_id,
		username=employee.username,
		name=employee.name,
		role=employee.role,
		manager_user_id=employee.manager_user_id,
	)


@app.get("/employees/me", response_model=EmployeeResponse)
def get_my_profile(token: dict = Depends(get_current_user_token), db: Session = Depends(get_db)) -> EmployeeResponse:
	employee = crud.get_by_user_id(db, int(token["userId"]))
	if employee is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
	return to_response(employee)


@app.get("/employees/{user_id}", response_model=EmployeeResponse)
def get_employee(
	user_id: int,
	token: dict = Depends(get_current_user_token),
	db: Session = Depends(get_db),
) -> EmployeeResponse:
	requester_id = int(token["userId"])
	requester_role = str(token["role"])

	employee = crud.get_by_user_id(db, user_id)
	if employee is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

	if requester_role == "Employee" and requester_id != user_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees can access only their own data")

	if requester_role == "Manager" and requester_id != user_id and employee.manager_user_id != requester_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can access only team members")

	return to_response(employee)


@app.get("/managers/{manager_user_id}/team", response_model=TeamResponse)
def get_manager_team(
	manager_user_id: int,
	token: dict = Depends(get_current_user_token),
	db: Session = Depends(get_db),
	include_self: bool = Query(default=False),
) -> TeamResponse:
	requester_id = int(token["userId"])
	requester_role = str(token["role"])
	if requester_role != "Manager" or requester_id != manager_user_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the manager can access this team")

	members = [to_response(member) for member in crud.get_team_members(db, manager_user_id)]
	if include_self:
		self_record = crud.get_by_user_id(db, manager_user_id)
		if self_record is not None:
			members.insert(0, to_response(self_record))
	return TeamResponse(manager_user_id=manager_user_id, members=members)

