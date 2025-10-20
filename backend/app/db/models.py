"""SQLModel database models."""

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Description(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str
    style: str
    content: str
    image_path: Optional[str] = Field(default=None)

    user: "User" = Relationship(back_populates="descriptions")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: Optional[str] = Field(default=None, index=True, unique=True)
    phone_number: Optional[str] = Field(default=None, index=True, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    descriptions: list[Description] = Relationship(back_populates="user")
    reset_tokens: list["PasswordResetToken"] = Relationship(back_populates="user")


class PasswordResetToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    token_hash: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=30))
    used: bool = Field(default=False)

    user: User = Relationship(back_populates="reset_tokens")
