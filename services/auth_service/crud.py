from sqlalchemy import select
from sqlalchemy.orm import Session

from services.auth_service.models import User


def get_user_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    return db.execute(statement).scalar_one_or_none()


def seed_users(db: Session) -> None:
    if db.query(User).first():
        return

    from shared.security import hash_password

    users = [
        User(id=1, username="manager1", password_hash=hash_password("Password@123"), role="Manager", employee_name="Alice Manager", manager_id=None),
        User(id=2, username="employee1", password_hash=hash_password("Password@123"), role="Employee", employee_name="Bob Employee", manager_id=1),
        User(id=3, username="employee2", password_hash=hash_password("Password@123"), role="Employee", employee_name="Carol Employee", manager_id=1),
    ]
    db.add_all(users)
    db.commit()
