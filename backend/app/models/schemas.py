# app/models/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# --- Base class for Post ---
class PostBase(BaseModel):
    title: str
    content: str

# --- Input for creating a Post ---
class PostCreate(PostBase):
    author_id: int  # link to User

# --- Response for Post ---
class PostResponse(PostBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Conversation
class ConversationCreate(BaseModel):
    user_id: int
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


# Message
class MessageCreate(BaseModel):
    conversation_id: int
    user_id: Optional[int] = None  # allow null if message from system/assistant without a user entry
    role: str
    text: str

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    user_id: Optional[int]
    role: str
    text: str
    created_at: datetime

    class Config:
        orm_mode = True
