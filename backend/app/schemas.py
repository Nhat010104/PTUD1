"""Pydantic models for request and response payloads."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class GenerateTextRequest(BaseModel):
    product_info: str = Field(..., min_length=3)
    style: str = Field(default="Marketing")


class DescriptionResponse(BaseModel):
    description: str
    seo_score: int
    seo_factors: List[str]
    history_id: str
    timestamp: str
    style: str
    source: str
    image_url: Optional[str]


class HistoryItem(BaseModel):
    id: str
    timestamp: str
    source: str
    style: str
    summary: str
    full_description: str
    image_url: Optional[str]


class ExportRequest(BaseModel):
    description: str


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    created_at: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    email: str
    token: str
    new_password: str = Field(min_length=6)


class MessageResponse(BaseModel):
    message: str
