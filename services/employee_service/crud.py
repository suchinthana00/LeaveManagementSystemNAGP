from sqlalchemy import select
from sqlalchemy.orm import Session

from services.employee_service.models import Employee


def seed_employees(db: Session) -> None:
    if db.query(Employee).first():
        return

    records = [
        Employee(id=1, user_id=1, username="manager1", name="Alice Manager", role="Manager", manager_user_id=None),
        Employee(id=2, user_id=2, username="employee1", name="Bob Employee", role="Employee", manager_user_id=1),
        Employee(id=3, user_id=3, username="employee2", name="Carol Employee", role="Employee", manager_user_id=1),
    ]
    db.add_all(records)
    db.commit()


def get_by_user_id(db: Session, user_id: int) -> Employee | None:
    statement = select(Employee).where(Employee.user_id == user_id)
    return db.execute(statement).scalar_one_or_none()


def get_team_members(db: Session, manager_user_id: int) -> list[Employee]:
    statement = select(Employee).where(Employee.manager_user_id == manager_user_id)
    return list(db.execute(statement).scalars().all())
