# app/models/crud.py
from sqlalchemy.orm import Session
from app.models import models

# ----- USERS -----
def create_user(db: Session, username: str, password: str, gender: str, full_name: str = None):
    user = models.User(username=username, password=password, gender=gender, full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


# ----- CONVERSATION -----
def create_conversation(db: Session, user_id: int, code: str, file_name: str, title: str = None):
    conv = models.Conversation(user_id=user_id, title=title, code=code, file_name=file_name)
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
