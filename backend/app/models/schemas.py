# app/models/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum


# --- Gender Enum for validation ---
class GenderEnum(str, Enum):
    male = "male"
    female = "female"

# --- App Type Enum for conversations ---
class AppTypeEnum(str, Enum):
    turtle = "turtle"
    upload = "upload"

class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[GenderEnum] = None

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    gender: Optional[GenderEnum]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

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

# --- Conversation ---
class ConversationCreate(BaseModel):
    title: Optional[str]
    code: Optional[str] = None  # Optional for turtle apps (will be generated)
    file_name: Optional[str] = None  # Optional for turtle apps
    app_type: AppTypeEnum = AppTypeEnum.upload
    app_image: Optional[str] = None  # Base64 encoded app image


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    code: str
    file_name: str
    app_type: AppTypeEnum
    app_image: Optional[str] = None

    class Config:
        from_attributes = True

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    app_image: Optional[str] = None


# Message
class MessageCreate(BaseModel):
    conversation_id: int
    user_id: Optional[int] = None
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
        from_attributes = True

class AnalyzeCommandRequest(BaseModel):
    conversation_id: int
    command: str
    language: Optional[str] = "en"

class ExecuteCommandRequest(BaseModel):
    conversation_id: int
    executable: str

class SimpleCodeRequest(BaseModel):
    code: str
    timeout: Optional[int] = 30  # Default 30 second timeout

# Voice Settings
class VoiceEngineEnum(str, Enum):
    standard = "standard"
    google = "google"

class VoiceSettings(BaseModel):
    voice_engine: VoiceEngineEnum = VoiceEngineEnum.standard
    volume: int = 70  # 0-100

class VoiceSettingsUpdate(BaseModel):
    voice_engine: Optional[VoiceEngineEnum] = None
    volume: Optional[int] = None


# --- Favorite Schemas ---
class FavoriteToggleRequest(BaseModel):
    conversation_id: Optional[int] = None
    builtin_app_id: Optional[str] = None

class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    conversation_id: Optional[int] = None
    builtin_app_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FavoriteToggleResponse(BaseModel):
    is_favorited: bool
    message: str