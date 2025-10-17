"""SQLModel session utilities."""

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from ..config import get_settings
from . import models  # noqa: F401 ensure models are registered

settings = get_settings()

engine = create_engine("sqlite:///data.db", echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(description)"))
        column_names = {row[1] for row in columns}
        if "image_path" not in column_names:
            connection.execute(text("ALTER TABLE description ADD COLUMN image_path TEXT"))


def get_session() -> Session:
    with Session(engine) as session:
        yield session
