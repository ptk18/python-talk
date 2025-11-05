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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="New Conversation")
    code = Column(Text, nullable=False)          # store Python code content
    file_name = Column(String, nullable=False)   # store uploaded file name
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

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
