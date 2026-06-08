from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from services.auth_service import crud
from services.auth_service.models import User
from services.auth_service.schemas import LoginRequest, TokenResponse, UserProfile, ValidateTokenResponse
from shared.app_factory import create_app
from shared.database import Base, SessionLocal, get_engine
from shared.deps import get_current_user_token
from shared.security import create_access_token, verify_password


app: FastAPI = create_app("auth-service")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=get_engine())
    with SessionLocal() as db:
        crud.seed_users(db)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user: User | None = crud.get_user_by_username(db, payload.username)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"userId": user.id, "role": user.role, "username": user.username, "employee_name": user.employee_name, "manager_id": user.manager_id})
    return TokenResponse(access_token=token)


@app.get("/auth/me", response_model=UserProfile)
def me(token: dict = Depends(get_current_user_token)) -> UserProfile:
    return UserProfile(
        id=int(token["userId"]),
        username=str(token.get("username", "")),
        role=str(token["role"]),
        employee_name=str(token.get("employee_name", "")),
        manager_id=token.get("manager_id"),
    )


@app.get("/auth/validate", response_model=ValidateTokenResponse)
def validate_token(token: dict = Depends(get_current_user_token)) -> ValidateTokenResponse:
    return ValidateTokenResponse(
        valid=True,
        user=UserProfile(
            id=int(token["userId"]),
            username=str(token.get("username", "")),
            role=str(token["role"]),
            employee_name=str(token.get("employee_name", "")),
            manager_id=token.get("manager_id"),
        ),
    )
