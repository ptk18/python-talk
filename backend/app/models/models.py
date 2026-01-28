# app/models/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
from datetime import datetime
import enum

# --- Enum for gender ---
class GenderEnum(enum.Enum):
    male = "male"
    female = "female"

# --- Enum for app type ---
class AppTypeEnum(enum.Enum):
    turtle = "turtle"
    upload = "upload"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)  # For old users
    password_hash = Column(String, nullable=False)  # For new auth system
    gender = Column(Enum(GenderEnum), nullable=True)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    conversations = relationship("Conversation", back_populates="user")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="New Conversation")
    code = Column(Text, nullable=False)          # store Python code content
    file_name = Column(String, nullable=False)   # store uploaded file name
    app_type = Column(Enum(AppTypeEnum), default=AppTypeEnum.upload)  # turtle or upload
    app_image = Column(Text, nullable=True)      # store base64 encoded app image
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    favorites = relationship("Favorite", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, nullable=False)  # "user" or "system"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    conversation = relationship("Conversation", back_populates="messages")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    builtin_app_id = Column(String, nullable=True)  # e.g., "builtin:codespace"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="favorites")
    conversation = relationship("Conversation", back_populates="favorites")
