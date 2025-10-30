# app/models/crud.py
from sqlalchemy.orm import Session
from app.models import models
from sqlalchemy.exc import IntegrityError

# ----- USERS -----
def create_user(db: Session, username: str, email: str, password_hash: str, full_name: str | None = None):
    user = models.User(username=username, email=email, password_hash=password_hash, full_name=full_name)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


# ----- CONVERSATION -----
def create_conversation(db: Session, user_id: int, title: str = None):
    conv = models.Conversation(user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

def get_conversation(db: Session, conversation_id: int):
    return db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()

def get_conversations_by_user(db: Session, user_id: int):
    return db.query(models.Conversation).filter(models.Conversation.user_id == user_id).order_by(models.Conversation.created_at.desc()).all()

def delete_conversation(db: Session, conversation_id: int):
    conv = get_conversation(db, conversation_id)
    if conv:
        db.delete(conv)
        db.commit()
    return conv


# ----- MESSAGE -----
def create_message(db: Session, conversation_id: int, role: str, text: str, user_id: int = None):
    msg = models.Message(conversation_id=conversation_id, role=role, text=text, user_id=user_id)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def get_messages(db: Session, conversation_id: int):
    return db.query(models.Message).filter(models.Message.conversation_id == conversation_id).order_by(models.Message.created_at).all()

def delete_messages_in_conversation(db: Session, conversation_id: int):
    msgs = db.query(models.Message).filter(models.Message.conversation_id == conversation_id).all()
    for m in msgs:
        db.delete(m)
    db.commit()
    return True
