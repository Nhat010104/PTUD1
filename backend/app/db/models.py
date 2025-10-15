"""SQLModel database models."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Description(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str
    style: str
    content: str
    image_path: Optional[str] = None

    user: "User" = Relationship(back_populates="descriptions")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    descriptions: list[Description] = Relationship(back_populates="user")
