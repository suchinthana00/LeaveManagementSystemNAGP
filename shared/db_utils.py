from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def build_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


def build_session_local(database_url: str):
    engine = build_engine(database_url)
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
