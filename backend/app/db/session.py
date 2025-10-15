"""SQLModel session utilities."""

from sqlmodel import Session, SQLModel, create_engine

from ..config import get_settings
from . import models  # noqa: F401 ensure models are registered


settings = get_settings()

engine = create_engine("sqlite:///data.db", echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    with Session(engine) as session:
        yield session
