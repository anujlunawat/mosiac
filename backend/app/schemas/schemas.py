from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Any, Optional
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    name: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class TicketRequest(BaseModel):
    doc_id: str


# schemas/schemas.py


class DocumentOut(BaseModel):
    id: str
    title: str
    owner_id: UUID | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
