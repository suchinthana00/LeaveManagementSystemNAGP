from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from shared.config import get_settings


Base = declarative_base()


def get_engine():
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, connect_args=connect_args, future=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine(), future=True)
