from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Message, Conversation
from datetime import datetime

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.post("/{conversation_id}")
def create_message(conversation_id: int, sender: str, content: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msg = Message(conversation_id=conversation_id, sender=sender, content=content, timestamp=datetime.utcnow())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

@router.get("/{conversation_id}")
def get_messages(conversation_id: int, db: Session = Depends(get_db)):
    return db.query(Message).filter(Message.conversation_id == conversation_id).all()
